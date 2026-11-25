import pygame

from src.create.prefab_ui import create_image, create_menu
from src.ecs.systems.s_menu import menu_action
from src.game.attract_scene import is_any_input
from src.game.menu_scene import MenuScene


class TitleScene(MenuScene):
    def __init__(self, game_engine) -> None:
        super().__init__(game_engine, "title")

    def do_create(self):
        super().do_create()
        # Sin tocar nada durante un rato, empieza el modo atractor
        self._idle_time = 0.0
        create_image(self.ecs_world, self._scene_cfg["logo"])
        create_menu(self.ecs_world, self._scene_cfg["menu"], self._scene_cfg["menu"]["options"])

    def do_process_events(self, event: pygame.event.Event):
        if is_any_input(event):
            self._idle_time = 0.0
        super().do_process_events(event)

    def do_update(self, delta_time: float):
        super().do_update(delta_time)
        self._idle_time += delta_time
        if self._idle_time >= self._interface_cfg["attract"]["idle_time"]:
            self.switch_scene("ATTRACT")

    def on_accept(self):
        action = menu_action(self.ecs_world)
        if action == "PLAY":
            self._game_engine.state.new_game(0)
            self.switch_scene("PLAY")
        elif action == "LEVELS":
            self.switch_scene("LEVEL_SELECT")
        elif action == "INSTRUCTIONS":
            self.switch_scene("INSTRUCTIONS")
        elif action == "CREDITS":
            self.switch_scene("CREDITS")
