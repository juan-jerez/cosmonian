"""Las ocho direcciones de movimiento, numeradas en el sentido de las agujas del reloj
empezando por arriba: 0 arriba, 1 arriba-derecha, 2 derecha... 7 arriba-izquierda."""

import math

import pygame

DIRECTIONS = [pygame.Vector2(0, -1).rotate(45 * i) for i in range(8)]


def direction_index(vector: pygame.Vector2) -> int:
    """Dirección más cercana a un vector (que no debe ser nulo)."""
    # atan2 con (x, -y) da el ángulo desde arriba, en el sentido de las agujas del reloj
    angle = math.degrees(math.atan2(vector.x, -vector.y))
    return round(angle / 45) % 8


def turn_step(current: int, target: int) -> int:
    """Paso (+1 o -1) para girar de una dirección a otra por el camino más corto."""
    diff = (target - current) % 8
    return 1 if diff <= 4 else -1
