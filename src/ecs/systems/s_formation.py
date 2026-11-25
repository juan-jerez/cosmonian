import random

import pygame
import esper

from src.create.prefab_creator import create_formation
from src.ecs.components.c_base import CBase
from src.ecs.components.c_enemy_ai import CEnemyAI, EnemyState
from src.ecs.components.c_formation import CFormation, CFormationMember
from src.ecs.components.c_formation_spawner import CFormationSpawner
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_alert_condition import alert_level
from src.ecs.systems.s_score import add_points
from src.ecs.systems.s_world_wrap import world_size, wrap_delta
from src.ecs.utils.steering import apply_steering, seek
from src.engine.service_locator import ServiceLocator


def system_formation_spawner(
    world: esper.World, delta_time: float, formations_info: dict, enemies_info: dict, player_max_speed: float
):
    """En AMARILLO o ROJO, cada cierto tiempo sale una formación de una base al azar."""
    if _player_center(world) is None or not world.get_component(CBase):
        return
    green = alert_level(world) == "GREEN"
    for _, c_fs in world.get_component(CFormationSpawner):
        if green and not c_fs.ignore_green:
            continue
        c_fs.timer -= delta_time
        if c_fs.timer > 0:
            continue
        c_fs.timer = c_fs.interval
        spawn_formation(world, c_fs, formations_info, enemies_info, player_max_speed)


def spawn_formation(
    world: esper.World,
    c_fs: CFormationSpawner,
    formations_info: dict,
    enemies_info: dict,
    player_max_speed: float,
):
    """Formación (figura y tipo al azar según los pesos del nivel) que sale de una base al azar
    rumbo al jugador."""
    player_center = _player_center(world)
    bases = world.get_components(CTransform, CBase)
    if player_center is None or not bases:
        return
    base_center = random.choice(bases)[1][0].pos
    shape = random.choices(list(c_fs.shapes), weights=list(c_fs.shapes.values()))[0]
    kind = random.choices(list(c_fs.kinds), weights=list(c_fs.kinds.values()))[0]
    direction = wrap_delta(player_center - base_center, world_size(world))
    if direction.length_squared() == 0:
        direction = pygame.Vector2(0, -1)
    create_formation(world, shape, kind, base_center, direction, formations_info, enemies_info, player_max_speed)
    ServiceLocator.sounds_service.play(formations_info["sound"])


def system_formation(world: esper.World, delta_time: float, enemies_info: dict, player_max_speed: float):
    """La formación va siempre directo hacia el jugador y cada miembro ocupa su hueco en la
    figura, girada según el rumbo. Si cae el capitán (o muere el jugador), se disuelve y los
    demás huyen."""
    player_center = _player_center(world)
    size = world_size(world)
    for formation_entity, (c_t, c_v, c_f) in world.get_components(CTransform, CVelocity, CFormation):
        c_f.members = [m for m in c_f.members if world.entity_exists(m)]
        if not c_f.members:
            # Toda la formación destruida por el jugador: bono
            if c_f.killed_by_player == c_f.total_members:
                add_points(world, c_f.full_bonus)
            world.delete_entity(formation_entity)
            continue
        if player_center is None or not world.entity_exists(c_f.captain_entity):
            _dissolve(world, formation_entity, c_f, enemies_info, player_max_speed)
            continue

        to_player = wrap_delta(player_center - c_t.pos, size)
        c_v.vel = apply_steering(c_v.vel, seek(to_player, c_f.max_speed), c_f.max_force, c_f.max_speed, delta_time)
        # La entidad de la formación no tiene imagen: se mantiene dentro del mundo aquí
        if size is not None:
            c_t.pos.xy = (c_t.pos.x % size.x, c_t.pos.y % size.y)
        angle = pygame.Vector2(0, -1).angle_to(c_v.vel)

        for member in c_f.members:
            m_t = world.component_for_entity(member, CTransform)
            m_s = world.component_for_entity(member, CSurface)
            c_m = world.component_for_entity(member, CFormationMember)
            m_t.pos.xy = c_t.pos + c_m.offset.rotate(angle) - pygame.Vector2(m_s.area.size) / 2
            world.component_for_entity(member, CVelocity).vel.xy = c_v.vel


def _dissolve(world: esper.World, formation_entity: int, c_f: CFormation, enemies_info: dict, player_max_speed: float):
    for member in c_f.members:
        kind = world.component_for_entity(member, CFormationMember).kind
        world.remove_component(member, CFormationMember)
        c_ai = CEnemyAI(kind, enemies_info[kind], enemies_info["steering"], 1, player_max_speed * enemies_info[kind]["speed_factor"])
        # Huyen (el tipo E sigue recto, como siempre)
        if c_ai.state != EnemyState.STRAIGHT:
            c_ai.state = EnemyState.LEAVE
        world.add_component(member, c_ai)
    world.delete_entity(formation_entity)


def _player_center(world: esper.World) -> pygame.Vector2 | None:
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    if not players:
        return None
    p_t, p_s, _ = players[0][1]
    return p_t.pos + pygame.Vector2(p_s.area.size) / 2
