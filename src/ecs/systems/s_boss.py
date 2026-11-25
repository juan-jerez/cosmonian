import random

import pygame
import esper

from src.create.prefab_creator import (
    create_enemy_bullet,
    create_explosion,
    create_formation,
    create_homing_shot,
    destroy_boss,
    kill_player,
)
from src.ecs.components.c_boss import BossState, CBoss, CBossBar, CHomingShot
from src.ecs.components.c_directional_sprite import CDirectionalSprite
from src.ecs.components.c_formation import CFormation
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_bullet import CTagBullet
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_score import add_points
from src.ecs.systems.s_world_wrap import boxes_overlap, world_size, wrap_delta
from src.ecs.utils.steering import apply_steering, seek
from src.engine.service_locator import ServiceLocator


def system_boss(
    world: esper.World,
    delta_time: float,
    boss_info: dict,
    enemies_info: dict,
    formations_info: dict,
    player_max_speed: float,
):
    """El jefe se acerca despacio al jugador y, cada cierto tiempo, ataca:
    - "burst": se queda quieto 2 s cargando (parpadea) y lanza anillos de balas en todas direcciones.
    - "homing": lanza una bala que persigue al jugador y aguanta varios disparos.
    - "formations": despliega dos alineaciones, una a cada lado."""
    player_center = _player_center(world)
    size = world_size(world)
    for _, (c_t, c_s, c_v, c_ds, c_boss) in world.get_components(
        CTransform, CSurface, CVelocity, CDirectionalSprite, CBoss
    ):
        center = c_t.pos + pygame.Vector2(c_s.area.size) / 2
        to_player = None if player_center is None else wrap_delta(player_center - center, size)
        c_boss.timer -= delta_time

        if c_boss.state == BossState.MOVE:
            if to_player is not None:
                desired = seek(to_player, c_boss.max_speed)
                c_v.vel = apply_steering(c_v.vel, desired, c_boss.max_force, c_boss.max_speed, delta_time)
            if c_v.vel.length_squared() > 0:
                c_boss.heading = c_v.vel.normalize()
            if c_boss.timer <= 0 and to_player is not None:
                _start_attack(world, c_boss, c_v, center, boss_info, enemies_info, formations_info, player_max_speed)
        elif c_boss.state == BossState.CHARGE:
            c_v.vel.xy = (0, 0)
            if c_boss.timer <= 0:
                c_boss.state = BossState.FIRE
                c_boss.rings_left = boss_info["burst"]["rings"]
                c_boss.timer = 0
        elif c_boss.state == BossState.FIRE:
            c_v.vel.xy = (0, 0)
            if c_boss.timer <= 0:
                _fire_ring(world, center, boss_info["burst"], c_boss.rings_left)
                c_boss.rings_left -= 1
                c_boss.timer = boss_info["burst"]["ring_delay"]
                if c_boss.rings_left == 0:
                    c_boss.state = BossState.MOVE
                    c_boss.timer = c_boss.random_move_time()

        # Parpadeo en blanco: al recibir un golpe y, más seguido, mientras carga el ataque
        c_boss.flash_timer = max(0.0, c_boss.flash_timer - delta_time)
        blink = boss_info["flash"]["charge_blink"]
        charging_flash = c_boss.state == BossState.CHARGE and int(c_boss.timer / blink) % 2 == 0
        c_ds.surfaces = c_boss.flash_surfaces if c_boss.flash_timer > 0 or charging_flash else c_boss.normal_surfaces


def _start_attack(
    world: esper.World,
    c_boss: CBoss,
    c_v: CVelocity,
    center: pygame.Vector2,
    boss_info: dict,
    enemies_info: dict,
    formations_info: dict,
    player_max_speed: float,
):
    weights = dict(c_boss.attack_weights)
    # No se despliegan más alineaciones si ya hay demasiadas en juego
    if len(world.get_component(CFormation)) >= boss_info["formations"]["max_active"]:
        weights.pop("formations", None)
    attack = random.choices(list(weights), weights=list(weights.values()))[0]
    c_boss.timer = c_boss.random_move_time()

    if attack == "burst":
        c_boss.state = BossState.CHARGE
        c_boss.timer = boss_info["burst"]["charge_time"]
        c_v.vel.xy = (0, 0)
        ServiceLocator.sounds_service.play(boss_info["burst"]["sound_charge"])
    elif attack == "homing":
        homing_info = boss_info["homing"]
        start = center + c_boss.heading * homing_info["spawn_distance"]
        create_homing_shot(world, start, c_boss.heading, homing_info, player_max_speed)
    else:
        player_center = _player_center(world)
        side = c_boss.heading.rotate(90) * boss_info["formations"]["side_offset"]
        form_info = boss_info["formations"]
        for offset in (side, -side):
            start = center + offset
            direction = wrap_delta(player_center - start, world_size(world))
            if direction.length_squared() == 0:
                direction = c_boss.heading
            shape = random.choices(list(form_info["shapes"]), weights=list(form_info["shapes"].values()))[0]
            kind = random.choices(list(form_info["kinds"]), weights=list(form_info["kinds"].values()))[0]
            create_formation(world, shape, kind, start, direction, formations_info, enemies_info, player_max_speed)
        ServiceLocator.sounds_service.play(formations_info["sound"])


def _fire_ring(world: esper.World, center: pygame.Vector2, burst_info: dict, ring_number: int):
    """Un anillo de balas en todas direcciones; cada anillo va girado medio paso respecto al
    anterior para cubrir los huecos."""
    count = burst_info["bullets_per_ring"]
    step = 360 / count
    offset = step / 2 if ring_number % 2 == 0 else 0
    bullet_info = burst_info["bullet"]
    for i in range(count):
        direction = pygame.Vector2(0, -1).rotate(offset + i * step)
        create_enemy_bullet(world, center + direction * 20, direction * bullet_info["velocity"], bullet_info)
    ServiceLocator.sounds_service.play(burst_info["sound_fire"])


def system_homing_shot(world: esper.World, delta_time: float):
    """La bala perseguidora gira hacia el jugador (steering), sin poder girar de golpe."""
    player_center = _player_center(world)
    if player_center is None:
        return
    size = world_size(world)
    for _, (c_t, c_s, c_v, c_hs) in world.get_components(CTransform, CSurface, CVelocity, CHomingShot):
        to_player = wrap_delta(player_center - (c_t.pos + pygame.Vector2(c_s.area.size) / 2), size)
        c_v.vel = apply_steering(c_v.vel, seek(to_player, c_hs.max_speed), c_hs.max_force, c_hs.max_speed, delta_time)


def system_collision_boss(world: esper.World, boss_info: dict, explosion_info: dict, player_info: dict):
    """Las balas del jugador quitan vida al jefe y a su bala perseguidora; tocar a cualquiera de
    los dos mata al jugador."""
    size = world_size(world)
    targets = [
        (entity, c_hb.rect(c_t, c_s))
        for entity, (c_t, c_s, c_hb) in world.get_components(CTransform, CSurface, CHitBox)
        if world.has_component(entity, CBoss) or world.has_component(entity, CHomingShot)
    ]
    for bullet_entity, (b_t, b_s, b_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagBullet):
        if not world.entity_exists(bullet_entity):
            continue
        bullet_rect = b_hb.rect(b_t, b_s)
        for target, target_rect in targets:
            if not world.entity_exists(target):
                continue
            if boxes_overlap(bullet_rect.center, bullet_rect.size, target_rect.center, target_rect.size, size):
                world.delete_entity(bullet_entity)
                _hit(world, target, bullet_rect.center, boss_info, explosion_info)
                break

    for player_entity, (p_t, p_s, p_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagPlayer):
        player_rect = p_hb.rect(p_t, p_s)
        for target, target_rect in targets:
            if not world.entity_exists(target) or not world.entity_exists(player_entity):
                continue
            if boxes_overlap(player_rect.center, player_rect.size, target_rect.center, target_rect.size, size):
                # La bala perseguidora se gasta al alcanzar al jugador (también contra el escudo)
                if world.has_component(target, CHomingShot):
                    world.delete_entity(target)
                    create_explosion(world, target_rect.center, explosion_info)
                kill_player(world, player_entity, player_info["death"], explosion_info)


def _hit(world: esper.World, target: int, where, boss_info: dict, explosion_info: dict):
    if world.has_component(target, CHomingShot):
        c_hs = world.component_for_entity(target, CHomingShot)
        c_hs.hp -= 1
        if c_hs.hp <= 0:
            add_points(world, c_hs.points)
            create_explosion(world, where, explosion_info, world.component_for_entity(target, CVelocity).vel)
            world.delete_entity(target)
        else:
            ServiceLocator.sounds_service.play(c_hs.hit_sound)
        return
    c_boss = world.component_for_entity(target, CBoss)
    c_boss.hp -= 1
    c_boss.flash_timer = boss_info["flash"]["hit_time"]
    # Chispa en el punto del impacto (sin sonido, para no saturar)
    create_explosion(world, where, explosion_info, sound=False)
    if c_boss.hp <= 0:
        add_points(world, c_boss.points)
        destroy_boss(world, target, boss_info, explosion_info)


def system_boss_bar(world: esper.World):
    """La barra de vida se redibuja solo cuando cambia la vida del jefe."""
    bosses = [c_boss for _, c_boss in world.get_component(CBoss)]
    hp = bosses[0].hp if bosses else 0
    max_hp = bosses[0].max_hp if bosses else 1
    for _, (c_s, c_bar) in world.get_components(CSurface, CBossBar):
        if c_bar.shown == hp:
            continue
        c_bar.shown = hp
        c_s.surf.fill(c_bar.colors["back"])
        fill_w = round((c_bar.rect.w - 2) * max(hp, 0) / max_hp)
        pygame.draw.rect(c_s.surf, c_bar.colors["fill"], (1, 1, fill_w, c_bar.rect.h - 2))
        pygame.draw.rect(c_s.surf, c_bar.colors["border"], c_s.surf.get_rect(), 1)


def _player_center(world: esper.World) -> pygame.Vector2 | None:
    players = world.get_components(CTransform, CSurface, CTagPlayer)
    if not players:
        return None
    p_t, p_s, _ = players[0][1]
    return p_t.pos + pygame.Vector2(p_s.area.size) / 2
