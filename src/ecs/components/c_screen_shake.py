import pygame


class CScreenShake:
    def __init__(self, duration: float, intensity: float) -> None:
        self.duration = duration
        self.intensity = intensity
        self.time_left = duration
        # Desplazamiento que se aplica al dibujar el mundo en este cuadro
        self.offset = pygame.Vector2(0, 0)
