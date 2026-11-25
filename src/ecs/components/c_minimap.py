import pygame


class CMinimap:
    def __init__(self, world_size: pygame.Vector2, size: pygame.Vector2, colors_info: dict) -> None:
        # Escala del mundo al minimapa (la misma en ambos ejes para no deformarlo)
        self.scale: float = min(size.x / world_size.x, size.y / world_size.y)
        # En pausa el radar se queda vacío
        self.empty = False
        self.colors = {name: pygame.Color(c["r"], c["g"], c["b"]) for name, c in colors_info.items()}
