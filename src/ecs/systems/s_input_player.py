from typing import Callable
import pygame
import esper

from src.ecs.components.c_input_command import CInputCommand, CommandPhase, InputType


def system_input_player(
    world: esper.World,
    event: pygame.event.Event,
    do_action: Callable[[CInputCommand], None],
):
    components = world.get_component(CInputCommand)

    for _, c_input in components:
        if c_input.input_type == InputType.KEYBOARD:
            if event.type == pygame.KEYDOWN and c_input.key == event.key:
                c_input.phase = CommandPhase.START
                do_action(c_input)
            elif event.type == pygame.KEYUP and c_input.key == event.key:
                c_input.phase = CommandPhase.END
                do_action(c_input)
        elif c_input.input_type == InputType.MOUSE:
            if event.type == pygame.MOUSEBUTTONDOWN and c_input.key == event.button:
                c_input.phase = CommandPhase.START
                do_action(c_input)
            elif event.type == pygame.MOUSEBUTTONUP and c_input.key == event.button:
                c_input.phase = CommandPhase.END
                do_action(c_input)
        elif c_input.input_type == InputType.JOY_BUTTON:
            if event.type == pygame.JOYBUTTONDOWN and c_input.key == event.button:
                c_input.phase = CommandPhase.START
                do_action(c_input)
            elif event.type == pygame.JOYBUTTONUP and c_input.key == event.button:
                c_input.phase = CommandPhase.END
                do_action(c_input)
        elif c_input.input_type == InputType.JOY_HAT:
            # La cruceta manda su posición entera cada vez que cambia: se compara el eje que toca
            if event.type == pygame.JOYHATMOTION:
                index, sign = c_input.key
                _set_pressed(c_input, event.value[index] == sign, do_action)
        elif c_input.input_type == InputType.JOY_AXIS:
            if event.type == pygame.JOYAXISMOTION and event.axis == c_input.key[0]:
                value = event.value * c_input.key[1]
                if value >= c_input.axis_thresholds["press"]:
                    _set_pressed(c_input, True, do_action)
                elif value <= c_input.axis_thresholds["release"]:
                    _set_pressed(c_input, False, do_action)


def _set_pressed(c_input: CInputCommand, pressed: bool, do_action: Callable[[CInputCommand], None]):
    """La cruceta y el stick no avisan al pulsar y soltar como un botón: se genera el aviso
    solo cuando cambian de estado."""
    if pressed and c_input.phase != CommandPhase.START:
        c_input.phase = CommandPhase.START
        do_action(c_input)
    elif not pressed and c_input.phase == CommandPhase.START:
        c_input.phase = CommandPhase.END
        do_action(c_input)
