"""Persistent player settings and their runtime helpers."""

import json
import pathlib

import pygame

import config


DEFAULTS = {
    "resource_pack": None,
    "display_mode": "windowed",
    "master_volume": 1.0,
    "music_volume": 1.0,
    "sound_volume": 1.0,
}

_values = dict(DEFAULTS)


def load() -> dict:
    """Load settings, adding defaults introduced by newer game versions."""
    global _values
    saved = {}
    settings_path = pathlib.Path(config.SETTINGS_FILE)
    try:
        with settings_path.open("r", encoding="utf-8") as settings_file:
            saved = json.load(settings_file)
    except (OSError, json.JSONDecodeError):
        pass
    _values = dict(DEFAULTS)
    if isinstance(saved, dict):
        _values.update({key: value for key, value in saved.items() if key in DEFAULTS})
    save()
    return _values


def save():
    """Write the complete player settings document."""
    with pathlib.Path(config.SETTINGS_FILE).open("w", encoding="utf-8") as settings_file:
        json.dump(_values, settings_file, indent=2)


def get(key):
    return _values.get(key, DEFAULTS.get(key))


def set(key, value):
    if key not in DEFAULTS:
        raise KeyError(f"Unknown setting: {key}")
    _values[key] = value
    save()


def create_display() -> pygame.Surface:
    """Create a fixed logical-resolution display in the requested window mode."""
    logical_size = (config.Screen.Size.w, config.Screen.Size.h)
    if get("display_mode") == "fullscreen":
        # SCALED keeps pygame's coordinate system at the logical game size,
        # while fullscreen presents it at the monitor's native resolution.
        screen = pygame.display.set_mode(logical_size, pygame.FULLSCREEN | pygame.SCALED)
    else:
        screen = pygame.display.set_mode(logical_size)
    return screen


def apply_audio():
    """Apply current volume preferences to loaded pygame audio."""
    combined_music = float(get("master_volume")) * float(get("music_volume"))
    pygame.mixer.music.set_volume(combined_music)
    try:
        from . import assets
        combined_sound = float(get("master_volume")) * float(get("sound_volume"))
        for name in vars(assets.Sounds):
            sound = getattr(assets.Sounds, name)
            if isinstance(sound, pygame.mixer.Sound):
                sound.set_volume(combined_sound)
    except ImportError:
        pass
