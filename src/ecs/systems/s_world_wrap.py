import pygame
import esper

from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_world import CWorld


def system_world_wrap(world: esper.World):
    size = world_size(world)
    if size is None:
        return
    # Lo que sale por un borde del mundo entra por el contrario: el mundo no tiene fin
    for _, (c_t, c_s, _) in world.get_components(CTransform, CSurface, CVelocity):
        half = pygame.Vector2(c_s.area.size) / 2
        center = c_t.pos + half
        c_t.pos.xy = (center.x % size.x - half.x, center.y % size.y - half.y)


def world_size(world: esper.World) -> pygame.Vector2 | None:
    for _, c_w in world.get_component(CWorld):
        return c_w.size
    return None


def wrap_delta(delta: pygame.Vector2, size: pygame.Vector2 | None) -> pygame.Vector2:
    """Camino más corto entre dos puntos, que puede cruzar el borde del mundo."""
    if size is None:
        return pygame.Vector2(delta)
    return pygame.Vector2(
        (delta.x + size.x / 2) % size.x - size.x / 2,
        (delta.y + size.y / 2) % size.y - size.y / 2,
    )


def nearest_rect(rect: pygame.FRect, point: pygame.Vector2, size: pygame.Vector2 | None) -> pygame.FRect:
    """Copia del rectángulo situada lo más cerca posible del punto, contando el cruce de bordes."""
    center = pygame.Vector2(rect.center)
    return rect.move(point + wrap_delta(center - point, size) - center)


def boxes_overlap(
    a_center: tuple[float, float],
    a_size: tuple[float, float],
    b_center: tuple[float, float],
    b_size: tuple[float, float],
    size: pygame.Vector2 | None,
) -> bool:
    """Si dos rectángulos (dados por centro y tamaño) se tocan, contando el cruce de bordes.
    Solo usa números sueltos: sirve para descartar rápido los pares que están lejos."""
    dx = b_center[0] - a_center[0]
    dy = b_center[1] - a_center[1]
    if size is not None:
        dx = (dx + size.x / 2) % size.x - size.x / 2
        dy = (dy + size.y / 2) % size.y - size.y / 2
    return abs(dx) * 2 < a_size[0] + b_size[0] and abs(dy) * 2 < a_size[1] + b_size[1]
