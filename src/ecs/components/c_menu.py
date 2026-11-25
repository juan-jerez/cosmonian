import pygame


class CMenu:
    def __init__(self, actions: list[str], cursor_offset_x: float) -> None:
        # Acción de cada opción, en orden; la escena decide qué hacer con la elegida
        self.actions = actions
        self.selected = 0
        self.cursor_offset_x = cursor_offset_x


class CMenuOption:
    def __init__(self, index: int, surf_normal: pygame.Surface, surf_selected: pygame.Surface) -> None:
        self.index = index
        self.surf_normal = surf_normal
        self.surf_selected = surf_selected


class CMenuCursor:
    pass
