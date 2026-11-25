import copy

import pygame

from src.create.prefab_creator import (
    create_base,
    create_camera,
    create_world,
    create_world_background,
    directional_surfaces,
)
from src.create.prefab_ui import (
    INTERFACE_CFG,
    color_from_cfg,
    create_input_commands,
    create_menu,
    create_minimap,
    create_text,
)
from src.ecs.components.c_base import CBase
from src.ecs.components.c_camera import CCamera
from src.ecs.components.c_input_command import CInputCommand, CommandPhase
from src.ecs.components.c_lifetime import CLifetime
from src.ecs.components.c_menu import CMenu
from src.ecs.components.c_render_layer import CRenderLayer
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_editor_content import CTagEditorContent
from src.ecs.components.tags.c_tag_editor_options import CTagEditorOptions
from src.ecs.components.tags.c_tag_hidden import CTagHidden
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.components.tags.c_tag_ui import CTagUI
from src.ecs.systems.s_camera import camera_rect
from src.ecs.systems.s_lifetime import system_lifetime
from src.ecs.systems.s_menu import menu_index, menu_move, system_menu
from src.ecs.systems.s_minimap import system_minimap
from src.ecs.systems.s_starfield import system_starfield
from src.ecs.systems.s_world_wrap import wrap_delta
from src.engine.scenes.scene import Scene
from src.engine.service_locator import ServiceLocator
from src.game.levels import level_config, level_entries, round_count

# Opciones del menú del editor, en orden; las cuatro últimas son acciones
OPTIONS = ["LEVEL", "ROUND", "DIFFICULTY", "MUSIC", "TRIPLE", "SHIELD", "SAVE", "LOAD", "PLAY", "BACK"]


class EditorScene(Scene):
    """Editor de niveles. Se entra y se sale con E (o Back/Select en el mando) durante el juego.
    Edita la ronda que se estaba jugando: colocar, borrar y girar bases, mover el punto de
    partida y, en el menú de opciones, cambiar de nivel o ronda, la dificultad, la música, el
    disparo triple y los ítems de escudo; guardar el nivel en su JSON o volver a cargarlo."""

    def do_create(self):
        configs = ServiceLocator.configs_service
        self._interface_cfg = configs.get(INTERFACE_CFG)
        self._cfg = self._interface_cfg["editor"]
        self._base_cfg = configs.get("assets/cfg/base.json")
        self._presets = configs.get("assets/cfg/difficulty.json")["presets"]
        self._state = self._game_engine.state

        self._options_open = False
        self._options_before_event = False
        self._held: set[str] = set()
        self._fast = False
        self._new_orientation = "vertical"
        self._message_entity: int | None = None

        create_input_commands(self.ecs_world, "editor")
        create_input_commands(self.ecs_world, "menu")
        self._create_world()
        self._rebuild()
        music = self._interface_cfg["music"]
        ServiceLocator.sounds_service.play_music(self._level().get("music", music["default_level"]), music["volume"])

    # --- datos editados (viven en la configuración cargada en memoria) ---

    def _level_file(self) -> str:
        return level_entries()[self._state.level_index]["file"]

    def _level(self) -> dict:
        return level_config(self._state.level_index)

    def _round(self) -> dict:
        return self._level()["rounds"][self._state.round_index]

    # --- construcción de la escena ---

    def _create_world(self):
        world_info = self._level()["world"]
        viewport_info = self._interface_cfg["game"]["viewport"]
        self._world_size = pygame.Vector2(world_info["size"]["w"], world_info["size"]["h"])
        create_world(self.ecs_world, world_info)
        create_world_background(self.ecs_world, world_info, viewport_info)
        create_minimap(self.ecs_world, self._world_size)
        camera_entity = create_camera(self.ecs_world, viewport_info)
        self._camera_t = self.ecs_world.component_for_entity(camera_entity, CTransform)
        viewport = self.ecs_world.component_for_entity(camera_entity, CCamera).viewport
        self._viewport = viewport
        spawn = self._level()["player_spawn"]["position"]
        self._camera_t.pos.xy = pygame.Vector2(spawn["x"], spawn["y"]) - pygame.Vector2(viewport.size) / 2
        self._create_cursor()
        system_starfield(self.ecs_world, 0)

    def _create_cursor(self):
        """Mira fija en el centro de la vista: ahí se colocan y se eligen las cosas."""
        cursor_info = self._cfg["cursor"]
        size = cursor_info["size"]
        surface = pygame.Surface((size * 2 + 1, size * 2 + 1), pygame.SRCALPHA)
        color = color_from_cfg(cursor_info["color"])
        pygame.draw.line(surface, color, (0, size), (size * 2, size))
        pygame.draw.line(surface, color, (size, 0), (size, size * 2))
        cursor_entity = self.ecs_world.create_entity()
        self._cursor_entity = cursor_entity
        self.ecs_world.add_component(cursor_entity, CSurface.from_surface(surface))
        self.ecs_world.add_component(
            cursor_entity, CTransform(pygame.Vector2(self._viewport.center) - pygame.Vector2(size, size))
        )
        self.ecs_world.add_component(cursor_entity, CTagUI())

    def _rebuild(self):
        """Rehace las bases, el marcador de inicio y los textos a partir de la ronda editada."""
        for entity, _ in self.ecs_world.get_component(CTagEditorContent):
            self.ecs_world.delete_entity(entity)
        level = self._level()
        round_info = self._round()
        for place_info in round_info["bases"]:
            base_entity = create_base(self.ecs_world, place_info, self._base_cfg, round_info["base_behavior"])
            for entity in [base_entity] + self.ecs_world.component_for_entity(base_entity, CBase).parts:
                self.ecs_world.add_component(entity, CTagEditorContent())

        # Marcador del punto de partida: la nave del jugador (también aparece en el radar)
        spawn = level["player_spawn"]
        surface = directional_surfaces("player")[spawn["direction"]]
        center = pygame.Vector2(spawn["position"]["x"], spawn["position"]["y"])
        marker = self.ecs_world.create_entity()
        self.ecs_world.add_component(marker, CSurface.from_surface(surface))
        self.ecs_world.add_component(marker, CTransform(center - pygame.Vector2(surface.get_size()) / 2))
        self.ecs_world.add_component(marker, CTagPlayer())
        self.ecs_world.add_component(marker, CRenderLayer(2))
        self.ecs_world.add_component(marker, CTagEditorContent())

        values = {
            "level": self._state.level_index + 1,
            "round": self._state.round_index + 1,
            "orientation": self._cfg["orientations"][self._new_orientation],
            "bases": len(round_info["bases"]),
            "difficulty": round_info.get("difficulty", "-"),
            "triple": self._cfg["yes_no"][int(level["triple_shot"])],
            "spawn": f"{spawn['position']['x']},{spawn['position']['y']}",
        }
        texts = [self._cfg["header"], self._cfg["orientation"]] + self._cfg["help"] + self._cfg["sidebar"]
        for text_info in texts:
            text_entity = create_text(self.ecs_world, text_info, text_info["text"].format(**values))
            self.ecs_world.add_component(text_entity, CTagEditorContent())
        system_minimap(self.ecs_world)

    def _message(self, text: str, sound: str):
        # Un mensaje nuevo reemplaza al anterior
        self._clear_message()
        self._message_entity = create_text(self.ecs_world, self._cfg["message"], text)
        self.ecs_world.add_component(self._message_entity, CLifetime(self._cfg["message"]["duration"]))
        ServiceLocator.sounds_service.play(self._cfg["sounds"][sound])

    def _clear_message(self):
        if self._message_entity is not None and self.ecs_world.entity_exists(self._message_entity):
            self.ecs_world.delete_entity(self._message_entity)
        self._message_entity = None

    # --- bucle ---

    def do_process_events(self, event: pygame.event.Event):
        # Abrir o cerrar el menú con una tecla anula lo demás que haga esa misma tecla
        self._options_before_event = self._options_open
        super().do_process_events(event)

    def do_update(self, delta_time: float):
        if not self._options_open:
            direction = pygame.Vector2(0, 0)
            for name, step in (("LEFT", (-1, 0)), ("RIGHT", (1, 0)), ("UP", (0, -1)), ("DOWN", (0, 1))):
                if name in self._held:
                    direction += step
            if direction.length_squared() > 0:
                speed = self._cfg["camera_speed"] * (self._cfg["fast_factor"] if self._fast else 1)
                self._camera_t.pos += direction.normalize() * speed * delta_time
                self._camera_t.pos.xy = (self._camera_t.pos.x % self._world_size.x, self._camera_t.pos.y % self._world_size.y)
        system_starfield(self.ecs_world, delta_time)
        system_minimap(self.ecs_world)
        system_menu(self.ecs_world)
        system_lifetime(self.ecs_world, delta_time)

    def do_action(self, action: CInputCommand):
        if self._options_open != self._options_before_event:
            return
        name = action.name
        if name.startswith("EDITOR_") and name[7:] in ("UP", "DOWN", "LEFT", "RIGHT"):
            if action.phase == CommandPhase.START:
                self._held.add(name[7:])
            else:
                self._held.discard(name[7:])
            if self._options_open and action.phase == CommandPhase.START and name[7:] in ("LEFT", "RIGHT"):
                self._change_option(-1 if name == "EDITOR_LEFT" else 1)
            return
        if name == "EDITOR_FAST":
            self._fast = action.phase == CommandPhase.START
            return
        if action.phase != CommandPhase.START:
            return
        if name == "EDITOR_TOGGLE":
            self.switch_scene("PLAY")
        elif self._options_open:
            self._do_options_action(name)
        elif name == "EDITOR_OPTIONS":
            self._open_options()
        elif name == "EDITOR_PLACE":
            self._place_base()
        elif name == "EDITOR_REMOVE":
            self._remove_base()
        elif name == "EDITOR_ROTATE":
            self._rotate()
        elif name == "EDITOR_SPAWN":
            self._set_spawn()

    # --- edición en el mundo ---

    def _cursor(self) -> pygame.Vector2:
        center = pygame.Vector2(camera_rect(self.ecs_world).center)
        return pygame.Vector2(round(center.x) % self._world_size.x, round(center.y) % self._world_size.y)

    def _distance(self, position: dict, point: pygame.Vector2) -> float:
        return wrap_delta(pygame.Vector2(position["x"], position["y"]) - point, self._world_size).length()

    def _base_under_cursor(self) -> dict | None:
        cursor = self._cursor()
        bases = self._round()["bases"]
        near = [b for b in bases if self._distance(b["position"], cursor) <= self._cfg["select_distance"]]
        return min(near, key=lambda b: self._distance(b["position"], cursor)) if near else None

    def _place_base(self):
        cursor = self._cursor()
        if any(self._distance(b["position"], cursor) < self._cfg["min_base_distance"] for b in self._round()["bases"]):
            self._message("DEMASIADO CERCA DE OTRA BASE", "denied")
            return
        if self._distance(self._level()["player_spawn"]["position"], cursor) < self._cfg["min_spawn_distance"]:
            self._message("DEMASIADO CERCA DEL INICIO", "denied")
            return
        self._round()["bases"].append(
            {"position": {"x": int(cursor.x), "y": int(cursor.y)}, "orientation": self._new_orientation}
        )
        self._rebuild()
        self._message("BASE COLOCADA", "place")

    def _remove_base(self):
        base = self._base_under_cursor()
        if base is None:
            self._message("NO HAY BASE EN LA MIRA", "denied")
            return
        self._round()["bases"].remove(base)
        self._rebuild()
        self._message("BASE BORRADA", "remove")

    def _rotate(self):
        """Gira la base de la mira; si no hay ninguna, cambia la orientación de las nuevas."""
        base = self._base_under_cursor()
        swap = {"vertical": "horizontal", "horizontal": "vertical"}
        if base is not None:
            base["orientation"] = swap[base["orientation"]]
            text = "BASE " + self._cfg["orientations"][base["orientation"]]
        else:
            self._new_orientation = swap[self._new_orientation]
            text = "NUEVAS: " + self._cfg["orientations"][self._new_orientation]
        self._rebuild()
        self._message(text, "place")

    def _set_spawn(self):
        cursor = self._cursor()
        if any(self._distance(b["position"], cursor) < self._cfg["min_spawn_distance"] for b in self._round()["bases"]):
            self._message("DEMASIADO CERCA DE UNA BASE", "denied")
            return
        self._level()["player_spawn"]["position"] = {"x": int(cursor.x), "y": int(cursor.y)}
        self._rebuild()
        self._message("PUNTO DE PARTIDA", "place")

    # --- menú de opciones ---

    def _open_options(self, selected: int = 0):
        self._close_options()
        self._options_open = True
        # Con el menú abierto no se ven la mira ni los mensajes
        self._clear_message()
        self.ecs_world.add_component(self._cursor_entity, CTagHidden())
        before = self._ui_entities()
        play_area = self._interface_cfg["play_area"]
        shade = pygame.Surface((play_area["w"], play_area["h"]), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 210))
        shade_entity = self.ecs_world.create_entity()
        self.ecs_world.add_component(shade_entity, CSurface.from_surface(shade))
        self.ecs_world.add_component(shade_entity, CTransform(pygame.Vector2(0, 0)))
        self.ecs_world.add_component(shade_entity, CTagUI())
        self.ecs_world.add_component(shade_entity, CRenderLayer(-1))
        create_text(self.ecs_world, self._cfg["menu_title"])
        options = [{"text": self._option_text(option), "action": option} for option in OPTIONS]
        create_menu(self.ecs_world, self._cfg["menu"], options)
        for _, c_menu in self.ecs_world.get_component(CMenu):
            c_menu.selected = selected
        for entity in self._ui_entities() - before:
            self.ecs_world.add_component(entity, CTagEditorOptions())
        self.ecs_world.add_component(shade_entity, CTagEditorOptions())

    def _close_options(self):
        self._options_open = False
        if self.ecs_world.has_component(self._cursor_entity, CTagHidden):
            self.ecs_world.remove_component(self._cursor_entity, CTagHidden)
        for entity, _ in self.ecs_world.get_component(CTagEditorOptions):
            self.ecs_world.delete_entity(entity)

    def _ui_entities(self) -> set[int]:
        ui = {entity for entity, _ in self.ecs_world.get_component(CTagUI)}
        return ui | {entity for entity, _ in self.ecs_world.get_component(CMenu)}

    def _option_text(self, option: str) -> str:
        level = self._level()
        yes_no = self._cfg["yes_no"]
        if option == "LEVEL":
            return f"NIVEL: {level_entries()[self._state.level_index]['name'].replace('NIVEL ', '')}"
        if option == "ROUND":
            return f"RONDA: {self._state.round_index + 1} DE {round_count(self._state.level_index)}"
        if option == "DIFFICULTY":
            return f"DIFICULTAD: {self._round().get('difficulty', '-')}"
        if option == "MUSIC":
            name = level.get("music", "").split("/")[-1].removesuffix(".ogg").replace("_", " ").upper()
            return f"MUSICA: {name}"
        if option == "TRIPLE":
            return f"DISPARO TRIPLE: {yes_no[int(level['triple_shot'])]}"
        if option == "SHIELD":
            return f"ITEM ESCUDO: {yes_no[int(level['shield_item']['chance'] > 0)]}"
        return {"SAVE": "GUARDAR", "LOAD": "CARGAR DEL DISCO", "PLAY": "JUGAR", "BACK": "VOLVER"}[option]

    def _change_option(self, step: int):
        """Izquierda o derecha cambian el valor de la opción elegida."""
        option = OPTIONS[menu_index(self.ecs_world)]
        level = self._level()
        if option == "LEVEL":
            self._state.level_index = (self._state.level_index + step) % len(level_entries())
            self._state.round_index = 0
            self.switch_scene("EDITOR")
            return
        if option == "ROUND":
            self._state.round_index = (self._state.round_index + step) % round_count(self._state.level_index)
            self.switch_scene("EDITOR")
            return
        if option == "DIFFICULTY":
            # Aplica a la ronda los ajustes de enemigos, bases y formaciones de esa dificultad
            difficulty = min(10, max(1, self._round().get("difficulty", 1) + step))
            self._round()["difficulty"] = difficulty
            self._round().update(copy.deepcopy(self._presets[difficulty - 1]))
        elif option == "MUSIC":
            music_options = self._cfg["music_options"]
            current = level.get("music", music_options[0])
            index = music_options.index(current) if current in music_options else 0
            level["music"] = music_options[(index + step) % len(music_options)]
            ServiceLocator.sounds_service.play_music(level["music"], self._interface_cfg["music"]["volume"])
        elif option == "TRIPLE":
            level["triple_shot"] = not level["triple_shot"]
        elif option == "SHIELD":
            level["shield_item"]["chance"] = 0.0 if level["shield_item"]["chance"] > 0 else 0.6
        else:
            return
        self._rebuild()
        self._open_options(OPTIONS.index(option))

    def _do_options_action(self, name: str):
        if name == "MENU_UP":
            menu_move(self.ecs_world, -1)
        elif name == "MENU_DOWN":
            menu_move(self.ecs_world, 1)
        elif name in ("MENU_BACK", "EDITOR_OPTIONS"):
            self._close_options()
        elif name == "MENU_ACCEPT":
            option = OPTIONS[menu_index(self.ecs_world)]
            if option == "SAVE":
                ServiceLocator.configs_service.save(self._level_file())
                self._close_options()
                self._message("GUARDADO: " + self._level_file().split("/")[-1].upper(), "save")
            elif option == "LOAD":
                ServiceLocator.configs_service.reload(self._level_file())
                self.switch_scene("EDITOR")
            elif option == "PLAY":
                self.switch_scene("PLAY")
            elif option == "BACK":
                self._close_options()
