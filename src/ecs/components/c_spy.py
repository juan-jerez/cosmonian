class CSpy:
    def __init__(self, spy_info: dict) -> None:
        # Puntos según la distancia al jugador cuando se le destruye (más lejos, más puntos)
        self.points_by_distance: list[dict] = spy_info["points_by_distance"]
        # Ya estuvo entero dentro de la pantalla
        self.entered = False
        # Ya rebotó en el borde: la próxima vez que salga de la pantalla, escapa
        self.bounced = False

    def points(self, distance: float) -> int:
        for step in self.points_by_distance:
            if step["max_distance"] is None or distance <= step["max_distance"]:
                return step["points"]
        return self.points_by_distance[-1]["points"]
