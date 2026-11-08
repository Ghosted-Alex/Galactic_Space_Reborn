"""Tutorial Screen / Scene for Galactic Space Reborn.

Provides an interactive, keyframe-driven flight tutorial based on gameplay.py.
Features:
- Pre-defined entity and player positions per keyframe/step.
- Freezes gameplay state whenever a dialog is on-screen (referencing dialog.py).
- Modular keyframe system allowing easy addition, removal, and reordering of steps.
- Automatic transition back to GameMenuScene (src/scenes/game_menu.py) upon completion.
- Pause and exit confirmation modal returning to GameMenuScene.
"""

from __future__ import annotations

import math
import sys
from typing import Any, Callable

import pygame

import config
from src import assets
from src import bullet
from src import clock
from src import controls
from src import entity
from src import events
from src import logger
from src import powerup
from src import starfield
from src import stats
from src import states
from src import ui
from src import update as update_mod
from src.controls import ControllerInput
from .base import BaseScene
from .dialog import (
    ConfirmationDialog,
    DialogScene,
    BottomDialog,
    BottomBannerDialog,
    get_dialog_font,
    show_confirmation,
    show_dialog,
    show_bottom_dialog,
)


class TutorialKeyframe:
    """Represents a discrete stage/step within the flight training tutorial.

    Each keyframe can define:
    - Pre-defined player position
    - Pre-defined enemy positions and behavior (stationary or mobile)
    - Pre-defined powerup positions
    - Dialog briefing/instructions shown on activation (which freezes gameplay)
    - Objective condition required to complete the keyframe
    """

    def __init__(
        self,
        id: str,
        title: str = "",
        message: str | list[str] = "",
        objective_text: str = "",
        player_pos: tuple[int, int] | None = None,
        enemies: list[dict[str, Any]] | None = None,
        powerups: list[dict[str, Any]] | None = None,
        clear_enemies_on_enter: bool = True,
        clear_powerups_on_enter: bool = True,
        clear_bullets_on_enter: bool = True,
        condition: str | Callable[[dict[str, Any], TutorialScene], bool] = "dialog_closed",
        condition_target: int | float = 1,
        dialog_actions: list[tuple[str, Callable] | dict] | None = None,
        dialog_kwargs: dict[str, Any] | None = None,
        on_enter: Callable[[dict[str, Any], TutorialScene], None] | None = None,
        on_complete: Callable[[dict[str, Any], TutorialScene], None] | None = None,
        auto_advance_delay: float = 0.4,
        allow_random_enemies: bool = False,
        allow_random_powerups: bool = False,
        speaker: str | None = None,
        dialog_type: str = "bottom",
        dialog_class: type | None = None,
    ):
        """Initializes a new Tutorial Keyframe.

        Args:
            id: Unique identifier for this step.
            title: Header title for dialog and top HUD banner.
            message: Dialog message text explaining instructions to the player.
            objective_text: Short text displayed in the in-game HUD banner during play.
            player_pos: (x, y) coordinates to place the player ship.
            enemies: List of enemy specification dicts:
                    e.g. [{"x": 800, "y": 400, "type": 0, "shield": False, "stationary": True}]
            powerups: List of powerup specification dicts:
                    e.g. [{"x": 750, "y": 400, "type": 0, "stationary": True}]
            clear_enemies_on_enter: If True, purges existing enemies before starting this step.
            clear_powerups_on_enter: If True, purges existing powerups before starting this step.
            clear_bullets_on_enter: If True, purges existing bullets before starting this step.
            condition: Completion condition type:
                        - "dialog_closed": completes when dialog is dismissed
                        - "move": player must move condition_target pixels
                        - "shoot": player must fire condition_target shots
                        - "enemies_cleared": all enemies spawned in this step are destroyed
                        - "powerups_cleared": all powerups spawned in this step are collected
                        - "timer": wait condition_target seconds of unpaused play
                        - callable: fn(state, scene) -> bool
            condition_target: Quantitative goal for "move", "shoot", or "timer".
            dialog_actions: Optional custom buttons for the dialog. Defaults to [("CONTINUE", ...)].
            dialog_kwargs: Additional parameters passed to DialogScene.
            on_enter: Hook executed when entering this keyframe.
            on_complete: Hook executed when this keyframe's objective is completed.
            auto_advance_delay: Seconds to delay after condition is satisfied before advancing.
            allow_random_enemies: If True, allows random background enemy spawning.
            allow_random_powerups: If True, allows random background powerup drops.
        """
        self.id = id
        self.title = title
        self.message = message
        self.objective_text = objective_text or title
        self.player_pos = player_pos
        self.enemies = enemies or []
        self.powerups = powerups or []
        self.clear_enemies_on_enter = clear_enemies_on_enter
        self.clear_powerups_on_enter = clear_powerups_on_enter
        self.clear_bullets_on_enter = clear_bullets_on_enter
        self.condition = condition
        self.condition_target = condition_target
        self.dialog_actions = dialog_actions
        self.dialog_kwargs = dialog_kwargs or {}
        self.on_enter = on_enter
        self.on_complete = on_complete
        self.auto_advance_delay = auto_advance_delay
        self.allow_random_enemies = allow_random_enemies
        self.allow_random_powerups = allow_random_powerups
        self.speaker = speaker
        self.dialog_type = dialog_type
        self.dialog_class = dialog_class

    def check_condition(self, state: dict[str, Any], scene: TutorialScene) -> bool:
        """Evaluates whether the keyframe's completion criteria are satisfied."""
        if callable(self.condition):
            try:
                return bool(self.condition(state, scene))
            except Exception as err:
                logger.engine_log.error(f"[Tutorial] Error checking keyframe callable condition: {err}")
                return False

        if self.condition == "dialog_closed":
            return state.get("dialog_dismissed_for_step", False)

        if self.condition == "move":
            return state.get("step_move_distance", 0.0) >= self.condition_target

        if self.condition == "shoot":
            return state.get("step_shots_fired", 0) >= self.condition_target

        if self.condition == "enemies_cleared":
            # Condition met once all enemies are destroyed (and spawn has completed)
            has_spawned = state.get("step_enemies_spawned", False)
            return has_spawned and len(state.get("enemies", [])) == 0

        if self.condition == "powerups_cleared":
            has_spawned = state.get("step_powerups_spawned", False)
            return has_spawned and len(state.get("powerups", [])) == 0

        if self.condition == "timer":
            return state.get("step_active_time", 0.0) >= self.condition_target

        return False


def get_default_keyframes() -> list[TutorialKeyframe]:
    """Generates the standard modular sequence of tutorial keyframes.

    Users can inspect or extend this sequence to add more tutorial steps.
    """
    screen_h = getattr(getattr(config, "Screen", None), "Size", None)
    mid_y = (config.Screen.Size.h // 2 - 20) if screen_h else 400

    return [
        # --- 1. WELCOME & OVERVIEW ---
        TutorialKeyframe(
            id="welcome",
            title="FLIGHT ACADEMY: BRIEFING",
            message=(
                "Welcome to the Pilot Training Academy, Cadet!\n\n"
                "This flight simulation will guide you through starship navigation, "
                "blaster weapons targeting, enemy shielding mechanics, and deep space salvage.\n\n"
                "Press Z/SPACE/ENTER or (A) to begin your basic flight certification."
            ),
            objective_text="Review the initial flight briefing.",
            player_pos=(180, mid_y),
            condition="dialog_closed",
            dialog_actions=[("BEGIN", None)],
        ),
        # --- 2. BASIC PROPULSION & MANEUVERING ---
        TutorialKeyframe(
            id="movement",
            title="PROPULSION & MANEUVERING",
            message=(
                "First, let's test your sub-light engines.\n\n"
                "- Keyboard: Use W/A/S/D or ARROW KEYS to steer your starship.\n"
                "- Controller: Use the Left Analog Stick or D-Pad.\n\n"
                "Maneuver your ship around the sector to calibrate thrusters."
            ),
            objective_text="Calibrate thrusters: Maneuver your ship around the sector.",
            player_pos=(180, mid_y),
            condition="move",
            condition_target=220.0,
            dialog_actions=[("CONTINUE", None)],
        ),
        # --- 3. WEAPONS CALIBRATION ---
        TutorialKeyframe(
            id="weapons",
            title="WEAPONS CALIBRATION",
            message=(
                "Thrusters calibrated. Now let's test your primary blaster cannons.\n\n"
                "- Keyboard: Press SPACEBAR to fire.\n"
                "- Controller: Press (A) button or Right Bumper (RB).\n\n"
                "Blaster fire draws power from your energy capacitor, "
                "which automatically recharges over time.\n\n"
                "Fire 3 blaster bolts to calibrate targeting computers."
            ),
            objective_text="Weapons test: Fire your plasma blasters (3 times).",
            player_pos=(180, mid_y),
            condition="shoot",
            condition_target=3,
            dialog_actions=[("CONTINUE", None)],
        ),
        # --- 4. TARGET PRACTICE ---
        TutorialKeyframe(
            id="target_practice",
            title="TARGET ACQUISITION",
            message=(
                "Sensors detect a stationary target drone in forward sector!\n\n"
                "Align your starship vertically with the hostile drone and open fire.\n\n"
                "Destroy the target drone to proceed."
            ),
            objective_text="Target practice: Align and destroy the training drone.",
            player_pos=(180, mid_y),
            enemies=[
                {
                    "x": 820,
                    "y": mid_y,
                    "type": 0,
                    "shield": False,
                    "stationary": True,
                }
            ],
            condition="enemies_cleared",
            dialog_actions=[("CONTINUE", None)],
        ),
        # --- 5. SHIELDED TARGET ENGAGEMENT ---
        TutorialKeyframe(
            id="shielded_enemy",
            title="DEFENSIVE SHIELDING",
            message=(
                "Warning: Some hostile starships are protected by forward kinetic shields!\n\n"
                "Shielded hostiles absorb initial impacts. You must score multiple consecutive "
                "hits to shatter the forward barrier before your bolts can pierce their hull.\n\n"
                "Break the shield and destroy the target drone."
            ),
            objective_text="Shield combat: Break the enemy shield and destroy the drone.",
            player_pos=(180, mid_y),
            enemies=[
                {
                    "x": 820,
                    "y": mid_y,
                    "type": 2,
                    "shield": True,
                    "stationary": True,
                }
            ],
            condition="enemies_cleared",
            dialog_actions=[("CONTINUE", None)],
        ),
        # --- 6. FIELD SALVAGE & POWERUPS ---
        TutorialKeyframe(
            id="powerups",
            title="FIELD REPAIRS & POWERUPS",
            message=(
                "During deep space combat, salvage drops will appear:\n\n"
                "- Green Wrench: Restores hull integrity.\n"
                "- Energy Cell: Recharges blaster capacitors.\n"
                "- Golden Wrench: Grants temporary invincibility!\n\n"
                "Fly into the wrench ahead to collect it."
            ),
            objective_text="Field salvage: Fly into the wrench to collect it.",
            player_pos=(180, mid_y),
            powerups=[
                {
                    "x": 720,
                    "y": mid_y,
                    "type": 0,
                    "stationary": True,
                }
            ],
            condition="powerups_cleared",
            dialog_actions=[("CONTINUE", None)],
        ),
        # --- 7. GRADUATION & COMPLETION ---
        TutorialKeyframe(
            id="completion",
            title="FLIGHT CERTIFICATION COMPLETE",
            message=(
                "Outstanding flight performance, Cadet!\n\n"
                "You have demonstrated full proficiency in sub-light navigation, "
                "plasma weapons fire, shield breaking, and supply salvage.\n\n"
                "You are now officially certified for combat deployment.\n"
                "Returning to Sector Command!"
            ),
            objective_text="Flight training complete! Returning to Game Menu...",
            player_pos=(180, mid_y),
            condition="dialog_closed",
            dialog_actions=[("RETURN", None)],
        ),
    ]


# Module-level state dictionary for tutorial gameplay
_state: dict[str, Any] = {
    "loaded": False,
    "player": None,
    "stars_bg": None,
    "enemies": [],
    "bullets": [],
    "powerups": [],
    "effects": [],
    "manager": None,
    # Keyframe & freeze system state
    "keyframes": [],
    "current_index": 0,
    "active_dialog": None,
    "is_frozen": False,
    "tutorial_finished": False,
    # Step progress tracking
    "dialog_dismissed_for_step": False,
    "step_move_distance": 0.0,
    "step_last_player_pos": None,
    "step_shots_fired": 0,
    "step_enemies_spawned": False,
    "step_powerups_spawned": False,
    "step_active_time": 0.0,
    "step_delay_timer": 0.0,
    "step_condition_satisfied": False,
}


def is_frozen() -> bool:
    """Returns True if gameplay is frozen because a dialog is on screen."""
    return bool(_state["is_frozen"] or _state["active_dialog"] is not None)


def add_keyframe(keyframe: TutorialKeyframe):
    """Appends a new keyframe to the tutorial sequence."""
    _state["keyframes"].append(keyframe)


def set_keyframes(keyframes: list[TutorialKeyframe]):
    """Replaces the active tutorial keyframes list."""
    _state["keyframes"] = list(keyframes)


def get_keyframes() -> list[TutorialKeyframe]:
    """Returns the current list of tutorial keyframes."""
    return _state["keyframes"]


def _apply_predefined_positions(keyframe: TutorialKeyframe):
    """Sets player, enemy, and powerup positions according to the keyframe."""
    player = _state["player"]

    # 1. Pre-defined player position
    if player and keyframe.player_pos is not None:
        target_x, target_y = keyframe.player_pos
        player.rect.topleft = (target_x, target_y)
        player.x, player.y = target_x, target_y
        player.hitbox.center = player.rect.center

    # 2. Clear lists if requested
    if keyframe.clear_enemies_on_enter:
        _state["enemies"].clear()
    if keyframe.clear_powerups_on_enter:
        _state["powerups"].clear()
    if keyframe.clear_bullets_on_enter:
        _state["bullets"].clear()

    # 3. Pre-defined enemy positions
    for enemy_def in keyframe.enemies:
        ex = enemy_def.get("x", 800)
        ey = enemy_def.get("y", 400)
        etype = enemy_def.get("type", 0)
        shield = enemy_def.get("shield", False)
        stationary = enemy_def.get("stationary", False)

        en = entity.Enemy(ex, ey, etype, shield=shield)
        en.x, en.y = ex, ey
        en.rect.topleft = (ex, ey)
        if hasattr(en, "hitbox"):
            en.hitbox.center = en.rect.center

        if stationary:
            en.speed = 0
            en.move = lambda: None  # Lock in place for target training
        elif "speed" in enemy_def and enemy_def["speed"] is not None:
            en.speed = enemy_def["speed"]

        _state["enemies"].append(en)

    _state["step_enemies_spawned"] = len(_state["enemies"]) > 0

    # 4. Pre-defined powerup positions
    for p_def in keyframe.powerups:
        px = p_def.get("x", 700)
        py = p_def.get("y", 400)
        ptype = p_def.get("type", 0)
        stationary = p_def.get("stationary", False)

        p_obj = powerup.Spawn(px, py, ptype)
        p_obj.x, p_obj.y = px, py
        p_obj.rect.topleft = (px, py)

        if stationary:
            p_obj.speed = 0
            p_obj.move = lambda: None  # Lock in place for collection training
        elif "speed" in p_def and p_def["speed"] is not None:
            p_obj.speed = p_def["speed"]

        _state["powerups"].append(p_obj)

    _state["step_powerups_spawned"] = len(_state["powerups"]) > 0


def _show_keyframe_dialog(keyframe: TutorialKeyframe, manager=None):
    """Displays the keyframe's dialog and activates the gameplay freeze."""
    mgr = manager or _state.get("manager")

    if not keyframe.message and not keyframe.title:
        # No dialog for this step, unfreeze immediately
        _state["active_dialog"] = None
        _state["is_frozen"] = False
        _state["dialog_dismissed_for_step"] = True
        return

    dismissed = False

    def on_dialog_dismissed():
        nonlocal dismissed
        if dismissed:
            return
        dismissed = True

        # Unfreeze gameplay as soon as the dialog closes
        _state["active_dialog"] = None
        _state["is_frozen"] = False
        _state["dialog_dismissed_for_step"] = True

        # If step completes solely upon closing dialog, check condition immediately
        if keyframe.condition == "dialog_closed":
            _check_keyframe_progression(manager=mgr, force_advance=True)

    # Wrap actions so dismissal cleans up dialog state and unfreezes
    raw_actions = keyframe.dialog_actions or [("CONTINUE", None)]
    wrapped_actions = []
    for act in raw_actions:
        if isinstance(act, tuple):
            label = act[0]
            cb = act[1] if len(act) > 1 else None

            def make_cb(original_cb):
                def action_callback():
                    if callable(original_cb):
                        original_cb()
                    on_dialog_dismissed()
                return action_callback

            wrapped_actions.append((label, make_cb(cb)))
        elif isinstance(act, dict):
            orig_cb = act.get("callback")
            act_copy = dict(act)

            def make_dict_cb(original_cb):
                def action_callback():
                    if callable(original_cb):
                        original_cb()
                    on_dialog_dismissed()
                return action_callback

            act_copy["callback"] = make_dict_cb(orig_cb)
            wrapped_actions.append(act_copy)
        else:
            wrapped_actions.append((str(act), on_dialog_dismissed))

    # Instantiate dialog (supports Modal or Bottom Dialog, default: BottomDialog 1/3 screen)
    dialog_cls = getattr(keyframe, "dialog_class", None)
    if dialog_cls is None:
        dialog_cls = DialogScene if getattr(keyframe, "dialog_type", "bottom") == "modal" else BottomDialog

    # Configure kwargs with default 1/3 height_ratio and speaker for bottom dialogs
    dialog_kwargs = dict(keyframe.dialog_kwargs)
    if issubclass(dialog_cls, BottomDialog):
        if "height_ratio" not in dialog_kwargs and "height" not in dialog_kwargs:
            dialog_kwargs["height_ratio"] = 1.0 / 3.0
        if "speaker" not in dialog_kwargs and getattr(keyframe, "speaker", None):
            dialog_kwargs["speaker"] = keyframe.speaker

    dialog = dialog_cls(
        title=keyframe.title,
        message=keyframe.message,
        actions=wrapped_actions,
        on_cancel=on_dialog_dismissed,
        close_on_escape=False,
        dim_background=True,
        tag=f"tutorial_step_{keyframe.id}",
        **dialog_kwargs,
    )

    # Ensure any dialog dismissal (via close, unload, overlay close) invokes on_dialog_dismissed
    orig_unload = dialog.unload

    def wrapped_unload():
        orig_unload()
        on_dialog_dismissed()

    dialog.unload = wrapped_unload

    _state["active_dialog"] = dialog
    _state["is_frozen"] = True

    if mgr:
        mgr.show_overlay(dialog)
    else:
        dialog.load()


def _start_keyframe(index: int, manager=None):
    """Activates the keyframe at the specified index."""
    keyframes = _state["keyframes"]
    if not (0 <= index < len(keyframes)):
        # Reached the end of tutorial
        finish_tutorial(manager)
        return

    _state["current_index"] = index
    keyframe = keyframes[index]

    # Reset per-step tracking counters
    _state["dialog_dismissed_for_step"] = False
    _state["step_move_distance"] = 0.0
    player = _state["player"]
    if player:
        _state["step_last_player_pos"] = (player.rect.x, player.rect.y)
    _state["step_shots_fired"] = 0
    _state["step_active_time"] = 0.0
    _state["step_delay_timer"] = 0.0
    _state["step_condition_satisfied"] = False

    # Apply pre-defined positions and entities
    _apply_predefined_positions(keyframe)

    # Optional on_enter hook
    if callable(keyframe.on_enter):
        try:
            keyframe.on_enter(_state, None)
        except Exception as err:
            logger.engine_log.error(f"[Tutorial] Error in keyframe on_enter hook: {err}")

    # Show dialog and freeze gameplay
    _show_keyframe_dialog(keyframe, manager=manager)


def _check_keyframe_progression(manager=None, force_advance: bool = False):
    """Tests if the active keyframe is satisfied and advances when ready."""
    keyframes = _state["keyframes"]
    idx = _state["current_index"]
    if not (0 <= idx < len(keyframes)):
        return

    keyframe = keyframes[idx]

    if not force_advance and not _state["step_condition_satisfied"]:
        if keyframe.check_condition(_state, None):
            _state["step_condition_satisfied"] = True
            _state["step_delay_timer"] = keyframe.auto_advance_delay
            if callable(keyframe.on_complete):
                try:
                    keyframe.on_complete(_state, None)
                except Exception as err:
                    logger.engine_log.error(f"[Tutorial] Error in keyframe on_complete hook: {err}")

    if force_advance or (_state["step_condition_satisfied"] and _state["step_delay_timer"] <= 0):
        next_idx = idx + 1
        if next_idx < len(keyframes):
            _start_keyframe(next_idx, manager=manager)
        else:
            finish_tutorial(manager=manager)


def finish_tutorial(manager=None):
    """Completes the tutorial and transitions back to GameMenuScene."""
    _state["tutorial_finished"] = True
    mgr = manager or _state.get("manager")
    if mgr:
        from .game_menu import GameMenuScene
        mgr.set_scene(GameMenuScene(), fade=True)
    else:
        logger.engine_log.info("[Tutorial] Tutorial completed! Returning to GameMenuScene.")


def show_exit_prompt(manager=None):
    """Shows an overlay bottom confirmation dialog asking if the player wants to return to the game menu."""
    mgr = manager or _state.get("manager")
    if not mgr:
        return

    def on_confirm_exit():
        finish_tutorial(mgr)

    show_bottom_dialog(
        manager=mgr,
        title="ABORT FLIGHT TRAINING",
        message="Are you sure you want to exit flight training and return to the main menu?",
        actions=[
            ("CONFIRM", on_confirm_exit),
            ("DENY", None),
        ],
        height_ratio=1.0 / 3.0,
    )


def load(*args, keyframes: list[TutorialKeyframe] | None = None, manager=None, **kwargs):
    """Dedicated scene load function. Initializes player, stars, entities, and keyframes."""
    _state["loaded"] = True
    _state["manager"] = manager
    _state["tutorial_finished"] = False

    # Reset game state flags
    states.game_over = False
    states.game_over_ui_shown = False
    states.blink_timer = 60
    states.health_blink_timer = 60
    states.powerup_timer = 0
    states.powerup_active = False
    stats.score = 0

    # Initialize Player & Stars background
    _state["player"] = entity.Player(150, config.Screen.Size.h // 2 - 20)
    player_rect = _state["player"].texture.get_rect(
        center=(config.Screen.Size.w // 2, config.Screen.Size.h // 2)
    )
    _state["player"].x, _state["player"].y = player_rect.topleft

    _state["stars_bg"] = starfield.Generate(config.Screen.Size.w, config.Screen.Size.h)

    _state["enemies"].clear()
    _state["bullets"].clear()
    _state["powerups"].clear()
    _state["effects"].clear()

    # Load keyframes (custom or default)
    if keyframes is not None:
        _state["keyframes"] = list(keyframes)
    else:
        _state["keyframes"] = get_default_keyframes()

    # Start first keyframe
    _start_keyframe(0, manager=manager)


def unload():
    """Dedicated scene unload function. Cleans up entities and dialog overlays."""
    _state["loaded"] = False
    _state["player"] = None
    _state["stars_bg"] = None
    _state["enemies"].clear()
    _state["bullets"].clear()
    _state["powerups"].clear()
    _state["effects"].clear()
    _state["active_dialog"] = None
    _state["is_frozen"] = False
    _state["keyframes"].clear()


def handle_event(event: pygame.event.Event, manager=None):
    """Dedicated event handler for the tutorial scene."""
    if manager and not _state.get("manager"):
        _state["manager"] = manager

    mgr = manager or _state.get("manager")

    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit(0)

    # If dialog is active in standalone mode (no manager overlay), forward events to it
    if _state["active_dialog"] and (mgr is None or getattr(mgr, "overlay_scene", None) is not _state["active_dialog"]):
        _state["active_dialog"].handle_event(event)
        return

    # If game is frozen because an overlay is showing, skip gameplay inputs
    if is_frozen():
        return

    player = _state["player"]

    if event.type == pygame.KEYDOWN:
        # ESC: Ask to return to Game Menu
        if event.key == config.KeyBinds.General.escape and mgr:
            show_exit_prompt(mgr)
            return

        # Shoot primary weapon
        if controls.single_press(event=event, key=config.KeyBinds.Gameplay.shoot):
            if player:
                fired = events.on_shoot(player, _state["effects"], _state["bullets"])
                if fired:
                    _state["step_shots_fired"] += 1

    # Controller: Pause / Hamburger -> Exit prompt
    if ControllerInput.pause(event) and mgr:
        show_exit_prompt(mgr)
        return

    # Controller: Shoot (A button or RB)
    if ControllerInput.shoot(event):
        if player:
            fired = events.on_shoot(player, _state["effects"], _state["bullets"])
            if fired:
                _state["step_shots_fired"] += 1

    # Controller: D-Pad discrete movement
    if player and event.type == pygame.JOYHATMOTION:
        keys = pygame.key.get_pressed()
        player.handle_input(keys, event=event)


def update(dt: float = 1.0):
    """Dedicated update function. Freezes when a dialog is on screen."""
    if not _state["loaded"] or _state["tutorial_finished"]:
        return

    # FREEZE CHECK: The freeze happens whenever a dialog is on screen!
    if is_frozen():
        if _state["active_dialog"]:
            _state["active_dialog"].update(dt)
        return

    update_mod.update_time()
    player = _state["player"]

    if states.blink_timer < config.blink_timer_max:
        states.blink_timer += 1
    if states.health_blink_timer < config.blink_timer_max:
        states.health_blink_timer += 1

    keys = pygame.key.get_pressed()

    # Track player movement distance for "move" conditions
    if player:
        last_pos = _state["step_last_player_pos"]
        cur_pos = (player.rect.x, player.rect.y)
        if last_pos is not None:
            dist = math.hypot(cur_pos[0] - last_pos[0], cur_pos[1] - last_pos[1])
            _state["step_move_distance"] += dist
        _state["step_last_player_pos"] = cur_pos

    # 1. Update background starfield
    if _state["stars_bg"]:
        _state["stars_bg"].update()

    # 2. Update entities
    update_mod.update_entities(
        enemies=_state["enemies"],
        bullets=_state["bullets"],
        powerups=_state["powerups"],
        player=player,
        screen=None,
    )

    # 3. Update animations and effects
    for eff in _state["effects"][:]:
        eff.update(dt)
        if hasattr(eff, "is_expired") and eff.is_expired():
            _state["effects"].remove(eff)

    # 4. Handle player flight inputs
    if player:
        player.handle_input(keys)

        # Safety: keep player alive and replenished during training
        if player.health < 40:
            player.health = 100
        if player.energy < 30:
            player.energy += 1

    # 5. Optional random enemy / powerup spawns if current keyframe permits
    keyframes = _state["keyframes"]
    idx = _state["current_index"]
    if 0 <= idx < len(keyframes):
        current_kf = keyframes[idx]
        if current_kf.allow_random_enemies and clock.delay == 0:
            events.spawn_enemy(_state["enemies"])
        if current_kf.allow_random_powerups and clock.delay == 30:
            events.spawn_powerup(50, player, _state["powerups"])

    if clock.delay < 0:
        clock.delay = 60

    # 6. Step time tracking
    _state["step_active_time"] += (dt if dt > 0 else (1.0 / 60.0))

    if _state["step_condition_satisfied"]:
        _state["step_delay_timer"] -= (dt if dt > 0 else (1.0 / 60.0))

    # 7. Evaluate keyframe completion condition
    _check_keyframe_progression(manager=_state.get("manager"))


def _draw_tutorial_hud(screen: pygame.Surface):
    """Renders a tutorial objective banner at the top of the display."""
    keyframes = _state["keyframes"]
    idx = _state["current_index"]
    if not (0 <= idx < len(keyframes)):
        return

    kf = keyframes[idx]
    screen_w = screen.get_width()

    # Top HUD Banner container
    banner_w = min(740, screen_w - 60)
    banner_h = 58
    banner_x = (screen_w - banner_w) // 2
    banner_y = 12
    banner_rect = pygame.Rect(banner_x, banner_y, banner_w, banner_h)

    # Backdrop and border
    hud_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
    hud_surf.fill((16, 24, 38, 220))
    screen.blit(hud_surf, (banner_x, banner_y))
    pygame.draw.rect(screen, (135, 242, 255), banner_rect, width=2, border_radius=8)

    title_font = get_dialog_font("title", 13)
    body_font = get_dialog_font("body", 14)

    # Step indicator & title
    step_str = f"STEP {idx + 1}/{len(keyframes)}: {kf.title}"
    if title_font:
        t_surf = title_font.render(step_str, True, (135, 242, 255))
        screen.blit(t_surf, (banner_x + 16, banner_y + 8))

    # Objective description with progress tracker
    obj_text = kf.objective_text
    if kf.condition == "move":
        cur_d = int(min(kf.condition_target, _state.get("step_move_distance", 0.0)))
        obj_text += f" [{cur_d}/{int(kf.condition_target)} px]"
    elif kf.condition == "shoot":
        cur_s = min(int(kf.condition_target), _state.get("step_shots_fired", 0))
        obj_text += f" [{cur_s}/{int(kf.condition_target)}]"
    elif kf.condition == "enemies_cleared":
        remaining = len(_state.get("enemies", []))
        obj_text += f" [{remaining} target{'s' if remaining != 1 else ''} active]"
    elif kf.condition == "powerups_cleared":
        remaining = len(_state.get("powerups", []))
        obj_text += f" [{remaining} salvage active]"

    if body_font:
        o_surf = body_font.render(f"> {obj_text}", True, (240, 245, 255))
        screen.blit(o_surf, (banner_x + 16, banner_y + 32))


def draw(screen: pygame.Surface):
    """Dedicated draw function. Renders world entities, panel UI, and tutorial HUD."""
    screen.fill((0, 0, 0))

    if _state["stars_bg"]:
        _state["stars_bg"].draw(screen)

    player = _state["player"]

    # 1. World entities
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

    # 2. Main bottom HUD panel (health/energy)
    ui.draw_panel_ui(screen, player=player)

    # 3. Top Tutorial Objective Banner
    _draw_tutorial_hud(screen)

    # 4. If dialog is active in standalone mode (no manager overlay), draw it directly
    mgr = _state.get("manager")
    if _state["active_dialog"] and (mgr is None or getattr(mgr, "overlay_scene", None) is not _state["active_dialog"]):
        _state["active_dialog"].draw(screen)


class TutorialScene(BaseScene):
    """Class wrapper for Tutorial flight school scene."""

    def __init__(self, keyframes: list[TutorialKeyframe] | None = None):
        super().__init__()
        self.initial_keyframes = keyframes

    def load(self, *args, **kwargs):
        load(*args, keyframes=self.initial_keyframes, manager=self.manager, **kwargs)

    def unload(self):
        unload()

    def handle_event(self, event: pygame.event.Event):
        handle_event(event, self.manager)

    def update(self, dt: float = 1.0):
        update(dt)

    def draw(self, screen: pygame.Surface):
        draw(screen)

    def add_keyframe(self, keyframe: TutorialKeyframe):
        """Adds a new keyframe to this tutorial scene."""
        add_keyframe(keyframe)

    def set_keyframes(self, keyframes: list[TutorialKeyframe]):
        """Replaces the active tutorial keyframes list."""
        set_keyframes(keyframes)

    def get_keyframes(self) -> list[TutorialKeyframe]:
        """Returns the list of keyframes."""
        return get_keyframes()

    def next_keyframe(self):
        """Manually advances to the next keyframe."""
        _start_keyframe(_state["current_index"] + 1, manager=self.manager)

    def previous_keyframe(self):
        """Manually rewinds to the previous keyframe."""
        _start_keyframe(max(0, _state["current_index"] - 1), manager=self.manager)

    def jump_to_keyframe(self, index_or_id: int | str):
        """Jumps directly to a keyframe by index or string id."""
        if isinstance(index_or_id, int):
            _start_keyframe(index_or_id, manager=self.manager)
        else:
            for i, kf in enumerate(_state["keyframes"]):
                if kf.id == index_or_id:
                    _start_keyframe(i, manager=self.manager)
                    return
            logger.engine_log.warning(f"[Tutorial] Keyframe id '{index_or_id}' not found.")

    def finish_tutorial(self):
        """Finishes the tutorial and transitions back to GameMenuScene."""
        finish_tutorial(self.manager)
