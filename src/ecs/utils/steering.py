"""Steering behaviours (Craig Reynolds): cada uno devuelve la velocidad deseada; el giro hacia
ella lo limita apply_steering con la fuerza máxima del agente."""

import pygame


def seek(to_target: pygame.Vector2, max_speed: float) -> pygame.Vector2:
    """Ir directo hacia el objetivo (`to_target` es el vector desde el agente hasta él)."""
    if to_target.length_squared() == 0:
        return pygame.Vector2(0, 0)
    return to_target.normalize() * max_speed


def flee(to_target: pygame.Vector2, max_speed: float) -> pygame.Vector2:
    """Alejarse del objetivo."""
    return -seek(to_target, max_speed)


def wander(velocity: pygame.Vector2, turn: float, max_speed: float) -> pygame.Vector2:
    """Seguir más o menos el rumbo actual, girándolo `turn` grados."""
    if velocity.length_squared() == 0:
        return pygame.Vector2(max_speed, 0).rotate(turn)
    return velocity.normalize().rotate(turn) * max_speed


def apply_steering(
    velocity: pygame.Vector2, desired: pygame.Vector2, max_force: float, max_speed: float, delta_time: float
) -> pygame.Vector2:
    """Acerca la velocidad a la deseada sin superar la fuerza máxima, y la deja en max_speed
    (los enemigos nunca frenan: solo cambian de rumbo)."""
    steering = desired - velocity
    max_change = max_force * delta_time
    if steering.length() > max_change:
        steering.scale_to_length(max_change)
    new_velocity = velocity + steering
    if new_velocity.length_squared() == 0:
        return velocity
    return new_velocity.normalize() * max_speed
