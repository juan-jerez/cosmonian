"""Cuadrícula para buscar rápido qué hay cerca de algo en el mundo (que da la vuelta en los
dos ejes). Cada elemento se guarda en las celdas que toca su rectángulo; una consulta solo mira
las celdas que toca el rectángulo buscado, en lugar de recorrer todos los elementos."""

import math

import pygame


class SpatialGrid:
    def __init__(self, cell_size: float, world_size: pygame.Vector2) -> None:
        # Las celdas se ajustan para que el mundo tenga un número entero de ellas: así la vuelta
        # por un borde cae justo en la primera celda del lado contrario
        self.cols = max(1, round(world_size.x / cell_size))
        self.rows = max(1, round(world_size.y / cell_size))
        self.cell_w = world_size.x / self.cols
        self.cell_h = world_size.y / self.rows
        self.cells: dict[tuple[int, int], list] = {}

    def insert(self, item, center: tuple[float, float], size: tuple[float, float]):
        for cell in self._cells(center, size):
            self.cells.setdefault(cell, []).append(item)

    def query(self, center: tuple[float, float], size: tuple[float, float]) -> list:
        """Elementos que están en las mismas celdas (pueden no tocarse: hay que comprobarlo)."""
        found = []
        seen = set()
        for cell in self._cells(center, size):
            for item in self.cells.get(cell, ()):
                if id(item) not in seen:
                    seen.add(id(item))
                    found.append(item)
        return found

    def _cells(self, center: tuple[float, float], size: tuple[float, float]):
        first_x = math.floor((center[0] - size[0] / 2) / self.cell_w)
        last_x = math.floor((center[0] + size[0] / 2) / self.cell_w)
        first_y = math.floor((center[1] - size[1] / 2) / self.cell_h)
        last_y = math.floor((center[1] + size[1] / 2) / self.cell_h)
        # El módulo hace que lo que asoma por un borde caiga en las celdas del lado contrario
        for cx in range(first_x, last_x + 1):
            for cy in range(first_y, last_y + 1):
                yield (cx % self.cols, cy % self.rows)
