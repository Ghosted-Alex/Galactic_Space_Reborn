"""Update Module"""

import pygame

import config
from . import assets
from . import clock
from . import cutscenes
from . import events
from . import states


def update_entities(enemies, bullets, powerups, player, screen=None):
    for e in enemies[:]:
        e.move()    
        e.update()

        if e.y > config.Screen.Size.h:
            enemies.remove(e)
            continue

        # Check Bullet Collision
        for b in bullets[:]:
            if e.rect.colliderect(b.rect):
                
                e.health -= 1
                
                assets.Sounds.entity_damage.play()
                
                if e.health == 0:
                    events.on_score_increment(1)
                    if e in enemies: enemies.remove(e)
                    
                if e.shield:
                    if e.health == 1:
                        e.enemy_type = 0
                        e.shield = False
                        assets.Sounds.shield_destroy.play()

                if b in bullets: bullets.remove(b)
                break # Enemy is dead or damaged, stop checking bullets for it
            
        # Check Player Collision
        if e.rect.colliderect(player.hitbox):
            if not player.invincible:
                states.health_blink_timer = 0   

            assets.Sounds.entity_damage.play()

            if not player.invincible:
                if states.difficulty == 0:
                    player.health -= 10
                else:
                    player.health -= 15

            if e.shield:
                e.health -= 1
                if e.health == 1:
                    e.enemy_type = 0
                    e.shield = False
                    assets.Sounds.shield_destroy.play()
            else:
                if e in enemies: enemies.remove(e)

            if player.invincible:
                events.on_score_increment(1)
    
        if screen is not None:
            e.draw(screen)

    for b in bullets[:]: # [:] creates a copy so we can safely remove items
        b.update()
        if screen is not None:
            b.draw(screen)
        
        # Optimization: Delete bullet if it leaves the Screen
        if b.rect.bottom < 0 or b.rect.left > config.Screen.Size.w:
            bullets.remove(b)

    for p in powerups[:]:
        p.move()
        p.update()
    
        if p.y > config.Screen.Size.h or p.x < -50:
            powerups.remove(p)
            continue
        
        # Check player Collision
        if p.rect.colliderect(player.hitbox):
            if p.type == 0:
                pygame.mixer.Sound.play(assets.Sounds.player_health_gain)
                config.health_blink_timer = 0
                if player.health < 100:
                    if states.difficulty == 0:
                        player.health += 10
                    else:
                        player.health += 5
            if p.type == 2:
                pygame.mixer.Sound.play(assets.Sounds.player_power_gain)
                if player.energy < 100:
                    if states.difficulty == 0:
                        player.energy += 10
                    else:
                        player.energy += 5
            if p.type == 1:
                states.health_blink_timer = 0
                if player.health < 100:
                    player.health = 100
                cutscenes.run_invincibility_cutscene(player)
                powerups.clear()
    
            if p in powerups: powerups.remove(p)

        if screen is not None:
            p.draw(screen)

def update_time():
    clock.frame += 1
    clock.delay -= 1