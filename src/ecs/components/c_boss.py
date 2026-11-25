import random
from enum import Enum

import pygame


class CBoss:
    def __init__(self, boss_info: dict, max_speed: float, flash_surfaces: list[pygame.Surface]) -> None:
        self.max_hp: int = boss_info["hp"]
        self.hp = self.max_hp
        self.points: int = boss_info["points"]
        # Se acerca despacio al jugador; max_force limita cuánto gira por segundo
        self.max_speed = max_speed
        self.max_force: float = boss_info["max_force"]
        self.move_time: dict = boss_info["move_time"]
        self.attack_weights: dict[str, float] = boss_info["attack_weights"]
        self.state = BossState.MOVE
        self.timer = self.random_move_time()
        # Rumbo actual (para lanzar la bala perseguidora y las alineaciones)
        self.heading = pygame.Vector2(0, 1)
        # Ataque cargado: anillos de balas que faltan por lanzar
        self.rings_left = 0
        # Imágenes en blanco para parpadear al recibir un golpe o mientras carga
        self.flash_surfaces = flash_surfaces
        self.normal_surfaces: list[pygame.Surface] = []
        self.flash_timer = 0.0

    def random_move_time(self) -> float:
        return random.uniform(self.move_time["min"], self.move_time["max"])


class BossState(Enum):
    # Se acerca al jugador hasta que toca atacar
    MOVE = 0
    # Quieto mientras carga el ataque en todas direcciones
    CHARGE = 1
    # Quieto mientras lanza los anillos de balas
    FIRE = 2


class CHomingShot:
    def __init__(self, homing_info: dict, max_speed: float) -> None:
        # Bala que persigue al jugador y aguanta varios disparos
        self.hp: int = homing_info["hp"]
        self.points: int = homing_info["points"]
        self.max_speed = max_speed
        self.max_force: float = homing_info["max_force"]
        self.hit_sound: str = homing_info["hit_sound"]


class CBossBar:
    def __init__(self, rect: pygame.Rect, colors: dict) -> None:
        # Barra de vida del jefe en la parte superior de la pantalla
        self.rect = rect
        self.colors = colors
        self.shown: int | None = None
