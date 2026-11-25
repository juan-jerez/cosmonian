class CShield:
    def __init__(self, duration: float, blink_time: float) -> None:
        # Mientras el jugador lo tiene, nada lo mata (y él tampoco destruye nada al chocar)
        self.time_left = duration
        # En los últimos segundos el anillo parpadea para avisar de que se acaba
        self.blink_time = blink_time


class CShieldBubble:
    def __init__(self, owner: int, blink: float) -> None:
        # Anillo que se dibuja alrededor de la nave mientras dura el escudo
        self.owner = owner
        self.blink = blink
        self.blink_timer = blink


class CShieldItem:
    def __init__(self, blink_time: float, blink: float) -> None:
        # Ítem que da una carga de escudo; parpadea cuando le queda poco antes de desaparecer
        self.blink_time = blink_time
        self.blink = blink


class CShieldItemSpawner:
    def __init__(self, item_level_info: dict) -> None:
        # Cada `interval` segundos aparece un ítem con probabilidad `chance` (si no hay otro)
        self.interval: float = item_level_info["interval"]
        self.chance: float = item_level_info["chance"]
        self.timer = self.interval


class CShieldDisplay:
    def __init__(self, hud_info: dict) -> None:
        self.hud_info = hud_info
        self.shown: tuple | None = None
