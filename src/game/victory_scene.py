from src.engine.service_locator import ServiceLocator
from src.game.end_scene import EndScene


class VictoryScene(EndScene):
    """Tras la última ronda: muestra el puntaje, las vidas usadas y las continuaciones."""

    def __init__(self, game_engine) -> None:
        super().__init__(game_engine, "victory")

    def do_create(self):
        super().do_create()
        ServiceLocator.sounds_service.play(self._scene_cfg["sound"])

    def text_values(self) -> dict:
        state = self._game_engine.state
        return {"score": state.score, "lives": state.lives_lost, "continues": state.continues}

    def on_accept(self):
        if self.can_continue():
            self.finish_game()

    def on_back(self):
        self.on_accept()
