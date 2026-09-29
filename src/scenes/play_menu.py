import sys
import pygame
import config
from src import assets
from src import starfield
from src import states
from src.controls import ControllerInput
from .base import BaseScene

from src import logger

_DIFFICULTY_OPTIONS = [
    {"name": "EASY",    "texture": "difficulty0", "multiplier": 0.75, "color": (70, 160, 255)},
    {"name": "NORMAL",  "texture": "difficulty1", "multiplier": 1.0,  "color": (60, 220, 200)},
    {"name": "MEDIUM",  "texture": "difficulty2", "multiplier": 1.25, "color": (60, 210, 90)},
    {"name": "HARD",    "texture": "difficulty3", "multiplier": 1.5,  "color": (245, 210, 45)},
    {"name": "INSANE",  "texture": "difficulty4", "multiplier": 1.75, "color": (255, 140, 35)},
    {"name": "GALACTIC","texture": "difficulty5", "multiplier": 2.0,  "color": (255, 65,  65)},
]

# Menu entries – "DIFFICULTY" is a special handled entry
_MENU_LABELS = ["START GAME", "DIFFICULTY", "BACK"]

_state = {
    "loaded": False,
    "stars_bg": None,
    "selected_index": 0,
    "option_rects": [],
    "hover_item": None,
    "timer": 0,
    # Difficulty submenu state
    "submenu_open": False,
    "sub_selected_index": 1,  # Default: NORMAL
    "sub_option_rects": [],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_current_difficulty_info():
    """Returns the difficulty info dict that matches states.difficulty."""
    for opt in _DIFFICULTY_OPTIONS:
        if opt["multiplier"] == states.difficulty:
            return opt
    return _DIFFICULTY_OPTIONS[1]  # Fallback to Normal


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def load(*args, **kwargs):
    """Initialise play-menu state."""
    _state["loaded"] = True
    _state["stars_bg"] = starfield.Generate(config.Screen.Size.w, config.Screen.Size.h)
    _state["option_rects"] = []
    _state["sub_option_rects"] = []
    _state["selected_index"] = 0
    _state["submenu_open"] = False
    _state["timer"] = 0

    # Sync submenu selector to current states.difficulty
    for idx, opt in enumerate(_DIFFICULTY_OPTIONS):
        if opt["multiplier"] == states.difficulty:
            _state["sub_selected_index"] = idx
            break


def unload():
    """Clean up play-menu state."""
    _state["loaded"] = False
    _state["stars_bg"] = None
    _state["option_rects"].clear()
    _state["sub_option_rects"].clear()
    _state["submenu_open"] = False


# ---------------------------------------------------------------------------
# Event Handling
# ---------------------------------------------------------------------------

def handle_event(event: pygame.event.Event, manager=None):
    """Handle keyboard and mouse events for the play menu."""
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit(0)

    # ---- Submenu open: route events there ----
    if _state["submenu_open"]:
        _handle_submenu_event(event, manager)
        return

    # ---- Main play-menu events ----
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_UP, pygame.K_w):
            _state["selected_index"] = (_state["selected_index"] - 1) % len(_MENU_LABELS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            _state["selected_index"] = (_state["selected_index"] + 1) % len(_MENU_LABELS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            _activate_option(_state["selected_index"], manager)
        elif event.key == pygame.K_ESCAPE:
            _return_to_title(manager)

    # Controller navigation (main menu)
    elif ControllerInput.nav_up(event):
        _state["selected_index"] = (_state["selected_index"] - 1) % len(_MENU_LABELS)
    elif ControllerInput.nav_down(event):
        _state["selected_index"] = (_state["selected_index"] + 1) % len(_MENU_LABELS)
    elif ControllerInput.confirm(event):
        _activate_option(_state["selected_index"], manager)
    elif ControllerInput.cancel(event):
        _return_to_title(manager)

    elif event.type == pygame.MOUSEMOTION:
        mouse_pos = event.pos
        _state["hover_item"] = None
        for idx, rect in enumerate(_state["option_rects"]):
            if rect and rect.collidepoint(mouse_pos):
                _state["selected_index"] = idx
                _state["hover_item"] = f"opt_{idx}"

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mouse_pos = event.pos
        for idx, rect in enumerate(_state["option_rects"]):
            if rect and rect.collidepoint(mouse_pos):
                _activate_option(idx, manager)


def _handle_submenu_event(event: pygame.event.Event, manager=None):
    """Handle events when the difficulty submenu overlay is open."""
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_UP, pygame.K_w):
            _state["sub_selected_index"] = (_state["sub_selected_index"] - 1) % len(_DIFFICULTY_OPTIONS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            _state["sub_selected_index"] = (_state["sub_selected_index"] + 1) % len(_DIFFICULTY_OPTIONS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            _apply_difficulty_and_close()
        elif event.key == pygame.K_ESCAPE:
            _state["submenu_open"] = False  # Cancel without applying

    # Controller navigation (difficulty submenu)
    elif ControllerInput.nav_up(event):
        _state["sub_selected_index"] = (_state["sub_selected_index"] - 1) % len(_DIFFICULTY_OPTIONS)
    elif ControllerInput.nav_down(event):
        _state["sub_selected_index"] = (_state["sub_selected_index"] + 1) % len(_DIFFICULTY_OPTIONS)
    elif ControllerInput.confirm(event):
        _apply_difficulty_and_close()
    elif ControllerInput.cancel(event):
        _state["submenu_open"] = False  # Cancel without applying

    elif event.type == pygame.MOUSEMOTION:
        mouse_pos = event.pos
        for idx, rect in enumerate(_state["sub_option_rects"]):
            if rect and rect.collidepoint(mouse_pos):
                _state["sub_selected_index"] = idx

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mouse_pos = event.pos
        for idx, rect in enumerate(_state["sub_option_rects"]):
            if rect and rect.collidepoint(mouse_pos):
                _state["sub_selected_index"] = idx
                _apply_difficulty_and_close()
        # Click outside the panel to close without applying
        panel_rect = _state.get("submenu_panel_rect")
        if panel_rect and not panel_rect.collidepoint(mouse_pos):
            _state["submenu_open"] = False


def _apply_difficulty_and_close():
    """Apply the highlighted difficulty to config and close the submenu."""
    opt = _DIFFICULTY_OPTIONS[_state["sub_selected_index"]]
    states.difficulty = opt["multiplier"]
    logger.engine_log.info(f"Difficulty set to {opt['name']} ({states.difficulty}x)")
    _state["submenu_open"] = False


def _activate_option(index: int, manager=None):
    """Execute the selected play-menu option."""
    if index == 0:  # START GAME
        _start_gameplay(manager)
    elif index == 1:  # This is the difficulty button.
        # you can
        for idx, opt in enumerate(_DIFFICULTY_OPTIONS):
            if opt["multiplier"] == states.difficulty:
                _state["sub_selected_index"] = idx
                break
        _state["submenu_open"] = True
    elif index == 2:  # BACK
        _return_to_title(manager)


def _start_gameplay(manager=None):
    """Launch the gameplay scene."""
    diff_info = _get_current_difficulty_info()
    logger.engine_log.info(f"Starting run - {diff_info['name']} ({states.difficulty}x)")
    if manager:
        from .gameplay import GameplayScene
        manager.set_scene(GameplayScene(), fade=True)


def _return_to_title(manager=None):
    """Return to the title screen."""
    if manager:
        from .title import TitleScene
        manager.set_scene(TitleScene(), fade=True)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def update(dt: float = 1.0):
    """Advance background starfield and timer."""
    if _state["stars_bg"]:
        _state["stars_bg"].update()
    _state["timer"] += 1


# ---------------------------------------------------------------------------
# Draw
# ---------------------------------------------------------------------------

def draw(screen: pygame.Surface):
    """Render the play menu (and difficulty submenu overlay if open)."""
    screen.fill((0, 0, 0))

    if _state["stars_bg"]:
        _state["stars_bg"].draw(screen)

    center_x = config.Screen.Size.w // 2
    font = getattr(assets, "pressStart2P", None)

    # 1. Header
    if font:
        header_surf = font.render("GAME CONFIGURATION", True, (255, 255, 255))
        shadow_surf  = font.render("GAME CONFIGURATION", True, (40, 40, 60))
        header_rect = header_surf.get_rect(center=(center_x, 160))
        screen.blit(shadow_surf, header_rect.move(0, 3))
        screen.blit(header_surf, header_rect)

        sub_surf = font.render("Set up your run and press Start", True, (135, 242, 255))
        screen.blit(sub_surf, sub_surf.get_rect(center=(center_x, 210)))

    # 2. Menu buttons
    _state["option_rects"] = []
    diff_info = _get_current_difficulty_info()

    btn_width = 560
    btn_height = 72
    start_y = 310
    spacing = 100

    for idx, label in enumerate(_MENU_LABELS):
        is_selected = (idx == _state["selected_index"])

        btn_rect = pygame.Rect(center_x - btn_width // 2, start_y + idx * spacing, btn_width, btn_height)
        _state["option_rects"].append(btn_rect)

        # Background & border
        if is_selected:
            bg_color     = (30, 45, 65)
            border_color = (135, 242, 255)
            border_w     = 2
            text_color   = (135, 242, 255)
        else:
            bg_color     = (18, 22, 32)
            border_color = (55, 65, 80)
            border_w     = 1
            text_color   = (200, 200, 200)

        pygame.draw.rect(screen, bg_color, btn_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, btn_rect, width=border_w, border_radius=10)

        # Selector arrow
        if is_selected:
            if font:
                arrow_surf = font.render(">", True, (135, 242, 255))
                screen.blit(arrow_surf, (btn_rect.x + 14, btn_rect.centery - arrow_surf.get_height() // 2))

        # ---- Special rendering for DIFFICULTY button ----
        if idx == 1:
            # Draw current difficulty icon on the left side of the button
            tex_surf = getattr(assets.Textures, diff_info["texture"], None)
            icon_x = btn_rect.x + 50

            if tex_surf is not None:
                # Scale icon to fit button height nicely
                icon_h = btn_height - 16
                scale_f = icon_h / tex_surf.get_height()
                icon_w = int(tex_surf.get_width() * scale_f)
                icon_surf = pygame.transform.scale(tex_surf, (icon_w, icon_h))
                icon_rect = icon_surf.get_rect(midleft=(icon_x, btn_rect.centery))
                screen.blit(icon_surf, icon_rect)
                text_start_x = icon_rect.right + 14
            else:
                text_start_x = icon_x + 10

            # Difficulty label + current name
            if font:
                label_surf = font.render("DIFFICULTY", True, text_color)
                screen.blit(label_surf, label_surf.get_rect(midleft=(text_start_x, btn_rect.centery - 10)))

                diff_name_surf = font.render(diff_info["name"], True, diff_info["color"])
                screen.blit(diff_name_surf, diff_name_surf.get_rect(midleft=(text_start_x, btn_rect.centery + 18)))
        else:
            # Standard centered label
            if font:
                text_surf = font.render(label, True, text_color)
                screen.blit(text_surf, text_surf.get_rect(center=btn_rect.center))

    # 3. Footer hint
    if font:
        hint = "ESC to go Back"
        hint_surf = font.render(hint, True, (80, 90, 110))
        screen.blit(hint_surf, hint_surf.get_rect(center=(center_x, config.Screen.Size.h - 50)))

    # 4. Difficulty submenu overlay (drawn on top if open)
    if _state["submenu_open"]:
        _draw_difficulty_submenu(screen, font, center_x)


def _draw_difficulty_submenu(screen: pygame.Surface, font, center_x: int):
    """Draw the difficulty picker overlay panel."""
    # Dim the background
    overlay = pygame.Surface((config.Screen.Size.w, config.Screen.Size.h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    panel_w   = 700
    card_h    = 66
    spacing   = 76
    panel_h   = 60 + len(_DIFFICULTY_OPTIONS) * spacing + 20
    panel_x   = center_x - panel_w // 2
    panel_y   = config.Screen.Size.h // 2 - panel_h // 2

    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    _state["submenu_panel_rect"] = panel_rect

    # Panel background
    pygame.draw.rect(screen, (14, 18, 28), panel_rect, border_radius=12)
    pygame.draw.rect(screen, (135, 242, 255), panel_rect, width=2, border_radius=12)

    # Panel title
    if font:
        title_surf = font.render("SELECT DIFFICULTY", True, (255, 255, 255))
        screen.blit(title_surf, title_surf.get_rect(center=(center_x, panel_y + 30)))

    # Difficulty cards
    _state["sub_option_rects"] = []
    cards_start_y = panel_y + 60

    for idx, opt in enumerate(_DIFFICULTY_OPTIONS):
        is_selected = (idx == _state["sub_selected_index"])
        is_active   = (opt["multiplier"] == states.difficulty)

        card_rect = pygame.Rect(panel_x + 20, cards_start_y + idx * spacing, panel_w - 40, card_h)
        _state["sub_option_rects"].append(card_rect)

        bg_color     = (30, 45, 65)     if is_selected else (18, 22, 32)
        border_color = opt["color"]      if (is_selected or is_active) else (55, 65, 80)
        border_w     = 3                 if is_selected else (2 if is_active else 1)

        pygame.draw.rect(screen, bg_color, card_rect, border_radius=8)
        pygame.draw.rect(screen, border_color, card_rect, width=border_w, border_radius=8)

        # Color strip on left
        strip = pygame.Rect(card_rect.x, card_rect.y, 8, card_h)
        pygame.draw.rect(screen, opt["color"], strip, border_top_left_radius=8, border_bottom_left_radius=8)

        # Icon
        tex_surf = getattr(assets.Textures, opt["texture"], None)
        text_x = card_rect.x + 24

        if tex_surf is not None:
            icon_h = card_h - 12
            scale_f = icon_h / tex_surf.get_height()
            icon_w = int(tex_surf.get_width() * scale_f)
            icon_surf = pygame.transform.scale(tex_surf, (icon_w, icon_h))
            icon_rect = icon_surf.get_rect(midleft=(card_rect.x + 20, card_rect.centery))
            screen.blit(icon_surf, icon_rect)
            text_x = icon_rect.right + 16

        if font:
            name_color = opt["color"] if is_selected else (230, 230, 230)
            name_surf  = font.render(opt["name"], True, name_color)
            screen.blit(name_surf, name_surf.get_rect(midleft=(text_x, card_rect.centery)))

            # "ACTIVE" badge for currently configured difficulty
            if is_active:
                badge_surf = font.render("[CURRENT]", True, (135, 242, 255))
                screen.blit(badge_surf, badge_surf.get_rect(midright=(card_rect.right - 16, card_rect.centery)))

    # Dismiss hint
    if font:
        hint_surf = font.render("ENTER to Confirm  |  ESC to Cancel", True, (100, 110, 130))
        screen.blit(hint_surf, hint_surf.get_rect(center=(center_x, panel_rect.bottom + 20)))


# ---------------------------------------------------------------------------
# Scene Class Wrapper
# ---------------------------------------------------------------------------

class PlayMenuScene(BaseScene):
    """Class wrapper for the Play Menu scene."""

    def load(self, *args, **kwargs):
        load(*args, **kwargs)

    def unload(self):
        unload()

    def handle_event(self, event: pygame.event.Event):
        handle_event(event, self.manager)

    def update(self, dt: float = 1.0):
        update(dt)

    def draw(self, screen: pygame.Surface):
        draw(screen)
