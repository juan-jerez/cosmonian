import pygame
import esper

from src.create.prefab_creator import create_player_shots
from src.ecs.components.c_autopilot import CAutopilot
from src.ecs.components.c_base_turret import CBaseTurret, TurretState
from src.ecs.components.c_obstacle import CObstacle
from src.ecs.components.c_player_ship import CPlayerShip
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_base_part import CTagBasePart
from src.ecs.components.tags.c_tag_bullet import CTagBullet
from src.ecs.components.tags.c_tag_enemy import CTagEnemy
from src.ecs.components.tags.c_tag_enemy_bullet import CTagEnemyBullet
from src.ecs.systems.s_player_ship import steer_player
from src.ecs.systems.s_world_wrap import world_size, wrap_delta
from src.ecs.utils.directions import DIRECTIONS, direction_index


def system_autopilot(world: esper.World, delta_time: float, bullet_info: dict, triple_shot: bool):
    """Maneja la nave en el modo atractor:
    1. Si tiene algo peligroso justo delante, gira hacia un lado para esquivarlo.
    2. Si hay un enemigo cerca, va hacia él.
    3. Si no, va a por la torreta más cercana y, al llegar, la rodea.
    Dispara cuando lo que persigue está delante y a tiro."""
    size = world_size(world)
    for _, (c_t, c_s, c_v, c_ship, c_ap) in world.get_components(
        CTransform, CSurface, CVelocity, CPlayerShip, CAutopilot
    ):
        center = c_t.pos + pygame.Vector2(c_s.area.size) / 2
        heading = DIRECTIONS[c_ship.direction]

        def offsets(*components) -> list[pygame.Vector2]:
            found = []
            for _, (o_t, o_s, *_rest) in world.get_components(CTransform, CSurface, *components):
                found.append(wrap_delta(o_t.pos + pygame.Vector2(o_s.area.size) / 2 - center, size))
            return found

        dangers = offsets(CObstacle) + offsets(CTagEnemyBullet) + offsets(CTagBasePart) + offsets(CTagEnemy)
        ahead = [d for d in dangers if d.length() < c_ap.avoid_distance and d.dot(heading) > 0]
        enemies = sorted(offsets(CTagEnemy), key=lambda d: d.length())
        turrets = sorted(
            (
                wrap_delta(t_t.pos + pygame.Vector2(t_s.area.size) / 2 - center, size)
                for _, (t_t, t_s, c_tur) in world.get_components(CTransform, CSurface, CBaseTurret)
                if c_tur.state != TurretState.DESTROYED
            ),
            key=lambda d: d.length(),
        )

        target = None
        if ahead:
            # Esquiva hacia el lado contrario a lo más cercano
            closest = min(ahead, key=lambda d: d.length())
            side = 1 if heading.cross(closest) < 0 else -1
            desired = heading.rotate(90 * side)
        elif enemies and enemies[0].length() < c_ap.engage_distance:
            target = enemies[0]
            desired = target
        elif turrets:
            target = turrets[0]
            # Lejos va directo; cerca rodea la base para no chocar con ella
            desired = target if target.length() > c_ap.orbit_distance else target.rotate(90)
        else:
            desired = heading
        if desired.length_squared() > 0:
            steer_player(world, direction_index(desired))

        c_ap.fire_timer -= delta_time
        aimed = False
        if target is not None and target.length() < c_ap.fire_range:
            # angle_to puede dar, por ejemplo, -350 grados: se lleva al rango -180..180
            angle = (heading.angle_to(target) + 180) % 360 - 180
            aimed = abs(angle) < c_ap.fire_angle
        if aimed and c_ap.fire_timer <= 0 and len(world.get_component(CTagBullet)) < bullet_info["max_bullets"]:
            c_ap.fire_timer = c_ap.fire_interval
            create_player_shots(world, center, c_ship.direction, c_v.vel, bullet_info, triple_shot)
