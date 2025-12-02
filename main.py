"""
Eco Ranger - 2D экологическая игра (Top-Down View)
ENHANCED GRAPHICS VERSION
Максимальная графика для Pygame
"""

import pygame
import sys
import random
import math
from enum import Enum

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Загрузка звуков
try:
    # Звуковые эффекты
    sound_pickup = pygame.mixer.Sound('pickup.wav')
    sound_trash_dump = pygame.mixer.Sound('trash_dump.wav')
    sound_dash = pygame.mixer.Sound('dash.wav')
    sound_poison = pygame.mixer.Sound('poison.wav')
    sound_heal = pygame.mixer.Sound('heal.wav')
    sound_button = pygame.mixer.Sound('button.wav')

    # Устанавливаем громкость эффектов
    sound_pickup.set_volume(0.3)
    sound_trash_dump.set_volume(0.4)
    sound_dash.set_volume(0.5)
    sound_poison.set_volume(0.6)
    sound_heal.set_volume(0.5)
    sound_button.set_volume(0.3)

    SOUNDS_ENABLED = True
except:
    SOUNDS_ENABLED = False
    print("Не удалось загрузить звуки")

# Константы экрана
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60

# Размер мира (больше чем экран)
WORLD_WIDTH = 2400
WORLD_HEIGHT = 1400

# Размер тайла
TILE_SIZE = 32

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
LIGHT_GREEN = (144, 238, 144)
FOREST_GREEN = (34, 100, 34)
BLUE = (0, 150, 255)
YELLOW = (255, 215, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
SKY_BLUE = (135, 206, 235)
WATER_BLUE = (64, 164, 223)

# Настройки игрока
PLAYER_SPEED = 4

# Состояния игры
class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSE = 3
    GAME_OVER = 4
    LEVEL_COMPLETE = 5
    SHOP = 6
    CUTSCENE = 7

class Camera:
    """Класс камеры для плавного следования за игроком"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0

    def apply(self, entity, shake_offset=(0, 0)):
        """Применить смещение камеры к объекту (с учетом тряски)"""
        return entity.rect.x - self.x + shake_offset[0], entity.rect.y - self.y + shake_offset[1]

    def update(self, target):
        """Обновить позицию камеры (плавное следование)"""
        # Центрируем камеру на цели
        target_x = -target.rect.centerx + SCREEN_WIDTH // 2
        target_y = -target.rect.centery + SCREEN_HEIGHT // 2

        # Плавное движение камеры (всегда следует за персонажем)
        self.x += ((-target_x - self.x) * 0.1)
        self.y += ((-target_y - self.y) * 0.1)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Eco Ranger - Жақсартылған Нұсқа")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        self.current_level = 1
        self.score = 0
        self.health = 100

        # Камера
        self.camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)

        # Загрузка шрифтов
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 20)

        # Музыка
        self.current_music = None
        pygame.mixer.music.set_volume(0.3)

        # Группы спрайтов
        self.all_sprites = pygame.sprite.Group()
        self.trash_group = pygame.sprite.Group()
        self.obstacles_group = pygame.sprite.Group()
        self.particles_group = pygame.sprite.Group()
        self.ground_tiles = pygame.sprite.Group()
        self.decorations = pygame.sprite.Group()

        self.player = None
        self.recycling_station = None
        self.drone = None

        # Магазин и улучшения
        self.total_coins = 0  # Всего заработанных монет
        self.upgrades = {
            'bag': False,  # Большая сумка (вместимость x2)
            'tractor': False,  # Трактор (скорость сбора x2, вместимость x3)
            'advanced_drone': False  # Продвинутый дрон с pathfinding
        }
        self.upgrade_prices = {
            'bag': 100,
            'tractor': 250,
            'advanced_drone': 200
        }

        # Группа NPC
        self.npcs_group = pygame.sprite.Group()

        # Группа врагов-мусорщиков
        self.litterers_group = pygame.sprite.Group()

        # Новые группы для интерактивных элементов
        self.grass_tiles = pygame.sprite.Group()
        self.poison_plants = pygame.sprite.Group()
        self.heal_stations = pygame.sprite.Group()
        self.river_segments = pygame.sprite.Group()
        self.water_flow_particles = pygame.sprite.Group()

        # Состояние игрока
        self.player_poisoned = False
        self.poison_timer = 0
        self.poison_duration = 300  # 5 секунд
        self.player_in_blocked_water = False  # Флаг для замедления в воде

        # Состояние ручья
        self.river_blocked = True
        self.river_trash_count = 0
        self.river_trash_needed = 1

        # Катсцена
        self.cutscene_active = False
        self.cutscene_timer = 0
        self.cutscene_type = None
        self.celebrating_villagers = pygame.sprite.Group()

        # Система квестов
        self.active_quests = []  # Список активных квестов
        self.quest_objectives = pygame.sprite.Group()  # Объекты квестов (мусорные баки и т.д.)
        self.quest_givers = pygame.sprite.Group()  # НПС дающие квесты

        # Деревенские дома
        self.houses = pygame.sprite.Group()

        # Таймер и звезды
        self.level_time_limit = 180  # 3 минуты = 180 секунд
        self.level_timer = self.level_time_limit
        self.level_stars = 0  # 0-3 звезды
        self.level_best_times = {1: None, 2: None, 3: None}  # Лучшее время для каждого уровня
        self.level_best_stars = {1: 0, 2: 0, 3: 0}  # Лучшие звезды для каждого уровня

        # Комбо-система
        self.combo_count = 0  # Текущее комбо
        self.combo_timer = 0  # Таймер комбо (в кадрах)
        self.combo_max_time = 180  # 3 секунды (180 кадров при 60 FPS)
        self.combo_multiplier = 1.0  # Множитель очков
        self.max_combo = 0  # Лучшее комбо за сессию

        # Эффекты сочности (juice)
        self.screen_shake = 0  # Сила тряски экрана
        self.screen_shake_offset = (0, 0)  # Смещение для тряски
        self.flash_alpha = 0  # Прозрачность вспышки
        self.flash_color = WHITE  # Цвет вспышки

    def new_game(self):
        """Начать новую игру"""
        self.score = 0
        self.health = 100
        self.current_level = 1
        self.load_level(1)
        self.state = GameState.PLAYING

    def load_level(self, level_num):
        """Загрузить уровень"""
        # Очистка всех групп
        self.all_sprites.empty()
        self.trash_group.empty()
        self.obstacles_group.empty()
        self.particles_group.empty()
        self.ground_tiles.empty()
        self.decorations.empty()
        self.grass_tiles.empty()
        self.poison_plants.empty()
        self.heal_stations.empty()
        self.river_segments.empty()
        self.water_flow_particles.empty()
        self.npcs_group.empty()
        self.litterers_group.empty()
        self.quest_objectives.empty()
        self.quest_givers.empty()
        self.houses.empty()
        self.celebrating_villagers.empty()

        # Сброс состояний
        self.player_poisoned = False
        self.poison_timer = 0
        self.river_blocked = True
        self.river_trash_count = 0
        self.active_quests = []
        self.cutscene_active = False
        self.cutscene_timer = 0
        self.cutscene_type = None

        # Сброс таймера для нового уровня
        self.level_timer = self.level_time_limit
        self.level_stars = 0

        # Создание земли
        self.create_ground(level_num)

        # Создание игрока в центре
        self.player = Player(WORLD_WIDTH // 2, WORLD_HEIGHT // 2, self)
        self.all_sprites.add(self.player)

        # Применение улучшений к игроку
        if self.upgrades['bag']:
            self.player.max_trash = 10
        if self.upgrades['tractor']:
            self.player.max_trash = 15
            self.player.has_tractor = True

        # Создание станции переработки
        station_x = WORLD_WIDTH - 200
        station_y = 200
        self.recycling_station = RecyclingStation(station_x, station_y)
        self.all_sprites.add(self.recycling_station)

        # Уровень 1: Лес
        if level_num == 1:
            self.create_forest_level()
        # Уровень 2: Город
        elif level_num == 2:
            self.create_city_level()
        # Уровень 3: Пустыня
        elif level_num == 3:
            self.create_desert_level()
            # Создаем дрон для третьего уровня
            self.drone = Drone(self.player)
            self.all_sprites.add(self.drone)

    def create_ground(self, level_num):
        """Создать землю"""
        for x in range(0, WORLD_WIDTH, TILE_SIZE):
            for y in range(0, WORLD_HEIGHT, TILE_SIZE):
                tile = GroundTile(x, y, level_num)
                self.ground_tiles.add(tile)

    def create_forest_level(self):
        """Создать уровень 1 - Лес"""
        # Создаем ручей (заблокированный мусором)
        self.create_river()

        # Трава по всему лесу (текстурированная)
        for i in range(200):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            grass = GrassTile(x, y)
            self.grass_tiles.add(grass)
            self.all_sprites.add(grass)

        # Деревья разных размеров
        tree_positions = []
        for i in range(40):
            x = random.randint(100, WORLD_WIDTH - 100)
            y = random.randint(100, WORLD_HEIGHT - 100)

            # Проверка дистанции от других деревьев
            too_close = False
            for tx, ty in tree_positions:
                if math.sqrt((x - tx)**2 + (y - ty)**2) < 80:
                    too_close = True
                    break

            if not too_close:
                tree_type = random.choice(["tree", "tree_big", "tree_small"])
                tree = Obstacle(x, y, tree_type)
                self.obstacles_group.add(tree)
                self.all_sprites.add(tree)
                tree_positions.append((x, y))

        # Ядовитые растения среди травы (8-12 штук)
        for i in range(10):
            x = random.randint(100, WORLD_WIDTH - 100)
            y = random.randint(100, WORLD_HEIGHT - 100)
            poison = PoisonPlant(x, y)
            self.poison_plants.add(poison)
            self.all_sprites.add(poison)

        # Кусты и камни как декорации
        for i in range(60):
            x = random.randint(50, WORLD_WIDTH - 50)
            y = random.randint(50, WORLD_HEIGHT - 50)
            deco_type = random.choice(["bush", "rock", "flower", "mushroom"])
            deco = Decoration(x, y, deco_type, 1)
            self.decorations.add(deco)
            self.all_sprites.add(deco)

        # Мусор с проверкой коллизий (часть около ручья)
        trash_count = 0
        river_trash_count = 0
        attempts = 0

        # Находим сегмент блокировки
        blockage_segment = None
        for segment in self.river_segments:
            if segment.is_blockage_point:
                blockage_segment = segment
                break

        while trash_count < 1 and attempts < 150:
            # 1 мусор для теста
            if river_trash_count < 1 and blockage_segment:
                # Размещаем мусор в районе блокировки
                x = blockage_segment.rect.centerx + random.randint(-40, 40)
                y = blockage_segment.rect.centery + random.randint(-60, 60)
                is_river_trash = True
                river_trash_count += 1
            else:
                x = random.randint(200, WORLD_WIDTH - 200)
                y = random.randint(200, WORLD_HEIGHT - 200)
                is_river_trash = False

            # Проверка что не пересекается с препятствиями
            test_rect = pygame.Rect(x, y, 24, 24)
            collision = False

            for obs in self.obstacles_group:
                if test_rect.colliderect(obs.rect):
                    collision = True
                    break

            if not collision:
                trash = Trash(x, y, random.choice(["plastic", "paper", "bottle", "can"]), 1, river_trash=is_river_trash)
                self.trash_group.add(trash)
                self.all_sprites.add(trash)
                trash_count += 1

            attempts += 1

        # Деревенские дома (3 штуки в разных местах)
        house_positions = [
            (500, 300),
            (1800, 400),
            (1200, 1000)
        ]
        for hx, hy in house_positions:
            house = House(hx, hy)
            self.houses.add(house)
            self.all_sprites.add(house)

        # Создание квестов для уровня леса
        # Квест 1: Очистить мусорный бак около первого дома
        quest1 = Quest(
            quest_id=1,
            description="Қоқыс жәшігін тазала!",
            reward=50,
            objective_type="trash_bin",
            objective_count=1
        )

        # НПС дающий квест возле первого дома
        npc1 = QuestGiver(550, 320, quest1)
        self.quest_givers.add(npc1)
        self.npcs_group.add(npc1)
        self.all_sprites.add(npc1)

        # Мусорный бак для квеста (рядом с домом, но не слишком близко)
        bin1 = QuestObjective(650, 280, quest_id=1)
        quest1.objectives.append(bin1)
        self.quest_objectives.add(bin1)
        self.all_sprites.add(bin1)

        # Квест 2: Очистить мусорный бак около второго дома
        quest2 = Quest(
            quest_id=2,
            description="Қоқысты тазалауға көмектес!",
            reward=50,
            objective_type="trash_bin",
            objective_count=1
        )

        npc2 = QuestGiver(1850, 420, quest2)
        self.quest_givers.add(npc2)
        self.npcs_group.add(npc2)
        self.all_sprites.add(npc2)

        bin2 = QuestObjective(1750, 460, quest_id=2)
        quest2.objectives.append(bin2)
        self.quest_objectives.add(bin2)
        self.all_sprites.add(bin2)

    def create_river(self):
        """Создать извилистую реку в лесу"""
        # Создаем извилистую реку используя точки пути
        river_points = [
            (200, 0),      # Начало (верх карты)
            (250, 150),
            (180, 300),
            (220, 450),
            (300, 550),    # Точка блокировки (центр)
            (280, 700),
            (350, 850),
            (300, 1000),
            (400, 1150),
            (350, 1300),
            (400, WORLD_HEIGHT)  # Конец (низ карты)
        ]

        # Создаем сегменты реки между точками
        river_width = 80
        for i in range(len(river_points) - 1):
            x1, y1 = river_points[i]
            x2, y2 = river_points[i + 1]

            # Центр сегмента
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Длина сегмента
            length = int(math.sqrt((x2 - x1)**2 + (y2 - y1)**2))

            # Угол сегмента
            angle = math.atan2(y2 - y1, x2 - x1)

            # Создаем сегмент реки
            # Сегмент 4 (в центре) - место блокировки
            is_blocked_segment = (i == 4)

            segment = RiverSegment(
                center_x - river_width // 2,
                center_y - length // 2,
                river_width,
                length,
                flowing=False,
                angle=angle,
                is_blockage_point=is_blocked_segment
            )
            self.river_segments.add(segment)
            self.all_sprites.add(segment)

        # Спавн 3-5 мусорщиков в лесу
        num_litterers = random.randint(3, 5)
        for i in range(num_litterers):
            x = random.randint(200, WORLD_WIDTH - 200)
            y = random.randint(200, WORLD_HEIGHT - 200)
            litterer = Litterer(x, y, WORLD_WIDTH, WORLD_HEIGHT, level=1)
            self.litterers_group.add(litterer)
            self.all_sprites.add(litterer)

    def create_city_level(self):
        """Создать уровень 2 - Город"""
        # Дороги (сначала рисуем их как основу)
        # Горизонтальные дороги
        road1 = Road(0, 300, WORLD_WIDTH, 80, 'horizontal')
        road2 = Road(0, 800, WORLD_WIDTH, 80, 'horizontal')
        self.decorations.add(road1, road2)
        self.all_sprites.add(road1, road2)

        # Вертикальные дороги
        road3 = Road(600, 0, 80, WORLD_HEIGHT, 'vertical')
        road4 = Road(1400, 0, 80, WORLD_HEIGHT, 'vertical')
        self.decorations.add(road3, road4)
        self.all_sprites.add(road3, road4)

        # Здания (не на дорогах)
        for i in range(25):
            attempts = 0
            while attempts < 50:
                x = random.randint(200, WORLD_WIDTH - 200)
                y = random.randint(200, WORLD_HEIGHT - 200)

                # Проверка что не на дороге
                on_road = False
                if (280 < y < 380) or (780 < y < 880):  # горизонтальные дороги
                    on_road = True
                if (580 < x < 680) or (1380 < x < 1480):  # вертикальные дороги
                    on_road = True

                if not on_road:
                    building = Obstacle(x, y, "building")
                    self.obstacles_group.add(building)
                    self.all_sprites.add(building)
                    break
                attempts += 1

        # NPC на улицах
        npc_names = ["Анна", "Иван", "Мария", "Сергей", "Ольга", "Дмитрий"]
        for i in range(12):
            # Размещаем NPC вдоль дорог
            if i % 2 == 0:
                # На горизонтальных дорогах
                x = random.randint(100, WORLD_WIDTH - 100)
                y = random.choice([320, 820])
            else:
                # На вертикальных дорогах
                x = random.choice([620, 1420])
                y = random.randint(100, WORLD_HEIGHT - 100)

            name = random.choice(npc_names)
            npc = NPC(x, y, name)
            self.npcs_group.add(npc)
            self.all_sprites.add(npc)

        # Городские декорации
        for i in range(50):
            x = random.randint(50, WORLD_WIDTH - 50)
            y = random.randint(50, WORLD_HEIGHT - 50)
            deco_type = random.choice(["streetlight", "bench", "sign", "hydrant"])
            deco = Decoration(x, y, deco_type, 2)
            self.decorations.add(deco)
            self.all_sprites.add(deco)

        # Мусор
        trash_count = 0
        attempts = 0
        while trash_count < 1 and attempts < 150:
            x = random.randint(200, WORLD_WIDTH - 200)
            y = random.randint(200, WORLD_HEIGHT - 200)

            test_rect = pygame.Rect(x, y, 24, 24)
            collision = False

            for obs in self.obstacles_group:
                if test_rect.colliderect(obs.rect):
                    collision = True
                    break

            if not collision:
                trash_type = random.choice(["plastic", "paper", "glass"])
                trash = Trash(x, y, trash_type, 2)
                self.trash_group.add(trash)
                self.all_sprites.add(trash)
                trash_count += 1

            attempts += 1

        # Спавн 4-6 мусорщиков в городе (больше чем в лесу)
        num_litterers = random.randint(4, 6)
        for i in range(num_litterers):
            x = random.randint(200, WORLD_WIDTH - 200)
            y = random.randint(200, WORLD_HEIGHT - 200)
            litterer = Litterer(x, y, WORLD_WIDTH, WORLD_HEIGHT, level=2)
            self.litterers_group.add(litterer)
            self.all_sprites.add(litterer)

    def create_desert_level(self):
        """Создать уровень 3 - Пустыня"""
        # Токсичные препятствия и кактусы
        for i in range(30):
            x = random.randint(200, WORLD_WIDTH - 200)
            y = random.randint(200, WORLD_HEIGHT - 200)
            obs_type = random.choice(["toxic", "cactus"])
            obstacle = Obstacle(x, y, obs_type)
            self.obstacles_group.add(obstacle)
            self.all_sprites.add(obstacle)

        # Пустынные декорации
        for i in range(70):
            x = random.randint(50, WORLD_WIDTH - 50)
            y = random.randint(50, WORLD_HEIGHT - 50)
            deco_type = random.choice(["small_rock", "skull", "dead_tree", "tumbleweed"])
            deco = Decoration(x, y, deco_type, 3)
            self.decorations.add(deco)
            self.all_sprites.add(deco)

        # Мусор
        trash_count = 0
        attempts = 0
        while trash_count < 1 and attempts < 200:
            x = random.randint(200, WORLD_WIDTH - 200)
            y = random.randint(200, WORLD_HEIGHT - 200)

            test_rect = pygame.Rect(x, y, 24, 24)
            collision = False

            for obs in self.obstacles_group:
                if test_rect.colliderect(obs.rect):
                    collision = True
                    break

            if not collision:
                trash_type = random.choice(["plastic", "paper", "glass", "metal"])
                needs_drone = random.random() < 0.3
                trash = Trash(x, y, trash_type, 3, needs_drone=needs_drone)
                self.trash_group.add(trash)
                self.all_sprites.add(trash)
                trash_count += 1

            attempts += 1

        # Спавн 5-7 мусорщиков в пустыне (максимум)
        num_litterers = random.randint(5, 7)
        for i in range(num_litterers):
            x = random.randint(200, WORLD_WIDTH - 200)
            y = random.randint(200, WORLD_HEIGHT - 200)
            litterer = Litterer(x, y, WORLD_WIDTH, WORLD_HEIGHT, level=3)
            self.litterers_group.add(litterer)
            self.all_sprites.add(litterer)

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSE
                    elif self.state == GameState.PAUSE:
                        self.state = GameState.PLAYING
                    elif self.state == GameState.SHOP:
                        self.state = GameState.MENU
                    else:
                        self.running = False

                if self.state == GameState.MENU:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if SOUNDS_ENABLED:
                            sound_button.play()
                        self.new_game()
                    if event.key == pygame.K_s:
                        if SOUNDS_ENABLED:
                            sound_button.play()
                        self.state = GameState.SHOP

                if self.state == GameState.SHOP:
                    # Покупка в магазине
                    if event.key == pygame.K_1:  # Купить сумку
                        self.buy_upgrade('bag')
                    if event.key == pygame.K_2:  # Купить трактор
                        self.buy_upgrade('tractor')
                    if event.key == pygame.K_3:  # Купить продвинутый дрон
                        self.buy_upgrade('advanced_drone')

                if self.state == GameState.PLAYING:
                    # Удар по врагам (клавиша F)
                    if event.key == pygame.K_f:
                        # Создаем зону удара вокруг игрока
                        punch_rect = self.player.rect.inflate(30, 30)
                        for litterer in self.litterers_group:
                            if punch_rect.colliderect(litterer.rect) and not litterer.stunned:
                                litterer.get_stunned()
                                # Эффект удара (желтые частицы)
                                for _ in range(15):
                                    particle = Particle(litterer.rect.centerx,
                                                      litterer.rect.centery, YELLOW)
                                    self.particles_group.add(particle)
                                    self.all_sprites.add(particle)

                    if event.key == pygame.K_e:
                        result = self.player.collect_trash(self.trash_group)
                        collected = result["count"]
                        if collected > 0:
                            # Применяем урон от опасного мусора
                            if result["damage"] > 0:
                                self.health -= result["damage"]
                                # Красные частицы для урона
                                for _ in range(10):
                                    particle = Particle(self.player.rect.centerx,
                                                      self.player.rect.centery, RED)
                                    self.particles_group.add(particle)
                                    self.all_sprites.add(particle)

                            # Добавляем бонусные очки сразу
                            if result["bonus_points"] > 0:
                                self.score += int(result["bonus_points"] * self.combo_multiplier)
                                # Золотые частицы для бонусов
                                for _ in range(8):
                                    particle = Particle(self.player.rect.centerx,
                                                      self.player.rect.centery, (255, 215, 0))
                                    self.particles_group.add(particle)
                                    self.all_sprites.add(particle)

                            # Обновление комбо
                            self.combo_count += collected
                            self.combo_timer = self.combo_max_time

                            # Рассчитываем множитель (x1, x2, x3, x4...)
                            self.combo_multiplier = 1 + (self.combo_count // 3) * 0.5
                            self.combo_multiplier = min(self.combo_multiplier, 5.0)  # Макс x5

                            # Обновляем макс комбо
                            if self.combo_count > self.max_combo:
                                self.max_combo = self.combo_count

                            # Эффекты сочности при высоком комбо
                            if self.combo_multiplier >= 2.0:
                                # Тряска экрана (сильнее при выше комбо)
                                shake_intensity = min(int(self.combo_multiplier * 3), 15)
                                self.screen_shake = shake_intensity

                                # Цветная вспышка
                                if self.combo_multiplier >= 4:
                                    self.flash_color = (255, 100, 255)  # Фиолетовая
                                elif self.combo_multiplier >= 3:
                                    self.flash_color = (255, 50, 50)  # Красная
                                elif self.combo_multiplier >= 2:
                                    self.flash_color = ORANGE
                                self.flash_alpha = 50
                    # Рывок (Dash) на пробел или Shift
                    if event.key == pygame.K_SPACE or event.key == pygame.K_LSHIFT:
                        if self.player.perform_dash():
                            # Визуальные эффекты для dash
                            for _ in range(8):
                                particle = Particle(
                                    self.player.rect.centerx,
                                    self.player.rect.centery,
                                    (150, 200, 255)  # Голубые частицы
                                )
                                self.particles_group.add(particle)
                                self.all_sprites.add(particle)
                            # Небольшая тряска при dash
                            self.screen_shake = 3

                    # Исправлен конфликт: T для переключения дрона вместо D
                    if event.key == pygame.K_t and self.drone:
                        if hasattr(self.drone, 'toggle'):
                            self.drone.toggle()
                        else:
                            self.drone.active = not self.drone.active

                if self.state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_RETURN:
                        # Добавляем монеты за завершение уровня
                        self.total_coins += self.score
                        self.next_level()

                if self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self.state = GameState.MENU

            # Обработка мыши для продвинутого дрона
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == GameState.PLAYING and self.drone and isinstance(self.drone, AdvancedDrone):
                    # Конвертировать экранные координаты в мировые
                    mouse_x, mouse_y = event.pos
                    world_x = mouse_x + self.camera.x
                    world_y = mouse_y + self.camera.y
                    self.drone.set_target(world_x, world_y)

    def next_level(self):
        """Перейти на следующий уровень"""
        if self.current_level < 3:
            self.current_level += 1
            self.load_level(self.current_level)
            self.state = GameState.PLAYING
        else:
            self.state = GameState.MENU

    def buy_upgrade(self, upgrade_name):
        """Купить улучшение"""
        if self.upgrades[upgrade_name]:
            return  # Уже куплено

        price = self.upgrade_prices[upgrade_name]
        if self.total_coins >= price:
            self.total_coins -= price
            self.upgrades[upgrade_name] = True

            # Звук покупки
            if SOUNDS_ENABLED:
                sound_button.play()

            # Если купили продвинутый дрон, заменяем старый дрон
            if upgrade_name == 'advanced_drone' and self.current_level == 3:
                if self.drone:
                    self.drone.kill()
                self.drone = AdvancedDrone(self.player)
                self.all_sprites.add(self.drone)

    def update(self):
        """Обновление игровой логики"""
        if self.state != GameState.PLAYING and self.state != GameState.CUTSCENE:
            return

        # Проверка воды ПЕРЕД обновлением игрока (устанавливаем флаг замедления)
        self.player_in_blocked_water = False
        if self.current_level == 1:
            for river_segment in self.river_segments:
                water_state = river_segment.apply_current_to_player(self.player)
                if water_state == "blocked":
                    self.player_in_blocked_water = True
                    break

        # Обновление всех спрайтов (включая игрока - он двигается с учетом флага)
        self.all_sprites.update()

        # Применение течения реки ПОСЛЕ движения игрока
        if self.current_level == 1:
            for river_segment in self.river_segments:
                river_segment.push_player_by_current(self.player)

        # Обновление камеры
        self.camera.update(self.player)

        # Обновление NPC (проверка близости игрока)
        for npc in self.npcs_group:
            npc.check_player_nearby(self.player)

        # Обновление мусорщиков и выброс мусора
        for litterer in self.litterers_group:
            if litterer.should_drop_litter():
                # Определяем редкость мусора
                rand = random.random()
                if rand < 0.05:  # 5% шанс золотого
                    rarity = "golden"
                    particle_color = (255, 215, 0)
                elif rand < 0.15:  # 10% шанс опасного
                    rarity = "dangerous"
                    particle_color = (255, 0, 0)
                else:  # 85% обычный
                    rarity = "normal"
                    particle_color = (100, 70, 30)

                # Создаем новый мусор на месте мусорщика
                trash_type = random.choice(["plastic", "paper", "bottle", "can"])
                new_trash = Trash(
                    litterer.rect.centerx,
                    litterer.rect.centery,
                    trash_type,
                    self.current_level,
                    rarity=rarity
                )
                self.trash_group.add(new_trash)
                self.all_sprites.add(new_trash)

                # Небольшая визуальная обратная связь
                for _ in range(5 if rarity != "normal" else 3):
                    particle = Particle(
                        litterer.rect.centerx,
                        litterer.rect.centery,
                        particle_color
                    )
                    self.particles_group.add(particle)
                    self.all_sprites.add(particle)

        # Проверка столкновений с препятствиями
        for obstacle in self.obstacles_group:
            if self.player.rect.colliderect(obstacle.rect):
                self.player.rect.x -= self.player.vel_x
                self.player.rect.y -= self.player.vel_y

                if obstacle.toxic:
                    if random.random() < 0.02:
                        self.health -= 1
                        for _ in range(3):
                            particle = Particle(self.player.rect.centerx,
                                              self.player.rect.centery, RED)
                            self.particles_group.add(particle)
                            self.all_sprites.add(particle)

        # Старый дрон (уровень 3, базовый)
        if self.drone and isinstance(self.drone, Drone) and self.drone.active:
            if self.drone.collect_trash(self.trash_group):
                self.score += 15
                for _ in range(5):
                    particle = Particle(self.drone.rect.centerx,
                                      self.drone.rect.centery, BLUE)
                    self.particles_group.add(particle)
                    self.all_sprites.add(particle)

        # Продвинутый дрон (купленный в магазине)
        if self.drone and isinstance(self.drone, AdvancedDrone):
            # Автосбор мусора
            if self.drone.collect_trash_auto(self.trash_group):
                self.score += 15
                for _ in range(5):
                    particle = Particle(self.drone.rect.centerx,
                                      self.drone.rect.centery, GREEN)
                    self.particles_group.add(particle)
                    self.all_sprites.add(particle)

            # Передача мусора игроку
            collected = self.drone.return_to_player()
            if collected > 0:
                self.player.carrying_trash = min(
                    self.player.carrying_trash + collected,
                    self.player.max_trash
                )

        # Проверка столкновений с ядовитыми растениями (только лес)
        if self.current_level == 1:
            for poison_plant in self.poison_plants:
                if self.player.rect.colliderect(poison_plant.rect):
                    if not self.player_poisoned:
                        self.player_poisoned = True
                        self.poison_timer = self.poison_duration

                        # Звук отравления
                        if SOUNDS_ENABLED:
                            sound_poison.play()

                        # Создаем аптечку рядом
                        heal_x = poison_plant.rect.x + random.randint(80, 150)
                        heal_y = poison_plant.rect.y + random.randint(-50, 50)
                        heal = HealingStation(heal_x, heal_y)
                        self.heal_stations.add(heal)
                        self.all_sprites.add(heal)

                        # Эффект отравления
                        for _ in range(10):
                            particle = Particle(self.player.rect.centerx,
                                              self.player.rect.centery,
                                              (150, 50, 200))
                            self.particles_group.add(particle)
                            self.all_sprites.add(particle)

            # Обновление эффекта отравления
            if self.player_poisoned:
                self.poison_timer -= 1
                if self.poison_timer <= 0:
                    self.player_poisoned = False

            # Проверка столкновения с аптечкой
            for heal_station in self.heal_stations:
                if self.player.rect.colliderect(heal_station.rect):
                    if self.player_poisoned:
                        self.player_poisoned = False
                        self.poison_timer = 0
                        heal_station.kill()

                        # Звук лечения
                        if SOUNDS_ENABLED:
                            sound_heal.play()

                        # Эффект исцеления
                        for _ in range(15):
                            particle = Particle(self.player.rect.centerx,
                                              self.player.rect.centery,
                                              (0, 255, 100))
                            self.particles_group.add(particle)
                            self.all_sprites.add(particle)

        # Проверка доставки мусора
        if self.player.carrying_trash and self.player.rect.colliderect(self.recycling_station.rect):
            # Проверяем есть ли мусор от ручья
            delivered_river_trash = False
            for trash in list(self.trash_group):
                if trash.river_trash and self.player.carrying_trash > 0:
                    delivered_river_trash = True
                    break

            # Очки с учетом комбо-множителя
            base_points = self.player.carrying_trash * 10
            total_points = int(base_points * self.combo_multiplier)
            self.score += total_points
            self.player.carrying_trash = 0

            # Звук выброса мусора
            if SOUNDS_ENABLED:
                sound_trash_dump.play()

            # Больше частиц при высоком комбо
            particle_count = 15 + int(self.combo_multiplier * 5)
            for _ in range(particle_count):
                particle = Particle(self.recycling_station.rect.centerx,
                                  self.recycling_station.rect.centery,
                                  random.choice([GREEN, YELLOW, BLUE]))
                self.particles_group.add(particle)
                self.all_sprites.add(particle)

        # Проверка разблокировки ручья (уровень 1)
        if self.current_level == 1 and self.river_blocked:
            # Подсчет мусора блокирующего ручей
            river_trash_remaining = sum(1 for trash in self.trash_group if trash.river_trash)

            if river_trash_remaining == 0:
                # Разблокировать ручей!
                self.river_blocked = False
                for segment in self.river_segments:
                    segment.start_flowing()

                # Создать эффект течения воды
                for _ in range(50):
                    for segment in self.river_segments:
                        particle = WaterFlowParticle(
                            segment.rect.x + random.randint(0, segment.width),
                            segment.rect.y + random.randint(0, segment.height)
                        )
                        self.water_flow_particles.add(particle)
                        self.all_sprites.add(particle)

                # Запуск катсцены праздования!
                self.start_river_restoration_cutscene()

        # Генерация частиц воды ТОЛЬКО если ручей разблокирован И течет
        if self.current_level == 1 and not self.river_blocked:
            if random.random() < 0.15:  # 15% шанс каждый кадр
                for segment in self.river_segments:
                    if segment.flowing:  # Только текущие сегменты
                        particle = WaterFlowParticle(
                            segment.rect.x + random.randint(0, segment.width),
                            segment.rect.y + random.randint(0, segment.height // 2)
                        )
                        self.water_flow_particles.add(particle)
                        self.all_sprites.add(particle)

        # Логика квестов
        if self.current_level == 1:
            # Проверка взаимодействия с quest givers
            for quest_giver in self.quest_givers:
                if quest_giver.check_player_nearby(self.player):
                    # Проверяем нажата ли клавиша E для взаимодействия
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_e] and quest_giver.has_quest:
                        # Активировать квест
                        if quest_giver.quest not in self.active_quests:
                            self.active_quests.append(quest_giver.quest)
                            quest_giver.has_quest = False  # Квест выдан

            # Проверка сбора quest objectives
            for objective in self.quest_objectives:
                if not objective.collected and self.player.rect.colliderect(objective.rect):
                    # Проверяем что квест активен
                    for quest in self.active_quests:
                        if quest.quest_id == objective.quest_id and not quest.completed:
                            objective.collected = True
                            quest.current_count += 1

                            # Проверка завершения квеста
                            if quest.current_count >= quest.objective_count:
                                quest.completed = True
                                self.total_coins += quest.reward
                                self.score += quest.reward

                                # Эффект завершения квеста
                                for _ in range(20):
                                    particle = Particle(
                                        objective.rect.centerx,
                                        objective.rect.centery,
                                        YELLOW
                                    )
                                    self.particles_group.add(particle)
                                    self.all_sprites.add(particle)

                                objective.kill()  # Удаляем объект

        # Обновление катсцены
        if self.cutscene_active:
            self.cutscene_timer += 1
            # Катсцена длится 180 кадров (3 секунды при 60 FPS)
            if self.cutscene_timer >= 180:
                self.cutscene_active = False
                self.cutscene_timer = 0
                self.cutscene_type = None
                self.celebrating_villagers.empty()
                self.state = GameState.PLAYING

        # Обновление таймера уровня
        if self.state == GameState.PLAYING:
            self.level_timer -= 1 / FPS  # Уменьшаем на 1/60 секунды каждый кадр
            if self.level_timer <= 0:
                self.level_timer = 0
                self.state = GameState.GAME_OVER  # Время вышло = проигрыш

        # Обновление комбо-таймера
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                # Сброс комбо
                self.combo_count = 0
                self.combo_multiplier = 1.0

        # Обновление эффектов сочности
        if self.screen_shake > 0:
            self.screen_shake -= 1
            # Случайное смещение для тряски
            shake_amount = self.screen_shake * 0.5
            self.screen_shake_offset = (
                random.randint(-int(shake_amount), int(shake_amount)),
                random.randint(-int(shake_amount), int(shake_amount))
            )
        else:
            self.screen_shake_offset = (0, 0)

        # Затухание вспышки
        if self.flash_alpha > 0:
            self.flash_alpha -= 10

        # Условия победы/поражения
        if len(self.trash_group) == 0 and self.player.carrying_trash == 0:
            # Рассчитываем звезды на основе оставшегося времени
            time_spent = self.level_time_limit - self.level_timer
            if time_spent <= 90:  # Менее 1:30
                self.level_stars = 3
            elif time_spent <= 120:  # Менее 2:00
                self.level_stars = 2
            elif time_spent <= 150:  # Менее 2:30
                self.level_stars = 1
            else:
                self.level_stars = 1  # Минимум 1 звезда за прохождение

            # Сохраняем лучшие результаты
            if self.level_best_times[self.current_level] is None or time_spent < self.level_best_times[self.current_level]:
                self.level_best_times[self.current_level] = time_spent
            if self.level_stars > self.level_best_stars[self.current_level]:
                self.level_best_stars[self.current_level] = self.level_stars

            self.state = GameState.LEVEL_COMPLETE

        if self.health <= 0:
            self.state = GameState.GAME_OVER

    def draw(self):
        """Отрисовка"""
        self.screen.fill(BLACK)

        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.SHOP:
            self.draw_shop()
        elif self.state == GameState.PLAYING:
            self.draw_game()
            self.draw_hud()
        elif self.state == GameState.PAUSE:
            self.draw_game()
            self.draw_hud()
            self.draw_pause()
        elif self.state == GameState.CUTSCENE:
            self.draw_cutscene()
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_game()
            self.draw_level_complete()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()

        pygame.display.flip()

    def play_music(self, music_file):
        """Воспроизвести музыку с зацикливанием"""
        if self.current_music != music_file:
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.play(-1)  # -1 = бесконечное зацикливание
                self.current_music = music_file
            except:
                pass

    def draw_menu(self):
        """Отрисовка меню - современный дизайн"""
        # Воспроизводим музыку меню
        self.play_music('menu_music.wav')

        # Анимированный градиентный фон (зелено-синий природный)
        time_offset = pygame.time.get_ticks() / 1000
        for y in range(0, SCREEN_HEIGHT, 2):
            ratio = y / SCREEN_HEIGHT
            wave = math.sin(ratio * 3 + time_offset) * 20

            r = int(20 + ratio * 40 + wave)
            g = int(80 + ratio * 60 + wave)
            b = int(60 + ratio * 40)

            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y), 2)

        # Декоративные элементы (листья падающие)
        for i in range(15):
            leaf_y = (pygame.time.get_ticks() // 20 + i * 50) % SCREEN_HEIGHT
            leaf_x = 100 + i * 80 + int(math.sin(leaf_y / 50) * 30)
            pygame.draw.circle(self.screen, (100, 200, 100, 100), (leaf_x, leaf_y), 8)
            pygame.draw.circle(self.screen, (80, 180, 80), (leaf_x, leaf_y), 8, 2)

        # Главная панель меню
        panel_width = 900
        panel_height = 600
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = 50

        # Панель с закругленными углами и тенью
        shadow = pygame.Surface((panel_width + 10, panel_height + 10), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 100))
        self.screen.blit(shadow, (panel_x + 5, panel_y + 5))

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        # Градиент на панели
        for i in range(panel_height):
            alpha = 220 - int(i / panel_height * 40)
            pygame.draw.line(panel, (30, 60, 40, alpha), (0, i), (panel_width, i))

        pygame.draw.rect(panel, (100, 200, 150), (0, 0, panel_width, panel_height), 5, 15)
        self.screen.blit(panel, (panel_x, panel_y))

        # ЛОГОТИП с эффектом
        logo_y = panel_y + 40
        pulse = abs(math.sin(time_offset * 2)) * 10

        # Тени заголовка (многослойные)
        for offset in [(8, 8), (5, 5), (2, 2)]:
            alpha = int(100 - offset[0] * 10)
            shadow_surf = self.font_large.render("ECO RANGER", True, (0, 50, 0))
            shadow_surf.set_alpha(alpha)
            shadow_rect = shadow_surf.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], logo_y + offset[1]))
            self.screen.blit(shadow_surf, shadow_rect)

        # Основной заголовок с пульсацией
        title = self.font_large.render("ECO RANGER", True, (100 + int(pulse), 255, 100 + int(pulse)))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, logo_y))
        self.screen.blit(title, title_rect)

        # Подзаголовок с иконкой
        subtitle_y = logo_y + 60
        pygame.draw.circle(self.screen, (50, 200, 50), (SCREEN_WIDTH // 2 - 150, subtitle_y), 12)
        pygame.draw.circle(self.screen, WHITE, (SCREEN_WIDTH // 2 - 150, subtitle_y), 12, 2)

        subtitle = self.font_medium.render("Планетаны сақта!", True, (200, 255, 200))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2 + 20, subtitle_y))
        self.screen.blit(subtitle, subtitle_rect)

        # Монеты с красивой иконкой
        coin_y = subtitle_y + 60
        coin_panel = pygame.Surface((250, 50), pygame.SRCALPHA)
        coin_panel.fill((255, 200, 0, 180))
        pygame.draw.rect(coin_panel, (255, 215, 0), (0, 0, 250, 50), 3, 10)
        self.screen.blit(coin_panel, (SCREEN_WIDTH // 2 - 125, coin_y - 15))

        # Иконка монеты
        pygame.draw.circle(self.screen, YELLOW, (SCREEN_WIDTH // 2 - 80, coin_y + 10), 18)
        pygame.draw.circle(self.screen, ORANGE, (SCREEN_WIDTH // 2 - 80, coin_y + 10), 18, 3)
        pygame.draw.circle(self.screen, ORANGE, (SCREEN_WIDTH // 2 - 80, coin_y + 10), 12, 2)

        coins_text = self.font_medium.render(f"{self.total_coins}", True, WHITE)
        coins_rect = coins_text.get_rect(center=(SCREEN_WIDTH // 2 + 10, coin_y + 10))
        self.screen.blit(coins_text, coins_rect)

        # КНОПКИ (красивые современные)
        buttons = [
            {"text": "ОЙЫНДЫ БАСТАУ", "key": "ENTER", "color": (50, 200, 50), "y_offset": 0},
            {"text": "ДҮКЕН", "key": "S", "color": (200, 150, 50), "y_offset": 80},
            {"text": "ШЫҒУ", "key": "ESC", "color": (200, 50, 50), "y_offset": 160}
        ]

        button_start_y = coin_y + 100
        for button in buttons:
            btn_y = button_start_y + button["y_offset"]
            btn_width = 400
            btn_height = 60
            btn_x = SCREEN_WIDTH // 2 - btn_width // 2

            # Тень кнопки
            shadow_btn = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
            shadow_btn.fill((0, 0, 0, 80))
            self.screen.blit(shadow_btn, (btn_x + 4, btn_y + 4))

            # Кнопка с градиентом
            btn_surf = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
            base_color = button["color"]
            for i in range(btn_height):
                ratio = i / btn_height
                r = int(base_color[0] * (1 - ratio * 0.3))
                g = int(base_color[1] * (1 - ratio * 0.3))
                b = int(base_color[2] * (1 - ratio * 0.3))
                pygame.draw.line(btn_surf, (r, g, b, 230), (5, i), (btn_width - 5, i))

            pygame.draw.rect(btn_surf, WHITE, (0, 0, btn_width, btn_height), 3, 12)
            self.screen.blit(btn_surf, (btn_x, btn_y))

            # Текст кнопки
            btn_text = self.font_medium.render(button["text"], True, WHITE)
            btn_text_rect = btn_text.get_rect(center=(SCREEN_WIDTH // 2, btn_y + btn_height // 2))
            self.screen.blit(btn_text, btn_text_rect)

            # Подсказка клавиши
            key_hint = self.font_tiny.render(f"[{button['key']}]", True, (200, 200, 200))
            key_hint_rect = key_hint.get_rect(center=(SCREEN_WIDTH // 2 + btn_width // 2 - 50, btn_y + btn_height // 2))
            self.screen.blit(key_hint, key_hint_rect)

        # Управление внизу (компактно)
        control_y = SCREEN_HEIGHT - 60
        controls = "WASD/Бағдаршалар - қозғалу  |  E - жинау  |  T - дрон"
        control_text = self.font_tiny.render(controls, True, (150, 200, 150))
        control_rect = control_text.get_rect(center=(SCREEN_WIDTH // 2, control_y))
        self.screen.blit(control_text, control_rect)

    def draw_game(self):
        """Отрисовка игрового процесса"""
        # Воспроизводим игровую музыку
        self.play_music('game_music.wav')

        # Рисуем тайлы земли с учетом камеры и тряски
        for tile in self.ground_tiles:
            screen_pos = self.camera.apply(tile, self.screen_shake_offset)
            # Отрисовываем только видимые тайлы
            if -TILE_SIZE < screen_pos[0] < SCREEN_WIDTH and -TILE_SIZE < screen_pos[1] < SCREEN_HEIGHT:
                self.screen.blit(tile.image, screen_pos)

        # ВАЖНО: Рисуем реку РАНЬШЕ всех объектов (на уровне леса)
        if self.current_level == 1:
            for river_segment in self.river_segments:
                screen_pos = self.camera.apply(river_segment, self.screen_shake_offset)
                if -200 < screen_pos[0] < SCREEN_WIDTH + 200 and -200 < screen_pos[1] < SCREEN_HEIGHT + 200:
                    self.screen.blit(river_segment.image, screen_pos)

        # Сортируем спрайты по Y для правильного наложения (исключая реку)
        visible_sprites = []
        for sprite in self.all_sprites:
            # Пропускаем сегменты реки - они уже нарисованы
            if sprite in self.river_segments:
                continue

            screen_pos = self.camera.apply(sprite, self.screen_shake_offset)
            if -100 < screen_pos[0] < SCREEN_WIDTH + 100 and -100 < screen_pos[1] < SCREEN_HEIGHT + 100:
                visible_sprites.append((sprite, screen_pos))

        # Сортируем по Y координате
        visible_sprites.sort(key=lambda x: x[0].rect.bottom)

        # Рисуем сначала декорации
        for sprite, screen_pos in visible_sprites:
            if sprite in self.decorations:
                self.screen.blit(sprite.image, screen_pos)
                # Тени для декораций
                if hasattr(sprite, 'draw_shadow'):
                    sprite.draw_shadow(self.screen, screen_pos)

        # Затем все остальное
        for sprite, screen_pos in visible_sprites:
            if sprite not in self.decorations:
                self.screen.blit(sprite.image, screen_pos)

        # Цветная вспышка при высоком комбо
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surface.fill((*self.flash_color, self.flash_alpha))
            self.screen.blit(flash_surface, (0, 0))

        # Сообщения от NPC
        for npc in self.npcs_group:
            if hasattr(npc, 'showing_message') and npc.showing_message:
                screen_pos = self.camera.apply(npc, self.screen_shake_offset)
                # Облако с сообщением над NPC
                message_surface = self.font_tiny.render(npc.message, True, BLACK)
                msg_width = message_surface.get_width() + 20
                msg_height = 30

                # Белое облако сообщения
                bubble_rect = pygame.Rect(screen_pos[0] - msg_width//2 + 17,
                                         screen_pos[1] - 50, msg_width, msg_height)
                pygame.draw.rect(self.screen, WHITE, bubble_rect, 0, 8)
                pygame.draw.rect(self.screen, BLACK, bubble_rect, 2, 8)

                # Текст
                self.screen.blit(message_surface, (bubble_rect.x + 10, bubble_rect.y + 7))

    def draw_hud(self):
        """Отрисовка интерфейса"""
        # Полупрозрачная панель с градиентом
        hud_panel = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
        for y in range(100):
            alpha = int(180 - (y * 1.5))
            color = (0, 0, 0, alpha)
            pygame.draw.rect(hud_panel, color, (0, y, SCREEN_WIDTH, 1))
        self.screen.blit(hud_panel, (0, 0))

        # ТАЙМЕР (большой, в центре вверху)
        minutes = int(self.level_timer // 60)
        seconds = int(self.level_timer % 60)
        timer_text = f"{minutes}:{seconds:02d}"

        # Цвет таймера зависит от оставшегося времени
        if self.level_timer > 60:
            timer_color = GREEN
        elif self.level_timer > 30:
            timer_color = YELLOW
        else:
            timer_color = RED

        # Панель таймера
        timer_panel = pygame.Surface((200, 60), pygame.SRCALPHA)
        timer_panel.fill((0, 0, 0, 180))
        pygame.draw.rect(timer_panel, timer_color, (0, 0, 200, 60), 3, 10)
        self.screen.blit(timer_panel, (SCREEN_WIDTH // 2 - 100, 15))

        # Текст таймера
        timer_surf = self.font_large.render(timer_text, True, timer_color)
        timer_rect = timer_surf.get_rect(center=(SCREEN_WIDTH // 2, 45))
        self.screen.blit(timer_surf, timer_rect)

        # Очки с иконкой
        pygame.draw.circle(self.screen, YELLOW, (35, 25), 15)
        score_text = self.font_small.render(f"{self.score}", True, WHITE)
        self.screen.blit(score_text, (55, 12))

        # Уровень
        level_text = self.font_small.render(f"Деңгей {self.current_level}/3", True, WHITE)
        self.screen.blit(level_text, (20, 55))

        # Оставшийся мусор
        remaining_trash = len(self.trash_group)
        trash_color = RED if remaining_trash > 0 else GREEN
        trash_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.rect(trash_icon, trash_color, (5, 5, 20, 20), 0, 3)
        self.screen.blit(trash_icon, (SCREEN_WIDTH // 2 - 100, 10))

        trash_count_text = self.font_small.render(f"{remaining_trash}", True, trash_color)
        self.screen.blit(trash_count_text, (SCREEN_WIDTH // 2 - 60, 12))

        # Здоровье
        health_text = self.font_small.render("HP", True, WHITE)
        self.screen.blit(health_text, (SCREEN_WIDTH - 230, 12))

        # Красивая полоса здоровья
        bar_width = 180
        bar_height = 28
        bar_x = SCREEN_WIDTH - 200
        bar_y = 50

        # Фон полосы
        pygame.draw.rect(self.screen, (50, 0, 0), (bar_x, bar_y, bar_width, bar_height), 0, 5)

        # Градиент здоровья
        health_width = int((self.health / 100) * bar_width)
        for x in range(health_width):
            ratio = x / bar_width
            if self.health > 50:
                color = (int(100 * ratio), 255 - int(100 * ratio), 0)
            else:
                color = (255, int(100 * (1 - ratio)), 0)
            pygame.draw.rect(self.screen, color, (bar_x + x, bar_y + 2, 1, bar_height - 4))

        # Обводка
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 3, 5)

        # Текст HP
        hp_text = self.font_small.render(f"{self.health}", True, WHITE)
        hp_rect = hp_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
        self.screen.blit(hp_text, hp_rect)

        # Инвентарь
        if self.player and self.player.carrying_trash > 0:
            inv_panel = pygame.Surface((200, 50), pygame.SRCALPHA)
            inv_panel.fill((0, 100, 0, 200))
            self.screen.blit(inv_panel, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70))

            inv_text = self.font_small.render(f"Сөмке: {self.player.carrying_trash}/{self.player.max_trash}", True, WHITE)
            self.screen.blit(inv_text, (SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 63))

        # Статус дрона
        if self.current_level == 3 and self.drone:
            drone_panel = pygame.Surface((120, 35), pygame.SRCALPHA)
            drone_color = (0, 150, 0, 200) if self.drone.active else (150, 0, 0, 200)
            drone_panel.fill(drone_color)
            self.screen.blit(drone_panel, (350, 10))

            drone_status = "ДРОН ҚОС" if self.drone.active else "ДРОН ӨШІР"
            drone_text = self.font_small.render(drone_status, True, WHITE)
            self.screen.blit(drone_text, (360, 15))

        # Индикатор Dash (слева внизу)
        dash_panel_w = 150
        dash_panel_h = 50
        dash_x = 20
        dash_y = SCREEN_HEIGHT - 130

        # Фон панели
        dash_panel = pygame.Surface((dash_panel_w, dash_panel_h), pygame.SRCALPHA)
        dash_panel.fill((50, 50, 50, 180))
        pygame.draw.rect(dash_panel, (150, 200, 255), (0, 0, dash_panel_w, dash_panel_h), 2, 5)
        self.screen.blit(dash_panel, (dash_x, dash_y))

        # Текст DASH
        dash_label = self.font_tiny.render("СЕКІРУ [SPACE]", True, (150, 200, 255))
        self.screen.blit(dash_label, (dash_x + 10, dash_y + 5))

        # Прогресс-бар cooldown
        bar_width = dash_panel_w - 20
        bar_height = 10
        bar_x = dash_x + 10
        bar_y = dash_y + 30

        # Фон бара
        pygame.draw.rect(self.screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height), 0, 3)

        # Заполнение бара
        if self.player.dash_cooldown > 0:
            # Перезарядка
            progress = 1 - (self.player.dash_cooldown / self.player.dash_cooldown_max)
            fill_width = int(bar_width * progress)
            bar_color = (100, 100, 100) if fill_width < bar_width else (150, 200, 255)
            pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, fill_width, bar_height), 0, 3)

            # Текст cooldown
            cd_text = self.font_tiny.render(f"{self.player.dash_cooldown // 60 + 1}с", True, WHITE)
            self.screen.blit(cd_text, (bar_x + bar_width // 2 - 10, bar_y - 15))
        else:
            # Готов к использованию
            pygame.draw.rect(self.screen, (150, 255, 150), (bar_x, bar_y, bar_width, bar_height), 0, 3)
            ready_text = self.font_tiny.render("ДАЙЫН!", True, (150, 255, 150))
            self.screen.blit(ready_text, (bar_x + bar_width // 2 - 20, bar_y - 15))

        # Статус отравления (только на уровне леса)
        if self.current_level == 1 and self.player_poisoned:
            poison_panel = pygame.Surface((180, 45), pygame.SRCALPHA)
            poison_panel.fill((120, 50, 150, 200))
            self.screen.blit(poison_panel, (SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 130))

            poison_text = self.font_small.render("УЛАНДЫ!", True, (255, 100, 255))
            self.screen.blit(poison_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT - 125))

            # Таймер
            time_left = self.poison_timer // 60
            timer_text = self.font_tiny.render(f"Дәріхананы тап! {time_left}с", True, WHITE)
            self.screen.blit(timer_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT - 105))

        # Статус ручья (только на уровне леса)
        if self.current_level == 1:
            river_trash_count = sum(1 for trash in self.trash_group if trash.river_trash)
            if river_trash_count > 0:
                river_panel = pygame.Surface((220, 40), pygame.SRCALPHA)
                river_panel.fill((0, 100, 150, 200))
                self.screen.blit(river_panel, (20, SCREEN_HEIGHT - 60))

                river_text = self.font_tiny.render(f"Өзен бұғатталған! Қоқыс: {river_trash_count}", True, WATER_BLUE)
                self.screen.blit(river_text, (30, SCREEN_HEIGHT - 50))
            elif not self.river_blocked:
                river_panel = pygame.Surface((180, 35), pygame.SRCALPHA)
                river_panel.fill((0, 150, 200, 200))
                self.screen.blit(river_panel, (20, SCREEN_HEIGHT - 55))

                river_text = self.font_small.render("Өзен ағады!", True, WHITE)
                self.screen.blit(river_text, (30, SCREEN_HEIGHT - 48))

        # КОМБО (компактное отображение справа вверху)
        if self.combo_count > 0:
            combo_x = SCREEN_WIDTH - 220
            combo_y = 95

            # Пульсирующий эффект (меньше)
            pulse = abs(math.sin(pygame.time.get_ticks() / 100)) * 3

            # Цвет зависит от множителя
            if self.combo_multiplier >= 4:
                combo_color = (255, 100, 255)  # Фиолетовый
            elif self.combo_multiplier >= 3:
                combo_color = (255, 50, 50)  # Красный
            elif self.combo_multiplier >= 2:
                combo_color = ORANGE  # Оранжевый
            else:
                combo_color = YELLOW  # Желтый

            # Панель комбо (компактная)
            combo_width = 200 + int(pulse)
            combo_height = 70
            combo_panel = pygame.Surface((combo_width, combo_height), pygame.SRCALPHA)
            combo_panel.fill((0, 0, 0, 180))
            pygame.draw.rect(combo_panel, combo_color, (0, 0, combo_width, combo_height), 3, 10)
            self.screen.blit(combo_panel, (combo_x, combo_y))

            # Текст COMBO (меньше)
            combo_label = self.font_medium.render("COMBO", True, combo_color)
            combo_label_rect = combo_label.get_rect(center=(combo_x + combo_width // 2, combo_y + 20))
            self.screen.blit(combo_label, combo_label_rect)

            # Множитель
            multiplier_text = f"x{self.combo_multiplier:.1f}"
            multiplier_surf = self.font_medium.render(multiplier_text, True, WHITE)
            multiplier_rect = multiplier_surf.get_rect(center=(combo_x + combo_width // 2, combo_y + 45))
            self.screen.blit(multiplier_surf, multiplier_rect)

            # Прогресс-бар комбо-таймера (внизу панели, тоньше)
            bar_width = combo_width - 20
            bar_height = 6
            bar_x = combo_x + 10
            bar_y = combo_y + combo_height - 12

            # Фон бара
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), 0, 3)

            # Заполненная часть
            fill_width = int((self.combo_timer / self.combo_max_time) * bar_width)
            if fill_width > 0:
                pygame.draw.rect(self.screen, combo_color, (bar_x, bar_y, fill_width, bar_height), 0, 3)

            # Обводка
            pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1, 3)

        # Активные квесты
        if self.active_quests:
            quest_y = 150
            for quest in self.active_quests:
                if not quest.completed:
                    quest_panel = pygame.Surface((280, 60), pygame.SRCALPHA)
                    quest_panel.fill((200, 150, 0, 200))
                    self.screen.blit(quest_panel, (SCREEN_WIDTH - 300, quest_y))

                    quest_title = self.font_tiny.render("ТАПСЫРМА:", True, YELLOW)
                    self.screen.blit(quest_title, (SCREEN_WIDTH - 290, quest_y + 5))

                    quest_desc = self.font_tiny.render(quest.description, True, WHITE)
                    self.screen.blit(quest_desc, (SCREEN_WIDTH - 290, quest_y + 25))

                    reward_text = self.font_tiny.render(f"Сыйлық: {quest.reward} монета", True, GREEN)
                    self.screen.blit(reward_text, (SCREEN_WIDTH - 290, quest_y + 42))

                    quest_y += 70

        # Подсказка взаимодействия с NPC
        if self.current_level == 1:
            for quest_giver in self.quest_givers:
                if quest_giver.check_player_nearby(self.player):
                    hint_panel = pygame.Surface((200, 35), pygame.SRCALPHA)
                    hint_panel.fill((255, 215, 0, 220))
                    self.screen.blit(hint_panel, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 120))

                    hint_text = self.font_small.render("E-ны бас", True, BLACK)
                    self.screen.blit(hint_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 113))

        # Миникарта
        self.draw_minimap()

    def draw_minimap(self):
        """Миникарта"""
        size = 180
        x = SCREEN_WIDTH - size - 15
        y = SCREEN_HEIGHT - size - 15

        # Фон с градиентом
        minimap = pygame.Surface((size, size), pygame.SRCALPHA)
        for i in range(size):
            alpha = int(200 - (i * 0.5))
            pygame.draw.rect(minimap, (20, 20, 20, alpha), (0, i, size, 1))
        self.screen.blit(minimap, (x, y))

        # Рамка
        pygame.draw.rect(self.screen, WHITE, (x, y, size, size), 3, 5)

        # Масштаб
        scale_x = size / WORLD_WIDTH
        scale_y = size / WORLD_HEIGHT

        # Игрок
        if self.player:
            px = x + int(self.player.rect.centerx * scale_x)
            py = y + int(self.player.rect.centery * scale_y)
            pygame.draw.circle(self.screen, BLUE, (px, py), 5)
            pygame.draw.circle(self.screen, WHITE, (px, py), 5, 1)

        # Мусор
        for trash in self.trash_group:
            tx = x + int(trash.rect.centerx * scale_x)
            ty = y + int(trash.rect.centery * scale_y)
            color = RED if trash.needs_drone else YELLOW
            pygame.draw.circle(self.screen, color, (tx, ty), 3)

        # Станция
        if self.recycling_station:
            sx = x + int(self.recycling_station.rect.centerx * scale_x)
            sy = y + int(self.recycling_station.rect.centery * scale_y)
            pygame.draw.rect(self.screen, GREEN, (sx - 4, sy - 4, 8, 8), 0, 2)

        # Заголовок
        label = self.font_tiny.render("КАРТА", True, WHITE)
        self.screen.blit(label, (x + 8, y + 5))

    def draw_pause(self):
        """Пауза"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render("КІДІРІС", True, YELLOW)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        # Тень
        shadow = self.font_large.render("КІДІРІС", True, DARK_GRAY)
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, SCREEN_HEIGHT // 2 + 3))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(pause_text, pause_rect)

    def draw_level_complete(self):
        """Уровень пройден"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        complete_text = self.font_large.render("ДЕҢГЕЙ ӨТІЛДІ!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))

        shadow = self.font_large.render("ДЕҢГЕЙ ӨТІЛДІ!", True, DARK_GREEN)
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, SCREEN_HEIGHT // 2 - 57))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(complete_text, complete_rect)

        # Звезды!
        star_y = SCREEN_HEIGHT // 2
        star_spacing = 80
        star_start_x = SCREEN_WIDTH // 2 - (self.level_stars * star_spacing) // 2

        for i in range(3):
            star_x = star_start_x + i * star_spacing
            star_color = YELLOW if i < self.level_stars else GRAY

            # Рисуем звезду (5 лучей)
            star_size = 35
            points = []
            for j in range(10):
                angle = math.pi / 2 + j * math.pi / 5
                radius = star_size if j % 2 == 0 else star_size // 2
                px = star_x + int(math.cos(angle) * radius)
                py = star_y + int(math.sin(angle) * radius)
                points.append((px, py))

            pygame.draw.polygon(self.screen, star_color, points)
            pygame.draw.polygon(self.screen, WHITE, points, 2)

        # Время
        time_spent = self.level_time_limit - self.level_timer
        time_minutes = int(time_spent // 60)
        time_seconds = int(time_spent % 60)
        time_text = self.font_medium.render(f"Уақыт: {time_minutes}:{time_seconds:02d}", True, WHITE)
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(time_text, time_rect)

        score_text = self.font_medium.render(f"Ұпай: {self.score}", True, YELLOW)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(score_text, score_rect)

        continue_text = self.font_small.render("ENTER-ді бас", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.screen.blit(continue_text, continue_rect)

    def draw_game_over(self):
        """Game Over"""
        # Красный градиент
        for y in range(0, SCREEN_HEIGHT, 5):
            intensity = int(100 - (y / SCREEN_HEIGHT) * 50)
            color = (intensity, 0, 0)
            pygame.draw.rect(self.screen, color, (0, y, SCREEN_WIDTH, 5))

        game_over_text = self.font_large.render("ОЙЫН АЯҚТАЛДЫ", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))

        shadow = self.font_large.render("ОЙЫН АЯҚТАЛДЫ", True, DARK_GRAY)
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 4, SCREEN_HEIGHT // 2 - 46))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(game_over_text, game_over_rect)

        score_text = self.font_medium.render(f"Ұпай: {self.score}", True, YELLOW)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(score_text, score_rect)

        continue_text = self.font_small.render("ENTER - мәзірге", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        self.screen.blit(continue_text, continue_rect)

    def draw_shop(self):
        """Отрисовка магазина - современный дизайн"""
        # Воспроизводим музыку магазина
        self.play_music('shop_music.wav')

        time_offset = pygame.time.get_ticks() / 1000

        # Красивый градиентный фон (золотисто-коричневый)
        for y in range(0, SCREEN_HEIGHT, 2):
            ratio = y / SCREEN_HEIGHT
            r = int(40 + ratio * 60)
            g = int(30 + ratio * 40)
            b = int(10 + ratio * 30)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y), 2)

        # Декоративные монеты летают
        for i in range(10):
            coin_x = 50 + i * 120 + int(math.sin(time_offset + i) * 30)
            coin_y = 100 + int(math.cos(time_offset * 0.5 + i) * 50)
            pygame.draw.circle(self.screen, (255, 215, 0, 150), (coin_x, coin_y), 12)
            pygame.draw.circle(self.screen, (255, 180, 0), (coin_x, coin_y), 12, 2)

        # Заголовок с эффектом
        title_y = 50
        for offset in [(4, 4), (2, 2)]:
            shadow = self.font_large.render("ЖАҚСАРТУ ДҮКЕНІ", True, (100, 70, 20))
            shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], title_y + offset[1]))
            self.screen.blit(shadow, shadow_rect)

        title = self.font_large.render("ЖАҚСАРТУ ДҮКЕНІ", True, (255, 215, 0))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        self.screen.blit(title, title_rect)

        # Баланс монет (большая красивая панель)
        balance_y = 120
        balance_width = 350
        balance_height = 70
        balance_x = SCREEN_WIDTH // 2 - balance_width // 2

        # Тень
        shadow_surf = pygame.Surface((balance_width + 6, balance_height + 6), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        self.screen.blit(shadow_surf, (balance_x + 3, balance_y + 3))

        # Панель баланса
        balance_surf = pygame.Surface((balance_width, balance_height), pygame.SRCALPHA)
        for i in range(balance_height):
            ratio = i / balance_height
            color = (int(255 * (1 - ratio * 0.2)), int(200 * (1 - ratio * 0.2)), 0, 230)
            pygame.draw.line(balance_surf, color, (0, i), (balance_width, i))

        pygame.draw.rect(balance_surf, (255, 215, 0), (0, 0, balance_width, balance_height), 4, 15)
        self.screen.blit(balance_surf, (balance_x, balance_y))

        # Иконка монеты
        coin_icon_x = balance_x + 35
        coin_icon_y = balance_y + balance_height // 2
        pygame.draw.circle(self.screen, (255, 230, 0), (coin_icon_x, coin_icon_y), 25)
        pygame.draw.circle(self.screen, (255, 180, 0), (coin_icon_x, coin_icon_y), 25, 3)
        pygame.draw.circle(self.screen, (255, 180, 0), (coin_icon_x, coin_icon_y), 18, 2)

        # Текст баланса
        balance_label = self.font_small.render("Сіздің балансыңыз:", True, WHITE)
        self.screen.blit(balance_label, (coin_icon_x + 40, balance_y + 12))

        balance_amount = self.font_large.render(f"{self.total_coins}", True, WHITE)
        self.screen.blit(balance_amount, (coin_icon_x + 40, balance_y + 28))

        # Товары (карточки улучшений)
        items = [
            {
                "id": "bag",
                "title": "Үлкен сөмке",
                "price": self.upgrade_prices['bag'],
                "description": "Сыйымдылықты арттырады",
                "stats": "10 қоқыс бірлігі",
                "icon_color": (100, 150, 100),
                "key": "1"
            },
            {
                "id": "tractor",
                "title": "Трактор",
                "price": self.upgrade_prices['tractor'],
                "description": "Қоқысты тезірек жинайды",
                "stats": "Жылдамдық x2, 15 бірлік",
                "icon_color": (200, 50, 50),
                "key": "2"
            },
            {
                "id": "advanced_drone",
                "title": "Ақылды дрон",
                "price": self.upgrade_prices['advanced_drone'],
                "description": "Автоматты жинау",
                "stats": "Тышқанды басу арқылы жинау",
                "icon_color": (50, 150, 255),
                "key": "3"
            }
        ]

        card_start_y = 220
        card_width = 340
        card_height = 140
        card_spacing = 20
        cards_per_row = 3

        for idx, item in enumerate(items):
            col = idx % cards_per_row
            card_x = 50 + col * (card_width + card_spacing)
            card_y = card_start_y

            owned = self.upgrades[item["id"]]
            can_afford = self.total_coins >= item["price"]

            # Тень карточки
            shadow = pygame.Surface((card_width + 6, card_height + 6), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 120))
            self.screen.blit(shadow, (card_x + 4, card_y + 4))

            # Карточка
            card = pygame.Surface((card_width, card_height), pygame.SRCALPHA)

            if owned:
                # Зеленая - куплено
                base_color = (50, 150, 50)
            elif can_afford:
                # Синяя - можно купить
                base_color = (50, 100, 200)
            else:
                # Серая - не хватает денег
                base_color = (80, 80, 80)

            # Градиент на карточке
            for i in range(card_height):
                ratio = i / card_height
                r = int(base_color[0] * (1 - ratio * 0.3))
                g = int(base_color[1] * (1 - ratio * 0.3))
                b = int(base_color[2] * (1 - ratio * 0.3))
                pygame.draw.line(card, (r, g, b, 240), (5, i), (card_width - 5, i))

            pygame.draw.rect(card, WHITE, (0, 0, card_width, card_height), 3, 12)
            self.screen.blit(card, (card_x, card_y))

            # Иконка товара
            icon_x = card_x + 30
            icon_y = card_y + card_height // 2
            pygame.draw.circle(self.screen, item["icon_color"], (icon_x, icon_y), 35)
            pygame.draw.circle(self.screen, WHITE, (icon_x, icon_y), 35, 3)

            # Название
            title_surf = self.font_medium.render(item["title"], True, WHITE)
            self.screen.blit(title_surf, (icon_x + 50, card_y + 15))

            # Описание
            desc_surf = self.font_tiny.render(item["description"], True, (220, 220, 220))
            self.screen.blit(desc_surf, (icon_x + 50, card_y + 45))

            # Статистика
            stats_surf = self.font_tiny.render(item["stats"], True, (180, 180, 180))
            self.screen.blit(stats_surf, (icon_x + 50, card_y + 65))

            # Цена и статус
            if owned:
                status_surf = self.font_small.render("✓ САТЫП АЛЫНДЫ", True, (100, 255, 100))
                self.screen.blit(status_surf, (icon_x + 50, card_y + 95))
            else:
                price_surf = self.font_small.render(f"{item['price']} монета", True, YELLOW)
                self.screen.blit(price_surf, (icon_x + 50, card_y + 95))

                # Кнопка покупки
                key_label = self.font_tiny.render(f"[{item['key']}]", True, WHITE)
                key_rect = key_label.get_rect(right=card_x + card_width - 15, centery=card_y + card_height - 20)

                key_bg = pygame.Surface((40, 25), pygame.SRCALPHA)
                if can_afford:
                    key_bg.fill((255, 215, 0, 200))
                else:
                    key_bg.fill((100, 100, 100, 200))
                pygame.draw.rect(key_bg, WHITE, (0, 0, 40, 25), 2, 5)
                self.screen.blit(key_bg, (key_rect.x - 10, key_rect.y - 5))
                self.screen.blit(key_label, key_rect)

        # Инструкции внизу
        inst_bg = pygame.Surface((SCREEN_WIDTH - 100, 50), pygame.SRCALPHA)
        inst_bg.fill((50, 50, 50, 200))
        pygame.draw.rect(inst_bg, WHITE, (0, 0, SCREEN_WIDTH - 100, 50), 2, 10)
        self.screen.blit(inst_bg, (50, SCREEN_HEIGHT - 80))

        inst_text = self.font_small.render("Сатып алу үшін 1, 2 немесе 3-ті басыңыз  |  ESC - мәзірге оралу", True, WHITE)
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 55))
        self.screen.blit(inst_text, inst_rect)

    def draw_shop_item(self, x, y, title, price, description, owned):
        """Отрисовка товара в магазине"""
        # Панель товара
        panel_width = 800
        panel_height = 100
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)

        if owned:
            # Зеленая панель для купленных товаров
            panel.fill((0, 100, 0, 150))
            status_color = GREEN
            status_text = "✓ САТЫП АЛЫНДЫ"
        else:
            # Синяя панель для доступных товаров
            panel.fill((0, 50, 150, 150))
            status_color = YELLOW
            status_text = "Қол жетімді"

        pygame.draw.rect(panel, WHITE, (0, 0, panel_width, panel_height), 3, 10)
        self.screen.blit(panel, (x, y))

        # Название
        title_surf = self.font_medium.render(title, True, WHITE)
        self.screen.blit(title_surf, (x + 20, y + 15))

        # Цена
        price_surf = self.font_small.render(price, True, YELLOW)
        self.screen.blit(price_surf, (x + 20, y + 50))

        # Описание
        desc_surf = self.font_small.render(description, True, WHITE)
        self.screen.blit(desc_surf, (x + 300, y + 50))

        # Статус
        status_surf = self.font_medium.render(status_text, True, status_color)
        status_rect = status_surf.get_rect(right=x + panel_width - 20, centery=y + panel_height // 2)
        self.screen.blit(status_surf, status_rect)

    def start_river_restoration_cutscene(self):
        """Запустить катсцену восстановления реки"""
        self.cutscene_active = True
        self.cutscene_timer = 0
        self.cutscene_type = "river_restoration"
        self.state = GameState.CUTSCENE

        # Создать празднующих жителей около реки
        blockage_segment = None
        for segment in self.river_segments:
            if segment.is_blockage_point:
                blockage_segment = segment
                break

        if blockage_segment:
            for i in range(6):
                offset_x = random.randint(-80, 80)
                offset_y = random.randint(-100, 100)
                villager = CelebratingVillager(
                    blockage_segment.rect.centerx + offset_x,
                    blockage_segment.rect.centery + offset_y
                )
                self.celebrating_villagers.add(villager)
                self.all_sprites.add(villager)

    def draw_cutscene(self):
        """Рисовать катсцену"""
        self.draw_game()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(100):
            alpha = int((i / 100) * 150)
            pygame.draw.rect(overlay, (0, 0, 0, alpha),
                           (i, i, SCREEN_WIDTH - i * 2, SCREEN_HEIGHT - i * 2), 1)
        self.screen.blit(overlay, (0, 0))

        if self.cutscene_type == "river_restoration":
            fade = min(1.0, self.cutscene_timer / 60)
            title_alpha = int(255 * fade)

            title_text = "ӨЗЕН ҚАЛПЫНА КЕЛТІРІЛДІ!"
            title = self.font_large.render(title_text, True, (100, 200, 255))
            title.set_alpha(title_alpha)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))

            shadow = self.font_large.render(title_text, True, (0, 50, 100))
            shadow.set_alpha(title_alpha // 2)
            shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, 103))

            self.screen.blit(shadow, shadow_rect)
            self.screen.blit(title, title_rect)

            if self.cutscene_timer > 30:
                subtitle_alpha = int(255 * min(1.0, (self.cutscene_timer - 30) / 40))
                subtitle = self.font_medium.render("Ауыл тұрғындары қуанышты!", True, YELLOW)
                subtitle.set_alpha(subtitle_alpha)
                subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 160))
                self.screen.blit(subtitle, subtitle_rect)

    def run(self):
        """Главный игровой цикл"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


class GroundTile(pygame.sprite.Sprite):
    """Тайл земли с улучшенной графикой"""
    def __init__(self, x, y, level):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        if level == 1:  # Лес - детализированная трава
            base = (40, 100, 40)
            var = random.randint(-15, 15)
            self.image.fill((base[0] + var, base[1] + var, base[2] + var))

            # Травинки
            for _ in range(8):
                gx = random.randint(0, TILE_SIZE)
                gy = random.randint(0, TILE_SIZE)
                grass_color = (30 + var, 90 + var, 30 + var)
                pygame.draw.line(self.image, grass_color, (gx, gy), (gx + 1, gy - 2))

            # Темные пятна
            if random.random() < 0.1:
                for _ in range(3):
                    dx = random.randint(0, TILE_SIZE - 4)
                    dy = random.randint(0, TILE_SIZE - 4)
                    pygame.draw.circle(self.image, (30, 80, 30), (dx, dy), 2)

        elif level == 2:  # Город - асфальт
            base = (60, 60, 60)
            var = random.randint(-10, 10)
            self.image.fill((base[0] + var, base[1] + var, base[2] + var))

            # Трещины
            if random.random() < 0.15:
                start = (random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE))
                end = (random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE))
                pygame.draw.line(self.image, (40, 40, 40), start, end, 1)

            # Пятна
            if random.random() < 0.2:
                for _ in range(2):
                    px = random.randint(0, TILE_SIZE)
                    py = random.randint(0, TILE_SIZE)
                    self.image.set_at((px, py), (50, 50, 50))

        else:  # Пустыня - песок
            base = (200, 170, 120)
            var = random.randint(-20, 20)
            self.image.fill((base[0] + var, base[1] + var, base[2] + var))

            # Песчинки
            for _ in range(15):
                sx = random.randint(0, TILE_SIZE - 1)
                sy = random.randint(0, TILE_SIZE - 1)
                sand_color = (base[0] + var + random.randint(-10, 10),
                            base[1] + var + random.randint(-10, 10),
                            base[2] + var + random.randint(-10, 10))
                self.image.set_at((sx, sy), sand_color)


class Player(pygame.sprite.Sprite):
    """Игрок с улучшенной графикой"""
    def __init__(self, x, y, game=None):
        super().__init__()
        self.game = game
        self.width = 40
        self.height = 40
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

        self.vel_x = 0
        self.vel_y = 0
        self.carrying_trash = 0
        self.max_trash = 5
        self.direction = 2
        self.animation_frame = 0
        self.has_tractor = False  # Флаг для трактора

        # Dash система
        self.dash_speed = 15  # Скорость рывка
        self.dash_duration = 10  # Длительность рывка (кадров)
        self.dash_cooldown_max = 60  # Перезарядка 1 секунда (60 кадров)
        self.dash_cooldown = 0  # Текущая перезарядка
        self.dash_active = False  # Активен ли рывок
        self.dash_timer = 0  # Таймер активного рывка
        self.dash_direction = (0, 0)  # Направление рывка

        self.draw_character()

    def draw_character(self):
        """Рисовать персонажа"""
        self.image.fill((0, 0, 0, 0))

        # Если есть трактор - рисуем трактор
        if self.has_tractor:
            self.draw_tractor()
            return

        suit_color = (40, 130, 220)
        skin_color = (255, 220, 177)
        helmet_color = (0, 180, 80)

        walk_offset = int(3 * math.sin(self.animation_frame))

        if self.direction == 0:  # Вверх
            # Тень
            pygame.draw.ellipse(self.image, (0, 0, 0, 100), (5, 35, 30, 8))

            pygame.draw.ellipse(self.image, skin_color, (12, 8, 16, 16))
            pygame.draw.arc(self.image, helmet_color, (10, 4, 20, 12), 0, math.pi, 4)
            pygame.draw.ellipse(self.image, suit_color, (10, 22, 20, 14))

            # Ноги
            pygame.draw.rect(self.image, suit_color, (12, 32 + walk_offset, 6, 6), 0, 2)
            pygame.draw.rect(self.image, suit_color, (22, 32 - walk_offset, 6, 6), 0, 2)

        elif self.direction == 1:  # Вправо
            pygame.draw.ellipse(self.image, (0, 0, 0, 100), (5, 35, 30, 8))

            pygame.draw.ellipse(self.image, skin_color, (16, 8, 16, 16))
            pygame.draw.circle(self.image, BLACK, (26, 14), 2)
            pygame.draw.arc(self.image, helmet_color, (14, 4, 20, 12), 0, math.pi, 4)
            pygame.draw.ellipse(self.image, suit_color, (12, 22, 22, 14))

            # Ноги
            pygame.draw.rect(self.image, suit_color, (14, 32 + walk_offset, 6, 6), 0, 2)
            pygame.draw.rect(self.image, suit_color, (24, 32 - walk_offset, 6, 6), 0, 2)

        elif self.direction == 2:  # Вниз
            pygame.draw.ellipse(self.image, (0, 0, 0, 100), (5, 35, 30, 8))

            pygame.draw.ellipse(self.image, skin_color, (12, 8, 16, 16))
            pygame.draw.circle(self.image, BLACK, (16, 14), 2)
            pygame.draw.circle(self.image, BLACK, (24, 14), 2)
            pygame.draw.arc(self.image, BLACK, (16, 18, 8, 4), 0, math.pi, 2)
            pygame.draw.arc(self.image, helmet_color, (10, 4, 20, 12), 0, math.pi, 4)
            pygame.draw.ellipse(self.image, suit_color, (10, 22, 20, 14))

            # Ноги
            pygame.draw.rect(self.image, suit_color, (12, 32 + walk_offset, 6, 6), 0, 2)
            pygame.draw.rect(self.image, suit_color, (22, 32 - walk_offset, 6, 6), 0, 2)

        else:  # Влево
            pygame.draw.ellipse(self.image, (0, 0, 0, 100), (5, 35, 30, 8))

            pygame.draw.ellipse(self.image, skin_color, (8, 8, 16, 16))
            pygame.draw.circle(self.image, BLACK, (14, 14), 2)
            pygame.draw.arc(self.image, helmet_color, (6, 4, 20, 12), 0, math.pi, 4)
            pygame.draw.ellipse(self.image, suit_color, (6, 22, 22, 14))

            # Ноги
            pygame.draw.rect(self.image, suit_color, (10, 32 + walk_offset, 6, 6), 0, 2)
            pygame.draw.rect(self.image, suit_color, (20, 32 - walk_offset, 6, 6), 0, 2)

        # Мешок
        if self.carrying_trash > 0:
            bag_x = 28 if self.direction == 1 else 4
            pygame.draw.circle(self.image, (80, 80, 80), (bag_x, 24), 8)
            pygame.draw.circle(self.image, (60, 60, 60), (bag_x, 24), 8, 2)

            font = pygame.font.Font(None, 16)
            num = font.render(str(self.carrying_trash), True, WHITE)
            num_rect = num.get_rect(center=(bag_x, 24))
            self.image.blit(num, num_rect)

    def draw_tractor(self):
        """Рисовать трактор"""
        tractor_color = (200, 50, 50)  # Красный трактор
        wheel_color = (40, 40, 40)
        window_color = (100, 150, 200)

        # Тень
        pygame.draw.ellipse(self.image, (0, 0, 0, 100), (2, 35, 36, 10))

        # Корпус трактора
        pygame.draw.rect(self.image, tractor_color, (8, 15, 24, 18), 0, 3)

        # Кабина
        pygame.draw.rect(self.image, tractor_color, (12, 8, 16, 12), 0, 2)

        # Окно
        if self.direction == 0:  # Вверх
            pygame.draw.rect(self.image, window_color, (14, 10, 12, 6), 0, 1)
        elif self.direction == 1:  # Вправо
            pygame.draw.rect(self.image, window_color, (18, 10, 8, 6), 0, 1)
        elif self.direction == 2:  # Вниз
            pygame.draw.rect(self.image, window_color, (14, 12, 12, 6), 0, 1)
        else:  # Влево
            pygame.draw.rect(self.image, window_color, (14, 10, 8, 6), 0, 1)

        # Колеса
        wheel_offset = int(2 * math.sin(self.animation_frame))
        pygame.draw.circle(self.image, wheel_color, (12, 32 + wheel_offset), 4)
        pygame.draw.circle(self.image, wheel_color, (28, 32 + wheel_offset), 4)
        pygame.draw.circle(self.image, GRAY, (12, 32 + wheel_offset), 2)
        pygame.draw.circle(self.image, GRAY, (28, 32 + wheel_offset), 2)

        # Труба
        pygame.draw.rect(self.image, DARK_GRAY, (18, 4, 4, 6))

        # Контейнер для мусора (сзади)
        if self.carrying_trash > 0:
            container_x = 2 if self.direction == 3 else 30
            pygame.draw.rect(self.image, (100, 100, 100), (container_x, 18, 8, 12), 0, 2)
            pygame.draw.rect(self.image, (80, 80, 80), (container_x, 18, 8, 12), 2, 2)

            # Количество мусора
            font = pygame.font.Font(None, 14)
            num = font.render(str(self.carrying_trash), True, WHITE)
            num_rect = num.get_rect(center=(container_x + 4, 24))
            self.image.blit(num, num_rect)

    def perform_dash(self):
        """Выполнить рывок"""
        if self.dash_cooldown > 0 or self.dash_active:
            return False

        # Определяем направление dash на основе текущего направления
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1

        # Если нет направления, используем текущее направление взгляда
        if dx == 0 and dy == 0:
            if self.direction == 0:  # Вверх
                dy = -1
            elif self.direction == 1:  # Вправо
                dx = 1
            elif self.direction == 2:  # Вниз
                dy = 1
            else:  # Влево
                dx = -1

        # Нормализуем диагональное направление
        length = math.sqrt(dx**2 + dy**2)
        if length > 0:
            dx /= length
            dy /= length

        self.dash_direction = (dx, dy)
        self.dash_active = True
        self.dash_timer = self.dash_duration
        self.dash_cooldown = self.dash_cooldown_max

        # Звук рывка
        if SOUNDS_ENABLED:
            sound_dash.play()

        return True

    def update(self):
        """Обновление"""
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        self.vel_y = 0
        moving = False

        # Обновление cooldown dash
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Если активен dash
        if self.dash_active:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dash_active = False
            else:
                # Движение с dash скоростью
                self.vel_x = self.dash_direction[0] * self.dash_speed
                self.vel_y = self.dash_direction[1] * self.dash_speed
                moving = True
        else:
            # Обычное движение
            # Скорость зависит от наличия трактора и отравления
            speed = PLAYER_SPEED * 2 if self.has_tractor else PLAYER_SPEED

            # Замедление при отравлении
            if self.game and self.game.player_poisoned:
                speed *= 0.5  # Замедление на 50%

            # Замедление в заблокированной воде
            if self.game and self.game.player_in_blocked_water:
                speed *= 0.6  # Замедление на 40%

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = -speed
                self.direction = 3
                moving = True
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = speed
                self.direction = 1
                moving = True
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.vel_y = -speed
                self.direction = 0
                moving = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.vel_y = speed
                self.direction = 2
                moving = True

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Границы мира
        self.rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))

        if moving:
            self.animation_frame += 0.3
        else:
            self.animation_frame = 0

        self.draw_character()

    def collect_trash(self, trash_group):
        """Собрать мусор"""
        if self.carrying_trash >= self.max_trash:
            return {"count": 0, "damage": 0, "bonus_points": 0}  # Возвращаем пустой результат

        # Радиус сбора зависит от наличия трактора
        radius = 50 if self.has_tractor else 25
        collect_rect = self.rect.inflate(radius, radius)
        hits = [trash for trash in trash_group if collect_rect.colliderect(trash.rect)]

        # Количество собираемого мусора за раз (трактор собирает больше)
        collect_count = 3 if self.has_tractor else 1

        collected = 0
        total_damage = 0
        total_bonus_points = 0

        for trash in hits:
            if not trash.needs_drone and collected < collect_count:
                # Проверяем редкость мусора
                if hasattr(trash, 'damage'):
                    total_damage += trash.damage
                if hasattr(trash, 'points'):
                    total_bonus_points += trash.points

                trash.kill()
                self.carrying_trash = min(self.carrying_trash + 1, self.max_trash)
                collected += 1

                # Звук сбора мусора
                if SOUNDS_ENABLED:
                    sound_pickup.play()

        return {"count": collected, "damage": total_damage, "bonus_points": total_bonus_points}


class Trash(pygame.sprite.Sprite):
    """Мусор с улучшенной графикой"""
    def __init__(self, x, y, trash_type, level, needs_drone=False, river_trash=False, rarity="normal"):
        super().__init__()
        self.trash_type = trash_type
        self.level = level
        self.needs_drone = needs_drone
        self.river_trash = river_trash  # Мусор блокирует ручей
        self.rarity = rarity  # "normal", "golden", "dangerous"
        self.size = 28

        # Бонусы и характеристики в зависимости от редкости
        if self.rarity == "golden":
            self.points = 30  # Золотой дает больше очков
            self.glow_color = (255, 215, 0)  # Золотое свечение
        elif self.rarity == "dangerous":
            self.points = 20  # Опасный дает средне очков
            self.damage = 5  # Отнимает 5 HP при сборе
            self.glow_color = (255, 0, 0)  # Красное свечение
        else:  # normal
            self.points = 10  # Обычный мусор
            self.glow_color = None

        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.pulse = 0
        self.draw_trash()

    def draw_trash(self):
        """Рисовать мусор с улучшенной графикой"""
        self.image.fill((0, 0, 0, 0))

        # Тень
        pygame.draw.ellipse(self.image, (0, 0, 0, 80), (4, 22, 20, 6))

        if self.trash_type == "plastic":
            # Пластиковая бутылка (детальная)
            bottle_color = (255, 200, 50)
            cap_color = (200, 50, 50)

            # Корпус бутылки
            pygame.draw.rect(self.image, bottle_color, (10, 8, 10, 14), 0, 3)
            pygame.draw.rect(self.image, (230, 180, 40), (10, 8, 10, 14), 2, 3)

            # Горлышко
            pygame.draw.rect(self.image, bottle_color, (12, 4, 6, 4), 0, 1)

            # Крышка
            pygame.draw.rect(self.image, cap_color, (11, 2, 8, 3), 0, 1)
            pygame.draw.circle(self.image, (180, 40, 40), (15, 3), 2)

            # Блики и детали
            pygame.draw.circle(self.image, (255, 255, 200), (12, 10), 2)
            pygame.draw.line(self.image, (200, 150, 30), (13, 12), (13, 18), 2)

            # Этикетка
            pygame.draw.rect(self.image, (255, 255, 255), (11, 14, 8, 4))

        elif self.trash_type == "bottle":
            # Стеклянная бутылка
            glass_color = (100, 180, 120)

            # Корпус
            pygame.draw.rect(self.image, glass_color, (9, 10, 12, 13), 0, 2)

            # Горлышко
            pygame.draw.rect(self.image, glass_color, (11, 5, 8, 6), 0, 1)

            # Блики стекла
            pygame.draw.circle(self.image, (200, 255, 220), (12, 12), 3)
            pygame.draw.line(self.image, (150, 220, 180), (10, 14), (10, 20), 2)

            # Обводка
            pygame.draw.rect(self.image, (70, 130, 90), (9, 10, 12, 13), 2, 2)

        elif self.trash_type == "can":
            # Алюминиевая банка
            can_color = (180, 180, 200)

            # Корпус банки
            pygame.draw.ellipse(self.image, can_color, (8, 8, 14, 16), 0)

            # Металлические полосы
            for y in range(10, 22, 3):
                pygame.draw.line(self.image, (150, 150, 170), (8, y), (22, y), 1)

            # Язычок открывания
            pygame.draw.rect(self.image, (140, 140, 160), (13, 6, 4, 3), 0, 1)
            pygame.draw.circle(self.image, (120, 120, 140), (15, 7), 2)

            # Блики металла
            pygame.draw.line(self.image, (220, 220, 240), (10, 10), (10, 20), 2)
            pygame.draw.circle(self.image, WHITE, (18, 12), 2)

        elif self.trash_type == "paper":
            # Мятая бумага
            paper_color = (245, 245, 230)

            # Основа мятой бумаги (неровная)
            points = [(6, 8), (10, 6), (16, 7), (22, 9), (21, 15), (18, 22), (12, 23), (7, 20), (5, 14)]
            pygame.draw.polygon(self.image, paper_color, points, 0)
            pygame.draw.polygon(self.image, (200, 200, 180), points, 2)

            # Складки
            pygame.draw.line(self.image, (220, 220, 200), (8, 10), (15, 18), 1)
            pygame.draw.line(self.image, (220, 220, 200), (12, 8), (18, 20), 1)
            pygame.draw.line(self.image, (220, 220, 200), (16, 9), (10, 20), 1)

            # Текст на бумаге
            for i in range(3):
                y = 12 + i * 4
                pygame.draw.line(self.image, (100, 100, 100), (9, y), (18, y), 1)

        elif self.trash_type == "glass":
            # Разбитое стекло
            glass_color = (150, 200, 255)

            # Осколки
            pygame.draw.polygon(self.image, glass_color, [(8, 12), (14, 8), (18, 14), (12, 20)], 0)
            pygame.draw.polygon(self.image, BLUE, [(8, 12), (14, 8), (18, 14), (12, 20)], 2)

            # Блики
            pygame.draw.circle(self.image, WHITE, (13, 11), 3)
            pygame.draw.circle(self.image, (200, 230, 255), (15, 15), 2)

            # Острые края
            pygame.draw.line(self.image, (100, 150, 200), (14, 8), (18, 14), 2)

        elif self.trash_type == "metal":
            # Металлолом
            metal_color = (140, 140, 140)

            # Ржавый металл
            pygame.draw.rect(self.image, metal_color, (7, 7, 16, 16), 0, 2)

            # Ржавчина
            rust_color = (180, 100, 60)
            pygame.draw.circle(self.image, rust_color, (10, 10), 3)
            pygame.draw.circle(self.image, rust_color, (18, 18), 4)
            pygame.draw.circle(self.image, (160, 80, 40), (14, 14), 2)

            # Металлические линии
            for i in range(4):
                c = (100 + i * 15, 100 + i * 15, 100 + i * 15)
                pygame.draw.line(self.image, c, (9, 10 + i * 3), (21, 10 + i * 3))

        # Свечение для редкого мусора
        if self.glow_color:
            pulse_size = int(abs(math.sin(self.pulse)) * 4)
            for i in range(3):
                alpha = 60 - i * 15
                radius = self.size // 2 + pulse_size + i * 2
                glow_surf = pygame.Surface((self.size + i * 6, self.size + i * 6), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.glow_color, alpha),
                                 (self.size // 2 + i * 3, self.size // 2 + i * 3), radius)
                self.image.blit(glow_surf, (-i * 3, -i * 3))

        # Индикатор для мусора требующего дрон
        if self.needs_drone:
            pygame.draw.rect(self.image, RED, (0, 0, self.size, self.size), 3, 3)
            font = pygame.font.Font(None, 14)
            d_text = font.render("D", True, RED)
            self.image.blit(d_text, (2, 2))

        # Индикатор мусора блокирующего ручей
        if self.river_trash:
            pygame.draw.circle(self.image, (0, 150, 255), (self.size - 5, 5), 4)
            pygame.draw.circle(self.image, WHITE, (self.size - 5, 5), 4, 1)

    def update(self):
        self.pulse += 0.1
        # Перерисовываем если есть свечение (для анимации)
        if self.glow_color:
            self.draw_trash()


class Obstacle(pygame.sprite.Sprite):
    """Препятствия с красивой графикой"""
    def __init__(self, x, y, obs_type):
        super().__init__()
        self.obs_type = obs_type
        self.toxic = (obs_type == "toxic")

        # Размеры в зависимости от типа
        sizes = {
            "tree": (56, 72),
            "tree_big": (72, 96),
            "tree_small": (40, 56),
            "building": (80, 100),
            "toxic": (48, 48),
            "cactus": (40, 64)
        }

        self.width, self.height = sizes.get(obs_type, (64, 80))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.glow = 0
        self.draw_obstacle()

    def draw_obstacle(self):
        """Рисовать препятствие"""
        self.image.fill((0, 0, 0, 0))

        if "tree" in self.obs_type:
            # Тень
            shadow_y = self.height - 12
            pygame.draw.ellipse(self.image, (0, 0, 0, 100),
                              (self.width // 4, shadow_y, self.width // 2, 12))

            # Размер дерева зависит от типа
            if self.obs_type == "tree_small":
                trunk_w = 10
                crown_base_size = self.width // 3
            elif self.obs_type == "tree_big":
                trunk_w = 20
                crown_base_size = self.width // 2 + 4
            else:  # tree
                trunk_w = 14
                crown_base_size = self.width // 2

            # Ствол с реалистичной текстурой коры
            trunk_x = self.width // 2 - trunk_w // 2
            trunk_h = self.height // 2

            # Базовый цвет ствола
            for y in range(trunk_h):
                # Вариация цвета для эффекта коры
                color_var = random.randint(-15, 15)
                bark_color = (
                    min(255, max(0, 101 + color_var)),
                    min(255, max(0, 67 + color_var)),
                    min(255, max(0, 33 + color_var))
                )
                pygame.draw.line(self.image, bark_color,
                               (trunk_x, self.height // 2 + y),
                               (trunk_x + trunk_w, self.height // 2 + y), 1)

            # Текстура коры (горизонтальные линии)
            for i in range(5):
                bark_y = self.height // 2 + random.randint(5, trunk_h - 5)
                pygame.draw.line(self.image, DARK_BROWN,
                               (trunk_x, bark_y),
                               (trunk_x + trunk_w, bark_y), 2)

            # Обводка ствола
            pygame.draw.rect(self.image, DARK_BROWN,
                           (trunk_x, self.height // 2, trunk_w, trunk_h), 2, 3)

            # Многослойная крона с естественной формой
            crown_y = self.height // 4
            crown_center_x = self.width // 2

            # Слои кроны (темнее к светлее)
            crown_layers = [
                (DARK_GREEN, crown_base_size, 0),
                ((44, 130, 44), crown_base_size - 4, -3),
                (FOREST_GREEN, crown_base_size - 8, -6),
                ((54, 149, 54), crown_base_size - 12, -10),
                (GREEN, crown_base_size - 16, -14),
                (LIGHT_GREEN, crown_base_size - 20, -18)
            ]

            for color, size, y_offset in crown_layers:
                if size > 0:
                    # Несколько кругов для более естественной формы
                    pygame.draw.circle(self.image, color,
                                     (crown_center_x, crown_y + y_offset), size)

            # Добавляем "листья" на краях кроны
            for _ in range(8):
                leaf_angle = random.random() * math.pi * 2
                leaf_dist = crown_base_size - 10
                leaf_x = int(crown_center_x + math.cos(leaf_angle) * leaf_dist)
                leaf_y = int(crown_y + math.sin(leaf_angle) * leaf_dist - 10)
                leaf_color = random.choice([DARK_GREEN, FOREST_GREEN, GREEN])
                pygame.draw.circle(self.image, leaf_color, (leaf_x, leaf_y), 6)

        elif self.obs_type == "building":
            # Тень
            pygame.draw.rect(self.image, (0, 0, 0, 100),
                           (4, self.height - 8, self.width - 4, 8))

            # Здание
            pygame.draw.rect(self.image, (70, 70, 80), (8, 12, self.width - 16, self.height - 20), 0, 4)
            pygame.draw.rect(self.image, (50, 50, 60), (8, 12, self.width - 16, self.height - 20), 3, 4)

            # Окна в сетке
            for row in range(6):
                for col in range(3):
                    wx = 14 + col * 18
                    wy = 20 + row * 12
                    if random.random() > 0.3:
                        window_color = YELLOW if random.random() > 0.6 else (40, 40, 50)
                    else:
                        window_color = (30, 30, 40)
                    pygame.draw.rect(self.image, window_color, (wx, wy, 12, 8), 0, 2)

        elif self.obs_type == "toxic":
            # Анимированное свечение
            glow_val = int(60 + 40 * math.sin(self.glow))
            toxic_color = (140 + glow_val, 0, 240 - glow_val)

            # Бочка
            pygame.draw.ellipse(self.image, toxic_color, (8, 8, 32, 32))
            pygame.draw.ellipse(self.image, (255, 0, 255), (8, 8, 32, 32), 3)

            # Полосы опасности
            for i in range(3):
                y = 14 + i * 8
                pygame.draw.rect(self.image, YELLOW, (10, y, 28, 3))
                pygame.draw.rect(self.image, BLACK, (10, y + 3, 28, 2))

            # Знак
            font = pygame.font.Font(None, 32)
            warning = font.render("!", True, YELLOW)
            self.image.blit(warning, (18, 12))

        elif self.obs_type == "cactus":
            # Тень
            pygame.draw.ellipse(self.image, (0, 0, 0, 100), (8, self.height - 10, 24, 10))

            cactus_green = (50, 140, 50)
            # Ствол
            pygame.draw.rect(self.image, cactus_green, (14, 16, 12, self.height - 20), 0, 3)
            # Руки
            pygame.draw.rect(self.image, cactus_green, (4, 28, 12, 20), 0, 3)
            pygame.draw.rect(self.image, cactus_green, (24, 32, 12, 16), 0, 3)

            # Иголки
            for _ in range(15):
                nx = random.randint(14, 25)
                ny = random.randint(16, self.height - 10)
                pygame.draw.circle(self.image, (40, 100, 40), (nx, ny), 1)

    def update(self):
        if self.toxic:
            self.glow += 0.1
            if self.glow >= math.pi * 2:
                self.glow = 0
            self.draw_obstacle()


class Decoration(pygame.sprite.Sprite):
    """Декорации"""
    def __init__(self, x, y, deco_type, level):
        super().__init__()
        self.deco_type = deco_type
        self.level = level

        # Размеры
        sizes = {
            "bush": (32, 24), "rock": (24, 20), "flower": (16, 16),
            "mushroom": (20, 20), "streetlight": (24, 64), "bench": (48, 32),
            "sign": (32, 48), "hydrant": (24, 32), "small_rock": (20, 16),
            "skull": (24, 20), "dead_tree": (32, 48), "tumbleweed": (28, 28)
        }

        self.width, self.height = sizes.get(deco_type, (32, 32))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.draw_decoration()

    def draw_decoration(self):
        """Рисовать декорацию"""
        self.image.fill((0, 0, 0, 0))

        if self.deco_type == "bush":
            # Куст
            pygame.draw.circle(self.image, DARK_GREEN, (10, 14), 8)
            pygame.draw.circle(self.image, DARK_GREEN, (22, 14), 8)
            pygame.draw.circle(self.image, GREEN, (16, 10), 9)

        elif self.deco_type == "rock":
            # Камень
            pygame.draw.ellipse(self.image, (100, 100, 100), (4, 8, 16, 12))
            pygame.draw.ellipse(self.image, (80, 80, 80), (4, 8, 16, 12), 2)

        elif self.deco_type == "flower":
            # Цветок
            stem_color = (50, 150, 50)
            petal_color = random.choice([(255, 100, 100), (255, 200, 50), (200, 100, 255)])
            pygame.draw.line(self.image, stem_color, (8, 16), (8, 8), 2)
            for angle in range(0, 360, 72):
                rad = math.radians(angle)
                px = int(8 + math.cos(rad) * 4)
                py = int(8 + math.sin(rad) * 4)
                pygame.draw.circle(self.image, petal_color, (px, py), 3)
            pygame.draw.circle(self.image, YELLOW, (8, 8), 2)

        elif self.deco_type == "streetlight":
            # Фонарь
            pygame.draw.rect(self.image, (60, 60, 60), (10, 12, 4, 52))
            pygame.draw.rect(self.image, (80, 80, 80), (6, 8, 12, 8), 0, 2)
            pygame.draw.circle(self.image, YELLOW, (12, 12), 4)

        # Добавьте больше типов декораций по аналогии...

class RecyclingStation(pygame.sprite.Sprite):
    """Станция переработки - улучшенная"""
    def __init__(self, x, y):
        super().__init__()
        self.width = 80
        self.height = 80
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.glow = 0
        self.draw_station()

    def draw_station(self):
        """Рисовать станцию"""
        self.image.fill((0, 0, 0, 0))

        # Тень
        pygame.draw.ellipse(self.image, (0, 0, 0, 100), (10, 70, 60, 10))

        # Здание
        building_color = (0, 140, 40)
        pygame.draw.rect(self.image, building_color, (12, 24, 56, 56), 0, 5)
        pygame.draw.rect(self.image, DARK_GREEN, (12, 24, 56, 56), 4, 5)

        # Крыша
        roof_points = [(12, 24), (40, 8), (68, 24)]
        pygame.draw.polygon(self.image, DARK_GREEN, roof_points)
        pygame.draw.polygon(self.image, FOREST_GREEN, roof_points, 2)

        # Дверь
        pygame.draw.rect(self.image, BROWN, (32, 48, 16, 32), 0, 3)
        pygame.draw.circle(self.image, YELLOW, (44, 64), 2)

        # Окна
        pygame.draw.rect(self.image, SKY_BLUE, (20, 32, 12, 12), 0, 2)
        pygame.draw.rect(self.image, SKY_BLUE, (48, 32, 12, 12), 0, 2)

        # Символ переработки с анимацией
        glow_val = int(200 + 55 * math.sin(self.glow))
        symbol_color = (0, glow_val, 0)

        pygame.draw.circle(self.image, symbol_color, (40, 16), 6, 2)
        # Стрелки
        points1 = [(40, 10), (37, 14), (40, 14)]
        points2 = [(43, 18), (40, 20), (43, 22)]
        pygame.draw.polygon(self.image, symbol_color, points1)
        pygame.draw.polygon(self.image, symbol_color, points2)

    def update(self):
        self.glow += 0.1
        if self.glow >= math.pi * 2:
            self.glow = 0
        self.draw_station()


class Drone(pygame.sprite.Sprite):
    """Дрон - улучшенный"""
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.active = False
        self.width = 40
        self.height = 28
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.hover_offset = 0
        self.propeller_frame = 0
        self.update_position()
        self.draw_drone()

    def draw_drone(self):
        """Рисовать дрона"""
        self.image.fill((0, 0, 0, 0))

        if self.active:
            body_color = (80, 180, 255)
            prop_color = (180, 255, 180)
            light_color = GREEN
        else:
            body_color = (100, 100, 100)
            prop_color = (80, 80, 80)
            light_color = RED

        # Корпус
        pygame.draw.ellipse(self.image, body_color, (12, 10, 16, 12))
        pygame.draw.ellipse(self.image, (60, 140, 220) if self.active else (80, 80, 80),
                          (12, 10, 16, 12), 2)

        # Пропеллеры
        prop_positions = [(6, 6), (30, 6), (6, 20), (30, 20)]
        for px, py in prop_positions:
            pygame.draw.circle(self.image, BLACK, (px, py), 3)
            pygame.draw.circle(self.image, body_color, (px, py), 2)

            if self.active:
                offset = int(4 * math.sin(self.propeller_frame + px))
                pygame.draw.line(self.image, prop_color,
                               (px - 5, py + offset), (px + 5, py - offset), 2)
            else:
                pygame.draw.line(self.image, prop_color, (px - 4, py), (px + 4, py), 2)

        # Камера/сенсор
        pygame.draw.circle(self.image, BLACK, (20, 16), 4)
        pygame.draw.circle(self.image, light_color, (20, 16), 2)
        pygame.draw.circle(self.image, WHITE, (21, 15), 1)

    def toggle(self):
        self.active = not self.active

    def update(self):
        if self.active:
            self.hover_offset += 0.15
            self.propeller_frame += 0.5
            target_x = self.player.rect.centerx - 20
            target_y = self.player.rect.centery - 50
            self.rect.x += (target_x - self.rect.x) * 0.1
            self.rect.y = int(target_y + math.sin(self.hover_offset) * 6)
        else:
            self.rect.centerx = self.player.rect.centerx
            self.rect.centery = self.player.rect.centery - 40

        self.draw_drone()

    def update_position(self):
        self.rect.centerx = self.player.rect.centerx
        self.rect.centery = self.player.rect.centery - 40

    def collect_trash(self, trash_group):
        if not self.active:
            return False
        collect_rect = self.rect.inflate(70, 70)
        for trash in trash_group:
            if trash.needs_drone and collect_rect.colliderect(trash.rect):
                trash.kill()
                return True
        return False


class Road(pygame.sprite.Sprite):
    """Дорога для города"""
    def __init__(self, x, y, width, height, orientation='horizontal'):
        super().__init__()
        self.width = width
        self.height = height
        self.orientation = orientation
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.draw_road()

    def draw_road(self):
        # Асфальт
        self.image.fill((60, 60, 60))

        # Разметка
        if self.orientation == 'horizontal':
            # Белые полосы по центру
            stripe_y = self.height // 2
            for stripe_x in range(0, self.width, 40):
                pygame.draw.rect(self.image, WHITE, (stripe_x, stripe_y - 2, 20, 4))
        else:  # vertical
            # Белые полосы по центру
            stripe_x = self.width // 2
            for stripe_y in range(0, self.height, 40):
                pygame.draw.rect(self.image, WHITE, (stripe_x - 2, stripe_y, 4, 20))


class NPC(pygame.sprite.Sprite):
    """NPC который хвалит игрока"""
    def __init__(self, x, y, name="Азамат"):
        super().__init__()
        self.width = 35
        self.height = 40
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.name = name
        self.praise_messages = [
            "Таза болғаны үшін рахмет!",
            "Сіз маңызды іс істеп жатырсыз!",
            "Жарайсың, эко-батыр!",
            "Біздің қала таза болды!",
            "Осылай жалғастырыңыз!"
        ]
        self.showing_message = False
        self.message = ""
        self.message_timer = 0

        # Случайный цвет одежды
        self.shirt_color = random.choice([
            (200, 50, 50),   # Красный
            (50, 100, 200),  # Синий
            (50, 200, 50),   # Зеленый
            (200, 150, 50),  # Оранжевый
            (150, 50, 200)   # Фиолетовый
        ])

        self.draw_npc()

    def draw_npc(self):
        """Рисовать NPC"""
        self.image.fill((0, 0, 0, 0))

        skin_color = (255, 220, 177)
        pants_color = (50, 50, 100)

        # Тень
        pygame.draw.ellipse(self.image, (0, 0, 0, 100), (3, 36, 29, 7))

        # Голова
        pygame.draw.ellipse(self.image, skin_color, (10, 5, 15, 15))

        # Глаза
        pygame.draw.circle(self.image, BLACK, (14, 11), 2)
        pygame.draw.circle(self.image, BLACK, (21, 11), 2)

        # Улыбка
        pygame.draw.arc(self.image, BLACK, (12, 12, 11, 8), 0, math.pi, 2)

        # Тело
        pygame.draw.ellipse(self.image, self.shirt_color, (8, 19, 19, 14))

        # Ноги
        pygame.draw.rect(self.image, pants_color, (10, 30, 6, 8), 0, 2)
        pygame.draw.rect(self.image, pants_color, (19, 30, 6, 8), 0, 2)

    def check_player_nearby(self, player, distance=100):
        """Проверить близость игрока"""
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.sqrt(dx*dx + dy*dy)

        if dist < distance:
            if not self.showing_message:
                self.message = random.choice(self.praise_messages)
                self.showing_message = True
                self.message_timer = 120  # 2 секунды
        else:
            self.showing_message = False

    def update(self):
        if self.showing_message:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.showing_message = False


class Litterer(pygame.sprite.Sprite):
    """Враг-мусорщик, который ходит и бросает мусор"""
    def __init__(self, x, y, world_width, world_height, level=1):
        super().__init__()
        self.width = 35
        self.height = 40
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # Границы мира для движения
        self.world_width = world_width
        self.world_height = world_height

        # Уровень определяет параметры
        self.level = level

        # Движение
        self.speed = 1.5
        self.direction = random.choice(['left', 'right', 'up', 'down'])
        self.direction_timer = random.randint(60, 180)  # Меняет направление каждые 1-3 сек

        # Выброс мусора (зависит от уровня)
        # Уровень 1: 20 секунд (1200 кадров), Уровень 2: 15 секунд (900), Уровень 3: 10 секунд (600)
        litter_cooldowns = {1: 1200, 2: 900, 3: 600}
        self.litter_cooldown = litter_cooldowns.get(level, 1200)
        self.litter_timer = random.randint(self.litter_cooldown // 2, self.litter_cooldown)

        # Максимум мусора на уровень (1: 10, 2: 15, 3: 20)
        self.max_trash_spawned = {1: 10, 2: 15, 3: 20}.get(level, 10)
        self.trash_spawned = 0

        # Механика оглушения
        self.stunned = False
        self.stun_timer = 0
        self.stun_duration = 3600  # 60 секунд (60 FPS * 60)
        self.star_rotation = 0  # Для анимации звездочек

        # Рисуем злодея (темные цвета)
        self.draw_litterer()

    def draw_litterer(self):
        """Рисовать мусорщика"""
        self.image.fill((0, 0, 0, 0))

        if self.stunned:
            # Присевший злодей
            # Голова (темная, ниже)
            pygame.draw.circle(self.image, (80, 60, 40), (17, 18), 10)

            # Закрытые глаза (крестики)
            pygame.draw.line(self.image, BLACK, (11, 16), (15, 20), 2)
            pygame.draw.line(self.image, BLACK, (15, 16), (11, 20), 2)
            pygame.draw.line(self.image, BLACK, (19, 16), (23, 20), 2)
            pygame.draw.line(self.image, BLACK, (23, 16), (19, 20), 2)

            # Тело (присевший, короче)
            pygame.draw.rect(self.image, (40, 40, 40), (7, 26, 20, 10))

            # Ноги (согнутые)
            pygame.draw.rect(self.image, (30, 30, 30), (10, 36, 5, 4))
            pygame.draw.rect(self.image, (30, 30, 30), (19, 36, 5, 4))

            # Звездочки над головой (вращающиеся)
            self.draw_stars()
        else:
            # Обычный злодей
            # Голова (темная)
            pygame.draw.circle(self.image, (80, 60, 40), (17, 12), 10)

            # Злобные глаза
            pygame.draw.circle(self.image, (255, 0, 0), (13, 10), 2)
            pygame.draw.circle(self.image, (255, 0, 0), (21, 10), 2)

            # Тело (грязная одежда)
            pygame.draw.rect(self.image, (40, 40, 40), (7, 20, 20, 15))

            # Ноги
            pygame.draw.rect(self.image, (30, 30, 30), (10, 35, 5, 5))
            pygame.draw.rect(self.image, (30, 30, 30), (19, 35, 5, 5))

            # Мусор в руке (коричневый мешок)
            pygame.draw.circle(self.image, (100, 70, 30), (28, 25), 4)

    def draw_stars(self):
        """Рисовать звездочки над головой"""
        # 3 звездочки кружатся над головой
        for i in range(3):
            angle = self.star_rotation + (i * 120)  # 3 звезды на 120 градусов друг от друга
            rad = math.radians(angle)
            x = 17 + int(math.cos(rad) * 15)
            y = 5 + int(math.sin(rad) * 8)

            # Рисуем маленькую звездочку
            star_size = 4
            points = []
            for j in range(10):
                star_angle = math.pi / 2 + j * math.pi / 5 + math.radians(self.star_rotation)
                radius = star_size if j % 2 == 0 else star_size // 2
                px = x + int(math.cos(star_angle) * radius)
                py = y + int(math.sin(star_angle) * radius)
                points.append((px, py))

            pygame.draw.polygon(self.image, YELLOW, points)
            pygame.draw.polygon(self.image, ORANGE, points, 1)

    def get_stunned(self):
        """Оглушить мусорщика"""
        self.stunned = True
        self.stun_timer = self.stun_duration
        self.star_rotation = 0

    def update(self):
        """Обновление мусорщика"""
        # Обработка оглушения
        if self.stunned:
            self.stun_timer -= 1
            self.star_rotation += 5  # Вращаем звездочки
            if self.stun_timer <= 0:
                self.stunned = False
            # Перерисовываем злодея
            self.draw_litterer()
            return  # Не двигаемся и не выбрасываем мусор когда оглушен

        # Случайное движение
        self.direction_timer -= 1
        if self.direction_timer <= 0:
            self.direction = random.choice(['left', 'right', 'up', 'down'])
            self.direction_timer = random.randint(60, 180)

        # Движение в выбранном направлении
        old_x, old_y = self.rect.x, self.rect.y

        if self.direction == 'left':
            self.rect.x -= self.speed
        elif self.direction == 'right':
            self.rect.x += self.speed
        elif self.direction == 'up':
            self.rect.y -= self.speed
        elif self.direction == 'down':
            self.rect.y += self.speed

        # Проверка границ мира
        if self.rect.x < 0 or self.rect.x > self.world_width - self.width:
            self.rect.x = old_x
            self.direction = random.choice(['left', 'right', 'up', 'down'])
        if self.rect.y < 0 or self.rect.y > self.world_height - self.height:
            self.rect.y = old_y
            self.direction = random.choice(['left', 'right', 'up', 'down'])

        # Таймер выброса мусора
        self.litter_timer -= 1

    def should_drop_litter(self):
        """Проверка, пора ли выбросить мусор"""
        # Не выбрасываем если оглушен
        if self.stunned:
            return False

        # Не выбрасываем если достигли лимита
        if self.trash_spawned >= self.max_trash_spawned:
            return False

        if self.litter_timer <= 0:
            self.litter_timer = self.litter_cooldown  # Используем кулдаун в зависимости от уровня
            self.trash_spawned += 1
            return True
        return False


class AdvancedDrone(pygame.sprite.Sprite):
    """Продвинутый дрон с pathfinding по клику мыши"""
    def __init__(self, player):
        super().__init__()
        self.width = 30
        self.height = 24
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.player = player
        self.rect.centerx = player.rect.centerx
        self.rect.centery = player.rect.centery - 40

        self.active = False
        self.target_pos = None
        self.speed = 3
        self.collected_trash = []

        self.draw_drone()

    def draw_drone(self):
        """Рисовать продвинутый дрон"""
        self.image.fill((0, 0, 0, 0))

        # Корпус (зеленый с градиентом)
        for i in range(10):
            shade = 180 + i * 5
            pygame.draw.ellipse(self.image, (0, shade, 0),
                              (7, 8 + i, 16, 2))

        # Пропеллеры
        pygame.draw.circle(self.image, (100, 100, 100), (5, 8), 5)
        pygame.draw.circle(self.image, (100, 100, 100), (25, 8), 5)
        pygame.draw.circle(self.image, (150, 150, 150), (5, 8), 3)
        pygame.draw.circle(self.image, (150, 150, 150), (25, 8), 3)

        # Индикатор активности
        if self.active:
            pygame.draw.circle(self.image, GREEN, (15, 12), 3)
        else:
            pygame.draw.circle(self.image, RED, (15, 12), 3)

    def set_target(self, world_x, world_y):
        """Установить целевую позицию"""
        if self.active:
            self.target_pos = (world_x, world_y)

    def update(self):
        """Обновить позицию дрона"""
        self.draw_drone()  # Перерисовать для обновления индикатора

        if not self.active:
            # Следовать за игроком
            self.rect.centerx = self.player.rect.centerx
            self.rect.centery = self.player.rect.centery - 40
            return

        if self.target_pos:
            # Двигаться к цели
            dx = self.target_pos[0] - self.rect.centerx
            dy = self.target_pos[1] - self.rect.centery
            dist = math.sqrt(dx*dx + dy*dy)

            if dist > 5:
                # Нормализовать и двигаться
                self.rect.centerx += (dx / dist) * self.speed
                self.rect.centery += (dy / dist) * self.speed
            else:
                # Достигли цели
                self.target_pos = None

    def collect_trash_auto(self, trash_group):
        """Автоматический сбор мусора при достижении"""
        if not self.active or self.target_pos:
            return False

        collect_rect = self.rect.inflate(50, 50)
        for trash in trash_group:
            if collect_rect.colliderect(trash.rect):
                self.collected_trash.append(trash)
                trash.kill()
                return True
        return False

    def return_to_player(self):
        """Вернуться к игроку и передать мусор"""
        dist_to_player = math.sqrt(
            (self.rect.centerx - self.player.rect.centerx)**2 +
            (self.rect.centery - self.player.rect.centery)**2
        )

        if dist_to_player < 50 and self.collected_trash:
            # Передать мусор игроку
            count = len(self.collected_trash)
            self.collected_trash.clear()
            return count
        return 0


class GrassTile(pygame.sprite.Sprite):
    """Трава для леса"""
    def __init__(self, x, y):
        super().__init__()
        self.size = random.randint(30, 50)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.draw_grass()

    def draw_grass(self):
        # Разные оттенки зеленого для травы
        base_green = random.randint(80, 120)
        grass_color = (20, base_green, 20)

        # Рисуем несколько травинок
        for i in range(random.randint(5, 10)):
            blade_x = random.randint(0, self.size)
            blade_y = random.randint(5, self.size)
            blade_height = random.randint(8, 15)
            blade_width = random.randint(2, 4)

            # Небольшая вариация цвета
            var = random.randint(-15, 15)
            color = (grass_color[0] + var, grass_color[1] + var, grass_color[2] + var)

            # Рисуем травинку
            pygame.draw.line(self.image, color,
                           (blade_x, blade_y),
                           (blade_x + random.randint(-2, 2), blade_y - blade_height),
                           blade_width)


class PoisonPlant(pygame.sprite.Sprite):
    """Ядовитое растение которое замедляет игрока"""
    def __init__(self, x, y):
        super().__init__()
        self.width = 32
        self.height = 32
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.glow = 0
        self.draw_plant()

    def draw_plant(self):
        """Рисовать ядовитое растение (похоже на траву но с фиолетовым оттенком)"""
        self.image.fill((0, 0, 0, 0))

        # Ядовитый цвет (темно-зеленый с фиолетовым)
        poison_color = (60, 100, 80)
        highlight_color = (120, 60, 150)  # Фиолетовый

        # Стебель
        for i in range(5):
            stalk_x = 8 + i * 5
            pygame.draw.line(self.image, poison_color,
                           (stalk_x, 28), (stalk_x, 10), 3)

        # Листья с фиолетовым свечением
        glow_intensity = int(abs(math.sin(self.glow)) * 50)
        glow_color = (poison_color[0] + glow_intensity,
                     poison_color[1],
                     poison_color[2] + glow_intensity)

        for i in range(6):
            leaf_x = 5 + i * 4
            leaf_y = 15 + random.randint(-3, 3)
            pygame.draw.circle(self.image, glow_color, (leaf_x, leaf_y), 4)

        # Яркие фиолетовые точки (споры)
        for i in range(3):
            spore_x = random.randint(8, 24)
            spore_y = random.randint(8, 20)
            pygame.draw.circle(self.image, highlight_color, (spore_x, spore_y), 2)

    def update(self):
        self.glow += 0.05
        if self.glow > math.pi * 2:
            self.glow = 0
        self.draw_plant()


class HealingStation(pygame.sprite.Sprite):
    """Аптечка для лечения отравления"""
    def __init__(self, x, y):
        super().__init__()
        self.width = 40
        self.height = 40
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.pulse = 0
        self.draw_station()

    def draw_station(self):
        """Рисовать аптечку"""
        self.image.fill((0, 0, 0, 0))

        # Пульсация
        pulse_size = int(3 * abs(math.sin(self.pulse)))

        # Белый фон аптечки
        box_rect = pygame.Rect(5 - pulse_size, 5 - pulse_size,
                              30 + pulse_size * 2, 30 + pulse_size * 2)
        pygame.draw.rect(self.image, WHITE, box_rect, 0, 5)
        pygame.draw.rect(self.image, RED, box_rect, 3, 5)

        # Красный крест
        # Вертикальная линия
        pygame.draw.rect(self.image, RED, (17, 10, 6, 20), 0, 2)
        # Горизонтальная линия
        pygame.draw.rect(self.image, RED, (10, 17, 20, 6), 0, 2)

    def update(self):
        self.pulse += 0.1
        if self.pulse > math.pi * 2:
            self.pulse = 0
        self.draw_station()


class RiverSegment(pygame.sprite.Sprite):
    """Сегмент ручья"""
    def __init__(self, x, y, width, height, flowing=False, angle=0, is_blockage_point=False):
        super().__init__()
        self.width = width
        self.height = height
        self.flowing = flowing
        self.angle = angle  # Угол течения
        self.is_blockage_point = is_blockage_point  # Точка блокировки мусором
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.wave_offset = random.random() * math.pi * 2

        # Сила течения (для физики)
        self.flow_strength = 2.0 if flowing else 0
        self.flow_direction_x = math.cos(angle + math.pi / 2)  # Перпендикулярно углу
        self.flow_direction_y = math.sin(angle + math.pi / 2)

        self.draw_water()

    def draw_water(self):
        """Рисовать воду"""
        self.image.fill((0, 0, 0, 0))

        if self.flowing:
            # Текущая вода (анимированная)
            base_blue = WATER_BLUE

            # Волны
            for y in range(0, self.height, 3):
                wave = int(10 * math.sin(self.wave_offset + y * 0.2))
                color_var = int(20 * abs(math.sin(self.wave_offset + y * 0.1)))
                water_color = (
                    base_blue[0] + color_var,
                    base_blue[1] + color_var,
                    base_blue[2] + color_var
                )
                pygame.draw.rect(self.image, water_color, (wave, y, self.width - wave, 3))
        else:
            # Стоячая вода (тусклая)
            stagnant_color = (40, 80, 100)
            pygame.draw.rect(self.image, stagnant_color, (0, 0, self.width, self.height))

            # Темные пятна (загрязнение)
            for i in range(5):
                x = random.randint(0, self.width - 10)
                y = random.randint(0, self.height - 10)
                pygame.draw.circle(self.image, (30, 60, 70), (x, y), random.randint(3, 8))

            # Если это точка блокировки - рисуем дополнительное загрязнение
            if self.is_blockage_point:
                # Более темная, грязная вода в центре
                blockage_color = (25, 50, 60)
                center_y = self.height // 2
                pygame.draw.ellipse(self.image, blockage_color,
                                  (5, center_y - 30, self.width - 10, 60))

                # Мусорные пятна
                for i in range(10):
                    x = random.randint(10, self.width - 10)
                    y = random.randint(center_y - 25, center_y + 25)
                    size = random.randint(2, 6)
                    mud_color = (20 + random.randint(0, 20),
                               40 + random.randint(0, 20),
                               50 + random.randint(0, 20))
                    pygame.draw.circle(self.image, mud_color, (x, y), size)

    def update(self):
        self.wave_offset += 0.1
        if self.wave_offset > math.pi * 2:
            self.wave_offset = 0
        self.draw_water()

    def start_flowing(self):
        """Начать течение"""
        self.flowing = True
        self.flow_strength = 2.0

    def apply_current_to_player(self, player):
        """Проверить состояние воды под игроком"""
        if player.rect.colliderect(self.rect):
            if self.flowing:
                return "flowing"
            else:
                # Стоячая вода замедляет (возвращаем флаг)
                return "blocked"
        return None

    def push_player_by_current(self, player):
        """Толкнуть игрока течением (вызывается после движения)"""
        if player.rect.colliderect(self.rect) and self.flowing:
            # Сильное течение толкает игрока
            player.rect.x += self.flow_direction_x * self.flow_strength
            player.rect.y += self.flow_direction_y * self.flow_strength


class WaterFlowParticle(pygame.sprite.Sprite):
    """Частица воды для эффекта течения"""
    def __init__(self, x, y):
        super().__init__()
        self.size = random.randint(2, 5)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (100, 180, 255), (self.size // 2, self.size // 2), self.size // 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = random.uniform(1, 3)
        self.vel_y = random.uniform(0.5, 1.5)
        self.lifetime = random.randint(30, 60)

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


class Particle(pygame.sprite.Sprite):
    """Частицы с улучшенной графикой"""
    def __init__(self, x, y, color):
        super().__init__()
        self.size = random.randint(3, 6)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (self.size // 2, self.size // 2), self.size // 2)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.vel_x = random.uniform(-3, 3)
        self.vel_y = random.uniform(-4, -1)
        self.lifetime = random.randint(20, 40)

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.vel_y += 0.2
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


class House(pygame.sprite.Sprite):
    """Деревенский дом"""
    def __init__(self, x, y):
        super().__init__()
        self.width = 80
        self.height = 90
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.draw_house()

    def draw_house(self):
        """Рисовать дом"""
        # Стены (деревянные)
        wall_color = (160, 100, 50)
        pygame.draw.rect(self.image, wall_color, (10, 30, 60, 50), 0, 5)

        # Деревянные доски
        for i in range(30, 80, 8):
            pygame.draw.line(self.image, (140, 80, 40), (10, i), (70, i), 1)

        # Крыша (красная черепица)
        roof_color = (180, 50, 50)
        roof_points = [(5, 30), (40, 5), (75, 30)]
        pygame.draw.polygon(self.image, roof_color, roof_points)

        # Черепица
        for y in range(10, 30, 6):
            for x in range(15, 65, 12):
                pygame.draw.arc(self.image, (140, 30, 30), (x, y, 10, 6), 0, math.pi, 2)

        # Дверь
        door_color = (100, 60, 30)
        pygame.draw.rect(self.image, door_color, (28, 50, 24, 30), 0, 3)
        pygame.draw.circle(self.image, YELLOW, (48, 65), 2)

        # Окна
        window_color = (150, 200, 255)
        # Левое окно
        pygame.draw.rect(self.image, window_color, (18, 42, 14, 14), 0, 2)
        pygame.draw.line(self.image, DARK_BROWN, (18, 49), (32, 49), 2)
        pygame.draw.line(self.image, DARK_BROWN, (25, 42), (25, 56), 2)

        # Правое окно
        pygame.draw.rect(self.image, window_color, (58, 42, 14, 14), 0, 2)
        pygame.draw.line(self.image, DARK_BROWN, (58, 49), (72, 49), 2)
        pygame.draw.line(self.image, DARK_BROWN, (65, 42), (65, 56), 2)

        # Труба на крыше
        chimney_color = (120, 60, 40)
        pygame.draw.rect(self.image, chimney_color, (50, 12, 10, 20))

        # Дым из трубы
        smoke_color = (200, 200, 200, 100)
        pygame.draw.circle(self.image, smoke_color, (55, 8), 4)
        pygame.draw.circle(self.image, smoke_color, (58, 4), 3)


class Quest:
    """Класс квеста"""
    def __init__(self, quest_id, description, reward, objective_type, objective_count=1):
        self.quest_id = quest_id
        self.description = description
        self.reward = reward
        self.objective_type = objective_type
        self.objective_count = objective_count
        self.current_count = 0
        self.completed = False
        self.objectives = []  # Список объектов квеста


class QuestGiver(pygame.sprite.Sprite):
    """НПС дающий квесты (светится желтым)"""
    def __init__(self, x, y, quest):
        super().__init__()
        self.width = 40
        self.height = 50
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.quest = quest
        self.has_quest = True
        self.glow_offset = 0
        self.interaction_distance = 60
        self.draw_npc()

    def draw_npc(self):
        """Рисовать НПС"""
        self.image.fill((0, 0, 0, 0))

        # Желтое свечение если есть квест
        if self.has_quest:
            glow_radius = int(25 + 5 * abs(math.sin(self.glow_offset)))
            glow_color = (255, 215, 0, 80)
            pygame.draw.circle(self.image, glow_color, (20, 30), glow_radius)

        # Тело НПС (фермер)
        skin_color = (255, 220, 177)
        clothes_color = (100, 150, 100)

        # Тень
        pygame.draw.ellipse(self.image, (0, 0, 0, 100), (8, 45, 24, 8))

        # Голова
        pygame.draw.ellipse(self.image, skin_color, (12, 10, 16, 16))

        # Шляпа (соломенная)
        hat_color = (210, 180, 140)
        pygame.draw.arc(self.image, hat_color, (8, 8, 24, 16), 0, math.pi, 6)

        # Глаза
        pygame.draw.circle(self.image, BLACK, (16, 16), 2)
        pygame.draw.circle(self.image, BLACK, (24, 16), 2)

        # Улыбка
        pygame.draw.arc(self.image, BLACK, (14, 18, 12, 8), 0, math.pi, 2)

        # Тело
        pygame.draw.ellipse(self.image, clothes_color, (10, 24, 20, 18))

        # Руки
        pygame.draw.rect(self.image, clothes_color, (6, 28, 6, 10), 0, 2)
        pygame.draw.rect(self.image, clothes_color, (28, 28, 6, 10), 0, 2)

        # Ноги
        pygame.draw.rect(self.image, (60, 40, 20), (12, 38, 6, 10), 0, 2)
        pygame.draw.rect(self.image, (60, 40, 20), (22, 38, 6, 10), 0, 2)

    def update(self):
        self.glow_offset += 0.1
        self.draw_npc()

    def check_player_nearby(self, player):
        """Проверить близость игрока"""
        distance = math.sqrt((self.rect.centerx - player.rect.centerx)**2 +
                           (self.rect.centery - player.rect.centery)**2)
        return distance < self.interaction_distance and self.has_quest


class QuestObjective(pygame.sprite.Sprite):
    """Объект квеста (мусорный бак, урна и т.д.)"""
    def __init__(self, x, y, quest_id):
        super().__init__()
        self.width = 32
        self.height = 40
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.quest_id = quest_id
        self.glow_offset = 0
        self.collected = False
        self.draw_bin()

    def draw_bin(self):
        """Рисовать мусорный бак"""
        self.image.fill((0, 0, 0, 0))

        # Свечение (желто-зеленое)
        if not self.collected:
            glow_radius = int(20 + 4 * abs(math.sin(self.glow_offset)))
            glow_color = (255, 255, 0, 100)
            pygame.draw.circle(self.image, glow_color, (16, 20), glow_radius)

        # Мусорный бак (серый металлический)
        bin_color = (120, 120, 130)
        pygame.draw.rect(self.image, bin_color, (6, 10, 20, 26), 0, 3)

        # Крышка
        lid_color = (100, 100, 110)
        pygame.draw.ellipse(self.image, lid_color, (4, 8, 24, 8))
        pygame.draw.circle(self.image, (80, 80, 90), (16, 12), 3)

        # Полосы на баке
        for i in range(15, 35, 6):
            pygame.draw.line(self.image, (140, 140, 150), (6, i), (26, i), 1)

        # Символ переработки
        recycle_color = GREEN
        pygame.draw.circle(self.image, recycle_color, (16, 22), 6, 2)
        pygame.draw.polygon(self.image, recycle_color,
                          [(16, 18), (16, 26), (13, 22)])

    def update(self):
        self.glow_offset += 0.15
        self.draw_bin()


class CelebratingVillager(pygame.sprite.Sprite):
    """Житель деревни празднующий восстановление реки"""
    def __init__(self, x, y):
        super().__init__()
        self.width = 30
        self.height = 40
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.jump_offset = 0
        self.jump_speed = 0.2
        self.skin_color = random.choice([
            (255, 220, 177),
            (200, 160, 130),
            (230, 190, 150)
        ])
        self.clothes_color = random.choice([
            (200, 50, 50),
            (50, 100, 200),
            (100, 200, 100),
            (200, 150, 50)
        ])

    def draw_villager(self):
        """Рисовать празднующего жителя"""
        self.image.fill((0, 0, 0, 0))

        jump_y = int(8 * abs(math.sin(self.jump_offset)))

        # Тень
        shadow_size = 20 - jump_y // 2
        pygame.draw.ellipse(self.image, (0, 0, 0, 80),
                          (5, 36, shadow_size, 6))

        y_offset = -jump_y

        # Голова
        pygame.draw.ellipse(self.image, self.skin_color,
                          (8, 8 + y_offset, 14, 14))

        # Глаза (счастливые)
        pygame.draw.circle(self.image, BLACK, (12, 14 + y_offset), 2)
        pygame.draw.circle(self.image, BLACK, (18, 14 + y_offset), 2)

        # Широкая улыбка
        pygame.draw.arc(self.image, BLACK, (10, 16 + y_offset, 10, 6),
                       0, math.pi, 2)

        # Тело
        pygame.draw.ellipse(self.image, self.clothes_color,
                          (7, 20 + y_offset, 16, 12))

        # Руки вверх (празднование!)
        pygame.draw.line(self.image, self.clothes_color,
                        (9, 24 + y_offset), (5, 18 + y_offset), 4)
        pygame.draw.line(self.image, self.clothes_color,
                        (21, 24 + y_offset), (25, 18 + y_offset), 4)

        # Ноги
        pygame.draw.rect(self.image, (60, 40, 20),
                        (10, 30 + y_offset, 4, 8), 0, 2)
        pygame.draw.rect(self.image, (60, 40, 20),
                        (16, 30 + y_offset, 4, 8), 0, 2)

    def update(self):
        self.jump_offset += self.jump_speed
        self.draw_villager()


if __name__ == "__main__":
    game = Game()
    game.run()
