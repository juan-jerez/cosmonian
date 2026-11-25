import pygame
import esper

from src.create.prefab_creator import create_enemy_bullet
from src.ecs.components.c_base_turret import CBaseTurret, TurretState
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_animation import set_frame
from src.ecs.systems.s_world_wrap import world_size, wrap_delta


def system_base_turret(world: esper.World, delta_time: float, bullet_info: dict):
    """Las torretas esperan con el jugador cerca, se abren y le disparan; luego se cierran."""
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    player_center = None
    if players:
        p_t, p_s, _ = players[0][1]
        player_center = p_t.pos + pygame.Vector2(p_s.area.size) / 2
    size = world_size(world)

    for _, (c_t, c_s, c_tur) in world.get_components(CTransform, CSurface, CBaseTurret):
        if c_tur.state == TurretState.DESTROYED:
            continue
        center = c_t.pos + pygame.Vector2(c_s.area.size) / 2
        to_player = None if player_center is None else wrap_delta(player_center - center, size)
        in_range = to_player is not None and 0 < to_player.length() <= c_tur.range

        if c_tur.state == TurretState.IDLE:
            if in_range:
                c_tur.timer -= delta_time
                if c_tur.timer <= 0:
                    c_tur.state = TurretState.OPEN
                    c_tur.timer = c_tur.open_time
        elif c_tur.state == TurretState.OPEN:
            c_tur.timer -= delta_time
            if c_tur.timer <= 0:
                if in_range:
                    create_enemy_bullet(world, center, to_player.normalize() * bullet_info["velocity"], bullet_info)
                    c_tur.state = TurretState.FIRING
                    c_tur.timer = c_tur.firing_time
                else:
                    c_tur.state = TurretState.IDLE
                    c_tur.timer = c_tur.random_interval()
        elif c_tur.state == TurretState.FIRING:
            c_tur.timer -= delta_time
            if c_tur.timer <= 0:
                c_tur.state = TurretState.IDLE
                c_tur.timer = c_tur.random_interval()

        set_frame(c_s, c_tur.frames[c_tur.state.name.lower()])
