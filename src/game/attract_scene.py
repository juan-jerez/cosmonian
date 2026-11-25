import pygame

from src.create.prefab_ui import create_text
from src.ecs.components.c_autopilot import CAutopilot
from src.ecs.components.c_blink import CBlink
from src.ecs.systems.s_autopilot import system_autopilot
from src.engine.game_state import GameState
from src.engine.service_locator import ServiceLocator
from src.game.info_scene import InfoScene
from src.game.play_scene import PlayScene


def is_any_input(event: pygame.event.Event) -> bool:
    """Cualquier tecla, clic o botón del mando (o mover la cruceta o el stick a fondo)."""
    if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN):
        return True
    if event.type == pygame.JOYHATMOTION:
        return event.value != (0, 0)
    if event.type == pygame.JOYAXISMOTION:
        return abs(event.value) > 0.5
    return False


class AttractScene(PlayScene):
    """Modo atractor: una ronda que juega sola un piloto automático. Usa su propio estado de
    partida (no toca el puntaje, el récord ni las vidas reales). Termina al pasar un tiempo o
    al morir la nave, y entonces se muestran las instrucciones; cualquier botón vuelve al título."""

    def _game_state(self) -> GameState:
        configs = ServiceLocator.configs_service
        self._attract_cfg = configs.get("assets/cfg/interface.json")["attract"]
        state = GameState(configs.get("assets/cfg/score.json"), configs.get("assets/cfg/shield.json"))
        state.new_game(self._attract_cfg["level"])
        state.round_index = self._attract_cfg["round"]
        # El panel muestra el récord real, pero lo que pase en la demostración no se guarda.
        # La demostración termina poco después de la primera muerte (antes de reaparecer),
        # así que nunca llega a la derrota
        state.hi_score = self._game_engine.state.hi_score
        return state

    def do_create(self):
        super().do_create()
        self._demo_time = self._attract_cfg["demo_time"]
        self._dead_time = 0.0
        for text_info in self._attract_cfg["texts"]:
            text_entity = create_text(self.ecs_world, text_info)
            self.ecs_world.add_component(text_entity, CBlink(self._attract_cfg["blink"]))

    def do_process_events(self, event: pygame.event.Event):
        # Nadie maneja la nave: cualquier botón termina la demostración
        if is_any_input(event):
            self.switch_scene("TITLE")

    def do_update(self, delta_time: float):
        if self._player_alive() and self._cutscene_timer is None:
            # El piloto automático se le pone a la nave en cuanto puede moverse
            if not self.ecs_world.has_component(self._player_entity, CAutopilot):
                self.ecs_world.add_component(self._player_entity, CAutopilot(self._attract_cfg["autopilot"]))
            system_autopilot(self.ecs_world, delta_time, self.bullet_cfg, self.level_cfg["triple_shot"])
        super().do_update(delta_time)

        self._demo_time -= delta_time
        if not self._player_alive():
            self._dead_time += delta_time
        if self._demo_time <= 0 or self._dead_time >= self._attract_cfg["after_death"]:
            self.switch_scene("ATTRACT_INFO")

    def switch_scene(self, new_scene_name: str):
        # Si la demostración superase la ronda o perdiera, no se entra a una partida real
        if new_scene_name not in ("TITLE", "ATTRACT_INFO"):
            new_scene_name = "ATTRACT_INFO"
        super().switch_scene(new_scene_name)


class AttractInfoScene(InfoScene):
    """Instrucciones que siguen a la demostración: vuelven solas al título tras unos segundos,
    o antes si se pulsa cualquier botón."""

    def __init__(self, game_engine) -> None:
        super().__init__(game_engine, "instructions")

    def do_create(self):
        super().do_create()
        self._time_left = self._interface_cfg["attract"]["info_time"]

    def do_process_events(self, event: pygame.event.Event):
        if is_any_input(event):
            self.switch_scene("TITLE")

    def do_update(self, delta_time: float):
        super().do_update(delta_time)
        self._time_left -= delta_time
        if self._time_left <= 0:
            self.switch_scene("TITLE")
