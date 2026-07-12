import sys
import arcade

from pydantic import ValidationError

from mazegenerator import MazeGenerator
from src.parser import ConfigParser, PacmanConfig
from src.logger import log_message, LogType


TILE_SPRITE_SCALING = 0.5
PLAYER_SCALING = 1.5

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Not Pacman"
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SPRITE_SCALING
CAMERA_PAN_SPEED = 0.15

# Physics
MOVEMENT_SPEED = 5

# Direction Constants for easy tracking
DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3


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
        self.current_texture_index = 0
        self.time_since_last_frame = 0.0
        self.animation_speed = 0.05  # Seconds per frame (lower is faster)
        self.current_direction = DIR_RIGHT # Default starting direction

    def setup(self):
        """Set up the game and initialize all core variables."""

        # Initialize the sprite list for the player
        self.player_list = arcade.SpriteList()
        
        # Load the raw sprite sheet
        sprite_sheet = arcade.load_spritesheet("src/assets/PacManAssets-PacMan.png")

        # Extract the grid of textures from the sheet
        all_textures = sprite_sheet.get_texture_grid(
            size=(32, 32),
            columns=4,
            count=11
        )

        # Base textures (Facing Right)
        self.moving_right = all_textures[0:4]
        
        # Generated textures (Facing Left - mirrored horizontally)
        self.moving_left = [tex.flip_left_right() for tex in self.moving_right]

        # Other animations (Death)
        self.destroying_right = all_textures[4:8]
        self.destroying_right2 = all_textures[8:11]

        # Instantiate the player sprite
        self.player_sprite = arcade.Sprite(scale=PLAYER_SCALING)
        self.player_sprite.texture = self.moving_right[0]
        
        # Reset animation state for safety on restart
        self.current_texture_index = 0
        self.time_since_last_frame = 0.0
        self.current_direction = DIR_RIGHT

        # Initialize cameras
        self.game_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        # Setup GUI text elements (FPS and Game Over screens)
        self.fps_text = arcade.Text('FPS:', 10, 10, arcade.color.BLACK, 14)
        self.game_over_text = arcade.Text(
            'GAME OVER',
            self.window.center_x,
            self.window.center_y,
            arcade.color.BLACK, 30,
            anchor_x='center',
            anchor_y='center'
        )

        # Set the initial spawning coordinates for the player
        self.player_sprite.center_x = 128
        self.player_sprite.center_y = 64
        
        # Add the configured player to the sprite list
        self.player_list.append(self.player_sprite)

        # Load the initial level (Map, Walls, Physics Engine setup)
        self.load_level(self.level)

        # Reset game state flags
        self.game_over = False

    def load_level(self, level):
        """Load a specific level map and configure boundaries."""

        # Read in the tiled map
        self.tile_map = arcade.load_tilemap(
            f":resources:tiled_maps/level_{level}.json", scaling=TILE_SPRITE_SCALING
        )

        # Calculate the right edge of the map in pixels
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        # Initialize the physics engine for collisions
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite,
            self.tile_map.sprite_lists["Platforms"],
        )

        # Set the background color
        if self.tile_map.background_color:
            self.window.background_color = self.tile_map.background_color

        # Setup Camera boundaries
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
        """Render the screen."""
        self.clear()

        # Draw game elements (Follows the player)
        with self.game_camera.activate():
            self.tile_map.sprite_lists["Platforms"].draw()
            self.player_list.draw()

        # Draw GUI elements (Fixed on screen)
        with self.gui_camera.activate():
            output = f"FPS: {1/self.window.delta_time:.0f}" if self.window.delta_time > 0 else "FPS: 0"
            arcade.Text(
                output, 10, 20, arcade.color.BLACK, 14
            ).draw()

            if self.game_over:
                self.game_over_text.position = self.window.center
                self.game_over_text.draw()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        
        # Track both movement and the direction facing for the animation
        if key == arcade.key.UP:
            self.player_sprite.change_y = MOVEMENT_SPEED
            self.current_direction = DIR_DOWN
        elif key == arcade.key.DOWN:
            self.player_sprite.change_y = -MOVEMENT_SPEED
            self.current_direction = DIR_UP
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -MOVEMENT_SPEED
            self.current_direction = DIR_LEFT
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = MOVEMENT_SPEED
            self.current_direction = DIR_RIGHT


    def on_key_release(self, key, modifiers):
        """Called whenever a key is released."""
        # Will be deleted when we will have the maze
        # Pacman cannot stay in place except if he's hiting a wall
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_sprite.change_y = 0


    def on_update(self, delta_time):
        """Movement and game logic, including animation loops."""

        # Level transition logic
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

        if not self.game_over:
            # Update position based on velocity and handle collisions
            self.physics_engine.update()
            
            # Check if player is moving
            is_moving = self.player_sprite.change_x != 0 or self.player_sprite.change_y != 0

            if is_moving:
                # Accumulate time
                self.time_since_last_frame += delta_time
                
                # Move to next frame if enough time has passed
                if self.time_since_last_frame >= self.animation_speed:
                    self.time_since_last_frame = 0.0
                    self.current_texture_index += 1
                    
                    # Loop back to 0 if we exceed the number of frames
                    if self.current_texture_index >= len(self.moving_right):
                        self.current_texture_index = 0
            else:
                # Set to a static frame when not moving (0 = closed mouth, 1 = slightly open)
                self.current_texture_index = 0

            # Apply Texture and Rotation based on direction
            if self.current_direction == DIR_RIGHT:
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = 0
                
            elif self.current_direction == DIR_LEFT:
                self.player_sprite.texture = self.moving_left[self.current_texture_index]
                self.player_sprite.angle = 0
                
            elif self.current_direction == DIR_UP:
                # Use right-facing texture, but rotate the sprite 90 degrees UP
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = 90
                
            elif self.current_direction == DIR_DOWN:
                # Use right-facing texture, but rotate the sprite 90 degrees DOWN
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = -90


def main():
    if len(sys.argv) != 2:
        log_message("You must provide a valid config json file path", LogType.ERROR)
        sys.exit(1)
        
    parser = ConfigParser(sys.argv[1])
    try:
        log_message("Parsing config file...", LogType.INFO)
        config = parser.parse(PacmanConfig)
        log_message("Config file successfully parsed !", LogType.SUCCESS)
    except FileNotFoundError:
        log_message(f"Error : File '{parser.filepath}' not found.", LogType.ERROR)
    except ValidationError as e:
        if e.errors():
            log_message(repr(e.errors()[0]['msg']), LogType.ERROR)
        else:
            log_message("Validation Error occurred.", LogType.ERROR)
    except Exception as e:
        log_message(f"Error when parsing : {e}", LogType.ERROR)
    
    # Generate Maze
    maze = MazeGenerator((15, 15))
    maze.generate()
    
    # Setup Window and Game
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    game = GameView()
    game.setup()

    window.show_view(game)
    window.run()


if __name__ == "__main__":
    main()