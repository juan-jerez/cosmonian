import math

import pygame
import esper

from src.ecs.components.c_camera import CCamera
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_player import CTagPlayer


def system_camera(world: esper.World):
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    if not players:
        return
    _, (pl_t, pl_s, _) = players[0]
    # Se parte del píxel en el que se dibuja el jugador (ver to_pixel), no de su posición con
    # decimales: así la cámara también cae en un píxel exacto y la nave no tiembla en pantalla
    player_center = to_pixel(pl_t.pos) + pygame.Vector2(pl_s.area.w // 2, pl_s.area.h // 2)

    for _, (c_t, c_cam) in world.get_components(CTransform, CCamera):
        # El jugador queda siempre en el centro de la zona de juego
        c_t.pos.xy = player_center - pygame.Vector2(c_cam.viewport.w // 2, c_cam.viewport.h // 2)


def to_pixel(pos: pygame.Vector2) -> pygame.Vector2:
    """Píxel en el que se dibuja una posición del mundo. Todo se redondea igual (hacia abajo),
    así lo que se mueve junto no se separa un píxel y vuelve a juntarse de un cuadro a otro."""
    return pygame.Vector2(math.floor(pos.x), math.floor(pos.y))


def camera_offset(world: esper.World) -> pygame.Vector2:
    """Lo que hay que restar a una posición del mundo para obtener su posición en pantalla."""
    for _, (c_t, c_cam) in world.get_components(CTransform, CCamera):
        return c_t.pos - pygame.Vector2(c_cam.viewport.topleft)
    return pygame.Vector2(0, 0)


def camera_rect(world: esper.World) -> pygame.FRect:
    """Zona del mundo que se ve en pantalla; vacía si no hay cámara."""
    for _, (c_t, c_cam) in world.get_components(CTransform, CCamera):
        return pygame.FRect(c_t.pos, c_cam.viewport.size)
    return pygame.FRect(0, 0, 0, 0)


def camera_viewport(world: esper.World) -> pygame.Rect | None:
    for _, c_cam in world.get_component(CCamera):
        return c_cam.viewport
    return None
