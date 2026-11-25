import pygame
import esper

from src.create.prefab_creator import create_explosion, destroy_obstacle, kill_player
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_shield import CShield
from src.ecs.components.c_obstacle import CObstacle, ObstacleKind
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.tags.c_tag_bullet import CTagBullet
from src.ecs.components.tags.c_tag_enemy import CTagEnemy
from src.ecs.components.tags.c_tag_enemy_bullet import CTagEnemyBullet
from src.ecs.components.tags.c_tag_lethal_explosion import CTagLethalExplosion
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.components.tags.c_tag_player_caused import CTagPlayerCaused
from src.ecs.systems.s_score import award
from src.ecs.systems.s_world_wrap import boxes_overlap, nearest_rect, world_size
from src.ecs.utils.spatial_grid import SpatialGrid

# Tamaño de celda de la cuadrícula: algo mayor que el objeto más grande que se compara
CELL_SIZE = 32


def system_collision_obstacle(world: esper.World, obstacles_info: dict, explosion_info: dict, player_info: dict):
    """Choques con rocas, minas y rocas indestructibles. Una bala, el jugador o un enemigo que
    toca una roca o una mina la destruye y muere con ella (la bala desaparece). La roca
    indestructible no se rompe: destruye balas, jugador y enemigos."""
    size = world_size(world)
    # Los obstáculos son muchos: su centro y tamaño se calculan una vez por cuadro
    # y se guardan en una cuadrícula para comparar cada cosa solo con los obstáculos cercanos
    grid = SpatialGrid(CELL_SIZE, size)
    for ob_entity, (o_t, o_s, o_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CObstacle):
        ob_center = o_t.pos + pygame.Vector2(o_s.area.size) / 2
        grid.insert((ob_entity, ob_center, o_hb.size), ob_center, o_hb.size)

    def touching(rect: pygame.FRect):
        for ob_entity, ob_center, ob_size in grid.query(rect.center, rect.size):
            if boxes_overlap(rect.center, rect.size, ob_center, ob_size, size) and world.entity_exists(ob_entity):
                return ob_entity
        return None

    for tag in (CTagBullet, CTagEnemyBullet):
        for bullet_entity, (b_t, b_s, b_hb, _) in world.get_components(CTransform, CSurface, CHitBox, tag):
            if not world.entity_exists(bullet_entity):
                continue
            ob_entity = touching(b_hb.rect(b_t, b_s))
            if ob_entity is not None:
                world.delete_entity(bullet_entity)
                # Solo las balas del jugador le dan puntos
                by_player = tag is CTagBullet
                if by_player:
                    award(world, ob_entity)
                destroy_obstacle(world, ob_entity, obstacles_info, explosion_info, by_player)

    for player_entity, (p_t, p_s, p_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagPlayer):
        # Con el escudo activo la nave atraviesa rocas y minas sin romperlas
        if not world.entity_exists(player_entity) or world.has_component(player_entity, CShield):
            continue
        ob_entity = touching(p_hb.rect(p_t, p_s))
        if ob_entity is not None:
            award(world, ob_entity)
            destroy_obstacle(world, ob_entity, obstacles_info, explosion_info, by_player=True)
            kill_player(world, player_entity, player_info["death"], explosion_info)

    for enemy_entity, (e_t, e_s, e_v, e_hb, _) in world.get_components(
        CTransform, CSurface, CVelocity, CHitBox, CTagEnemy
    ):
        if not world.entity_exists(enemy_entity):
            continue
        enemy_rect = e_hb.rect(e_t, e_s)
        ob_entity = touching(enemy_rect)
        if ob_entity is not None:
            destroy_obstacle(world, ob_entity, obstacles_info, explosion_info)
            world.delete_entity(enemy_entity)
            create_explosion(world, enemy_rect.center, explosion_info, e_v.vel)

    _lethal_explosions(world, obstacles_info, explosion_info, player_info)


def _lethal_explosions(world: esper.World, obstacles_info: dict, explosion_info: dict, player_info: dict):
    """La explosión de una mina mata al jugador y a los enemigos que alcanza, y hace estallar
    las minas cercanas (reacción en cadena)."""
    size = world_size(world)
    for blast_entity, (x_t, x_s, x_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagLethalExplosion):
        blast = x_hb.rect(x_t, x_s)
        by_player = world.has_component(blast_entity, CTagPlayerCaused)

        def hit(entity_t: CTransform, entity_s: CSurface, entity_hb: CHitBox) -> bool:
            rect = nearest_rect(entity_hb.rect(entity_t, entity_s), pygame.Vector2(blast.center), size)
            return blast.colliderect(rect)

        for player_entity, (p_t, p_s, p_hb, _) in world.get_components(CTransform, CSurface, CHitBox, CTagPlayer):
            if hit(p_t, p_s, p_hb):
                kill_player(world, player_entity, player_info["death"], explosion_info)
        for enemy_entity, (e_t, e_s, e_v, e_hb, _) in world.get_components(
            CTransform, CSurface, CVelocity, CHitBox, CTagEnemy
        ):
            if world.entity_exists(enemy_entity) and hit(e_t, e_s, e_hb):
                if by_player:
                    award(world, enemy_entity)
                world.delete_entity(enemy_entity)
                create_explosion(world, e_hb.rect(e_t, e_s).center, explosion_info, e_v.vel)
        for ob_entity, (o_t, o_s, o_hb, c_ob) in world.get_components(CTransform, CSurface, CHitBox, CObstacle):
            if c_ob.kind == ObstacleKind.MINE and world.entity_exists(ob_entity) and hit(o_t, o_s, o_hb):
                if by_player:
                    award(world, ob_entity)
                destroy_obstacle(world, ob_entity, obstacles_info, explosion_info, by_player)
