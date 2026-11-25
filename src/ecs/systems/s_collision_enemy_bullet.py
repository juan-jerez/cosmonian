import pygame
import esper

from src.create.prefab_creator import create_explosion, kill_player
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_enemy import CTagEnemy
from src.ecs.components.tags.c_tag_enemy_bullet import CTagEnemyBullet
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_world_wrap import nearest_rect, world_size


def system_collision_enemy_bullet(world: esper.World, explosion_info: dict, player_info: dict):
    """Las balas de las torretas matan al jugador y también a los enemigos que se cruzan con ellas."""
    size = world_size(world)
    bullets = world.get_components(CTransform, CSurface, CHitBox, CTagEnemyBullet)
    for bullet_entity, (b_t, b_s, b_hb, _) in bullets:
        bullet_rect = b_hb.rect(b_t, b_s)
        for player_entity, (p_t, p_s, p_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagPlayer):
            player_rect = nearest_rect(p_hb.rect(p_t, p_s), pygame.Vector2(bullet_rect.center), size)
            if bullet_rect.colliderect(player_rect):
                # Con el escudo activo, la bala se pierde sin hacer daño
                world.delete_entity(bullet_entity)
                kill_player(world, player_entity, player_info["death"], explosion_info)
                break
        if not world.entity_exists(bullet_entity):
            continue
        for enemy_entity, (e_t, e_s, e_v, e_hb, _) in world.get_components(
            CTransform, CSurface, CVelocity, CHitBox, CTagEnemy
        ):
            enemy_rect = nearest_rect(e_hb.rect(e_t, e_s), pygame.Vector2(bullet_rect.center), size)
            if bullet_rect.colliderect(enemy_rect):
                world.delete_entity(bullet_entity)
                world.delete_entity(enemy_entity)
                create_explosion(world, enemy_rect.center, explosion_info, e_v.vel)
                break
