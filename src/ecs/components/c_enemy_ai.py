import random
from enum import Enum

import pygame


class CEnemyAI:
    def __init__(
        self, kind: str, enemy_info: dict, steering_info: dict, accuracy: float, max_speed: float
    ) -> None:
        self.kind = kind
        self.points: int = enemy_info["points"]
        # Siempre vuela a esta velocidad; max_force limita cuánto puede girar por segundo
        self.max_speed = max_speed
        self.max_force: float = enemy_info["max_force"]

        behavior = enemy_info["behavior"]
        if behavior == "straight":
            # Tipo E: va recto y no se desvía
            self.state = EnemyState.STRAIGHT
            self.state_time = 0.0
            self.after_chase = EnemyState.STRAIGHT
        else:
            # Tipo I: persigue un rato y luego se va; tipo P: persigue poco y luego vaga al azar
            chase_time = enemy_info["chase_time"]
            self.state = EnemyState.CHASE
            self.state_time = random.uniform(chase_time["min"], chase_time["max"])
            self.after_chase = EnemyState.LEAVE if behavior == "chase_then_leave" else EnemyState.WANDER

        # Dificultad: con poca precisión apunta a un punto más alejado del jugador
        self.deviation: float = (1 - accuracy) * steering_info["deviation"]
        self.aim_interval: float = steering_info["aim_interval"]
        self.aim_timer = 0.0
        self.aim_offset = pygame.Vector2(0, 0)
        # Grados por segundo que puede cambiar su rumbo al vagar
        self.wander_jitter: float = enemy_info.get("wander_jitter", 0)
        # Segundos en los que no choca con las bases (al salir del núcleo de una)
        self.base_grace = 0.0


class EnemyState(Enum):
    CHASE = 0
    LEAVE = 1
    WANDER = 2
    STRAIGHT = 3
