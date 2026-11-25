class CSpawnProtection:
    def __init__(self, duration: float, blink: float) -> None:
        # Al reaparecer, la nave es invulnerable un momento (y parpadea) para no morir al instante
        self.time_left = duration
        self.blink = blink
