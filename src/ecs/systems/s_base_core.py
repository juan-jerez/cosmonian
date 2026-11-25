import esper

from src.ecs.components.c_base_core import CBaseCore, CoreState
from src.ecs.components.c_surface import CSurface
from src.ecs.systems.s_animation import set_frame


def system_base_core(world: esper.World, delta_time: float):
    """El núcleo se abre, espera abierto, se cierra y espera cerrado; en algunos niveles está
    siempre abierto."""
    for _, (c_s, c_core) in world.get_components(CSurface, CBaseCore):
        if c_core.mode == "open":
            set_frame(c_s, c_core.frames["open"])
            continue

        c_core.just_opened = False
        c_core.timer -= delta_time
        if c_core.timer <= 0:
            if c_core.state == CoreState.CLOSED:
                c_core.state = CoreState.OPENING
                c_core.timer = c_core.frame_time * 2
            elif c_core.state == CoreState.OPENING:
                c_core.state = CoreState.OPEN
                c_core.timer = c_core.open_time
                c_core.just_opened = True
            elif c_core.state == CoreState.OPEN:
                c_core.state = CoreState.CLOSING
                c_core.timer = c_core.frame_time * 2
            else:
                c_core.state = CoreState.CLOSED
                c_core.timer = c_core.closed_time

        # Al abrirse y cerrarse pasa por los dos cuadros intermedios
        first_half = c_core.timer > c_core.frame_time
        if c_core.state == CoreState.OPEN:
            frame = "open"
        elif c_core.state == CoreState.CLOSED:
            frame = "closed"
        elif c_core.state == CoreState.OPENING:
            frame = "almost_closed" if first_half else "half_open"
        else:
            frame = "half_open" if first_half else "almost_closed"
        set_frame(c_s, c_core.frames[frame])
