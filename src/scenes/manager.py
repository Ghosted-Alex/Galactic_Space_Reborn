"""Scene Manager module supporting smooth screen fade transitions and dedicated scene lifecycle management."""

import pygame


class SceneManager:
    """Manages active scene, screen switching, and smooth fade transitions."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.current_scene = None
        self.next_scene = None
        self.next_scene_args = ()
        self.next_scene_kwargs = {}
        
        # Fade transition state
        self.fading = False
        self.fade_alpha = 0
        self.fade_mode = None  # 'out' (fading to black) or 'in' (fading from black)
        self.fade_speed = 12
        self.fade_surface = pygame.Surface(screen.get_size()).convert()
        self.fade_surface.fill((0, 0, 0))
        self.window_reload_requested = False
        self.overlay_scene = None
        self.scene_stack = []

    def request_window_reload(self):
        """Ask the game loop to recreate the display and reload its assets."""
        self.window_reload_requested = True

    def consume_window_reload_request(self) -> bool:
        """Returns and clears a pending display reload request."""
        requested = self.window_reload_requested
        self.window_reload_requested = False
        return requested

    def replace_screen(self, screen: pygame.Surface):
        """Attach the manager to a newly created pygame display surface."""
        self.screen = screen
        self.fade_surface = pygame.Surface(screen.get_size()).convert()
        self.fade_surface.fill((0, 0, 0))

    def show_overlay(self, scene):
        """Show an input-blocking overlay without unloading the current scene."""
        if self.overlay_scene is None:
            self.overlay_scene = scene
            scene.manager = self
            scene.load()

    def close_overlay(self):
        """Close the active overlay and resume the current scene."""
        if self.overlay_scene:
            self.overlay_scene.unload()
            self.overlay_scene = None

    def push_scene(self, scene):
        """Temporarily replace the scene while preserving it for a later return."""
        if self.current_scene:
            self.scene_stack.append(self.current_scene)
        self.current_scene = scene
        scene.manager = self
        scene.load()

    def has_previous_scene(self) -> bool:
        return bool(self.scene_stack)

    def pop_scene(self):
        """Discard the temporary scene and restore the preserved one."""
        if not self.scene_stack:
            return
        if self.current_scene:
            self.current_scene.unload()
        self.current_scene = self.scene_stack.pop()

    def set_scene(self, scene, fade: bool = True, fade_speed: int = 12, *args, **kwargs):
        """Switches to a new scene, optionally with a smooth fade transition."""
        if not fade or self.current_scene is None:
            # Immediate scene switch without fade
            if self.current_scene:
                self.current_scene.unload()
            self.current_scene = scene
            self.current_scene.manager = self
            self.current_scene.load(*args, **kwargs)
        else:
            # Initiate fade transition
            self.next_scene = scene
            self.next_scene_args = args
            self.next_scene_kwargs = kwargs
            self.fade_speed = fade_speed
            self.fade_mode = 'out'
            self.fading = True
            self.fade_alpha = 0

    def handle_event(self, event: pygame.event.Event):
        """Pass events to the current scene (unless fading out)."""
        if self.fading and self.fade_mode == 'out':
            return  # Block input during fade out transition
        if self.overlay_scene:
            self.overlay_scene.handle_event(event)
        elif self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt: float = 1.0):
        """Update active scene and fade animation state."""
        if self.fading:
            if self.fade_mode == 'out':
                self.fade_alpha += self.fade_speed
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
                    # Unload current scene and load next scene at peak dark alpha
                    if self.current_scene:
                        self.current_scene.unload()
                    self.current_scene = self.next_scene
                    self.current_scene.manager = self
                    self.current_scene.load(*self.next_scene_args, **self.next_scene_kwargs)
                    self.next_scene = None
                    self.fade_mode = 'in'
            elif self.fade_mode == 'in':
                self.fade_alpha -= self.fade_speed
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fading = False
                    self.fade_mode = None

        if self.current_scene and not self.overlay_scene:
            self.current_scene.update(dt)
        if self.overlay_scene:
            self.overlay_scene.update(dt)

    def draw(self, screen: pygame.Surface = None):
        """Draw current scene and overlay fade effect if transitioning."""
        target_screen = screen or self.screen
        if self.current_scene:
            self.current_scene.draw(target_screen)

        if self.overlay_scene:
            self.overlay_scene.draw(target_screen)

        if self.fading and self.fade_alpha > 0:
            self.fade_surface.set_alpha(int(self.fade_alpha))
            target_screen.blit(self.fade_surface, (0, 0))


def fade_screen(screen: pygame.Surface, mode: str = "out", speed: int = 15, clock=None, draw_fn=None):
    """Standalone helper function to fade screen in or out synchronously."""
    fade_surface = pygame.Surface(screen.get_size()).convert()
    fade_surface.fill((0, 0, 0))
    clock = clock or pygame.time.Clock()

    if mode == "out":
        alpha_range = range(0, 256, speed)
    else:
        alpha_range = range(255, -1, -speed)

    for alpha in alpha_range:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit(0)

        if draw_fn:
            draw_fn(screen)

        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)
