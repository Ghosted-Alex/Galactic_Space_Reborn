"""Events Module — Overridable game loop functions exposed to people who forks the project"""

import random
import pygame
import config
import traceback
import datetime
from pathlib import Path

from typing import NoReturn

from . import entity
from . import bullet
from . import powerup
from . import assets
from . import stats
from . import states
from . import animation
from . import logger

# =============================================================================
# SPAWNING events
# =============================================================================

def spawn_enemy(enemies: list) -> None:
    """Spawns a new enemy and appends it to the active enemies list.

    Override this to change enemy types, spawn positions, spawn rates,
    formations, or turn the game into something like Space Invaders entirely.

    Args:
        enemies: The live enemies list from the game loop.
    """
    enemy_chance = random.randint(0, 2 if states.difficulty >= 1.0 else 1)
    shield = (enemy_chance == 2) if states.difficulty >= 1.0 else False

    new_enemy = entity.Enemy(1000, random.randint(48, config.Screen.Size.h - 48), enemy_chance, shield=shield)
    enemies.append(new_enemy)


def spawn_powerup(chance: int, player, powerups: list) -> None:
    """Evaluates a chance roll and conditionally spawns a powerup.

    Override this to change drop rates, add new powerup types, or make
    drops context-sensitive in completely different ways.

    Args:
        chance: A random integer (1-100) rolled by the game loop.
        player: The live Player instance.
        powerups: The live powerups list from the game loop.
    """
    # Health Wrench -- 15% base chance when player isn't full health
    if not states.powerup_active and player.health <= 95 and 1 <= chance <= 15:
        print("Wrench powerup Summoned!")
        new_powerup = powerup.Spawn(1000, random.randint(48, config.Screen.Size.h-48), 0)
        powerups.append(new_powerup)

    # Energy Cell -- 10% base chance when player isn't full energy
    elif not states.powerup_active and player.energy <= 95 and 16 <= chance <= 25:
        print("Energy powerup Summoned!")
        new_powerup = powerup.Spawn(1000, random.randint(48, 816), 2)
        powerups.append(new_powerup)

    # Power Wrench (Invincibility) -- 5% flat chance, only if no powerup is active
    elif not states.powerup_active and 50 <= chance <= 55:
        print("Power Wrench powerup Summoned!")
        new_powerup = powerup.Spawn(1000, random.randint(48, 816), 1)
        powerups.append(new_powerup)


# =============================================================================
# PLAYER ACTION events
# =============================================================================

def on_shoot(player, effects: list, bullets: list) -> bool:
    """Called when the player attempts to fire a bullet.

    Override this to change bullet type, cost, count, spread, cooldown,
    or any other shoot behavior.

    Args:
        player: The live Player instance.
        bullets: The live bullets list from the game loop.
        effects: The live shooting animation

    Returns:
        True if a bullet was successfully fired, False if energy was too low.
    """
    if player.energy > 5:
        # Create bullet
        new_bullet = bullet.Normal(player.rect.centerx, player.rect.centery)
        bullets.append(new_bullet)
        
        # Create and add effect slightly in front of the player
        # Adjust '+ 20' to match your player width
        new_effect = animation.ShootEffect(player.rect.right-10, player.rect.centery+10)
        effects.append(new_effect)
        
        assets.Sounds.player_shoot.play()
        player.energy -= 5
        return True
    else:
        pygame.mixer.Sound.play(assets.Sounds.fail)
        states.blink_timer = 0
        return False


# =============================================================================
# SCORING events
# =============================================================================

def on_score_increment(amount: int = 1) -> None:
    """Called every time the score should increase.

    Override this to multiply scores, add combo bonuses, clamp differently,
    or route score changes to an external system.

    Args:
        amount: How much to add to the score (default: 1).
    """
    stats.score += amount


# =============================================================================
# HIGH SCORE I/O events
# =============================================================================

def save_high_score(score: int, path) -> None:
    """Saves the high score to disk.

    Override this to change the save location, file format (e.g. JSON),
    or add a remote leaderboard write.

    Args:
        score: The score value to persist.
        path:  The target file path (pathlib.Path or str).
    """
    with open(path, "w") as file:
        file.write(str(score))
    print(f"[events] High score saved: {score} -> {path}")


def load_high_score(path) -> int:
    """Loads the high score from disk.

    Override this to change the load source, file format, or pull from
    a remote leaderboard instead.

    Args:
        path: The source file path (pathlib.Path or str).

    Returns:
        The loaded high score as an integer.
    """
    with open(path, "r") as file:
        return int(file.read().strip())


# =============================================================================
# GAME STATE events
# =============================================================================

def on_crash(e) -> NoReturn:
    crash_comments = [
        "# Shields down, captain!",
        "# That wasn't a meteor...",
        "# Houston, we have a fatal crash!.",
        "# Target locked onto an IndexError.",
        "# The hyperspace drive just divided by zero.",
        "# Nav-computer outputted NaN instead of coordinates.",
        "# Laser inventory overflow! Evacuate the module!",
        "# Hull breach detected in the main event loop.",
        "# Alien malware detected in the asset loader.",
        "# Engines fired backwards. Oops.",
        "# The mothership didn't like that trajectory.",
        "# Lost tracking on enemy ship #404.",
        "# Reactor core melted. Who turned off the cooling fan?",
        "# We forgot to attach a hitbox to the asteroid.",
        "# Subspace communication array disconnected abruptly.",
        "# Tachyon particles interfered with the Python interpreter.",
        "# Gravity well too strong. Escape velocity failed.",
        "# Autopilot is currently asleep at the wheel.",
        "# That's a lot of bullets on screen.",
    ]

    crash_comment = crash_comments[random.randint(0, len(crash_comments)-1)]

    # Format the traceback string
    error_trace = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    
    # Write to a log file (similar to Minecraft crash logs)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = logs_dir / f"crash-{timestamp}.log"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write("--- Galactic Space Reborn Crash Report ---\n")
        f.write(f"{crash_comment}\n")
        f.write(f"Time: {timestamp}\n")
        f.write(f"Description: {e}\n\n")
        f.write("A detailed walkthrough of the error, its code path and all known details is as follows:\n")
        f.write(error_trace)

    logger.engine_log.critical(e)

    print(f"--- Galactic Space Reborn Crash Report ---\n{crash_comment}\nTime: {timestamp}\nDescription: {e}\n\nA detailed walkthrough of the error, its code path and all known details is as follows:\n{error_trace}")

def on_game_over() -> None:
    """Called when the player's health reaches zero.

    Override this to change death behavior -- play a different sound,
    trigger a cutscene, delay the game-over screen, add a revival mechanic,
    or anything else.
    """
    print("Game Over!")
    assets.Sounds.player_death.play()
    states.game_over = True
