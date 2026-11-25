class CWarp:
    def __init__(self, duration: float, speed: float) -> None:
        # Las estrellas pasan muy rápido y van frenando: la nave parece despegar
        self.duration = duration
        self.speed = speed
        self.elapsed = 0.0
