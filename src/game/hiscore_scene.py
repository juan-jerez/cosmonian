import random

import pygame

from src.create.prefab_creator import create_explosion
from src.create.prefab_ui import color_from_cfg, create_text, render_text, text_pos
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.systems.s_animation import system_animation
from src.ecs.systems.s_explosion_kill import system_explosion_kill
from src.engine.service_locator import ServiceLocator
from src.game.end_scene import EndScene


class HiScoreScene(EndScene):
    """Celebración del nuevo récord: el título cambia de color y estallan fuegos artificiales."""

    def __init__(self, game_engine) -> None:
        super().__init__(game_engine, "hiscore")

    def do_create(self):
        super().do_create()
        cfg = self._scene_cfg
        score_info = cfg["score"]
        create_text(self.ecs_world, score_info, score_info["text"].format(score=self._game_engine.state.score))
        self._title_entity = create_text(self.ecs_world, cfg["title"])
        self._color_index = 0
        self._color_timer = 0.0
        self._firework_timer = 0.0
        play_area = self._interface_cfg["play_area"]
        self._play_area = pygame.Vector2(play_area["w"], play_area["h"])
        ServiceLocator.sounds_service.play(cfg["sound"])

    def do_update(self, delta_time: float):
        super().do_update(delta_time)
        cfg = self._scene_cfg
        self._color_timer -= delta_time
        if self._color_timer <= 0:
            self._color_timer = cfg["color_time"]
            self._color_index = (self._color_index + 1) % len(cfg["colors"])
            c_s = self.ecs_world.component_for_entity(self._title_entity, CSurface)
            c_s.surf = render_text(cfg["title"], color=color_from_cfg(cfg["colors"][self._color_index]))
            self.ecs_world.component_for_entity(self._title_entity, CTransform).pos.xy = text_pos(cfg["title"], c_s)

        self._firework_timer -= delta_time
        if self._firework_timer <= 0:
            self._firework_timer = cfg["firework_interval"]
            # Fuegos artificiales: explosiones sin sonido repartidas por la zona de juego
            center = (random.uniform(20, self._play_area.x - 20), random.uniform(20, self._play_area.y - 40))
            explosion_info = {"sprite": random.choice(cfg["firework_sprites"]), "framerate": cfg["firework_framerate"]}
            create_explosion(self.ecs_world, center, explosion_info, sound=False)
        system_animation(self.ecs_world, delta_time)
        system_explosion_kill(self.ecs_world)

    def on_accept(self):
        if self.can_continue():
            # El récord ya quedó guardado; la celebración no se repite
            self._game_engine.state.new_record = False
            self.switch_scene("TITLE")

    def on_back(self):
        self.on_accept()
