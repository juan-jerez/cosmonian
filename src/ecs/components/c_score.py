from src.engine.game_state import GameState


class CScore:
    def __init__(self, state: GameState, score_info: dict) -> None:
        # El puntaje y las vidas viven en el estado del juego para pasar de una ronda a otra
        self.state = state
        extra_info = score_info["extra_lives"]
        self.second_extra_life: int = extra_info["second"]
        self.extra_life_every: int = extra_info["every"]
        self.sound_extra_life: str = score_info["sound_extra_life"]
