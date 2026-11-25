import pygame


class FontsService:
    def __init__(self) -> None:
        self._fonts: dict[tuple[str, int], pygame.font.Font] = {}

    def get(self, path: str, size: int) -> pygame.font.Font:
        # La misma fuente con otro tamaño es un objeto distinto
        if (path, size) not in self._fonts:
            self._fonts[(path, size)] = pygame.font.Font(path, size)
        return self._fonts[(path, size)]
