class CWipe:
    def __init__(self, duration: float, origin_y: float, closing: bool = False) -> None:
        # La superficie se descubre desde su centro hacia arriba y hacia abajo,
        # o se cierra hacia el centro si closing es verdadero
        self.duration = duration
        self.closing = closing
        self.elapsed: float = 0
        # Posición vertical de la superficie completa; la franja visible se coloca a partir de ella
        self.origin_y = origin_y
