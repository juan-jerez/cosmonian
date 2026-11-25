class CBulletDirection:
    def __init__(self, direction: int) -> None:
        # Dirección en que se disparó (src/ecs/utils/directions.py); su velocidad no basta para
        # saberlo porque incluye la de la nave
        self.direction = direction
