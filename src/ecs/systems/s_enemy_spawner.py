import math
import random

import pygame
import esper

from src.create.prefab_creator import create_enemy
from src.ecs.components.c_base import CBase
from src.ecs.components.c_base_core import CBaseCore
from src.ecs.components.c_enemy_ai import CEnemyAI
from src.ecs.components.c_enemy_spawner import CEnemySpawner
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_world_wrap import world_size, wrap_delta


def system_enemy_spawner(
    world: esper.World,
    delta_time: float,
    enemies_info: dict,
    player_max_speed: float,
    view_size: pygame.Vector2,
):
    """Cada cierto tiempo aparece un enemigo al azar desde cualquier dirección, justo fuera de
    la pantalla, rumbo al jugador."""
    player_center = _player_center(world)
    if player_center is None:
        return
    for _, c_spw in world.get_component(CEnemySpawner):
        if not c_spw.active:
            continue
        c_spw.timer -= delta_time * c_spw.rate
        if c_spw.timer > 0:
            continue
        c_spw.timer += c_spw.interval
        if len(world.get_component(CEnemyAI)) >= c_spw.max_enemies * c_spw.max_factor:
            continue
        kind = random.choices(list(c_spw.types), weights=list(c_spw.types.values()))[0]
        # A la distancia de la esquina de la pantalla más un margen: no se ve aparecer
        distance = math.hypot(view_size.x, view_size.y) / 2 + enemies_info["spawn"]["margin"]
        offset = pygame.Vector2(distance, 0).rotate(random.uniform(0, 360))
        create_enemy(
            world, kind, player_center + offset, -offset, enemies_info, c_spw.accuracy, player_max_speed * c_spw.speed
        )


def system_base_core_spawner(world: esper.World, enemies_info: dict, player_max_speed: float):
    """Al terminar de abrirse, el núcleo de una base lanza un enemigo tipo E por su abertura,
    hacia el lado en que está el jugador (si está cerca)."""
    player_center = _player_center(world)
    spawners = [c_spw for _, c_spw in world.get_component(CEnemySpawner)]
    # En VERDE tampoco salen de las bases
    if player_center is None or (spawners and not spawners[0].active):
        return
    speed = spawners[0].speed if spawners else 1.0
    spawn_info = enemies_info["spawn"]
    size = world_size(world)
    for _, (c_t, c_s, c_core) in world.get_components(CTransform, CSurface, CBaseCore):
        if not (c_core.just_opened and c_core.spawn_e):
            continue
        center = c_t.pos + pygame.Vector2(c_s.area.size) / 2
        to_player = wrap_delta(player_center - center, size)
        if to_player.length() > spawn_info["core_spawn_range"]:
            continue
        vertical = world.component_for_entity(c_core.base_entity, CBase).vertical
        if vertical:
            direction = pygame.Vector2(0, 1 if to_player.y >= 0 else -1)
        else:
            direction = pygame.Vector2(1 if to_player.x >= 0 else -1, 0)
        enemy_entity = create_enemy(
            world, "E", center + direction * spawn_info["core_spawn_offset"], direction, enemies_info, 1, player_max_speed * speed
        )
        # Sale desde dentro de la base: un instante sin chocar con ella
        world.component_for_entity(enemy_entity, CEnemyAI).base_grace = spawn_info["base_grace"]


def _player_center(world: esper.World) -> pygame.Vector2 | None:
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    if not players:
        return None
    p_t, p_s, _ = players[0][1]
    return p_t.pos + pygame.Vector2(p_s.area.size) / 2
