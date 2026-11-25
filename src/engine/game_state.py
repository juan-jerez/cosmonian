class GameState:
    """Datos que sobreviven al cambio de escena: el récord y la partida en curso."""

    def __init__(self, score_info: dict, shield_info: dict) -> None:
        self._score_info = score_info
        self._shield_info = shield_info
        self.hi_score: int = score_info["default_hi_score"]
        # Modo trampa (tecla T en el juego); se mantiene entre rondas y partidas
        self.cheat = False
        self.new_game(0)

    def new_game(self, level_index: int):
        """Partida nueva desde la primera ronda de un nivel."""
        self.level_index = level_index
        self.round_index = 0
        self.score = 0
        # Vidas de reserva: con 0 se sigue jugando la última (4 vidas en total)
        self.lives: int = self._score_info["lives"] - 1
        extra_info = self._score_info["extra_lives"]
        self.next_extra_life: int = extra_info["first"]
        # Para la escena de victoria
        self.lives_lost = 0
        self.continues = 0
        # Si en esta partida se superó el récord (para la escena de celebración)
        self.new_record = False
        # Cargas del escudo (tecla X); se consiguen con ítems y se conservan entre vidas y rondas
        self.shield_charges: int = self._shield_info["start_charges"]

    def continue_game(self):
        """Continuar tras perder: se recuperan todas las vidas y se pierde todo el puntaje."""
        self.score = 0
        self.lives = self._score_info["lives"] - 1
        self.next_extra_life = self._score_info["extra_lives"]["first"]
        self.shield_charges = self._shield_info["start_charges"]
        self.continues += 1
