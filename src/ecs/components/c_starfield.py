import random

import pygame


class CStarfield:
    def __init__(self, area: pygame.Vector2, stars_info: dict) -> None:
        self.star_size: int = stars_info["size"]
        # Segundos que tarda una estrella en apagarse y volver a encenderse (igual para todas)
        self.blink_period: float = stars_info["blink_period"]
        # Fracción del movimiento de la cámara que siguen las estrellas (0: fijas en pantalla);
        # con menos de 1 se mueven más despacio que el mundo y parecen lejanas
        self.parallax: float = stars_info.get("parallax", 0)
        # Píxeles por segundo que bajan las estrellas (en los menús caen de arriba hacia abajo)
        self.fall_speed: float = stars_info.get("fall_speed", 0)
        self.area = area
        # Desplazamiento acumulado de las estrellas y última posición de la cámara vista
        self.scroll = pygame.Vector2(0, 0)
        self.last_camera: pygame.Vector2 | None = None
        # Las capas lejanas son más tenues
        brightness = stars_info.get("brightness", 1)
        # Rango de tonos opcional (por ejemplo, rojizos en el mundo del jefe)
        hue_range = stars_info.get("hue", {"min": 0, "max": 360})
        self.stars = [
            Star(
                pygame.Vector2(random.uniform(0, area.x), random.uniform(0, area.y)),
                _random_color(brightness, hue_range),
                random.random(),
            )
            for _ in range(stars_info["number"])
        ]


class Star:
    def __init__(self, pos: pygame.Vector2, color: pygame.Color, phase: float) -> None:
        self.pos = pos
        self.color = color
        # Punto del ciclo de brillo (0 a 1); al empezar en puntos distintos no brillan a la vez
        self.phase = phase


def _random_color(brightness: float, hue_range: dict) -> pygame.Color:
    color = pygame.Color(0, 0, 0)
    hue = random.uniform(hue_range["min"], hue_range["max"]) % 360
    color.hsva = (hue, random.uniform(30, 100), 100 * brightness, 100)
    return color
