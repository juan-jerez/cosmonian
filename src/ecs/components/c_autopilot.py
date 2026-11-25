class CAutopilot:
    def __init__(self, autopilot_info: dict) -> None:
        # Piloto automático del modo atractor: esquiva, persigue enemigos y ataca bases
        self.avoid_distance: float = autopilot_info["avoid_distance"]
        self.engage_distance: float = autopilot_info["engage_distance"]
        self.orbit_distance: float = autopilot_info["orbit_distance"]
        self.fire_range: float = autopilot_info["fire_range"]
        self.fire_angle: float = autopilot_info["fire_angle"]
        self.fire_interval: float = autopilot_info["fire_interval"]
        self.fire_timer = 0.0
