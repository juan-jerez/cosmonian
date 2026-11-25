import pygame

from src.create.prefab_intro import create_intro
from src.ecs.systems.s_intro_timeline import intro_finished, system_intro_timeline
from src.ecs.systems.s_slide import system_slide
from src.ecs.systems.s_starfield import system_starfield
from src.ecs.systems.s_wipe import system_wipe
from src.engine.scenes.scene import Scene
from src.engine.service_locator import ServiceLocator


class IntroScene(Scene):
    def do_create(self):
        self._intro_cfg = ServiceLocator.configs_service.get("assets/cfg/interface.json")["intro"]
        create_intro(self.ecs_world, self._intro_cfg, self._game_engine.state.hi_score)
        music = ServiceLocator.configs_service.get("assets/cfg/interface.json")["music"]
        ServiceLocator.sounds_service.play_music(music["menus"], music["volume"])

    def do_process_events(self, event: pygame.event.Event):
        # Cualquier tecla o botón salta la intro
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN):
            self.switch_scene("TITLE")

    def do_update(self, delta_time: float):
        system_intro_timeline(self.ecs_world, delta_time, self._intro_cfg)
        system_starfield(self.ecs_world, delta_time)
        system_wipe(self.ecs_world, delta_time)
        system_slide(self.ecs_world, delta_time)
        if intro_finished(self.ecs_world):
            self.switch_scene("TITLE")
