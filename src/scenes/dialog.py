"""Dialog module for Galactic Space Reborn.

Provides flexible, standalone, and overlay dialog scenes for notifications,
confirmations, interactive tutorials, patch note update screens, and custom popups.
"""

from __future__ import annotations

import pygame
import config
from src import logger
from src.controls import ControllerInput
from .base import BaseScene


_FONT_CACHE: dict[tuple[str, int], pygame.font.Font] = {}


def get_dialog_font(font_type: str = "body", size: int = 18) -> pygame.font.Font:
    """Retrieves or creates a cached Pygame font for dialog surfaces."""
    cache_key = (font_type, size)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    font_path = None
    try:
        from src import assets
        if font_type == "title":
            font_path = assets.resolve_asset_path("fonts/PressStart2P-Regular.ttf")
        else:
            font_path = assets.resolve_asset_path("fonts/Monocraft.ttf")
    except Exception:
        pass

    font = None
    if font_path and font_path.exists():
        try:
            font = pygame.font.Font(str(font_path), size)
        except Exception:
            font = None

    if font is None:
        try:
            # Fallback to system monospace font or Pygame default font
            font = pygame.font.SysFont("monospace", size)
        except Exception:
            try:
                font = pygame.font.Font(None, size)
            except Exception:
                font = None

    _FONT_CACHE[cache_key] = font
    return font


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Splits and wraps text into lines fitting within max_width pixels."""
    if not text:
        return []

    lines: list[str] = []
    # Preserve explicit linebreaks first
    paragraphs = text.split("\n")
    for para in paragraphs:
        if not para:
            lines.append("")
            continue

        words = para.split(" ")
        current_line: list[str] = []
        for word in words:
            test_line = " ".join(current_line + [word])
            line_w, _ = font.size(test_line)
            if line_w <= max_width or not current_line:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

    return lines


class DialogScene(BaseScene):
    """Reusable, styled modal dialog scene that can overlay any screen."""

    def __init__(
        self,
        title: str = "DIALOG SAMPLE",
        message: str | list[str] = "This is a sample dialog, this is only a test dialog to test the modal only, if you want all tests, please use python3 main.py -s gsr.scene:dialog_test for all tests.\n\nLorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. ",
        actions: list[tuple[str, callable] | dict] | None = None,
        on_cancel: callable | None = None,
        width: int | None = None,
        height: int | None = None,
        pos: tuple[int, int] | None = None,
        align: str = "left",
        button_layout: str = "auto",
        close_on_escape: bool = True,
        dim_background: bool = True,
        tag: str | None = None,
    ):
        super().__init__()
        self.title = title
        self.raw_message = message
        self.on_cancel = on_cancel
        self.custom_width = width
        self.custom_height = height
        self.custom_pos = pos
        self.align = align
        self.button_layout = button_layout
        self.close_on_escape = close_on_escape
        self.dim_background = dim_background
        self.tag = tag

        self.selected_index: int = 0
        self.actions: list[dict] = []
        self.button_rects: list[pygame.Rect] = []
        self.panel_rect: pygame.Rect = pygame.Rect(0, 0, 100, 100)
        self.wrapped_lines: list[str] = []

        self.set_actions(actions)
        self._recalculate_layout()

    def set_title(self, title: str):
        """Update the dialog header title dynamically."""
        self.title = title
        self._recalculate_layout()

    def set_message(self, message: str | list[str]):
        """Update the dialog body message dynamically."""
        self.raw_message = message
        self._recalculate_layout()

    def set_actions(self, actions: list[tuple[str, callable] | dict] | None):
        """Configure the available actions / buttons."""
        self.actions = []
        if not actions:
            # Default single dismissal button
            self.actions.append({"label": "OK", "callback": None, "close": True})
        else:
            for item in actions:
                if isinstance(item, dict):
                    self.actions.append({
                        "label": str(item.get("label", "OK")),
                        "callback": item.get("callback"),
                        "close": item.get("close", True),
                    })
                elif isinstance(item, (tuple, list)):
                    label = str(item[0])
                    callback = item[1] if len(item) > 1 else None
                    close = item[2] if len(item) > 2 else True
                    self.actions.append({"label": label, "callback": callback, "close": close})
                elif isinstance(item, str):
                    self.actions.append({"label": item, "callback": None, "close": True})

        if self.selected_index >= len(self.actions):
            self.selected_index = max(0, len(self.actions) - 1)
        self._recalculate_layout()

    def _get_screen_size(self) -> tuple[int, int]:
        screen_w = getattr(getattr(config, "Screen", None), "Size", None)
        if screen_w and hasattr(screen_w, "w") and hasattr(screen_w, "h"):
            return config.Screen.Size.w, config.Screen.Size.h
        surf = pygame.display.get_surface()
        if surf:
            return surf.get_size()
        return 1072, 861

    def _recalculate_layout(self):
        screen_w, screen_h = self._get_screen_size()

        # Determine panel width
        panel_w = self.custom_width or min(680, screen_w - 80)
        panel_w = max(380, panel_w)

        # Prepare fonts
        body_font = get_dialog_font("body", 18)
        content_max_w = panel_w - 60

        # Wrap text
        if isinstance(self.raw_message, list):
            self.wrapped_lines = []
            for item in self.raw_message:
                self.wrapped_lines.extend(wrap_text(str(item), body_font, content_max_w))
        else:
            self.wrapped_lines = wrap_text(str(self.raw_message), body_font, content_max_w)

        # Calculate height
        title_h = 50 if self.title else 20
        line_height = body_font.get_linesize() if body_font else 22
        message_h = max(30, len(self.wrapped_lines) * line_height)

        # Sizing buttons
        num_buttons = len(self.actions)
        is_horizontal = (self.button_layout == "horizontal") or (
            self.button_layout == "auto" and num_buttons <= 3
        )

        button_area_h = 60 if is_horizontal else (num_buttons * 50 + 10)
        hint_h = 24 if self.close_on_escape else 10
        padding = 40

        calculated_h = title_h + message_h + button_area_h + hint_h + padding
        panel_h = self.custom_height or min(calculated_h, screen_h - 60)
        panel_h = max(200, panel_h)

        # Position panel
        if self.custom_pos:
            panel_x, panel_y = self.custom_pos
        else:
            panel_x = (screen_w - panel_w) // 2
            panel_y = (screen_h - panel_h) // 2

        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        # Layout button rectangles
        self.button_rects = []
        if is_horizontal:
            btn_h = 44
            spacing = 20
            available_w = panel_w - 60
            btn_w = max(110, (available_w - spacing * (num_buttons - 1)) // max(1, num_buttons))
            btn_w = min(180, btn_w)
            total_btns_w = num_buttons * btn_w + (num_buttons - 1) * spacing
            start_x = panel_x + (panel_w - total_btns_w) // 2
            btn_y = self.panel_rect.bottom - btn_h - (32 if self.close_on_escape else 20)

            for i in range(num_buttons):
                rect = pygame.Rect(start_x + i * (btn_w + spacing), btn_y, btn_w, btn_h)
                self.button_rects.append(rect)
        else:
            btn_h = 42
            spacing = 10
            btn_w = min(panel_w - 80, 280)
            btn_x = panel_x + (panel_w - btn_w) // 2
            start_y = self.panel_rect.bottom - (num_buttons * (btn_h + spacing)) - (25 if self.close_on_escape else 15)

            for i in range(num_buttons):
                rect = pygame.Rect(btn_x, start_y + i * (btn_h + spacing), btn_w, btn_h)
                self.button_rects.append(rect)

    def load(self, *args, **kwargs):
        """Called when dialog becomes active."""
        self.selected_index = 0
        self._recalculate_layout()

    def unload(self):
        """Called when dialog is dismissed."""
        self.button_rects = []

    def close(self):
        """Closes this dialog overlay and restores previous screen control."""
        if self.manager:
            if getattr(self.manager, "overlay_scene", None) is self:
                self.manager.close_overlay()
            elif hasattr(self.manager, "has_previous_scene") and self.manager.has_previous_scene():
                self.manager.pop_scene()
            elif getattr(self.manager, "current_scene", None) is self:
                # Fallback to title scene if run as root scene
                try:
                    from .title import TitleScene
                    self.manager.set_scene(TitleScene(), fade=True)
                except Exception:
                    pass

    def _trigger_action(self, index: int):
        if not (0 <= index < len(self.actions)):
            return

        action = self.actions[index]
        callback = action.get("callback")
        should_close = action.get("close", True)

        if callable(callback):
            try:
                result = callback()
            except TypeError:
                try:
                    result = callback(self)
                except Exception as err:
                    logger.engine_log.error(f"[Dialog] Callback execution error: {err}")
                    result = None

            # Returning False explicitly keeps the dialog open (useful for multi-step wizards)
            if result is False:
                should_close = False

        if should_close:
            self.close()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            pygame.quit()
            import sys
            sys.exit(0)

        num_actions = len(self.actions)

        # Keyboard Navigation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.close_on_escape:
                if callable(self.on_cancel):
                    try:
                        self.on_cancel()
                    except TypeError:
                        self.on_cancel(self)
                self.close()
                return

            if num_actions > 0:
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                    self.selected_index = (self.selected_index - 1) % num_actions
                elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                    self.selected_index = (self.selected_index + 1) % num_actions
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._trigger_action(self.selected_index)

        # Controller Navigation
        elif ControllerInput.nav_left(event) or ControllerInput.nav_up(event):
            if num_actions > 0:
                self.selected_index = (self.selected_index - 1) % num_actions
        elif ControllerInput.nav_right(event) or ControllerInput.nav_down(event):
            if num_actions > 0:
                self.selected_index = (self.selected_index + 1) % num_actions
        elif ControllerInput.confirm(event):
            if num_actions > 0:
                self._trigger_action(self.selected_index)
        elif ControllerInput.cancel(event) and self.close_on_escape:
            if callable(self.on_cancel):
                try:
                    self.on_cancel()
                except TypeError:
                    self.on_cancel(self)
            self.close()

        # Mouse Navigation
        elif event.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = idx
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = idx
                    self._trigger_action(idx)
                    break

    def update(self, dt: float = 1.0):
        """Update hook for animations or dynamic text."""
        pass

    def draw(self, screen: pygame.Surface):
        # 1. Dim background backdrop
        if self.dim_background:
            shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 180))
            screen.blit(shade, (0, 0))

        # 2. Main Dialog Panel
        pygame.draw.rect(screen, (18, 24, 36), self.panel_rect, border_radius=12)
        pygame.draw.rect(screen, (135, 242, 255), self.panel_rect, width=2, border_radius=12)

        # 3. Title Header
        title_font = get_dialog_font("title", 20)
        curr_y = self.panel_rect.y + 24
        if self.title and title_font:
            title_surf = title_font.render(self.title, True, (135, 242, 255))
            title_rect = title_surf.get_rect(center=(self.panel_rect.centerx, curr_y + 8))
            screen.blit(title_surf, title_rect)

            curr_y += 34
            # Separator accent line
            pygame.draw.line(
                screen,
                (45, 60, 85),
                (self.panel_rect.x + 24, curr_y),
                (self.panel_rect.right - 24, curr_y),
                1,
            )
            curr_y += 18
        else:
            curr_y += 10

        # 4. Message Content
        body_font = get_dialog_font("body", 18)
        if body_font and self.wrapped_lines:
            line_height = body_font.get_linesize()
            for line in self.wrapped_lines:
                if not line:
                    curr_y += line_height // 2
                    continue
                surf = body_font.render(line, True, (220, 230, 245))
                if self.align == "center":
                    rect = surf.get_rect(center=(self.panel_rect.centerx, curr_y + line_height // 2))
                else:
                    rect = surf.get_rect(topleft=(self.panel_rect.x + 30, curr_y))
                screen.blit(surf, rect)
                curr_y += line_height

        # 5. Action Buttons
        btn_font = get_dialog_font("title", 14)
        for idx, (action, rect) in enumerate(zip(self.actions, self.button_rects)):
            is_selected = (idx == self.selected_index)
            bg_color = (30, 45, 65) if is_selected else (22, 30, 45)
            border_color = (135, 242, 255) if is_selected else (60, 80, 110)
            text_color = (255, 255, 255) if is_selected else (190, 200, 215)

            pygame.draw.rect(screen, bg_color, rect, border_radius=8)
            pygame.draw.rect(screen, border_color, rect, width=2 if is_selected else 1, border_radius=8)

            if btn_font:
                label_text = ("> " if is_selected else "  ") + action["label"]
                text_surf = btn_font.render(label_text, True, text_color)
                screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        # 6. Escape / Controller hint
        if self.close_on_escape and body_font:
            hint_surf = body_font.render("ESC / (B) TO CANCEL", True, (110, 125, 145))
            hint_surf = pygame.transform.smoothscale(
                hint_surf,
                (max(1, hint_surf.get_width() // 2), max(1, hint_surf.get_height() // 2)),
            )
            screen.blit(hint_surf, hint_surf.get_rect(center=(self.panel_rect.centerx, self.panel_rect.bottom - 16)))


class ConfirmationDialog(DialogScene):
    """Preset confirmation modal with YES / NO actions."""

    def __init__(
        self,
        message: str = "Are you sure you want to proceed?",
        on_confirm: callable | None = None,
        on_cancel: callable | None = None,
        title: str = "CONFIRM",
        confirm_label: str = "YES",
        cancel_label: str = "NO",
        **kwargs,
    ):
        # Backward-compatibility for legacy signature: Confirmation(x, y, w, h, text, font)
        if isinstance(message, (int, float)):
            x, y, w, h = int(message), int(on_confirm), int(on_cancel), int(title)
            text_content = str(confirm_label)
            super().__init__(
                title="",
                message=text_content,
                actions=[("OK", None)],
                width=w,
                height=h,
                pos=(x, y),
                **kwargs,
            )
            return

        actions = [
            {"label": confirm_label, "callback": on_confirm, "close": True},
            {"label": cancel_label, "callback": on_cancel, "close": True},
        ]
        super().__init__(
            title=title,
            message=message,
            actions=actions,
            on_cancel=on_cancel,
            **kwargs,
        )


class MessageDialog(DialogScene):
    """Preset alert / information modal with a single dismissal button."""

    def __init__(
        self,
        message: str = "",
        title: str = "NOTICE",
        on_dismiss: callable | None = None,
        ok_label: str = "OK",
        **kwargs,
    ):
        actions = [{"label": ok_label, "callback": on_dismiss, "close": True}]
        super().__init__(
            title=title,
            message=message,
            actions=actions,
            on_cancel=on_dismiss,
            **kwargs,
        )


class MultiPageDialog(DialogScene):
    """Multi-page dialog supporting interactive tutorials and update notes."""

    def __init__(
        self,
        pages: list[dict],
        on_complete: callable | None = None,
        on_cancel: callable | None = None,
        finish_label: str = "FINISH",
        next_label: str = "NEXT",
        prev_label: str = "PREV",
        **kwargs,
    ):
        self.pages = pages or [{"title": "INFO", "message": ""}]
        self.current_page: int = 0
        self.on_complete = on_complete
        self.finish_label = finish_label
        self.next_label = next_label
        self.prev_label = prev_label
        self._extra_kwargs = kwargs

        super().__init__(title="", message="", actions=[], on_cancel=on_cancel, **kwargs)
        self._load_current_page()

    def _load_current_page(self, forward_focus: bool = True):
        page = self.pages[self.current_page]
        title = page.get("title", f"STEP {self.current_page + 1}/{len(self.pages)}")
        message = page.get("message", "")

        is_last = (self.current_page == len(self.pages) - 1)
        actions = []

        if self.current_page > 0:
            actions.append({"label": self.prev_label, "callback": self.prev_page, "close": False})

        if is_last:
            actions.append({"label": self.finish_label, "callback": self._on_finish, "close": True})
        else:
            actions.append({"label": self.next_label, "callback": self.next_page, "close": False})

        self.title = title
        self.raw_message = message
        self.set_actions(actions)

        # Focus forward action (NEXT / FINISH) when moving forward
        if forward_focus and len(self.actions) > 1:
            self.selected_index = len(self.actions) - 1
        elif not forward_focus:
            self.selected_index = 0

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._load_current_page(forward_focus=True)
        return False

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._load_current_page(forward_focus=False)
        return False

    def _on_finish(self):
        if callable(self.on_complete):
            try:
                self.on_complete()
            except TypeError:
                self.on_complete(self)


# Quick helper functions to trigger dialogs easily from any scene
def show_dialog(
    manager,
    title: str = "DIALOG",
    message: str | list[str] = "",
    actions: list | None = None,
    **kwargs,
) -> DialogScene:
    """Creates and immediately displays a DialogScene as an overlay on the SceneManager."""
    dialog = DialogScene(title=title, message=message, actions=actions, **kwargs)
    manager.show_overlay(dialog)
    return dialog


def show_message(
    manager,
    title: str = "NOTICE",
    message: str | list[str] = "",
    on_dismiss: callable | None = None,
    ok_label: str = "OK",
    **kwargs,
) -> MessageDialog:
    """Creates and displays a MessageDialog overlay."""
    dialog = MessageDialog(title=title, message=message, on_dismiss=on_dismiss, ok_label=ok_label, **kwargs)
    manager.show_overlay(dialog)
    return dialog


def show_confirmation(
    manager,
    message: str = "Are you sure?",
    on_confirm: callable | None = None,
    on_cancel: callable | None = None,
    title: str = "CONFIRM",
    confirm_label: str = "YES",
    cancel_label: str = "NO",
    **kwargs,
) -> ConfirmationDialog:
    """Creates and displays a ConfirmationDialog overlay."""
    dialog = ConfirmationDialog(
        message=message,
        on_confirm=on_confirm,
        on_cancel=on_cancel,
        title=title,
        confirm_label=confirm_label,
        cancel_label=cancel_label,
        **kwargs,
    )
    manager.show_overlay(dialog)
    return dialog


class BottomDialog(DialogScene):
    """Full-width bottom-docked dialog modal with configurable height (default: 1/3 screen).

    Anchored along the bottom of the screen, taking up the full screen width (with optional margin).
    Height is configurable via `height_ratio` (default 1/3 of the screen) or explicit pixel `height`.
    """

    def __init__(
        self,
        title: str = "",
        message: str | list[str] = "",
        actions: list[tuple[str, callable] | dict] | None = None,
        height: int | float | None = None,
        height_ratio: float = 1.0 / 3.0,
        margin: int = 0,
        button_align: str = "right",
        speaker: str | None = None,
        avatar: pygame.Surface | None = None,
        align: str = "left",
        dim_background: bool = True,
        close_on_escape: bool = True,
        **kwargs,
    ):
        self.height_ratio = float(height_ratio)
        self.margin = int(margin)
        self.button_align = button_align
        self.speaker = speaker
        self.avatar = avatar
        self.avatar_rect: pygame.Rect | None = None

        super().__init__(
            title=title,
            message=message,
            actions=actions,
            height=height,
            align=align,
            dim_background=dim_background,
            close_on_escape=close_on_escape,
            **kwargs,
        )

    def _recalculate_layout(self):
        screen_w, screen_h = self._get_screen_size()

        # Height determination: explicit pixel height, ratio float (<= 1.0), or height_ratio (default 1/3)
        if self.custom_height is not None:
            if isinstance(self.custom_height, float) and 0.0 < self.custom_height <= 1.0:
                panel_h = int(screen_h * self.custom_height)
            else:
                panel_h = int(self.custom_height)
        else:
            panel_h = int(screen_h * self.height_ratio)

        panel_h = max(100, min(panel_h, screen_h))

        # Full width docked at bottom
        panel_w = max(240, screen_w - (self.margin * 2))
        panel_x = self.margin
        panel_y = screen_h - panel_h - self.margin
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        # Avatar layout
        avatar_w = 0
        if self.avatar:
            av_size = min(panel_h - 36, 160)
            self.avatar_rect = pygame.Rect(panel_x + 24, panel_y + (panel_h - av_size) // 2, av_size, av_size)
            avatar_w = av_size + 24
        else:
            self.avatar_rect = None

        # Prepare fonts & text wrapping
        body_font = get_dialog_font("body", 18)
        num_buttons = len(self.actions)
        is_horizontal = (self.button_layout == "horizontal") or (
            self.button_layout == "auto" and num_buttons <= 4
        )
        btn_h = 42
        spacing = 16

        # Reserve horizontal space for buttons if right-aligned
        if self.button_align == "right" and is_horizontal and num_buttons > 0:
            btn_w = 140
            total_btns_w = num_buttons * btn_w + (num_buttons - 1) * spacing
            content_max_w = panel_w - 60 - avatar_w - (total_btns_w + 30)
            if content_max_w < 340:
                content_max_w = panel_w - 60 - avatar_w
        else:
            content_max_w = panel_w - 60 - avatar_w

        content_max_w = max(200, content_max_w)

        # Wrap text
        if isinstance(self.raw_message, list):
            self.wrapped_lines = []
            for item in self.raw_message:
                self.wrapped_lines.extend(wrap_text(str(item), body_font, content_max_w))
        else:
            self.wrapped_lines = wrap_text(str(self.raw_message), body_font, content_max_w)

        # Layout button rectangles
        self.button_rects = []
        if is_horizontal:
            btn_w = 140
            total_btns_w = num_buttons * btn_w + (num_buttons - 1) * spacing

            if self.button_align == "right":
                start_x = self.panel_rect.right - 30 - total_btns_w
            else:
                start_x = panel_x + (panel_w - total_btns_w) // 2

            btn_y = self.panel_rect.bottom - btn_h - (24 if self.close_on_escape else 16)

            for i in range(num_buttons):
                rect = pygame.Rect(start_x + i * (btn_w + spacing), btn_y, btn_w, btn_h)
                self.button_rects.append(rect)
        else:
            btn_w = min(220, panel_w - 80)
            btn_x = self.panel_rect.right - btn_w - 30 if self.button_align == "right" else panel_x + (panel_w - btn_w) // 2
            start_y = self.panel_rect.bottom - (num_buttons * (btn_h + spacing)) - 16

            for i in range(num_buttons):
                rect = pygame.Rect(btn_x, start_y + i * (btn_h + spacing), btn_w, btn_h)
                self.button_rects.append(rect)

    def draw(self, screen: pygame.Surface):
        # 1. Dim background
        if self.dim_background:
            shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 160))
            screen.blit(shade, (0, 0))

        # 2. Main Dialog Panel
        panel_surf = pygame.Surface((self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((16, 22, 34, 245))
        screen.blit(panel_surf, self.panel_rect.topleft)

        # Accent border
        if self.margin == 0:
            pygame.draw.line(
                screen,
                (135, 242, 255),
                (self.panel_rect.left, self.panel_rect.top),
                (self.panel_rect.right, self.panel_rect.top),
                3,
            )
            pygame.draw.line(
                screen,
                (50, 90, 130),
                (self.panel_rect.left, self.panel_rect.top + 3),
                (self.panel_rect.right, self.panel_rect.top + 3),
                1,
            )
        else:
            pygame.draw.rect(screen, (135, 242, 255), self.panel_rect, width=2, border_radius=10)

        # 3. Avatar
        content_x = self.panel_rect.x + 30
        if self.avatar and self.avatar_rect:
            scaled_av = pygame.transform.smoothscale(self.avatar, self.avatar_rect.size)
            screen.blit(scaled_av, self.avatar_rect.topleft)
            pygame.draw.rect(screen, (135, 242, 255), self.avatar_rect, width=2, border_radius=6)
            content_x = self.avatar_rect.right + 20

        # 4. Header (Speaker / Title)
        curr_y = self.panel_rect.y + 18
        title_font = get_dialog_font("title", 18)
        header_text = self.speaker or self.title

        if header_text and title_font:
            accent_color = (255, 215, 80) if self.speaker else (135, 242, 255)
            h_surf = title_font.render(header_text, True, accent_color)
            screen.blit(h_surf, (content_x, curr_y))

            if self.speaker and self.title:
                sub_font = get_dialog_font("body", 14)
                if sub_font:
                    sub_surf = sub_font.render(f"// {self.title}", True, (140, 160, 185))
                    screen.blit(sub_surf, (content_x + h_surf.get_width() + 16, curr_y + 2))

            curr_y += h_surf.get_height() + 8
            divider_w = min(400, self.panel_rect.right - content_x - 30)
            if divider_w > 50:
                pygame.draw.line(
                    screen,
                    (45, 65, 95),
                    (content_x, curr_y),
                    (content_x + divider_w, curr_y),
                    1,
                )
                curr_y += 10
        else:
            curr_y += 8

        # 5. Message Content
        body_font = get_dialog_font("body", 18)
        if body_font and self.wrapped_lines:
            line_height = body_font.get_linesize()
            for line in self.wrapped_lines:
                if not line:
                    curr_y += line_height // 2
                    continue
                surf = body_font.render(line, True, (220, 235, 250))
                screen.blit(surf, (content_x, curr_y))
                curr_y += line_height

        # 6. Action Buttons
        btn_font = get_dialog_font("title", 14)
        for idx, (action, rect) in enumerate(zip(self.actions, self.button_rects)):
            is_selected = (idx == self.selected_index)
            bg_color = (35, 55, 85) if is_selected else (22, 30, 48)
            border_color = (135, 242, 255) if is_selected else (65, 85, 115)
            text_color = (255, 255, 255) if is_selected else (190, 205, 225)

            pygame.draw.rect(screen, bg_color, rect, border_radius=8)
            pygame.draw.rect(screen, border_color, rect, width=2 if is_selected else 1, border_radius=8)

            if btn_font:
                label_text = ("> " if is_selected else "  ") + action["label"]
                text_surf = btn_font.render(label_text, True, text_color)
                screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        # 7. Escape / Cancel hint
        if self.close_on_escape and body_font:
            hint_surf = body_font.render("ESC / (B) TO CANCEL", True, (100, 120, 140))
            hint_surf = pygame.transform.smoothscale(
                hint_surf,
                (max(1, hint_surf.get_width() // 2), max(1, hint_surf.get_height() // 2)),
            )
            hint_x = content_x
            hint_y = self.panel_rect.bottom - 16
            screen.blit(hint_surf, hint_surf.get_rect(midleft=(hint_x, hint_y)))


BottomBannerDialog = BottomDialog


class MultiPageBottomDialog(BottomDialog):
    """Multi-page variant of BottomDialog supporting interactive multi-step dialogues."""

    def __init__(
        self,
        pages: list[dict],
        on_complete: callable | None = None,
        on_cancel: callable | None = None,
        finish_label: str = "FINISH",
        next_label: str = "NEXT",
        prev_label: str = "PREV",
        height: int | float | None = None,
        height_ratio: float = 1.0 / 3.0,
        **kwargs,
    ):
        self.pages = pages or [{"title": "INFO", "message": ""}]
        self.current_page: int = 0
        self.on_complete = on_complete
        self.finish_label = finish_label
        self.next_label = next_label
        self.prev_label = prev_label

        super().__init__(
            title="",
            message="",
            actions=[],
            on_cancel=on_cancel,
            height=height,
            height_ratio=height_ratio,
            **kwargs,
        )
        self._load_current_page()

    def _load_current_page(self, forward_focus: bool = True):
        page = self.pages[self.current_page]
        title = page.get("title", f"STEP {self.current_page + 1}/{len(self.pages)}")
        message = page.get("message", "")
        self.speaker = page.get("speaker", None)
        self.avatar = page.get("avatar", None)

        is_last = (self.current_page == len(self.pages) - 1)
        actions = []

        if self.current_page > 0:
            actions.append({"label": self.prev_label, "callback": self.prev_page, "close": False})

        if is_last:
            actions.append({"label": self.finish_label, "callback": self._on_finish, "close": True})
        else:
            actions.append({"label": self.next_label, "callback": self.next_page, "close": False})

        self.title = title
        self.raw_message = message
        self.set_actions(actions)

        if forward_focus and len(self.actions) > 1:
            self.selected_index = len(self.actions) - 1
        elif not forward_focus:
            self.selected_index = 0

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._load_current_page(forward_focus=True)
        return False

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._load_current_page(forward_focus=False)
        return False

    def _on_finish(self):
        if callable(self.on_complete):
            try:
                self.on_complete()
            except TypeError:
                self.on_complete(self)


def show_bottom_dialog(
    manager,
    title: str = "",
    message: str | list[str] = "",
    actions: list | None = None,
    height: int | float | None = None,
    height_ratio: float = 1.0 / 3.0,
    **kwargs,
) -> BottomDialog:
    """Creates and displays a BottomDialog overlay docked to the bottom of the screen."""
    dialog = BottomDialog(
        title=title,
        message=message,
        actions=actions,
        height=height,
        height_ratio=height_ratio,
        **kwargs,
    )
    manager.show_overlay(dialog)
    return dialog
