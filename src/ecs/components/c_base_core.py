import random
from enum import Enum


class CBaseCore:
    def __init__(self, base_entity: int, core_info: dict, behavior_info: dict) -> None:
        self.base_entity = base_entity
        self.frames: dict[str, int] = core_info["frames"]
        # Segundos que dura cada cuadro intermedio al abrirse o cerrarse
        self.frame_time: float = core_info["frame_time"]
        # "cycle": se abre y se cierra; "open": siempre abierto
        self.mode: str = behavior_info["core_mode"]
        self.open_time: float = behavior_info["core_open_time"]
        self.closed_time: float = behavior_info["core_closed_time"]
        # Si al abrirse lanza un enemigo tipo E (se añade con los enemigos)
        self.spawn_e: bool = behavior_info["spawn_e"]
        # Se activa en el cuadro en que termina de abrirse (para lanzar un enemigo tipo E)
        self.just_opened = False
        if self.mode == "open":
            self.state = CoreState.OPEN
            self.timer = 0.0
        else:
            # Empiezan desfasados para que no se abran todos los núcleos a la vez
            self.state = CoreState.CLOSED
            self.timer = random.uniform(0, self.closed_time)

    def is_open(self) -> bool:
        return self.state == CoreState.OPEN


class CoreState(Enum):
    CLOSED = 0
    OPENING = 1
    OPEN = 2
    CLOSING = 3
