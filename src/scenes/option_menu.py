"""Reusable scene base for menus declared with @option_def."""

import pygame

import config
from src import assets, settings, starfield
from src.controls import ControllerInput
from .base import BaseScene


class OptionMenuScene(BaseScene):
    title = "SETTINGS"
    requires_apply = False

    def __init__(self):
        super().__init__()
        self.options = []
        for name in dir(self):
            callback = getattr(self, name)
            if hasattr(callback, "_is_option_definition"):
                self.options.append({
                    "key": callback._option_key,
                    "label": callback._option_label,
                    "choices": callback._option_choices,
                    "description": callback._option_description,
                    "callback": callback,
                    "order": callback._option_order,
                })
        self.options.sort(key=lambda option: option["order"])
        self.selected_index = 0
        self.row_rects = []
        self.apply_rect = None
        self.pending_values = {}
        self.stars_bg = None

    def load(self, *args, **kwargs):
        self.selected_index = 0
        self.pending_values = {option["key"]: settings.get(option["key"]) for option in self.options}
        self.stars_bg = starfield.Generate(config.Screen.Size.w, config.Screen.Size.h)

    def unload(self):
        self.stars_bg = None
        self.row_rects = []

    def return_to_options(self):
        from .options import OptionsScene
        self.manager.set_scene(OptionsScene(), fade=True)

    def _change_value(self, direction):
        if self.requires_apply and self.selected_index == len(self.options):
            return
        option = self.options[self.selected_index]
        choices = option["choices"]
        current = self.pending_values[option["key"]] if self.requires_apply else settings.get(option["key"])
        try:
            current_index = choices.index(current)
        except ValueError:
            current_index = 0
        value = choices[(current_index + direction) % len(choices)]
        if self.requires_apply:
            self.pending_values[option["key"]] = value
        else:
            settings.set(option["key"], value)
            option["callback"](value)

    def _apply_pending_changes(self):
        """Persist deferred settings and run their callbacks once confirmed."""
        for option in self.options:
            key = option["key"]
            value = self.pending_values[key]
            if value != settings.get(key):
                settings.set(key, value)
                option["callback"](value)

    def _activate_selected(self):
        if self.requires_apply and self.selected_index == len(self.options):
            self._apply_pending_changes()
        else:
            self._change_value(1)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.return_to_options()
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % (len(self.options) + int(self.requires_apply))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % (len(self.options) + int(self.requires_apply))
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._change_value(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_RETURN, pygame.K_SPACE):
                self._activate_selected()
        # Controller navigation
        elif ControllerInput.nav_up(event):
            self.selected_index = (self.selected_index - 1) % (len(self.options) + int(self.requires_apply))
        elif ControllerInput.nav_down(event):
            self.selected_index = (self.selected_index + 1) % (len(self.options) + int(self.requires_apply))
        elif ControllerInput.nav_left(event):
            self._change_value(-1)
        elif ControllerInput.nav_right(event) or ControllerInput.confirm(event):
            self._activate_selected()
        elif ControllerInput.cancel(event):
            self.return_to_options()
        elif event.type == pygame.MOUSEMOTION:
            for index, row in enumerate(self.row_rects):
                if row.collidepoint(event.pos):
                    self.selected_index = index
                    break
            if self.apply_rect and self.apply_rect.collidepoint(event.pos):
                self.selected_index = len(self.options)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, row in enumerate(self.row_rects):
                if row.collidepoint(event.pos):
                    self.selected_index = index
                    self._change_value(1)
                    break
            if self.apply_rect and self.apply_rect.collidepoint(event.pos):
                self.selected_index = len(self.options)
                self._apply_pending_changes()

    def update(self, dt=1.0):
        if self.stars_bg:
            self.stars_bg.update()

    def draw(self, screen):
        screen.fill((0, 0, 0))
        if self.stars_bg:
            self.stars_bg.draw(screen)
        title_font = getattr(assets, "pressStart2P", None)
        body_font = getattr(assets, "monocraft", title_font)
        center_x = config.Screen.Size.w // 2
        if title_font:
            title = title_font.render(self.title, True, (255, 255, 255))
            screen.blit(title, title.get_rect(center=(center_x, 105)))

        panel = pygame.Rect(center_x - 390, 175, 780, 450)
        pygame.draw.rect(screen, (18, 24, 36), panel, border_radius=10)
        pygame.draw.rect(screen, (60, 80, 110), panel, width=2, border_radius=10)
        self.row_rects = []
        for index, option in enumerate(self.options):
            row = pygame.Rect(panel.x + 25, panel.y + 28 + index * 105, panel.width - 50, 84)
            self.row_rects.append(row)
            selected = index == self.selected_index
            pygame.draw.rect(screen, (30, 45, 65) if selected else (22, 30, 45), row, border_radius=8)
            pygame.draw.rect(screen, (135, 242, 255) if selected else (60, 80, 110), row, width=2 if selected else 1, border_radius=8)
            if body_font:
                label = body_font.render(option["label"], True, (255, 255, 255))
                selected_value = self.pending_values[option["key"]] if self.requires_apply else settings.get(option["key"])
                value = body_font.render(str(selected_value).upper(), True, (219, 212, 53))
                screen.blit(label, (row.x + 20, row.y + 12))
                screen.blit(value, value.get_rect(topright=(row.right - 20, row.y + 12)))
                if option["description"]:
                    description = body_font.render(option["description"], True, (145, 160, 180))
                    description = pygame.transform.smoothscale(description, (max(1, description.get_width() // 2), max(1, description.get_height() // 2)))
                    screen.blit(description, (row.x + 20, row.y + 52))
        self.apply_rect = None
        if self.requires_apply:
            self.apply_rect = pygame.Rect(panel.centerx - 150, panel.bottom - 82, 300, 48)
            selected = self.selected_index == len(self.options)
            pygame.draw.rect(screen, (45, 30, 35) if selected else (30, 25, 35), self.apply_rect, border_radius=6)
            pygame.draw.rect(screen, (255, 135, 135) if selected else (135, 242, 255), self.apply_rect, width=2 if selected else 1, border_radius=6)
            if body_font:
                apply_text = body_font.render("APPLY & RESTART", True, (255, 255, 255))
                apply_text = pygame.transform.smoothscale(apply_text, (max(1, int(apply_text.get_width() * 0.7)), max(1, int(apply_text.get_height() * 0.7))))
                screen.blit(apply_text, apply_text.get_rect(center=self.apply_rect.center))
                if self.manager and self.manager.has_previous_scene():
                    warning = body_font.render("Changing the video settings requires a restart\nAny unsaved progress will be lost", True, (255, 135, 135))
                    warning = pygame.transform.smoothscale(warning, (max(1, warning.get_width() // 2), max(1, warning.get_height() // 2)))
                    screen.blit(warning, warning.get_rect(center=(center_x, panel.bottom + 25)))
        if body_font:
            help_text = body_font.render("LEFT/RIGHT TO CHANGE    ESC TO GO BACK", True, (135, 150, 170))
            screen.blit(help_text, help_text.get_rect(center=(center_x, config.Screen.Size.h - 70)))
