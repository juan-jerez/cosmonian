class CBase:
    def __init__(self, vertical: bool, points: int, turrets: int) -> None:
        # Vertical: el núcleo solo es vulnerable a disparos que entran de arriba o de abajo;
        # horizontal: de izquierda o derecha
        self.vertical = vertical
        self.points = points
        # Entidades que forman la base (cuerpo, torretas y núcleo), para borrarlas juntas
        self.parts: list[int] = []
        self.turrets_left = turrets
