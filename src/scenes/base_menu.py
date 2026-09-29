import pygame
import config
from src import assets
from .base import BaseScene


class DecoratorMenuScene(BaseScene):
    def __init__(self):
        super().__init__()
        self.buttons = []
        self.submenus = {}

        # State tracking
        self.selected_index = 0
        self.option_rects = []
        self.active_submenu = None

        # Look for methods decorated with @button or @submenu
        for attr_name in dir(self):
            attr = getattr(self, attr_name)

            # Process Buttons
            if hasattr(attr, "_is_menu_button"):
                self.buttons.append({
                    "text": attr._button_text,
                    "w": attr._button_width,
                    "h": attr._button_height,
                    "order": attr._button_order,
                    "callback": attr
                })

            # Process Submenus
            if hasattr(attr, "_is_submenu_handler"):
                self.submenus[attr._trigger_text] = attr

        # Sort buttons by explicit order
        self.buttons.sort(key=lambda b: b["order"])

    def handle_event(self, event: pygame.event.Event):
        # Direct input routing if an overlay submenu is open
        if self.active_submenu:
            if self.active_submenu(event) == "CLOSE":
                self.active_submenu = None
            return

        # Keyboard Navigation
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._trigger_button(self.selected_index)

        # Mouse Navigation
        elif event.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(self.option_rects):
                if rect and rect.collidepoint(event.pos):
                    self.selected_index = idx

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in enumerate(self.option_rects):
                if rect and rect.collidepoint(event.pos):
                    self._trigger_button(idx)

    def _trigger_button(self, index):
        btn = self.buttons[index]
        if btn["text"] in self.submenus:
            self.active_submenu = self.submenus[btn["text"]]
        else:
            btn["callback"]()

    def draw_buttons(self, screen, start_y, spacing):
        center_x = config.Screen.Size.w // 2
        font = getattr(assets, "pressStart2P", None)
        self.option_rects = []

        for idx, btn in enumerate(self.buttons):
            is_selected = (idx == self.selected_index)
            btn_rect = pygame.Rect(center_x - btn["w"] // 2, start_y + idx * spacing, btn["w"], btn["h"])
            self.option_rects.append(btn_rect)

            bg_color = (30, 45, 65) if is_selected else (18, 22, 32)
            border_color = (135, 242, 255) if is_selected else (55, 65, 80)

            pygame.draw.rect(screen, bg_color, btn_rect, border_radius=10)
            pygame.draw.rect(screen, border_color, btn_rect, width=2 if is_selected else 1, border_radius=10)

            if font:
                if hasattr(self, "draw_custom_button_content"):
                    handled = self.draw_custom_button_content(screen, btn, btn_rect, is_selected, font)
                    if handled: continue

                text_surf = font.render(btn["text"], True, (135, 242, 255) if is_selected else (200, 200, 200))
                screen.blit(text_surf, text_surf.get_rect(center=btn_rect.center))