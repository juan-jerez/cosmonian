import pygame
import esper

from src.create.prefab_creator import create_explosion, kill_player
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_shield import CShield
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_enemy import CTagEnemy
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_score import award
from src.ecs.systems.s_world_wrap import nearest_rect, world_size


def system_collision_player_enemy(world: esper.World, explosion_info: dict, player_info: dict):
    """Si un enemigo toca al jugador, mueren los dos; con el escudo activo, el enemigo rebota."""
    size = world_size(world)
    for player_entity, (p_t, p_s, p_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagPlayer):
        player_rect = p_hb.rect(p_t, p_s)
        for enemy_entity, (e_t, e_s, e_v, e_hb, _) in world.get_components(
            CTransform, CSurface, CVelocity, CHitBox, CTagEnemy
        ):
            if not world.entity_exists(enemy_entity):
                continue
            # Un enemigo al otro lado del borde del mundo puede estar tocando al jugador
            enemy_rect = nearest_rect(e_hb.rect(e_t, e_s), pygame.Vector2(player_rect.center), size)
            if enemy_rect.colliderect(player_rect):
                if world.has_component(player_entity, CShield):
                    _bounce_off_shield(e_t, e_v, enemy_rect, player_rect)
                    continue
                award(world, enemy_entity)
                world.delete_entity(enemy_entity)
                create_explosion(world, enemy_rect.center, explosion_info, e_v.vel)
                kill_player(world, player_entity, player_info["death"], explosion_info)
                break


def _bounce_off_shield(e_t: CTransform, e_v: CVelocity, enemy_rect: pygame.FRect, player_rect: pygame.FRect):
    """El escudo no destruye: el enemigo sale de encima de la nave y rebota."""
    overlap_x = min(enemy_rect.right, player_rect.right) - max(enemy_rect.left, player_rect.left)
    overlap_y = min(enemy_rect.bottom, player_rect.bottom) - max(enemy_rect.top, player_rect.top)
    axis = 0 if overlap_x < overlap_y else 1
    sign = 1 if enemy_rect.center[axis] >= player_rect.center[axis] else -1
    e_t.pos[axis] += sign * (overlap_x if axis == 0 else overlap_y)
    if e_v.vel[axis] * sign < 0:
        e_v.vel[axis] = -e_v.vel[axis]
