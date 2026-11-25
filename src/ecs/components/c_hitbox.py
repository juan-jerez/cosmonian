import pygame

from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform


class CHitBox:
    def __init__(self, size: pygame.Vector2) -> None:
        # Rectángulo de colisión centrado en la entidad, independiente del tamaño de su imagen
        self.size = size

    def rect(self, c_t: CTransform, c_s: CSurface) -> pygame.FRect:
        center = c_t.pos + pygame.Vector2(c_s.area.size) / 2
        return pygame.FRect(center - self.size / 2, self.size)
