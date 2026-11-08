"""Initialization Module"""
import pathlib
import sys
from typing import Any

import json

import pygame
from pygame import Clock, Surface
from pygame.joystick import JoystickType

from . import assets
import config
from . import settings

from . import logger

from .scenes import SceneManager, fade_screen

from src.pack import load_resources, verify_manifest

# Modular keyframe triggers based on loader progress percentage (0 - 100)
SPLASH_KEYFRAMES = {
    "preroll_fade_in_trigger": 0,    # Percentage threshold to trigger pre-roll fade-in (e.g., 0%, 15%, 25%)
    "fade_in_speed": 12,              # Alpha increase per frame
    "preroll_target_alpha": 255,     # Target opacity once triggered
}

# --- MODULAR CONFIGURATION FOR PRE-ROLL TRIGGERS ---
SPLASH_CONFIG = {
    # Percentage (0-100) at which the pre-roll splash starts fading in
    "trigger_pct": 15,  
    # Alpha increment per frame during fade-in
    "fade_speed": 12,   
}

def load_splash_texture() -> tuple[pygame.Surface | None, int]:
    """
    Attempts to pre-read assets.json to get the pre_roll file and scale configuration,
    loading and scaling the image before full manifest streaming begins.
    """
    assets_dir = pathlib.Path(config.DATA_PATH) / "assets"
    manifest_path = assets_dir / "assets.json"

    splash_file = "textures/ui/preRoll.png"
    splash_scale = 8  # Default scale fallback from assets.json definition

    # Pre-parse assets.json for the pre_roll entry if available
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
                pre_roll_entry = data.get("textures", {}).get("pre_roll")
                if isinstance(pre_roll_entry, dict):
                    splash_file = pre_roll_entry.get("file", splash_file)
                    splash_scale = pre_roll_entry.get("scale", splash_scale)
                elif isinstance(pre_roll_entry, str):
                    splash_file = pre_roll_entry
        except Exception as e:
            logger.engine_log.warning(f"Could not parse pre_roll scale from assets.json: {e}")

    # Load and scale texture
    splash_path = assets_dir / splash_file
    if splash_path.exists():
        try:
            raw_splash = pygame.image.load(splash_path).convert_alpha()
            scaled_splash = pygame.transform.scale_by(raw_splash, splash_scale)
            return scaled_splash, splash_scale
        except Exception as e:
            logger.engine_log.warning(f"Could not load pre_roll splash image: {e}")

    return None, splash_scale

def draw_loading_ui(
    surface: pygame.Surface,
    progress_pct: int,
    status_msg: str,
    splash_img: pygame.Surface = None,
    splash_alpha: int = 0
):
    """Renders the dark background, splash graphic with dynamic alpha, lowered loading bar, and status text."""
    scr_width, scr_height = surface.get_size()

    # 1. Base Background
    surface.fill((15, 15, 22))

    # 2. Render Scaled Splash Image with Alpha (No copy() allocation for better performance)
    if splash_img and splash_alpha > 0:
        splash_img.set_alpha(splash_alpha)
        splash_rect = splash_img.get_rect(center=(scr_width // 2, scr_height // 2 - 20))
        surface.blit(splash_img, splash_rect)

    # 3. Status Message Text
    if hasattr(assets, 'monocraft') and assets.monocraft:
        font = assets.monocraft
    else:
        font = pygame.font.Font(None, 24)

    status_surf = font.render(status_msg, True, (200, 200, 220))
    status_rect = status_surf.get_rect(center=(scr_width // 2, scr_height - 55))
    surface.blit(status_surf, status_rect)

    # 4. Progress Bar Geometry
    bar_width = int(scr_width * 0.65)
    bar_height = 35
    bar_x = (scr_width - bar_width) // 2
    bar_y = scr_height // 2 + 100

    border_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)

    clamped_pct = max(0, min(100, progress_pct))
    fill_width = int((bar_width - 6) * (clamped_pct / 100.0))
    fill_rect = pygame.Rect(bar_x + 3, bar_y + 3, fill_width, bar_height - 6)

    # 5. Render Progress Fill & Border
    pygame.draw.rect(surface, (40, 45, 60), border_rect, border_radius=6)
    if fill_width > 0:
        pygame.draw.rect(surface, (80, 160, 240), fill_rect, border_radius=4)
    pygame.draw.rect(surface, (100, 110, 140), border_rect, 2, border_radius=6)

    # 6. Percentage Text
    pct_surf = font.render(f"{clamped_pct}%", True, (255, 255, 255))
    pct_rect = pct_surf.get_rect(center=(scr_width // 2, bar_y + bar_height // 2 + 2.5))
    surface.blit(pct_surf, pct_rect)

def show_loading_screen(
    surface: pygame.Surface,
    fps: int = 60,
    debug: bool = False,
    trigger_pct: int = SPLASH_CONFIG["trigger_pct"]
):
    """
    Displays the splash screen and loading bar, triggering splash reveal at `trigger_pct`.
    """
    clock = pygame.time.Clock()

    # 1. Pre-load splash texture and dynamic scale factor
    splash_img, scale = load_splash_texture()

    # 2. Instantiate generator
    loader = assets.load_assets_generator(debug=debug)

    progress_pct = 0
    status_msg = "Initializing engine..."
    loading = True
    splash_alpha = 0

    # 3. Main Boot & Stream Loop
    while loading:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

        try:
            progress_pct, status_msg = next(loader)

            # Hot-reload pre_roll if downloaded during fresh install sync
            if splash_img is None:
                splash_img, _ = load_splash_texture()

        except StopIteration:
            loading = False
            progress_pct = 100
            status_msg = "Loading Complete! Starting Game..."

        # Modular Trigger Check: Only advance alpha if loading percentage >= trigger_pct
        if progress_pct >= trigger_pct and splash_alpha < 255:
            splash_alpha = min(255, splash_alpha + SPLASH_CONFIG["fade_speed"])

        # Draw frame
        draw_loading_ui(
            surface,
            progress_pct,
            status_msg,
            splash_img=splash_img,
            splash_alpha=splash_alpha
        )
        pygame.display.flip()
        clock.tick(fps)

    # 4. Fade-Out to Black Sequence
    fade_overlay = pygame.Surface(surface.get_size()).convert()
    fade_overlay.fill((0, 0, 0))

    for alpha in range(0, 256, 15):
        fade_overlay.set_alpha(alpha)
        draw_loading_ui(surface, 100, "Loading Complete! Starting Game...", splash_img=splash_img, splash_alpha=splash_alpha)
        surface.blit(fade_overlay, (0, 0))
        pygame.display.flip()
        clock.tick(fps)

def initialize_files() -> None:
    files_created = []
    """Check for files and if files don't exist they will be created automatically"""
    pass
    
    logger.engine_log.info("All Files Initialized.")
    logger.engine_log.info(f"Files Created: {files_created}") if len(files_created) != 0 else ...

def initialize_vars() -> Any:
    """Usage: <vars_to_initialize> = initialize.initialize_vars()\n
    Commonly used when edited to initialize global variables"""

    fps_clock = pygame.time.Clock()
    settings.load()
    screen = settings.create_display()

    pygame.display.set_caption(config.Game.title)

    # Restore the player's resource-pack choice before resolving any assets.
    load_resources()
    settings.apply_audio()

    if assets.Textures.icon is not None:
        pygame.display.set_icon(assets.Textures.icon)
    else:
        vanilla_icon_path = pathlib.Path(config.DATA_PATH) / "assets" / "textures" / "ui" / "icon.png"
        if vanilla_icon_path.is_file():
            fallback_surface = pygame.image.load(str(vanilla_icon_path)).convert_alpha()
            pygame.display.set_icon(fallback_surface)
            logger.engine_log.warning("Game icon undefined. Safely loaded vanilla fallback display icon.")
    
    run = True

    return fps_clock, screen, run

def initialize_scene_manager(screen: pygame.Surface) -> SceneManager:
    scene_manager = SceneManager(screen)

    return scene_manager

def load_controller_nodes() -> list[JoystickType]:
    """Load controller nodes into global variables"""
    pygame.joystick.init()

    controller_nodes = [
        pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
    ]
    for node in controller_nodes:
        logger.engine_log.info(f"Initialized Controller Nodes: {node.get_name()}")

    return controller_nodes

def unload_controller_nodes() -> Any:
    """Unload controller nodes out of global variables"""
    pygame.joystick.quit()