import pygame
import esper

from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_surface import CSurface
from src.ecs.components.tags.c_tag_bullet import CTagBullet
from src.ecs.systems.s_world_wrap import nearest_rect, world_size


def system_screen_bullet(world: esper.World, screen_rect: pygame.FRect):
    query = world.get_components(CTransform, CSurface, CTagBullet)
    size = world_size(world)

    for bullet_entity, (c_t, c_s, _) in query:
        # Se usa la copia de la bala más cercana a la zona visible, por si cruzó un borde del mundo
        bullet_rect = nearest_rect(c_s.get_frect(c_t.pos), pygame.Vector2(screen_rect.center), size)
        if not screen_rect.contains(bullet_rect):
            world.delete_entity(bullet_entity)
