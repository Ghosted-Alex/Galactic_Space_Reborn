"""Module for Entities"""

import pygame

from . import assets
from . import states
from .controls import ControllerInput

import config
from . import logger

class Player:
    """Instance Class for player"""
    def __init__(self, x: int, y: int, color: int = 0):
        self.x = x
        self.y = y
        self.speed = 8
        self.health = 100
        self.health_drain = 100
        self.energy = 100
        self.texture = None
        self.invincible = False
        self.color = color

        hitbox_width = 16
        hitbox_height = 16

        # Logic to pick texture based on the 'color' (color/type) argument
        if self.color == 0:
            self.texture = assets.Textures.player0
            print("Texture Set Blue")
        else:
            self.texture = assets.Textures.player_blank
            print("Texture Set None")

        print(self.texture)

        # Full image rect (used for rendering / positioning)
        self.rect = self.texture.get_rect(center=(self.x, self.y))

        self.hitbox = self.rect.inflate(-hitbox_width, -hitbox_height)
        
    def draw(self, surface):
        """Blits the player texture\n
        Draws a green hitbox rectangle (if debug mode is on)"""
        # Draw the actual ship sprite
        surface.blit(self.texture, self.rect)
        
        # Draws green outline around the active collision hitbox, also draws gray outline around the active image rect
        if config.debug:
            pygame.draw.rect(surface, (51, 255, 51), self.hitbox, 1)
            pygame.draw.rect(surface, (109, 109, 109), self.rect, 1)

    # In player.py -> handle_input
    def handle_input(self, keys, controller=None, event: pygame.event.Event = None):
        # 1. Keyboard fallback inputs
        up = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_i] or keys[pygame.K_o]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN] or keys[pygame.K_k]
        left = keys[pygame.K_a] or keys[pygame.K_LEFT] or keys[pygame.K_j]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT] or keys[pygame.K_l]

        # 2. Apply Keyboard Movement
        if up:
            self.rect.y -= self.speed
        if down:
            self.rect.y += self.speed
        if left:
            self.rect.x -= self.speed
        if right:
            self.rect.x += self.speed

        # 3. Apply Controller Analog Stick & D-Pad Movement if connected
        if controller:
            move_x, move_y = controller.get_move_vector()
            self.rect.x += int(move_x * self.speed)
            self.rect.y += int(move_y * self.speed)

        # Apply controller continuous D-Pad and analog movement via ControllerInput
        dpad_x, dpad_y = ControllerInput.get_dpad_vector()
        if dpad_x != 0 or dpad_y != 0:
            self.rect.x += dpad_x * self.speed
            self.rect.y += dpad_y * self.speed
        elif not controller:
            # Fallback to analog stick via ControllerInput if controller wasn't passed explicitly
            stick_x, stick_y = ControllerInput.get_move_vector()
            if stick_x != 0 or stick_y != 0:
                self.rect.x += int(stick_x * self.speed)
                self.rect.y += int(stick_y * self.speed)

        # 4. Apply Controller D-Pad discrete event movement if passed
        if event is not None:
            edpad_x, edpad_y = ControllerInput.get_dpad_move(event)
            self.rect.x += edpad_x * self.speed
            self.rect.y += edpad_y * self.speed

        # 5. Boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > config.Screen.Size.w:
            self.rect.right = config.Screen.Size.w
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > config.Screen.Size.h - 45:
            self.rect.bottom = config.Screen.Size.h - 45

        # 6. Keep the collision hitbox locked to the ship's center after movement/clamping
        self.hitbox.center = self.rect.center

    def update_appearance(self):
        color = None

        if self.invincible:
            self.texture = assets.Textures.player_variant_invincible
        else:
            if self.color == 0:
                self.texture = assets.Textures.player0
                color = "Blue"
            else:
                self.texture = assets.Textures.player_blank
            
            logger.engine_log.critical(f"Texture Set {color}")

class Enemy:
    def __init__(self, x: int, y: int, enemy_type: int, shield: bool = False):
        self.x = x
        self.y = y
        self.start_y = y # Store the initial Y for wave patterns
        self.enemy_type = enemy_type
        self.isAlive = True
        self.shield = shield
        self.difficulty = states.difficulty

        # {"name": "EASY", "texture": "difficulty0", "multiplier": 0.75, "color": (70, 160, 255)}
        # {"name": "NORMAL", "texture": "difficulty1", "multiplier": 1.0, "color": (60, 220, 200)}
        # {"name": "MEDIUM", "texture": "difficulty2", "multiplier": 1.25, "color": (60, 210, 90)}
        # {"name": "HARD", "texture": "difficulty3", "multiplier": 1.5, "color": (245, 210, 45)}
        # {"name": "INSANE", "texture": "difficulty4", "multiplier": 1.75, "color": (255, 140, 35)}
        # {"name": "GALACTIC", "texture": "difficulty5", "multiplier": 2.0, "color": (255, 65, 65)}

        if self.enemy_type == 0:
            self.image = assets.Textures.enemy0
            if 0.75 <= self.difficulty <= 1.25:
                self.health = 1
            elif 1.5 <= self.difficulty <= 1.75:
                self.health = 2
                self.enemy_type = 2
                self.shield = True
            elif self.difficulty == 2:
                self.health = 3
                self.enemy_type = 2
                self.shield = True

        if self.enemy_type == 1:
            self.image = assets.Textures.enemy1
            if 0.75 <= self.difficulty <= 1.25:
                self.health = 1
            elif 1.5 <= self.difficulty <= 1.75:
                self.health = 2
                self.enemy_type = 2
                self.shield = True
            elif self.difficulty == 2:
                self.health = 3
                self.enemy_type = 2
                self.shield = True

        if self.enemy_type == 2:
            self.image = assets.Textures.enemy0
            if self.difficulty <= 1.25:
                self.health = 3
            elif 1.5 <= self.difficulty <= 1.75:
                self.health = 5
            elif self.difficulty == 2:
                self.health = 7

        print(f"{self.enemy_type} summoned with health {self.health}")

        hitbox_width = 16
        hitbox_height = 16

        # Full image rect (used for rendering / positioning)
        self.rect = self.image.get_rect(center=(self.x, self.y))

        self.hitbox = self.rect.inflate(-hitbox_width, -hitbox_height)
        
        self.max_health = self.health
        
        # Unique attributes based on type
        self.speed = 3 if enemy_type == 0 else 5
        self.angle = 0 # Used for math-based movement

    def move(self):
        """Updates position based on enemy_type"""
        if self.enemy_type == 0: # Standard Grunt
            self.x -= self.speed

        elif self.enemy_type == 1: # The "Fast Diver"
            self.x -= self.speed + 4
            # Slight drift towards center
            if self.y < 400: self.y += 1
            else: self.y -= 1

        elif self.enemy_type == 2: # The "Waver" (Sine Wave) - Also includes Health so it takes more than 1 shot to kill
            self.x -= self.speed - 1
            self.angle += 0.1
            # Move side-to-side using a sine wave
            self.y = self.start_y + config.math.sin(self.angle) * 50

    def update(self):
        # Call move and then update the rect
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        if self.enemy_type == 0:
            img = pygame.transform.flip(self.image, True, False)
        elif self.enemy_type == 2:
            img = pygame.transform.flip(self.image, True, False)
        else:
            img = self.image
        
        self.shield_image = assets.Textures.shield
        
        if self.shield:
            shield_rect = assets.Textures.shield.get_rect(
                right=self.rect.left + 5, # Slightly overlapping the left side
                centery=self.rect.centery
            )
            surface.blit(assets.Textures.shield, shield_rect)

        surface.blit(img, self.rect) 
        
        bar_width = 30
        bar_height = 4
        # Calculate health percentage
        health_pct = self.health / self.max_health
        
        # Position: Center it under the enemy, 2 pixels below the sprite
        bar_x = self.rect.centerx - (bar_width // 2)
        bar_y = self.rect.bottom + 2
        
        # Draw background (Red)
        pygame.draw.rect(surface, (200, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Draw current health (Green)
        pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, bar_width * health_pct, bar_height))
        # ---------------------------------
        
        if config.debug:
            pygame.draw.rect(surface, (255, 51, 51), self.rect, 1)

# armada = [] #create empty list
# for i in range (4): #handles rows
#     for j in range (14): #handles columns
#         armada.append(Enemy(j*60+50, i*50+50, assets.Textures.Enemy.enemy0, 0)) #push Enemy objects into list

if __name__ == "__main__":
    print("Execution of module detected! Please run main.py for the game to work properly.")