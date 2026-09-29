"""Config Module"""

import pygame
import os
import pathlib
import sys
import math

from src import logger

# ------------------- PYINSTALLER EXCLUSIVE CODE | DO NOT EDIT --------------
if hasattr(sys, "_MEIPASS"):
  # Compiled Exe: Static assets and manifests come from the read-only temp sandbox
  WIN_PATH = pathlib.Path(sys._MEIPASS)
  # Writable Data: Saves, settings, and mods go next to the actual game launcher executable
  DATA_PATH = pathlib.Path(sys.executable).resolve().parent
else:
  # Dev Mode: Everything lives relative to config.py
  WIN_PATH = pathlib.Path(__file__).resolve().parent
  DATA_PATH = WIN_PATH
# ----------------------------------------------------------------------------

# --- Static Engine Files (Bundled in PyInstaller) ---
MANIFEST_FILE = (
    WIN_PATH / "manifest.json"
)  # Defaults to temp folder when compiled

# --- Writable User Data / Saves / External Content ---
HIGH_SCORE_FILE = DATA_PATH / "high_score.txt"
SETTINGS_FILE = DATA_PATH / "settings.json"

# Resource packs and mods should live outside so players can add them easily!
RESOURCE_PACKS_DIR = DATA_PATH / "resource_packs"

PACKS_ACTIVE = False
"""Whether the current runtime is using a resource pack instead of vanilla assets."""


def check_high_score_exists() -> bool:
    """Dynamic boolean check: True if high_score.txt exists on disk right now."""
    return HIGH_SCORE_FILE.exists()

class ControllerBindings:
    class XboxController:
        # Standard Xbox layout mappings in Pygame
        BUTTON_A = 0
        BUTTON_B = 1
        BUTTON_X = 2
        BUTTON_Y = 3
        BUTTON_LB = 4
        BUTTON_RB = 5
        BUTTON_BACK = 6
        BUTTON_START = 7
        BUTTON_LS = 8
        BUTTON_RS = 9
        BUTTON_SHOOT = 0  # Map A button or RT/RB for shooting

        # Axis mappings
        AXIS_LEFT_X = 0
        AXIS_LEFT_Y = 1
        AXIS_RIGHT_X = 2
        AXIS_RIGHT_Y = 3
        AXIS_TRIGGER_LEFT = 4
        AXIS_TRIGGER_RIGHT = 5

    @staticmethod
    def get_controller(joystick_index=0):
        if pygame.joystick.get_count() > joystick_index:
            try:
                return pygame.joystick.Joystick(joystick_index)
            except pygame.error:
                return None
        return None
        
    @staticmethod
    def get_move_vector(deadzone=0.15):
        """Returns normalized (x, y) vector for movement with deadzone applied."""
        if pygame.joystick.get_count() == 0:
            return 0.0, 0.0
        try:
            joystick = ControllerBindings.get_controller(0)
            if not joystick:
                return 0.0, 0.0
            x = joystick.get_axis(ControllerBindings.XboxController.AXIS_LEFT_X)
            y = joystick.get_axis(ControllerBindings.XboxController.AXIS_LEFT_Y)
            if abs(x) < deadzone: x = 0.0
            if abs(y) < deadzone: y = 0.0
            return x, y
        except pygame.error:
            return 0.0, 0.0

class KeyBinds:
    """Organizes control inputs into categories for easy access."""

    class Gameplay:
        """Controls for player movement and actions."""
        up = pygame.K_w
        left = pygame.K_a
        down = pygame.K_s
        right = pygame.K_d
        shoot = (pygame.K_SPACE, pygame.K_z)

    class Debug:
        """Keys reserved for development and troubleshooting."""
        numpad_plus = pygame.K_KP_PLUS
        numrow_1 = pygame.K_1
        debug_key = pygame.K_F12

    class General:
        """Miscellaneous game controls."""
        reset = pygame.K_r
        escape = pygame.K_ESCAPE

SPRITE_SCALING = 3
"""Multiplier for sprite asset scaling."""

debug = False
"""Boolean flag to enable/disable debug mode."""

# Color constants (RGB)
background_health_color = (15, 15, 15)
background_energy_color = (15, 15, 15)

health_color_high = (50, 168, 82)  # Green
health_color_med = (166, 164, 51)  # Yellow
health_color_low = (166, 51, 51)  # Red
health_color_drain = (135, 242, 255)  # Cyan

energy_color = (219, 212, 53)

blink_timer_max = 60
"""Max frames for UI blink animations."""


class Screen:
    """Screen settings."""

    class Size:
        """Resolution dimensions."""
        w = 1072
        """Window width."""
        h = 861
        """Window height."""


class Game:
    """Global game metadata."""
    title = "Galactic Space Reborn"

format_ver = 1

version_string = "1.0-beta.3"
"""Args:
    String: '<major>.<minor>-beta|build.<beta|build_number>'"""

# Initialize variables
major, minor = "0", "0"
build = "0"

# 1. Separate the core version (e.g., "1.0") from the metadata tail
if "-" in version_string:
    core, tail = version_string.split("-", 1)
else:
    core, tail = version_string, ""

# 2. Extract major and minor
version_bits = core.split(".")
major = version_bits[0]
if len(version_bits) > 1:
    minor = version_bits[1]

build = tail # e.g., "beta.1 / build.20260822"

version = f"{major}.{minor}-{build}"

p02_pos = [Screen.Size.w - 246, Screen.Size.h - 195]
"""Position anchor for the Panel 02 UI Element."""

logger.config_log.info("Loaded Config")

if __name__ == "__main__":
    print(ModuleNotFoundError(
        "No module named config.__main__; 'config' is a dedicated module for Galactic Space Reborn and cannot be directly executed"))
    print("(Run the game with main.py, not the config file)")
