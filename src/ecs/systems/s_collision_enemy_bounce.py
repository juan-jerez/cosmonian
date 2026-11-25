import pygame
import esper

from src.ecs.components.c_enemy_ai import CEnemyAI
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_obstacle import CObstacle, ObstacleKind
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_base_part import CTagBasePart
from src.ecs.components.tags.c_tag_enemy import CTagEnemy
from src.ecs.systems.s_world_wrap import boxes_overlap, nearest_rect, world_size
from src.ecs.utils.spatial_grid import SpatialGrid

# Tamaño de celda de la cuadrícula de piezas de bases
CELL_SIZE = 32


def system_collision_enemy_bounce(world: esper.World):
    """Los enemigos que chocan entre sí o contra una base rebotan: se separan e invierten su
    velocidad en el eje en el que se tocan."""
    size = world_size(world)
    enemies = world.get_components(CTransform, CSurface, CVelocity, CHitBox, CTagEnemy)
    for i, (_, (a_t, a_s, a_v, a_hb, _)) in enumerate(enemies):
        for _, (b_t, b_s, b_v, b_hb, _) in enemies[i + 1 :]:
            a_rect = a_hb.rect(a_t, a_s)
            b_rect = b_hb.rect(b_t, b_s)
            if not boxes_overlap(a_rect.center, a_hb.size, b_rect.center, b_hb.size, size):
                continue
            b_rect = nearest_rect(b_rect, pygame.Vector2(a_rect.center), size)
            # Se separan por el eje en el que se meten menos uno en el otro
            overlap_x = min(a_rect.right, b_rect.right) - max(a_rect.left, b_rect.left)
            overlap_y = min(a_rect.bottom, b_rect.bottom) - max(a_rect.top, b_rect.top)
            axis = 0 if overlap_x < overlap_y else 1
            overlap = overlap_x if axis == 0 else overlap_y
            # Signo: hacia dónde hay que empujar a A para alejarlo de B
            sign = 1 if a_rect.center[axis] >= b_rect.center[axis] else -1
            a_t.pos[axis] += sign * overlap / 2
            b_t.pos[axis] -= sign * overlap / 2
            # Solo rebotan si se están acercando (si ya se alejan, se dejan como van)
            if (a_v.vel[axis] - b_v.vel[axis]) * sign < 0:
                a_v.vel[axis] = -a_v.vel[axis]
                b_v.vel[axis] = -b_v.vel[axis]

    # Las bases no se mueven: el enemigo (o la roca indestructible) sale entero de la pieza y rebota
    parts = world.get_components(CTransform, CSurface, CHitBox, CTagBasePart)
    hard_rocks = [
        (entity, (c_t, c_s, c_v, c_hb, c_ob))
        for entity, (c_t, c_s, c_v, c_hb, c_ob) in world.get_components(CTransform, CSurface, CVelocity, CHitBox, CObstacle)
        if c_ob.kind == ObstacleKind.HARD_ROCK
    ]
    grid = SpatialGrid(CELL_SIZE, size)
    for _, (p_t, p_s, p_hb, _) in parts:
        part_rect = p_hb.rect(p_t, p_s)
        grid.insert((part_rect, p_hb.size), part_rect.center, p_hb.size)
    for entity, (e_t, e_s, e_v, e_hb, _) in enemies + hard_rocks:
        # El tipo E que acaba de salir del núcleo atraviesa su base
        if world.has_component(entity, CEnemyAI) and world.component_for_entity(entity, CEnemyAI).base_grace > 0:
            continue
        for part_rect, part_size in grid.query(e_hb.rect(e_t, e_s).center, e_hb.size):
            e_rect = e_hb.rect(e_t, e_s)
            if not boxes_overlap(e_rect.center, e_hb.size, part_rect.center, part_size, size):
                continue
            p_rect = nearest_rect(part_rect, pygame.Vector2(e_rect.center), size)
            overlap_x = min(e_rect.right, p_rect.right) - max(e_rect.left, p_rect.left)
            overlap_y = min(e_rect.bottom, p_rect.bottom) - max(e_rect.top, p_rect.top)
            axis = 0 if overlap_x < overlap_y else 1
            sign = 1 if e_rect.center[axis] >= p_rect.center[axis] else -1
            e_t.pos[axis] += sign * (overlap_x if axis == 0 else overlap_y)
            if e_v.vel[axis] * sign < 0:
                e_v.vel[axis] = -e_v.vel[axis]
