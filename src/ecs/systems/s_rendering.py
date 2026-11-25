import math

import pygame
import esper

from src.ecs.components.c_clip import CClip
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_render_layer import CRenderLayer
from src.ecs.components.c_screen_shake import CScreenShake
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_surface import CSurface
from src.ecs.components.tags.c_tag_hidden import CTagHidden
from src.ecs.components.tags.c_tag_ui import CTagUI
from src.ecs.systems.s_camera import camera_offset, camera_rect, camera_viewport, to_pixel
from src.ecs.systems.s_world_wrap import world_size


def system_rendering(world: esper.World, screen: pygame.Surface, show_hitboxes: bool = False):
    # El mundo se desplaza según la cámara y la sacudida de pantalla; la interfaz no
    shake = pygame.Vector2(0, 0)
    for _, c_sh in world.get_component(CScreenShake):
        shake += c_sh.offset
    world_shift = to_pixel(shake) - camera_offset(world)
    view = camera_rect(world)
    view_cx, view_cy = view.center
    # Con cámara, lo que queda fuera de la vista no se dibuja (se descarta con cálculo simple)
    has_camera = view.w > 0
    size = world_size(world)

    def world_pos(pos: pygame.Vector2, w: float, h: float) -> tuple[int, int] | None:
        # El mundo no tiene bordes: cada cosa se dibuja en su copia más cercana a la cámara,
        # a un número exacto de veces el tamaño del mundo de distancia
        dx = pos.x + w / 2 - view_cx
        dy = pos.y + h / 2 - view_cy
        jump_x = jump_y = 0.0
        if size is not None:
            jump_x = -round(dx / size.x) * size.x
            jump_y = -round(dy / size.y) * size.y
        if has_camera and (abs(dx + jump_x) * 2 > view.w + w or abs(dy + jump_y) * 2 > view.h + h):
            return None
        return (
            math.floor(pos.x + jump_x) + int(world_shift.x),
            math.floor(pos.y + jump_y) + int(world_shift.y),
        )

    # Las entidades con CRenderLayer se ordenan por capa (los fondos van detrás)
    layers = {entity: c_rl.layer for entity, c_rl in world.get_component(CRenderLayer)}
    query = sorted(world.get_components(CTransform, CSurface), key=lambda item: layers.get(item[0], 0))
    ui_entities = {entity for entity, _ in world.get_component(CTagUI)}
    hidden = {entity for entity, _ in world.get_component(CTagHidden)}
    query = [item for item in query if item[0] not in hidden]

    # Con cámara, el mundo solo se dibuja dentro de su zona de juego (no sobre el panel lateral)
    screen.set_clip(camera_viewport(world))
    for entity, (c_t, c_s) in query:
        # La interfaz se dibuja al final para que quede siempre encima de los sprites
        if entity in ui_entities:
            continue
        screen_pos = world_pos(c_t.pos, c_s.area.w, c_s.area.h)
        if screen_pos is not None:
            screen.blit(c_s.surf, screen_pos, area=c_s.area)

    # Modo de depuración: rectángulos de colisión encima de cada entidad
    if show_hitboxes:
        for _, (c_t, c_s, c_hb) in world.get_components(CTransform, CSurface, CHitBox):
            rect = c_hb.rect(c_t, c_s)
            top_left = world_pos(pygame.Vector2(rect.topleft), rect.w, rect.h)
            if top_left is not None:
                pygame.draw.rect(screen, (255, 0, 255), (top_left, c_hb.size), 1)
    screen.set_clip(None)

    for entity, (c_t, c_s) in query:
        if entity not in ui_entities:
            continue
        # Un CClip limita la zona de la pantalla en la que puede dibujarse la entidad
        if world.has_component(entity, CClip):
            screen.set_clip(world.component_for_entity(entity, CClip).rect)
        screen.blit(c_s.surf, c_t.pos, area=c_s.area)
        screen.set_clip(None)
