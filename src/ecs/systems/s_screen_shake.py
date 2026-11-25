import random

import esper

from src.ecs.components.c_screen_shake import CScreenShake


def system_screen_shake(world: esper.World, delta_time: float):
    for shake_entity, c_sh in world.get_component(CScreenShake):
        c_sh.time_left -= delta_time
        if c_sh.time_left <= 0:
            world.delete_entity(shake_entity)
            continue
        # La sacudida pierde fuerza a medida que se acaba
        strength = c_sh.intensity * (c_sh.time_left / c_sh.duration)
        c_sh.offset.xy = (random.uniform(-strength, strength), random.uniform(-strength, strength))
