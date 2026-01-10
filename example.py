import arcade

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Гонки - Карта"
TILE_SCALING = 0.5
CAR_SPEED = 5


class GameWindow(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.ground_list = None
        self.trassa_list = None
        self.decoration_list = None
        self.lines_list = None
        self.collision_list = None
        self.car_list = arcade.SpriteList()
        self.car_yellow = None
        self.physics_engine = None
        self.timer = 3.0
        self.game_started = False
        self.countdown_text = ""
        self.show_go_text = False
        self.go_text_timer = 0

    def setup(self):
        # карта
        tile_map = arcade.load_tilemap("carr2.tmx", scaling=TILE_SCALING)
        self.ground_list = tile_map.sprite_lists["ground"]
        self.trassa_list = tile_map.sprite_lists["trassa"]
        self.decoration_list = tile_map.sprite_lists["sdecoration"]
        self.lines_list = tile_map.sprite_lists["finish_start_lines"]
        self.collision_list = tile_map.sprite_lists["collisions"]
        self.car_yellow = arcade.Sprite("car_yellow (1).png", 0.2)
        self.car_yellow.center_x = 500
        self.car_yellow.center_y = 700
        self.car_yellow.change_x = 0
        self.car_yellow.change_y = 0
        self.car_list.append(self.car_yellow)

        #красная машина (не управляемая)
        car_red = arcade.Sprite("car_red.png", 0.08)
        car_red.center_x = 400
        car_red.center_y = 700
        self.car_list.append(car_red)

        #синяя машина (не управляемая)
        car_blue = arcade.Sprite("car_blue.png", 0.08)
        car_blue.center_x = 600
        car_blue.center_y = 700
        self.car_list.append(car_blue)
        self.physics_engine = arcade.PhysicsEngineSimple(self.car_yellow, self.collision_list)
        self.timer = 3.0
        self.game_started = False
        self.countdown_text = "3"
        self.show_go_text = False
        self.go_text_timer = 0

    def on_draw(self):
        self.clear()
        self.ground_list.draw()
        self.trassa_list.draw()
        self.decoration_list.draw()
        self.lines_list.draw()
        self.car_list.draw()

        if not self.game_started:
            arcade.draw_text(
                self.countdown_text,
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                arcade.color.RED, 100,
                align="center", anchor_x="center", anchor_y="center",
                bold=True
            )

            arcade.draw_text(
                "ПРИГОТОВЬТЕСЬ К СТАРТУ!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
                arcade.color.WHITE, 30,
                align="center", anchor_x="center", anchor_y="center"
            )
        elif self.show_go_text:
            arcade.draw_text(
                "ГОНКА!",
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                arcade.color.GREEN, 60,
                align="center", anchor_x="center", anchor_y="center",
                bold=True
            )

    def on_update(self, delta_time):
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
                self.go_text_timer = 1
        if self.game_started and self.show_go_text:
            self.go_text_timer -= delta_time
            if self.go_text_timer <= 0:
                self.show_go_text = False
        if self.game_started and self.physics_engine:
            self.physics_engine.update()
        if self.car_yellow:
            if self.car_yellow.center_x < 0:
                self.car_yellow.center_x = 0
            elif self.car_yellow.center_x > SCREEN_WIDTH:
                self.car_yellow.center_x = SCREEN_WIDTH
            if self.car_yellow.center_y < 0:
                self.car_yellow.center_y = 0
            elif self.car_yellow.center_y > SCREEN_HEIGHT:
                self.car_yellow.center_y = SCREEN_HEIGHT

    def on_key_press(self, key, modifiers):
        if self.game_started and self.car_yellow:
            if key == arcade.key.UP:
                self.car_yellow.change_y = CAR_SPEED
            elif key == arcade.key.DOWN:
                self.car_yellow.change_y = -CAR_SPEED
            elif key == arcade.key.LEFT:
                self.car_yellow.change_x = -CAR_SPEED
            elif key == arcade.key.RIGHT:
                self.car_yellow.change_x = CAR_SPEED
        if key == arcade.key.R:
            self.setup()

    def on_key_release(self, key, modifiers):
        if self.game_started and self.car_yellow:
            if key == arcade.key.UP or key == arcade.key.DOWN:
                self.car_yellow.change_y = 0
            elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
                self.car_yellow.change_x = 0


def main():
    window = GameWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()