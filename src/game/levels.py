"""Acceso a los niveles y sus rondas. levels.json lista los niveles en orden; el JSON de cada
nivel tiene lo común a todas sus rondas y una lista "rounds" con lo propio de cada una (bases y
dificultad), que se combina con lo común al jugarla."""

from src.engine.service_locator import ServiceLocator

LEVELS_CFG = "assets/cfg/levels.json"


def level_entries() -> list[dict]:
    return ServiceLocator.configs_service.get(LEVELS_CFG)["levels"]


def level_config(level_index: int) -> dict:
    return ServiceLocator.configs_service.get(level_entries()[level_index]["file"])


def round_count(level_index: int) -> int:
    return len(level_config(level_index)["rounds"])


def round_config(level_index: int, round_index: int) -> dict:
    """Configuración completa de una ronda: lo del nivel y, encima, lo de la ronda."""
    level = level_config(level_index)
    merged = {key: value for key, value in level.items() if key != "rounds"}
    merged.update(level["rounds"][round_index])
    return merged


def global_round(level_index: int, round_index: int) -> int:
    """Número de ronda contando desde el principio del juego (el que muestra el panel)."""
    return sum(round_count(i) for i in range(level_index)) + round_index + 1


def next_round(level_index: int, round_index: int) -> tuple[int, int] | None:
    """Ronda siguiente (nivel, ronda); None si era la última del juego."""
    if round_index + 1 < round_count(level_index):
        return level_index, round_index + 1
    if level_index + 1 < len(level_entries()):
        return level_index + 1, 0
    return None
