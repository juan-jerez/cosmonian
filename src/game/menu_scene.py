from src.create.prefab_ui import (
    INTERFACE_CFG,
    create_input_commands,
    create_menu_starfield,
    create_radar,
    create_sidebar,
    create_text,
)
from src.ecs.components.c_input_command import CInputCommand, CommandPhase
from src.ecs.systems.s_blink import system_blink
from src.ecs.systems.s_menu import menu_move, system_menu
from src.ecs.systems.s_starfield import system_starfield
from src.engine.scenes.scene import Scene
from src.engine.service_locator import ServiceLocator


class MenuScene(Scene):
    """Base de las escenas fuera del juego: estrellas que caen, panel lateral en reposo y
    textos de la configuración. Las subclases añaden su menú y deciden qué hace cada opción."""

    def __init__(self, game_engine, cfg_key: str) -> None:
        super().__init__(game_engine)
        self._cfg_key = cfg_key

    def do_create(self):
        self._interface_cfg = ServiceLocator.configs_service.get(INTERFACE_CFG)
        self._scene_cfg = self._interface_cfg[self._cfg_key]
        create_menu_starfield(self.ecs_world)
        create_sidebar(self.ecs_world, self._game_engine.state.hi_score, self.sidebar_score(), 1)
        create_radar(self.ecs_world)
        values = self.text_values()
        for text_info in self._scene_cfg.get("texts", []):
            create_text(self.ecs_world, text_info, text_info["text"].format(**values))
        create_input_commands(self.ecs_world, "menu")
        self.start_music()

    def do_update(self, delta_time: float):
        system_starfield(self.ecs_world, delta_time)
        system_menu(self.ecs_world)
        system_blink(self.ecs_world, delta_time)

    def do_action(self, action: CInputCommand):
        if action.phase != CommandPhase.START:
            return
        if action.name == "MENU_UP":
            menu_move(self.ecs_world, -1)
        elif action.name == "MENU_DOWN":
            menu_move(self.ecs_world, 1)
        elif action.name == "MENU_ACCEPT":
            ServiceLocator.sounds_service.play(self._interface_cfg["menu_style"]["sound_accept"])
            self.on_accept()
        elif action.name == "MENU_BACK":
            self.on_back()

    def start_music(self):
        """Música de los menús (las escenas de fin de partida la detienen)."""
        music = self._interface_cfg["music"]
        ServiceLocator.sounds_service.play_music(music["menus"], music["volume"])

    def sidebar_score(self) -> int:
        """Puntaje del 1UP; fuera del juego es 0."""
        return 0

    def text_values(self) -> dict:
        """Valores para los textos de la configuración que tienen marcas como {score}."""
        return {}

    def on_accept(self):
        pass

    def on_back(self):
        pass
