"""Entidades de la intro animada: estrellas, panel con el título y créditos que entran y salen."""

import pygame
import esper

from src.create.prefab_ui import (
    INTERFACE_CFG,
    create_image,
    create_menu_starfield,
    create_radar,
    create_rectangle,
    create_sidebar,
    create_text,
    rect_from_cfg,
)
from src.ecs.components.c_clip import CClip
from src.ecs.components.c_intro_member import CIntroMember
from src.ecs.components.c_intro_timeline import CIntroTimeline
from src.ecs.components.c_render_layer import CRenderLayer
from src.ecs.components.c_slide import CSlide
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_wipe import CWipe
from src.ecs.components.tags.c_tag_ui import CTagUI
from src.engine.service_locator import ServiceLocator


def create_intro(world: esper.World, intro_info: dict, hi_score: int):
    timeline_entity = world.create_entity()
    world.add_component(timeline_entity, CIntroTimeline(intro_info["times"], len(intro_info["credits"])))

    # El panel lateral y las estrellas se mantienen durante toda la intro
    create_sidebar(world, hi_score, 0, 1)
    create_radar(world)
    create_menu_starfield(world)

    # Pantalla 1: estrellas y textos de presentación
    for text_info in intro_info["screen_stars"]:
        _add_to_group(world, create_text(world, text_info), "stars_screen")


def create_intro_credits(world: esper.World, intro_info: dict):
    """Pantalla 2: el panel se abre desde el centro; el título entra por la izquierda y los
    créditos por la derecha, uno tras otro."""
    times = intro_info["times"]
    clip = _play_clip()

    panel_entity = create_rectangle(world, intro_info["panel"]["rect"], intro_info["panel"]["color"])
    world.add_component(panel_entity, CWipe(times["wipe"], rect_from_cfg(intro_info["panel"]["rect"]).y))
    world.add_component(panel_entity, CRenderLayer(-1))
    world.component_for_entity(panel_entity, CSurface).area.h = 0
    _add_to_group(world, panel_entity, "panel")

    title_entity = create_image(world, intro_info["title_image"])
    _add_slide_in(world, title_entity, -clip.w, times["wipe"], times["slide"], clip)
    _add_to_group(world, title_entity, "title")

    for i, text_info in enumerate(intro_info["credits"]):
        credit_entity = create_text(world, text_info)
        _add_slide_in(world, credit_entity, clip.w, times["wipe"] + times["stagger"] * i, times["slide"], clip)
        _add_to_group(world, credit_entity, "credits")


def create_intro_outro(world: esper.World, intro_info: dict):
    """El título sale por la izquierda y los créditos por la derecha."""
    clip = _play_clip()
    for group, offset in (("title", -clip.w), ("credits", clip.w)):
        for entity in _group(world, group):
            c_t = world.component_for_entity(entity, CTransform)
            world.add_component(
                entity, CSlide(c_t.pos.x, c_t.pos.x + offset, 0, intro_info["times"]["slide_out"], leaving=True)
            )


def create_intro_close(world: esper.World, intro_info: dict):
    """El panel se cierra hacia el centro y quedan solo las estrellas."""
    origin_y = rect_from_cfg(intro_info["panel"]["rect"]).y
    for entity in _group(world, "panel"):
        world.add_component(entity, CWipe(intro_info["times"]["wipe"], origin_y, closing=True))


def _play_clip() -> pygame.Rect:
    """Zona de juego: lo que entra o sale de lado no se dibuja fuera de ella."""
    play_area = ServiceLocator.configs_service.get(INTERFACE_CFG)["play_area"]
    return pygame.Rect(0, 0, play_area["w"], play_area["h"])


def _add_to_group(world: esper.World, entity: int, group: str):
    world.add_component(entity, CIntroMember(group))


def _group(world: esper.World, group: str) -> list[int]:
    return [entity for entity, c_member in world.get_component(CIntroMember) if c_member.group == group]


def _add_slide_in(
    world: esper.World, entity: int, offset: float, delay: float, duration: float, clip: pygame.Rect
):
    c_t = world.component_for_entity(entity, CTransform)
    target_x = c_t.pos.x
    c_t.pos.x += offset
    world.add_component(entity, CSlide(c_t.pos.x, target_x, delay, duration))
    # Mientras entra o sale, no debe dibujarse sobre el panel lateral
    world.add_component(entity, CClip(clip))
    if not world.has_component(entity, CTagUI):
        world.add_component(entity, CTagUI())
