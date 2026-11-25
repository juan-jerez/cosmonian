import pygame


class CExplosionBurst:
    def __init__(self, burst_info: dict, explosion_info: dict) -> None:
        # Explosiones que faltan por crear, una cada `interval` segundos, repartidas al azar
        # dentro de un círculo de radio `radius` alrededor de la entidad
        self.explosions_left: int = burst_info["explosions"]
        self.interval: float = burst_info["interval"]
        self.radius: float = burst_info["radius"]
        self.explosion_info = explosion_info
        self.timer: float = 0
