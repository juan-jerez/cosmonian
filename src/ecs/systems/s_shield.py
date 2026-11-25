import random

import pygame
import esper

from src.create.prefab_creator import create_shield_item
from src.create.prefab_ui import color_from_cfg, render_text, text_pos
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_lifetime import CLifetime
from src.ecs.components.c_score import CScore
from src.ecs.components.c_shield import CShield, CShieldBubble, CShieldDisplay, CShieldItem, CShieldItemSpawner
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_hidden import CTagHidden
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_world_wrap import boxes_overlap, world_size
from src.engine.service_locator import ServiceLocator


def system_shield(world: esper.World, delta_time: float):
    """Cuenta el tiempo del escudo y mantiene el anillo centrado en la nave; en los últimos
    segundos el anillo parpadea."""
    for player_entity, c_sh in world.get_component(CShield):
        c_sh.time_left -= delta_time
        if c_sh.time_left <= 0:
            world.remove_component(player_entity, CShield)

    for bubble_entity, (c_t, c_s, c_b) in world.get_components(CTransform, CSurface, CShieldBubble):
        owner = c_b.owner
        if not world.entity_exists(owner) or not world.has_component(owner, CShield):
            world.delete_entity(bubble_entity)
            continue
        o_t = world.component_for_entity(owner, CTransform)
        o_s = world.component_for_entity(owner, CSurface)
        c_t.pos.xy = o_t.pos + pygame.Vector2(o_s.area.size) / 2 - pygame.Vector2(c_s.area.size) / 2
        if world.component_for_entity(owner, CShield).time_left < world.component_for_entity(owner, CShield).blink_time:
            c_b.blink_timer -= delta_time
            if c_b.blink_timer <= 0:
                c_b.blink_timer += c_b.blink
                _toggle_hidden(world, bubble_entity)


def system_shield_item_spawner(world: esper.World, delta_time: float, shield_info: dict):
    """Cada cierto tiempo, con cierta probabilidad, aparece un ítem de escudo a una distancia
    del jugador a la que se puede ir a buscar (se ve en el radar)."""
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    if not players or world.get_component(CShieldItem):
        return
    p_t, p_s, _ = players[0][1]
    player_center = p_t.pos + pygame.Vector2(p_s.area.size) / 2
    size = world_size(world)
    for _, c_sp in world.get_component(CShieldItemSpawner):
        c_sp.timer -= delta_time
        if c_sp.timer > 0:
            continue
        c_sp.timer = c_sp.interval
        if random.random() >= c_sp.chance:
            continue
        distance_info = shield_info["item"]["distance"]
        offset = pygame.Vector2(random.uniform(distance_info["min"], distance_info["max"]), 0)
        center = player_center + offset.rotate(random.uniform(0, 360))
        if size is not None:
            center.xy = (center.x % size.x, center.y % size.y)
        create_shield_item(world, center, shield_info)


def system_shield_item(world: esper.World, delta_time: float, shield_info: dict):
    """El jugador recoge el ítem al tocarlo (una carga más, hasta el máximo); el ítem parpadea
    cuando está a punto de desaparecer."""
    size = world_size(world)
    players = world.get_components(CTransform, CSurface, CHitBox, CTagPlayer)
    for item_entity, (c_t, c_s, c_hb, c_item, c_lt) in world.get_components(
        CTransform, CSurface, CHitBox, CShieldItem, CLifetime
    ):
        if c_lt.time_left < c_item.blink_time:
            # Parpadeo: visible y oculto alternando cada `blink` segundos
            hidden = int(c_lt.time_left / c_item.blink) % 2 == 1
            if hidden != world.has_component(item_entity, CTagHidden):
                _toggle_hidden(world, item_entity)
        item_rect = c_hb.rect(c_t, c_s)
        for _, (p_t, p_s, p_hb, _) in players:
            player_rect = p_hb.rect(p_t, p_s)
            if boxes_overlap(item_rect.center, item_rect.size, player_rect.center, player_rect.size, size):
                for _, c_sc in world.get_component(CScore):
                    c_sc.state.shield_charges = min(shield_info["max_charges"], c_sc.state.shield_charges + 1)
                ServiceLocator.sounds_service.play(shield_info["sounds"]["pickup"])
                world.delete_entity(item_entity)
                break


def system_shield_display(world: esper.World):
    """Texto con las cargas de escudo (o el aviso de que está activo)."""
    active = bool(world.get_component(CShield))
    for _, c_sc in world.get_component(CScore):
        charges = c_sc.state.shield_charges
        for _, (c_t, c_s, c_d) in world.get_components(CTransform, CSurface, CShieldDisplay):
            if c_d.shown == (charges, active):
                continue
            c_d.shown = (charges, active)
            hud = c_d.hud_info
            if active:
                text, color = hud["active_text"], hud["colors"]["active"]
            else:
                text = hud["text"].format(charges=charges)
                color = hud["colors"]["ready" if charges > 0 else "empty"]
            c_s.surf = render_text(hud, text, color_from_cfg(color))
            c_s.area = c_s.surf.get_rect()
            c_t.pos.xy = text_pos(hud, c_s)


def has_shield(world: esper.World, entity: int) -> bool:
    return world.has_component(entity, CShield)


def _toggle_hidden(world: esper.World, entity: int):
    if world.has_component(entity, CTagHidden):
        world.remove_component(entity, CTagHidden)
    else:
        world.add_component(entity, CTagHidden())
