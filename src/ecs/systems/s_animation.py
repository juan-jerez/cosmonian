import esper

from src.ecs.components.c_animation import CAnimation
from src.ecs.components.c_surface import CSurface


def system_animation(world: esper.World, delta_time: float):
    query = world.get_components(CSurface, CAnimation)

    for _, (c_s, c_a) in query:
        anim = c_a.animations_list[c_a.curr_anim]
        c_a.curr_anim_time -= delta_time
        while c_a.curr_anim_time <= 0:
            c_a.curr_anim_time += anim.framerate
            c_a.curr_frame += 1
            if c_a.curr_frame > anim.end:
                c_a.curr_frame = anim.start
                c_a.loops_completed += 1
        set_frame_area(c_s, c_a)


def set_frame_area(c_s: CSurface, c_a: CAnimation):
    frame_w = c_s.surf.get_width() // c_a.number_frames
    c_s.area.w = frame_w
    c_s.area.x = frame_w * c_a.curr_frame


def set_animation(c_a: CAnimation, name: str):
    index = c_a.get_index(name)
    if c_a.curr_anim == index:
        return
    c_a.curr_anim = index
    c_a.curr_frame = c_a.animations_list[index].start
    c_a.curr_anim_time = c_a.animations_list[index].framerate
    c_a.loops_completed = 0


def set_frame(c_s: CSurface, frame: int):
    """Muestra un cuadro concreto de una tira, para entidades que eligen su cuadro según su
    estado en lugar de animarse solas."""
    c_s.area.x = c_s.area.w * frame
