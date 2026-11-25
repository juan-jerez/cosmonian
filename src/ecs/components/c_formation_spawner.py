class CFormationSpawner:
    def __init__(self, formations_level_info: dict) -> None:
        # Cada cuánto sale una formación de alguna base (solo en AMARILLO o ROJO)
        self.interval: float = formations_level_info["interval"]
        # Pesos de cada figura y de cada tipo de enemigo al elegir al azar
        self.shapes: dict[str, float] = formations_level_info["shapes"]
        self.kinds: dict[str, float] = formations_level_info["kinds"]
        # Segundos hasta la primera formación (por defecto, un intervalo completo)
        self.timer: float = formations_level_info.get("first_delay", self.interval)
        # Para pruebas: también salen en VERDE
        self.ignore_green: bool = formations_level_info.get("ignore_green", False)
