import pygame


class SoundsService:
    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        # Música que está sonando (se lee del archivo mientras suena, no se carga entera)
        self._music: str | None = None

    def get(self, path: str) -> pygame.mixer.Sound:
        if path not in self._sounds:
            self._sounds[path] = pygame.mixer.Sound(path)
        return self._sounds[path]

    def play(self, path: str) -> None:
        self.get(path).play()

    def play_loop(self, path: str, volume: float = 1.0) -> None:
        """Reproduce el sonido en bucle hasta que se llame a stop."""
        sound = self.get(path)
        sound.set_volume(volume)
        sound.play(loops=-1)

    def stop(self, path: str) -> None:
        self.get(path).stop()

    def pause_all(self) -> None:
        pygame.mixer.pause()
        pygame.mixer.music.pause()

    def resume_all(self) -> None:
        pygame.mixer.unpause()
        pygame.mixer.music.unpause()

    def stop_all(self) -> None:
        """Corta todos los efectos (también los pausados), por ejemplo al cambiar de escena. La
        música sigue: cada escena decide si cambia, continúa o se detiene."""
        pygame.mixer.stop()
        pygame.mixer.unpause()
        pygame.mixer.music.unpause()

    def play_music(self, path: str, volume: float) -> None:
        """Música de fondo en bucle; si ya suena la misma, sigue sin volver a empezar."""
        pygame.mixer.music.set_volume(volume)
        if self._music == path:
            return
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(loops=-1)
        self._music = path

    def stop_music(self) -> None:
        pygame.mixer.music.stop()
        self._music = None
