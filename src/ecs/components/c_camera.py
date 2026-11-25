import pygame


class CCamera:
    def __init__(self, viewport: pygame.Rect) -> None:
        # Zona de la pantalla donde se dibuja el mundo; la posición de la cámara (esquina superior
        # izquierda de lo que se ve, en coordenadas del mundo) está en su CTransform
        self.viewport = viewport
