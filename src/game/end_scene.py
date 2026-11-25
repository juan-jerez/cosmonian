from src.create.prefab_ui import create_text
from src.ecs.components.c_blink import CBlink
from src.engine.service_locator import ServiceLocator
from src.game.menu_scene import MenuScene


class EndScene(MenuScene):
    """Base de las escenas de fin de partida (victoria, derrota y récord): un botón lleva a la
    siguiente, pero no antes de `min_time` para no saltarla sin querer."""

    def do_create(self):
        super().do_create()
        self._elapsed = 0.0
        if self._scene_cfg.get("press_button", True):
            press_entity = create_text(self.ecs_world, self._interface_cfg["press_button"])
            self.ecs_world.add_component(press_entity, CBlink(self._interface_cfg["press_blink"]))

    def do_update(self, delta_time: float):
        super().do_update(delta_time)
        self._elapsed += delta_time

    def sidebar_score(self) -> int:
        # El 1UP sigue mostrando el puntaje de la partida que acaba de terminar
        return self._game_engine.state.score

    def start_music(self):
        # Victoria, derrota y récord tienen su propio sonido: sin música de fondo
        ServiceLocator.sounds_service.stop_music()

    def can_continue(self) -> bool:
        return self._elapsed >= self._scene_cfg.get("min_time", 0)

    def finish_game(self):
        """Al terminar la partida, si se superó el récord se celebra antes de volver al título."""
        if self._game_engine.state.new_record:
            self.switch_scene("HISCORE")
        else:
            self.switch_scene("TITLE")
