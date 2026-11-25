class CSlide:
    def __init__(
        self,
        start_x: float,
        target_x: float,
        delay: float,
        duration: float,
        leaving: bool = False,
    ) -> None:
        self.start_x = start_x
        self.target_x = target_x
        self.delay = delay
        self.duration = duration
        # Al salir de pantalla acelera (en vez de frenar) y la entidad se borra al terminar
        self.leaving = leaving
        self.elapsed: float = 0
