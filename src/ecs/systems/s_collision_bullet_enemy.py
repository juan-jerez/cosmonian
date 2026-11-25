import pygame
import esper

from src.create.prefab_creator import create_explosion
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_bullet import CTagBullet
from src.ecs.components.tags.c_tag_enemy import CTagEnemy
from src.ecs.systems.s_score import award
from src.ecs.systems.s_world_wrap import nearest_rect, world_size


def system_collision_bullet_enemy(world: esper.World, explosion_info: dict):
    bullets = world.get_components(CTransform, CSurface, CHitBox, CTagBullet)
    enemies = world.get_components(CTransform, CSurface, CVelocity, CHitBox, CTagEnemy)
    size = world_size(world)
    killed: set[int] = set()

    for bullet_entity, (b_t, b_s, b_hb, _) in bullets:
        if not world.entity_exists(bullet_entity):
            continue
        bullet_rect = b_hb.rect(b_t, b_s)
        for enemy_entity, (e_t, e_s, e_v, e_hb, _) in enemies:
            if enemy_entity in killed:
                continue
            # Una bala al otro lado del borde del mundo puede estar tocando al enemigo
            enemy_rect = nearest_rect(e_hb.rect(e_t, e_s), pygame.Vector2(bullet_rect.center), size)
            if bullet_rect.colliderect(enemy_rect):
                killed.add(enemy_entity)
                award(world, enemy_entity)
                world.delete_entity(enemy_entity)
                world.delete_entity(bullet_entity)
                # La explosión sigue moviéndose como el enemigo
                create_explosion(world, enemy_rect.center, explosion_info, e_v.vel)
                break
