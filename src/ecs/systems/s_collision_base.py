import pygame
import esper

from src.create.prefab_creator import create_explosion, destroy_base, kill_player
from src.ecs.components.c_base import CBase
from src.ecs.components.c_base_core import CBaseCore
from src.ecs.components.c_base_turret import CBaseTurret, TurretState
from src.ecs.components.c_bullet_direction import CBulletDirection
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_shield import CShield
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.tags.c_tag_base_part import CTagBasePart
from src.ecs.components.tags.c_tag_bullet import CTagBullet
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.systems.s_animation import set_frame
from src.ecs.systems.s_score import add_points, award
from src.ecs.systems.s_world_wrap import nearest_rect, world_size


def system_collision_bullet_base(world: esper.World, base_info: dict, explosion_info: dict):
    """Balas del jugador contra las bases. Una torreta alcanzada queda destruida; el núcleo
    solo cae si está abierto y la bala entra en línea recta por su abertura. Si caen las seis
    torretas o el núcleo, la base estalla entera."""
    size = world_size(world)
    parts = world.get_components(CTransform, CSurface, CHitBox, CTagBasePart)
    bullets = world.get_components(CTransform, CSurface, CHitBox, CBulletDirection, CTagBullet)
    for bullet_entity, (b_t, b_s, b_hb, b_dir, _) in bullets:
        # Pudo chocar ya contra un enemigo en este cuadro
        if not world.entity_exists(bullet_entity):
            continue
        bullet_rect = b_hb.rect(b_t, b_s)
        for part_entity, (p_t, p_s, p_hb, _) in parts:
            if not world.entity_exists(part_entity) or _is_destroyed_turret(world, part_entity):
                continue
            part_rect = nearest_rect(p_hb.rect(p_t, p_s), pygame.Vector2(bullet_rect.center), size)
            if not bullet_rect.colliderect(part_rect):
                continue
            world.delete_entity(bullet_entity)
            if world.has_component(part_entity, CBaseTurret):
                _destroy_turret(world, part_entity, p_s, part_rect.center, base_info, explosion_info)
            else:
                c_core = world.component_for_entity(part_entity, CBaseCore)
                c_base = world.component_for_entity(c_core.base_entity, CBase)
                if c_core.is_open() and _enters_opening(b_dir.direction, c_base.vertical):
                    add_points(world, c_base.points)
                    destroy_base(world, c_core.base_entity, base_info, explosion_info)
            break


def system_collision_player_base(world: esper.World, explosion_info: dict, player_info: dict):
    """Chocar contra una torreta (aunque esté destruida) o contra el núcleo mata al jugador."""
    size = world_size(world)
    for player_entity, (pl_t, pl_s, pl_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagPlayer):
        # Con el escudo activo la nave atraviesa las bases
        if not world.entity_exists(player_entity) or world.has_component(player_entity, CShield):
            continue
        player_rect = pl_hb.rect(pl_t, pl_s)
        for part_entity, (p_t, p_s, p_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagBasePart):
            if not world.entity_exists(part_entity):
                continue
            part_rect = nearest_rect(p_hb.rect(p_t, p_s), pygame.Vector2(player_rect.center), size)
            if player_rect.colliderect(part_rect):
                kill_player(world, player_entity, player_info["death"], explosion_info)
                break


def _is_destroyed_turret(world: esper.World, entity: int) -> bool:
    return (
        world.has_component(entity, CBaseTurret)
        and world.component_for_entity(entity, CBaseTurret).state == TurretState.DESTROYED
    )


def _destroy_turret(
    world: esper.World, turret_entity: int, c_s: CSurface, center, base_info: dict, explosion_info: dict
):
    # Los restos de la torreta se quedan en la base
    c_tur = world.component_for_entity(turret_entity, CBaseTurret)
    c_tur.state = TurretState.DESTROYED
    award(world, turret_entity)
    set_frame(c_s, c_tur.frames["destroyed"])
    create_explosion(world, center, explosion_info)
    c_base = world.component_for_entity(c_tur.base_entity, CBase)
    c_base.turrets_left -= 1
    if c_base.turrets_left == 0:
        add_points(world, c_base.points)
        destroy_base(world, c_tur.base_entity, base_info, explosion_info)


def _enters_opening(direction: int, vertical: bool) -> bool:
    """La abertura del núcleo de una base vertical mira hacia arriba y hacia abajo."""
    return direction in ((0, 4) if vertical else (2, 6))
