"""Music and sound settings declared with reusable option definitions."""

from src import settings
from src.decorators import option_def
from .option_menu import OptionMenuScene


VOLUME_STEPS = (0.0, 0.25, 0.5, 0.75, 1.0)


class AudioOptionsScene(OptionMenuScene):
    title = "MUSIC & SOUNDS"

    @option_def("master_volume", "MASTER VOLUME", VOLUME_STEPS, order=0, description="Controls all game audio.")
    def master_volume(self, value):
        settings.apply_audio()

    @option_def("music_volume", "MUSIC VOLUME", VOLUME_STEPS, order=1, description="Controls music playback volume.")
    def music_volume(self, value):
        settings.apply_audio()

    @option_def("sound_volume", "SOUND VOLUME", VOLUME_STEPS, order=2, description="Controls gameplay sound effects.")
    def sound_volume(self, value):
        settings.apply_audio()
