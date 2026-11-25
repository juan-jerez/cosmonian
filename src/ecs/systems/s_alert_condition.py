import esper

from src.ecs.components.c_alert_condition import CAlertCondition
from src.ecs.components.c_base import CBase
from src.ecs.components.c_enemy_ai import CEnemyAI
from src.ecs.components.c_enemy_spawner import CEnemySpawner
from src.ecs.components.c_velocity import CVelocity
from src.engine.service_locator import ServiceLocator


def system_alert_condition(world: esper.World, delta_time: float, alert_info: dict):
    """VERDE al empezar (sin enemigos) y, poco después, AMARILLO. Destruir una base devuelve a
    VERDE un rato. Pasa a ROJO (sin vuelta atrás) si el nivel se alarga o si escapa un espía."""
    for _, c_ac in world.get_component(CAlertCondition):
        previous = c_ac.level
        c_ac.level_time += delta_time

        bases = len(world.get_component(CBase))
        first_frame = c_ac.bases_left is None
        if not first_frame and bases < c_ac.bases_left and c_ac.level != "RED":
            c_ac.level = "GREEN"
            c_ac.green_timer = c_ac.base_green_time
        c_ac.bases_left = bases

        if c_ac.level == "GREEN":
            c_ac.green_timer -= delta_time
            if c_ac.green_timer <= 0:
                c_ac.level = "YELLOW"
        if c_ac.spy_escaped or c_ac.level_time >= c_ac.red_after:
            c_ac.level = "RED"

        if first_frame or c_ac.level != previous:
            _apply_level(world, c_ac.level, alert_info["red"])
        if c_ac.level != previous:
            ServiceLocator.sounds_service.play(alert_info["sounds"][c_ac.level])


def _apply_level(world: esper.World, level: str, red_info: dict):
    red = level == "RED"
    for _, c_spw in world.get_component(CEnemySpawner):
        c_spw.active = level != "GREEN"
        c_spw.rate = red_info["spawn_rate"] if red else 1.0
        c_spw.speed = red_info["speed"] if red else 1.0
        c_spw.max_factor = red_info["max_enemies"] if red else 1.0
    # Los enemigos que ya están en juego también se aceleran
    if red:
        for _, (c_v, c_ai) in world.get_components(CVelocity, CEnemyAI):
            c_ai.max_speed *= red_info["speed"]
            c_v.vel *= red_info["speed"]


def set_alert_level(world: esper.World, level: str, alert_info: dict):
    """Fija la condición a mano (modo trampa): se aplica y suena como un cambio normal."""
    for _, c_ac in world.get_component(CAlertCondition):
        c_ac.level = level
        c_ac.spy_escaped = False
        # Para que no vuelva a ROJO enseguida por tiempo ni salga de VERDE al instante
        c_ac.level_time = 0
        c_ac.green_timer = c_ac.base_green_time
    _apply_level(world, level, alert_info["red"])
    ServiceLocator.sounds_service.play(alert_info["sounds"][level])


def alert_level(world: esper.World) -> str:
    """Condición actual; fuera del juego es VERDE."""
    for _, c_ac in world.get_component(CAlertCondition):
        return c_ac.level
    return "GREEN"
