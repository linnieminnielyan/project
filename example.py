import arcade
import random
import math
from arcade.gui import UIManager, UIFlatButton, UILabel, UIInputText
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
import sqlite3

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Гонки - Многоуровневая игра"
BUTTON_SIZE = {"width": 200, "height": 50}
TILE_SCALING = 0.5
CAR_SPEED_LEVEL_1 = 5
CAR_SPEED_LEVEL_2 = 7
AI_CAR_SPEED_MIN = 2.0
AI_CAR_SPEED_MAX = 4.0


class GameDatabase:

    def __init__(self, db_name="game_database12345.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect_database()

    def connect_database(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    current_level INTEGER DEFAULT 1,
                    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
                )
            ''')
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return False

    def register_player(self, username, password):
        try:
            if not self.conn:
                if not self.connect_database():
                    return False, "Ошибка подключения к базе данных"
            if not username or not password:
                return False, "Логин и пароль не могут быть пустыми"

            if len(username) < 3:
                return False, "Логин должен быть не менее 3 символов"

            if len(password) < 4:
                return False, "Пароль должен быть не менее 4 символов"
            self.cursor.execute("SELECT id FROM players WHERE username = ?", (username,))
            existing_player = self.cursor.fetchone()

            if existing_player:
                return False, "Игрок с таким логином уже существует"
            self.cursor.execute(
                "INSERT INTO players (username, password) VALUES (?, ?)",
                (username, password)
            )
            player_id = self.cursor.lastrowid
            self.cursor.execute(
                "INSERT INTO player_progress (player_id, current_level) VALUES (?, ?)",
                (player_id, 1)
            )
            self.conn.commit()
            return True, "Регистрация успешна! Ваш текущий уровень: 1"
        except sqlite3.IntegrityError:
            return False, "Игрок с таким логином уже существует"
        except Exception as e:
            return False, f"Ошибка регистрации: {str(e)}"

    def login_player(self, username, password):
        try:
            if not self.conn:
                if not self.connect_database():
                    return False, "Ошибка подключения к базе данных"

            self.cursor.execute(
                "SELECT id, username FROM players WHERE username = ? AND password = ?",
                (username, password)
            )
            player = self.cursor.fetchone()
            if player:
                self.cursor.execute(
                    "SELECT current_level FROM player_progress WHERE player_id = ?",
                    (player[0],)
                )
                progress = self.cursor.fetchone()
                current_level = progress[0] if progress else 1
                return True, {
                    'id': player[0],
                    'username': player[1],
                    'current_level': current_level
                }
            else:
                return False, "Неверный логин или пароль"
        except Exception as e:
            return False, f"Ошибка входа: {str(e)}"

    def update_player_level(self, player_id, new_level):
        try:
            if not self.conn:
                if not self.connect_database():
                    return False, "Ошибка подключения к базе данных"
            self.cursor.execute(
                "UPDATE player_progress SET current_level = ? WHERE player_id = ?",
                (new_level, player_id)
            )
            if self.cursor.rowcount == 0:
                self.cursor.execute(
                    "INSERT INTO player_progress (player_id, current_level) VALUES (?, ?)",
                    (player_id, new_level)
                )

            self.conn.commit()
            return True, f"Уровень обновлен до {new_level}"
        except Exception as e:
            return False, f"Ошибка обновления уровня: {str(e)}"

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            except:
                pass

db = GameDatabase("game_database12345.db")

class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ui_manager = UIManager()
        self.setup_ui()

    def setup_ui(self):
        vbox = UIBoxLayout(space_between=20)
        label = UILabel(
            text="ИГРА ГОНКИ",
            font_size=36,
            text_color=arcade.color.GOLD,
            width=350,
            align="center",
            bold=True
        )
        vbox.add(label)

        sub_label = UILabel(
            text="Добро пожаловать в гоночную арену!",
            font_size=18,
            text_color=arcade.color.LIGHT_GRAY,
            width=350,
            align="center"
        )
        vbox.add(sub_label)
        enter_button = UIFlatButton(
            text="ВОЙТИ",
            width=BUTTON_SIZE['width'],
            height=BUTTON_SIZE['height']
        )
        enter_button.on_click = self.on_enter_clicked
        vbox.add(enter_button)
        new_player_button = UIFlatButton(
            text="РЕГИСТРАЦИЯ",
            width=BUTTON_SIZE['width'],
            height=BUTTON_SIZE['height']
        )
        new_player_button.on_click = self.on_registration_clicked
        vbox.add(new_player_button)
        anchor_layout = UIAnchorLayout()
        anchor_layout.add(vbox, anchor_x="center", anchor_y="center")
        self.ui_manager.add(anchor_layout)

    def on_enter_clicked(self, event):
        login_view = LoginView()
        self.window.show_view(login_view)

    def on_registration_clicked(self, event):
        registration_view = RegistrationView()
        self.window.show_view(registration_view)

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.DARK_BLUE)
        self.ui_manager.draw()
        arcade.draw_text(
            "Для начала игры зарегистрируйтесь или войдите в систему",
            SCREEN_WIDTH // 2, 40,
            arcade.color.LIGHT_GRAY, 14,
            anchor_x="center", anchor_y="center"
        )

    def on_show_view(self):
        self.ui_manager.enable()

    def on_hide_view(self):
        self.ui_manager.disable()

    def on_mouse_motion(self, x, y, dx, dy):
        self.ui_manager.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        self.ui_manager.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self.ui_manager.on_mouse_release(x, y, button, modifiers)


class LoginView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ui_manager = UIManager()
        self.username_input = None
        self.password_input = None
        self.message_label = None
        self.setup_ui()

    def setup_ui(self):
        vbox = UIBoxLayout(space_between=15)

        title = UILabel(
            text="ВХОД В СИСТЕМУ",
            font_size=28,
            text_color=arcade.color.GOLD,
            width=400,
            align="center",
            bold=True
        )
        vbox.add(title)

        # Поле логина
        username_label = UILabel(
            text="Имя пользователя:",
            font_size=16,
            text_color=arcade.color.WHITE
        )
        vbox.add(username_label)

        self.username_input = UIInputText(
            width=300,
            height=40,
            font_size=16,
            text_color=arcade.color.BLACK,
            bg_color=arcade.color.LIGHT_GRAY,
            placeholder_text="Введите логин"
        )
        vbox.add(self.username_input)

        # Поле пароля
        password_label = UILabel(
            text="Пароль:",
            font_size=16,
            text_color=arcade.color.WHITE
        )
        vbox.add(password_label)

        self.password_input = UIInputText(
            width=300,
            height=40,
            font_size=16,
            text_color=arcade.color.BLACK,
            bg_color=arcade.color.LIGHT_GRAY,
            placeholder_text="Введите пароль",
            password=True
        )
        vbox.add(self.password_input)

        # Кнопки
        button_container = UIBoxLayout(vertical=False, space_between=20)

        login_button = UIFlatButton(
            text="ВОЙТИ",
            width=140,
            height=45
        )
        login_button.on_click = self.on_login_clicked
        button_container.add(login_button)

        back_button = UIFlatButton(
            text="НАЗАД",
            width=140,
            height=45
        )
        back_button.on_click = self.on_back_clicked
        button_container.add(back_button)

        vbox.add(button_container)
        self.message_label = UILabel(
            text="",
            font_size=12,
            text_color=arcade.color.RED,
            width=400,
            align="center"
        )
        vbox.add(self.message_label)
        anchor_layout = UIAnchorLayout()
        anchor_layout.add(vbox, anchor_x="center", anchor_y="center")
        self.ui_manager.add(anchor_layout)

    def on_login_clicked(self, event):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        if not username or not password:
            self.message_label.text = "Заполните все поля"
            self.message_label.text_color = arcade.color.RED
            return

        success, result = db.login_player(username, password)

        if success:
            self.message_label.text = " Вход выполнен успешно!"
            self.message_label.text_color = arcade.color.GREEN
            if result['current_level'] == 1:
                game_view = GameView(result)
                self.window.show_view(game_view)
            elif result['current_level'] == 2:
                second_level = SecondLevel(result)
                self.window.show_view(second_level)
            elif result['current_level'] >= 3:
                third_level = SecondLevel(result)
                self.window.show_view(third_level)
        else:
            self.message_label.text = f" {result}"
            self.message_label.text_color = arcade.color.RED

    def on_back_clicked(self, event):
        menu_view = MainMenuView()
        self.window.show_view(menu_view)

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self.ui_manager.draw()

    def on_show_view(self):
        self.ui_manager.enable()

    def on_hide_view(self):
        self.ui_manager.disable()

    def on_mouse_motion(self, x, y, dx, dy):
        self.ui_manager.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        self.ui_manager.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self.ui_manager.on_mouse_release(x, y, button, modifiers)


class RegistrationView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ui_manager = UIManager()
        self.username_input = None
        self.password_input = None
        self.confirm_password_input = None
        self.message_label = None
        self.setup_ui()

    def setup_ui(self):
        vbox = UIBoxLayout(space_between=15)
        label = UILabel(
            text="СОЗДАНИЕ НОВОГО АККАУНТА",
            font_size=28,
            text_color=arcade.color.GOLD,
            width=400,
            align="center",
            bold=True
        )
        vbox.add(label)
        instruction = UILabel(
            text="Заполните форму для регистрации",
            font_size=14,
            text_color=arcade.color.LIGHT_GRAY,
            width=400,
            align="center"
        )
        vbox.add(instruction)
        vbox.add(UILabel(text="", height=10))
        username_label = UILabel(
            text="Имя пользователя:",
            font_size=16,
            text_color=arcade.color.WHITE
        )
        vbox.add(username_label)
        self.username_input = UIInputText(
            width=300,
            height=40,
            font_size=16,
            text_color=arcade.color.BLACK,
            bg_color=arcade.color.LIGHT_GRAY,
            placeholder_text="Введите логин (минимум 3 символа)"
        )
        vbox.add(self.username_input)
        password_label = UILabel(
            text="Пароль:",
            font_size=16,
            text_color=arcade.color.WHITE
        )
        vbox.add(password_label)
        self.password_input = UIInputText(
            width=300,
            height=40,
            font_size=16,
            text_color=arcade.color.BLACK,
            bg_color=arcade.color.LIGHT_GRAY,
            placeholder_text="Введите пароль (минимум 4 символа)",
            password=True
        )
        vbox.add(self.password_input)
        confirm_label = UILabel(
            text="Подтвердите пароль:",
            font_size=16,
            text_color=arcade.color.WHITE
        )
        vbox.add(confirm_label)
        self.confirm_password_input = UIInputText(
            width=300,
            height=40,
            font_size=16,
            text_color=arcade.color.BLACK,
            bg_color=arcade.color.LIGHT_GRAY,
            placeholder_text="Повторите пароль",
            password=True
        )
        vbox.add(self.confirm_password_input)
        vbox.add(UILabel(text="", height=20))
        register_button = UIFlatButton(
            text="СОЗДАТЬ АККАУНТ",
            width=250,
            height=50
        )
        register_button.on_click = self.on_register_clicked
        vbox.add(register_button)
        vbox.add(UILabel(text="", height=10))
        back_button = UIFlatButton(
            text="НАЗАД",
            width=180,
            height=40
        )
        back_button.on_click = self.on_back_clicked
        vbox.add(back_button)
        vbox.add(UILabel(text="", height=10))
        self.message_label = UILabel(
            text="",
            font_size=12,
            text_color=arcade.color.RED,
            width=400,
            align="center"
        )
        vbox.add(self.message_label)
        anchor_layout = UIAnchorLayout()
        anchor_layout.add(vbox, anchor_x="center", anchor_y="center")
        self.ui_manager.add(anchor_layout)

    def on_register_clicked(self, event):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        confirm_password = self.confirm_password_input.text.strip()
        if not username or not password or not confirm_password:
            self.message_label.text = "Заполните все поля"
            self.message_label.text_color = arcade.color.RED
            return
        if len(username) < 3:
            self.message_label.text = " Логин должен быть не менее 3 символов"
            self.message_label.text_color = arcade.color.RED
            return
        if len(password) < 4:
            self.message_label.text = "️ Пароль должен быть не менее 4 символов"
            self.message_label.text_color = arcade.color.RED
            return
        if password != confirm_password:
            self.message_label.text = "Пароли не совпадают"
            self.message_label.text_color = arcade.color.RED
            return
        success, message = db.register_player(username, password)

        if success:
            self.message_label.text = f" {message}"
            self.message_label.text_color = arcade.color.GREEN
            self.username_input.text = ""
            self.password_input.text = ""
            self.confirm_password_input.text = ""
            login_success, player_data = db.login_player(username, password)
            if login_success:
                game_view = GameView(player_data)
                self.window.show_view(game_view)
        else:
            self.message_label.text = f" {message}"
            self.message_label.text_color = arcade.color.RED

    def on_back_clicked(self, event):
        menu_view = MainMenuView()
        self.window.show_view(menu_view)

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self.ui_manager.draw()
        arcade.draw_text(
            "После регистрации вы автоматически войдете в игру",
            SCREEN_WIDTH // 2, 50,
            arcade.color.LIGHT_GRAY, 15,
            anchor_x="center", anchor_y="center"
        )

    def on_show_view(self):
        self.ui_manager.enable()

    def on_hide_view(self):
        self.ui_manager.disable()

    def on_mouse_motion(self, x, y, dx, dy):
        self.ui_manager.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        self.ui_manager.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self.ui_manager.on_mouse_release(x, y, button, modifiers)


class GameOverView(arcade.View):
    def __init__(self, message, player_data, is_victory=False, winner_name=""):
        super().__init__()
        self.message = message
        self.player_data = player_data
        self.is_victory = is_victory
        self.winner_name = winner_name
        self.ui_manager = UIManager()
        self.setup_ui()

    def setup_ui(self):
        vbox = UIBoxLayout(space_between=20)
        title = "ВЫ ВЫИГРАЛИ!" if self.is_victory else "ПРОИГРЫШ"
        title_color = arcade.color.GOLD if self.is_victory else arcade.color.RED

        title_label = UILabel(
            text=title,
            font_size=36,
            text_color=title_color,
            width=500,
            align="center",
            bold=True
        )
        vbox.add(title_label)

        message_label = UILabel(
            text=self.message,
            font_size=20,
            text_color=arcade.color.WHITE,
            width=500,
            align="center"
        )
        vbox.add(message_label)
        if not self.is_victory and self.winner_name:
            winner_label = UILabel(
                text=f"Выиграла машина: {self.winner_name}",
                font_size=18,
                text_color=arcade.color.YELLOW,
                width=500,
                align="center"
            )
            vbox.add(winner_label)

        player_label = UILabel(
            text=f"Игрок: {self.player_data['username']} | Уровень: {self.player_data['current_level']}",
            font_size=16,
            text_color=arcade.color.LIGHT_GRAY,
            width=500,
            align="center"
        )
        vbox.add(player_label)
        button_container = UIBoxLayout(vertical=False, space_between=20)
        restart_button = UIFlatButton(
            text="ЗАНОВО",
            width=180,
            height=50
        )
        restart_button.on_click = self.on_restart_clicked
        button_container.add(restart_button)
        if self.is_victory and self.player_data['current_level'] < 4:
            next_level_button = UIFlatButton(
                text="СЛЕДУЮЩИЙ УРОВЕНЬ",
                width=180,
                height=50
            )
            next_level_button.on_click = self.on_next_level_clicked
            button_container.add(next_level_button)
        menu_button = UIFlatButton(
            text="В МЕНЮ",
            width=180,
            height=50
        )
        menu_button.on_click = self.on_menu_clicked
        button_container.add(menu_button)
        vbox.add(button_container)
        anchor_layout = UIAnchorLayout()
        anchor_layout.add(vbox, anchor_x="center", anchor_y="center")
        self.ui_manager.add(anchor_layout)

    def on_restart_clicked(self, event):
        if self.player_data['current_level'] == 1:
            game_view = GameView(self.player_data)
        elif self.player_data['current_level'] == 2:
            game_view = SecondLevel(self.player_data)
        elif self.player_data['current_level'] >= 3:
            game_view = SecondLevel(self.player_data)
        self.window.show_view(game_view)

    def on_next_level_clicked(self, event):
        if self.player_data['current_level'] == 1:
            second_level = SecondLevel(self.player_data)
            self.window.show_view(second_level)
        elif self.player_data['current_level'] == 2:
            third_level = SecondLevel(self.player_data)
            self.window.show_view(third_level)
        elif self.player_data['current_level'] == 3:
            game_view = GameView(self.player_data)
            self.window.show_view(game_view)

    def on_menu_clicked(self, event):
        menu_view = MainMenuView()
        self.window.show_view(menu_view)

    def on_draw(self):
        self.clear()
        if self.is_victory:
            arcade.set_background_color(arcade.color.DARK_GREEN)
        else:
            arcade.set_background_color(arcade.color.DARK_RED)
        self.ui_manager.draw()

    def on_show_view(self):
        self.ui_manager.enable()

    def on_hide_view(self):
        self.ui_manager.disable()

    def on_mouse_motion(self, x, y, dx, dy):
        self.ui_manager.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        self.ui_manager.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self.ui_manager.on_mouse_release(x, y, button, modifiers)


class GameView(arcade.View):
    def __init__(self, player_data):
        super().__init__()
        self.player_data = player_data
        sound1 = arcade.load_sound('Aphex_Twin_-_Ptolemy_80592407.mp3')
        sound1.play(volume=0.07)
        self.timer = 3.0
        self.game_started = False
        self.countdown_text = ""
        self.show_go_text = False
        self.go_text_timer = 0
        self.finish_line_y = 150
        self.finish_line_x_start = 200
        self.finish_line_x_end = 760
        self.ai_cars = []
        self.race_finished = False
        self.road_limits = (200, 760)
        self.finish_order = []  # Список машин в порядке финиша
        self.finish_times = {}  # Время финиша каждой машины
        self.game_time = 0
        self.race_start_time = 0
        self.result_shown = False

        self.setup()

    def setup(self):
        tile_map = arcade.load_tilemap("carr2.tmx", scaling=TILE_SCALING)
        self.ground_list = tile_map.sprite_lists["ground"]
        self.trassa_list = tile_map.sprite_lists["trassa"]
        self.decoration_list = tile_map.sprite_lists["sdecoration"]
        self.lines_list = tile_map.sprite_lists["finish_start_lines"]
        self.collision_list = tile_map.sprite_lists["collisions"]

        self.car_list = arcade.SpriteList()
        self.ai_cars = []
        self.finish_order = []
        self.finish_times = {}
        self.race_finished = False
        self.result_shown = False
        self.game_time = 0
        self.race_start_time = 0
        self.calculate_road_limits()
        self.car_yellow = arcade.Sprite("car_yellow (12).png", 0.2)
        self.car_yellow.center_x = 450
        self.car_yellow.center_y = 700
        self.car_yellow.change_x = 0
        self.car_yellow.change_y = 0
        self.car_yellow.has_finished = False
        self.car_yellow.collision_radius = 25
        self.car_yellow.is_player = True
        self.car_yellow.color_name = "Желтая (Вы)"
        self.car_yellow.finish_position = 0
        self.car_yellow.car_length = 60
        self.car_yellow.car_width = 30
        self.car_yellow.front_bumper_y = 0
        self.car_yellow.rear_bumper_y = 0
        self.car_list.append(self.car_yellow)
        self.car_red = arcade.Sprite("car_red12.png", 0.08)
        self.car_red.center_x = 300
        self.car_red.center_y = 700
        self.car_red.ai_speed = random.uniform(AI_CAR_SPEED_MIN, AI_CAR_SPEED_MAX)
        self.car_red.has_finished = False
        self.car_red.collision_radius = 25
        self.car_red.is_player = False
        self.car_red.color_name = "Красная"
        self.car_red.finish_position = 0
        self.car_red.car_length = 24
        self.car_red.car_width = 12
        self.car_red.front_bumper_y = 0
        self.car_red.rear_bumper_y = 0
        self.car_list.append(self.car_red)
        self.ai_cars.append(self.car_red)
        self.car_blue = arcade.Sprite("car_blue123.png", 0.08)
        self.car_blue.center_x = 600
        self.car_blue.center_y = 700
        self.car_blue.ai_speed = random.uniform(AI_CAR_SPEED_MIN, AI_CAR_SPEED_MAX)
        self.car_blue.has_finished = False
        self.car_blue.collision_radius = 25
        self.car_blue.is_player = False
        self.car_blue.color_name = "Синяя"
        self.car_blue.finish_position = 0
        # Параметры для определения передней/задней части
        self.car_blue.car_length = 24
        self.car_blue.car_width = 12
        self.car_blue.front_bumper_y = 0
        self.car_blue.rear_bumper_y = 0
        self.car_list.append(self.car_blue)
        self.ai_cars.append(self.car_blue)

        self.create_physics_engines()

        self.timer = 3.0
        self.game_started = False
        self.countdown_text = "3"
        self.show_go_text = False
        self.go_text_timer = 0

    def calculate_road_limits(self):
        if self.trassa_list and len(self.trassa_list) > 0:
            min_x = SCREEN_WIDTH
            max_x = 0

            for tile in self.trassa_list:
                if tile.center_x < min_x:
                    min_x = tile.center_x
                if tile.center_x > max_x:
                    max_x = tile.center_x

            road_width = max_x - min_x
            padding = road_width * 0.05

            self.road_limits = (min_x + padding, max_x - padding)
        else:
            self.road_limits = (200, 760)

    def create_physics_engines(self):
        self.physics_engines = []

        self.player_physics = arcade.PhysicsEngineSimple(self.car_yellow, self.collision_list)
        self.physics_engines.append(self.player_physics)

        for ai_car in self.ai_cars:
            ai_physics = arcade.PhysicsEngineSimple(ai_car, self.collision_list)
            self.physics_engines.append(ai_physics)

    def update_car_bumpers(self, car):
        if car.scale == 0.2:
            half_length = car.car_length / 2
            car.front_bumper_y = car.center_y - half_length
            car.rear_bumper_y = car.center_y + half_length
        else:
            half_length = car.car_length / 2
            car.front_bumper_y = car.center_y - half_length
            car.rear_bumper_y = car.center_y + half_length

    def check_car_collision_front_rear(self, car1, car2):
        if car1.has_finished or car2.has_finished:
            return False
        self.update_car_bumpers(car1)
        self.update_car_bumpers(car2)
        half_width1 = car1.car_width / 2
        half_width2 = car2.car_width / 2

        x_overlap = abs(car1.center_x - car2.center_x) < (half_width1 + half_width2)

        if not x_overlap:
            return False
        front_to_rear = (car1.front_bumper_y <= car2.rear_bumper_y and
                         car1.front_bumper_y >= car2.front_bumper_y)

        rear_to_front = (car1.rear_bumper_y >= car2.front_bumper_y and
                         car1.rear_bumper_y <= car2.rear_bumper_y)

        side_by_side = (car1.rear_bumper_y > car2.front_bumper_y and
                        car1.front_bumper_y < car2.rear_bumper_y)

        return front_to_rear or rear_to_front or side_by_side

    def check_car_collisions(self, car):
        if car.has_finished:
            return

        for other_car in self.car_list:
            if other_car != car and not other_car.has_finished:
                if self.check_car_collision_front_rear(car, other_car):
                    self.handle_collision(car, other_car)

    def handle_collision(self, car1, car2):
        self.update_car_bumpers(car1)
        self.update_car_bumpers(car2)

        # тип столкновения
        front_to_rear = car1.front_bumper_y <= car2.rear_bumper_y and car1.front_bumper_y >= car2.front_bumper_y
        rear_to_front = car1.rear_bumper_y >= car2.front_bumper_y and car1.rear_bumper_y <= car2.rear_bumper_y
        if front_to_rear:
            push_strength = 20
            if car1.is_player:
                car1.change_y *= 0.3
            else:
                car1.ai_speed *= 0.4
            if car2.is_player:
                car2.change_y = min(car2.change_y - 3, -CAR_SPEED_LEVEL_1)
            else:
                car2.ai_speed = min(car2.ai_speed * 1.5, AI_CAR_SPEED_MAX * 2)

        elif rear_to_front:
            # car1 врезается спереди в car2
            push_strength = 15
            if car1.is_player:
                car1.change_y *= 0.5
            else:
                car1.ai_speed *= 0.6
            if car2.is_player:
                car2.change_y = max(car2.change_y + 2, CAR_SPEED_LEVEL_1)
            else:
                car2.ai_speed = max(car2.ai_speed * 0.8, AI_CAR_SPEED_MIN)
        else:
            # Боковое столкновение
            push_strength = 10
            if car1.is_player:
                car1.change_y *= 0.7
            else:
                car1.ai_speed *= 0.8
            if car2.is_player:
                car2.change_y *= 0.7
            else:
                car2.ai_speed *= 0.8

        # Горизонтальное отталкивание
        dx = car2.center_x - car1.center_x
        if dx != 0:
            push_x = push_strength * 0.3 * (1 if dx > 0 else -1)
            car1.center_x -= push_x
            car2.center_x += push_x

        # Вертикальное отталкивание
        dy = car2.center_y - car1.center_y
        if dy != 0:
            push_y = push_strength * (1 if dy > 0 else -1)
            car1.center_y -= push_y
            car2.center_y += push_y
        self.keep_car_on_road(car1, is_ai=(not car1.is_player))
        self.keep_car_on_road(car2, is_ai=(not car2.is_player))

    def keep_car_on_road(self, car, is_ai=False):
        left_limit, right_limit = self.road_limits
        if car.center_x < left_limit:
            car.center_x = left_limit + 5
            if is_ai and not car.has_finished:
                car.ai_speed *= 0.95
            elif not is_ai and not car.has_finished:
                car.change_x = 0

        elif car.center_x > right_limit:
            car.center_x = right_limit - 5
            if is_ai and not car.has_finished:
                car.ai_speed *= 0.95
            elif not is_ai and not car.has_finished:
                car.change_x = 0

    def check_finish_line(self, car):
        if car.has_finished:
            return False
        if not (self.finish_line_x_start <= car.center_x <= self.finish_line_x_end):
            return False
        self.update_car_bumpers(car)
        if car.front_bumper_y <= self.finish_line_y:
            return True
        return False

    def handle_finish(self, car):
        if not car.has_finished:
            car.has_finished = True
            if car.is_player:
                car.change_x = 0
                car.change_y = 0
            else:
                car.ai_speed = 0
            car.center_y = self.finish_line_y - 5
            race_time = self.game_time - self.race_start_time
            self.finish_times[car] = race_time
            self.finish_order.append(car)
            car.finish_position = len(self.finish_order)
            self.check_race_completion()

    def check_race_completion(self):
        all_finished = all(car.has_finished for car in self.car_list)
        if all_finished and not self.race_finished:
            print(" ВСЕ МАШИНЫ ФИНИШИРОВАЛИ НА УРОВНЕ 1!")
            print("Порядок финиша:")
            for i, car in enumerate(self.finish_order, 1):
                print(f"{i}. {car.color_name} - {self.finish_times[car]:.2f} сек")
            self.race_finished = True
            arcade.schedule(self.show_final_results, 1.0)

    def show_final_results(self, delta_time=None):
        arcade.unschedule(self.show_final_results)
        if self.result_shown:
            return
        self.result_shown = True
        if self.finish_order:
            winner = self.finish_order[0]
            winner_name = winner.color_name
            is_victory = winner.is_player
            message = ""
            if is_victory:
                message = f" ПОБЕДА! Уровень 1 пройден!\nВы финишировали ПЕРВЫМ!\nВремя: {self.finish_times[winner]:.2f} сек"

                success, db_message = db.update_player_level(self.player_data['id'], 2)
                if success:
                    print(f" Уровень игрока {self.player_data['username']} обновлен до 2 в БД")
                    self.player_data['current_level'] = 2
                else:
                    print(f" Ошибка обновления уровня в БД: {db_message}")
            else:
                player_car = self.car_yellow
                player_time = self.finish_times.get(player_car, 0)

                #  позиция игрока
                if player_car in self.finish_order:
                    player_position = self.finish_order.index(player_car) + 1
                else:
                    player_position = "не финишировал"

                message += f'Вы проиграли уровень 1!\n'
                if isinstance(player_position, int):
                    message += f"Вы финишировали {player_position}-м,\n"
                if player_time > 0:
                    message += f"Ваше время: {player_time:.2f} сек"
        else:
            is_victory = False
            message = " Гонка завершена"
            winner_name = ""
        game_over_view = GameOverView(message, self.player_data, is_victory, winner_name)
        self.window.show_view(game_over_view)

    def update_ai_cars(self, delta_time):
        if not self.game_started or self.race_finished:
            return
        for ai_car in self.ai_cars:
            if ai_car.has_finished:
                continue
            ai_car.center_y -= ai_car.ai_speed

            # Проверяем столкновения
            self.check_car_collisions(ai_car)

            # Небольшие случайные отклонения
            if random.random() < 0.03:
                deviation = random.uniform(-10, 10)
                new_x = ai_car.center_x + deviation

                left_limit, right_limit = self.road_limits
                if left_limit <= new_x <= right_limit:
                    ai_car.center_x = new_x
                else:
                    ai_car.center_x += -deviation * 0.3

            self.keep_car_on_road(ai_car, is_ai=True)
            if self.check_finish_line(ai_car) and not ai_car.has_finished:
                self.handle_finish(ai_car)

    def on_update(self, delta_time):
        self.game_time += delta_time
        if not self.game_started:
            self.timer -= delta_time
            if self.timer > 2.0:
                self.countdown_text = "3"
            elif self.timer > 1.0:
                self.countdown_text = "2"
            elif self.timer > 0:
                self.countdown_text = "1"
            else:
                self.countdown_text = ""
                self.game_started = True
                self.show_go_text = True
                self.go_text_timer = 1.0
                self.race_start_time = self.game_time

        # Скрывать текст "ГОНКА!" через 1 секунду
        if self.game_started and self.show_go_text:
            self.go_text_timer -= delta_time
            if self.go_text_timer <= 0:
                self.show_go_text = False
        if self.game_started and not self.race_finished:
            for physics_engine in self.physics_engines:
                physics_engine.update()
            if self.car_yellow and not self.car_yellow.has_finished:
                self.check_car_collisions(self.car_yellow)
            self.update_ai_cars(delta_time)
            if self.car_yellow and not self.car_yellow.has_finished:
                self.keep_car_on_road(self.car_yellow, is_ai=False)

                # Проверяем финиш игрока
                if self.check_finish_line(self.car_yellow) and not self.car_yellow.has_finished:
                    self.handle_finish(self.car_yellow)

    def on_draw(self):
        self.clear()
        if self.ground_list:
            self.ground_list.draw()
        if self.trassa_list:
            self.trassa_list.draw()
        if self.decoration_list:
            self.decoration_list.draw()
        if self.lines_list:
            self.lines_list.draw()
        if self.car_list:
            self.car_list.draw()
        arcade.draw_text(
            f"Игрок: {self.player_data['username']}",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            f"Уровень: {self.player_data['current_level']}",
            10, SCREEN_HEIGHT - 60,
            arcade.color.WHITE, 16
        )
        if self.game_started and not self.race_finished:
            race_time = self.game_time - self.race_start_time
            arcade.draw_text(
                f"Время: {race_time:.1f} сек",
                SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30,
                arcade.color.YELLOW, 16
            )
        if self.game_started and not self.race_finished:
            arcade.draw_text(
                "Цель: первым пересечь линию финиша!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30,
                arcade.color.YELLOW, 22,
                anchor_x="center"
            )
            if self.finish_order:
                arcade.draw_text(
                    f"Финишировало: {len(self.finish_order)}/3",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60,
                    arcade.color.CYAN, 18,
                    anchor_x="center"
                )
                if len(self.finish_order) > 0:
                    leader = self.finish_order[0]
                    if leader.is_player:
                        arcade.draw_text(
                            "ВЫ ЛИДИРУЕТЕ!",
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90,
                            arcade.color.GREEN, 20,
                            anchor_x="center", bold=True
                        )
                    else:
                        arcade.draw_text(
                            f"Лидирует: {leader.color_name}",
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90,
                            arcade.color.RED, 18,
                            anchor_x="center"
                        )

        if not self.game_started:
            arcade.draw_text(
                self.countdown_text,
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                arcade.color.RED, 100,
                anchor_x="center", anchor_y="center",
                bold=True
            )
            arcade.draw_text(
                "ПРИГОТОВЬТЕСЬ К СТАРТУ!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
                arcade.color.WHITE, 30,
                anchor_x="center", anchor_y="center"
            )
        elif self.show_go_text:
            arcade.draw_text(
                "ГОНКА!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                arcade.color.GREEN, 60,
                anchor_x="center", anchor_y="center",
                bold=True
            )

    def on_key_press(self, key, modifiers):
        if self.game_started and self.car_yellow and not self.car_yellow.has_finished:
            if key == arcade.key.UP:
                self.car_yellow.change_y = CAR_SPEED_LEVEL_1
            elif key == arcade.key.DOWN:
                self.car_yellow.change_y = -CAR_SPEED_LEVEL_1
            elif key == arcade.key.LEFT:
                self.car_yellow.change_x = -CAR_SPEED_LEVEL_1
            elif key == arcade.key.RIGHT:
                self.car_yellow.change_x = CAR_SPEED_LEVEL_1

        if key == arcade.key.R:
            self.setup()

        if key == arcade.key.ESCAPE:
            # Возврат в главное меню
            menu_view = MainMenuView()
            self.window.show_view(menu_view)

    def on_key_release(self, key, modifiers):
        if self.game_started and self.car_yellow and not self.car_yellow.has_finished:
            if key == arcade.key.UP or key == arcade.key.DOWN:
                self.car_yellow.change_y = 0
            elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
                self.car_yellow.change_x = 0


class SecondLevel(arcade.View):
    def __init__(self, player_data):
        super().__init__()
        self.player_data = player_data
        self.timer = 3.0
        self.game_started = False
        self.countdown_text = "3"
        self.show_go_text = False
        self.go_text_timer = 0
        self.ai_cars = []
        self.race_finished = False
        self.finish_order = []
        self.finish_times = {}
        self.game_time = 0
        self.race_start_time = 0
        self.finish_line_x = 900
        self.finish_line_y_start = 200
        self.finish_line_y_end = 600
        self.result_shown = False
        self.music_playing = False
        self.setup()

    def setup(self):
        if not self.music_playing:
            sound = arcade.load_sound('Aphex_Twin_-_Ptolemy_80592407.mp3')
            sound.play(volume=0.07)
            self.music_playing = True
        tile_map = arcade.load_tilemap("does.tmx", scaling=TILE_SCALING)
        self.ground_list = tile_map.sprite_lists["earth"]
        self.finish_list = tile_map.sprite_lists["finish"]
        self.start_list = tile_map.sprite_lists["start"]
        self.collisions_list = tile_map.sprite_lists["collisions"]
        self.roks_list = tile_map.sprite_lists["rocs"]
        self.car_list = arcade.SpriteList()
        self.ai_cars = []
        self.car_yellow = arcade.Sprite("car_yellow (1).png", 0.2)
        self.car_yellow.center_x = 50
        self.car_yellow.center_y = 650
        self.car_yellow.angle = 0
        self.car_yellow.change_x = 0
        self.car_yellow.change_y = 0
        self.car_yellow.has_finished = False
        self.car_yellow.collision_radius = 25
        self.car_yellow.is_player = True
        self.car_yellow.color_name = "Желтая (Вы)"
        self.car_list.append(self.car_yellow)
        self.car_red = arcade.Sprite("car_red1.png", 0.08)
        self.car_red.center_x = 50
        self.car_red.center_y = 430
        self.car_red.angle = 0
        self.car_red.ai_speed = random.uniform(AI_CAR_SPEED_MIN, AI_CAR_SPEED_MAX)
        self.car_red.has_finished = False
        self.car_red.collision_radius = 25
        self.car_red.is_player = False
        self.car_red.color_name = "Красная"
        self.car_list.append(self.car_red)
        self.ai_cars.append(self.car_red)
        self.car_blue = arcade.Sprite("car_blue1.png", 0.08)
        self.car_blue.center_x = 50
        self.car_blue.center_y = 250
        self.car_blue.angle = 0
        self.car_blue.ai_speed = random.uniform(AI_CAR_SPEED_MIN, AI_CAR_SPEED_MAX)
        self.car_blue.has_finished = False
        self.car_blue.collision_radius = 25
        self.car_blue.is_player = False
        self.car_blue.color_name = "Синяя"
        self.car_list.append(self.car_blue)
        self.ai_cars.append(self.car_blue)
        self.physics_engines = []
        all_collision_objects = arcade.SpriteList()
        all_collision_objects.extend(self.collisions_list)
        all_collision_objects.extend(self.roks_list)
        self.player_physics = arcade.PhysicsEngineSimple(self.car_yellow, all_collision_objects)
        self.physics_engines.append(self.player_physics)
        for ai_car in self.ai_cars:
            ai_physics = arcade.PhysicsEngineSimple(ai_car, all_collision_objects)
            self.physics_engines.append(ai_physics)
        self.timer = 3.0
        self.game_started = False
        self.countdown_text = "3"
        self.show_go_text = False
        self.go_text_timer = 0
        self.race_finished = False
        self.game_time = 0
        self.race_start_time = 0
        self.finish_order = []
        self.finish_times = {}
        self.result_shown = False

    def check_car_collision(self, car1, car2):
        if car1.has_finished or car2.has_finished:
            return False
        distance = math.sqrt(
            (car1.center_x - car2.center_x) ** 2 +
            (car1.center_y - car2.center_y) ** 2
        )
        collision_distance = car1.collision_radius + car2.collision_radius
        return distance < collision_distance

    def handle_car_collision(self, car1, car2):
        dx = car2.center_x - car1.center_x
        dy = car2.center_y - car1.center_y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance == 0:
            dx = random.uniform(-1, 1)
            dy = random.uniform(-1, 1)
            distance = math.sqrt(dx * dx + dy * dy)
        dx /= distance
        dy /= distance
        push_strength = 15

        if car1.is_player:
            car1.change_x -= dx * push_strength * 0.5
            car1.change_y -= dy * push_strength * 0.5
            car1.change_x *= 0.7
            car1.change_y *= 0.7
        else:
            car1.ai_speed *= 0.7
            car1.center_x -= dx * push_strength * 0.3
            car1.center_y -= dy * push_strength * 0.3

        if car2.is_player:
            car2.change_x += dx * push_strength * 0.5
            car2.change_y += dy * push_strength * 0.5
            car2.change_x *= 0.7
            car2.change_y *= 0.7
        else:
            car2.ai_speed *= 0.7
            car2.center_x += dx * push_strength * 0.3
            car2.center_y += dy * push_strength * 0.3

    def check_all_car_collisions(self):
        for i in range(len(self.car_list)):
            car1 = self.car_list[i]
            if car1.has_finished:
                continue
            for j in range(i + 1, len(self.car_list)):
                car2 = self.car_list[j]
                if car2.has_finished:
                    continue
                if self.check_car_collision(car1, car2):
                    self.handle_car_collision(car1, car2)

    def keep_car_in_bounds(self, car, is_ai=False):
        margin = 20
        if car.center_x < margin:
            car.center_x = margin
            if car.is_player:
                car.change_x = max(car.change_x, 0)
            else:
                car.ai_speed = max(car.ai_speed * 0.8, AI_CAR_SPEED_MIN)
        if car.center_x > SCREEN_WIDTH - margin:
            car.center_x = SCREEN_WIDTH - margin
            if car.is_player:
                car.change_x = min(car.change_x, 0)
            else:
                car.ai_speed = max(car.ai_speed * 0.8, AI_CAR_SPEED_MIN)
        if car.center_y < margin:
            car.center_y = margin
            if car.is_player:
                car.change_y = max(car.change_y, 0)
        if car.center_y > SCREEN_HEIGHT - margin:
            car.center_y = SCREEN_HEIGHT - margin
            if car.is_player:
                car.change_y = min(car.change_y, 0)

    def check_finish_line(self, car):
        if car.has_finished:
            return False
        if not (self.finish_line_y_start <= car.center_y <= self.finish_line_y_end):
            return False
        if car.center_x >= self.finish_line_x:
            return True
        return False

    def handle_finish(self, car):
        if not car.has_finished:
            car.has_finished = True
            if car.is_player:
                car.change_x = 0
                car.change_y = 0
            else:
                car.ai_speed = 0
            car.center_x = self.finish_line_x - 10
            race_time = self.game_time - self.race_start_time
            self.finish_times[car] = race_time
            self.finish_order.append(car)
            self.check_race_completion()

    def check_race_completion(self):
        all_finished = all(car.has_finished for car in self.car_list)
        if all_finished and not self.race_finished:
            self.race_finished = True
            self.show_final_results()

    def show_final_results(self):
        if self.result_shown:
            return
        self.result_shown = True
        winner = self.finish_order[0] if self.finish_order else None
        winner_name = winner.color_name if winner else ""
        is_victory = winner.is_player if winner else False
        if is_victory:
            message = f" ПОБЕДА! Уровень 2 пройден!\nВы финишировали ПЕРВЫМ!\nВремя: {self.finish_times[winner]:.2f} сек"
            success, db_message = db.update_player_level(self.player_data['id'], 3)
            if success:
                self.player_data['current_level'] = 3
        else:
            player_car = self.car_yellow
            player_time = self.finish_times.get(player_car, 0)

            if player_car in self.finish_order:
                player_position = self.finish_order.index(player_car) + 1
            else:
                player_position = "не финишировал"
            message = f'Вы проиграли уровень 2!\n'
            if isinstance(player_position, int):
                message += f"Вы финишировали {player_position}-м,\n"
            if player_time > 0:
                message += f"Ваше время: {player_time:.2f} сек"

        class SecondLevelGameOverView(arcade.View):
            def __init__(self, message, player_data, is_victory=False, winner_name=""):
                super().__init__()
                self.message = message
                self.player_data = player_data
                self.is_victory = is_victory
                self.winner_name = winner_name
                self.ui_manager = UIManager()
                self.setup_ui()

            def setup_ui(self):
                vbox = UIBoxLayout(space_between=20)
                title = "ВЫ ВЫИГРАЛИ!" if self.is_victory else "ПРОИГРЫШ"
                title_color = arcade.color.GOLD if self.is_victory else arcade.color.RED
                title_label = UILabel(
                    text=title,
                    font_size=36,
                    text_color=title_color,
                    width=500,
                    align="center",
                    bold=True
                )
                vbox.add(title_label)
                message_label = UILabel(
                    text=self.message,
                    font_size=20,
                    text_color=arcade.color.WHITE,
                    width=500,
                    align="center"
                )
                vbox.add(message_label)
                if not self.is_victory and self.winner_name:
                    winner_label = UILabel(
                        text=f"Выиграла машина: {self.winner_name}",
                        font_size=18,
                        text_color=arcade.color.YELLOW,
                        width=500,
                        align="center"
                    )
                    vbox.add(winner_label)
                player_label = UILabel(
                    text=f"Игрок: {self.player_data['username']} | Уровень: {self.player_data['current_level']}",
                    font_size=16,
                    text_color=arcade.color.LIGHT_GRAY,
                    width=500,
                    align="center"
                )
                vbox.add(player_label)
                button_container = UIBoxLayout(vertical=False, space_between=20)
                restart_button = UIFlatButton(
                    text="ЗАНОВО",
                    width=180,
                    height=50
                )
                restart_button.on_click = self.on_restart_clicked
                button_container.add(restart_button)
                menu_button = UIFlatButton(
                    text="В МЕНЮ",
                    width=180,
                    height=50
                )
                menu_button.on_click = self.on_menu_clicked
                button_container.add(menu_button)

                vbox.add(button_container)
                anchor_layout = UIAnchorLayout()
                anchor_layout.add(vbox, anchor_x="center", anchor_y="center")
                self.ui_manager.add(anchor_layout)

            def on_restart_clicked(self, event):
                game_view = SecondLevel(self.player_data)
                self.window.show_view(game_view)

            def on_menu_clicked(self, event):
                menu_view = MainMenuView()
                self.window.show_view(menu_view)

            def on_draw(self):
                self.clear()
                if self.is_victory:
                    arcade.set_background_color(arcade.color.DARK_GREEN)
                else:
                    arcade.set_background_color(arcade.color.DARK_RED)
                self.ui_manager.draw()

            def on_show_view(self):
                self.ui_manager.enable()

            def on_hide_view(self):
                self.ui_manager.disable()

            def on_mouse_motion(self, x, y, dx, dy):
                self.ui_manager.on_mouse_motion(x, y, dx, dy)

            def on_mouse_press(self, x, y, button, modifiers):
                self.ui_manager.on_mouse_press(x, y, button, modifiers)

            def on_mouse_release(self, x, y, button, modifiers):
                self.ui_manager.on_mouse_release(x, y, button, modifiers)
        game_over_view = SecondLevelGameOverView(message, self.player_data, is_victory, winner_name)
        self.window.show_view(game_over_view)

    def update_ai_cars(self, delta_time):
        if not self.game_started or self.race_finished:
            return

        for ai_car in self.ai_cars:
            if ai_car.has_finished:
                continue

            ai_car.center_x += ai_car.ai_speed

            if random.random() < 0.04:
                deviation = random.uniform(-15, 15)
                new_y = ai_car.center_y + deviation
                y_min, y_max = 100, 700
                if y_min <= new_y <= y_max:
                    ai_car.center_y = new_y
                else:
                    ai_car.center_y -= deviation * 0.5

            self.keep_car_in_bounds(ai_car, is_ai=True)

            if self.check_finish_line(ai_car):
                self.handle_finish(ai_car)

    def on_update(self, delta_time):
        self.game_time += delta_time

        if not self.game_started:
            self.timer -= delta_time
            if self.timer > 2.0:
                self.countdown_text = "3"
            elif self.timer > 1.0:
                self.countdown_text = "2"
            elif self.timer > 0:
                self.countdown_text = "1"
            else:
                self.countdown_text = ""
                self.game_started = True
                self.show_go_text = True
                self.go_text_timer = 1.0
                self.race_start_time = self.game_time

        if self.game_started and self.show_go_text:
            self.go_text_timer -= delta_time
            if self.go_text_timer <= 0:
                self.show_go_text = False

        if self.game_started and not self.race_finished:
            for physics_engine in self.physics_engines:
                physics_engine.update()

            self.check_all_car_collisions()
            self.update_ai_cars(delta_time)

            if not self.car_yellow.has_finished:
                self.keep_car_in_bounds(self.car_yellow, is_ai=False)

                if self.check_finish_line(self.car_yellow):
                    self.handle_finish(self.car_yellow)

            if not self.race_finished:
                all_finished = all(car.has_finished for car in self.car_list)
                if all_finished:
                    self.check_race_completion()

    def on_draw(self):
        self.clear()
        self.ground_list.draw()
        self.roks_list.draw()
        self.finish_list.draw()
        self.start_list.draw()
        self.collisions_list.draw()
        self.car_list.draw()

        arcade.draw_text(
            f"Игрок: {self.player_data['username']}",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 16
        )

        arcade.draw_text(
            f"Уровень: {self.player_data['current_level']}",
            10, SCREEN_HEIGHT - 60,
            arcade.color.WHITE, 16
        )

        if self.game_started and not self.race_finished:
            race_time = self.game_time - self.race_start_time
            arcade.draw_text(
                f"Время: {race_time:.1f} сек",
                SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30,
                arcade.color.YELLOW, 16
            )

        if self.game_started and not self.race_finished:
            arcade.draw_text(
                "Цель: первым пересечь финишную линию справа!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30,
                arcade.color.YELLOW, 22,
                anchor_x="center"
            )

            arcade.draw_text(
                "Избегайте камней!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60,
                arcade.color.ORANGE, 19,
                anchor_x="center"
            )

            if self.finish_order:
                arcade.draw_text(
                    f"Финишировало: {len(self.finish_order)}/3",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90,
                    arcade.color.CYAN, 18,
                    anchor_x="center"
                )

                if len(self.finish_order) > 0:
                    leader = self.finish_order[0]
                    if leader.is_player:
                        arcade.draw_text(
                            "ВЫ ЛИДИРУЕТЕ!",
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120,
                            arcade.color.GREEN, 20,
                            anchor_x="center", bold=True
                        )
                    else:
                        arcade.draw_text(
                            f"Лидирует: {leader.color_name}",
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120,
                            arcade.color.RED, 18,
                            anchor_x="center"
                        )

        if not self.game_started:
            arcade.draw_text(
                self.countdown_text,
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                arcade.color.RED, 100,
                anchor_x="center", anchor_y="center",
                bold=True
            )

            arcade.draw_text(
                "ПРИГОТОВЬТЕСЬ К СТАРТУ!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
                arcade.color.WHITE, 33,
                anchor_x="center", anchor_y="center"
            )
        elif self.show_go_text:
            arcade.draw_text(
                "ГОНКА!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                arcade.color.GREEN, 60,
                anchor_x="center", anchor_y="center",
                bold=True
            )

    def on_show_view(self):
        if not self.music_playing:
            sound = arcade.load_sound('Aphex_Twin_-_Ptolemy_80592407.mp3')
            sound.play(volume=0.07)
            self.music_playing = True

    def on_key_press(self, key, modifiers):
        if self.game_started and not self.car_yellow.has_finished:
            if key == arcade.key.RIGHT:
                self.car_yellow.change_x = CAR_SPEED_LEVEL_2
            elif key == arcade.key.LEFT:
                self.car_yellow.change_x = -CAR_SPEED_LEVEL_2
            elif key == arcade.key.UP:
                self.car_yellow.change_y = CAR_SPEED_LEVEL_2
            elif key == arcade.key.DOWN:
                self.car_yellow.change_y = -CAR_SPEED_LEVEL_2

        if key == arcade.key.R:
            self.setup()

        if key == arcade.key.ESCAPE:
            menu_view = MainMenuView()
            self.window.show_view(menu_view)

    def on_key_release(self, key, modifiers):
        if self.game_started and not self.car_yellow.has_finished:
            if key == arcade.key.RIGHT or key == arcade.key.LEFT:
                self.car_yellow.change_x = 0
            elif key == arcade.key.UP or key == arcade.key.DOWN:
                self.car_yellow.change_y = 0
def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu_view = MainMenuView()
    window.show_view(menu_view)
    arcade.run()
    db.close()


if __name__ == "__main__":
    main()