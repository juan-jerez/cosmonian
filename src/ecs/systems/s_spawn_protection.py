import esper

from src.ecs.components.c_spawn_protection import CSpawnProtection
from src.ecs.components.tags.c_tag_hidden import CTagHidden


def system_spawn_protection(world: esper.World, delta_time: float):
    for entity, c_sp in world.get_component(CSpawnProtection):
        c_sp.time_left -= delta_time
        if c_sp.time_left <= 0:
            world.remove_component(entity, CSpawnProtection)
            if world.has_component(entity, CTagHidden):
                world.remove_component(entity, CTagHidden)
            continue
        # Parpadea: visible y oculta alternando cada `blink` segundos
        hidden = int(c_sp.time_left / c_sp.blink) % 2 == 1
        if hidden and not world.has_component(entity, CTagHidden):
            world.add_component(entity, CTagHidden())
        elif not hidden and world.has_component(entity, CTagHidden):
            world.remove_component(entity, CTagHidden)
