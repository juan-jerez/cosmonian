class CLifetime:
    def __init__(self, seconds: float) -> None:
        # Segundos que le quedan a la entidad antes de borrarse
        self.time_left = seconds
