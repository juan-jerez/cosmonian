import random
import pygame
import esper
from src.ecs.components.c_animation import CAnimation
from src.ecs.components.c_camera import CCamera
from src.ecs.components.c_enemy_ai import CEnemyAI
from src.ecs.components.c_enemy_spawner import CEnemySpawner
from src.ecs.components.c_alert_condition import CAlertCondition
from src.ecs.components.c_base import CBase
from src.ecs.components.c_boss import CBoss, CBossBar, CHomingShot
from src.ecs.components.c_base_core import CBaseCore
from src.ecs.components.c_base_turret import CBaseTurret, TurretState
from src.ecs.components.c_bullet_direction import CBulletDirection
from src.ecs.components.c_directional_sprite import CDirectionalSprite
from src.ecs.components.c_explosion_burst import CExplosionBurst
from src.ecs.components.c_formation import CFormation, CFormationMember
from src.ecs.components.c_formation_spawner import CFormationSpawner
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_player_ship import CPlayerShip
from src.ecs.components.c_lifetime import CLifetime
from src.ecs.components.c_obstacle import CObstacle, ObstacleKind
from src.ecs.components.c_player_state import CPlayerState
from src.ecs.components.c_points import CPoints
from src.ecs.components.c_render_layer import CRenderLayer
from src.ecs.components.c_shield import CShield, CShieldBubble, CShieldItem
from src.ecs.components.c_spawn_protection import CSpawnProtection
from src.ecs.components.c_spy import CSpy
from src.ecs.components.c_spy_spawner import CSpySpawner
from src.ecs.components.c_screen_shake import CScreenShake

from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_world import CWorld
from src.ecs.components.tags.c_tag_base_part import CTagBasePart
from src.ecs.components.tags.c_tag_bullet import CTagBullet
from src.ecs.components.tags.c_tag_enemy_bullet import CTagEnemyBullet
from src.ecs.components.tags.c_tag_enemy import CTagEnemy
from src.ecs.components.tags.c_tag_explosion import CTagExplosion
from src.ecs.components.tags.c_tag_invincible import CTagInvincible
from src.ecs.components.tags.c_tag_lethal_explosion import CTagLethalExplosion
from src.ecs.components.tags.c_tag_player import CTagPlayer
from src.ecs.components.tags.c_tag_player_caused import CTagPlayerCaused
from src.ecs.components.tags.c_tag_ui import CTagUI
from src.ecs.systems.s_animation import set_frame_area
from src.ecs.systems.s_world_wrap import wrap_delta
from src.ecs.utils.directions import DIRECTIONS, direction_index
from src.create.prefab_ui import (
    color_from_cfg,
    create_starfield,
    create_text,
    rect_from_cfg,
    sprite_strip,
    sprite_surface,
)
from src.engine.service_locator import ServiceLocator


def create_sprite(
    world: esper.World,
    pos: pygame.Vector2,
    vel: pygame.Vector2,
    surface: pygame.Surface,
    animations: dict | None = None,
) -> int:
    sprite_entity = world.create_entity()
    c_surf = CSurface.from_surface(surface)
    world.add_component(sprite_entity, c_surf)
    world.add_component(sprite_entity, CTransform(pos))
    world.add_component(sprite_entity, CVelocity(vel))
    if animations is not None:
        c_anim = CAnimation(animations)
        world.add_component(sprite_entity, c_anim)
        set_frame_area(c_surf, c_anim)
    return sprite_entity


def sprite_size(image_info: dict) -> pygame.Vector2:
    """Tamaño de un cuadro de la entidad según su imagen y número de cuadros."""
    surf = ServiceLocator.images_service.get(image_info["image"])
    number_frames = image_info["animations"]["number_frames"] if "animations" in image_info else 1
    return pygame.Vector2(surf.get_width() // number_frames, surf.get_height())


def create_enemy(
    world: esper.World,
    kind: str,
    center: pygame.Vector2,
    direction: pygame.Vector2,
    enemies_info: dict,
    accuracy: float,
    player_max_speed: float,
) -> int:
    """Enemigo de tipo I, P o E que sale en `direction`; su velocidad es la del jugador por el
    factor de su tipo, así siempre es algo más rápido que él."""
    enemy_info = enemies_info[kind]
    surfaces = directional_surfaces(enemy_info["sprite"])
    max_speed = player_max_speed * enemy_info["speed_factor"]
    velocity = direction.normalize() * max_speed
    index = direction_index(velocity)
    pos = center - pygame.Vector2(surfaces[index].get_size()) / 2
    enemy_entity = create_sprite(world, pos, velocity, surfaces[index])
    world.add_component(enemy_entity, CDirectionalSprite(surfaces, index))
    world.add_component(
        enemy_entity, CEnemyAI(kind, enemy_info, enemies_info["steering"], accuracy, max_speed)
    )
    world.add_component(enemy_entity, CPoints(enemy_info["points"]))
    add_hitbox(world, enemy_entity, enemy_info["hitbox"])
    world.add_component(enemy_entity, CTagEnemy())
    world.add_component(enemy_entity, CRenderLayer(2))
    return enemy_entity


def create_spy(
    world: esper.World, center: pygame.Vector2, direction: pygame.Vector2, spy_info: dict, player_max_speed: float
) -> int:
    surfaces = directional_surfaces(spy_info["sprite"])
    velocity = direction.normalize() * player_max_speed * spy_info["speed_factor"]
    index = direction_index(velocity)
    spy_entity = create_sprite(world, center - pygame.Vector2(surfaces[index].get_size()) / 2, velocity, surfaces[index])
    world.add_component(spy_entity, CDirectionalSprite(surfaces, index))
    world.add_component(spy_entity, CSpy(spy_info))
    add_hitbox(world, spy_entity, spy_info["hitbox"])
    world.add_component(spy_entity, CTagEnemy())
    world.add_component(spy_entity, CRenderLayer(2))
    return spy_entity


def create_alert(world: esper.World, alert_info: dict, spy_level_info: dict) -> int:
    """Estado de alerta del nivel y el generador de espías."""
    alert_entity = world.create_entity()
    world.add_component(alert_entity, CAlertCondition(alert_info))
    world.add_component(alert_entity, CSpySpawner(spy_level_info))
    return alert_entity


def create_formation_spawner(world: esper.World, formations_level_info: dict) -> int:
    spawner_entity = world.create_entity()
    world.add_component(spawner_entity, CFormationSpawner(formations_level_info))
    return spawner_entity


def create_formation(
    world: esper.World,
    shape: str,
    kind: str,
    center: pygame.Vector2,
    direction: pygame.Vector2,
    formations_info: dict,
    enemies_info: dict,
    player_max_speed: float,
) -> int:
    """Formación de cuatro enemigos del mismo tipo y su capitán (el primer hueco de la figura,
    de otro color). La entidad de la formación lleva la posición y el rumbo del grupo."""
    speed = player_max_speed * formations_info["speed_factor"]
    velocity = direction.normalize() * speed
    angle = pygame.Vector2(0, -1).angle_to(velocity)
    formation_entity = world.create_entity()
    world.add_component(formation_entity, CTransform(center.copy()))
    world.add_component(formation_entity, CVelocity(velocity.copy()))

    enemy_info = enemies_info[kind]
    members = []
    for i, slot in enumerate(formations_info["shapes"][shape]):
        offset = pygame.Vector2(slot["x"], slot["y"]) * formations_info["spacing"]
        if i == 0:
            surfaces = captain_surfaces(enemy_info["sprite"], formations_info["captain_tint"])
        else:
            surfaces = directional_surfaces(enemy_info["sprite"])
        index = direction_index(velocity)
        pos = center + offset.rotate(angle) - pygame.Vector2(surfaces[index].get_size()) / 2
        member_entity = create_sprite(world, pos, velocity.copy(), surfaces[index])
        world.add_component(member_entity, CDirectionalSprite(surfaces, index))
        world.add_component(member_entity, CFormationMember(formation_entity, offset, kind))
        points = formations_info["captain_points"] if i == 0 else enemy_info["points"]
        world.add_component(member_entity, CPoints(points))
        add_hitbox(world, member_entity, enemy_info["hitbox"])
        world.add_component(member_entity, CTagEnemy())
        world.add_component(member_entity, CRenderLayer(2))
        members.append(member_entity)

    c_form = CFormation(formations_info, members[0], members)
    c_form.max_speed = speed
    c_form.heading = velocity.normalize()
    world.add_component(formation_entity, c_form)
    return formation_entity


_captain_cache: dict[str, list[pygame.Surface]] = {}


def captain_surfaces(sprite_name: str, tint_info: dict) -> list[pygame.Surface]:
    """Imágenes del capitán: las del enemigo con un tinte que lo distingue."""
    if sprite_name not in _captain_cache:
        tint = (tint_info["r"], tint_info["g"], tint_info["b"])
        tinted = []
        for surface in directional_surfaces(sprite_name):
            copy = surface.copy()
            # Solo suma color: lo transparente sigue transparente
            copy.fill(tint, special_flags=pygame.BLEND_RGB_ADD)
            tinted.append(copy)
        _captain_cache[sprite_name] = tinted
    return _captain_cache[sprite_name]


_directional_cache: dict[str, list[pygame.Surface]] = {}


def directional_surfaces(sprite_name: str) -> list[pygame.Surface]:
    """Las ocho imágenes giradas de un sprite que mira hacia arriba. Girar pixel art es costoso,
    así que se calculan una sola vez por sprite."""
    if sprite_name not in _directional_cache:
        base = sprite_surface(sprite_name)
        _directional_cache[sprite_name] = [rotate_pixel_art(base, -45 * i) for i in range(8)]
    return _directional_cache[sprite_name]


def create_player(world: esper.World, player_info: dict, spawn_info: dict) -> int:
    # Una imagen de la nave por cada dirección: la original mira hacia arriba y se gira de 45 en 45
    surfaces = directional_surfaces(player_info["sprite"])
    direction = spawn_info["direction"]
    surface = surfaces[direction]
    # La posición de origen del nivel es el centro del jugador
    center = pygame.Vector2(spawn_info["position"]["x"], spawn_info["position"]["y"])
    pos = center - pygame.Vector2(surface.get_size()) / 2
    player_entity = create_sprite(world, pos, pygame.Vector2(0, 0), surface)
    world.add_component(player_entity, CDirectionalSprite(surfaces, direction))
    world.add_component(player_entity, CPlayerShip(player_info, direction))
    add_hitbox(world, player_entity, player_info["hitbox"])
    world.add_component(player_entity, CTagPlayer())
    # Por encima de las bases, para que la nave se vea al pasar sobre ellas
    world.add_component(player_entity, CRenderLayer(2))
    world.add_component(player_entity, CPlayerState(player_info["sound"], player_info["sound_volume"]))
    return player_entity


def rotate_pixel_art(surface: pygame.Surface, angle: float) -> pygame.Surface:
    """Gira una imagen de pixel art con menos dientes que pygame.transform.rotate: se amplía
    8 veces con scale2x (que suaviza los bordes sin mezclar colores), se gira y se reduce."""
    big = surface
    for _ in range(3):
        big = pygame.transform.scale2x(big)
    rotated = pygame.transform.rotate(big, angle)
    return pygame.transform.scale(rotated, (round(rotated.get_width() / 8), round(rotated.get_height() / 8)))


def create_player_shots(
    world: esper.World,
    center: pygame.Vector2,
    direction: int,
    ship_velocity: pygame.Vector2,
    bullet_info: dict,
    triple: bool,
):
    """Disparo de la nave: hacia delante (una bala, o tres en paralelo con el disparo triple)
    y siempre una hacia atrás."""
    side_offset = bullet_info["triple_offset"]
    front_offsets = (-side_offset, 0, side_offset) if triple else (0,)
    for offset in front_offsets:
        _create_player_bullet(world, center, direction, offset, ship_velocity, bullet_info)
    _create_player_bullet(world, center, (direction + 4) % 8, 0, ship_velocity, bullet_info)
    ServiceLocator.sounds_service.play(bullet_info["sound"])


def _create_player_bullet(
    world: esper.World,
    center: pygame.Vector2,
    direction: int,
    side_offset: float,
    ship_velocity: pygame.Vector2,
    bullet_info: dict,
):
    forward = DIRECTIONS[direction]
    # Sale del extremo de la nave; las del disparo triple, desplazadas hacia los lados
    start = center + forward * bullet_info["spawn_offset"] + forward.rotate(90) * side_offset
    surface = _bullet_surface(bullet_info, direction)
    pos = start - pygame.Vector2(surface.get_size()) / 2
    # Se suma la velocidad de la nave para que la bala se aleje de ella a su velocidad normal
    velocity = forward * bullet_info["velocity"] + ship_velocity
    bullet_entity = create_sprite(world, pos, velocity, surface)
    add_hitbox(world, bullet_entity, bullet_info["hitbox"])
    world.add_component(bullet_entity, CTagBullet())
    world.add_component(bullet_entity, CBulletDirection(direction))


def _bullet_surface(bullet_info: dict, direction: int) -> pygame.Surface:
    sprites = bullet_info["sprites"]
    if direction in (0, 4):
        return sprite_surface(sprites["vertical"])
    if direction in (2, 6):
        return sprite_surface(sprites["horizontal"])
    diagonal = sprite_surface(sprites["diagonal"])
    # La imagen diagonal va de abajo a la izquierda hacia arriba a la derecha ("/");
    # para las otras dos diagonales se refleja
    if direction in (1, 5):
        return diagonal
    return ServiceLocator.images_service.get_flipped(diagonal)


def create_explosion(
    world: esper.World,
    center: tuple[float, float],
    explosion_info: dict,
    velocity: pygame.Vector2 | None = None,
    sound: bool = True,
) -> int:
    """Explosión animada; con `velocity` sigue moviéndose como lo que explotó."""
    surface, number_frames = sprite_strip(explosion_info["sprite"])
    animations = {
        "number_frames": number_frames,
        "list": [{"name": "EXPLODE", "start": 0, "end": number_frames - 1, "framerate": explosion_info["framerate"]}],
    }
    pos = pygame.Vector2(center) - pygame.Vector2(surface.get_width() / number_frames, surface.get_height()) / 2
    vel = pygame.Vector2(0, 0) if velocity is None else pygame.Vector2(velocity)
    explosion_entity = create_sprite(world, pos, vel, surface, animations)
    world.add_component(explosion_entity, CTagExplosion())
    world.add_component(explosion_entity, CRenderLayer(3))
    if sound:
        ServiceLocator.sounds_service.play(explosion_info["sound"])
    return explosion_entity


def kill_player(world: esper.World, player_entity: int, death_info: dict, explosion_info: dict):
    """El jugador desaparece y en su lugar queda una ráfaga de explosiones."""
    # Si dos cosas lo alcanzan en el mismo cuadro, solo muere una vez; con escudo no muere
    if not world.entity_exists(player_entity) or world.has_component(player_entity, CShield):
        return
    # En modo trampa tampoco, ni justo después de reaparecer
    if world.has_component(player_entity, CTagInvincible) or world.has_component(player_entity, CSpawnProtection):
        return
    c_t = world.component_for_entity(player_entity, CTransform)
    c_s = world.component_for_entity(player_entity, CSurface)
    c_pst = world.component_for_entity(player_entity, CPlayerState)
    ServiceLocator.sounds_service.stop(c_pst.move_sound)
    burst_entity = world.create_entity()
    world.add_component(burst_entity, CTransform(c_t.pos + pygame.Vector2(c_s.area.size) / 2))
    world.add_component(burst_entity, CExplosionBurst(death_info, explosion_info))
    world.delete_entity(player_entity)


def add_hitbox(world: esper.World, entity: int, hitbox_info: dict | None):
    """HitBox de la configuración o, si no la tiene, del tamaño del cuadro de la imagen."""
    if hitbox_info is None:
        size = pygame.Vector2(world.component_for_entity(entity, CSurface).area.size)
    else:
        size = pygame.Vector2(hitbox_info["w"], hitbox_info["h"])
    world.add_component(entity, CHitBox(size))


def create_base(world: esper.World, place_info: dict, base_info: dict, behavior_info: dict) -> int:
    """Base enemiga: un cuerpo decorativo, seis torretas y un núcleo. La configuración describe
    la base vertical; la horizontal es la misma girada 90 grados."""
    center = pygame.Vector2(place_info["position"]["x"], place_info["position"]["y"])
    vertical = place_info["orientation"] == "vertical"
    turret_info = base_info["turret"]

    def place(offset: pygame.Vector2) -> pygame.Vector2:
        # Girar 90 grados en el sentido de las agujas del reloj: (x, y) pasa a (-y, x)
        return center + (offset if vertical else pygame.Vector2(-offset.y, offset.x))

    base_entity = world.create_entity()
    c_base = CBase(vertical, base_info["points"], len(turret_info["positions"]))
    world.add_component(base_entity, CTransform(center.copy()))
    world.add_component(base_entity, c_base)

    body, body_center = _base_body(base_info["body"])
    if not vertical:
        body = pygame.transform.rotate(body, -90)
    body_entity = world.create_entity()
    world.add_component(body_entity, CSurface.from_surface(body))
    world.add_component(body_entity, CTransform(place(body_center) - pygame.Vector2(body.get_size()) / 2))
    c_base.parts.append(body_entity)

    for position in turret_info["positions"]:
        turret_entity = _create_base_part(
            world, turret_info, place(pygame.Vector2(position["x"], position["y"])), vertical
        )
        world.add_component(turret_entity, CBaseTurret(base_entity, turret_info, behavior_info["turret_interval"]))
        world.add_component(turret_entity, CPoints(turret_info["points"]))
        c_base.parts.append(turret_entity)

    core_info = base_info["core"]
    core_entity = _create_base_part(world, core_info, center, vertical)
    world.add_component(core_entity, CBaseCore(base_entity, core_info, behavior_info))
    c_base.parts.append(core_entity)
    return base_entity


def _base_body(body_info: list[dict]) -> tuple[pygame.Surface, pygame.Vector2]:
    """Junta las piezas del cuerpo (arcos y conectores) en una imagen. Devuelve también la
    posición de su centro respecto al centro de la base."""
    pieces = []
    for piece_info in body_info:
        surface = sprite_surface(piece_info["sprite"])
        if piece_info["flip"]:
            surface = ServiceLocator.images_service.get_flipped(surface)
        pieces.append((surface, pygame.Vector2(piece_info["offset"]["x"], piece_info["offset"]["y"])))
    bounds = pygame.Rect(pieces[0][1], pieces[0][0].get_size()).unionall(
        [pygame.Rect(offset, surface.get_size()) for surface, offset in pieces[1:]]
    )
    body = pygame.Surface(bounds.size, pygame.SRCALPHA)
    for surface, offset in pieces:
        body.blit(surface, offset - pygame.Vector2(bounds.topleft))
    return body, pygame.Vector2(bounds.center)


def _create_base_part(world: esper.World, part_info: dict, center: pygame.Vector2, vertical: bool) -> int:
    """Torreta o núcleo: una tira de cuadros (girados si la base es horizontal) y su HitBox."""
    strip, number_frames = sprite_strip(part_info["sprite"])
    if not vertical:
        strip = _rotate_strip(strip, number_frames)
    c_s = CSurface.from_surface(strip)
    c_s.area.w = strip.get_width() // number_frames
    part_entity = world.create_entity()
    world.add_component(part_entity, c_s)
    world.add_component(part_entity, CTransform(center - pygame.Vector2(c_s.area.size) / 2))
    add_hitbox(world, part_entity, part_info["hitbox"])
    world.add_component(part_entity, CTagBasePart())
    world.add_component(part_entity, CRenderLayer(1))
    return part_entity


def _rotate_strip(strip: pygame.Surface, number_frames: int) -> pygame.Surface:
    """Gira 90 grados cada cuadro de una tira (de cuadros cuadrados) sin desordenarlos."""
    cell = strip.get_width() // number_frames
    rotated = pygame.Surface(strip.get_size(), pygame.SRCALPHA)
    for i in range(number_frames):
        frame = strip.subsurface((i * cell, 0, cell, strip.get_height()))
        rotated.blit(pygame.transform.rotate(frame, -90), (i * cell, 0))
    return rotated


def destroy_base(world: esper.World, base_entity: int, base_info: dict, explosion_info: dict):
    """La base estalla entera: una ráfaga en el núcleo y una explosión en cada torreta que
    quedaba en pie; después desaparecen todas sus partes."""
    c_base = world.component_for_entity(base_entity, CBase)
    for part in c_base.parts:
        if world.has_component(part, CBaseTurret):
            if world.component_for_entity(part, CBaseTurret).state != TurretState.DESTROYED:
                create_explosion(world, _entity_center(world, part), explosion_info)
        world.delete_entity(part)
    burst_entity = world.create_entity()
    world.add_component(burst_entity, CTransform(world.component_for_entity(base_entity, CTransform).pos.copy()))
    world.add_component(burst_entity, CExplosionBurst(base_info["destruction"], explosion_info))
    create_screen_shake(world, base_info["screen_shake"])
    world.delete_entity(base_entity)


def _entity_center(world: esper.World, entity: int) -> pygame.Vector2:
    c_t = world.component_for_entity(entity, CTransform)
    c_s = world.component_for_entity(entity, CSurface)
    return c_t.pos + pygame.Vector2(c_s.area.size) / 2


def create_enemy_bullet(world: esper.World, center: pygame.Vector2, velocity: pygame.Vector2, bullet_info: dict) -> int:
    size = pygame.Vector2(bullet_info["size"]["w"], bullet_info["size"]["h"])
    color = pygame.Color(bullet_info["color"]["r"], bullet_info["color"]["g"], bullet_info["color"]["b"])
    bullet_entity = world.create_entity()
    world.add_component(bullet_entity, CSurface(size, color))
    world.add_component(bullet_entity, CTransform(center - size / 2))
    world.add_component(bullet_entity, CVelocity(velocity))
    add_hitbox(world, bullet_entity, bullet_info["hitbox"])
    world.add_component(bullet_entity, CTagEnemyBullet())
    world.add_component(bullet_entity, CLifetime(bullet_info["lifetime"]))
    world.add_component(bullet_entity, CRenderLayer(2))
    return bullet_entity


def create_obstacles(
    world: esper.World,
    counts_info: dict,
    obstacles_info: dict,
    spawn_center: pygame.Vector2,
    base_centers: list[pygame.Vector2],
    world_size: pygame.Vector2,
):
    """Reparte al azar las rocas, minas y rocas indestructibles del nivel, lejos del punto de
    partida del jugador, de las bases y unas de otras."""
    placement = obstacles_info["placement"]
    taken: list[pygame.Vector2] = []

    def free_position() -> pygame.Vector2:
        # Si tras muchos intentos no hay sitio, se usa el último probado
        for _ in range(200):
            pos = pygame.Vector2(random.uniform(0, world_size.x), random.uniform(0, world_size.y))
            if (
                wrap_delta(pos - spawn_center, world_size).length() >= placement["min_distance_spawn"]
                and all(wrap_delta(pos - c, world_size).length() >= placement["min_distance_base"] for c in base_centers)
                and all(wrap_delta(pos - t, world_size).length() >= placement["min_distance_obstacle"] for t in taken)
            ):
                break
        taken.append(pos)
        return pos

    for _ in range(counts_info["rocks"]):
        _create_rock(world, free_position(), obstacles_info["rock"])
    for _ in range(counts_info["mines"]):
        _create_mine(world, free_position(), obstacles_info["mine"])
    for _ in range(counts_info["hard_rocks"]):
        _create_hard_rock(world, free_position(), obstacles_info["hard_rock"])


def _create_rock(world: esper.World, center: pygame.Vector2, rock_info: dict) -> int:
    surface = sprite_surface(random.choice(rock_info["sprites"]))
    rock_entity = create_sprite(world, center - pygame.Vector2(surface.get_size()) / 2, pygame.Vector2(0, 0), surface)
    add_hitbox(world, rock_entity, rock_info["hitbox"])
    world.add_component(rock_entity, CObstacle(ObstacleKind.ROCK))
    world.add_component(rock_entity, CPoints(rock_info["points"]))
    return rock_entity


def _create_mine(world: esper.World, center: pygame.Vector2, mine_info: dict) -> int:
    # Dos cuadros: las luces de los extremos parpadean
    surface, number_frames = sprite_strip(mine_info["sprite"])
    animations = {
        "number_frames": number_frames,
        "list": [{"name": "BLINK", "start": 0, "end": number_frames - 1, "framerate": mine_info["framerate"]}],
    }
    frame_size = pygame.Vector2(surface.get_width() / number_frames, surface.get_height())
    mine_entity = create_sprite(world, center - frame_size / 2, pygame.Vector2(0, 0), surface, animations)
    add_hitbox(world, mine_entity, mine_info["hitbox"])
    world.add_component(mine_entity, CObstacle(ObstacleKind.MINE))
    world.add_component(mine_entity, CPoints(mine_info["points"]))
    return mine_entity


def _create_hard_rock(world: esper.World, center: pygame.Vector2, hard_rock_info: dict) -> int:
    surface = sprite_surface(random.choice(hard_rock_info["sprites"]))
    speed = random.uniform(hard_rock_info["velocity"]["min"], hard_rock_info["velocity"]["max"])
    velocity = pygame.Vector2(speed, 0).rotate(random.uniform(0, 360))
    rock_entity = create_sprite(world, center - pygame.Vector2(surface.get_size()) / 2, velocity, surface)
    add_hitbox(world, rock_entity, hard_rock_info["hitbox"])
    world.add_component(rock_entity, CObstacle(ObstacleKind.HARD_ROCK))
    return rock_entity


def destroy_obstacle(
    world: esper.World, obstacle_entity: int, obstacles_info: dict, explosion_info: dict, by_player: bool = False
):
    """Destruye una roca o una mina. La mina deja una explosión letal (de otro color); si la
    hizo estallar el jugador, lo que destruya esa explosión también le da puntos. Las rocas
    indestructibles no se destruyen."""
    if not world.entity_exists(obstacle_entity):
        return
    c_ob = world.component_for_entity(obstacle_entity, CObstacle)
    if c_ob.kind == ObstacleKind.HARD_ROCK:
        return
    center = _entity_center(world, obstacle_entity)
    world.delete_entity(obstacle_entity)
    if c_ob.kind == ObstacleKind.MINE:
        mine_explosion_info = obstacles_info["mine"]["explosion"]
        explosion_entity = create_explosion(world, center, mine_explosion_info)
        add_hitbox(world, explosion_entity, mine_explosion_info["hitbox"])
        world.add_component(explosion_entity, CTagLethalExplosion())
        if by_player:
            world.add_component(explosion_entity, CTagPlayerCaused())
    else:
        create_explosion(world, center, explosion_info)


def create_enemy_spawner(world: esper.World, enemies_info: dict) -> int:
    spawner_entity = world.create_entity()
    world.add_component(spawner_entity, CEnemySpawner(enemies_info))
    return spawner_entity


def activate_shield(world: esper.World, player_entity: int, shield_info: dict):
    """Protege al jugador unos segundos y dibuja un anillo a su alrededor."""
    bubble_info = shield_info["bubble"]
    world.add_component(player_entity, CShield(shield_info["duration"], bubble_info["blink_time"]))
    radius = bubble_info["radius"]
    size = (radius + bubble_info["width"]) * 2
    ring = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(ring, color_from_cfg(bubble_info["color"]), (size // 2, size // 2), radius, bubble_info["width"])
    bubble_entity = world.create_entity()
    world.add_component(bubble_entity, CSurface.from_surface(ring))
    world.add_component(bubble_entity, CTransform(pygame.Vector2(0, 0)))
    world.add_component(bubble_entity, CShieldBubble(player_entity, bubble_info["blink"]))
    world.add_component(bubble_entity, CRenderLayer(3))
    ServiceLocator.sounds_service.play(shield_info["sounds"]["activate"])


def create_shield_item(world: esper.World, center: pygame.Vector2, shield_info: dict) -> int:
    """Ítem que da una carga de escudo; la hoja de sprites no trae uno, así que se dibuja."""
    item_info = shield_info["item"]
    radius = item_info["radius"]
    surface = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
    middle = (radius + 1, radius + 1)
    pygame.draw.circle(surface, color_from_cfg(item_info["color"]), middle, radius, 2)
    pygame.draw.circle(surface, color_from_cfg(item_info["core_color"]), middle, radius // 2)
    item_entity = world.create_entity()
    world.add_component(item_entity, CSurface.from_surface(surface))
    world.add_component(item_entity, CTransform(center - pygame.Vector2(surface.get_size()) / 2))
    add_hitbox(world, item_entity, item_info["hitbox"])
    world.add_component(item_entity, CShieldItem(item_info["blink_time"], item_info["blink"]))
    world.add_component(item_entity, CLifetime(item_info["lifetime"]))
    world.add_component(item_entity, CRenderLayer(1))
    return item_entity


def create_boss(world: esper.World, center: pygame.Vector2, boss_info: dict, player_max_speed: float) -> int:
    """Jefe: una nave grande que gira según su rumbo y parpadea en blanco al recibir golpes."""
    surfaces = _boss_surfaces(boss_info)
    flash = _tinted_copies(surfaces, boss_info["flash"]["tint"])
    index = 4  # mirando hacia abajo, hacia el jugador
    boss_entity = create_sprite(world, center - pygame.Vector2(surfaces[index].get_size()) / 2, pygame.Vector2(0, 0), surfaces[index])
    world.add_component(boss_entity, CDirectionalSprite(surfaces, index))
    c_boss = CBoss(boss_info, player_max_speed * boss_info["speed_factor"], flash)
    c_boss.normal_surfaces = surfaces
    world.add_component(boss_entity, c_boss)
    add_hitbox(world, boss_entity, boss_info["hitbox"])
    world.add_component(boss_entity, CRenderLayer(2))
    return boss_entity


_boss_cache: dict[str, list[pygame.Surface]] = {}


def _boss_surfaces(boss_info: dict) -> list[pygame.Surface]:
    """Las ocho imágenes giradas del jefe (calculadas una sola vez: girar pixel art es costoso)."""
    if boss_info["image"] not in _boss_cache:
        base = ServiceLocator.images_service.get(boss_info["image"])
        base = pygame.transform.scale_by(base, boss_info["scale"])
        _boss_cache[boss_info["image"]] = [rotate_pixel_art(base, -45 * i) for i in range(8)]
    return _boss_cache[boss_info["image"]]


def _tinted_copies(surfaces: list[pygame.Surface], tint_info: dict) -> list[pygame.Surface]:
    tint = (tint_info["r"], tint_info["g"], tint_info["b"])
    copies = []
    for surface in surfaces:
        copy = surface.copy()
        copy.fill(tint, special_flags=pygame.BLEND_RGB_ADD)
        copies.append(copy)
    return copies


def create_homing_shot(
    world: esper.World, center: pygame.Vector2, direction: pygame.Vector2, homing_info: dict, player_max_speed: float
) -> int:
    """Bala del jefe que persigue al jugador y aguanta varios disparos."""
    radius = homing_info["radius"]
    surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    middle = (radius + 2, radius + 2)
    pygame.draw.circle(surface, color_from_cfg(homing_info["color"]), middle, radius + 2)
    pygame.draw.circle(surface, color_from_cfg(homing_info["core_color"]), middle, radius - 1)
    max_speed = player_max_speed * homing_info["speed_factor"]
    shot_entity = create_sprite(
        world, center - pygame.Vector2(surface.get_size()) / 2, direction.normalize() * max_speed, surface
    )
    add_hitbox(world, shot_entity, homing_info["hitbox"])
    world.add_component(shot_entity, CHomingShot(homing_info, max_speed))
    world.add_component(shot_entity, CLifetime(homing_info["lifetime"]))
    world.add_component(shot_entity, CRenderLayer(2))
    ServiceLocator.sounds_service.play(homing_info["sound"])
    return shot_entity


def create_boss_bar(world: esper.World, bar_info: dict) -> int:
    create_text(world, bar_info["label"])
    rect = rect_from_cfg(bar_info["rect"])
    bar_entity = world.create_entity()
    world.add_component(bar_entity, CSurface(pygame.Vector2(rect.size), color_from_cfg(bar_info["colors"]["back"])))
    world.add_component(bar_entity, CTransform(pygame.Vector2(rect.topleft)))
    colors = {name: color_from_cfg(color) for name, color in bar_info["colors"].items()}
    world.add_component(bar_entity, CBossBar(rect, colors))
    world.add_component(bar_entity, CTagUI())
    return bar_entity


def destroy_boss(world: esper.World, boss_entity: int, boss_info: dict, explosion_info: dict):
    """El jefe estalla en una gran ráfaga de explosiones y la pantalla se sacude."""
    c_t = world.component_for_entity(boss_entity, CTransform)
    c_s = world.component_for_entity(boss_entity, CSurface)
    burst_entity = world.create_entity()
    world.add_component(burst_entity, CTransform(c_t.pos + pygame.Vector2(c_s.area.size) / 2))
    world.add_component(burst_entity, CExplosionBurst(boss_info["death"], explosion_info))
    create_screen_shake(world, boss_info["screen_shake"])
    world.delete_entity(boss_entity)


def create_screen_shake(world: esper.World, shake_info: dict) -> int:
    shake_entity = world.create_entity()
    world.add_component(shake_entity, CScreenShake(shake_info["duration"], shake_info["intensity"]))
    return shake_entity


def create_camera(world: esper.World, viewport_info: dict) -> int:
    camera_entity = world.create_entity()
    world.add_component(camera_entity, CTransform(pygame.Vector2(0, 0)))
    world.add_component(camera_entity, CCamera(rect_from_cfg(viewport_info)))
    return camera_entity


def create_world(world: esper.World, world_info: dict) -> int:
    world_entity = world.create_entity()
    world.add_component(world_entity, CWorld(pygame.Vector2(world_info["size"]["w"], world_info["size"]["h"])))
    return world_entity


def create_world_background(world: esper.World, world_info: dict, viewport_info: dict):
    """Capas de estrellas que se desplazan a distinta velocidad con la cámara, dando profundidad."""
    viewport_size = pygame.Vector2(viewport_info["w"], viewport_info["h"])
    layers = world_info["star_layers"]
    for i, layer_info in enumerate(layers):
        # La primera capa (la más lejana) se dibuja más al fondo
        create_starfield(world, viewport_size, layer_info, i - len(layers))
