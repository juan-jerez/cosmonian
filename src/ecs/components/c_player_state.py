from enum import Enum


class CPlayerState:
    def __init__(self, move_sound: str, move_volume: float) -> None:
        self.state = PlayerState.IDLE
        # Sonido de motor que suena en bucle mientras el jugador se mueve
        self.move_sound = move_sound
        self.move_volume = move_volume


class PlayerState(Enum):
    IDLE = 0
    MOVE = 1
