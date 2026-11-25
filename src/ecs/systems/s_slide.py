import esper

from src.ecs.components.c_slide import CSlide
from src.ecs.components.c_transform import CTransform


def system_slide(world: esper.World, delta_time: float):
    for entity, (c_t, c_sl) in world.get_components(CTransform, CSlide):
        c_sl.elapsed += delta_time
        t = min(max(c_sl.elapsed - c_sl.delay, 0) / c_sl.duration, 1)
        # Al entrar frena al llegar a su sitio (ease-out); al salir arranca lento y acelera (ease-in)
        eased = t**3 if c_sl.leaving else 1 - (1 - t) ** 3
        c_t.pos.x = c_sl.start_x + (c_sl.target_x - c_sl.start_x) * eased
        if t >= 1:
            if c_sl.leaving:
                world.delete_entity(entity)
            else:
                world.remove_component(entity, CSlide)
