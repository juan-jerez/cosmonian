import pygame


class CDirectionalSprite:
    def __init__(self, surfaces: list[pygame.Surface], index: int) -> None:
        # Una imagen por cada una de las ocho direcciones (src/ecs/utils/directions.py)
        self.surfaces = surfaces
        self.index = index
