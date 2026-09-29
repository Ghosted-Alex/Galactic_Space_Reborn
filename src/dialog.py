import pygame

class Confirmation:
    def __init__(self, x, y, w, h, text, font):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.surf = pygame.Surface((w, h))
        self.surf.fill("black")  # Background color
        self.rect = self.surf.get_rect(topleft=(x, y))
        self.text = text
        self.font = pygame.font.Font(None if not font else font, 50)
    
    def render(self, screen):
        # Draw the dialog box
        screen.blit(self.surf, self.rect)
        # Render the text
        text_surface = self.font.render(self.text, True, "white")
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)