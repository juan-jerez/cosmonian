import asyncio
import sys

import pygame

from src.engine.game_state import GameState
from src.engine.scenes.scene import Scene
from src.engine.service_locator import ServiceLocator
from src.game.attract_scene import AttractInfoScene, AttractScene
from src.game.defeat_scene import DefeatScene
from src.game.editor_scene import EditorScene
from src.game.hiscore_scene import HiScoreScene
from src.game.info_scene import InfoScene
from src.game.intro_scene import IntroScene
from src.game.level_select_scene import LevelSelectScene
from src.game.play_scene import PlayScene
from src.game.title_scene import TitleScene
from src.game.victory_scene import VictoryScene


class GameEngine:
    def __init__(self) -> None:
        configs = ServiceLocator.configs_service
        self.window_cfg = configs.get("assets/cfg/window.json")
        score_cfg = configs.get("assets/cfg/score.json")

        pygame.init()
        pygame.display.set_caption(self.window_cfg["title"])

        # En el navegador (pygbag) el lienzo ya se escala a la página; SCALED solo en escritorio
        self.screen = pygame.display.set_mode(
            (self.window_cfg["size"]["w"], self.window_cfg["size"]["h"]),
            0 if sys.platform == "emscripten" else pygame.SCALED,
        )

        # Mandos abiertos, por su identificador; se añaden y quitan al conectarlos o desconectarlos
        self._joysticks: dict[int, pygame.joystick.JoystickType] = {}
        for index in range(pygame.joystick.get_count()):
            self._open_joystick(index)

        self.is_running = False
        self._clock = pygame.time.Clock()
        self._framerate = self.window_cfg["framerate"]
        self._delta_time = 0
        self._bg_color = pygame.Color(
            self.window_cfg["bg_color"]["r"],
            self.window_cfg["bg_color"]["g"],
            self.window_cfg["bg_color"]["b"],
        )

        # Datos que se comparten entre escenas: récord, ronda, puntaje y vidas
        self.state = GameState(score_cfg, configs.get("assets/cfg/shield.json"))

        self._scenes: dict[str, Scene] = {
            "INTRO": IntroScene(self),
            "TITLE": TitleScene(self),
            "LEVEL_SELECT": LevelSelectScene(self),
            "INSTRUCTIONS": InfoScene(self, "instructions"),
            "CREDITS": InfoScene(self, "credits"),
            "PLAY": PlayScene(self),
            "VICTORY": VictoryScene(self),
            "DEFEAT": DefeatScene(self),
            "HISCORE": HiScoreScene(self),
            "ATTRACT": AttractScene(self),
            "ATTRACT_INFO": AttractInfoScene(self),
            "EDITOR": EditorScene(self),
        }
        self._current_scene: Scene | None = None
        self._scene_name_to_switch: str | None = None

    async def run(self, start_scene_name: str = "INTRO") -> None:
        self.is_running = True
        self.switch_scene(start_scene_name)
        self._handle_switch_scene()
        frame = 0
        while self.is_running:
            self._calculate_time()
            self._process_events()
            self._update()
            self._draw()
            self._handle_switch_scene()
            # Cede el control en cada cuadro; en el navegador (pygbag) es obligatorio
            await asyncio.sleep(0)
            frame += 1
            if frame in (1, 30):
                self._fit_web_canvas()
        self._clean()

    def switch_scene(self, new_scene_name: str):
        # El cambio se hace al terminar el cuadro, para no vaciar el mundo en mitad de un sistema
        self._scene_name_to_switch = new_scene_name

    def _fit_web_canvas(self):
        # pygbag ajusta el lienzo a la proporción que tenga en ese momento; si lo hizo antes de
        # abrirse la ventana, queda con otra proporción y el juego se ve deformado
        if sys.platform == "emscripten":
            import platform  # pylint: disable=import-outside-toplevel

            platform.window.window_resize()

    def _calculate_time(self):
        self._clock.tick(self._framerate)
        self._delta_time = self._clock.get_time() / 1000.0

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.JOYDEVICEADDED:
                self._open_joystick(event.device_index)
            elif event.type == pygame.JOYDEVICEREMOVED:
                self._joysticks.pop(event.instance_id, None)
            else:
                self._current_scene.do_process_events(event)

    def _open_joystick(self, device_index: int):
        # Un mando solo envía eventos mientras está abierto
        joystick = pygame.joystick.Joystick(device_index)
        self._joysticks[joystick.get_instance_id()] = joystick

    def _update(self):
        self._current_scene.simulate(self._delta_time)

    def _draw(self):
        self.screen.fill(self._bg_color)
        self._current_scene.draw(self.screen)
        pygame.display.flip()

    def _handle_switch_scene(self):
        if self._scene_name_to_switch is None:
            return
        if self._current_scene is not None:
            self._current_scene.clean()
        self._current_scene = self._scenes[self._scene_name_to_switch]
        self._scene_name_to_switch = None
        self._current_scene.do_create()

    def _clean(self):
        if self._current_scene is not None:
            self._current_scene.clean()
        pygame.quit()
