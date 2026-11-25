class CEnemySpawner:
    def __init__(self, enemies_info: dict) -> None:
        # Cada cuánto aparece un enemigo y cuántos puede haber a la vez
        self.interval: float = enemies_info["spawn_interval"]
        self.max_enemies: int = enemies_info["max_enemies"]
        # Peso de cada tipo al elegir al azar cuál aparece
        self.types: dict[str, float] = enemies_info["types"]
        # Dificultad: de 0 (se desvían mucho) a 1 (van directos al jugador)
        self.accuracy: float = enemies_info["accuracy"]
        self.timer = self.interval
        # Los controla la condición de alerta: sin enemigos en VERDE, más rápido en ROJO
        self.active = True
        self.rate = 1.0
        # En ROJO los enemigos nuevos son más rápidos y caben más a la vez
        self.speed = 1.0
        self.max_factor = 1.0
