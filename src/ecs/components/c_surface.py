import pygame


class CSurface:
    def __init__(self, size: pygame.Vector2, color: pygame.Color) -> None:
        self.surf = pygame.Surface(size)
        self.surf.fill(color)
        # Área de la superficie que se dibuja y que define el tamaño de la entidad
        self.area = self.surf.get_rect()

    @classmethod
    def from_surface(cls, surface: pygame.Surface) -> "CSurface":
        c_surf = cls(pygame.Vector2(0, 0), pygame.Color(0, 0, 0))
        c_surf.surf = surface
        c_surf.area = surface.get_rect()
        return c_surf

    @classmethod
    def from_text(cls, text: str, font: pygame.font.Font, color: pygame.Color) -> "CSurface":
        # Sin antialiasing para que la fuente pixel art se vea nítida
        return cls.from_surface(font.render(text, False, color))

    @staticmethod
    def as_rectangle(size: pygame.Vector2, color: pygame.Color) -> "CSurface":
        return CSurface(size, color)

    def get_frect(self, pos: pygame.Vector2) -> pygame.FRect:
        """Rectángulo de la entidad en pantalla, a partir del área y su posición."""
        return pygame.FRect(pos.x, pos.y, self.area.w, self.area.h)
