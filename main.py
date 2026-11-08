#!/usr/bin/env python3

# Galactic Space Reborn
# Copyright (c) Ghosted Alex 2026
# Code Made under the MIT license:
# Github: https://github.com/Ghosted-Alex/Galactic_Space_Reborn?tab=MIT-2-ov-file
# GitLab: https://gitlab.com/ghostedalex/Galactic_Space_Reborn/-/blob/main/LICENSE_MIT?ref_type=heads

# General Imports
import os

import pathlib
import random
import sys
import argparse
import time

import pygame

from src import scenes

# Source Imports
import config

from src import assets
from src import settings
from src import initialize
from src import utilities

from src import events

from src import logger

from src.asset_update import AssetUpdater

# Map string names passed via --scene / -s to Scene classes
SCENE_MAP = {
    f"{config.scene_namespace}:title": scenes.TitleScene,
    f"{config.scene_namespace}:play_menu": scenes.PlayMenuScene,
    f"{config.scene_namespace}:game_menu": scenes.GameMenuScene,
    f"{config.scene_namespace}:options": scenes.OptionsScene,
    f"{config.scene_namespace}:video_options": scenes.VideoOptionsScene,
    f"{config.scene_namespace}:audio_options": scenes.AudioOptionsScene,
    f"{config.scene_namespace}:pause_menu": scenes.PauseMenuScene,
    f"{config.scene_namespace}:resource_pack": scenes.ResourcePackMenuScene,
    f"{config.scene_namespace}:gameplay": scenes.GameplayScene,
    f"{config.scene_namespace}:tutorial": scenes.TutorialScene,
    f"{config.scene_namespace}:dialog": scenes.DialogScene,
    f"{config.scene_namespace}:dialog_test": scenes.DialogTestScene,
}

def parse_cli_args():
    parser = argparse.ArgumentParser(description="Galactic Space Reborn is a fast-paced space shooter where you blast through and dodge enemies. Collecting Power-Ups can help you throughout your runs. Fight through increasingly difficult levels and take down bosses to prove who can achieve the highest score.")
    parser.add_argument(
        "-s", "--scene",
        type=str,
        default="title",
        choices=list(SCENE_MAP.keys()),
        help="Initial scene to load on launch (default: title)"
    )

    exclusive_args = parser.add_mutually_exclusive_group()

    parser.add_argument(
        "-e", "--experimental",
        action="store_true",
        help="Enables experimental parts of the game"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enables debug symbols | Only use this flag if you are a developer and/or if you know what you are doing"
    )
    return parser.parse_args()

def main() -> any:
    """The gateway into the game"""

    # Parse arguments prior to GUI setup
    args = parse_cli_args()

    experimental = True if args.experimental else False
    debug = True if args.debug else False

    if experimental and debug:
        logger.engine_log.critical("The game can not be ran with both experimental features and debug symbols enabled, please enable one or the other\n\nmain.py: error: argument -e/--experimental: not allowed with argument --debug")
        pygame.quit()
        sys.exit(1)

    if experimental:
        logger.engine_log.warning(f"WARNING! Experimental Flag Enabled! These are features actively being tested and being iterated on, Please be sure to back up all user data.")
        config.set_version(1)

    if debug:
        logger.engine_log.warning("WARNING! Debug Symbols are enabled, the game may misbehave or crash, only use the --debug flag if you know what you are doing!")
        config.set_version(2)

    assets_path = pathlib.Path(f"{config.DATA_PATH}/assets") # or whatever your local assets directory path is
    updater = AssetUpdater(assets_dir=assets_path, debug=False)
    updater.run()

    logger.asset_thread_log.info("Up to Date!")

    # Quick Initialization
    pygame.init()

    fps_clock, scr, game_running = initialize.initialize_vars()

    initialize.initialize_files()

    controller_node = initialize.load_controller_nodes()

    player_controller = None
    if pygame.joystick.get_count() > 0:
        player_controller = config.ControllerBindings.XboxController

    # 1. Show the loading screen FIRST
    initialize.show_loading_screen(scr, 24, debug=debug)

    # 2. Initialize the scene manager
    scene_manager = initialize.initialize_scene_manager(scr)

    # 3. Resolve targeted scene class from arguments (defaults to TitleScene if invalid or unspecified)
    target_scene_class = SCENE_MAP.get(args.scene.lower(), scenes.TitleScene)

    # 4. Set the resolved scene
    scene_manager.set_scene(target_scene_class(), fade=True, fade_speed=12)

    logger.engine_log.info(f"FPS Clock: {fps_clock} | Screen Surface: {scr} | Scene Manager: {scene_manager}")

    # 5. Set Up variables
    return fps_clock, scr, game_running, scene_manager


def reload_game_window():
    """Recreate pygame's window and refill the asset cache for a new pack."""
    global SCR

    pygame.mixer.stop()
    pygame.display.quit()
    pygame.display.init()
    SCR = settings.create_display()
    pygame.display.set_caption(config.Game.title)

    initialize.show_loading_screen(SCR, 24)
    settings.apply_audio()
    if assets.Textures.icon is not None:
        pygame.display.set_icon(assets.Textures.icon)

    scene_manager.replace_screen(SCR)
    scene_manager.set_scene(scenes.TitleScene(), fade=False)

running = False

if __name__ == "__main__":
    try:
        FPS, SCR, running, scene_manager = main()
    except Exception as e:
        events.on_crash(e=e)

while running:
    dt = FPS.tick(60) / 1000.0  # Framerate clock tick

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            initialize.unload_controller_nodes()
            running = False
            pygame.quit()
        scene_manager.handle_event(event)

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == config.ControllerBindings.XboxController.BUTTON_A:
                # print("[Input] Action: Jump / Select")
                pass

    move_x, move_y = config.ControllerBindings.get_move_vector(deadzone=0.15)
    if move_x != 0 or move_y != 0:
        # print("[Input] Action: Move")
        pass

    if scene_manager.consume_window_reload_request():
        reload_game_window()

    scene_manager.update(dt)
    scene_manager.draw(SCR)

    pygame.display.flip()
