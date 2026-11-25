from typing import TYPE_CHECKING

import pygame
import esper

from src.ecs.components.c_input_command import CInputCommand
from src.ecs.systems.s_input_player import system_input_player
from src.ecs.systems.s_rendering import system_rendering
from src.engine.service_locator import ServiceLocator

if TYPE_CHECKING:
    from src.engine.game_engine import GameEngine


class Scene:
    """Una pantalla del juego (intro, título, nivel...). Cada escena tiene su propio mundo ECS,
    que se vacía al salir de ella."""

    def __init__(self, game_engine: "GameEngine") -> None:
        self.ecs_world = esper.World()
        self._game_engine = game_engine

    def do_process_events(self, event: pygame.event.Event):
        system_input_player(self.ecs_world, event, self.do_action)

    def simulate(self, delta_time: float):
        self.do_update(delta_time)
        self.ecs_world._clear_dead_entities()

    def draw(self, screen: pygame.Surface):
        system_rendering(self.ecs_world, screen)

    def clean(self):
        self.do_clean()
        self.ecs_world.clear_database()
        ServiceLocator.sounds_service.stop_all()

    def switch_scene(self, new_scene_name: str):
        self._game_engine.switch_scene(new_scene_name)

    def do_create(self):
        pass

    def do_update(self, delta_time: float):
        pass

    def do_action(self, action: CInputCommand):
        pass

    def do_clean(self):
        pass
