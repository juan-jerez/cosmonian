import esper

from src.ecs.components.c_starfield import CStarfield
from src.ecs.components.c_warp import CWarp


def system_warp(world: esper.World, delta_time: float):
    for entity, (c_sf, c_w) in world.get_components(CStarfield, CWarp):
        c_w.elapsed += delta_time
        t = min(c_w.elapsed / c_w.duration, 1)
        # Las capas cercanas pasan más rápido que las lejanas (paralaje); frena con ease-out
        c_sf.fall_speed = c_w.speed * max(c_sf.parallax, 0.1) * (1 - t) ** 2
        if t >= 1:
            c_sf.fall_speed = 0
            world.remove_component(entity, CWarp)
