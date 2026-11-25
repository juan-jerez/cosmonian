import esper

from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_wipe import CWipe


def system_wipe(world: esper.World, delta_time: float):
    for entity, (c_t, c_s, c_w) in world.get_components(CTransform, CSurface, CWipe):
        c_w.elapsed += delta_time
        t = min(c_w.elapsed / c_w.duration, 1)
        shown = 1 - t if c_w.closing else t
        full_h = c_s.surf.get_height()
        visible_h = round(full_h * shown)
        # Se dibuja solo la franja central, que crece (o se encoge) hacia arriba y hacia abajo
        top = (full_h - visible_h) // 2
        c_s.area.update(0, top, c_s.surf.get_width(), visible_h)
        c_t.pos.y = c_w.origin_y + top
        if t >= 1:
            if c_w.closing:
                world.delete_entity(entity)
            else:
                world.remove_component(entity, CWipe)
