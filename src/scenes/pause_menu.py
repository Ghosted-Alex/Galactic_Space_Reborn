"""Pause overlay for an active gameplay run."""

import pygame

import config
from src import assets
from src.controls import ControllerInput
from .base import BaseScene


class PauseMenuScene(BaseScene):
    options = ("RESUME", "OPTIONS", "QUIT TO TITLE")

    def __init__(self):
        super().__init__()
        self.selected_index = 0
        self.option_rects = []

    def load(self, *args, **kwargs):
        self.selected_index = 0
        self.option_rects = []

    def unload(self):
        self.option_rects = []

    def _activate(self, index):
        selected = self.options[index]
        if selected == "RESUME":
            self.manager.close_overlay()
        elif selected == "OPTIONS":
            self.manager.close_overlay()
            from .options import OptionsScene
            self.manager.push_scene(OptionsScene())
        elif selected == "QUIT TO TITLE":
            self.manager.close_overlay()
            from .title import TitleScene
            self.manager.set_scene(TitleScene(), fade=True)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.close_overlay()
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate(self.selected_index)
        # Controller navigation
        elif ControllerInput.nav_up(event):
            self.selected_index = (self.selected_index - 1) % len(self.options)
        elif ControllerInput.nav_down(event):
            self.selected_index = (self.selected_index + 1) % len(self.options)
        elif ControllerInput.confirm(event):
            self._activate(self.selected_index)
        elif ControllerInput.cancel(event) or ControllerInput.pause(event):
            # B button or Start/Back closes the pause menu (resume)
            self.manager.close_overlay()
        elif event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = index
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = index
                    self._activate(index)
                    break

    def draw(self, screen):
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 175))
        screen.blit(shade, (0, 0))
        center_x = config.Screen.Size.w // 2
        panel = pygame.Rect(center_x - 290, 205, 580, 410)
        pygame.draw.rect(screen, (18, 24, 36), panel, border_radius=10)
        pygame.draw.rect(screen, (135, 242, 255), panel, width=2, border_radius=10)

        title_font = getattr(assets, "pressStart2P", None)
        body_font = getattr(assets, "monocraft", title_font)
        if title_font:
            title = title_font.render("PAUSED", True, (255, 255, 255))
            screen.blit(title, title.get_rect(center=(center_x, panel.y + 65)))

        self.option_rects = []
        for index, label in enumerate(self.options):
            button = pygame.Rect(panel.x + 50, panel.y + 115 + index * 85, panel.width - 100, 60)
            self.option_rects.append(button)
            selected = index == self.selected_index
            pygame.draw.rect(screen, (30, 45, 65) if selected else (22, 30, 45), button, border_radius=8)
            pygame.draw.rect(screen, (135, 242, 255) if selected else (60, 80, 110), button, width=2 if selected else 1, border_radius=8)
            if body_font:
                text = body_font.render(("> " if selected else "  ") + label, True, (255, 255, 255) if selected else (190, 200, 215))
                screen.blit(text, text.get_rect(center=button.center))

        if body_font:
            hint = body_font.render("ESC TO RESUME", True, (135, 150, 170))
            hint = pygame.transform.smoothscale(hint, (max(1, hint.get_width() // 2), max(1, hint.get_height() // 2)))
            screen.blit(hint, hint.get_rect(center=(center_x, panel.bottom - 25)))
