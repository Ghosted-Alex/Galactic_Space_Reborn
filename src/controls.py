"""Controls Module"""

import pygame

import config


def single_press(event: pygame.event.Event, key, input_type: str = "none") -> bool:
    """Checks if a specific key was pressed once (KEYDOWN)."""
    if event.type != pygame.KEYDOWN:
        return False
    if isinstance(key, (tuple, list)):
        return event.key in key

    return event.key == key


def repeat_press(key) -> bool | tuple[bool, ...]:
    """Checks if a key is currently held down."""

    keys = pygame.key.get_pressed()

    return keys[key]


def check_combo(event: pygame.event.Event, keys: list[int]) -> bool:
    """
    Checks if a specific combo was completed.

    Args:
        event: The current KEYDOWN event.
        keys: A list of key constants (e.g., [pygame.K_F12, pygame.K_1]).
        The last key in this list is treated as the 'trigger' key.
    """
    if event.type != pygame.KEYDOWN:
        return False

    # 1. Check if the trigger key (the last one in the list) is the one just pressed
    trigger_key = keys[-1]
    if event.key != trigger_key:
        return False

    # 2. Check if all other keys in the list are currently being held down
    pressed_keys = pygame.key.get_pressed()
    for key in keys[:-1]:
        if not pressed_keys[key]:
            return False

    return True


class ControllerInput:
    """Translates raw joystick events into named game actions for Xbox controllers.

    Every scene calls these static helpers instead of comparing raw button/hat values
    directly, keeping controller logic in one maintainable place.

    D-Pad uses JOYHATMOTION (hat 0). Buttons use JOYBUTTONDOWN.

    Xbox button layout (SDL2 / pygame default):
        A=0  B=1  X=2  Y=3  LB=4  RB=5  Back/View=6  Start=7  LS=8  RS=9
        Xbox-logo button = 8 on some drivers; omitted here as it is unreliable.

    D-Pad hat values:  up=(0,1)  down=(0,-1)  left=(-1,0)  right=(1,0)
    """

    # ------------------------------------------------------------------ #
    # Navigation — menus / UI                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def nav_up(event: pygame.event.Event) -> bool:
        """D-Pad up or left-stick up (hat motion only — use analog in update loops)."""
        if event.type == pygame.JOYHATMOTION and event.hat == 0:
            return event.value[1] == 1  # hat y +1 = up
        return False

    @staticmethod
    def nav_down(event: pygame.event.Event) -> bool:
        """D-Pad down."""
        if event.type == pygame.JOYHATMOTION and event.hat == 0:
            return event.value[1] == -1  # hat y -1 = down
        return False

    @staticmethod
    def nav_left(event: pygame.event.Event) -> bool:
        """D-Pad left — used for cycling option values."""
        if event.type == pygame.JOYHATMOTION and event.hat == 0:
            return event.value[0] == -1  # hat x -1 = left
        return False

    @staticmethod
    def nav_right(event: pygame.event.Event) -> bool:
        """D-Pad right — used for cycling option values."""
        if event.type == pygame.JOYHATMOTION and event.hat == 0:
            return event.value[0] == 1  # hat x +1 = right
        return False

    # ------------------------------------------------------------------ #
    # Confirm / Cancel                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def confirm(event: pygame.event.Event) -> bool:
        """A button — confirm/select the highlighted menu item."""
        return (
            event.type == pygame.JOYBUTTONDOWN
            and event.button == config.ControllerBindings.XboxController.BUTTON_A
        )

    @staticmethod
    def cancel(event: pygame.event.Event) -> bool:
        """B button — cancel / go back."""
        return (
            event.type == pygame.JOYBUTTONDOWN
            and event.button == config.ControllerBindings.XboxController.BUTTON_B
        )

    # ------------------------------------------------------------------ #
    # Gameplay actions                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def shoot(event: pygame.event.Event) -> bool:
        """A button (or RB) — fire a bullet during gameplay."""
        return (
            event.type == pygame.JOYBUTTONDOWN
            and event.button in (
                config.ControllerBindings.XboxController.BUTTON_A,
                config.ControllerBindings.XboxController.BUTTON_RB,
            )
        )

    # ------------------------------------------------------------------ #
    # System                                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def pause(event: pygame.event.Event) -> bool:
        """Start button OR Back/View (hamburger) button — open the pause menu.

        Both BUTTON_START (7) and BUTTON_BACK (6) trigger pause so players can
        use whichever feels natural.
        """
        return (
            event.type == pygame.JOYBUTTONDOWN
            and event.button in (
                config.ControllerBindings.XboxController.BUTTON_START,
                config.ControllerBindings.XboxController.BUTTON_BACK,
            )
        )

    # ------------------------------------------------------------------ #
    # Analog movement (called every frame in update loops, not events)    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_move_vector(deadzone: float = 0.15) -> tuple[float, float]:
        """Return the normalized (x, y) movement vector from the left analog stick.

        Returns (0.0, 0.0) when no joystick is connected or the stick is within
        the deadzone, so callers never have to guard against missing hardware.
        """
        if pygame.joystick.get_count() == 0:
            return 0.0, 0.0
        try:
            joystick = pygame.joystick.Joystick(0)
            x = joystick.get_axis(config.ControllerBindings.XboxController.AXIS_LEFT_X)
            y = joystick.get_axis(config.ControllerBindings.XboxController.AXIS_LEFT_Y)
            if abs(x) < deadzone:
                x = 0.0
            if abs(y) < deadzone:
                y = 0.0
            return x, y
        except pygame.error:
            return 0.0, 0.0

    @staticmethod
    def get_dpad_move(event: pygame.event.Event) -> tuple[int, int]:
        """Return a discrete (dx, dy) movement vector from D-Pad hat events.

        Returns (0, 0) when the event is not a hat motion.
        Note: pygame hat y-axis is +1 for up, so we negate it to match screen coords.
        """
        if event.type == pygame.JOYHATMOTION and event.hat == 0:
            hat_x, hat_y = event.value
            return hat_x, -hat_y  # flip y so +dy = moving down on screen
        return 0, 0

    @staticmethod
    def get_dpad_vector() -> tuple[int, int]:
        """Returns the current held (dx, dy) direction of the D-Pad hat.

        Returns (0, 0) when no joystick is connected or D-Pad is centered.
        Flips y so that +dy is moving downwards on screen.
        """
        if pygame.joystick.get_count() == 0:
            return 0, 0
        try:
            joystick = pygame.joystick.Joystick(0)
            if joystick.get_numhats() > 0:
                hat_x, hat_y = joystick.get_hat(0)
                return hat_x, -hat_y
        except pygame.error:
            pass
        return 0, 0