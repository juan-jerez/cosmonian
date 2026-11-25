class CAnimation:
    def __init__(self, animations: dict) -> None:
        self.number_frames: int = animations["number_frames"]
        self.animations_list: list[AnimationData] = []
        if self.number_frames <= 0:
            raise ValueError("number_frames debe ser mayor que cero")
        for anim in animations["list"]:
            anim_data = AnimationData(anim)
            if anim_data.end >= self.number_frames:
                raise ValueError(
                    f"Animación {anim_data.name}: el cuadro final ({anim_data.end}) "
                    f"excede el número de cuadros ({self.number_frames})"
                )
            self.animations_list.append(anim_data)
        self.curr_anim = 0
        self.curr_frame = self.animations_list[0].start
        self.curr_anim_time = self.animations_list[0].framerate
        # Veces que la animación actual ha llegado a su último cuadro y reiniciado
        self.loops_completed = 0

    def get_index(self, name: str) -> int:
        for index, anim in enumerate(self.animations_list):
            if anim.name == name:
                return index
        raise KeyError(f"Animación no encontrada: {name}")


class AnimationData:
    def __init__(self, anim_data: dict) -> None:
        self.name: str = anim_data["name"]
        self.start: int = anim_data["start"]
        self.end: int = anim_data["end"]
        if self.start < 0 or self.end < self.start:
            raise ValueError(
                f"Animación {self.name}: el cuadro final debe ser igual o mayor que el de inicio"
            )
        if anim_data["framerate"] <= 0:
            raise ValueError(f"Animación {self.name}: el framerate no puede ser cero")
        # Tiempo en segundos que dura cada cuadro
        self.framerate: float = 1.0 / anim_data["framerate"]
