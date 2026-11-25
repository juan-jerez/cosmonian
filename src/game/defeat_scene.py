import math

from src.create.prefab_ui import create_text
from src.engine.service_locator import ServiceLocator
from src.game.end_scene import EndScene


class DefeatScene(EndScene):
    """Sin vidas: se puede continuar en la misma ronda (con todas las vidas y sin puntaje)
    durante unos segundos; si no se acepta, se acaba la partida."""

    def __init__(self, game_engine) -> None:
        super().__init__(game_engine, "defeat")

    def do_create(self):
        super().do_create()
        self._time_left: float = self._scene_cfg["countdown"]
        self._count_entity: int | None = None
        self._shown_seconds: int | None = None
        self._show_count()
        ServiceLocator.sounds_service.play(self._scene_cfg["sound"])

    def do_update(self, delta_time: float):
        super().do_update(delta_time)
        self._time_left -= delta_time
        if self._time_left <= 0:
            self.finish_game()
            return
        self._show_count()

    def _show_count(self):
        seconds = math.ceil(self._time_left)
        if seconds == self._shown_seconds:
            return
        self._shown_seconds = seconds
        if self._count_entity is not None:
            self.ecs_world.delete_entity(self._count_entity)
        count_info = self._scene_cfg["count"]
        self._count_entity = create_text(self.ecs_world, count_info, count_info["text"].format(seconds=seconds))

    def on_accept(self):
        self._game_engine.state.continue_game()
        self.switch_scene("PLAY")

    def on_back(self):
        self.finish_game()
