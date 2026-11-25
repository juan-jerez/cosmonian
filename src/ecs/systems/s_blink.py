import esper

from src.ecs.components.c_blink import CBlink
from src.ecs.components.tags.c_tag_hidden import CTagHidden


def system_blink(world: esper.World, delta_time: float):
    for entity, c_bl in world.get_component(CBlink):
        c_bl.timer -= delta_time
        if c_bl.timer > 0:
            continue
        c_bl.timer += c_bl.period
        if world.has_component(entity, CTagHidden):
            world.remove_component(entity, CTagHidden)
        else:
            world.add_component(entity, CTagHidden())
