"""Initialization Module"""
import pathlib
import sys
from typing import Any

import pygame
from pygame import Clock, Surface
from pygame.joystick import JoystickType

from . import assets
import config
from . import settings

from . import logger

from .scenes import SceneManager, fade_screen

from src.pack import load_resources, verify_manifest

def show_loading_screen(screen, fade_speed):
    """Load all assets with a visual loading screen, displaying the splash screen when progress reaches halfway."""

    if not verify_manifest():
        logger.rp_thread_log.error("Aborting asset streaming sequence due to manifest file verification errors.")
        pygame.quit()
        sys.exit(1)

    # Pre-resolve pre-roll splash texture configuration
    manifest = assets.get_merged_manifest()
    pre_roll_cfg = manifest.get("textures", {}).get("pre_roll", "textures/ui/preRoll.png")
    if isinstance(pre_roll_cfg, dict):
        rel_path = pre_roll_cfg.get("file", "textures/ui/preRoll.png")
        scale = pre_roll_cfg.get("scale", config.SPRITE_SCALING)
    else:
        rel_path = pre_roll_cfg
        scale = config.SPRITE_SCALING

    pre_roll_path = assets.resolve_asset_path(rel_path)
    pre_roll_img = None
    if pre_roll_path.is_file():
        try:
            raw_pre_roll = pygame.image.load(str(pre_roll_path)).convert_alpha()
            pre_roll_img = pygame.transform.scale_by(raw_pre_roll, scale)
        except Exception as err:
            logger.rp_thread_log.error(f"Error loading pre-roll graphic: {err}")

    # 1. Start asset loading generator
    loader = assets.load_assets_generator()
    screen_rect = screen.get_rect()

    # Fade-in state for the pre-roll splash
    pre_roll_alpha = 0          # current alpha (0=transparent, 255=opaque)

    # 2. Progress loop
    for progress, current_file_text in loader:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

        screen.fill((0, 0, 0))

        bar_width = 400
        bar_height = 20
        bar_x = screen_rect.centerx - (bar_width // 2)
        bar_y = screen_rect.centery + 100
        progress_bar_width = (progress / 100) * bar_width

        if progress >= 25 and pre_roll_img is not None:
            pre_roll_alpha = min(255, pre_roll_alpha + fade_speed)
            pre_roll_img.set_alpha(pre_roll_alpha)
            pre_roll_rect = pre_roll_img.get_rect(center=(screen_rect.centerx, bar_y - 150))
            screen.blit(pre_roll_img, pre_roll_rect)

        # Draw progress bar outlines and fill
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, progress_bar_width, bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (bar_x - 4, bar_y - 4, bar_width + 8, bar_height + 8), 1)

        # Draw progress, title, and current file text
        if hasattr(assets, 'pressStart2P') and assets.pressStart2P is not None:
            title = assets.pressStart2P.render("Loading Game...", True, (255, 255, 255))
            status = assets.pressStart2P.render(f"({progress}%)", True, (255, 255, 255))

            # Create a smaller font or render the current file string (you can scale it down if 30pt is too big)
            file_surf = assets.pressStart2P.render(current_file_text, True, (180, 180, 180))
            # Optional: Scale down file text so it doesn't overflow the screen width
            file_surf = pygame.transform.smoothscale(file_surf, (int(file_surf.get_width() * 0.5),
                                                                 int(file_surf.get_height() * 0.5)))

            title_rect = title.get_rect(center=(screen_rect.centerx, bar_y - 30))
            status_rect = status.get_rect(center=(screen_rect.centerx, bar_y + 45))
            file_rect = file_surf.get_rect(center=(screen_rect.centerx, bar_y + 80))

            screen.blit(title, title_rect)
            screen.blit(status, status_rect)
            screen.blit(file_surf, file_rect)

        pygame.display.flip()

    # Fade out loading screen to black before entering title screen
    fade_screen(screen, mode="out", speed=15)

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