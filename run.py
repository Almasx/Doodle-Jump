import os
import sys
import pygame
import random

pygame.init()
size = width, height = 320, 480
screen = pygame.display.set_mode(size)
pygame.mixer.init()
vec = pygame.math.Vector2
running = True
fps = 60
ACC = 0.5
FRIC = -0.12


def load_image(name, colorkey=None):
    fullname = os.path.join('data', 'images', name)

    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def load_sound(name):
    fullname = os.path.join('data', 'sounds', name)
    if not os.path.isfile(fullname):
        print(f"Файл со звуком '{fullname}' не найден")
        sys.exit()
    return pygame.mixer.Sound(fullname)


def load_font(name, size=30):
    fullname = os.path.join('data', 'fonts', name)
    if not os.path.isfile(fullname):
        print(f"Файл с шрифтом '{fullname}' не найден")
        sys.exit()
    return pygame.font.Font(fullname, size)


class Platform(pygame.sprite.Sprite):
    game_tiles = load_image('game-tiles.png')
    platform_height, platform_width = 16, 58

    def __init__(self, x1, y1, platform_width=58, monster_on=False):
        self.point = True
        self.image = pygame.Surface([platform_width, self.platform_height])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (0, 0, 59, 17))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, platform_width, self.platform_height)
        self.monster_on = monster_on
        if check_overlap(self, platforms) or check_overlap(self, spacers):
            super().__init__(all_sprites, platforms, bioms[current_biom][-2])
            self.kill()
        else:
            super().__init__(all_sprites, platforms, bioms[current_biom][-2])
        if monster_on:
            self.space = pygame.sprite.Sprite(all_sprites, spacers)
            self.space.image = pygame.Surface([70, 100])
            self.space.image.fill((255, 255, 255))
            self.space.image.set_colorkey((255, 255, 255))
            self.space.rect = pygame.Rect(x1, y1 - 100, 70, 100)

    def update(self):
        if check_overlap(self, spacers):
            self.kill()


class Trap_Platform(Platform):
    frames = [(0, 90, 61, 21)] * 2 + [(0, 118, 59, 27)] * 2 + [(0, 147, 60, 37)] * 2

    def __init__(self, x1, y1, moving=False, platform_width=61):
        super().__init__(x1, y1, platform_width)
        self.image = pygame.Surface([platform_width, self.platform_height])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (0, 72, 61, 21))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, platform_width, 19)
        self.moving = moving
        self.speed = random.choice((-1, 1))
        self.trapped, self.state = False, 0
        self.velocity = 0
        self.acceleration = 0
        self.alpha = 100

    def update(self):
        super().update()
        if self.moving:
            self.rect.move_ip(self.speed, 0)
            if self.speed > 0 and self.rect.right > width:
                self.speed = -1
            if self.speed < 0 and self.rect.left < 0:
                self.speed = 1
        if pygame.sprite.spritecollideany(self, player) and not self.trapped:
            if cube.velocity.y > 0 and cube.rect.bottom < self.rect.bottom + 10:
                load_sound('lomise.mp3').play()
                self.trapped = True
                self.moving = False
        if self.trapped:
            try:
                self.image = pygame.Surface([self.frames[self.state][2], self.frames[self.state][3]])
                self.image.fill((255, 255, 255))
                self.image.set_colorkey((255, 255, 255))
                self.image.blit(self.game_tiles, (0, 0), self.frames[self.state])
                self.rect = pygame.Rect(self.rect.x, self.rect.y, self.frames[self.state][2],
                                        self.frames[self.state][3])
                self.state += 1
            except IndexError:
                self.acceleration = 0.5
                self.acceleration += self.velocity * FRIC
                self.velocity += self.acceleration
                self.rect.y += self.velocity + 0.5 * self.acceleration
            finally:
                self.image.set_alpha(self.alpha)
                self.alpha = self.alpha - 1 if self.alpha > 0 else 0
                if self.alpha == 0:
                    self.kill()


class Cloud_Platform(Platform):
    def __init__(self, x1, y1, platform_width=58):
        super().__init__(x1, y1, platform_width)
        self.image = pygame.Surface([platform_width, self.platform_height])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (0, 54, 59, 17))
        self.state, self.alpha = False, 100

    def update(self):
        super().update()
        if self.state:
            self.image.set_alpha(self.alpha)
            self.alpha = self.alpha - 2 if self.alpha > 0 else 0
            if self.alpha == 0:
                self.kill()


class Moving_Platform(Platform):
    def __init__(self, x1, y1, axe, platform_width=58):
        self.limit = 100
        super().__init__(x1, y1 - self.limit, platform_width)
        crop = (0, 18, 58, 16) if axe else (0, 36, 58, 16)
        self.image = pygame.Surface([platform_width, self.platform_height])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), crop)
        self.initial_positions = vec(x1, y1)
        self.position = vec(x1, y1)
        self.axe = axe
        self.speed = random.choice((-1, 1))
        self.space = pygame.sprite.Sprite(all_sprites, spacers)
        self.space.image = pygame.Surface([width, self.platform_height] if axe
                                          else [platform_width, self.limit])
        self.space.image.fill((255, 255, 255))
        self.space.image.set_colorkey((255, 255, 255))
        self.space.rect = pygame.Rect((0, y1, width, 19) if axe else (x1, y1 - self.limit * 2,
                                                                      platform_width,
                                                                      self.limit * 2))

    def update(self):
        if self.axe:
            self.rect.move_ip(self.speed, 0)
            if self.speed > 0 and self.rect.right > width:
                self.speed = -1
            if self.speed < 0 and self.rect.left < 0:
                self.speed = 1
        else:
            self.rect.move_ip(0, self.speed)
            self.position += vec(0, self.speed)
            if self.speed > 0 and self.position.y > self.initial_positions.y + self.limit:
                self.speed = -1
            if self.speed < 0 and self.position.y < self.initial_positions.y:
                self.speed = 1


class Explosion_Platform(Platform):
    frames = [(0, 201, 59, 17)] * 2 + [(0, 219, 59, 17)] * 2 + [(0, 237, 59, 17)] * 2 + \
             [(0, 255, 59, 17)] * 34 + [(0, 273, 60, 19)] * 3 + [(0, 292, 63, 27)] * 4 + \
             [(0, 320, 64, 30)] * 2

    def __init__(self, x1, y1, platform_width=59):
        super().__init__(x1, y1, platform_width)
        self.image = pygame.Surface([platform_width, self.platform_height])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (0, 183, 59, 17))
        self.alpha = 100
        self.ready = False
        self.explosion_sound = [load_sound('explodingplatform.mp3'),
                                load_sound('explodingplatform2.mp3')]

    def update(self):
        super().update()
        if self.rect.y > height // 3 and not self.ready:
            self.state, self.start_time = False, pygame.time.get_ticks()
            self.time = random.randint(1, 2)
            self.ready = True
        if self.ready:
            if pygame.time.get_ticks() - self.start_time > self.time * 1000 and not self.state:
                self.state = True
            if self.state:
                try:
                    self.image = pygame.Surface(
                        [self.frames[self.state][2], self.frames[self.state][3]])
                    self.image.fill((255, 255, 255))
                    self.image.set_colorkey((255, 255, 255))
                    self.image.blit(self.game_tiles, (0, 0), self.frames[self.state])
                    self.rect = pygame.Rect(self.rect.x, self.rect.y, self.frames[self.state][2],
                                            self.frames[self.state][3])
                    self.state += 1
                    if self.state == 40:
                        random.choice(self.explosion_sound).play()
                except IndexError:
                    self.image.set_alpha(self.alpha)
                    self.alpha = self.alpha - 10 if self.alpha > 0 else 0
                    if self.alpha == 0:
                        self.kill()


class Cube(pygame.sprite.Sprite):
    frames = [load_image('lik-njuska.png'),
              load_image('lik-left.png'), load_image('lik-left-odskok.png'),
              load_image('lik-puca.png'), load_image('lik-puca-odskok.png'),
              load_image('lik-right.png'), load_image('lik-right-odskok.png')]

    def __init__(self, pos):
        super().__init__(all_sprites, player)
        self.direction = 1
        self.image = pygame.Surface([62, 60])
        self.image.blit(self.frames[self.direction], (0, 0), (0, 0, 59, 17))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(pos[0], pos[1], 62, 60)
        self.velocity = vec(0, 0)
        self.acceleration = vec(0, 0)
        self.cooldown, self.last_shot = 500, 0
        self.cooldown_sprite, self.last_shot_sprite = 200, 0
        self.state_shot, self.past_direction = False, 1
        self.gun, self.gun_state = None, 0
        self.jump_sound = load_sound('jump.wav')
        self.shot_sound = [load_sound('pucanje.mp3'), load_sound('pucanje2.mp3')]
        self.falling = False
        self.score, self.height = 0, height - pos[1]
        self.crash = 0

    def move(self):
        self.acceleration = vec(0, 0.3)
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_a]:
            self.direction = 1
            self.acceleration.x = -ACC
        elif pressed_keys[pygame.K_d]:
            self.direction = 5
            self.acceleration.x = ACC

        self.acceleration.x += self.velocity.x * FRIC
        self.velocity += self.acceleration
        self.rect.x += self.velocity.x + 0.5 * self.acceleration.x
        self.rect.y += self.velocity.y + 0.5 * self.acceleration.y
        self.height -= self.velocity.y + 0.5 * self.acceleration.y
        self.rect.x = 0 if self.rect.x > width else width if self.rect.x < 0 \
            else self.rect.x

    def jump(self):
        self.jump_sound.play()
        self.velocity.y = -10

    def update(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if self.velocity.y > 3:
            if hits and self.rect.bottom < hits[0].rect.bottom + 10:
                if pygame.sprite.collide_mask(self, hits[0]) and not self.falling:
                    if hits[0].point:
                        hits[0].point = False
                        self.score = round(self.height if self.score < self.height else self.score)
                    if isinstance(hits[0], Trap_Platform):
                        pass
                    elif isinstance(hits[0], Explosion_Platform):
                        hits[0].state = True
                        self.rect.y = hits[0].rect.top - 80
                        self.jump()
                    elif isinstance(hits[0], Cloud_Platform):
                        hits[0].ready = True
                        hits[0].state = True
                        load_sound('bijeli.mp3').play()
                        self.rect.y = hits[0].rect.top - 80
                        self.jump()
                    else:
                        self.rect.y = hits[0].rect.top - 80
                        self.jump()
        hits = pygame.sprite.spritecollide(self, mobs, False)
        if hits and pygame.sprite.collide_mask(self, hits[0]):
            if self.rect.bottom < hits[0].rect.bottom:
                if hasattr(hits[0], 'space'):
                    hits[0].space.kill()
                hits[0].kill()
                load_sound('jumponmonster.mp3').play()
                self.velocity.y = -22
            else:
                self.falling = True
                self.velocity.y = 5
                self.crash += 1
        if self.crash == 1:
            load_sound('monster-crash.mp3').play()
            self.crash += 1
        if pygame.key.get_pressed()[pygame.K_w]:
            self.state_shot, self.past_direction = True, self.direction if self.direction != 3 else \
                self.past_direction
            self.direction = 3
            self.gun_state = 1
            self.last_shot_sprite = pygame.time.get_ticks()
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot >= self.cooldown:
                random.choice(self.shot_sound).play()
                bullet = Bullet(self.rect.midtop)
                bullet.get_shot()
                self.last_shot = current_time
        if self.state_shot:
            if pygame.time.get_ticks() - self.last_shot_sprite >= self.cooldown_sprite:
                self.state_shot = False
                self.direction = self.past_direction
                self.last_shot_sprite = pygame.time.get_ticks()
        self.image = self.frames[self.direction]
        if self.direction == 3:
            if not self.gun:
                if self.gun_state:
                    self.gun = pygame.sprite.Sprite()
                    self.gun.image = pygame.Surface([13, 19])
                    self.gun.image.fill((255, 255, 255))
                    self.gun.image.set_colorkey((255, 255, 255))
                    self.gun.image.blit(self.frames[0], (0, 0), (0, 0, 13, 19))
                    self.gun.rect = self.gun.image.get_rect()
                    all_sprites.add(self.gun)
            self.gun.rect.y = self.rect.y
            self.gun.rect.x = self.rect.x + (self.image.get_width() - 13) // 2
        else:
            if self.gun:
                self.gun.kill()
                self.gun = None


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__(all_sprites, bullets)
        self.image = pygame.Surface([12, 12])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(load_image('projectile-tiles.png'), (0, 0), (0, 0, 12, 12))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (pos[0], pos[1])
        self.velocity = vec(0, 0)
        self.acceleration = vec(0, 0)

    def get_shot(self):
        self.velocity.y = -20

    def update(self):
        if self.rect.y <= 0:
            self.kill()
        self.acceleration = vec(0, 0.5)
        self.velocity += self.acceleration
        self.rect.y += self.velocity.y + 0.5 * self.acceleration.y


class Monster(pygame.sprite.Sprite):
    game_tiles = load_image('game-tiles.png')
    killed_sound = load_sound('monsterpogodak.mp3')

    def __init__(self, hp):
        self.radar = load_sound('monsterblizu.mp3')
        self.radar.play(-1)
        super().__init__(all_sprites, mobs)
        self.hp, self.dying, self.hit = hp, False, False

    def update(self):
        hits = pygame.sprite.spritecollide(self, bullets, False)
        if hits:
            if pygame.sprite.collide_mask(self, hits[0]):
                hits[0].kill()
                self.hp -= 1
                self.dying, self.hit = True, True
        else:
            self.hit = False
        if self.hp == 0:
            self.killed_sound.play()
            if hasattr(self, 'space'):
                self.space.kill()
            self.kill()

    def kill(self):
        pygame.sprite.Sprite.kill(self)
        self.radar.stop()


class Flying_Monster(Monster):
    def __init__(self, x1, y1, hp):
        super().__init__(hp)
        self.step, self.position = vec(1, 1), vec(x1, y1)
        self.rest_mask = vec(x1, y1)
        self.space = pygame.sprite.Sprite(all_sprites, spacers)
        self.space.image = pygame.Surface([60, 100])
        self.space.image.fill((255, 255, 255))
        self.space.image.set_colorkey((255, 255, 255))
        self.space.rect = pygame.Rect(x1, y1, 60, 100)

    def update(self):
        super().update()
        self.rect.move_ip(self.step.x, self.step.y)
        self.rest_mask += vec(self.step.x, self.step.y)
        if self.position.x - 5 > self.rect.x or \
                self.rect.x > self.position.x + 5:
            self.step.x *= -1
        if self.rest_mask.y - 2 > self.position.y or \
                self.position.y > self.rest_mask.y + 3:
            self.step.y *= -1


class Flying_Spider(Flying_Monster):
    def __init__(self, x1, y1):
        super().__init__(x1, y1, 1)
        self.image = pygame.Surface([57, 52])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (336, 169, 57, 52))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, 57, 52)


class Flying_Blob(Flying_Monster):
    def __init__(self, x1, y1):
        super().__init__(x1, y1, 1)
        self.image = pygame.Surface([48, 38])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (148, 264, 48, 38))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, 48, 38)


class Flying_Bug(Flying_Monster):
    frames = [(148, 0, 78, 46), (227, 0, 81, 46), (308, 0, 81, 46), (390, 0, 80, 46),
              (148, 46, 79, 46), (390, 0, 80, 46), (308, 0, 81, 46), (227, 0, 81, 46),
              (148, 0, 78, 46)]

    def __init__(self, x1, y1):
        super().__init__(x1, y1, 1)
        self.state = 0
        self.image = pygame.Surface([self.frames[self.state][2], self.frames[self.state][3]])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), self.frames[self.state])
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, self.frames[self.state][2], self.frames[self.state][3])

    def update(self):
        super().update()
        try:
            self.image = pygame.Surface([self.frames[self.state][2], self.frames[self.state][3]])
            self.image.fill((255, 255, 255))
            self.image.set_colorkey((255, 255, 255))
            self.image.blit(self.game_tiles, (0, 0), self.frames[self.state])
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = pygame.Rect(self.rect.x, self.rect.y, self.frames[self.state][2],
                                    self.frames[self.state][3])
            self.state += 1
        except IndexError:
            self.state = 0


class Jumping_Monster(Monster):
    def __init__(self, hp):
        super().__init__(hp)
        jumping_mobs.add(self)
        self.velocity = vec(0, 0)
        self.acceleration = vec(0, 0)

    def update(self):
        super().update()
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits and self.rect.bottom < hits[0].rect.bottom + 1:
            if pygame.sprite.collide_mask(self, hits[0]) and hits[0].monster_on:
                self.rect.y = hits[0].rect.top - self.image.get_height() - 10
                self.velocity.y = -2.5
        self.acceleration = vec(0, 0.1)
        self.velocity += self.acceleration
        self.rect.y += self.velocity.y + 0.1 * self.acceleration.y


class Jumping_Bug(Jumping_Monster):
    frames = [(130, 420, 69, 89)] * 2 + [(66, 93, 66, 91)] * 2 + [(63, 420, 67, 91)] * 2 + \
             [(67, 0, 64, 91)] * 2 + [(0, 420, 62, 89)] * 2 + [(67, 0, 64, 91)] * 2 + \
             [(63, 420, 67, 91)] * 2 + [(66, 93, 66, 91)]

    def __init__(self, x1, y1):
        super().__init__(5)
        self.state = 0
        self.image = pygame.Surface([self.frames[self.state][2], self.frames[self.state][3]])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), self.frames[self.state])
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, self.frames[self.state][2], self.frames[self.state][3])

    def update(self):
        super().update()
        try:
            self.image = pygame.Surface([self.frames[self.state][2], self.frames[self.state][3]])
            self.image.fill((255, 255, 255))
            self.image.set_colorkey((255, 255, 255))
            self.image.blit(self.game_tiles, (0, 0), self.frames[self.state])
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = pygame.Rect(self.rect.x, self.rect.y, self.frames[self.state][2],
                                    self.frames[self.state][3])
            self.state += 1
        except IndexError:
            self.state = 0


class Jumping_Floor(Jumping_Monster):
    def __init__(self, x1, y1):
        super().__init__(3)
        self.state = 0
        self.image = pygame.Surface((92, 35))
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (512, 0, 92, 35))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, 92, 35)
        self.cooldown_sprite, self.last_shot_sprite = 150, 0

    def update(self):
        super().update()
        if self.state:
            if pygame.time.get_ticks() - self.last_shot_sprite >= self.cooldown_sprite:
                self.image = pygame.Surface((92, 35))
                self.image.fill((255, 255, 255))
                self.image.set_colorkey((255, 255, 255))
                self.image.blit(self.game_tiles, (0, 0), (512, 0, 92, 35))
                self.mask = pygame.mask.from_surface(self.image)
                self.rect = pygame.Rect(self.rect.x, self.rect.y, 92, 35)
                self.last_shot_sprite = pygame.time.get_ticks()
        if self.hit:
            self.state = True
            self.last_shot_sprite = pygame.time.get_ticks()
            self.image = pygame.Surface((92, 35))
            self.image.fill((255, 255, 255))
            self.image.set_colorkey((255, 255, 255))
            self.image.blit(self.game_tiles, (0, 0), (512, 36, 92, 35))
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = pygame.Rect(self.rect.x, self.rect.y, 92, 35)


class Jumping_Wall(Jumping_Monster):
    def __init__(self, x1, y1):
        super().__init__(2)
        self.state = 0
        self.image = pygame.Surface((66, 87))
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (512, 426, 66, 87))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, 66, 87)
        self.cooldown_sprite, self.last_shot_sprite = 150, 0

    def update(self):
        super().update()
        if self.state:
            if pygame.time.get_ticks() - self.last_shot_sprite >= self.cooldown_sprite:
                self.image = pygame.Surface((66, 87))
                self.image.fill((255, 255, 255))
                self.image.set_colorkey((255, 255, 255))
                self.image.blit(self.game_tiles, (0, 0), (512, 426, 66, 87))
                self.mask = pygame.mask.from_surface(self.image)
                self.rect = pygame.Rect(self.rect.x, self.rect.y, 66, 87)
                self.last_shot_sprite = pygame.time.get_ticks()
        if self.hit:
            self.state = True
            self.last_shot_sprite = pygame.time.get_ticks()
            self.image = pygame.Surface((66, 87))
            self.image.fill((255, 255, 255))
            self.image.set_colorkey((255, 255, 255))
            self.image.blit(self.game_tiles, (0, 0), (512, 336, 66, 87))
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = pygame.Rect(self.rect.x, self.rect.y, 66, 87)


class Bulky_Blue(Jumping_Monster):
    def __init__(self, x1, y1):
        super().__init__(1)
        self.state = 0
        self.image = pygame.Surface((88, 57))
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (512, 69, 88, 57))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, 88, 57)


class Bulky_Green(Jumping_Monster):
    frames = [(0, 359, 84, 55)] * 3 + [(63, 236, 84, 55)] * 5 + [(84, 360, 84, 61)] * 6 + \
             [(147, 203, 84, 60)] * 5 + [(63, 299, 84, 61)] * 4

    def __init__(self, x1, y1):
        super().__init__(2)
        self.state = 0
        self.image = pygame.Surface([self.frames[self.state][2], self.frames[self.state][3]])
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), self.frames[self.state])
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, self.frames[self.state][2], self.frames[self.state][3])

    def update(self):
        super().update()
        if self.dying:
            try:
                self.image = pygame.Surface([self.frames[self.state][2], self.frames[self.state][3]])
                self.image.fill((255, 255, 255))
                self.image.set_colorkey((255, 255, 255))
                self.image.blit(self.game_tiles, (0, 0), self.frames[self.state])
                self.mask = pygame.mask.from_surface(self.image)
                self.rect = pygame.Rect(self.rect.x, self.rect.y, self.frames[self.state][2],
                                        self.frames[self.state][3])
                self.state += 1
            except IndexError:
                self.state = 3


class Walking_Monster(Monster):
    def __init__(self, x1, y1):
        super().__init__(1)
        self.step, self.position = vec(random.choice((-1, 1)), 1.3), vec(x1, y1)
        self.rest_mask = vec(x1, y1)
        self.position = vec(x1, y1)
        self.image = pygame.Surface((39, 51))
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.game_tiles, (0, 0), (64 if self.step.x == 1 else 105, 186, 39, 51))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, 39, 51)
        self.space = pygame.sprite.Sprite(all_sprites, spacers)
        self.space.image = pygame.Surface([width, 60])
        self.space.image.fill((255, 255, 255))
        self.space.image.set_colorkey((255, 255, 255))
        self.space.rect = pygame.Rect(x1, y1, width, 90)

    def update(self):
        super().update()
        self.rect.move_ip(self.step.x, self.step.y)
        self.rest_mask += vec(self.step.x, self.step.y)
        if self.rest_mask.y - 12 > self.position.y or \
                self.position.y > self.rest_mask.y + 12:
            self.step.y *= -1
        if self.step.x > 0 and self.rect.right > width or self.step.x < 0 and self.rect.left < 0:
            self.step.x *= -1
            self.image = pygame.Surface((39, 51))
            self.image.fill((255, 255, 255))
            self.image.set_colorkey((255, 255, 255))
            self.image.blit(self.game_tiles, (0, 0), (64 if self.step.x == 1 else 105, 186, 39, 51))
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = pygame.Rect(self.rect.x, self.rect.y, 39, 51)


class Ui_Button(pygame.sprite.Sprite):
    buttons = load_image('menu.png')

    def __init__(self, x, y):
        super().__init__(buttons)
        self.image = pygame.Surface((112, 42))
        self.image.fill((255, 255, 255))
        self.image.set_colorkey((255, 255, 255))
        self.image.blit(self.buttons, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x, y, 112, 42)

    def handle_event(self, position):
        return True if self.rect.x < position[0] < self.rect.x + self.image.get_width() and \
                       self.rect.y < position[1] < self.rect.y + self.image.get_height() else False


bioms = {'normal': [[Platform] * 60 + [Trap_Platform] * 19 + [Moving_Platform] * 15 +
                    [Explosion_Platform] * 5 + [Cloud_Platform], 35, 4.5, pygame.sprite.Group(),
                    2000],
         'explosive lands': [[Explosion_Platform], 16, 1, pygame.sprite.Group(), 1000],
         'clouds': [[Cloud_Platform], 16, 1, pygame.sprite.Group(), 1000],
         'moving platforms': [[Moving_Platform], 7, 0.5, pygame.sprite.Group(), 1000]}
current_biom, passed_bioms = 'normal', 0
bioms_poll = ['moving platforms', 'clouds', 'explosive lands', 'normal']
mob_rates = [0] * 149 + [1]
all_mobs = [Flying_Blob, Flying_Bug, Flying_Spider, Walking_Monster]
clock = pygame.time.Clock()


def generate_platforms():
    while len(bioms[current_biom][-2]) < bioms[current_biom][1]:
        raft = random.choice(bioms[current_biom][0])
        x, y = random.randrange(0, width - random.randrange(50, 100)),\
               platforms.sprites()[-1].rect.y - random.randrange(10, 60)
        if y < bioms[current_biom][-1] - cube.score + passed_bioms:
            if raft == Moving_Platform:
                if current_biom == 'moving platforms':
                    raft(x, platforms.sprites()[-1].rect.y - random.randrange(40, 120), 1)
                else:
                    axe = random.choice([1] * 95 + [0] * 5)
                    if not axe:
                        y = platforms.sprites()[-1].rect.y - random.randrange(100, 120)
                        raft(x, y, axe)

            elif raft == Trap_Platform:
                raft(x, y, random.choice([1] + [0] * 9))
            elif raft == Platform:
                if random.choice(mob_rates):
                    monster = random.choice(all_mobs)
                    if issubclass(monster, Flying_Monster):
                        y = platforms.sprites()[-1].rect.y - random.randrange(50, 60)
                        monster(x, y)
                    elif monster == Walking_Monster:
                        y = platforms.sprites()[-1].rect.y - random.randrange(50, 60)
                        monster(x, y)
                    else:
                        if monster in [Jumping_Bug, Jumping_Wall]:
                            raft(x, y, 58, True)
                            monster(x, y - 100)
                        else:
                            raft(x, y, 58, True)
                            raft(x + 58, y, 58, True)
                            monster(x, y - 60)
                else:
                    raft(x, y)
            else:
                raft(x, y)


def check_overlap(platform, group):
    if pygame.sprite.spritecollideany(platform, group):
        return True
    else:
        for entity in group:
            if entity == platform:
                continue
            if isinstance(entity, Platform):
                if entity.monster_on == platform.monster_on and platform.monster_on:
                    continue
            if (abs(platform.rect.top - entity.rect.bottom) < 50) and (abs(platform.rect.bottom -
                                                                           entity.rect.top) < 50):
                return True
        return False


def starting_screen():
    page = load_image('Default.png')
    button = Ui_Button(60, 138)
    btn = pygame.sprite.Group()
    btn.add(button)
    font = load_font('al-seana.ttf')
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button.handle_event(event.pos):
                    return
        screen.blit(page, (0, 0))
        btn.draw(screen)
        screen.blit(font.render('play', True, (0, 0, 0)), (100, 138))
        pygame.display.flip()
        clock.tick(60)


def game_over_screen():
    font = load_font('al-seana.ttf')
    with open('./data/data.txt', mode='rt') as file:
        line = file.readlines()[0]
        high_score = int(line) if cube.score < int(line) else cube.score
    screen.blit(load_font('al-seana.ttf', 50).render('game over!', True, (126, 7, 8)), (73, 103))
    screen.blit(font.render(f'your score {str(cube.score)}', True, (0, 0, 0)), (73, 156))
    screen.blit(font.render(f'your high score {str(high_score)}', True, (0, 0, 0)), (73, 184))
    with open('./data/data.txt', mode='wt') as file:
        file.write(str(high_score))


all_sprites = pygame.sprite.Group()
spacers = pygame.sprite.Group()
platforms = pygame.sprite.Group()
player = pygame.sprite.Group()
bullets = pygame.sprite.Group()
mobs = pygame.sprite.Group()
jumping_mobs = pygame.sprite.Group()
buttons = pygame.sprite.Group()
background = load_image('bck.png')
falling = False
falling, falling_2 = False, True
gameover, game_over_sound = False, False
top_screen = load_image('space-top-score.png')
starting_screen()
cube = Cube((299, height - 490))
solid_platform = Platform(33, height - 180, 58, True)
Platform(33 + 58, height - 180, 58, True)
trap_platform = Platform(103, height - 390)
horizontal_platform = Platform(299, height - 290)
explosion_platform = Platform(143, height - 490)
solid_platform_for_mob = Platform(33, 0)
walking_monster = Bulky_Green(33, height - 180 - 60)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if gameover:
                pass
    if cube.rect.top <= 100 and not falling and falling_2:
        cube.rect.y += abs(cube.velocity.y)
        for plat in platforms:
            plat.rect.y += abs(cube.velocity.y)
            if plat.monster_on:
                plat.space.rect.y += abs(cube.velocity.y)
                if plat.rect.top >= height:
                    plat.space.kill()
            if isinstance(plat, Moving_Platform):
                plat.space.rect.y += abs(cube.velocity.y)
                if not plat.axe:
                    if plat.rect.y - plat.limit >= height:
                        plat.space.kill()
                        plat.kill()
                else:
                    if plat.rect.top >= height:
                        plat.space.kill()
                        plat.kill()

            else:
                if plat.rect.top >= height:
                    plat.kill()
        for mob in mobs:
            mob.rect.y += abs(cube.velocity.y)
            if hasattr(mob, 'space'):
                mob.space.rect.y += abs(cube.velocity.y)
                if mob.rect.top >= height:
                    mob.space.kill()
                    mob.kill()
            else:
                if mob.rect.top >= height:
                    mob.kill()
    if cube.rect.top <= 10 and falling:
        falling = False
        falling_2 = False
        cube.velocity.y = 0
    if cube.rect.bottom > height and falling_2:
        game_over_sound = True
        falling = True
    if game_over_sound and not gameover:
        load_sound('pada.mp3').play()
        game_over_sound = False
        gameover = True
    if falling:
        cube.rect.y -= cube.velocity.y * 1.1
        for plat in platforms:
            plat.rect.y -= cube.velocity.y * 0.5
            if plat.rect.top < 0:
                plat.kill()
        for mob in mobs:
            mob.rect.y -= cube.velocity.y * 0.5
            if mob.rect.top < 0:
                mob.kill()
    if cube.score - passed_bioms > bioms[current_biom][-1]:
        bioms[current_biom][-2] = pygame.sprite.Group()
        passed_bioms += bioms[current_biom][-1]
        current_biom = random.choice(bioms_poll)
    if not falling and falling_2:
        generate_platforms()
        pass
    cube.move()
    all_sprites.update()
    screen.blit(background, (0, 0))
    all_sprites.draw(screen)
    screen.blit(top_screen, (0, 0), (0, 0, 320, 45))
    font = load_font('al-seana.ttf')
    screen.blit(font.render(str(cube.score), True, (0, 0, 0)), (10, 2))
    screen.blit(font.render(current_biom, True, (0, 0, 0)), (width // 2, 2))
    if cube.rect.y > 500:
        game_over_screen()
    pygame.display.flip()
    clock.tick(60)

