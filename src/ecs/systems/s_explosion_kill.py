import esper

from src.ecs.components.c_animation import CAnimation
from src.ecs.components.tags.c_tag_explosion import CTagExplosion


def system_explosion_kill(world: esper.World):
    query = world.get_components(CAnimation, CTagExplosion)

    for explosion_entity, (c_a, _) in query:
        # La explosión desaparece cuando su animación termina por primera vez
        if c_a.loops_completed > 0:
            world.delete_entity(explosion_entity)
