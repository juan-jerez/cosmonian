import pygame
import esper

from src.ecs.components.c_base import CBase
from src.ecs.components.c_boss import CBoss
from src.ecs.components.c_formation import CFormation
from src.ecs.components.c_shield import CShieldItem
from src.ecs.components.c_minimap import CMinimap
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_camera import camera_rect


def system_minimap(world: esper.World):
    for _, (c_s, c_mm) in world.get_components(CSurface, CMinimap):
        colors = c_mm.colors
        c_s.surf.fill(colors["background"])
        if c_mm.empty:
            continue

        # Recuadro con la zona del mundo que se ve en pantalla
        view = camera_rect(world)
        view_rect = pygame.Rect(
            view.x * c_mm.scale, view.y * c_mm.scale, view.w * c_mm.scale, view.h * c_mm.scale
        )
        # Si la zona visible cruza un borde del mundo, el recuadro sigue por el lado contrario
        map_w, map_h = c_s.surf.get_size()
        for dx in (-map_w, 0, map_w):
            for dy in (-map_h, 0, map_h):
                pygame.draw.rect(c_s.surf, colors["view"], view_rect.move(dx, dy), 1)

        # Las bases, como cuadrados en la posición de su núcleo
        for _, (c_t, _) in world.get_components(CTransform, CBase):
            pos = pygame.Vector2(c_t.pos) * c_mm.scale
            pygame.draw.rect(c_s.surf, colors["base"], (pos.x - 2, pos.y - 2, 4, 4))

        # Los ítems de escudo, para poder ir a buscarlos
        for _, (c_t, i_s, _) in world.get_components(CTransform, CSurface, CShieldItem):
            pos = (c_t.pos + pygame.Vector2(i_s.area.size) / 2) * c_mm.scale
            pygame.draw.circle(c_s.surf, colors["item"], pos, 2)

        # El jefe, como un cuadrado grande
        for _, (c_t, b_s, _) in world.get_components(CTransform, CSurface, CBoss):
            pos = (c_t.pos + pygame.Vector2(b_s.area.size) / 2) * c_mm.scale
            pygame.draw.rect(c_s.surf, colors["boss"], (pos.x - 3, pos.y - 3, 7, 7))

        # Las formaciones, como una cruz en el centro del grupo
        for _, (c_t, _) in world.get_components(CTransform, CFormation):
            pos = pygame.Vector2(c_t.pos) * c_mm.scale
            pygame.draw.line(c_s.surf, colors["formation"], pos - (2, 2), pos + (2, 2))
            pygame.draw.line(c_s.surf, colors["formation"], pos + (-2, 2), pos + (2, -2))

        # El jugador se dibuja al final para que quede encima de los enemigos
        for _, (c_t, p_s, _) in world.get_components(CTransform, CSurface, CTagPlayer):
            pygame.draw.circle(c_s.surf, colors["player"], _to_minimap(c_t, p_s, c_mm, c_s, 2.5), 2.5)


def _to_minimap(
    c_t: CTransform, entity_s: CSurface, c_mm: CMinimap, map_s: CSurface, radius: float
) -> pygame.Vector2:
    """Centro de la entidad en el minimapa, ajustado para que el punto quede siempre dentro."""
    pos = pygame.Vector2(entity_s.get_frect(c_t.pos).center) * c_mm.scale
    pos.x = pygame.math.clamp(pos.x, radius, map_s.surf.get_width() - radius)
    pos.y = pygame.math.clamp(pos.y, radius, map_s.surf.get_height() - radius)
    return pos
