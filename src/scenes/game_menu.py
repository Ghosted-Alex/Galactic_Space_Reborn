"""Title Screen / Scene for Galactic Space Reborn.

Provides dedicated load(), unload(), handle_event(), update(), and draw() functions
as well as a TitleScene class wrapper.
"""

import sys
import pygame
import config
from src import assets
from src import starfield
from src import stats
from src import events
from src.controls import ControllerInput
from .base import BaseScene
from src.decorators import button
from .play_menu import PlayMenuScene
from .dialog import show_message

def _return_to_title(manager=None):
    """Return to the title screen."""
    if manager:
        from .title import TitleScene
        manager.set_scene(TitleScene(), fade=True)

def _show_not_implemented(manager=None):
    show_message(manager=manager, title="Coming Soon!", message=["Sandbox is currently under construction\n",
    "Release of Sandbox is planned to be implemented in Release 1.0\n",
    "Release 1.0 is currently in development"])

class GameMenuScene(BaseScene):
    """Data-driven Title Screen scene utilizing decorators for menu mapping."""

    def load(self, *args, **kwargs):
        self.selected_index = 0
        self.timer = 0
        self.stars_bg = starfield.Generate(config.Screen.Size.w, config.Screen.Size.h)
        self.option_rects = []

        if config.check_high_score_exists():
            stats.high_score = events.load_high_score(config.HIGH_SCORE_FILE)

        # Discover all methods decorated with @button
        self.buttons = []
        for name in dir(self):
            attr = getattr(self, name)
            if callable(attr) and getattr(attr, "_is_menu_button", False):
                self.buttons.append({
                    "text": getattr(attr, "_button_text"),
                    "order": getattr(attr, "_button_order"),
                    "callback": attr
                })
        self.buttons.sort(key=lambda b: b["order"])

    def unload(self):
        self.stars_bg = None
        self.option_rects.clear()

    # --- Declarative Menu Buttons ---

    @button("MAIN GAME", order=0)
    def _on_main(self):
        if self.manager:
            self.manager.set_scene(PlayMenuScene(), fade=True)

    @button("SANDBOX (LOCKED)", order=1)
    def _on_sandbox(self):
        _show_not_implemented(self.manager)

    @button("TUTORIAL", order=2)
    def _on_tutorial(self):
        if self.manager:
            from .tutorial import TutorialScene
            self.manager.set_scene(TutorialScene(), fade=True)

    @button("BACK TO TITLE", order=3)
    def _on_back(self):
        _return_to_title(self.manager)

    # --- Scene Lifecycle ---

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)

            # ---- Main play-menu events ----
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.buttons[self.selected_index]["callback"]()
            elif event.key == pygame.K_ESCAPE:
                _return_to_title(self.manager)

        # Controller navigation (game menu)
        elif ControllerInput.nav_up(event):
            _state["selected_index"] = (_state["selected_index"] - 1) % len(_MENU_LABELS)
        elif ControllerInput.nav_down(event):
            _state["selected_index"] = (_state["selected_index"] + 1) % len(_MENU_LABELS)
        elif ControllerInput.confirm(event):
            _activate_option(_state["selected_index"], self.manager)
        elif ControllerInput.cancel(event):
            _return_to_title(self.manager)

        elif event.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(self.option_rects):
                if rect and rect.collidepoint(event.pos):
                    self.selected_index = idx

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in enumerate(self.option_rects):
                if rect and rect.collidepoint(event.pos):
                    self.buttons[idx]["callback"]()

    def update(self, dt: float = 1.0):
        if self.stars_bg:
            self.stars_bg.update()
        self.timer += 1

    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))

        if self.stars_bg:
            self.stars_bg.draw(screen)

        center_x = config.Screen.Size.w // 2

        font = getattr(assets, "pressStart2P", None)
        font_large = getattr(assets, 'pressStart2P', None)

        # 1. Header
        if font:
            header_surf = font.render("PLAY GAME", True, (255, 255, 255))
            shadow_surf  = font.render("PLAY GAME", True, (40, 40, 60))
            header_rect = header_surf.get_rect(center=(center_x, 160))
            screen.blit(shadow_surf, header_rect.move(0, 4))
            screen.blit(header_surf, header_rect)

            shadow_sub_surf = font.render("Choose a Game Mode", True, (0, 78, 88))
            sub_surf = font.render("Choose a Game Mode", True, (135, 242, 255))
            screen.blit(shadow_sub_surf, shadow_sub_surf.get_rect(center=(center_x, 214)))
            screen.blit(sub_surf, sub_surf.get_rect(center=(center_x, 210)))

        # Render Buttons via Metadata
        self.option_rects = []
        start_y = 360
        spacing = 65

        for idx, btn in enumerate(self.buttons):
            is_selected = (idx == self.selected_index)
            color = (255, 255, 255) if not is_selected else (135, 242, 255)

            if font_large:
                prefix = "> " if is_selected else "  "
                full_text = prefix + btn["text"] + (" <" if is_selected else "  ")
                text_surf = font_large.render(full_text, True, color)
                rect = text_surf.get_rect(center=(center_x, start_y + idx * spacing))

                self.option_rects.append(rect)

                if is_selected:
                    box_rect = rect.inflate(24, 16)
                    pygame.draw.rect(screen, (30, 45, 65), box_rect, border_radius=6)
                    pygame.draw.rect(screen, (135, 242, 255), box_rect, width=2, border_radius=6)

                screen.blit(text_surf, rect)

# --- Module-Level Bridge Functions (Keeps src/scenes/__init__.py happy) ---

# A global or singleton instance if your __init__.py expects to call load/unload directly
_active_title_scene = None

def load(*args, **kwargs):
    global _active_title_scene
    if _active_title_scene is None:
        _active_title_scene = TitleScene()
    _active_title_scene.load(*args, **kwargs)

def unload():
    global _active_title_scene
    if _active_title_scene:
        _active_title_scene.unload()

def handle_event(event: pygame.event.Event, manager=None):
    if _active_title_scene:
        _active_title_scene.manager = manager
        _active_title_scene.handle_event(event)

def update(dt: float = 1.0):
    if _active_title_scene:
        _active_title_scene.update(dt)

def draw(screen: pygame.Surface):
    if _active_title_scene:
        _active_title_scene.draw(screen)
