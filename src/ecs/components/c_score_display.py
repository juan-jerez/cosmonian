class CScoreDisplay:
    def __init__(self, field: str, text_info: dict) -> None:
        # "score" (1UP), "hi_score" o "lives" (número de vidas cuando no caben los iconos)
        self.field = field
        self.text_info = text_info
        self.shown: int | None = None


class CLifeIcon:
    def __init__(self, index: int) -> None:
        # Se ve si el jugador tiene más de `index` vidas de reserva
        self.index = index
