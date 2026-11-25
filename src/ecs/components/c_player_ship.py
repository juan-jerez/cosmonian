class CPlayerShip:
    def __init__(self, ship_info: dict, direction: int) -> None:
        # Dirección actual y la que pide el jugador (índices de src/ecs/utils/directions.py)
        self.direction = direction
        self.target_direction = direction
        # La nave nunca se detiene: arranca en 0 y acelera hasta max_speed al empezar el nivel
        self.speed: float = 0
        self.max_speed: float = ship_info["max_speed"]
        self.acceleration: float = ship_info["acceleration"]
        # Segundos que tarda en girar 45 grados; al cambiar de dirección pasa por las intermedias
        self.turn_time: float = ship_info["turn_time"]
        self.turn_timer: float = 0
