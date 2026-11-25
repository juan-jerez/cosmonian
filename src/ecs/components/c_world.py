import pygame


class CWorld:
    def __init__(self, size: pygame.Vector2) -> None:
        # Tamaño del mundo; sus bordes están conectados (al salir por uno se entra por el opuesto)
        self.size = size
