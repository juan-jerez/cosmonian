import random
from enum import Enum


class CBaseTurret:
    def __init__(self, base_entity: int, turret_info: dict, interval_info: dict) -> None:
        self.base_entity = base_entity
        self.state = TurretState.IDLE
        self.frames: dict[str, int] = turret_info["frames"]
        self.points: int = turret_info["points"]
        # Solo dispara si el jugador está a menos de esta distancia
        self.range: float = turret_info["range"]
        self.open_time: float = turret_info["open_time"]
        self.firing_time: float = turret_info["firing_time"]
        # Cada torreta espera un tiempo al azar entre disparos, así no disparan todas a la vez
        self.interval_min: float = interval_info["min"]
        self.interval_max: float = interval_info["max"]
        self.timer = self.random_interval()

    def random_interval(self) -> float:
        return random.uniform(self.interval_min, self.interval_max)


class TurretState(Enum):
    IDLE = 0
    OPEN = 1
    FIRING = 2
    DESTROYED = 3
