"""Video settings declared with reusable option definitions."""

from src.decorators import option_def
from .option_menu import OptionMenuScene


class VideoOptionsScene(OptionMenuScene):
    title = "VIDEO"
    requires_apply = True

    @option_def(
        "display_mode", "DISPLAY MODE", ("windowed", "fullscreen"), order=0,
        description="Choose windowed play or desktop fullscreen.",
    )
    def display_mode(self, value):
        self.manager.request_window_reload()
