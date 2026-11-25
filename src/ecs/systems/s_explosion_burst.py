import random

import pygame
import esper

from src.create.prefab_creator import create_explosion
from src.ecs.components.c_explosion_burst import CExplosionBurst
from src.ecs.components.c_transform import CTransform


def system_explosion_burst(world: esper.World, delta_time: float):
    for entity, (c_t, c_eb) in world.get_components(CTransform, CExplosionBurst):
        c_eb.timer -= delta_time
        while c_eb.timer <= 0 and c_eb.explosions_left > 0:
            offset = pygame.Vector2(random.uniform(0, c_eb.radius), 0).rotate(random.uniform(0, 360))
            create_explosion(world, c_t.pos + offset, c_eb.explosion_info)
            c_eb.explosions_left -= 1
            c_eb.timer += c_eb.interval
        if c_eb.explosions_left == 0:
            world.delete_entity(entity)
