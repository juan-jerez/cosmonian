import pygame


class CConditionDisplay:
    def __init__(self, bar_entity: int, center: pygame.Vector2) -> None:
        # Texto de la condición en el panel lateral y la barra de color que tiene detrás
        self.bar_entity = bar_entity
        self.center = center
        self.style: str | None = None
        self.blink_timer = 0.0
        self.blink_on = True
