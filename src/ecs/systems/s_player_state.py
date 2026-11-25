import esper

from src.ecs.components.c_player_state import CPlayerState, PlayerState
from src.ecs.components.c_velocity import CVelocity
from src.engine.service_locator import ServiceLocator


def system_player_state(world: esper.World):
    for _, (c_v, c_pst) in world.get_components(CVelocity, CPlayerState):
        new_state = PlayerState.MOVE if c_v.vel.length_squared() > 0 else PlayerState.IDLE
        if new_state != c_pst.state:
            # El motor suena solo mientras el jugador se mueve
            if new_state == PlayerState.MOVE:
                ServiceLocator.sounds_service.play_loop(c_pst.move_sound, c_pst.move_volume)
            else:
                ServiceLocator.sounds_service.stop(c_pst.move_sound)
            c_pst.state = new_state
