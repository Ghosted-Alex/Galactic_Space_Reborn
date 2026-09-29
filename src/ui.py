"""User Interface Module"""

import ast

import pygame

import config
from . import assets
from . import states
from . import stats


def eval_safe_coordinate(expression, default_value=0) -> int:
    """
    Safely resolves integers, floats, or formulas referencing config.py values.
    Natively prevents arbitrary code lines from executing.
    """
    if isinstance(expression, (int, float)):
        return int(expression)

    if not isinstance(expression, str):
        return default_value

    try:
        # Parse the coordinate math equation string into an isolated expression tree node
        node = ast.parse(expression, mode='eval')

        def _resolve(n):
            if isinstance(n, ast.Expression):
                return _resolve(n.body)
            elif isinstance(n, ast.Constant):
                return n.value
            elif isinstance(n, ast.BinOp):
                # Handle standard arithmetic operators securely
                left = _resolve(n.left)
                right = _resolve(n.right)
                if isinstance(n.op, ast.Add): return left + right
                if isinstance(n.op, ast.Sub): return left - right
                if isinstance(n.op, ast.Mult): return left * right
                if isinstance(n.op, ast.Div): return left / right
            elif isinstance(n, ast.Attribute):
                # Unpack and map attributes out backward (e.g. config.Screen.Size.w)
                parts = []
                curr = n
                while isinstance(curr, ast.Attribute):
                    parts.append(curr.attr)
                    curr = curr.value
                if isinstance(curr, ast.Name):
                    parts.append(curr.id)
                parts.reverse()

                # CORRECT CHECK: Target the first string element inside the unpacked path array!
                if parts and parts[0] == 'config':
                    obj = config
                    # Recurse down your configuration sub-classes properties maps dynamically
                    for part in parts[1:]:
                        obj = getattr(obj, part)
                    return float(obj) if isinstance(obj, (int, float)) else 0
            raise ValueError("Unsafe token expression blocked inside coordinate string layout.")

        return int(_resolve(node))
    except Exception as err:
        print(f"[UI Sandbox] Error parsing coordinate configuration equation: {err}")
        return default_value


# Modding registry for custom UI elements, populated dynamically by behavioral UI mixins
_CUSTOM_UI_REGISTRY = {"CUSTOM_TEXT": {}}

def register_custom_text(text_id: str, text: str, x: int | str = 0, y: int | str = 0, color: tuple[int, int, int] = (255, 255, 255)):
    """Registers a custom text element to be rendered on the HUD."""
    _CUSTOM_UI_REGISTRY["CUSTOM_TEXT"][text_id] = {
        "text": text,
        "x": x,
        "y": y,
        "color": color
    }

def clear_custom_ui():
    """Clears all registered custom UI elements."""
    _CUSTOM_UI_REGISTRY["CUSTOM_TEXT"].clear()

def draw_game_over_ui(screen):
    # 1. Create a temporary screen with the same size as the screen
    overlay = pygame.Surface((config.Screen.Size.w, config.Screen.Size.h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    # Cap values for display safety
    display_score = min(int(stats.score), 1000000)
    display_high_score = min(int(stats.high_score), 1000000)

    # 2. ONE-TIME SAVE LOGIC (Only runs the very first frame the game over screen appears)
    if not states.game_over_ui_shown:
        states.game_over_ui_shown = True

        # Check if they actually beat the record
        if display_score > display_high_score:
            print(f"High Score Achieved! New: {display_score}, Old: {display_high_score}")
            stats.high_score = stats.score
            display_high_score = display_score # Update local display variable for this frame

            # Save to file safely (Write mode 'w', not Read mode 'r'!)
            with open(config.HIGH_SCORE_FILE, "w") as file:
                file.write(str(stats.high_score))
        else:
            print(f"Regular Score (Score: {display_score}, Hi Score: {display_high_score})")

    # 3. RENDER TEXT SURFACES (Runs every frame to keep the text on screen)
    # Check against the OLD high score states to determine if we show the yellow banner
    if display_score > display_high_score or (stats.score == stats.high_score and display_score > 0):
        # If they just beat it, or if it's currently equal because we just updated it above
        score_go_str = assets.pressStart2P.render("New High Score!", True, (255, 180, 0))
    else:
        score_go_str = assets.pressStart2P.render(f"SCORE: {display_score:07d}", True, (255, 255, 255))

    hi_score_go_str = assets.pressStart2P.render(f"HIGH SCORE: {display_high_score:07d}", True, (255, 255, 255))

    ins_reset = assets.pressStart2P.render(f"Press \"{pygame.key.name(config.KeyBinds.General.reset, False)}\" to Reset Game", True, (255, 255, 255))
    ins_quit = assets.pressStart2P.render(f"Press \"{pygame.key.name(config.KeyBinds.General.escape, False)}\" to go back\nto title", True, (255, 255, 255))

    game_over_str = assets.pressStart2P.render('GAME OVER!', True, (251, 242, 54))

    # 4. Draw the UI elements on top
    screen.blit(game_over_str, (config.Screen.Size.w/2-game_over_str.width/2, 225))
    screen.blit(score_go_str, (config.Screen.Size.w/2-score_go_str.width/2, 275))
    screen.blit(hi_score_go_str, (config.Screen.Size.w/2-hi_score_go_str.width/2, 315))
    screen.blit(ins_reset, (config.Screen.Size.w/2-ins_reset.width/2, 500))
    screen.blit(ins_quit, (config.Screen.Size.w/2-ins_quit.width/2, 600))

def draw_panel_ui(screen, player):
    panel_rect = assets.Textures.panel_02.get_rect(topleft=(config.Screen.Size.w-246, config.Screen.Size.h-195))

    # Replace that whole 'for i in range(2)' block with this:
    if states.blink_timer < 60:
        # This checks if the timer is in the first or second half of a 30-frame cycle
        if (states.blink_timer // 15) % 2 == 0:
            config.background_energy_color  = (166, 51, 51) # Red
        else:
            config.background_energy_color  = (15, 15, 15)  # Dark
    else:
        config.background_energy_color  = (15, 15, 15) # Default Dark

    if states.health_blink_timer < 60:
        # This checks if the timer is in the first or second half of a 30-frame cycle
        if (states.health_blink_timer // 15) % 2 == 0:
            config.health_color_high = (255, 255, 255) # White
            config.health_color_low = (255, 255, 255) # White
            config.health_color_med = (255, 255, 255) # White
            config.health_color_drain = (135, 242, 255) # Drain Color (Cyan)
            config.background_health_color = (204, 53, 53) # Red
        else:
            if player.invincible == True and states.powerup_active == True:
                config.health_color_high = (219, 157, 0) # Invincible Health Color (Gold)
            else:
                config.health_color_high = (50, 168, 82) # High Health Color (Green)
            config.health_color_med = (255, 255, 0) # Medium Health Color (Yellow)
            config.health_color_low = (255, 0, 0) # Low Health Color (Red)
            config.health_color_drain = (135, 242, 255) # Drain Color (Cyan)
            config.background_health_color = (15, 15, 15)
    else:
        if player.invincible == True and states.powerup_active == True:
            config.health_color_high = (219, 157, 0) # Invincible Health Color (Gold)
        else:
            config.background_health_color = (15, 15, 15)
            config.health_color_high = (50, 168, 82) # High Health Color (Green)
            config.health_color_med = (255, 255, 0) # Medium Health Color (Yellow)
            config.health_color_low = (255, 0, 0) # Low Health Color (Red)
            # config.health_color_drain = (255, 0, 0) # Low Health Color (Red)
            config.health_color_drain = (135, 242, 255) # Drain Color (Cyan)

    timer_str = assets.pressStart2P.render(f"{states.powerup_type_text}: {states.powerup_timer}", True, (255,255,255))

    screen.blit(assets.Textures.panel_01, (0, config.Screen.Size.h-45))

    p02_hidden = False

    VISIBLE_X = config.Screen.Size.w - 246
    HIDDEN_X = config.Screen.Size.w
    # 1000000
    score_str = assets.pressStart2P.render(f"{stats.score:07d}", True, (255,255,255))
    high_score_str = assets.pressStart2P.render(f"{stats.high_score:07d}", True, (255,255,255))

    if player.rect.colliderect(panel_rect):
        # SLIDE TO HIDE
        if config.p02_pos[0] < HIDDEN_X:
            config.p02_pos[0] += 50
        else:
            config.p02_pos[0] = HIDDEN_X
            p02_hidden = True
    else:
        # SLIDE TO SHOW
        if config.p02_pos[0] > VISIBLE_X:
            config.p02_pos[0] -= 50
        else:
            config.p02_pos[0] = VISIBLE_X
            p02_hidden = False

    screen.blit(assets.Textures.panel_02, (config.p02_pos[0], config.p02_pos[1]))

    if p02_hidden == False:

        # 1. Get the current panel X from your config
        panel_x = config.p02_pos[0]

        # 2. Calculate text widths (do this after rendering)
        score_width = score_str.get_width()
        hi_score_width = high_score_str.get_width()

        # 3. Define the offset from the left edge of the panel
        # Example: 10 pixels from the left side of the panel
        text_offset_x = [20, 20] # [0] = Top, [1] = Bottom
        text_offset_y = [30, 97] # [0] = Top, [1] = Bottom

        # 4. Draw relative to panel_x
        # The Y values remain relative to the panel's top (config.p02_pos[1])
        screen.blit(score_str, (panel_x + text_offset_x[0], config.p02_pos[1] + text_offset_y[0]))
        screen.blit(high_score_str, (panel_x + text_offset_x[1], config.p02_pos[1] + text_offset_y[1]))

    # pygame.draw.rect(screen, (51, 255, 51), self.rect, 1)
    pygame.draw.rect(screen, config.background_health_color, (15, 826, 400, 25))

    pygame.draw.rect(screen, config.health_color_drain, (15, 826, player.health_drain*4, 25))

    if player.health > 50:
        pygame.draw.rect(screen, config.health_color_high, (15, 826, player.health*4, 25))
    if 50 >= player.health > 25:
        pygame.draw.rect(screen, config.health_color_med, (15, 826, player.health*4, 25))
    if player.health <= 25:
        pygame.draw.rect(screen, config.health_color_low, (15, 826, player.health*4, 25))

    if player.health_drain > player.health:
        player.health_drain -= .1
    elif player.health_drain < player.health:
        player.health_drain = player.health

    # 1. Background Bar (The gray slot)
    # Starts at 507, width 400 (507 + 400 = 907)
    pygame.draw.rect(screen, config.background_energy_color , (657, 826, 400, 25))

    # 2. The Draining Logic
    # We calculate the width first
    energy_width = player.energy * 4

    # To make it "reverse," we push the X-coordinate forward by the missing amount
    # 507 + (400 - energy_width)
    reverse_x = 657 + (400 - energy_width)

    # 3. Draw the Energy Bar (Yellow)
    if player.energy > 0:
        pygame.draw.rect(screen, config.energy_color, (reverse_x, 826, energy_width, 25))

    if player.health > 100:
        player.health = 100
    if player.energy > 100:
        player.energy = 100

    if states.powerup_timer > 0:
        if config.debug:
            screen.blit(timer_str, (20, 20))
