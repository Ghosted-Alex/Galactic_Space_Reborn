"""Resource pack selection scene."""

import sys
import pygame
import config
from src import assets, starfield, pack
from src.controls import ControllerInput
from .base import BaseScene

_state = {"loaded": False, "stars_bg": None, "packs": [], "selected_index": 0,
          "row_rects": [], "apply_rect": None, "back_rect": None, "hover_item": None}


def load(*args, **kwargs):
    _state["loaded"] = True
    _state["stars_bg"] = starfield.Generate(config.Screen.Size.w, config.Screen.Size.h)
    _state["packs"] = [{"id": None, "name": "Default Resource Pack", "description": "Use the game's built-in graphics and audio.", "author": "Galactic Space Reborn"}, *pack.discover_packs()]
    active_name = pack.get_active_pack_name()
    _state["selected_index"] = next((i for i, item in enumerate(_state["packs"]) if item["id"] == active_name), 0)
    _state["row_rects"] = []
    _state["hover_item"] = None


def unload():
    _state["loaded"] = False
    _state["stars_bg"] = None
    _state["row_rects"] = []


def _return_to_title(manager):
    if manager:
        from .title import TitleScene
        manager.set_scene(TitleScene(), fade=True)


def _apply_selected(manager):
    selected = _state["packs"][_state["selected_index"]]
    if selected["id"] != pack.get_active_pack_name() and pack.set_active_pack(selected["id"]):
        manager.request_window_reload()


def handle_event(event, manager=None):
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit(0)
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            _return_to_title(manager)
        elif event.key in (pygame.K_UP, pygame.K_w):
            _state["selected_index"] = (_state["selected_index"] - 1) % len(_state["packs"])
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            _state["selected_index"] = (_state["selected_index"] + 1) % len(_state["packs"])
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            _apply_selected(manager)
    # Controller navigation
    elif ControllerInput.nav_up(event):
        _state["selected_index"] = (_state["selected_index"] - 1) % len(_state["packs"])
    elif ControllerInput.nav_down(event):
        _state["selected_index"] = (_state["selected_index"] + 1) % len(_state["packs"])
    elif ControllerInput.confirm(event):
        _apply_selected(manager)
    elif ControllerInput.cancel(event):
        _return_to_title(manager)
    elif event.type == pygame.MOUSEMOTION:
        _state["hover_item"] = None
        for index, row in enumerate(_state["row_rects"]):
            if row.collidepoint(event.pos):
                _state["selected_index"] = index
                _state["hover_item"] = "pack"
                break
        if _state["apply_rect"] and _state["apply_rect"].collidepoint(event.pos):
            _state["hover_item"] = "apply"
        elif _state["back_rect"] and _state["back_rect"].collidepoint(event.pos):
            _state["hover_item"] = "back"
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for index, row in enumerate(_state["row_rects"]):
            if row.collidepoint(event.pos):
                _state["selected_index"] = index
                return
        if _state["apply_rect"] and _state["apply_rect"].collidepoint(event.pos):
            _apply_selected(manager)
        elif _state["back_rect"] and _state["back_rect"].collidepoint(event.pos):
            _return_to_title(manager)


def update(dt=1.0):
    if _state["stars_bg"]:
        _state["stars_bg"].update()


def _button(screen, rect, label, hovered, press_start_font):
    pygame.draw.rect(screen, (45, 30, 35) if hovered else (30, 25, 35), rect, border_radius=6)
    pygame.draw.rect(screen, (255, 135, 135) if hovered else (135, 242, 255), rect, width=1, border_radius=6)
    if press_start_font:
        rendered = press_start_font.render(label, True, (255, 255, 255))
        screen.blit(rendered, rendered.get_rect(center=rect.center))


def _wrap_description(text, font, max_width, max_lines=2):
    """Wrap text to a fixed pixel width, marking text that does not fit."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        candidate = f"{current_line} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current_line = candidate
            continue
        if current_line:
            lines.append(current_line)
        current_line = word
        if len(lines) == max_lines:
            break

    if len(lines) < max_lines and current_line:
        lines.append(current_line)

    has_more = len(lines) < len(words) and " ".join(lines) != " ".join(words)
    if has_more:
        final_line = lines[-1]
        while final_line and font.size(final_line + "...")[0] > max_width:
            final_line = final_line[:-1]
        lines[-1] = final_line.rstrip() + "..."
    return lines


def _draw_small_text(screen, text, font, position, color):
    """Render the menu's secondary text at half the title font's size."""
    rendered = font.render(text, True, color)
    small_size = (max(1, rendered.get_width() // 2), max(1, rendered.get_height() // 2))
    screen.blit(pygame.transform.smoothscale(rendered, small_size), position)


def draw(screen):
    screen.fill((0, 0, 0))
    if _state["stars_bg"]:
        _state["stars_bg"].draw(screen)
    monocraft_font = getattr(assets, "monocraft", None)
    press_start_font = getattr(assets, "pressStart2P", None)
    center_x = config.Screen.Size.w // 2
    if press_start_font:
        title = press_start_font.render("RESOURCE PACKS", True, (255, 255, 255))
        subtitle = press_start_font.render("SELECT A PACK, THEN APPLY", True, (135, 242, 255))
        screen.blit(title, title.get_rect(center=(center_x, 80)))
        screen.blit(subtitle, subtitle.get_rect(center=(center_x, 125)))
    panel = pygame.Rect(center_x - 410, 165, 820, 530)
    pygame.draw.rect(screen, (18, 24, 36), panel, border_radius=10)
    pygame.draw.rect(screen, (60, 80, 110), panel, width=2, border_radius=10)
    _state["row_rects"] = []
    for index, item in enumerate(_state["packs"]):
        row = pygame.Rect(panel.x + 20, panel.y + 25 + index * 105, panel.width - 40, 90)
        if row.bottom > panel.bottom - 12:
            break
        _state["row_rects"].append(row)
        selected = index == _state["selected_index"]
        if selected:
            pygame.draw.rect(screen, (30, 45, 65), row, border_radius=6)
            pygame.draw.rect(screen, (135, 242, 255), row, width=2, border_radius=6)
        if monocraft_font:
            color = (219, 212, 53) if item["id"] == pack.get_active_pack_name() else (255, 255, 255)
            displayed_name = item["name"][:47]
            name = monocraft_font.render(("> " if selected else "  ") + displayed_name, True, color)
            small_name_size = (max(1, int(name.get_width() * 0.75)), max(1, int(name.get_height() * 0.75)))
            screen.blit(pygame.transform.smoothscale(name, small_name_size), (row.x + 18, row.y + 12))
            description_width = (row.width - 36) * 2
            for line_index, line in enumerate(_wrap_description(item["description"], monocraft_font, description_width)):
                _draw_small_text(screen, line, monocraft_font, (row.x + 18, row.y + 48 + line_index * 18), (135, 242, 255))
    _state["apply_rect"] = pygame.Rect(center_x - 260, config.Screen.Size.h - 105, 240, 44)
    _state["back_rect"] = pygame.Rect(center_x + 20, config.Screen.Size.h - 105, 240, 44)
    _button(screen, _state["apply_rect"], "APPLY", _state["hover_item"] == "apply", press_start_font)
    _button(screen, _state["back_rect"], "BACK", _state["hover_item"] == "back", press_start_font)


class ResourcePackMenuScene(BaseScene):
    def load(self, *args, **kwargs): load(*args, **kwargs)
    def unload(self): unload()
    def handle_event(self, event): handle_event(event, self.manager)
    def update(self, dt=1.0): update(dt)
    def draw(self, screen): draw(screen)
