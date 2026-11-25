from enum import Enum


class CIntroTimeline:
    def __init__(self, times_info: dict, credits_count: int) -> None:
        self.stage = IntroStage.STARS
        self.stage_time: float = 0
        # Duración de cada etapa en segundos
        self.durations = {
            IntroStage.STARS: times_info["stars"],
            IntroStage.CREDITS: (
                times_info["wipe"]
                + times_info["slide"]
                + times_info["stagger"] * (credits_count - 1)
                + times_info["hold"]
            ),
            IntroStage.OUTRO: times_info["slide_out"],
            IntroStage.CLOSE: times_info["wipe"],
        }


class IntroStage(Enum):
    STARS = 0
    CREDITS = 1
    OUTRO = 2
    CLOSE = 3
    DONE = 4
