from enum import Enum


class CObstacle:
    def __init__(self, kind: "ObstacleKind") -> None:
        self.kind = kind


class ObstacleKind(Enum):
    # Estática; un disparo o un choque la destruye
    ROCK = 0
    # Estática; al destruirse deja una explosión que mata lo que toca
    MINE = 1
    # Se mueve en línea recta y nada la destruye
    HARD_ROCK = 2
