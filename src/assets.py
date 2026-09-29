"""Assets Module"""

import pathlib
import pygame
import config
import time
import random
import json
import importlib

from . import logger

# Initialize mixer for sound assets
pygame.mixer.init()

class Textures:
    """Storage containers that your entity files (entity.py) read from."""
    # player
    player_blank = None
    player0 = None
    player1 = None
    player2 = None
    player3 = None

    invincibility_charge = None

    player_variant_invincible = None
    
    # enemy
    enemy0 = None
    enemy1 = None
    enemy2 = None
    shield = None
    
    # bullet
    bullet_blank = None
    bullet0 = None
    bullet1 = None
    bullet2 = None
    bullet3 = None
    
    # effects
    effect_shoot = None
    
    # powerups
    wrench = None
    power_wrench = None
    energy = None
    
    # ui
    panel_01 = None
    panel_02 = None
    game_over = None
    icon = None
    pre_roll = None
    difficulty0 = None
    difficulty1 = None
    difficulty2 = None
    difficulty3 = None
    difficulty4 = None
    difficulty5 = None
    title = None

class Sounds:
    entity_damage = None
    player_death = None
    player_shoot = None
    player_power_gain = None
    player_health_gain = None
    fail = None
    shield_destroy = None

class Music:
    invincibility = None
    invincibility_full_draft = None

def check_assets():
    pass

def load_music(
    song: str | pathlib.Path, 
    fileHint: str = "", 
    loops: bool = False, 
    start: float = 0,
    fade: int = 0
    ):
    pygame.mixer.music.load(song, fileHint)
    if loops:
        pygame.mixer.music.play(-1, start=start, fade_ms=fade)
    else:
        pygame.mixer.music.play(0, start=start, fade_ms=fade)

def resolve_asset_path(relative_path: str | pathlib.Path) -> pathlib.Path:
    """Resolves an asset file path through the active resource pack, then vanilla."""
    try:
        from . import pack
    except ImportError:
        logger.engine_log.error("Unable to load resource pack: can't open file '<PROJECT_ROOT>/src/pack.py': [Errno 2] No such file or directory")

    return pathlib.Path(config.DATA_PATH) / "assets" / relative_path

def get_merged_manifest() -> dict:
    """Gets the active resource-pack manifest merged over the vanilla assets."""
    try:
        from . import pack
    except ImportError:
        logger.engine_log.error("Unable to load resource pack: can't open file '<PROJECT_ROOT>/src/pack.py': [Errno 2] No such file or directory")

    vanilla_base = pathlib.Path(config.DATA_PATH / "assets")
    vanilla_manifest_path = vanilla_base / "assets.json"
    with open(vanilla_manifest_path, "r") as f:
        vanilla_data = json.load(f)

    logger.engine_log.info(f"Vanilla Base set to: {vanilla_base}")
    # logger.engine_log.info(f"Vanilla Data set to: {vanilla_data}")
    logger.engine_log.info(f"Vanilla Manifest/Assets path set to: {vanilla_manifest_path}")

    return {
        "textures": dict(vanilla_data.get("textures", {})),
        "sound": dict(vanilla_data.get("audio", {}).get("sound", {})),
        "music": dict(vanilla_data.get("audio", {}).get("music", {}))
    }


def load_assets_generator():
    """
    Stream loads all game assets using the mod engine's path resolution pipeline
    (or vanilla fallback if mod.py is not present).
    """
    manifest = get_merged_manifest()
    texture_manifest = manifest["textures"]
    sound_manifest = manifest["sound"]
    music_manifest = manifest["music"]

    logger.rp_thread_log.info(f"Succesfully loaded asset manifest with {manifest}")

    total_items = len(texture_manifest) + len(sound_manifest) + len(music_manifest) + 2
    loaded_count = 0

    # 1. INITIALIZE FONT
    global pressStart2P, monocraft
    press_start_font_path = resolve_asset_path("fonts/PressStart2P-Regular.ttf")
    monocraft_font_path = resolve_asset_path("fonts/Monocraft.ttf")
    pressStart2P = pygame.font.Font(str(press_start_font_path), 30)
    monocraft = pygame.font.Font(str(monocraft_font_path), 30)
    loaded_count += 1
    yield int((loaded_count / total_items) * 100), "Initializing Fonts..."

    # 2. STREAM TEXTURES
    for target_var, entry in texture_manifest.items():
        time.sleep(random.random() / 5)
        rel_path = entry["file"] if isinstance(entry, dict) and "file" in entry else entry
        custom_scale = entry.get("scale") if isinstance(entry, dict) else None

        full_path = resolve_asset_path(rel_path)
        raw = pygame.image.load(full_path).convert_alpha()

        if custom_scale is not None:
            scaled = pygame.transform.scale_by(raw, custom_scale)
        elif target_var == "icon":
            scaled = raw
        else:
            scaled = pygame.transform.scale_by(raw, config.SPRITE_SCALING)

        setattr(Textures, target_var, scaled)
        loaded_count += 1
        # Yield percentage AND the current file/variable being loaded
        yield int((loaded_count / total_items) * 100), f"Texture: {target_var}"

    # 3. STREAM SOUNDS
    for target_var, entry in sound_manifest.items():
        time.sleep(random.random() / 5)
        rel_path = entry["file"] if isinstance(entry, dict) and "file" in entry else entry
        custom_vol = entry.get("volume") if isinstance(entry, dict) else None

        full_path = resolve_asset_path(rel_path)
        sound = pygame.mixer.Sound(full_path)

        if custom_vol is not None:
            sound.set_volume(float(custom_vol))
        elif target_var in ["player_power_gain", "fail", "shield_destroy"]:
            sound.set_volume(0.5)

        setattr(Sounds, target_var, sound)

        loaded_count += 1
        yield int((loaded_count / total_items) * 100), f"Sound: {target_var}"

    # 4. STREAM MUSIC
    for target_var, entry in music_manifest.items():
        time.sleep(random.random() / 5)
        rel_path = entry["file"] if isinstance(entry, dict) and "file" in entry else entry

        full_path = resolve_asset_path(rel_path)
        setattr(Music, target_var, str(full_path))

        loaded_count += 1
        yield int((loaded_count / total_items) * 100), f"Music: {target_var}"

    # 5. LOAD UI PANELS
    panel_01_path = resolve_asset_path("textures/ui/panel/panel_01.png")
    panel_02_path = resolve_asset_path("textures/ui/panel/panel_02.png")

    Textures.panel_01 = pygame.image.load(panel_01_path).convert_alpha()
    Textures.panel_02 = pygame.image.load(panel_02_path).convert_alpha()

    time.sleep(random.random() / 5)

    loaded_count += 1
    yield 100, "Finalizing UI Panels..."
