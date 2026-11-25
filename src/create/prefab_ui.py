"""Entidades de interfaz compartidas por todas las escenas: textos, imágenes, panel lateral,
estrellas, menús y controles."""

import pygame
import esper

from src.ecs.components.c_condition_display import CConditionDisplay
from src.ecs.components.c_input_command import CInputCommand, InputType
from src.ecs.components.c_menu import CMenu, CMenuCursor, CMenuOption
from src.ecs.components.c_minimap import CMinimap
from src.ecs.components.c_render_layer import CRenderLayer
from src.ecs.components.c_score_display import CLifeIcon, CScoreDisplay
from src.ecs.components.c_starfield import CStarfield
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_ui import CTagUI
from src.engine.service_locator import ServiceLocator

INTERFACE_CFG = "assets/cfg/interface.json"
INPUT_CFG = "assets/cfg/input.json"
SPRITES_CFG = "assets/cfg/sprites.json"


def color_from_cfg(color_info: dict) -> pygame.Color:
    return pygame.Color(color_info["r"], color_info["g"], color_info["b"])


def rect_from_cfg(rect_info: dict) -> pygame.Rect:
    return pygame.Rect(rect_info["x"], rect_info["y"], rect_info["w"], rect_info["h"])


def sprite_surface(name: str) -> pygame.Surface:
    """Imagen de un sprite de la hoja, según su recorte en sprites.json."""
    sprite_info = ServiceLocator.configs_service.get(SPRITES_CFG)[name]
    rect = rect_from_cfg(sprite_info["rect"])
    return ServiceLocator.images_service.get_region(sprite_info["image"], tuple(rect))


def sprite_strip(name: str) -> tuple[pygame.Surface, int]:
    """Tira con los cuadros de un sprite animado de sprites.json y su número de cuadros."""
    sprite_info = ServiceLocator.configs_service.get(SPRITES_CFG)[name]
    rects = tuple(tuple(rect_from_cfg(r)) for r in sprite_info["frames"])
    return ServiceLocator.images_service.get_strip(sprite_info["image"], rects), len(rects)


def render_text(text_info: dict, text: str | None = None, color: pygame.Color | None = None) -> pygame.Surface:
    # Lo que no define el texto (fuente, tamaño, color) se toma de text_defaults
    info = {**ServiceLocator.configs_service.get(INTERFACE_CFG)["text_defaults"], **text_info}
    font = ServiceLocator.fonts_service.get(info["font"], info["size"])
    if color is None:
        color = color_from_cfg(info["color"])
    return CSurface.from_text(info["text"] if text is None else text, font, color).surf


def create_text(world: esper.World, text_info: dict, text: str | None = None) -> int:
    """Crea un texto de la interfaz; `text` reemplaza al texto de la configuración."""
    c_surf = CSurface.from_surface(render_text(text_info, text))
    text_entity = world.create_entity()
    world.add_component(text_entity, c_surf)
    world.add_component(text_entity, CTransform(text_pos(text_info, c_surf)))
    world.add_component(text_entity, CTagUI())
    return text_entity


def text_pos(text_info: dict, c_surf: CSurface) -> pygame.Vector2:
    """Esquina superior izquierda del texto. La posición configurada es su centro o, con
    "align": "left" / "right", el punto medio de su borde izquierdo / derecho."""
    x = text_info["position"]["x"]
    align = text_info.get("align", "center")
    if align == "center":
        x -= c_surf.area.w / 2
    elif align == "right":
        x -= c_surf.area.w
    return pygame.Vector2(x, text_info["position"]["y"] - (c_surf.area.h / 2))


def create_image(world: esper.World, image_info: dict) -> int:
    """Imagen de la interfaz centrada en la posición configurada."""
    surface = ServiceLocator.images_service.get(image_info["image"])
    pos = pygame.Vector2(image_info["position"]["x"], image_info["position"]["y"])
    image_entity = world.create_entity()
    world.add_component(image_entity, CSurface.from_surface(surface))
    world.add_component(image_entity, CTransform(pos - pygame.Vector2(surface.get_size()) / 2))
    world.add_component(image_entity, CTagUI())
    return image_entity


def create_rectangle(world: esper.World, rect_info: dict, color_info: dict) -> int:
    rect = rect_from_cfg(rect_info)
    rect_entity = world.create_entity()
    world.add_component(rect_entity, CSurface(pygame.Vector2(rect.size), color_from_cfg(color_info)))
    world.add_component(rect_entity, CTransform(pygame.Vector2(rect.topleft)))
    return rect_entity


def create_sidebar(world: esper.World, hi_score: int, score: int, round_number: int) -> list[int]:
    """Panel derecho: HI-SCORE, 1UP, CONDITION, radar y ROUND. Devuelve las entidades creadas."""
    sidebar_info = ServiceLocator.configs_service.get(INTERFACE_CFG)["sidebar"]
    entities = []
    bar_info = sidebar_info["condition_bar"]
    bar_entity = create_rectangle(world, bar_info["rect"], bar_info["color"])
    # Es interfaz, pero va por detrás del texto de la condición que tiene encima
    world.add_component(bar_entity, CTagUI())
    world.add_component(bar_entity, CRenderLayer(-1))
    entities.append(bar_entity)
    for text_info in sidebar_info["texts"]:
        entities.append(create_text(world, text_info))
    condition_entity = create_text(world, sidebar_info["condition"])
    condition_center = pygame.Vector2(sidebar_info["condition"]["position"]["x"], sidebar_info["condition"]["position"]["y"])
    world.add_component(condition_entity, CConditionDisplay(bar_entity, condition_center))
    entities.append(condition_entity)
    for field, value in (("hi_score", hi_score), ("score", score)):
        # En el juego se actualizan solos (system_score_display)
        text_entity = create_text(world, sidebar_info[field], str(value))
        world.add_component(text_entity, CScoreDisplay(field, sidebar_info[field]))
        entities.append(text_entity)
    entities.append(create_text(world, sidebar_info["round"], str(round_number)))
    return entities


def create_lives_display(world: esper.World, score_info: dict):
    """Iconos de las vidas de reserva bajo el radar y, si no caben, el número total."""
    icons_info = score_info["life_icons"]
    surface = sprite_surface(icons_info["sprite"])
    for i in range(icons_info["max"]):
        icon_entity = world.create_entity()
        world.add_component(icon_entity, CSurface.from_surface(surface))
        x = icons_info["position"]["x"] + i * icons_info["spacing"]
        world.add_component(icon_entity, CTransform(pygame.Vector2(x, icons_info["position"]["y"])))
        world.add_component(icon_entity, CLifeIcon(i))
        world.add_component(icon_entity, CTagUI())
    count_info = ServiceLocator.configs_service.get(INTERFACE_CFG)["sidebar"]["lives_count"]
    count_entity = create_text(world, count_info, "")
    world.add_component(count_entity, CScoreDisplay("lives", count_info))


def create_radar(world: esper.World) -> int:
    """Radar vacío del panel lateral, para las escenas en las que no se juega."""
    radar_info = ServiceLocator.configs_service.get(INTERFACE_CFG)["sidebar"]["radar"]
    radar_entity = create_rectangle(world, radar_info["rect"], radar_info["color"])
    world.add_component(radar_entity, CTagUI())
    return radar_entity


def create_minimap(world: esper.World, world_size: pygame.Vector2) -> int:
    """Radar del panel lateral convertido en minimapa del mundo."""
    interface_info = ServiceLocator.configs_service.get(INTERFACE_CFG)
    radar_rect = rect_from_cfg(interface_info["sidebar"]["radar"]["rect"])
    colors_info = interface_info["game"]["minimap"]["colors"]
    minimap_entity = world.create_entity()
    world.add_component(
        minimap_entity, CSurface(pygame.Vector2(radar_rect.size), color_from_cfg(colors_info["background"]))
    )
    world.add_component(minimap_entity, CTransform(pygame.Vector2(radar_rect.topleft)))
    world.add_component(minimap_entity, CMinimap(world_size, pygame.Vector2(radar_rect.size), colors_info))
    world.add_component(minimap_entity, CTagUI())
    world.add_component(minimap_entity, CRenderLayer(-1))
    return minimap_entity


def create_starfield(world: esper.World, area: pygame.Vector2, stars_info: dict, layer: int = -2) -> int:
    starfield_entity = world.create_entity()
    world.add_component(starfield_entity, CSurface.from_surface(pygame.Surface(area, pygame.SRCALPHA)))
    world.add_component(starfield_entity, CTransform(pygame.Vector2(0, 0)))
    world.add_component(starfield_entity, CStarfield(area, stars_info))
    world.add_component(starfield_entity, CRenderLayer(layer))
    return starfield_entity


def create_menu_starfield(world: esper.World) -> int:
    """Estrellas de los menús: ocupan la zona de juego y caen de arriba hacia abajo."""
    interface_info = ServiceLocator.configs_service.get(INTERFACE_CFG)
    play_area = pygame.Vector2(interface_info["play_area"]["w"], interface_info["play_area"]["h"])
    return create_starfield(world, play_area, interface_info["menu_stars"])


def create_menu(world: esper.World, menu_info: dict, options: list[dict]) -> int:
    """Menú vertical con un cursor; `options` es una lista de {"text", "action"}."""
    style = ServiceLocator.configs_service.get(INTERFACE_CFG)["menu_style"]
    normal = color_from_cfg(style["colors"]["normal"])
    selected = color_from_cfg(style["colors"]["selected"])
    x = menu_info["position"]["x"]
    y = menu_info["position"]["y"]

    for i, option in enumerate(options):
        option_info = {"text": option["text"]}
        surf_normal = render_text(option_info, color=normal)
        option_entity = world.create_entity()
        world.add_component(option_entity, CSurface.from_surface(surf_normal))
        world.add_component(option_entity, CTransform(pygame.Vector2(x, y + i * style["spacing"])))
        world.add_component(
            option_entity, CMenuOption(i, surf_normal, render_text(option_info, color=selected))
        )
        world.add_component(option_entity, CTagUI())

    cursor_info = style["cursor"]
    cursor = pygame.transform.rotate(sprite_surface(cursor_info["sprite"]), cursor_info["angle"])
    cursor_entity = world.create_entity()
    world.add_component(cursor_entity, CSurface.from_surface(cursor))
    world.add_component(cursor_entity, CTransform(pygame.Vector2(0, 0)))
    world.add_component(cursor_entity, CMenuCursor())
    world.add_component(cursor_entity, CTagUI())

    menu_entity = world.create_entity()
    world.add_component(menu_entity, CMenu([o["action"] for o in options], cursor_info["offset_x"]))
    return menu_entity


def create_input_commands(world: esper.World, group: str):
    """Crea un comando por cada tecla o botón del grupo de input.json; varias teclas (y botones
    del mando) pueden activar el mismo comando."""
    input_info = ServiceLocator.configs_service.get(INPUT_CFG)
    for name, keys in input_info[group].items():
        for key_info in keys:
            input_type, key = input_binding(key_info)
            input_entity = world.create_entity()
            world.add_component(input_entity, CInputCommand(name, key, input_type, input_info["axis_thresholds"]))


# Posición de la cruceta: (eje del hat, sentido); en el hat, arriba es +1
_HAT_DIRECTIONS = {"UP": (1, 1), "DOWN": (1, -1), "LEFT": (0, -1), "RIGHT": (0, 1)}


def input_binding(key_info: dict) -> tuple[InputType, object]:
    """Tipo de entrada y tecla/botón de una asignación de input.json."""
    input_type = InputType[key_info["type"]]
    if input_type in (InputType.KEYBOARD, InputType.MOUSE):
        return input_type, getattr(pygame, key_info["key"])
    if input_type == InputType.JOY_BUTTON:
        return input_type, key_info["button"]
    if input_type == InputType.JOY_HAT:
        return input_type, _HAT_DIRECTIONS[key_info["direction"]]
    return input_type, (key_info["axis"], key_info["direction"])
