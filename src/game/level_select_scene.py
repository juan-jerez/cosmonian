from src.create.prefab_ui import create_menu
from src.ecs.systems.s_menu import menu_index
from src.game.levels import level_entries
from src.game.menu_scene import MenuScene


class LevelSelectScene(MenuScene):
    def __init__(self, game_engine) -> None:
        super().__init__(game_engine, "level_select")

    def do_create(self):
        super().do_create()
        options = [{"text": level["name"], "action": level["file"]} for level in level_entries()]
        create_menu(self.ecs_world, self._scene_cfg["menu"], options)

    def on_accept(self):
        self._game_engine.state.new_game(menu_index(self.ecs_world))
        self.switch_scene("PLAY")

    def on_back(self):
        self.switch_scene("TITLE")
