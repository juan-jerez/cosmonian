import pygame


class CClip:
    def __init__(self, rect: pygame.Rect) -> None:
        # Solo se dibuja la parte de la entidad que queda dentro de este rectángulo
        self.rect = rect
