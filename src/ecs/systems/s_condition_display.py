import esper

from src.create.prefab_ui import color_from_cfg, render_text
from src.ecs.components.c_alert_condition import CAlertCondition
from src.ecs.components.c_condition_display import CConditionDisplay
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform


def system_condition_display(world: esper.World, delta_time: float, alert_info: dict):
    """Muestra la condición en el panel lateral; mientras hay un espía a la vista parpadea
    "¡ESPIA!" alternando con la condición."""
    level = "GREEN"
    spy_visible = False
    for _, c_ac in world.get_component(CAlertCondition):
        level = c_ac.level
        spy_visible = c_ac.spy_visible

    for _, (c_t, c_s, c_cd) in world.get_components(CTransform, CSurface, CConditionDisplay):
        if spy_visible:
            c_cd.blink_timer -= delta_time
            if c_cd.blink_timer <= 0:
                c_cd.blink_on = not c_cd.blink_on
                c_cd.blink_timer = alert_info["spy_blink"]
        else:
            c_cd.blink_on = False
            c_cd.blink_timer = 0
        style_name = "SPY" if spy_visible and c_cd.blink_on else level
        if style_name == c_cd.style:
            continue
        # Solo se vuelve a dibujar el texto cuando cambia
        c_cd.style = style_name
        style = alert_info["styles"][style_name]
        world.component_for_entity(c_cd.bar_entity, CSurface).surf.fill(color_from_cfg(style["bar"]))
        c_s.surf = render_text({"text": style["text"]}, color=color_from_cfg(style["text_color"]))
        c_s.area = c_s.surf.get_rect()
        c_t.pos.xy = c_cd.center - (c_s.area.w / 2, c_s.area.h / 2)
