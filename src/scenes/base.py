"""Base Scene module for Galactic Space Reborn scene architecture."""

import pygame


class BaseScene:
    """Abstract base class for all game screens / scenes."""

    def __init__(self):
        self.manager = None

    def load(self, *args, **kwargs):
        """Called when the scene is loaded/entered. Override in subclasses."""
        pass

    def unload(self):
        """Called when transitioning out of the scene. Override in subclasses."""
        pass

    def handle_event(self, event: pygame.event.Event):
        """Process input events. Override in subclasses."""
        pass

    def update(self, dt: float = 1.0):
        """Update scene logic. Override in subclasses."""
        pass

    def draw(self, screen: pygame.Surface):
        """Render scene visuals to the screen. Override in subclasses."""
        pass
