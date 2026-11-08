"""Tests for Tutorial flight school scene and modular keyframe system."""

import os
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1072, 861))

import config
from src import assets
from src.scenes import SceneManager
from src.scenes.game_menu import GameMenuScene
from src.scenes.tutorial import (
    TutorialScene,
    TutorialKeyframe,
    get_default_keyframes,
    is_frozen,
    _state,
)

# Load assets once for tests
for _ in assets.load_assets_generator():
    pass


class TestTutorialScene(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.get_surface()
        self.manager = SceneManager(self.screen)

    def tearDown(self):
        if self.manager.overlay_scene:
            self.manager.close_overlay()
        if self.manager.current_scene:
            self.manager.current_scene.unload()

    def test_default_keyframes_structure(self):
        """Verifies that default keyframes are generated properly with expected ids."""
        keyframes = get_default_keyframes()
        self.assertGreaterEqual(len(keyframes), 5)
        step_ids = [kf.id for kf in keyframes]
        self.assertIn("welcome", step_ids)
        self.assertIn("movement", step_ids)
        self.assertIn("weapons", step_ids)
        self.assertIn("target_drone", step_ids)
        self.assertIn("shielded_enemy", step_ids)
        self.assertIn("powerups", step_ids)
        self.assertIn("completion", step_ids)

    def test_default_tutorial_launches_with_bottom_dialog(self):
        """Verifies that launching the default tutorial uses BottomDialog with 1/3 screen height."""
        from src.scenes.dialog import BottomDialog
        scene = TutorialScene()
        self.manager.set_scene(scene, fade=False)

        screen_h = self.screen.get_height()
        expected_h = int(screen_h * (1.0 / 3.0))

        self.assertIsInstance(_state["active_dialog"], BottomDialog)
        self.assertEqual(_state["active_dialog"].panel_rect.height, expected_h)
        self.assertEqual(_state["active_dialog"].panel_rect.bottom, screen_h)
        self.assertEqual(_state["active_dialog"].speaker, "FLIGHT INSTRUCTOR")

    def test_predefined_positions(self):
        """Verifies player and enemy pre-defined positions on keyframe entry."""
        custom_kf = TutorialKeyframe(
            id="test_positions",
            title="TEST POS",
            message="Test message",
            player_pos=(250, 350),
            enemies=[{"x": 750, "y": 350, "type": 0, "stationary": True}],
            powerups=[{"x": 650, "y": 350, "type": 0, "stationary": True}],
            condition="dialog_closed",
        )

        scene = TutorialScene(keyframes=[custom_kf])
        self.manager.set_scene(scene, fade=False)

        # Verify player position
        self.assertIsNotNone(_state["player"])
        self.assertEqual(_state["player"].rect.topleft, (250, 350))

        # Verify enemy pre-defined position and stationary behavior
        self.assertEqual(len(_state["enemies"]), 1)
        self.assertEqual(_state["enemies"][0].x, 750)
        self.assertEqual(_state["enemies"][0].y, 350)
        self.assertEqual(_state["enemies"][0].speed, 0)

        # Verify powerup pre-defined position
        self.assertEqual(len(_state["powerups"]), 1)
        self.assertEqual(_state["powerups"][0].x, 650)
        self.assertEqual(_state["powerups"][0].y, 350)

    def test_freeze_when_dialog_is_active(self):
        """Verifies that gameplay is frozen whenever a dialog is active, and unfreezes on dismiss."""
        custom_kf = TutorialKeyframe(
            id="test_freeze",
            title="FREEZE TEST",
            message="This should freeze the game.",
            player_pos=(200, 300),
            condition="move",
            condition_target=100.0,
        )

        scene = TutorialScene(keyframes=[custom_kf])
        self.manager.set_scene(scene, fade=False)

        # Active dialog is on screen -> MUST BE FROZEN
        self.assertTrue(is_frozen())
        self.assertIsNotNone(_state["active_dialog"])
        self.assertIsNotNone(self.manager.overlay_scene)

        # Attempt to update scene while frozen
        initial_player_x = _state["player"].rect.x
        scene.update(1.0)
        self.assertEqual(_state["player"].rect.x, initial_player_x)

        # Dismiss dialog
        self.manager.overlay_scene.close()

        # Dialog closed -> MUST BE UNFROZEN
        self.assertFalse(is_frozen())
        self.assertIsNone(_state["active_dialog"])

    def test_tutorial_keyframe_bottom_dialog(self):
        """Verifies that a TutorialKeyframe with dialog_type='bottom' instantiates a BottomDialog."""
        from src.scenes.dialog import BottomDialog
        custom_kf = TutorialKeyframe(
            id="test_bottom",
            title="RADIO COMMS",
            message="Incoming transmission from flight instructor.",
            dialog_type="bottom",
            condition="dialog_closed",
        )

        scene = TutorialScene(keyframes=[custom_kf])
        self.manager.set_scene(scene, fade=False)

        self.assertTrue(is_frozen())
        self.assertIsInstance(_state["active_dialog"], BottomDialog)
        self.assertEqual(_state["active_dialog"].panel_rect.bottom, self.screen.get_height())
        self.manager.overlay_scene.close()
        self.assertFalse(is_frozen())

    def test_completion_condition_movement(self):
        """Verifies movement condition detection and keyframe advancement."""
        kf1 = TutorialKeyframe(
            id="step_move",
            title="MOVE STEP",
            message="Move ship",
            player_pos=(200, 300),
            condition="move",
            condition_target=50.0,
            auto_advance_delay=0.0,
        )
        kf2 = TutorialKeyframe(
            id="step_final",
            title="FINAL STEP",
            message="Final",
            condition="dialog_closed",
        )

        scene = TutorialScene(keyframes=[kf1, kf2])
        self.manager.set_scene(scene, fade=False)

        # Dismiss dialog to unfreeze
        self.manager.overlay_scene.close()
        self.assertFalse(is_frozen())
        self.assertEqual(_state["current_index"], 0)

        # Simulate player movement
        _state["player"].rect.x += 60
        scene.update(1.0)

        # Keyframe should advance to step 2
        self.assertEqual(_state["current_index"], 1)

    def test_completion_condition_shooting(self):
        """Verifies shooting condition detection and progression."""
        kf1 = TutorialKeyframe(
            id="step_shoot",
            title="SHOOT STEP",
            message="Fire blasters",
            player_pos=(200, 300),
            condition="shoot",
            condition_target=2,
            auto_advance_delay=0.0,
        )
        kf2 = TutorialKeyframe(
            id="step_after",
            title="NEXT STEP",
            message="Next",
            condition="dialog_closed",
        )

        scene = TutorialScene(keyframes=[kf1, kf2])
        self.manager.set_scene(scene, fade=False)

        # Dismiss dialog to unfreeze
        self.manager.overlay_scene.close()

        # Fire 2 shots
        shoot_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        scene.handle_event(shoot_event)
        scene.handle_event(shoot_event)

        scene.update(1.0)
        self.assertEqual(_state["current_index"], 1)

    def test_completion_condition_enemies_cleared(self):
        """Verifies enemies_cleared condition advances when enemies list is empty."""
        kf1 = TutorialKeyframe(
            id="step_target",
            title="TARGET STEP",
            message="Destroy target",
            enemies=[{"x": 800, "y": 300, "type": 0, "stationary": True}],
            condition="enemies_cleared",
            auto_advance_delay=0.0,
        )
        kf2 = TutorialKeyframe(
            id="step_next",
            title="AFTER TARGET",
            message="Done",
            condition="dialog_closed",
        )

        scene = TutorialScene(keyframes=[kf1, kf2])
        self.manager.set_scene(scene, fade=False)

        # Dismiss dialog
        self.manager.overlay_scene.close()
        self.assertEqual(len(_state["enemies"]), 1)

        # Eliminate enemy
        _state["enemies"].clear()
        scene.update(1.0)

        # Should advance to next step
        self.assertEqual(_state["current_index"], 1)

    def test_completion_transitions_back_to_game_menu(self):
        """Verifies that finishing the final tutorial keyframe returns to GameMenuScene."""
        kf = TutorialKeyframe(
            id="only_step",
            title="ONLY STEP",
            message="Complete tutorial",
            condition="dialog_closed",
        )

        scene = TutorialScene(keyframes=[kf])
        self.manager.set_scene(scene, fade=False)

        # Dismiss dialog on the only/final step
        self.manager.overlay_scene.close()

        # Should transition scene to GameMenuScene
        self.assertTrue(_state["tutorial_finished"])
        # If transitioning with fade, next_scene is GameMenuScene
        next_or_cur = self.manager.next_scene or self.manager.current_scene
        self.assertIsInstance(next_or_cur, GameMenuScene)

    def test_modular_add_and_set_keyframes(self):
        """Verifies modular keyframe manipulation (add_keyframe, set_keyframes)."""
        scene = TutorialScene(keyframes=[])
        kf_a = TutorialKeyframe(id="a", title="A", message="A msg")
        kf_b = TutorialKeyframe(id="b", title="B", message="B msg")

        scene.add_keyframe(kf_a)
        scene.add_keyframe(kf_b)

        kfs = scene.get_keyframes()
        self.assertEqual(len(kfs), 2)
        self.assertEqual(kfs[0].id, "a")
        self.assertEqual(kfs[1].id, "b")


if __name__ == "__main__":
    unittest.main()
