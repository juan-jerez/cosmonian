import pygame

from src.create.prefab_creator import (
    create_alert,
    create_base,
    create_boss,
    create_boss_bar,
    create_camera,
    destroy_base,
    destroy_boss,
    create_enemy_spawner,
    create_formation_spawner,
    create_obstacles,
    create_player,
    create_player_shots,
    activate_shield,
    create_world,
    create_world_background,
)
from src.create.prefab_ui import (
    INTERFACE_CFG,
    create_input_commands,
    create_lives_display,
    input_binding,
    create_menu,
    create_minimap,
    create_sidebar,
    create_text,
)
from src.ecs.components.c_base import CBase
from src.ecs.components.c_boss import CBoss
from src.ecs.components.c_blink import CBlink
from src.ecs.components.c_input_command import CInputCommand, CommandPhase
from src.ecs.components.c_lifetime import CLifetime
from src.ecs.components.c_menu import CMenu
from src.ecs.components.c_minimap import CMinimap
from src.ecs.components.c_player_ship import CPlayerShip
from src.ecs.components.c_score import CScore
from src.ecs.components.c_spawn_protection import CSpawnProtection
from src.ecs.components.c_shield import CShieldDisplay, CShieldItemSpawner
from src.ecs.components.c_starfield import CStarfield
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_warp import CWarp
from src.ecs.components.c_formation_spawner import CFormationSpawner
from src.ecs.components.tags.c_tag_bullet import CTagBullet
from src.ecs.components.tags.c_tag_cheat_ui import CTagCheatUI
from src.ecs.components.tags.c_tag_invincible import CTagInvincible
from src.ecs.components.tags.c_tag_hidden import CTagHidden
from src.ecs.components.tags.c_tag_pause_ui import CTagPauseUI
from src.ecs.components.tags.c_tag_ui import CTagUI
from src.ecs.systems.s_alert_condition import alert_level, set_alert_level, system_alert_condition
from src.ecs.systems.s_blink import system_blink
from src.ecs.systems.s_animation import system_animation
from src.ecs.systems.s_base_core import system_base_core
from src.ecs.systems.s_base_turret import system_base_turret
from src.ecs.systems.s_boss import system_boss, system_boss_bar, system_collision_boss, system_homing_shot
from src.ecs.systems.s_camera import camera_rect, system_camera
from src.ecs.systems.s_collision_bullet_enemy import system_collision_bullet_enemy
from src.ecs.systems.s_condition_display import system_condition_display
from src.ecs.systems.s_directional_sprite import system_directional_sprite
from src.ecs.systems.s_collision_base import system_collision_bullet_base, system_collision_player_base
from src.ecs.systems.s_collision_enemy_bounce import system_collision_enemy_bounce
from src.ecs.systems.s_collision_enemy_bullet import system_collision_enemy_bullet
from src.ecs.systems.s_collision_obstacle import system_collision_obstacle
from src.ecs.systems.s_collision_player_enemy import system_collision_player_enemy
from src.ecs.systems.s_enemy_ai import system_enemy_ai
from src.ecs.systems.s_enemy_spawner import system_base_core_spawner, system_enemy_spawner
from src.ecs.systems.s_explosion_burst import system_explosion_burst
from src.ecs.systems.s_explosion_kill import system_explosion_kill
from src.ecs.systems.s_formation import spawn_formation, system_formation, system_formation_spawner
from src.ecs.systems.s_lifetime import system_lifetime
from src.ecs.systems.s_menu import menu_action, menu_move, system_menu
from src.ecs.systems.s_minimap import system_minimap
from src.ecs.systems.s_movement import system_movement
from src.ecs.systems.s_player_ship import steer_player, system_player_ship
from src.ecs.systems.s_player_state import system_player_state
from src.ecs.systems.s_rendering import system_rendering
from src.ecs.systems.s_score import system_score_display
from src.ecs.systems.s_screen_bullet import system_screen_bullet
from src.ecs.systems.s_screen_shake import system_screen_shake
from src.ecs.systems.s_shield import (
    has_shield,
    system_shield,
    system_shield_display,
    system_shield_item,
    system_shield_item_spawner,
)
from src.ecs.systems.s_spawn_protection import system_spawn_protection
from src.ecs.systems.s_spy import spawn_spy, system_spy, system_spy_spawner
from src.ecs.systems.s_starfield import system_starfield
from src.ecs.systems.s_warp import system_warp
from src.ecs.systems.s_world_wrap import system_world_wrap
from src.ecs.utils.directions import direction_index
from src.engine.scenes.scene import Scene
from src.game.levels import global_round, next_round, round_config
from src.engine.service_locator import ServiceLocator


class PlayScene(Scene):
    def do_create(self):
        configs = ServiceLocator.configs_service
        self.enemies_cfg = configs.get("assets/cfg/enemies.json")
        self.player_cfg = configs.get("assets/cfg/player.json")
        self.bullet_cfg = configs.get("assets/cfg/bullet.json")
        self.explosion_cfg = configs.get("assets/cfg/explosion.json")
        self.shield_cfg = configs.get("assets/cfg/shield.json")
        self.boss_cfg = configs.get("assets/cfg/boss.json")
        self.base_cfg = configs.get("assets/cfg/base.json")
        self.obstacles_cfg = configs.get("assets/cfg/obstacles.json")
        self.alert_cfg = configs.get("assets/cfg/alert.json")
        self.formations_cfg = configs.get("assets/cfg/formations.json")
        self.score_cfg = configs.get("assets/cfg/score.json")
        self._state = self._game_state()
        self.interface_cfg = configs.get(INTERFACE_CFG)
        # Lo común del nivel combinado con lo propio de la ronda que se juega
        self.level_cfg = round_config(self._state.level_index, self._state.round_index)

        self.is_paused = False
        self._paused_before_event = False
        # En pausa: "menu" (opciones) o "info" (instrucciones o créditos)
        self._pause_view = "menu"
        # Entidades del mundo ocultas durante la pausa
        self._hidden_by_pause: list[int] = []
        # Depuración: dibuja los rectángulos de colisión (F2)
        self._show_hitboxes = False
        # Segundos que faltan para que reaparezca el jugador tras morir (None: está vivo)
        self._respawn_timer: float | None = None
        # Al destruir todas las bases se pasa de ronda tras un mensaje (None: ronda en curso)
        self._level_clear_timer: float | None = None
        # Sin vidas, se espera a que acabe la explosión y se pasa a la derrota (None: se sigue jugando)
        self._game_over_timer: float | None = None
        # Despegue al empezar la ronda: el jugador no se puede mover (None: ya terminó)
        self._cutscene_timer: float | None = None

        self._spawn_player()
        # Flechas pulsadas, en el orden en que se pulsaron (la última manda en su eje)
        self._player_directions: list[str] = []
        # Al soltar una flecha, el cambio de dirección espera un instante (ver do_action)
        self._pending_release_time: float | None = None

        create_enemy_spawner(self.ecs_world, self.level_cfg["enemies"])
        create_alert(self.ecs_world, self.level_cfg["alert"], self.level_cfg["spy"])
        create_formation_spawner(self.ecs_world, self.level_cfg["formations"])
        item_spawner = self.ecs_world.create_entity()
        self.ecs_world.add_component(item_spawner, CShieldItemSpawner(self.level_cfg["shield_item"]))
        for place_info in self.level_cfg["bases"]:
            create_base(self.ecs_world, place_info, self.base_cfg, self.level_cfg["base_behavior"])
        spawn = self.level_cfg["player_spawn"]["position"]
        spawn_center = pygame.Vector2(spawn["x"], spawn["y"])
        # Los obstáculos se reparten lejos de las bases y, en la ronda del jefe, de él
        keep_clear = [pygame.Vector2(b["position"]["x"], b["position"]["y"]) for b in self.level_cfg["bases"]]
        if self.level_cfg.get("boss"):
            offset = self.boss_cfg["spawn_offset"]
            boss_center = spawn_center + pygame.Vector2(offset["x"], offset["y"])
            create_boss(self.ecs_world, boss_center, self.boss_cfg, self.player_cfg["max_speed"])
            create_boss_bar(self.ecs_world, self.boss_cfg["bar"])
            keep_clear.append(boss_center)
        create_obstacles(
            self.ecs_world,
            self.level_cfg["obstacles"],
            self.obstacles_cfg,
            spawn_center,
            keep_clear,
            pygame.Vector2(self.level_cfg["world"]["size"]["w"], self.level_cfg["world"]["size"]["h"]),
        )
        create_input_commands(self.ecs_world, "play")
        create_input_commands(self.ecs_world, "menu")
        # Esc pausa el juego, pero dentro de la pausa solo sirve para volver (como en los menús)
        menu_back = configs.get("assets/cfg/input.json")["menu"]["MENU_BACK"]
        self._menu_back_keys = {input_binding(key_info) for key_info in menu_back}

        viewport_info = self.interface_cfg["game"]["viewport"]
        world_info = self.level_cfg["world"]
        create_world(self.ecs_world, world_info)
        create_world_background(self.ecs_world, world_info, viewport_info)
        create_sidebar(
            self.ecs_world,
            self._state.hi_score,
            self._state.score,
            global_round(self._state.level_index, self._state.round_index),
        )
        create_lives_display(self.ecs_world, self.score_cfg)
        shield_hud = self.shield_cfg["hud"]
        shield_text = create_text(self.ecs_world, shield_hud, "")
        self.ecs_world.add_component(shield_text, CShieldDisplay(shield_hud))
        score_entity = self.ecs_world.create_entity()
        self.ecs_world.add_component(score_entity, CScore(self._state, self.score_cfg))
        create_minimap(self.ecs_world, pygame.Vector2(world_info["size"]["w"], world_info["size"]["h"]))
        create_camera(self.ecs_world, viewport_info)
        if self._state.cheat:
            self._show_cheat_texts()
        # Cada nivel puede tener su música; si es la misma que ya sonaba, continúa
        music = self.interface_cfg["music"]
        level_music = self.level_cfg.get("music", music["default_level"])
        ServiceLocator.sounds_service.play_music(level_music, music["volume"])
        self._start_cutscene()
        # Se colocan cámara, estrellas, minimapa y vidas antes del primer cuadro
        system_camera(self.ecs_world)
        system_starfield(self.ecs_world, 0)
        system_minimap(self.ecs_world)
        system_score_display(self.ecs_world, self.score_cfg["life_icons"]["max"])
        system_shield_display(self.ecs_world)
        system_boss_bar(self.ecs_world)

    def do_update(self, delta_time: float):
        self._delta_time = delta_time
        # En pausa no se ejecuta ningún sistema de juego: nada se mueve, choca ni se anima.
        # Las estrellas siguen brillando, pero quietas (la cámara no se mueve)
        if self.is_paused:
            system_starfield(self.ecs_world, delta_time)
            system_menu(self.ecs_world)
            return
        if self._cutscene_timer is not None:
            self._update_cutscene()
            return
        self._update_respawn()
        self._update_pending_release()
        viewport = self.interface_cfg["game"]["viewport"]
        view_size = pygame.Vector2(viewport["w"], viewport["h"])
        system_alert_condition(self.ecs_world, delta_time, self.alert_cfg)
        system_spy_spawner(self.ecs_world, delta_time, self.enemies_cfg, self.player_cfg["max_speed"], view_size)
        system_enemy_spawner(
            self.ecs_world,
            delta_time,
            self.enemies_cfg,
            self.player_cfg["max_speed"],
            view_size,
        )
        system_enemy_ai(self.ecs_world, delta_time, self.enemies_cfg["spawn"]["despawn_distance"])
        system_formation_spawner(
            self.ecs_world, delta_time, self.formations_cfg, self.enemies_cfg, self.player_cfg["max_speed"]
        )
        system_boss(
            self.ecs_world, delta_time, self.boss_cfg, self.enemies_cfg, self.formations_cfg, self.player_cfg["max_speed"]
        )
        system_homing_shot(self.ecs_world, delta_time)
        system_player_ship(self.ecs_world, delta_time)
        system_player_state(self.ecs_world)
        system_movement(self.ecs_world, delta_time)
        system_formation(self.ecs_world, delta_time, self.enemies_cfg, self.player_cfg["max_speed"])
        system_directional_sprite(self.ecs_world)
        # Lo que cruza un borde del mundo aparece por el lado contrario
        system_world_wrap(self.ecs_world)
        system_base_core(self.ecs_world, delta_time)
        system_base_turret(self.ecs_world, delta_time, self.base_cfg["bullet"])
        system_base_core_spawner(self.ecs_world, self.enemies_cfg, self.player_cfg["max_speed"])
        # Las balas desaparecen al alejarse de lo que se ve
        system_screen_bullet(self.ecs_world, camera_rect(self.ecs_world))
        system_collision_player_enemy(self.ecs_world, self.explosion_cfg, self.player_cfg)
        system_collision_player_base(self.ecs_world, self.explosion_cfg, self.player_cfg)
        system_collision_enemy_bullet(self.ecs_world, self.explosion_cfg, self.player_cfg)
        system_collision_bullet_enemy(self.ecs_world, self.explosion_cfg)
        system_collision_bullet_base(self.ecs_world, self.base_cfg, self.explosion_cfg)
        system_collision_obstacle(self.ecs_world, self.obstacles_cfg, self.explosion_cfg, self.player_cfg)
        system_collision_boss(self.ecs_world, self.boss_cfg, self.explosion_cfg, self.player_cfg)
        system_collision_enemy_bounce(self.ecs_world)
        system_shield_item_spawner(self.ecs_world, delta_time, self.shield_cfg)
        system_shield_item(self.ecs_world, delta_time, self.shield_cfg)
        system_shield(self.ecs_world, delta_time)
        system_spawn_protection(self.ecs_world, delta_time)
        system_screen_shake(self.ecs_world, delta_time)
        system_animation(self.ecs_world, delta_time)
        system_explosion_kill(self.ecs_world)
        system_explosion_burst(self.ecs_world, delta_time)
        system_lifetime(self.ecs_world, delta_time)
        system_blink(self.ecs_world, delta_time)
        system_camera(self.ecs_world)
        system_spy(self.ecs_world)
        system_condition_display(self.ecs_world, delta_time, self.alert_cfg)
        system_starfield(self.ecs_world, delta_time)
        system_minimap(self.ecs_world)
        system_score_display(self.ecs_world, self.score_cfg["life_icons"]["max"])
        system_shield_display(self.ecs_world)
        system_boss_bar(self.ecs_world)
        self._update_level_clear()
        self._update_game_over()

    def _game_state(self):
        """Estado de la partida que se juega (la demostración usa uno propio)."""
        return self._game_engine.state

    def do_process_events(self, event: pygame.event.Event):
        # Una tecla puede activar varios comandos (Z dispara y acepta; Esc pausa y vuelve) y
        # esper no garantiza en qué orden llegan: si uno pausa o reanuda, los demás de esa
        # misma pulsación se ignoran (así "CONTINUAR" con Z no dispara)
        self._paused_before_event = self.is_paused
        super().do_process_events(event)

    def do_action(self, action: CInputCommand):
        if self.is_paused != self._paused_before_event:
            return
        if action.name == "PAUSE" and action.phase == CommandPhase.START:
            # No se pausa durante el despegue ni cuando la partida ya terminó
            if self.is_paused:
                if (action.input_type, action.key) not in self._menu_back_keys:
                    self._resume()
            elif self._cutscene_timer is None and self._game_over_timer is None:
                self._pause()
            return
        if self.is_paused:
            self._do_pause_action(action)
            return
        if action.name.startswith("MENU_"):
            return
        if action.name.startswith("CHEAT_"):
            if action.phase == CommandPhase.START:
                self._do_cheat(action.name)
            return
        if action.name == "EDITOR_TOGGLE" and action.phase == CommandPhase.START:
            # Editor de niveles: edita la ronda que se está jugando
            self.switch_scene("EDITOR")
            return
        if action.name == "TOGGLE_HITBOXES" and action.phase == CommandPhase.START:
            self._show_hitboxes = not self._show_hitboxes
        elif action.name in ("PLAYER_LEFT", "PLAYER_RIGHT", "PLAYER_UP", "PLAYER_DOWN"):
            # Durante el despegue no se puede mover
            if self._cutscene_timer is not None:
                return
            if action.name in self._player_directions:
                self._player_directions.remove(action.name)
            if action.phase == CommandPhase.START:
                self._player_directions.append(action.name)
                self._pending_release_time = None
                self._apply_held_direction()
            elif self._held_direction().length_squared() > 0:
                # Al soltar una flecha se espera un instante antes de seguir las que quedan: si es
                # el final de una diagonal, la otra flecha se suelta enseguida y la diagonal se
                # mantiene; si se sigue pulsando la otra, la nave toma esa dirección
                self._pending_release_time = self.player_cfg["release_grace"]
            else:
                # Sin flechas pulsadas la nave sigue en la dirección que llevaba: nunca se detiene
                self._pending_release_time = None
        elif action.name == "PLAYER_SPECIAL" and action.phase == CommandPhase.START:
            if self._cutscene_timer is None and self._player_alive():
                self._use_shield()
        elif action.name == "PLAYER_FIRE" and action.phase == CommandPhase.START:
            if self._cutscene_timer is not None or not self._player_alive():
                return
            num_bullets = len(self.ecs_world.get_component(CTagBullet))
            if num_bullets < self.bullet_cfg["max_bullets"]:
                create_player_shots(
                    self.ecs_world,
                    self._player_c_t.pos + pygame.Vector2(self._player_c_s.area.size) / 2,
                    self._player_c_ship.direction,
                    self._player_c_v.vel,
                    self.bullet_cfg,
                    self.level_cfg["triple_shot"],
                )

    def draw(self, screen: pygame.Surface):
        system_rendering(self.ecs_world, screen, self._show_hitboxes)

    def _spawn_player(self):
        self._player_entity = create_player(
            self.ecs_world, self.player_cfg, self.level_cfg["player_spawn"]
        )
        self._player_c_v = self.ecs_world.component_for_entity(self._player_entity, CVelocity)
        self._player_c_t = self.ecs_world.component_for_entity(self._player_entity, CTransform)
        self._player_c_s = self.ecs_world.component_for_entity(self._player_entity, CSurface)
        self._player_c_ship = self.ecs_world.component_for_entity(self._player_entity, CPlayerShip)
        if self._state.cheat:
            self.ecs_world.add_component(self._player_entity, CTagInvincible())

    def _player_alive(self) -> bool:
        return self.ecs_world.entity_exists(self._player_entity)

    def _update_respawn(self):
        """Al morir se pierde una vida: el jugador reaparece en el punto de partida al cabo de
        unos segundos. Si no le quedaban vidas de reserva, se acaba la partida."""
        if self._player_alive() or self._game_over_timer is not None:
            return
        if self._respawn_timer is None:
            self._state.lives_lost += 1
            if self._state.lives == 0:
                self._game_over_timer = self.interface_cfg["death_to_defeat"]
                return
            self._respawn_timer = self.player_cfg["death"]["respawn_time"]
        self._respawn_timer -= self._delta_time
        if self._respawn_timer <= 0:
            self._respawn_timer = None
            self._state.lives -= 1
            self._spawn_player()
            protection = self.player_cfg["respawn_protection"]
            self.ecs_world.add_component(
                self._player_entity, CSpawnProtection(protection["duration"], protection["blink"])
            )

    def _update_game_over(self):
        if self._game_over_timer is None:
            return
        self._game_over_timer -= self._delta_time
        if self._game_over_timer <= 0:
            self.switch_scene("DEFEAT")

    def _update_level_clear(self):
        """Sin bases en pie, se anuncia la ronda superada y después se pasa a la siguiente
        (que puede ser la primera del nivel siguiente) o a la victoria si era la última."""
        if self._level_clear_timer is None:
            if self.ecs_world.get_component(CBase) or self.ecs_world.get_component(CBoss):
                return
            if self._game_over_timer is not None:
                return
            # Al terminar la última ronda de un nivel se anuncia el nivel superado
            following = next_round(self._state.level_index, self._state.round_index)
            level_done = following is None or following[0] != self._state.level_index
            if self.level_cfg.get("boss"):
                clear_info = self.interface_cfg["boss_defeated"]
            else:
                clear_info = self.interface_cfg["level_clear" if level_done else "round_clear"]
            self._level_clear_timer = clear_info["duration"]
            text_entity = create_text(self.ecs_world, clear_info)
            self.ecs_world.add_component(text_entity, CLifetime(clear_info["duration"]))
            return
        self._level_clear_timer -= self._delta_time
        if self._level_clear_timer <= 0:
            following = next_round(self._state.level_index, self._state.round_index)
            if following is None:
                self.switch_scene("VICTORY")
            else:
                self._state.level_index, self._state.round_index = following
                self.switch_scene("PLAY")

    def _start_cutscene(self):
        """Despegue al empezar la ronda: las estrellas pasan a toda velocidad y van frenando,
        "BLAST OFF!" parpadea y suena; mientras tanto el jugador no se puede mover."""
        cutscene_info = self.interface_cfg["cutscene"]
        duration = cutscene_info["duration"]
        self._cutscene_timer = duration
        for entity, _ in self.ecs_world.get_component(CStarfield):
            self.ecs_world.add_component(entity, CWarp(duration, cutscene_info["warp_speed"]))
        blast_entity = create_text(self.ecs_world, cutscene_info["blast_off"])
        self.ecs_world.add_component(blast_entity, CBlink(cutscene_info["blink"]))
        self.ecs_world.add_component(blast_entity, CLifetime(duration))
        start_info = self.interface_cfg["level_start"]
        round_info = start_info["round"]
        # Un nivel puede tener su propio anuncio (el del jefe); si no, "NIVEL n - RONDA m"
        round_text = self.level_cfg.get("start_text") or round_info["text"].format(
            level=self._state.level_index + 1, round=self._state.round_index + 1
        )
        round_entity = create_text(self.ecs_world, round_info, round_text)
        self.ecs_world.add_component(round_entity, CLifetime(duration + start_info["duration"]))
        ServiceLocator.sounds_service.play(cutscene_info["sound"])

    def _update_cutscene(self):
        dt = self._delta_time
        self._cutscene_timer -= dt
        system_warp(self.ecs_world, dt)
        system_starfield(self.ecs_world, dt)
        system_blink(self.ecs_world, dt)
        system_lifetime(self.ecs_world, dt)
        system_camera(self.ecs_world)
        system_minimap(self.ecs_world)
        system_score_display(self.ecs_world, self.score_cfg["life_icons"]["max"])
        system_boss_bar(self.ecs_world)
        if self._cutscene_timer <= 0:
            self._cutscene_timer = None
            # Por si el último cuadro no llegó justo al final del efecto, las estrellas se detienen
            for entity, c_sf in self.ecs_world.get_component(CStarfield):
                c_sf.fall_speed = 0
                if self.ecs_world.has_component(entity, CWarp):
                    self.ecs_world.remove_component(entity, CWarp)
            # Ya se puede jugar: se anuncia la habilidad especial del nivel, si la tiene
            start_info = self.interface_cfg["level_start"]
            if self.level_cfg["triple_shot"]:
                text_entity = create_text(self.ecs_world, start_info["triple_shot"])
                self.ecs_world.add_component(text_entity, CLifetime(start_info["duration"]))

    def _pause(self):
        """En pausa desaparecen las naves y todo lo del mundo menos las estrellas, el radar se
        queda vacío y aparece el menú de opciones."""
        self.is_paused = True
        hidden = {entity for entity, _ in self.ecs_world.get_component(CTagHidden)}
        ui = {entity for entity, _ in self.ecs_world.get_component(CTagUI)}
        stars = {entity for entity, _ in self.ecs_world.get_component(CStarfield)}
        play_width = self.interface_cfg["game"]["viewport"]["w"]
        self._hidden_by_pause = []
        for entity, (c_t, _) in self.ecs_world.get_components(CTransform, CSurface):
            # Se ocultan el mundo y los mensajes sobre la zona de juego; el panel lateral no
            in_play_area = entity not in ui or c_t.pos.x < play_width
            if entity not in hidden and entity not in stars and in_play_area:
                self.ecs_world.add_component(entity, CTagHidden())
                self._hidden_by_pause.append(entity)
        for _, c_mm in self.ecs_world.get_component(CMinimap):
            c_mm.empty = True
        system_minimap(self.ecs_world)
        ServiceLocator.sounds_service.pause_all()
        self._show_pause_menu()

    def _resume(self):
        self.is_paused = False
        self._clear_pause_ui()
        for entity in self._hidden_by_pause:
            if self.ecs_world.entity_exists(entity) and self.ecs_world.has_component(entity, CTagHidden):
                self.ecs_world.remove_component(entity, CTagHidden)
        self._hidden_by_pause = []
        for _, c_mm in self.ecs_world.get_component(CMinimap):
            c_mm.empty = False
        # Las flechas que se soltaron durante la pausa no deben seguir contando
        self._player_directions = []
        self._pending_release_time = None
        ServiceLocator.sounds_service.resume_all()

    def _show_pause_menu(self):
        self._clear_pause_ui()
        self._pause_view = "menu"
        before = self._ui_entities()
        create_text(self.ecs_world, self.interface_cfg["paused"])
        menu_info = self.interface_cfg["pause_menu"]
        create_menu(self.ecs_world, menu_info, menu_info["options"])
        self._tag_pause_ui(before)

    def _show_pause_info(self, cfg_key: str):
        """Las mismas instrucciones o créditos del título, sin salir de la partida."""
        self._clear_pause_ui()
        self._pause_view = "info"
        before = self._ui_entities()
        for text_info in self.interface_cfg[cfg_key]["texts"]:
            create_text(self.ecs_world, text_info)
        self._tag_pause_ui(before)

    def _ui_entities(self) -> set[int]:
        ui = {entity for entity, _ in self.ecs_world.get_component(CTagUI)}
        return ui | {entity for entity, _ in self.ecs_world.get_component(CMenu)}

    def _tag_pause_ui(self, before: set[int]):
        # Lo que se acaba de crear pertenece a la pausa y se borra al salir de ella
        for entity in self._ui_entities() - before:
            self.ecs_world.add_component(entity, CTagPauseUI())

    def _clear_pause_ui(self):
        for entity, _ in self.ecs_world.get_component(CTagPauseUI):
            self.ecs_world.delete_entity(entity)

    def _do_pause_action(self, action: CInputCommand):
        if action.phase != CommandPhase.START:
            return
        if self._pause_view == "info":
            if action.name in ("MENU_ACCEPT", "MENU_BACK"):
                self._show_pause_menu()
            return
        if action.name == "MENU_UP":
            menu_move(self.ecs_world, -1)
        elif action.name == "MENU_DOWN":
            menu_move(self.ecs_world, 1)
        elif action.name == "MENU_BACK":
            self._resume()
        elif action.name == "MENU_ACCEPT":
            choice = menu_action(self.ecs_world)
            if choice == "RESUME":
                self._resume()
            elif choice == "LEVELS":
                self.switch_scene("LEVEL_SELECT")
            elif choice == "INSTRUCTIONS":
                self._show_pause_info("instructions")
            elif choice == "CREDITS":
                self._show_pause_info("credits")
            elif choice == "QUIT":
                self.switch_scene("TITLE")

    def _do_cheat(self, name: str):
        """Modo trampa (T), para poder observar el juego: invencible y con atajos."""
        if name == "CHEAT_TOGGLE":
            self._state.cheat = not self._state.cheat
            if self._player_alive():
                if self._state.cheat:
                    self.ecs_world.add_component(self._player_entity, CTagInvincible())
                else:
                    self.ecs_world.remove_component(self._player_entity, CTagInvincible)
            if self._state.cheat:
                self._show_cheat_texts()
            else:
                for entity, _ in self.ecs_world.get_component(CTagCheatUI):
                    self.ecs_world.delete_entity(entity)
            return
        if not self._state.cheat or self._cutscene_timer is not None:
            return
        if name == "CHEAT_NEXT_ROUND":
            # Caen todas las bases (sin puntos) y se pasa de ronda como de costumbre
            for base_entity, _ in self.ecs_world.get_component(CBase):
                destroy_base(self.ecs_world, base_entity, self.base_cfg, self.explosion_cfg)
            for boss_entity, _ in self.ecs_world.get_component(CBoss):
                destroy_boss(self.ecs_world, boss_entity, self.boss_cfg, self.explosion_cfg)
        elif name == "CHEAT_ALERT":
            cycle = self.interface_cfg["cheat"]["alert_cycle"]
            current = alert_level(self.ecs_world)
            set_alert_level(self.ecs_world, cycle[(cycle.index(current) + 1) % len(cycle)], self.alert_cfg)
        elif name == "CHEAT_SPY" and self._player_alive():
            viewport = self.interface_cfg["game"]["viewport"]
            spawn_spy(
                self.ecs_world,
                self._player_c_t.pos + pygame.Vector2(self._player_c_s.area.size) / 2,
                self.enemies_cfg,
                self.player_cfg["max_speed"],
                pygame.Vector2(viewport["w"], viewport["h"]),
            )
        elif name == "CHEAT_FORMATION":
            for _, c_fs in self.ecs_world.get_component(CFormationSpawner):
                spawn_formation(self.ecs_world, c_fs, self.formations_cfg, self.enemies_cfg, self.player_cfg["max_speed"])
        elif name == "CHEAT_SHIELD":
            self._state.shield_charges = min(self.shield_cfg["max_charges"], self._state.shield_charges + 1)

    def _show_cheat_texts(self):
        for text_info in self.interface_cfg["cheat"]["texts"]:
            self.ecs_world.add_component(create_text(self.ecs_world, text_info), CTagCheatUI())

    def _use_shield(self):
        """Gasta una carga de escudo (tecla X); sin cargas o con el escudo ya activo, avisa."""
        if self._state.shield_charges <= 0 or has_shield(self.ecs_world, self._player_entity):
            ServiceLocator.sounds_service.play(self.shield_cfg["sounds"]["denied"])
            return
        self._state.shield_charges -= 1
        activate_shield(self.ecs_world, self._player_entity, self.shield_cfg)

    def _apply_held_direction(self):
        direction = self._held_direction()
        if direction.length_squared() > 0:
            steer_player(self.ecs_world, direction_index(direction))

    def _update_pending_release(self):
        if self._pending_release_time is None:
            return
        self._pending_release_time -= self._delta_time
        if self._pending_release_time <= 0:
            self._pending_release_time = None
            self._apply_held_direction()

    def _held_direction(self) -> pygame.Vector2:
        """Dirección de las flechas pulsadas; si dos de un mismo eje se pulsan a la vez
        (izquierda y derecha, o arriba y abajo), manda la última que se pulsó."""
        axes = {"PLAYER_LEFT": (0, -1), "PLAYER_RIGHT": (0, 1), "PLAYER_UP": (1, -1), "PLAYER_DOWN": (1, 1)}
        direction = [0, 0]
        for name in self._player_directions:
            axis, sign = axes[name]
            direction[axis] = sign
        return pygame.Vector2(direction)
