import pygame
import esper

from src.create.prefab_ui import render_text, text_pos
from src.ecs.components.c_formation import CFormation, CFormationMember
from src.ecs.components.c_points import CPoints
from src.ecs.components.c_score import CScore
from src.ecs.components.c_score_display import CLifeIcon, CScoreDisplay
from src.ecs.components.c_spy import CSpy
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_hidden import CTagHidden
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_world_wrap import world_size, wrap_delta
from src.engine.service_locator import ServiceLocator


def award(world: esper.World, entity: int):
    """Da al jugador los puntos de una entidad que acaba de destruir. El espía vale más cuanto
    más lejos esté del jugador; los miembros de una formación cuentan para el bono de grupo."""
    points = 0
    if world.has_component(entity, CSpy):
        points = world.component_for_entity(entity, CSpy).points(_distance_to_player(world, entity))
    elif world.has_component(entity, CPoints):
        points = world.component_for_entity(entity, CPoints).points
    if world.has_component(entity, CFormationMember):
        formation_entity = world.component_for_entity(entity, CFormationMember).formation_entity
        if world.entity_exists(formation_entity):
            world.component_for_entity(formation_entity, CFormation).killed_by_player += 1
    add_points(world, points)


def add_points(world: esper.World, points: int):
    """Suma puntos; el récord sube a la vez si se supera y se ganan vidas extra a los 50.000,
    a los 100.000 y después cada 100.000."""
    for _, c_sc in world.get_component(CScore):
        state = c_sc.state
        state.score += points
        if state.score > state.hi_score:
            state.hi_score = state.score
            state.new_record = True
        while state.score >= state.next_extra_life:
            state.lives += 1
            ServiceLocator.sounds_service.play(c_sc.sound_extra_life)
            if state.next_extra_life < c_sc.second_extra_life:
                state.next_extra_life = c_sc.second_extra_life
            else:
                state.next_extra_life += c_sc.extra_life_every


def system_score_display(world: esper.World, max_icons: int):
    """Actualiza 1UP, HI-SCORE y las vidas del panel (solo vuelve a dibujar lo que cambia)."""
    for _, c_sc in world.get_component(CScore):
        state = c_sc.state
        values = {"score": state.score, "hi_score": state.hi_score, "lives": state.lives}
        for _, (c_t, c_s, c_sd) in world.get_components(CTransform, CSurface, CScoreDisplay):
            value = values[c_sd.field]
            if value == c_sd.shown:
                continue
            c_sd.shown = value
            # El número de vidas solo aparece si no caben todas en los iconos
            text = "" if c_sd.field == "lives" and value <= max_icons else str(value)
            c_s.surf = render_text(c_sd.text_info, text)
            c_s.area = c_s.surf.get_rect()
            c_t.pos.xy = text_pos(c_sd.text_info, c_s)
        for icon_entity, c_li in world.get_component(CLifeIcon):
            hidden = c_li.index >= state.lives
            if hidden and not world.has_component(icon_entity, CTagHidden):
                world.add_component(icon_entity, CTagHidden())
            elif not hidden and world.has_component(icon_entity, CTagHidden):
                world.remove_component(icon_entity, CTagHidden)


def _distance_to_player(world: esper.World, entity: int) -> float:
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    if not players:
        return 0
    p_t, p_s, _ = players[0][1]
    e_t = world.component_for_entity(entity, CTransform)
    e_s = world.component_for_entity(entity, CSurface)
    delta = (e_t.pos + pygame.Vector2(e_s.area.size) / 2) - (p_t.pos + pygame.Vector2(p_s.area.size) / 2)
    return wrap_delta(delta, world_size(world)).length()
