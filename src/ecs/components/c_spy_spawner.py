class CSpySpawner:
    def __init__(self, spy_level_info: dict) -> None:
        # Segundos entre espías (solo cuentan en AMARILLO o ROJO y sin otro espía en juego)
        self.interval: float = spy_level_info["interval"]
        self.timer = self.interval
