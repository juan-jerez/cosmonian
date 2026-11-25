import pygame


class ImagesService:
    def __init__(self) -> None:
        self._images: dict[str, pygame.Surface] = {}
        self._regions: dict[tuple[str, tuple[int, int, int, int]], pygame.Surface] = {}
        self._flipped: dict[int, pygame.Surface] = {}

    def get(self, path: str) -> pygame.Surface:
        # Cada imagen se carga del disco una sola vez y se comparte entre entidades
        if path not in self._images:
            self._images[path] = pygame.image.load(path).convert_alpha()
        return self._images[path]

    def get_region(self, path: str, rect: tuple[int, int, int, int]) -> pygame.Surface:
        """Parte de una hoja de sprites (comparte los píxeles con la imagen completa)."""
        key = (path, rect)
        if key not in self._regions:
            self._regions[key] = self.get(path).subsurface(rect)
        return self._regions[key]

    def get_strip(self, path: str, rects: tuple[tuple[int, int, int, int], ...]) -> pygame.Surface:
        """Junta varios recortes de una hoja en una tira horizontal de cuadros del mismo tamaño
        (cada uno centrado en su celda), que es lo que espera el sistema de animación."""
        key = (path, rects)
        if key not in self._regions:
            cell_w = max(r[2] for r in rects)
            cell_h = max(r[3] for r in rects)
            strip = pygame.Surface((cell_w * len(rects), cell_h), pygame.SRCALPHA)
            for i, rect in enumerate(rects):
                strip.blit(
                    self.get(path).subsurface(rect),
                    (i * cell_w + (cell_w - rect[2]) // 2, (cell_h - rect[3]) // 2),
                )
            self._regions[key] = strip
        return self._regions[key]

    def get_flipped(self, surface: pygame.Surface) -> pygame.Surface:
        """Copia reflejada horizontalmente, creada una sola vez por imagen."""
        key = id(surface)
        if key not in self._flipped:
            self._flipped[key] = pygame.transform.flip(surface, True, False)
        return self._flipped[key]
