class CAlertCondition:
    def __init__(self, alert_info: dict) -> None:
        # "GREEN", "YELLOW" o "RED"; todos los niveles empiezan en VERDE
        self.level = "GREEN"
        # Segundos que quedan en VERDE antes de pasar a AMARILLO
        self.green_timer: float = alert_info["green_time"]
        # Al destruir una base se vuelve a VERDE durante este tiempo
        self.base_green_time: float = alert_info["base_green_time"]
        # Si el nivel dura más que esto, pasa a ROJO
        self.red_after: float = alert_info["red_after"]
        self.level_time = 0.0
        # Bases en pie en el cuadro anterior, para notar cuándo cae una
        self.bases_left: int | None = None
        # Los avisa el sistema del espía
        self.spy_visible = False
        self.spy_escaped = False
