import pygame
import esper

from src.ecs.components.c_directional_sprite import CDirectionalSprite
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.utils.directions import direction_index


def system_directional_sprite(world: esper.World):
    """Muestra la imagen que corresponde a la dirección en que se mueve cada entidad."""
    query = world.get_components(CTransform, CSurface, CVelocity, CDirectionalSprite)
    for _, (c_t, c_s, c_v, c_ds) in query:
        # Quieta conserva la última dirección
        if c_v.vel.length_squared() > 0:
            c_ds.index = direction_index(c_v.vel)
        set_direction_surface(c_t, c_s, c_ds)


def set_direction_surface(c_t: CTransform, c_s: CSurface, c_ds: CDirectionalSprite):
    surface = c_ds.surfaces[c_ds.index]
    if c_s.surf is surface:
        return
    # Las imágenes giradas miden distinto: se mantiene el centro de la entidad
    center = c_t.pos + pygame.Vector2(c_s.area.size) / 2
    c_s.surf = surface
    c_s.area = surface.get_rect()
    c_t.pos.xy = center - pygame.Vector2(c_s.area.size) / 2
