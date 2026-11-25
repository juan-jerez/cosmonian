class CRenderLayer:
    def __init__(self, layer: int) -> None:
        # Las capas menores se dibujan primero (más al fondo); sin este componente la capa es 0
        self.layer = layer
