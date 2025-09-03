import pygame
import random
import os

# --- Pygame'i başlatma ---
pygame.init()

# --- Ekran ayarları ---
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Atari Uçak Simülasyonu (Güncellendi)")

# --- Renk tanımları ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
BLUE = (0, 0, 150)
RED = (200, 0, 0)
YELLOW = (200, 200, 0)
GRAY = (150, 150, 150)
PURPLE = (150, 0, 150)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# --- Uçak Sınıfı (Geometrik Çizim) ---
class Aircraft(pygame.sprite.Sprite):
    def __init__(self, is_main=True):
        super().__init__()
        self.width = 40
        self.height = 60
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA)
        self.color = GREEN if is_main else YELLOW
        self.draw_aircraft_shape()
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 80))
        if not is_main:
            self.rect.x -= 70

        self.speed = 0
        self.max_speed = 100
        self.min_speed = 1
        self.acceleration = 0.2
        self.deceleration = 0.1
        self.horizontal_speed = 5
        self.score = 0
        self.fuel = 100

        self.last_shot_time = 0
        self.shoot_cooldown = 200

        self.super_jet_active = False
        self.super_jet_end_time = 0
        self.original_max_speed = self.max_speed

        self.extra_aircraft_active = False
        self.extra_aircraft_end_time = 0
        
        self.color_change_active = False
        self.color_change_end_time = 0
        self.last_color_change_time = 0
        self.color_cycle_cooldown = 100

    def draw_aircraft_shape(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, self.color, (self.width // 4, 0, self.width // 2, self.height))
        pygame.draw.rect(self.image, self.color, (0, self.height // 2 - 5, self.width, 10))
        pygame.draw.polygon(self.image, self.color, [
            (self.width // 2, 0),
            (self.width // 4, 15),
            (self.width * 3 // 4, 15)
        ])
        pygame.draw.rect(self.image, self.color, (self.width // 2 - 5, self.height - 20, 10, 20))

    def update(self, keys):
        current_time = pygame.time.get_ticks()
        
        # Item etkilerinin sürelerini kontrol et ve sona erdir
        if self.super_jet_active and current_time > self.super_jet_end_time:
            self.super_jet_active = False
            self.max_speed = self.original_max_speed
            self.speed = self.original_max_speed # Hızı eski normal hıza döndür
            
            # Jet süresi bitince yakıt azalsın
            self.fuel = max(0, self.fuel - 5) 

        if self.extra_aircraft_active and current_time > self.extra_aircraft_end_time:
            self.extra_aircraft_active = False
            self.fuel = max(0, self.fuel - 5)

        if self.color_change_active and current_time > self.color_change_end_time:
            self.color_change_active = False
            self.color = GREEN
            self.draw_aircraft_shape()
            self.fuel = max(0, self.fuel - 5)

        if self.color_change_active and current_time - self.last_color_change_time > self.color_cycle_cooldown:
            self.last_color_change_time = current_time
            colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, WHITE]
            self.color = random.choice(colors)
            self.draw_aircraft_shape()

        if keys[pygame.K_UP]:
            self.speed += self.acceleration
            if self.speed > self.max_speed:
                self.speed = self.max_speed
        elif keys[pygame.K_DOWN]:
            self.speed -= self.deceleration
            if self.speed < self.min_speed:
                self.speed = self.min_speed
        
        # Sadece süper hız aktif değilse yakıt tüket
        if not self.super_jet_active:
            self.fuel -= 0.05 * (self.speed / self.max_speed + 0.5)
            self.fuel = max(0, self.fuel) # Yakıt 0'ın altına inmesin
            
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.horizontal_speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.horizontal_speed

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def shoot(self, bullets):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.shoot_cooldown:
            self.last_shot_time = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            bullets.add(bullet)
            return bullet
        return None

    def activate_super_jet(self):
        self.super_jet_active = True
        self.super_jet_end_time = pygame.time.get_ticks() + 5 * 1000 # 5 Saniye
        self.max_speed = 100
        self.speed = self.max_speed
        self.fuel = min(100, self.fuel + 20) # Item alındığında yakıt takviyesi
        
    def activate_extra_aircraft(self):
        self.extra_aircraft_active = True
        self.extra_aircraft_end_time = pygame.time.get_ticks() + 10 * 1000
        self.fuel = min(100, self.fuel + 20)

    def activate_color_change(self):
        self.color_change_active = True
        self.color_change_end_time = pygame.time.get_ticks() + 10 * 1000
        self.fuel = min(100, self.fuel + 10)

# --- Mermi Sınıfı ---
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 5
        self.height = 15
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

# --- Engel/Item Sınıfı ---
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, item_type=None):
        super().__init__()
        self.type = item_type if item_type else random.choice(['cloud', 'fuel'])
        self.width = random.randint(50, 100)
        self.height = random.randint(30, 60)
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA)
        self.draw_shape()
        self.rect = self.image.get_rect(x=random.randint(0, WIDTH - self.width), y=random.randint(-200, -50))
        
    def draw_shape(self):
        self.image.fill((0, 0, 0, 0))
        if self.type == 'cloud':
            pygame.draw.rect(self.image, WHITE, (0, self.height // 2, self.width, self.height // 2))
            pygame.draw.ellipse(self.image, WHITE, (self.width // 4, 0, self.width // 2, self.height))
        elif self.type == 'fuel':
            pygame.draw.rect(self.image, YELLOW, (0, 0, self.width, self.height))
            font = pygame.font.Font(None, 20)
            text = font.render("FUEL", True, BLACK)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
            self.image.blit(text, text_rect)
        elif self.type == 'super_jet':
            pygame.draw.polygon(self.image, RED, [(self.width // 2, 0), (0, self.height), (self.width, self.height)])
            font = pygame.font.Font(None, 18)
            text = font.render("JET", True, BLACK)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
            self.image.blit(text, text_rect)
        elif self.type == 'mine_drop':
            pygame.draw.circle(self.image, BLACK, (self.width // 2, self.height // 2), self.width // 2)
            pygame.draw.line(self.image, WHITE, (0, 0), (self.width, self.height), 3)
            pygame.draw.line(self.image, WHITE, (self.width, 0), (0, self.height), 3)
            font = pygame.font.Font(None, 18)
            text = font.render("MINE", True, WHITE)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
            self.image.blit(text, text_rect)
        elif self.type == 'extra_aircraft':
            pygame.draw.rect(self.image, PURPLE, (0, 0, self.width, self.height))
            font = pygame.font.Font(None, 18)
            text = font.render("2X", True, BLACK)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
            self.image.blit(text, text_rect)
        elif self.type == 'color_change':
            pygame.draw.circle(self.image, ORANGE, (self.width // 2, self.height // 2), self.width // 2)
            font = pygame.font.Font(None, 18)
            text = font.render("COLOR", True, BLACK)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
            self.image.blit(text, text_rect)

    def update(self, scroll_speed):
        self.rect.y += scroll_speed
        if self.rect.top > HEIGHT:
            self.kill()

# --- Arka Plan (Tekrarlayan Çizgiler) ---
class Background:
    def __init__(self):
        self.line_spacing = 40
        self.line_color = BLUE
        self.y_offset = 0

    def draw(self, surface, scroll_speed):
        self.y_offset = (self.y_offset + scroll_speed) % self.line_spacing
        
        for y in range(-self.line_spacing, HEIGHT + self.line_spacing, self.line_spacing):
            current_y = (y + self.y_offset) % (HEIGHT + self.line_spacing)
            if current_y < HEIGHT:
                pygame.draw.line(surface, self.line_color, (0, current_y), (WIDTH, current_y), 1)

# --- HUD (Head-Up Display) Çizimi ---
def draw_hud(surface, aircraft):
    font = pygame.font.Font(None, 24)
    speed_text = font.render(f"HIZ: {aircraft.speed:.1f}", True, WHITE)
    surface.blit(speed_text, (10, 10))
    score_text = font.render(f"PUAN: {aircraft.score}", True, WHITE)
    surface.blit(score_text, (10, 40))
    
    pygame.draw.rect(surface, GRAY, (WIDTH - 120, 10, 110, 20), 2)
    fuel_color = GREEN if aircraft.fuel > 30 else RED
    pygame.draw.rect(surface, fuel_color, (WIDTH - 115, 15, max(0, aircraft.fuel), 10))
    fuel_text = font.render("YAKIT", True, WHITE)
    surface.blit(fuel_text, (WIDTH - 180, 10))

    current_time = pygame.time.get_ticks()
    if aircraft.super_jet_active:
        time_left = max(0, (aircraft.super_jet_end_time - current_time) / 1000)
        jet_text = font.render(f"JET: {time_left:.1f}s", True, RED)
        surface.blit(jet_text, (WIDTH - 180, 40))
    if aircraft.extra_aircraft_active:
        time_left = max(0, (aircraft.extra_aircraft_end_time - current_time) / 1000)
        extra_text = font.render(f"2X UCUS: {time_left:.1f}s", True, PURPLE)
        surface.blit(extra_text, (WIDTH - 180, 70))
    if aircraft.color_change_active:
        time_left = max(0, (aircraft.color_change_end_time - current_time) / 1000)
        color_text = font.render(f"RENK: {time_left:.1f}s", True, ORANGE)
        surface.blit(color_text, (WIDTH - 180, 100))

# --- Oyun Bitti Ekranı ---
def game_over_screen(surface, score):
    font_large = pygame.font.Font(None, 74)
    font_medium = pygame.font.Font(None, 36)
    game_over_text = font_large.render("OYUN BITTI", True, RED)
    score_text = font_medium.render(f"Puan: {score}", True, WHITE)
    restart_text = font_medium.render("Yeniden Oynamak Icin 'R' Tusuna Basin", True, YELLOW)
    game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
    surface.fill(BLACK)
    surface.blit(game_over_text, game_over_rect)
    surface.blit(score_text, score_rect)
    surface.blit(restart_text, restart_rect)
    pygame.display.flip()
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting_for_input = False
                    return True
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
    return False

# --- Ana Oyun Döngüsü ---
def main_game():
    main_aircraft = Aircraft(is_main=True)
    all_aircrafts = pygame.sprite.Group()
    all_aircrafts.add(main_aircraft)

    background = Background()
    obstacles = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    items = pygame.sprite.Group()

    item_types = ['super_jet', 'mine_drop', 'extra_aircraft', 'color_change']
    max_clouds = 5

    for _ in range(max_clouds):
        obstacle = Obstacle(item_type='cloud')
        obstacles.add(obstacle)
    
    for _ in range(3): # Başlangıçta 3 yakıt item'ı
        fuel = Obstacle(item_type='fuel')
        items.add(fuel)


    running = True
    game_over = False
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        if not game_over:
            keys = pygame.key.get_pressed()
            
            for aircraft in all_aircrafts:
                aircraft.update(keys)
                if keys[pygame.K_SPACE]:
                    aircraft.shoot(bullets)

            bullets.update()
            
            # Yakıt bitince oyun bitsin kontrolü aktif
            if main_aircraft.fuel <= 0:
                game_over = True

            obstacles.update(main_aircraft.speed)
            items.update(main_aircraft.speed)

            for aircraft in all_aircrafts:
                collided_obstacles = pygame.sprite.spritecollide(aircraft, obstacles, False)
                for obstacle in collided_obstacles:
                    if obstacle.type == 'cloud':
                        # Jet aktif değilse can götürsün
                        if not main_aircraft.super_jet_active: 
                            main_aircraft.fuel = max(0, main_aircraft.fuel - 10)
                            main_aircraft.score = max(0, main_aircraft.score - 1)
                        
                        obstacle.kill() # Bulut her durumda yok olsun
                        new_obstacle = Obstacle(item_type='cloud')
                        new_obstacle.rect.y = random.randint(-150, -50)
                        obstacles.add(new_obstacle)

                collided_items = pygame.sprite.spritecollide(aircraft, items, True)
                for item in collided_items:
                    if item.type == 'fuel':
                        main_aircraft.fuel = min(100, main_aircraft.fuel + 20)
                        main_aircraft.score += 5
                    elif item.type == 'super_jet':
                        main_aircraft.activate_super_jet()
                    elif item.type == 'mine_drop':
                        for cloud_obj in [o for o in obstacles if o.type == 'cloud']:
                            cloud_obj.kill()
                        main_aircraft.score += 50
                    elif item.type == 'extra_aircraft':
                        if not main_aircraft.extra_aircraft_active:
                            main_aircraft.activate_extra_aircraft()
                            clone_aircraft = Aircraft(is_main=False)
                            all_aircrafts.add(clone_aircraft)
                    elif item.type == 'color_change':
                        if not main_aircraft.color_change_active:
                            main_aircraft.activate_color_change()

            collisions = pygame.sprite.groupcollide(bullets, obstacles, True, False)
            for bullet, hit_obstacles in collisions.items():
                for hit_obstacle in hit_obstacles:
                    if hit_obstacle.type == 'cloud':
                        if random.random() < 0.25:
                            dropped_item_type = random.choice(item_types)
                            dropped_item = Obstacle(item_type=dropped_item_type)
                            dropped_item.rect.center = hit_obstacle.rect.center
                            items.add(dropped_item)
                        
                        hit_obstacle.kill()
                        main_aircraft.score += 10
                        
                        new_obstacle = Obstacle(item_type='cloud')
                        new_obstacle.rect.y = random.randint(-150, -50)
                        obstacles.add(new_obstacle)
            
            current_clouds = len([o for o in obstacles if o.type == 'cloud'])
            if current_clouds < max_clouds:
                new_cloud = Obstacle(item_type='cloud')
                new_cloud.rect.y = random.randint(-150, -50)
                obstacles.add(new_cloud)

            if not main_aircraft.extra_aircraft_active and len(all_aircrafts) > 1:
                for aircraft_to_remove in [ac for ac in all_aircrafts if ac != main_aircraft]:
                    aircraft_to_remove.kill()

            if random.random() < 0.005:
                new_item_type = random.choice(['fuel'] + item_types)
                new_item = Obstacle(item_type=new_item_type)
                new_item.rect.y = random.randint(-150, -50)
                items.add(new_item)


            screen.fill(BLACK)
            background.draw(screen, main_aircraft.speed)
            obstacles.draw(screen)
            items.draw(screen)
            bullets.draw(screen)
            all_aircrafts.draw(screen)
            draw_hud(screen, main_aircraft)
            
            pygame.display.flip()

        else:
            if game_over_screen(screen, main_aircraft.score):
                main_aircraft = Aircraft(is_main=True)
                all_aircrafts.empty()
                all_aircrafts.add(main_aircraft)
                obstacles.empty()
                bullets.empty()
                items.empty()
                for _ in range(max_clouds):
                    obstacles.add(Obstacle(item_type='cloud'))
                for _ in range(3): # Yeniden başlarken yakıt itemları da gelsin
                    fuel = Obstacle(item_type='fuel')
                    items.add(fuel)
                game_over = False
            else:
                running = False

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main_game()
