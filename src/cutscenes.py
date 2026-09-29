import pygame
import sys
from . import assets
from . import states
from . import animation


def run_invincibility_cutscene(player):
    """
    Handles the pre-gameplay charge-up cutscene using the engine's asset pipeline.
    """
    cutscene_duration = 2.312
    elapsed_time = 0.0

    screen = pygame.display.get_surface()
    cutscene_clock = pygame.time.Clock()

    # Grab the preloaded sheet directly from your Textures container!
    # (Make sure to update frame_width/frame_height to match your actual sheet dimensions)
    sheet_surface = assets.Textures.invincibility_charge

    charge_anim = animation.SpriteSheetAnimation(
        sheet=assets.Textures.invincibility_charge,
        frame_width=32,  # The width of the actual ship graphic you want to cut
        frame_height=16,
        duration=cutscene_duration,
        scale_factor=6,
        stride_x=32,
        # <--- Change this to the actual distance (in pixels) between the start of each frame cell on the sheet!
        max_frames=25
    )

    # Play music using your asset module's references
    pygame.mixer.music.load(assets.Music.invincibility_full_draft)
    pygame.mixer.music.play()

    while elapsed_time < cutscene_duration:
        dt = cutscene_clock.tick(60) / 1000.0
        elapsed_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

        if screen is not None:
            screen.fill((0, 0, 0))
            screen_rect = screen.get_rect()

            # Render current animation frame centered on screen
            current_frame = charge_anim.get_frame(elapsed_time)
            if current_frame:
                frame_rect = current_frame.get_rect(center=screen_rect.center)
                screen.blit(current_frame, frame_rect)

            # Final frame whiteout flash right before gameplay drops
            progress = min(1.0, elapsed_time / cutscene_duration)
            if progress >= 0.98:
                flash_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                alpha_val = int(((progress - 0.98) / 0.02) * 255)
                flash_surf.fill((255, 255, 255, alpha_val))
                screen.blit(flash_surf, (0, 0))

            pygame.display.flip()

    player.invincible = True
    states.powerup_active = True
    states.powerup_timer = 15.5
    states.powerup_type_text = "Invincibility"