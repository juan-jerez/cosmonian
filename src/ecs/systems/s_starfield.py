import pygame
import esper

from src.ecs.components.c_starfield import CStarfield
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.systems.s_camera import camera_rect
from src.ecs.systems.s_world_wrap import world_size, wrap_delta


def system_starfield(world: esper.World, delta_time: float):
    view = camera_rect(world)
    size = world_size(world)
    for _, (c_t, c_s, c_sf) in world.get_components(CTransform, CSurface, CStarfield):
        if view.w > 0:
            # El fondo acompaña a lo que se ve; las estrellas avanzan según cuánto se movió la
            # cámara (no según dónde está), así no saltan cuando el jugador cruza un borde del mundo
            camera = pygame.Vector2(view.topleft)
            c_t.pos.xy = camera
            if c_sf.last_camera is not None:
                c_sf.scroll += wrap_delta(camera - c_sf.last_camera, size) * c_sf.parallax
            c_sf.last_camera = camera
        c_sf.scroll.y -= c_sf.fall_speed * delta_time

        c_s.surf.fill((0, 0, 0, 0))
        for star in c_sf.stars:
            # Todas brillan al mismo ritmo, cada una en su propio punto del ciclo: la
            # transparencia baja de 255 a 0 y vuelve a subir
            star.phase = (star.phase + delta_time / c_sf.blink_period) % 1
            alpha = round(255 * abs(1 - 2 * star.phase))
            if alpha == 0:
                continue
            # Las estrellas se repiten para cubrir siempre toda la zona visible
            x = (star.pos.x - c_sf.scroll.x) % c_sf.area.x
            y = (star.pos.y - c_sf.scroll.y) % c_sf.area.y
            color = (star.color.r, star.color.g, star.color.b, alpha)
            pygame.draw.rect(c_s.surf, color, (x, y, c_sf.star_size, c_sf.star_size))
