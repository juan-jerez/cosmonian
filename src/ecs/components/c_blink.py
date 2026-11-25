class CBlink:
    def __init__(self, period: float) -> None:
        # Segundos que pasa visible y luego oculta, alternando
        self.period = period
        self.timer = period
