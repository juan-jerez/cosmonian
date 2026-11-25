import math
import random

import pygame
import esper

from src.create.prefab_creator import create_spy
from src.ecs.components.c_alert_condition import CAlertCondition
from src.ecs.components.c_spy import CSpy
from src.ecs.components.c_spy_spawner import CSpySpawner
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_alert_condition import alert_level
from src.ecs.systems.s_camera import camera_rect
from src.ecs.systems.s_world_wrap import nearest_rect, world_size, wrap_delta
from src.engine.service_locator import ServiceLocator


def system_spy_spawner(
    world: esper.World, delta_time: float, enemies_info: dict, player_max_speed: float, view_size: pygame.Vector2
):
    """En AMARILLO o ROJO, cada cierto tiempo aparece un espía fuera de la pantalla que la cruza."""
    if alert_level(world) == "GREEN" or world.get_component(CSpy):
        return
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    if not players:
        return
    p_t, p_s, _ = players[0][1]
    player_center = p_t.pos + pygame.Vector2(p_s.area.size) / 2
    for _, c_ss in world.get_component(CSpySpawner):
        c_ss.timer -= delta_time
        if c_ss.timer > 0:
            continue
        c_ss.timer = c_ss.interval
        spawn_spy(world, player_center, enemies_info, player_max_speed, view_size)


def spawn_spy(
    world: esper.World,
    player_center: pygame.Vector2,
    enemies_info: dict,
    player_max_speed: float,
    view_size: pygame.Vector2,
):
    """Espía fuera de la pantalla, en una dirección al azar, que la cruzará."""
    distance = math.hypot(view_size.x, view_size.y) / 2 + enemies_info["spawn"]["margin"]
    offset = pygame.Vector2(distance, 0).rotate(random.uniform(0, 360))
    # Cruza la pantalla en diagonal respecto al jugador, no directo hacia él
    direction = (-offset).rotate(random.uniform(-25, 25))
    create_spy(world, player_center + offset, direction, enemies_info["SPY"], player_max_speed)
    ServiceLocator.sounds_service.play(enemies_info["SPY"]["sound"])


def system_spy(world: esper.World):
    """El espía entra en la pantalla; la primera vez que llega a un borde rebota y la segunda
    escapa: entonces la condición pasa a ROJO. Mientras se ve, el panel muestra "¡ESPIA!"."""
    view = camera_rect(world)
    view_center = pygame.Vector2(view.center)
    size = world_size(world)
    visible = False
    escaped = False
    for entity, (c_t, c_s, c_v, c_spy) in world.get_components(CTransform, CSurface, CVelocity, CSpy):
        rect = nearest_rect(c_s.get_frect(c_t.pos), view_center, size)
        inside = view.contains(rect)
        on_screen = view.colliderect(rect)
        visible = visible or on_screen
        if not c_spy.entered:
            if inside:
                c_spy.entered = True
            elif wrap_delta(pygame.Vector2(rect.center) - view_center, size).length() > view.w * 1.5:
                # Si el jugador se alejó antes de que entrara, vuelve a buscar la pantalla
                c_v.vel = (view_center - pygame.Vector2(rect.center)).normalize() * c_v.vel.length()
            continue
        if inside:
            continue
        if not c_spy.bounced:
            # Rebota en el borde por el que intentaba salir
            if (rect.left < view.left and c_v.vel.x < 0) or (rect.right > view.right and c_v.vel.x > 0):
                c_v.vel.x = -c_v.vel.x
            if (rect.top < view.top and c_v.vel.y < 0) or (rect.bottom > view.bottom and c_v.vel.y > 0):
                c_v.vel.y = -c_v.vel.y
            c_spy.bounced = True
        elif not on_screen:
            world.delete_entity(entity)
            escaped = True

    for _, c_ac in world.get_component(CAlertCondition):
        c_ac.spy_visible = visible
        c_ac.spy_escaped = c_ac.spy_escaped or escaped
