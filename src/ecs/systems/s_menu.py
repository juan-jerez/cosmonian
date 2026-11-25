import pygame
import esper

from src.ecs.components.c_menu import CMenu, CMenuCursor, CMenuOption
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform


def system_menu(world: esper.World):
    """Resalta la opción elegida y coloca el cursor a su izquierda."""
    for _, c_menu in world.get_component(CMenu):
        selected_center: pygame.Vector2 | None = None
        for _, (c_t, c_s, c_opt) in world.get_components(CTransform, CSurface, CMenuOption):
            is_selected = c_opt.index == c_menu.selected
            c_s.surf = c_opt.surf_selected if is_selected else c_opt.surf_normal
            if is_selected:
                selected_center = pygame.Vector2(c_t.pos.x, c_t.pos.y + c_s.area.h / 2)
        if selected_center is None:
            continue
        for _, (c_t, c_s, _) in world.get_components(CTransform, CSurface, CMenuCursor):
            c_t.pos.xy = (
                selected_center.x - c_menu.cursor_offset_x - c_s.area.w / 2,
                selected_center.y - c_s.area.h / 2,
            )


def menu_move(world: esper.World, step: int):
    """Pasa a la opción siguiente (1) o anterior (-1); al llegar a un extremo da la vuelta."""
    for _, c_menu in world.get_component(CMenu):
        c_menu.selected = (c_menu.selected + step) % len(c_menu.actions)


def menu_action(world: esper.World) -> str | None:
    for _, c_menu in world.get_component(CMenu):
        return c_menu.actions[c_menu.selected]
    return None


def menu_index(world: esper.World) -> int:
    for _, c_menu in world.get_component(CMenu):
        return c_menu.selected
    return 0
