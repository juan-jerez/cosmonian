import random

import pygame
import esper

from src.ecs.components.c_enemy_ai import CEnemyAI, EnemyState
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_world_wrap import world_size, wrap_delta
from src.ecs.utils.steering import apply_steering, flee, seek, wander


def system_enemy_ai(world: esper.World, delta_time: float, despawn_distance: float):
    """Comportamiento de los enemigos con steering behaviours:
    - CHASE: persigue al jugador (apuntando más o menos cerca de él según la dificultad).
    - LEAVE: huye del jugador; al alejarse lo suficiente desaparece (tipo I).
    - WANDER: vaga al azar; al alejarse lo suficiente desaparece (tipo P).
    - STRAIGHT: sigue recto sin desviarse (tipo E)."""
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    player_center = None
    if players:
        p_t, p_s, _ = players[0][1]
        player_center = p_t.pos + pygame.Vector2(p_s.area.size) / 2
    size = world_size(world)

    for entity, (c_t, c_s, c_v, c_ai) in world.get_components(CTransform, CSurface, CVelocity, CEnemyAI):
        c_ai.base_grace = max(0, c_ai.base_grace - delta_time)
        center = c_t.pos + pygame.Vector2(c_s.area.size) / 2
        to_player = None if player_center is None else wrap_delta(player_center - center, size)

        if c_ai.state == EnemyState.CHASE:
            c_ai.state_time -= delta_time
            # Sin jugador (acaba de morir) dejan de perseguir
            if c_ai.state_time <= 0 or to_player is None:
                c_ai.state = c_ai.after_chase

        if c_ai.state == EnemyState.CHASE:
            # Cada cierto tiempo elige un punto al azar cerca del jugador al que apuntar
            c_ai.aim_timer -= delta_time
            if c_ai.aim_timer <= 0:
                c_ai.aim_timer = c_ai.aim_interval
                c_ai.aim_offset = pygame.Vector2(random.uniform(0, c_ai.deviation), 0).rotate(random.uniform(0, 360))
            desired = seek(to_player + c_ai.aim_offset, c_ai.max_speed)
        elif c_ai.state == EnemyState.LEAVE:
            desired = flee(to_player, c_ai.max_speed) if to_player is not None else c_v.vel
        elif c_ai.state == EnemyState.WANDER:
            turn = random.uniform(-c_ai.wander_jitter, c_ai.wander_jitter) * delta_time
            desired = wander(c_v.vel, turn, c_ai.max_speed)
        else:
            desired = c_v.vel

        if c_ai.max_force > 0:
            c_v.vel = apply_steering(c_v.vel, desired, c_ai.max_force, c_ai.max_speed, delta_time)

        # Los que ya no persiguen desaparecen al quedar lejos del jugador (si el jugador está
        # muerto siguen volando, y desaparecen cuando reaparezca lejos de ellos)
        far = to_player is not None and to_player.length() > despawn_distance
        if c_ai.state != EnemyState.CHASE and far:
            world.delete_entity(entity)
