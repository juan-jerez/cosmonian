from enum import Enum


class CInputCommand:
    def __init__(self, name: str, key, input_type: "InputType", axis_thresholds: dict | None = None) -> None:
        self.name = name
        # Tecla o botón (un número); en la cruceta, (eje del hat, sentido); en el stick, (eje, sentido)
        self.key = key
        self.input_type = input_type
        self.phase = CommandPhase.NA
        # Stick: se considera pulsado al pasar de `press` y suelto al bajar de `release`
        # (la diferencia evita que tiemble cerca del límite)
        self.axis_thresholds = axis_thresholds


class CommandPhase(Enum):
    NA = 0
    START = 1
    END = 2


class InputType(Enum):
    KEYBOARD = 0
    MOUSE = 1
    JOY_BUTTON = 2
    JOY_HAT = 3
    JOY_AXIS = 4
