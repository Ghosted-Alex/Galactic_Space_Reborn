"""Gameplay Screen / Scene for Galactic Space Reborn.

Provides dedicated load(), unload(), handle_event(), update(), and draw() functions
as well as a GameplayScene class wrapper.
"""

import os
import random
import sys
import pygame
import config
from src import assets
from src import entity
from src import update as update_mod
from src import ui
from src import controls
from src.controls import ControllerInput
from src import starfield
from src import stats
from src import clock
from src import states
from src import events
from .base import BaseScene


_state = {
    "loaded": False,
    "player": None,
    "stars_bg": None,
    "enemies": [],
    "bullets": [],
    "powerups": [],
    "effects": [],
}


def load(*args, **kwargs):
    """Dedicated scene load function. Initializes player, entities, and gameplay state."""
    _state["loaded"] = True
    
    # Reset game state flags
    states.game_over = False
    states.game_over_ui_shown = False
    states.blink_timer = 60
    states.health_blink_timer = 60
    states.powerup_timer = 0
    states.powerup_active = False
    stats.score = 0

    # Load high score
    if not config.check_high_score_exists():
        events.save_high_score(stats.high_score, config.HIGH_SCORE_FILE)
    else:
        stats.high_score = events.load_high_score(config.HIGH_SCORE_FILE)

    # Initialize Player & Stars background
    _state["player"] = entity.Player(150, config.Screen.Size.h // 2 - 20)
    player_rect = _state["player"].texture.get_rect(center=(config.Screen.Size.w // 2, config.Screen.Size.h // 2))
    _state["player"].x, _state["player"].y = player_rect.topleft

    _state["stars_bg"] = starfield.Generate(config.Screen.Size.w, config.Screen.Size.h)

    _state["enemies"].clear()
    _state["bullets"].clear()
    _state["powerups"].clear()
    _state["effects"].clear()


def unload():
    """Dedicated scene unload function. Cleans up gameplay entities."""
    _state["loaded"] = False
    _state["player"] = None
    _state["stars_bg"] = None
    _state["enemies"].clear()
    _state["bullets"].clear()
    _state["powerups"].clear()
    _state["effects"].clear()


def handle_event(event: pygame.event.Event, manager=None):
    """Dedicated event handler for active gameplay."""
    player = _state["player"]

    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit(0)

    if not states.game_over:
        if event.type == pygame.KEYDOWN:
            if event.key == config.KeyBinds.General.escape and manager:
                from .pause_menu import PauseMenuScene
                manager.show_overlay(PauseMenuScene())
                return
            if config.debug:
                if controls.single_press(event, config.KeyBinds.Debug.numpad_plus):
                    if stats.score < 10:
                        stats.score += 10
                    else:
                        stats.score += stats.score * 10
                if controls.single_press(event, config.KeyBinds.Debug.numrow_1):
                    keys_pressed = pygame.key.get_pressed()
                    if keys_pressed[config.KeyBinds.Debug.debug_key]:
                        events.spawn_powerup(50, player, _state["powerups"])

            if controls.single_press(event=event, key=config.KeyBinds.Gameplay.shoot):
                if player and not states.game_over:
                    events.on_shoot(player, _state["effects"], _state["bullets"])

        if event.type == pygame.KEYUP:
            if event.key == config.KeyBinds.Debug.debug_key:
                keys_pressed = pygame.key.get_pressed()
                combo_keys = [config.KeyBinds.Debug.numrow_1]
                if not any(keys_pressed[k] for k in combo_keys):
                    config.debug = not config.debug

        # --- Controller: Pause (Start or Back/hamburger) ---
        if ControllerInput.pause(event) and manager:
            from .pause_menu import PauseMenuScene
            manager.show_overlay(PauseMenuScene())
            return

        # --- Controller: Shoot (A button or RB) ---
        if ControllerInput.shoot(event):
            if player and not states.game_over:
                events.on_shoot(player, _state["effects"], _state["bullets"])

        # --- Controller: D-Pad movement (discrete hat step → player) ---
        if player and event.type == pygame.JOYHATMOTION:
            keys = pygame.key.get_pressed()
            player.handle_input(keys, event=event)

    else:
        # Game Over inputs — keyboard
        if event.type == pygame.KEYDOWN:
            if event.key == config.KeyBinds.General.reset:
                # Restart gameplay scene
                load()
            elif event.key == pygame.K_ESCAPE and manager:
                # Return to Title screen
                from .title import TitleScene
                manager.set_scene(TitleScene(), fade=True)

        # Game Over inputs — controller (A = restart, B = title)
        if ControllerInput.confirm(event):
            load()
        elif ControllerInput.cancel(event) and manager:
            from .title import TitleScene
            manager.set_scene(TitleScene(), fade=True)


def game_over():
    """Triggers game over event."""
    if not states.game_over:
        events.on_game_over()


def update(dt: float = 1.0):
    """Dedicated update function. Updates entities, physics, and gameplay logic."""
    if not _state["loaded"]:
        return

    update_mod.update_time()
    player = _state["player"]

    if not states.game_over:
        if states.blink_timer < config.blink_timer_max:
            states.blink_timer += 1
        if states.health_blink_timer < config.blink_timer_max:
            states.health_blink_timer += 1

        keys = pygame.key.get_pressed()

        if _state["stars_bg"]:
            _state["stars_bg"].update()

        update_mod.update_entities(
            enemies=_state["enemies"],
            bullets=_state["bullets"],
            powerups=_state["powerups"],
            player=player,
            screen=None
        )

        for eff in _state["effects"][:]:
            eff.update(dt)
            if hasattr(eff, 'is_expired') and eff.is_expired():
                _state["effects"].remove(eff)

        if player:
            player.handle_input(keys)

        if clock.delay < 0:
            clock.delay = 60

        # Adjust enemy spawn frequency according to states.difficulty
        diff_multiplier = getattr(states, "difficulty", 1.0)
        
        if clock.delay == 0:
            events.spawn_enemy(_state["enemies"])

        if clock.delay == random.randint(1, 60):
            chance = random.randint(1, 100)
            events.spawn_powerup(chance, player, _state["powerups"])

        if clock.delay == 0:
            if player and player.energy < 75:
                player.energy += 10
            if states.powerup_timer > 0:
                states.powerup_timer -= 1

        if states.powerup_timer <= 0 and states.powerup_active:
            if states.powerup_type == 0:
                states.health_blink_timer = 0
                states.powerup_active = False
                if player:
                    player.invincible = False

        if player and player.health <= 0:
            game_over()

        stats.score = min(stats.score, 1000000)
        stats.high_score = min(stats.high_score, 1000000)


def draw(screen: pygame.Surface):
    """Dedicated draw function. Renders gameplay scene."""
    screen.fill((0, 0, 0))

    if _state["stars_bg"]:
        _state["stars_bg"].draw(screen)

    player = _state["player"]

    if not states.game_over:
        # Draw game world entities
        for e in _state["enemies"]:
            e.draw(screen)

        for b in _state["bullets"]:
            b.draw(screen)

        for p in _state["powerups"]:
            p.draw(screen)

        for eff in _state["effects"]:
            eff.draw(screen)

        if player:
            player.draw(screen)

        ui.draw_panel_ui(screen, player=player)
    else:
        # Draw entities behind game over overlay
        for e in _state["enemies"]:
            e.draw(screen)
        for b in _state["bullets"]:
            b.draw(screen)
        for p in _state["powerups"]:
            p.draw(screen)
        if player:
            player.draw(screen)

        # Game Over drawing
        screen.blit(assets.Textures.panel_01, (0, config.Screen.Size.h - 45))
        pygame.draw.rect(screen, config.background_health_color, (15, 826, 400, 25))

        if player:
            pygame.draw.rect(screen, config.health_color_drain, (15, 826, player.health_drain * 4, 25))
            if player.health > 50:
                pygame.draw.rect(screen, config.health_color_high, (15, 826, player.health * 4, 25))
            elif 50 >= player.health > 25:
                pygame.draw.rect(screen, config.health_color_med, (15, 826, player.health * 4, 25))
            elif player.health <= 25:
                pygame.draw.rect(screen, config.health_color_low, (15, 826, player.health * 4, 25))

            if player.health_drain > player.health:
                player.health_drain -= .1
            elif player.health_drain < player.health:
                player.health_drain = player.health

        pygame.draw.rect(screen, config.background_energy_color, (657, 826, 400, 25))
        if player:
            energy_width = player.energy * 4
            reverse_x = 657 + (400 - energy_width)
            if player.energy > 0:
                pygame.draw.rect(screen, config.energy_color, (reverse_x, 826, energy_width, 25))

        ui.draw_game_over_ui(screen=screen)


class GameplayScene(BaseScene):
    """Class wrapper for Gameplay scene."""

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
