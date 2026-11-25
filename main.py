#!/usr/bin/python3
"""Función Main"""

import asyncio

# pygbag decide qué librerías descargar en el navegador leyendo los imports de main.py,
# así que pygame debe importarse aquí aunque solo se use en otros módulos
import pygame  # pylint: disable=unused-import

from src.engine.game_engine import GameEngine


async def main():
    engine = GameEngine()
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
