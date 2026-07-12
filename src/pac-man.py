import sys
import arcade

from pydantic import ValidationError

from mazegenerator import MazeGenerator
from src.parser import ConfigParser, PacmanConfig
from src.logger import log_message, LogType


TILE_SPRITE_SCALING = 0.5
PLAYER_SCALING = 0.6

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Not Pacman"
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SPRITE_SCALING
CAMERA_PAN_SPEED = 0.15

# Physics
MOVEMENT_SPEED = 5
JUMP_SPEED = 23
GRAVITY = 1.1


class GameView(arcade.View):
    """Main application class."""

    def __init__(self):
        """
        Initializer
        """
        super().__init__()

        # Tilemap Object
        self.tile_map = None

        # Sprite lists
        self.player_list = None

        # Set up the player
        self.score = 0
        self.player_sprite = None

        self.physics_engine = None
        self.end_of_map = 0
        self.game_over = False


        self.fps_text = None
        self.game_over_text = None

        self.level = 1
        self.max_level = 2

    def setup(self):
        """Set up the game and initialize the variables."""

        # Sprite lists
        self.player_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = arcade.Sprite(
            "src/assets/PacManAssets-PacMan.png",
            scale=PLAYER_SCALING,
        )

        self.game_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        self.fps_text = arcade.Text('FPS:', 10, 10, arcade.color.BLACK, 14)
        self.game_over_text = arcade.Text(
            'GAME OVER',
            self.window.center_x,
            self.window.center_y,
            arcade.color.BLACK, 30,
            anchor_x='center',
            anchor_y='center'
        )

        # Starting position of the player
        self.player_sprite.center_x = 128
        self.player_sprite.center_y = 64
        self.player_list.append(self.player_sprite)

        self.load_level(self.level)

        self.game_over = False

    def load_level(self, level):
        # layer_options = {"Platforms": {"use_spatial_hash": True}}

        # Read in the tiled map
        self.tile_map = arcade.load_tilemap(
            f":resources:tiled_maps/level_{level}.json", scaling=TILE_SPRITE_SCALING
        )

        # --- Walls ---

        # Calculate the right edge of the my_map in pixels
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            self.tile_map.sprite_lists["Platforms"],
            gravity_constant=GRAVITY,
        )

        # --- Other stuff
        # Set the background color
        if self.tile_map.background_color:
            self.window.background_color = self.tile_map.background_color

        max_x = GRID_PIXEL_SIZE * self.tile_map.width
        max_y = GRID_PIXEL_SIZE * self.tile_map.height
        limit_y = max_y > self.window.height
        self.camera_bounds = arcade.LRBT(
            self.window.width / 2.0,
            max_x - self.window.width / 2.0,
            self.window.height / 2.0,
            max_y - (self.window.height / 2.0 if limit_y else 0.0)
        )


    def on_draw(self):
        """
        Render the screen.
        """
        # This command has to happen before we start drawing
        self.clear()

        with self.game_camera.activate():
            # Draw all the sprites.
            self.tile_map.sprite_lists["Platforms"].draw()
            self.player_list.draw()

        with self.gui_camera.activate():
            # Put the text on the screen.
            # Adjust the text position based on the view port so that we don't
            # scroll the text too.
            output = f"FPS: {1/self.window.delta_time:.0f}"
            arcade.draw_text(
                output, 10, 20, arcade.color.BLACK, 14
            )

            if self.game_over:
                self.game_over_text.position = self.window.center
                self.game_over_text.draw()

    def on_key_press(self, key, modifiers):
        """
        Called whenever the mouse moves.
        """
        if key == arcade.key.UP:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = JUMP_SPEED
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """
        Called when the user presses a mouse button.
        """
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0

    def on_update(self, delta_time):
        """Movement and game logic"""

        if self.player_sprite.right >= self.end_of_map:
            if self.level < self.max_level:
                self.level += 1
                self.load_level(self.level)
                self.player_sprite.center_x = 128
                self.player_sprite.center_y = 64
                self.player_sprite.change_x = 0
                self.player_sprite.change_y = 0
            else:
                self.game_over = True

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        if not self.game_over:
            self.physics_engine.update()

    
    def on_resize(self, width, height):
        """ This method is automatically called when the window is resized. """

        # Call the parent. Failing to do this will mess up the coordinates,
        # and default to 0,0 at the center and the edges being -1 to 1.
        super().on_resize(width, height)

        print(f"Window resized to: {width}, {height}")


def main():
    if len(sys.argv) != 2:
        print("You must provide a valid config json file path", file=sys.stderr)
        sys.exit(1)
    parser = ConfigParser(sys.argv[1])
    try:
        log_message("Parsing config file...", LogType.INFO)
        config = parser.parse(PacmanConfig)
        log_message("Config file successfully parsed !", LogType.SUCCESS)
    except FileNotFoundError:
        log_message(f"Error : File '{parser.filepath}' not found.", LogType.ERROR)
    except ValidationError as e:
        log_message(repr(e.errors()[0]['msg']), LogType.ERROR)
    except Exception as e:
        log_message(f"Error when parsing : {e}", LogType.ERROR)
    

    maze = MazeGenerator((15, 15))
    maze.generate()
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    game = GameView()
    game.setup()

    window.show_view(game)
    window.run()


if __name__ == "__main__":
    main()