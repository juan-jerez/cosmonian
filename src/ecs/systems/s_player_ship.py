import esper

from src.ecs.components.c_player_ship import CPlayerShip
from src.ecs.components.c_velocity import CVelocity
from src.ecs.utils.directions import DIRECTIONS, turn_step


def system_player_ship(world: esper.World, delta_time: float):
    for _, (c_v, c_ship) in world.get_components(CVelocity, CPlayerShip):
        if c_ship.direction == c_ship.target_direction:
            # Así el próximo cambio de dirección empieza a girar enseguida
            c_ship.turn_timer = 0
        else:
            c_ship.turn_timer -= delta_time
            while c_ship.turn_timer <= 0 and c_ship.direction != c_ship.target_direction:
                step = turn_step(c_ship.direction, c_ship.target_direction)
                c_ship.direction = (c_ship.direction + step) % 8
                c_ship.turn_timer += c_ship.turn_time
                if c_ship.turn_time <= 0:
                    c_ship.direction = c_ship.target_direction

        c_ship.speed = min(c_ship.max_speed, c_ship.speed + c_ship.acceleration * delta_time)
        c_v.vel = DIRECTIONS[c_ship.direction] * c_ship.speed


def steer_player(world: esper.World, direction: int):
    """Cambia la dirección a la que quiere ir la nave; el giro lo hace system_player_ship."""
    for _, c_ship in world.get_component(CPlayerShip):
        c_ship.target_direction = direction
