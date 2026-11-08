"""Dialog Test Module for Galactic Space Reborn.

Provides separate test suites for basic functionality and push-to-the-limit stress testing
for all dialog types (MessageDialog, ConfirmationDialog, MultiPageDialog, and DialogScene).

Can be executed in multiple modes:
1. Automated headless test runner via CLI:
   python3 src/scenes/dialog_test.py [--suite {basic,limit,all}] [--dialog {message,confirmation,multipage,custom,all}]
2. Standard unittest:
   python3 -m unittest src/scenes/dialog_test.py
3. Interactive visual GUI scene:
   python3 src/scenes/dialog_test.py --interactive
   or via game scene manager with namespace 'gsr.scene:dialog_test'
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import unittest
from typing import Any, Callable

import pygame

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config
from src import logger
from src.controls import ControllerInput
from src.scenes.base import BaseScene
from src.scenes.manager import SceneManager
from src.scenes.dialog import (
    DialogScene,
    ConfirmationDialog,
    MessageDialog,
    MultiPageDialog,
    BottomDialog,
    BottomBannerDialog,
    MultiPageBottomDialog,
    show_dialog,
    show_message,
    show_confirmation,
    show_bottom_dialog,
    wrap_text,
    get_dialog_font,
)


def ensure_headless_display() -> pygame.Surface:
    """Ensures pygame and display are initialized, falling back to dummy driver if headless."""
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()

    surface = pygame.display.get_surface()
    if surface is None:
        try:
            surface = pygame.display.set_mode((1072, 861))
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            os.environ["SDL_AUDIODRIVER"] = "dummy"
            pygame.display.init()
            surface = pygame.display.set_mode((1072, 861))
    return surface


# ============================================================================
# 1. BASIC TEST SUITE
# ============================================================================

class BasicDialogTests(unittest.TestCase):
    """Basic functional tests for standard usage of all dialog components."""

    @classmethod
    def setUpClass(cls):
        cls.screen = ensure_headless_display()

    def setUp(self):
        self.manager = SceneManager(self.screen)

    # ------------------------------------------------------------------------
    # MessageDialog Basic Tests
    # ------------------------------------------------------------------------

    def test_basic_message_dialog(self):
        """Validates normal MessageDialog creation, action count, dismissal callback, and rendering."""
        dismissed = False

        def on_dismiss():
            nonlocal dismissed
            dismissed = True

        title = "MISSION BRIEFING"
        body = "Enemy fleet detected in Sector 4.\nIntercept immediately."
        dialog = MessageDialog(
            title=title,
            message=body,
            on_dismiss=on_dismiss,
            ok_label="ACKNOWLEDGE",
        )

        self.assertEqual(dialog.title, title)
        self.assertEqual(len(dialog.actions), 1)
        self.assertEqual(dialog.actions[0]["label"], "ACKNOWLEDGE")
        self.assertGreater(dialog.panel_rect.width, 300)
        self.assertGreater(dialog.panel_rect.height, 100)

        # Test drawing without error
        dialog.draw(self.screen)

        # Attach to manager and verify trigger execution
        self.manager.show_overlay(dialog)
        self.assertIs(self.manager.overlay_scene, dialog)

        # Simulate confirm (Enter key)
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        dialog.handle_event(enter_event)

        self.assertTrue(dismissed, "MessageDialog on_dismiss callback was not executed on confirm")
        self.assertIsNone(self.manager.overlay_scene, "MessageDialog did not close overlay after confirmation")

    def test_basic_message_dialog_escape(self):
        """Validates that pressing Escape dismisses a standard MessageDialog."""
        dismissed = False

        def on_dismiss():
            nonlocal dismissed
            dismissed = True

        dialog = MessageDialog(
            title="ALERT",
            message="Incoming missile warning.",
            on_dismiss=on_dismiss,
        )
        self.manager.show_overlay(dialog)

        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        dialog.handle_event(escape_event)

        self.assertTrue(dismissed, "MessageDialog on_dismiss was not executed on Escape")
        self.assertIsNone(self.manager.overlay_scene, "Overlay was not closed on Escape")

    # ------------------------------------------------------------------------
    # ConfirmationDialog Basic Tests
    # ------------------------------------------------------------------------

    def test_basic_confirmation_dialog_confirm(self):
        """Validates ConfirmationDialog YES / Confirm action execution."""
        confirmed = False
        cancelled = False

        def on_confirm():
            nonlocal confirmed
            confirmed = True

        def on_cancel():
            nonlocal cancelled
            cancelled = True

        dialog = ConfirmationDialog(
            message="Abort current hyperjump?",
            on_confirm=on_confirm,
            on_cancel=on_cancel,
            title="CONFIRM ABORT",
            confirm_label="ABORT",
            cancel_label="CANCEL",
        )

        self.assertEqual(dialog.title, "CONFIRM ABORT")
        self.assertEqual(len(dialog.actions), 2)
        self.assertEqual(dialog.actions[0]["label"], "ABORT")
        self.assertEqual(dialog.actions[1]["label"], "CANCEL")

        dialog.draw(self.screen)

        self.manager.show_overlay(dialog)
        # Default selection is 0 (Confirm)
        self.assertEqual(dialog.selected_index, 0)

        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        dialog.handle_event(enter_event)

        self.assertTrue(confirmed, "Confirm callback did not execute")
        self.assertFalse(cancelled, "Cancel callback executed during confirm")
        self.assertIsNone(self.manager.overlay_scene)

    def test_basic_confirmation_dialog_cancel(self):
        """Validates ConfirmationDialog NO / Cancel navigation and action execution."""
        confirmed = False
        cancelled = False

        def on_confirm():
            nonlocal confirmed
            confirmed = True

        def on_cancel():
            nonlocal cancelled
            cancelled = True

        dialog = ConfirmationDialog(
            message="Discard unsaved changes?",
            on_confirm=on_confirm,
            on_cancel=on_cancel,
        )
        self.manager.show_overlay(dialog)

        # Navigate right to select NO (index 1)
        right_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
        dialog.handle_event(right_event)
        self.assertEqual(dialog.selected_index, 1)

        # Trigger NO
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        dialog.handle_event(enter_event)

        self.assertFalse(confirmed)
        self.assertTrue(cancelled)
        self.assertIsNone(self.manager.overlay_scene)

    def test_basic_confirmation_dialog_legacy_signature(self):
        """Validates legacy positional argument signature compatibility."""
        dialog = ConfirmationDialog(100, 150, 450, 220, "Legacy Prompt Text", None)
        self.assertEqual(dialog.panel_rect.x, 100)
        self.assertEqual(dialog.panel_rect.y, 150)
        self.assertEqual(dialog.panel_rect.width, 450)
        self.assertEqual(dialog.panel_rect.height, 220)
        dialog.draw(self.screen)

    # ------------------------------------------------------------------------
    # MultiPageDialog Basic Tests
    # ------------------------------------------------------------------------

    def test_basic_multipage_dialog(self):
        """Validates page progression, back tracking, and completion of MultiPageDialog."""
        completed = False
        cancelled = False

        pages = [
            {"title": "PILOT MANUAL (1/3)", "message": "Use WASD or Left Stick to steer your ship."},
            {"title": "PILOT MANUAL (2/3)", "message": "Press SPACE or (A) to fire primary laser."},
            {"title": "PILOT MANUAL (3/3)", "message": "Collect shield power-ups to repair hull damage."},
        ]

        def on_complete():
            nonlocal completed
            completed = True

        def on_cancel():
            nonlocal cancelled
            cancelled = True

        dialog = MultiPageDialog(
            pages=pages,
            on_complete=on_complete,
            on_cancel=on_cancel,
            finish_label="COMMENCE",
            next_label="FORWARD",
            prev_label="BACK",
        )
        self.manager.show_overlay(dialog)

        # Page 1 validation: only FORWARD button
        self.assertEqual(dialog.current_page, 0)
        self.assertEqual(dialog.title, "PILOT MANUAL (1/3)")
        self.assertEqual(len(dialog.actions), 1)
        self.assertEqual(dialog.actions[0]["label"], "FORWARD")
        dialog.draw(self.screen)

        # Go to Page 2
        dialog.next_page()
        self.assertEqual(dialog.current_page, 1)
        self.assertEqual(dialog.title, "PILOT MANUAL (2/3)")
        self.assertEqual(len(dialog.actions), 2)
        self.assertEqual(dialog.actions[0]["label"], "BACK")
        self.assertEqual(dialog.actions[1]["label"], "FORWARD")
        dialog.draw(self.screen)

        # Go back to Page 1
        dialog.prev_page()
        self.assertEqual(dialog.current_page, 0)
        self.assertEqual(len(dialog.actions), 1)

        # Forward to Page 2 then Page 3
        dialog.next_page()
        dialog.next_page()
        self.assertEqual(dialog.current_page, 2)
        self.assertEqual(dialog.title, "PILOT MANUAL (3/3)")
        self.assertEqual(len(dialog.actions), 2)
        self.assertEqual(dialog.actions[0]["label"], "BACK")
        self.assertEqual(dialog.actions[1]["label"], "COMMENCE")
        dialog.draw(self.screen)

        # Trigger COMMENCE action (index 1)
        dialog._trigger_action(1)
        self.assertTrue(completed, "MultiPageDialog on_complete was not invoked on final page finish")
        self.assertFalse(cancelled)
        self.assertIsNone(self.manager.overlay_scene)

    # ------------------------------------------------------------------------
    # DialogScene (Custom / Generic) Basic Tests
    # ------------------------------------------------------------------------

    def test_basic_custom_dialog(self):
        """Validates generic DialogScene custom action definitions, alignment, and dynamic mutations."""
        action_log = []

        actions = [
            ("Alpha", lambda: action_log.append("alpha")),
            ("Beta", lambda: action_log.append("beta")),
            {"label": "Gamma", "callback": lambda: action_log.append("gamma"), "close": True},
        ]

        dialog = DialogScene(
            title="CUSTOM PROTOCOL",
            message=["Instruction Alpha", "Instruction Beta"],
            actions=actions,
            width=520,
            height=320,
            align="left",
            button_layout="horizontal",
        )

        self.assertEqual(len(dialog.actions), 3)
        self.assertEqual(len(dialog.button_rects), 3)
        self.assertEqual(dialog.panel_rect.width, 520)
        self.assertEqual(dialog.panel_rect.height, 320)
        self.assertEqual(dialog.align, "left")

        dialog.draw(self.screen)

        # Test dynamic mutations
        dialog.set_title("NEW HEADER")
        self.assertEqual(dialog.title, "NEW HEADER")

        dialog.set_message("A solitary string replacement.")
        self.assertEqual(dialog.raw_message, "A solitary string replacement.")

        dialog.set_actions([("Solo", None)])
        self.assertEqual(len(dialog.actions), 1)
        self.assertEqual(len(dialog.button_rects), 1)

        dialog.draw(self.screen)

    # ------------------------------------------------------------------------
    # Helper Functions Basic Tests
    # ------------------------------------------------------------------------

    def test_basic_helper_functions(self):
        """Validates show_dialog, show_message, and show_confirmation utility functions."""
        # show_message helper
        msg_dialog = show_message(self.manager, title="QUICK NOTICE", message="Test notice")
        self.assertIsInstance(msg_dialog, MessageDialog)
        self.assertIs(self.manager.overlay_scene, msg_dialog)
        msg_dialog.close()
        self.assertIsNone(self.manager.overlay_scene)

        # show_confirmation helper
        conf_dialog = show_confirmation(self.manager, message="Quick confirm?")
        self.assertIsInstance(conf_dialog, ConfirmationDialog)
        self.assertIs(self.manager.overlay_scene, conf_dialog)
        conf_dialog.close()
        self.assertIsNone(self.manager.overlay_scene)

        # show_dialog helper
        cust_dialog = show_dialog(self.manager, title="QUICK CUSTOM", message="Custom payload")
        self.assertIsInstance(cust_dialog, DialogScene)
        self.assertIs(self.manager.overlay_scene, cust_dialog)
        cust_dialog.close()
        self.assertIsNone(self.manager.overlay_scene)

    # ------------------------------------------------------------------------
    # BottomDialog / BottomBannerDialog Basic Tests
    # ------------------------------------------------------------------------

    def test_basic_bottom_dialog_layout(self):
        """Validates that BottomDialog spans the screen width and docks to the bottom with default 1/3 height."""
        screen_w, screen_h = self.screen.get_size()
        dialog = BottomDialog(
            title="COMMS TRANSMISSION",
            message="Incoming transmission from fleet command.",
            actions=[("ACKNOWLEDGE", None)],
        )

        # Full screen width
        self.assertEqual(dialog.panel_rect.width, screen_w)
        self.assertEqual(dialog.panel_rect.x, 0)

        # Docked at the bottom
        self.assertEqual(dialog.panel_rect.bottom, screen_h)

        # Default height is 1/3 of the screen
        expected_h = int(screen_h * (1.0 / 3.0))
        self.assertEqual(dialog.panel_rect.height, expected_h)

        # Draw without errors
        dialog.draw(self.screen)

    def test_bottom_dialog_configurable_height(self):
        """Validates configurable height options: explicit pixel height, float ratio, and height_ratio."""
        screen_w, screen_h = self.screen.get_size()

        # 1. Explicit pixel height
        d_px = BottomDialog(message="Pixel height test", height=240)
        self.assertEqual(d_px.panel_rect.height, 240)
        self.assertEqual(d_px.panel_rect.bottom, screen_h)

        # 2. Ratio via float height
        d_ratio_float = BottomDialog(message="Ratio float test", height=0.5)
        self.assertEqual(d_ratio_float.panel_rect.height, int(screen_h * 0.5))
        self.assertEqual(d_ratio_float.panel_rect.bottom, screen_h)

        # 3. Ratio via height_ratio argument
        d_ratio = BottomDialog(message="Height ratio test", height_ratio=0.25)
        self.assertEqual(d_ratio.panel_rect.height, int(screen_h * 0.25))
        self.assertEqual(d_ratio.panel_rect.bottom, screen_h)

        # 4. Optional margin
        d_margin = BottomDialog(message="Margin test", margin=20, height_ratio=0.3)
        self.assertEqual(d_margin.panel_rect.width, screen_w - 40)
        self.assertEqual(d_margin.panel_rect.bottom, screen_h - 20)
        self.assertEqual(d_margin.panel_rect.x, 20)

    def test_bottom_dialog_speaker_and_avatar(self):
        """Validates speaker callsign badge and avatar surface rendering in BottomDialog."""
        avatar_surf = pygame.Surface((64, 64))
        avatar_surf.fill((0, 200, 255))

        dialog = BottomDialog(
            title="TACTICAL ALERT",
            speaker="COMMANDER VANCE",
            avatar=avatar_surf,
            message="Hostile fleet closing in at sub-light speed.",
            actions=[("STAND BY", None)],
        )

        self.assertIsNotNone(dialog.avatar_rect)
        self.assertGreater(dialog.avatar_rect.width, 0)
        dialog.draw(self.screen)

    def test_show_bottom_dialog_helper(self):
        """Validates the show_bottom_dialog convenience helper attaches overlay properly."""
        dialog = show_bottom_dialog(
            self.manager,
            title="SECTOR ALERT",
            message="Drone activity detected.",
            height_ratio=0.35,
        )

        self.assertIsInstance(dialog, BottomDialog)
        self.assertIs(self.manager.overlay_scene, dialog)
        self.assertEqual(dialog.panel_rect.bottom, self.screen.get_height())
        dialog.close()
        self.assertIsNone(self.manager.overlay_scene)

    def test_multipage_bottom_dialog(self):
        """Validates MultiPageBottomDialog walks through pages while docked at screen bottom."""
        screen_h = self.screen.get_height()
        pages = [
            {"title": "PART 1", "message": "First transmission", "speaker": "OFFICER A"},
            {"title": "PART 2", "message": "Second transmission", "speaker": "OFFICER B"},
        ]

        completed = False
        dialog = MultiPageBottomDialog(pages=pages, on_complete=lambda: nonlocal_complete())

        def nonlocal_complete():
            nonlocal completed
            completed = True

        self.manager.show_overlay(dialog)
        self.assertEqual(dialog.panel_rect.bottom, screen_h)
        self.assertEqual(dialog.current_page, 0)

        # Next page
        dialog.next_page()
        self.assertEqual(dialog.current_page, 1)

        # Trigger finish
        dialog._trigger_action(1)
        self.assertTrue(completed)
        self.assertIsNone(self.manager.overlay_scene)


# ============================================================================
# 2. PUSH-TO-THE-LIMIT TEST SUITE
# ============================================================================

class LimitDialogTests(unittest.TestCase):
    """Stress and edge-case boundary tests that push all dialog components to their limits."""

    @classmethod
    def setUpClass(cls):
        cls.screen = ensure_headless_display()

    def setUp(self):
        self.manager = SceneManager(self.screen)

    # ------------------------------------------------------------------------
    # MessageDialog Limit Tests
    # ------------------------------------------------------------------------

    def test_limit_message_dialog_massive_text(self):
        """Stress test with an enormous body text (15,000+ words, 80,000+ characters)."""
        paragraph = (
            "Sector report indicates critical telemetry anomalies across outer perimeter boundaries. "
            "Quantum sensors detect hyperdrive emissions matching hostile dreadnought signatures. "
            "Shield resonance must be synchronized immediately to prevent catastrophic bulkhead collapse. "
        )
        massive_text = "\n\n".join([paragraph * 5 for _ in range(50)])
        self.assertGreater(len(massive_text), 40000)

        t_start = time.perf_counter()
        dialog = MessageDialog(title="MASSIVE PAYLOAD REPORT", message=massive_text)
        t_layout = time.perf_counter() - t_start

        # Layout calculation should complete in sub-second time
        self.assertLess(t_layout, 1.0, f"Massive text layout took too long: {t_layout:.2f}s")
        self.assertGreater(len(dialog.wrapped_lines), 200)

        # Drawing huge line-count onto surface
        t_draw_start = time.perf_counter()
        dialog.draw(self.screen)
        t_draw = time.perf_counter() - t_draw_start
        self.assertLess(t_draw, 0.5, f"Massive text draw took too long: {t_draw:.2f}s")

    def test_limit_message_dialog_empty_and_whitespace(self):
        """Validates that zero-length, whitespace-only, and empty list messages do not raise exceptions."""
        edge_cases = ["", "   ", "\t\t\n\n\r\n", " \n \n ", []]
        for idx, payload in enumerate(edge_cases):
            with self.subTest(payload_index=idx):
                dialog = MessageDialog(title="", message=payload)
                self.assertIsNotNone(dialog.panel_rect)
                dialog.draw(self.screen)

    def test_limit_message_dialog_unbroken_words(self):
        """Stress test with unbroken continuous tokens (1,500 characters without whitespace)."""
        unbroken_token = "WARP_DRIVE_CALIBRATION_FREQUENCY_VALUE_" * 40
        dialog = MessageDialog(
            title="UNBROKEN TOKEN TEST",
            message=f"Beginning token:\n{unbroken_token}\nEnd of transmission.",
        )
        self.assertGreater(len(dialog.wrapped_lines), 0)
        dialog.draw(self.screen)

    def test_limit_message_dialog_unicode_and_emojis(self):
        """Stress test with multi-byte UTF-8, emojis, CJK ideographs, RTL Arabic, and mathematical symbols."""
        unicode_payload = (
            "🚀 GALACTIC COMMAND 🌌\n"
            "Status: 👾 Alien Fleet Approaching [危險: 極大]\n"
            "Hyperdrive Frequency: ∇ × B = μ₀(J + ε₀ ∂E/∂t) ± ∞\n"
            "Transmissions: こんにちは世界 / مرحباً بك في الفضاء / Привет мир\n"
            "Key Codes: ⚡🛡️💥🎮🔥🌟\n"
        )
        dialog = MessageDialog(title="🌌 UNICODE HARNESS 🛸", message=unicode_payload)
        dialog.draw(self.screen)

    def test_limit_message_dialog_screen_extremes(self):
        """Stress test against extreme display resolutions: microscopic (120x120) and 4K (3840x2160)."""
        resolutions = [(120, 120), (320, 240), (2560, 1440), (3840, 2160), (5120, 1440)]
        for w, h in resolutions:
            with self.subTest(resolution=(w, h)):
                surf = pygame.Surface((w, h))
                dialog = MessageDialog(title="RESOLUTION STRESS", message="Testing boundary geometry.")
                # Force recalculation for target surface
                orig_size = (config.Screen.Size.w, config.Screen.Size.h)
                try:
                    config.Screen.Size.w, config.Screen.Size.h = w, h
                    dialog._recalculate_layout()
                    self.assertGreater(dialog.panel_rect.width, 0)
                    self.assertGreater(dialog.panel_rect.height, 0)
                    dialog.draw(surf)
                finally:
                    config.Screen.Size.w, config.Screen.Size.h = orig_size

    def test_limit_message_dialog_rapid_mutation(self):
        """Rapidly mutates title and message content 500 times in loop."""
        dialog = MessageDialog(title="INITIAL", message="Initial body")
        for i in range(500):
            dialog.set_title(f"CYCLE {i}")
            dialog.set_message(f"Dynamic memory payload sequence #{i} with variable length " * (i % 5 + 1))
        self.assertEqual(dialog.title, "CYCLE 499")
        dialog.draw(self.screen)

    # ------------------------------------------------------------------------
    # ConfirmationDialog Limit Tests
    # ------------------------------------------------------------------------

    def test_limit_confirmation_dialog_verbose_labels(self):
        """Stress test ConfirmationDialog with ultra-verbose labels and massive prompt."""
        huge_confirm = "PROCEED WITH IMMEDIATE REACTOR CORE PURGE AND INITIATE FULL EVACUATION PROTOCOL NOW"
        huge_cancel = "CANCEL PROCEDURE AND MANUALLY ATTEMPT FIELD CONTAINMENT STABILIZATION SEQUENCE"
        dialog = ConfirmationDialog(
            message="WARNING: Extreme system instability detected!\nConfirm emergency containment override?",
            confirm_label=huge_confirm,
            cancel_label=huge_cancel,
            button_layout="vertical",
        )
        self.assertEqual(dialog.actions[0]["label"], huge_confirm)
        self.assertEqual(dialog.actions[1]["label"], huge_cancel)
        dialog.draw(self.screen)

    def test_limit_confirmation_dialog_rapid_navigation(self):
        """Bombards ConfirmationDialog with 3,000 rapid directional navigation keypresses."""
        dialog = ConfirmationDialog(message="Rapid navigation stress test")
        keys = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_a, pygame.K_d, pygame.K_TAB]
        for i in range(3000):
            k = keys[i % len(keys)]
            dialog.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k))
            self.assertIn(dialog.selected_index, (0, 1))

    def test_limit_confirmation_dialog_persisting_callback(self):
        """Validates that callbacks returning False successfully prevent dialog closure under repeated hits."""
        attempts = 0

        def non_closing_confirm():
            nonlocal attempts
            attempts += 1
            return False  # Explicitly veto dismissal

        dialog = ConfirmationDialog(message="Persisting dialog test", on_confirm=non_closing_confirm)
        self.manager.show_overlay(dialog)

        # Trigger confirm 50 times
        for _ in range(50):
            enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            dialog.handle_event(enter_event)

        self.assertEqual(attempts, 50)
        self.assertIs(self.manager.overlay_scene, dialog, "Dialog unexpectedly closed when callback returned False")
        dialog.close()

    def test_limit_confirmation_dialog_legacy_parameters(self):
        """Stress tests legacy signature with negative coordinates and non-string arguments."""
        dialog = ConfirmationDialog(-500, -200, 0, 0, 123456789, None)
        self.assertIsNotNone(dialog.panel_rect)
        dialog.draw(self.screen)

    # ------------------------------------------------------------------------
    # MultiPageDialog Limit Tests
    # ------------------------------------------------------------------------

    def test_limit_multipage_dialog_100_pages(self):
        """Stress tests MultiPageDialog instantiated with 120 dynamically generated pages."""
        page_count = 120
        pages = [
            {
                "title": f"LOG ENTRY {idx + 1:03d}/{page_count}",
                "message": f"Deep space exploration telemetry log record #{idx + 1}.\n"
                           f"Signal strength: {100 - (idx % 80)}% | Sector: {idx * 7}",
            }
            for idx in range(page_count)
        ]

        completed = False
        dialog = MultiPageDialog(pages=pages, on_complete=lambda: setattr(dialog, "done", True))
        setattr(dialog, "done", False)

        # Rapidly walk through all 120 pages
        for expected_page in range(page_count):
            self.assertEqual(dialog.current_page, expected_page)
            if expected_page < page_count - 1:
                dialog.next_page()

        # Last page should have finish action
        self.assertEqual(dialog.current_page, page_count - 1)
        self.assertEqual(dialog.actions[-1]["label"], "FINISH")

        # Rapidly walk all the way back to page 0
        for _ in range(page_count - 1):
            dialog.prev_page()
        self.assertEqual(dialog.current_page, 0)

        dialog.draw(self.screen)

    def test_limit_multipage_dialog_boundary_overflow(self):
        """Ensures calling next_page() and prev_page() past bounds is safe and non-throwing."""
        pages = [{"title": "P1", "message": "Only 1"}, {"title": "P2", "message": "Only 2"}]
        dialog = MultiPageDialog(pages=pages)

        # Try to go before page 0
        for _ in range(30):
            res = dialog.prev_page()
            self.assertFalse(res)
            self.assertEqual(dialog.current_page, 0)

        # Advance to last page
        dialog.next_page()
        self.assertEqual(dialog.current_page, 1)

        # Try to advance past last page
        for _ in range(30):
            res = dialog.next_page()
            self.assertFalse(res)
            self.assertEqual(dialog.current_page, 1)

    def test_limit_multipage_dialog_single_and_empty(self):
        """Validates edge cases of 1 page and 0 pages (empty list)."""
        # 1 page: Should immediately show FINISH without NEXT/PREV
        single = MultiPageDialog(pages=[{"title": "SOLO", "message": "Solo page"}])
        self.assertEqual(len(single.actions), 1)
        self.assertEqual(single.actions[0]["label"], "FINISH")
        single.draw(self.screen)

        # 0 pages: Safe fallback
        empty = MultiPageDialog(pages=[])
        self.assertGreater(len(empty.pages), 0)
        empty.draw(self.screen)

    def test_limit_multipage_dialog_rapid_cycling(self):
        """Flipping back and forth 1,000 times in loop."""
        pages = [
            {"title": "Cycle A", "message": "Message A"},
            {"title": "Cycle B", "message": "Message B"},
        ]
        dialog = MultiPageDialog(pages=pages)
        for _ in range(1000):
            dialog.next_page()
            dialog.prev_page()
        self.assertEqual(dialog.current_page, 0)
        dialog.draw(self.screen)

    # ------------------------------------------------------------------------
    # DialogScene (Custom / Generic) Limit Tests
    # ------------------------------------------------------------------------

    def test_limit_custom_dialog_button_overload(self):
        """Stress tests custom dialog with 35 action buttons in vertical layout."""
        button_count = 35
        actions = [(f"Command {idx:02d}", None) for idx in range(button_count)]
        dialog = DialogScene(
            title="BUTTON OVERLOAD HARNESS",
            message="Selecting from excessive action list.",
            actions=actions,
            button_layout="vertical",
        )

        self.assertEqual(len(dialog.actions), button_count)
        self.assertEqual(len(dialog.button_rects), button_count)

        # Navigation index wrapping with 35 items
        for _ in range(button_count * 2):
            dialog.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
        self.assertEqual(dialog.selected_index, 0)

        dialog.draw(self.screen)

    def test_limit_custom_dialog_geometry_extremes(self):
        """Validates extreme widths, heights, and coordinates (negative, zero, massive)."""
        geometries = [
            (0, 0, (0, 0)),
            (-500, -500, (-100, -100)),
            (50000, 50000, (0, 0)),
            (10, 10, (-9999, -9999)),
        ]
        for w, h, pos in geometries:
            with self.subTest(geometry=(w, h, pos)):
                dialog = DialogScene(
                    title="GEOMETRY TEST",
                    message="Testing dimension bounds.",
                    width=w,
                    height=h,
                    pos=pos,
                )
                self.assertGreater(dialog.panel_rect.width, 0)
                self.assertGreater(dialog.panel_rect.height, 0)
                dialog.draw(self.screen)

    def test_limit_custom_dialog_event_bombardment(self):
        """Bombards custom dialog with 5,000 mixed events (mouse, keyboard, controller)."""
        actions = [("A", None), ("B", None), ("C", None), ("D", None)]
        dialog = DialogScene(title="EVENT STORM", actions=actions)

        for i in range(5000):
            ev_type = i % 4
            if ev_type == 0:
                ev = pygame.event.Event(pygame.MOUSEMOTION, pos=(i % 1000, (i * 3) % 800))
            elif ev_type == 1:
                ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB)
            elif ev_type == 2:
                ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(-10, -10))
            else:
                ev = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
            dialog.handle_event(ev)

        self.assertGreaterEqual(dialog.selected_index, 0)
        self.assertLess(dialog.selected_index, 4)

    # ------------------------------------------------------------------------
    # SceneManager Overlay Stress Tests
    # ------------------------------------------------------------------------

    def test_limit_overlay_manager_stress(self):
        """Opens and dismisses 100 dialog overlays in rapid sequential succession on SceneManager."""
        for idx in range(100):
            dlg = MessageDialog(title=f"BURST {idx}", message=f"Burst payload #{idx}")
            self.manager.show_overlay(dlg)
            self.assertIs(self.manager.overlay_scene, dlg)
            self.manager.update(1.0)
            self.manager.draw(self.screen)
            dlg.close()
            self.assertIsNone(self.manager.overlay_scene)


# ============================================================================
# 3. INTERACTIVE VISUAL TEST SCENE
# ============================================================================

class DialogTestScene(BaseScene):
    """Interactive visual inspection harness allowing live manual testing

    of basic dialogs and push-to-the-limit stress dialogs.
    """

    def __init__(self):
        super().__init__()
        self.selected_index = 0
        self.status_message = "Ready. Select a test or press [F1]/[F2] to run headless suites."
        self.status_color = (135, 242, 255)
        self.buttons: list[dict[str, Any]] = []

    def load(self, *args, **kwargs):
        self.selected_index = 0
        self.buttons = [
            # Basic Tests (Left Column)
            {"text": "1. Basic Message Dialog", "category": "BASIC", "callback": self._launch_basic_message, "col": 0, "row": 0},
            {"text": "2. Basic Confirmation Dialog", "category": "BASIC", "callback": self._launch_basic_confirmation, "col": 0, "row": 1},
            {"text": "3. Basic MultiPage (3 Pages)", "category": "BASIC", "callback": self._launch_basic_multipage, "col": 0, "row": 2},
            {"text": "4. Basic Custom Dialog", "category": "BASIC", "callback": self._launch_basic_custom, "col": 0, "row": 3},

            # Limit Tests (Right Column)
            {"text": "5. Limit: Massive Text & Unicode", "category": "LIMIT", "callback": self._launch_limit_massive_message, "col": 1, "row": 0},
            {"text": "6. Limit: Verbose Confirmation", "category": "LIMIT", "callback": self._launch_limit_verbose_confirm, "col": 1, "row": 1},
            {"text": "7. Limit: 100-Page MultiPage", "category": "LIMIT", "callback": self._launch_limit_100_pages, "col": 1, "row": 2},
            {"text": "8. Limit: 30-Button Overload", "category": "LIMIT", "callback": self._launch_limit_buttons_overload, "col": 1, "row": 3},

            # Actions / Runners (Bottom Row)
            {"text": "[F1] Run Headless Basic Suite", "category": "RUNNER", "callback": self._run_headless_basic, "col": 0, "row": 4},
            {"text": "[F2] Run Headless Limit Suite", "category": "RUNNER", "callback": self._run_headless_limit, "col": 1, "row": 4},
            {"text": "[F3] Run All Headless Suites", "category": "RUNNER", "callback": self._run_headless_all, "col": 0, "row": 5},
            {"text": "[ESC] Exit Test Harness", "category": "RUNNER", "callback": self._exit_harness, "col": 1, "row": 5},
        ]

    # --- Interactive Launch Callbacks ---

    def _launch_basic_message(self):
        show_message(
            self.manager,
            title="SYSTEM NOTICE",
            message="Main thrusters initialized.\nHyperdrive capacitor at 100% capacity.",
            ok_label="UNDERSTOOD",
        )

    def _launch_basic_confirmation(self):
        def on_yes():
            self.status_message = "Confirmation response: User selected [ENGAGE]!"
            self.status_color = (50, 220, 100)

        def on_no():
            self.status_message = "Confirmation response: User selected [HOLD]!"
            self.status_color = (255, 180, 50)

        show_confirmation(
            self.manager,
            title="TACTICAL ENGAGEMENT",
            message="Enemy dreadnought in targeting range.\nEngage photon torpedoes?",
            confirm_label="ENGAGE",
            cancel_label="HOLD",
            on_confirm=on_yes,
            on_cancel=on_no,
        )

    def _launch_basic_multipage(self):
        pages = [
            {"title": "TACTICAL CODEX (1/3)", "message": "Shield frequency harmonics absorb 70% of energy blasts."},
            {"title": "TACTICAL CODEX (2/3)", "message": "Kinetic railguns bypass magnetic shielding entirely."},
            {"title": "TACTICAL CODEX (3/3)", "message": "Overcharging warp coils grants brief invulnerability."},
        ]

        def on_done():
            self.status_message = "MultiPage Dialog completed successfully!"
            self.status_color = (50, 220, 100)

        dlg = MultiPageDialog(pages=pages, on_complete=on_done)
        self.manager.show_overlay(dlg)

    def _launch_basic_custom(self):
        def pick(name):
            self.status_message = f"Custom Dialog selected: [{name}]"
            self.status_color = (135, 242, 255)

        actions = [
            ("Shields", lambda: pick("Shields")),
            ("Weapons", lambda: pick("Weapons")),
            ("Engines", lambda: pick("Engines")),
        ]
        show_dialog(
            self.manager,
            title="POWER ROUTING",
            message="Select primary subsystem for auxiliary reactor power routing:",
            actions=actions,
            button_layout="horizontal",
        )

    def _launch_limit_massive_message(self):
        paragraph = (
            "🚨 CRITICAL TELEMETRY STRESS REPORT 🚨\n"
            "Quantum sensors: ∇ × B = μ₀(J + ε₀ ∂E/∂t) ± ∞\n"
            "Hostile Dreadnought Signatures detected in Sector 0xDEADBEEF!\n"
            "Translation matrix: こんにちは世界 / مرحباً بك في الفضاء / Привет мир\n"
            "Bulkhead integrity degradation rate: 98.42% over nominal.\n"
        )
        massive_text = "\n".join([f"[{i:02d}] {paragraph}" for i in range(15)])
        show_message(self.manager, title="LIMIT: MASSIVE TEXT & UNICODE 🌌", message=massive_text)

    def _launch_limit_verbose_confirm(self):
        show_confirmation(
            self.manager,
            title="LIMIT: VERBOSE CONFIRMATION",
            message="Extreme core temperature excursion detected across containment sectors 1 through 12.\n"
                    "Executing thermal flush will purge all auxiliary capacitors immediately.",
            confirm_label="INITIATE EMERGENCY THERMAL FLUSH OVERRIDE PROCEDURE",
            cancel_label="ABORT FLUSH AND ATTEMPT MANUAL RECOVERY",
            button_layout="vertical",
        )

    def _launch_limit_100_pages(self):
        pages = [
            {
                "title": f"LOG ARCHIVE {idx + 1:03d}/100",
                "message": f"Deep space survey log record index #{idx + 1}.\n"
                           f"Star system: HD-{idx * 137} | Coordinates: [{idx}, {idx * 2}, {idx * 3}]\n"
                           f"Stellar radiation level: nominal.",
            }
            for idx in range(100)
        ]
        dlg = MultiPageDialog(pages=pages)
        self.manager.show_overlay(dlg)

    def _launch_limit_buttons_overload(self):
        actions = [(f"System {idx + 1:02d}", None) for idx in range(30)]
        show_dialog(
            self.manager,
            title="LIMIT: 30-BUTTON OVERLOAD",
            message="Stress testing vertical layout with 30 distinct action items:",
            actions=actions,
            button_layout="vertical",
        )

    def _run_headless_basic(self):
        self.status_message = "Running Headless Basic Suite..."
        t_start = time.perf_counter()
        success = run_basic_tests(dialog_filter="all", verbose=False)
        dt = time.perf_counter() - t_start
        if success:
            self.status_message = f"Basic Suite: ALL PASSED in {dt:.3f}s"
            self.status_color = (50, 220, 100)
        else:
            self.status_message = f"Basic Suite: FAILURES DETECTED ({dt:.3f}s)"
            self.status_color = (255, 80, 80)

    def _run_headless_limit(self):
        self.status_message = "Running Headless Limit Suite..."
        t_start = time.perf_counter()
        success = run_limit_tests(dialog_filter="all", verbose=False)
        dt = time.perf_counter() - t_start
        if success:
            self.status_message = f"Limit Suite: ALL PASSED in {dt:.3f}s"
            self.status_color = (50, 220, 100)
        else:
            self.status_message = f"Limit Suite: FAILURES DETECTED ({dt:.3f}s)"
            self.status_color = (255, 80, 80)

    def _run_headless_all(self):
        self.status_message = "Running All Headless Suites..."
        t_start = time.perf_counter()
        success = run_all_tests(dialog_filter="all", verbose=False)
        dt = time.perf_counter() - t_start
        if success:
            self.status_message = f"All Suites: ALL PASSED in {dt:.3f}s"
            self.status_color = (50, 220, 100)
        else:
            self.status_message = f"All Suites: FAILURES DETECTED ({dt:.3f}s)"
            self.status_color = (255, 80, 80)

    def _exit_harness(self):
        if self.manager and hasattr(self.manager, "has_previous_scene") and self.manager.has_previous_scene():
            self.manager.pop_scene()
        else:
            pygame.quit()
            sys.exit(0)

    # --- Event & Render Handling ---

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._exit_harness()
                return
            elif event.key == pygame.K_F1:
                self._run_headless_basic()
                return
            elif event.key == pygame.K_F2:
                self._run_headless_limit()
                return
            elif event.key == pygame.K_F3:
                self._run_headless_all()
                return
            elif event.key in (pygame.K_1, pygame.K_KP1):
                self._launch_basic_message()
                return
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self._launch_basic_confirmation()
                return
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self._launch_basic_multipage()
                return
            elif event.key in (pygame.K_4, pygame.K_KP4):
                self._launch_basic_custom()
                return
            elif event.key in (pygame.K_5, pygame.K_KP5):
                self._launch_limit_massive_message()
                return
            elif event.key in (pygame.K_6, pygame.K_KP6):
                self._launch_limit_verbose_confirm()
                return
            elif event.key in (pygame.K_7, pygame.K_KP7):
                self._launch_limit_100_pages()
                return
            elif event.key in (pygame.K_8, pygame.K_KP8):
                self._launch_limit_buttons_overload()
                return

            # Navigation
            num_btns = len(self.buttons)
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % num_btns
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % num_btns
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_index = (self.selected_index - 1) % num_btns
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_index = (self.selected_index + 1) % num_btns
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if 0 <= self.selected_index < num_btns:
                    cb = self.buttons[self.selected_index].get("callback")
                    if callable(cb):
                        cb()

        elif event.type == pygame.MOUSEMOTION or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            # Hit test buttons
            for idx, btn in enumerate(self.buttons):
                rect = btn.get("_rect")
                if rect and rect.collidepoint(event.pos):
                    self.selected_index = idx
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        cb = btn.get("callback")
                        if callable(cb):
                            cb()
                    break

    def update(self, dt: float = 1.0):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill((10, 14, 24))
        sw, sh = screen.get_size()

        title_font = get_dialog_font("title", 24)
        header_font = get_dialog_font("title", 16)
        btn_font = get_dialog_font("body", 16)
        status_font = get_dialog_font("body", 15)

        # Header Title
        if title_font:
            title_surf = title_font.render("GALACTIC SPACE REBORN - DIALOG TEST HARNESS", True, (135, 242, 255))
            screen.blit(title_surf, title_surf.get_rect(center=(sw // 2, 45)))

        # Subtitle
        if header_font:
            sub_surf = header_font.render("Basic Functional Tests  vs  Push-To-The-Limit Stress Tests", True, (160, 180, 205))
            screen.blit(sub_surf, sub_surf.get_rect(center=(sw // 2, 80)))

        # Section Header Columns
        col1_x = 70
        col2_x = sw // 2 + 30
        col_w = sw // 2 - 100
        start_y = 120

        if header_font:
            h1 = header_font.render("[ BASIC DIALOG TESTS ]", True, (80, 220, 140))
            screen.blit(h1, (col1_x + 10, start_y))

            h2 = header_font.render("[ PUSH-TO-THE-LIMIT TESTS ]", True, (255, 130, 80))
            screen.blit(h2, (col2_x + 10, start_y))

        # Render test action buttons
        btn_h = 44
        y_spacing = 54
        base_y = start_y + 35

        for idx, btn in enumerate(self.buttons):
            col = btn["col"]
            row = btn["row"]
            bx = col1_x if col == 0 else col2_x
            by = base_y + row * y_spacing

            # Extra offset before runners
            if btn["category"] == "RUNNER" and row == 4:
                by += 20
            elif btn["category"] == "RUNNER" and row == 5:
                by += 20

            rect = pygame.Rect(bx, by, col_w, btn_h)
            btn["_rect"] = rect

            is_sel = (idx == self.selected_index)
            cat = btn["category"]

            if is_sel:
                border_c = (135, 242, 255)
                bg_c = (35, 55, 80)
                text_c = (255, 255, 255)
            else:
                if cat == "BASIC":
                    border_c = (50, 140, 90)
                    bg_c = (18, 32, 26)
                elif cat == "LIMIT":
                    border_c = (160, 70, 50)
                    bg_c = (34, 20, 20)
                else:
                    border_c = (60, 80, 110)
                    bg_c = (20, 28, 42)
                text_c = (200, 215, 230)

            pygame.draw.rect(screen, bg_c, rect, border_radius=6)
            pygame.draw.rect(screen, border_c, rect, width=2 if is_sel else 1, border_radius=6)

            if btn_font:
                prefix = "> " if is_sel else "  "
                label = btn_font.render(prefix + btn["text"], True, text_c)
                screen.blit(label, (rect.x + 16, rect.centery - label.get_height() // 2))

        # Status Bar at Bottom
        status_rect = pygame.Rect(70, sh - 75, sw - 140, 48)
        pygame.draw.rect(screen, (16, 22, 34), status_rect, border_radius=6)
        pygame.draw.rect(screen, (45, 60, 85), status_rect, width=1, border_radius=6)

        if status_font:
            status_surf = status_font.render(f"STATUS: {self.status_message}", True, self.status_color)
            screen.blit(status_surf, (status_rect.x + 16, status_rect.centery - status_surf.get_height() // 2))


# ============================================================================
# 4. PROGRAMMATIC & CLI RUNNERS
# ============================================================================

def _filter_test_methods(test_case_class: type, dialog_filter: str) -> list[str]:
    """Returns method names of test_case_class matching the dialog type filter."""
    dialog_map = {
        "message": ["message"],
        "confirmation": ["confirmation"],
        "multipage": ["multipage"],
        "custom": ["custom"],
        "all": ["message", "confirmation", "multipage", "custom", "helper", "overlay"],
    }
    keywords = dialog_map.get(dialog_filter.lower(), dialog_map["all"])

    matched: list[str] = []
    for attr in dir(test_case_class):
        if attr.startswith("test_"):
            if any(kw in attr.lower() for kw in keywords):
                matched.append(attr)
    return matched


def run_basic_tests(dialog_filter: str = "all", verbose: bool = True) -> bool:
    """Executes the Basic Dialog Test Suite."""
    ensure_headless_display()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    methods = _filter_test_methods(BasicDialogTests, dialog_filter)
    for m in methods:
        suite.addTest(BasicDialogTests(m))

    if verbose:
        print("\n" + "=" * 60)
        print(f"RUNNING BASIC DIALOG TESTS [Filter: {dialog_filter.upper()}] ({suite.countTestCases()} tests)")
        print("=" * 60)

    runner = unittest.TextTestRunner(verbosity=2 if verbose else 0)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_limit_tests(dialog_filter: str = "all", verbose: bool = True) -> bool:
    """Executes the Push-to-the-Limit Dialog Test Suite."""
    ensure_headless_display()
    suite = unittest.TestSuite()

    methods = _filter_test_methods(LimitDialogTests, dialog_filter)
    for m in methods:
        suite.addTest(LimitDialogTests(m))

    if verbose:
        print("\n" + "=" * 60)
        print(f"RUNNING PUSH-TO-THE-LIMIT DIALOG TESTS [Filter: {dialog_filter.upper()}] ({suite.countTestCases()} tests)")
        print("=" * 60)

    runner = unittest.TextTestRunner(verbosity=2 if verbose else 0)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_all_tests(dialog_filter: str = "all", verbose: bool = True) -> bool:
    """Executes both the Basic and Push-to-the-Limit Test Suites sequentially."""
    basic_ok = run_basic_tests(dialog_filter=dialog_filter, verbose=verbose)
    limit_ok = run_limit_tests(dialog_filter=dialog_filter, verbose=verbose)

    if verbose:
        print("\n" + "=" * 60)
        print("FINAL TEST SUMMARY")
        print(f"  - Basic Test Suite:           {'PASSED [OK]' if basic_ok else 'FAILED [X]'}")
        print(f"  - Push-To-The-Limit Suite:    {'PASSED [OK]' if limit_ok else 'FAILED [X]'}")
        print("=" * 60)

    return basic_ok and limit_ok


def start_interactive_harness():
    """Starts the interactive GUI test harness scene inside a live Pygame window."""
    pygame.init()
    screen = pygame.display.set_mode((config.Screen.Size.w, config.Screen.Size.h))
    pygame.display.set_caption("Galactic Space Reborn - Dialog Test Harness")

    clock = pygame.time.Clock()
    manager = SceneManager(screen)
    manager.set_scene(DialogTestScene(), fade=False)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            manager.handle_event(event)

        manager.update(dt)
        manager.draw(screen)
        pygame.display.flip()

    pygame.quit()


# ============================================================================
# 5. CLI ENTRYPOINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Galactic Space Reborn Dialog Test Suite (Basic & Push-to-the-Limit)"
    )
    parser.add_argument(
        "-s", "--suite",
        choices=["basic", "limit", "all"],
        default="all",
        help="Specify which test suite to execute (default: all)"
    )
    parser.add_argument(
        "-d", "--dialog",
        choices=["message", "confirmation", "multipage", "custom", "all"],
        default="all",
        help="Filter tests by specific dialog type (default: all)"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch the visual interactive GUI test scene"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Run tests in quiet mode with minimal output"
    )

    args = parser.parse_args()

    if args.interactive:
        start_interactive_harness()
        return

    verbose = not args.quiet
    if args.suite == "basic":
        success = run_basic_tests(dialog_filter=args.dialog, verbose=verbose)
    elif args.suite == "limit":
        success = run_limit_tests(dialog_filter=args.dialog, verbose=verbose)
    else:
        success = run_all_tests(dialog_filter=args.dialog, verbose=verbose)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
