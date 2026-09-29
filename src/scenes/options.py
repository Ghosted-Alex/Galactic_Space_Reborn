"""Top-level settings category menu."""

import sys

import pygame

import config
from src import assets, starfield
from src.controls import ControllerInput
from .base import BaseScene


_state = {
    "loaded": False,
    "stars_bg": None,
    "selected_index": 0,
    "options": ("VIDEO", "MUSIC & SOUNDS", "BACK"),
    "option_rects": [],
}


def load(*args, **kwargs):
    """Prepare the category selection screen."""
    _state["loaded"] = True
    _state["selected_index"] = 0
    _state["option_rects"] = []
    _state["stars_bg"] = starfield.Generate(config.Screen.Size.w, config.Screen.Size.h)


def unload():
    _state["loaded"] = False
    _state["stars_bg"] = None
    _state["option_rects"] = []


def _return_to_title(manager):
    if manager:
        if manager.has_previous_scene():
            manager.pop_scene()
        else:
            from .title import TitleScene
            manager.set_scene(TitleScene(), fade=True)


def _activate_option(index, manager):
    selected = _state["options"][index]
    if selected == "VIDEO" and manager:
        from .video_options import VideoOptionsScene
        manager.set_scene(VideoOptionsScene(), fade=True)
    elif selected == "MUSIC & SOUNDS" and manager:
        from .audio_options import AudioOptionsScene
        manager.set_scene(AudioOptionsScene(), fade=True)
    elif selected == "BACK":
        _return_to_title(manager)


def handle_event(event, manager=None):
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit(0)
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            _return_to_title(manager)
        elif event.key in (pygame.K_UP, pygame.K_w):
            _state["selected_index"] = (_state["selected_index"] - 1) % len(_state["options"])
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            _state["selected_index"] = (_state["selected_index"] + 1) % len(_state["options"])
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            _activate_option(_state["selected_index"], manager)
    # Controller navigation
    elif ControllerInput.nav_up(event):
        _state["selected_index"] = (_state["selected_index"] - 1) % len(_state["options"])
    elif ControllerInput.nav_down(event):
        _state["selected_index"] = (_state["selected_index"] + 1) % len(_state["options"])
    elif ControllerInput.confirm(event):
        _activate_option(_state["selected_index"], manager)
    elif ControllerInput.cancel(event):
        _return_to_title(manager)
    elif event.type == pygame.MOUSEMOTION:
        for index, option_rect in enumerate(_state["option_rects"]):
            if option_rect.collidepoint(event.pos):
                _state["selected_index"] = index
                break
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for index, option_rect in enumerate(_state["option_rects"]):
            if option_rect.collidepoint(event.pos):
                _state["selected_index"] = index
                _activate_option(index, manager)
                break


def update(dt=1.0):
    if _state["stars_bg"]:
        _state["stars_bg"].update()


def draw(screen):
    screen.fill((0, 0, 0))
    if _state["stars_bg"]:
        _state["stars_bg"].draw(screen)

    center_x = config.Screen.Size.w // 2
    title_font = getattr(assets, "pressStart2P", None)
    body_font = getattr(assets, "monocraft", title_font)
    if title_font:
        title = title_font.render("OPTIONS", True, (255, 255, 255))
        subtitle = title_font.render("GAME SETTINGS", True, (135, 242, 255))
        screen.blit(title, title.get_rect(center=(center_x, 110)))
        screen.blit(subtitle, subtitle.get_rect(center=(center_x, 155)))

    panel = pygame.Rect(center_x - 360, 205, 720, 410)
    pygame.draw.rect(screen, (18, 24, 36), panel, border_radius=10)
    pygame.draw.rect(screen, (60, 80, 110), panel, width=2, border_radius=10)

    _state["option_rects"] = []
    for index, label in enumerate(_state["options"]):
        button = pygame.Rect(panel.x + 45, panel.y + 45 + index * 105, panel.width - 90, 70)
        _state["option_rects"].append(button)
        selected = index == _state["selected_index"]
        pygame.draw.rect(screen, (30, 45, 65) if selected else (22, 30, 45), button, border_radius=8)
        pygame.draw.rect(screen, (135, 242, 255) if selected else (60, 80, 110), button, width=2 if selected else 1, border_radius=8)
        if body_font:
            text = body_font.render(("> " if selected else "  ") + label, True, (255, 255, 255) if selected else (190, 200, 215))
            screen.blit(text, text.get_rect(center=button.center))

    if body_font:
        helper = body_font.render("UP/DOWN OR W/S TO SELECT    ENTER TO CONFIRM", True, (135, 150, 170))
        screen.blit(helper, helper.get_rect(center=(center_x, config.Screen.Size.h - 70)))


class OptionsScene(BaseScene):
    def load(self, *args, **kwargs):
        load(*args, **kwargs)

    def unload(self):
        unload()

    def handle_event(self, event):
        handle_event(event, self.manager)

    def update(self, dt=1.0):
        update(dt)

    def draw(self, screen):
        draw(screen)
