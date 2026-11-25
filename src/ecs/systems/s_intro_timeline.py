import esper

from src.create.prefab_intro import create_intro_close, create_intro_credits, create_intro_outro
from src.ecs.components.c_intro_member import CIntroMember
from src.ecs.components.c_intro_timeline import CIntroTimeline, IntroStage


def system_intro_timeline(world: esper.World, delta_time: float, intro_info: dict):
    for _, c_tl in world.get_component(CIntroTimeline):
        c_tl.stage_time += delta_time
        duration = c_tl.durations.get(c_tl.stage)
        if duration is None or c_tl.stage_time < duration:
            continue

        if c_tl.stage == IntroStage.STARS:
            for entity, c_member in world.get_component(CIntroMember):
                if c_member.group == "stars_screen":
                    world.delete_entity(entity)
            create_intro_credits(world, intro_info)
            c_tl.stage = IntroStage.CREDITS
        elif c_tl.stage == IntroStage.CREDITS:
            create_intro_outro(world, intro_info)
            c_tl.stage = IntroStage.OUTRO
        elif c_tl.stage == IntroStage.OUTRO:
            create_intro_close(world, intro_info)
            c_tl.stage = IntroStage.CLOSE
        elif c_tl.stage == IntroStage.CLOSE:
            c_tl.stage = IntroStage.DONE
        c_tl.stage_time = 0


def intro_finished(world: esper.World) -> bool:
    return any(c_tl.stage == IntroStage.DONE for _, c_tl in world.get_component(CIntroTimeline))
