import arcade


TILE_SOURCE_SIZE = 16 
PLAYER_SOURCE_SIZE = 32 

TILE_SPRITE_SCALING = 3.0 
PLAYER_SCALING = 1.3 

GRID_PIXEL_SIZE = TILE_SOURCE_SIZE * TILE_SPRITE_SCALING

WALL_THICKNESS = 4
WALL_COLOR = arcade.color.BLUE_SAPPHIRE

CAMERA_PAN_SPEED = 0.15
MOVEMENT_SPEED = 5

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

        self.wall_list = None
        self.player_list = None

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
        self.animation_speed = 0.05         # Seconds per frame (lower is faster)
        self.current_direction = DIR_RIGHT

    def setup(self, maze_data):
        """Set up the game and initialize all core variables, including the procedural maze."""

        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        
        
        sprite_sheet = arcade.load_spritesheet("src/assets/PacManAssets-PacMan.png")

        all_textures = sprite_sheet.get_texture_grid(
            size=(32, 32),
            columns=4,
            count=11
        )

        self.moving_right = all_textures[0:4]
        
        self.moving_left = [tex.flip_left_right() for tex in self.moving_right]

        self.destroying_right = all_textures[4:8]
        self.destroying_right2 = all_textures[8:11]

        self.player_sprite = arcade.Sprite(scale=PLAYER_SCALING)
        self.player_sprite.texture = self.moving_right[0]
        
        self.current_texture_index = 0
        self.time_since_last_frame = 0.0
        self.current_direction = DIR_RIGHT

        
        rows = len(maze_data)
        cols = len(maze_data[0]) if rows > 0 else 0
        
        self.end_of_map = cols * GRID_PIXEL_SIZE

        for row_index, row in enumerate(maze_data):
            for col_index, cell_value in enumerate(row):
                
                if cell_value == 0:
                    continue
                
                # Calculate the exact center of the current cell
                cx = col_index * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
                cy = (rows - 1 - row_index) * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
                
                # North Wall (Bit 0)
                if cell_value & 1:
                    wall = arcade.SpriteSolidColor(
                        width=int(GRID_PIXEL_SIZE), 
                        height=WALL_THICKNESS, 
                        color=WALL_COLOR
                    )
                    wall.center_x = cx
                    wall.center_y = cy + (GRID_PIXEL_SIZE / 2) - (WALL_THICKNESS / 2)
                    self.wall_list.append(wall)
                
                # East Wall (Bit 1)
                if cell_value & 2:
                    wall = arcade.SpriteSolidColor(
                        width=WALL_THICKNESS, 
                        height=int(GRID_PIXEL_SIZE), 
                        color=WALL_COLOR
                    )
                    wall.center_x = cx + (GRID_PIXEL_SIZE / 2) - (WALL_THICKNESS / 2)
                    wall.center_y = cy
                    self.wall_list.append(wall)
                
                # South Wall (Bit 2)
                if cell_value & 4:
                    wall = arcade.SpriteSolidColor(
                        width=int(GRID_PIXEL_SIZE), 
                        height=WALL_THICKNESS, 
                        color=WALL_COLOR
                    )
                    wall.center_x = cx
                    wall.center_y = cy - (GRID_PIXEL_SIZE / 2) + (WALL_THICKNESS / 2)
                    self.wall_list.append(wall)
                
                # West Wall (Bit 3)
                if cell_value & 8:
                    wall = arcade.SpriteSolidColor(
                        width=WALL_THICKNESS, 
                        height=int(GRID_PIXEL_SIZE), 
                        color=WALL_COLOR
                    )
                    wall.center_x = cx - (GRID_PIXEL_SIZE / 2) + (WALL_THICKNESS / 2)
                    wall.center_y = cy
                    self.wall_list.append(wall)

        # Initialize cameras
        self.game_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        # Setup GUI text elements (White text on black background)
        self.fps_text = arcade.Text('FPS:', 10, 10, arcade.color.WHITE, 14)
        
        # Position is set exactly once here, preventing the crash
        self.game_over_text = arcade.Text(
            'GAME OVER',
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE, 
            font_size=50,
            anchor_x='center',
            anchor_y='center'
        )

        # Set the initial spawning coordinates for the player (bottom-left corner safely inside grid)
        self.player_sprite.center_x = GRID_PIXEL_SIZE * 1.5
        self.player_sprite.center_y = GRID_PIXEL_SIZE * 1.5
        self.player_list.append(self.player_sprite)

        # Initialize the physics engine with the procedural walls
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite,
            self.wall_list,
        )

        # Setup Camera boundaries to match the dynamic maze size
        max_x = GRID_PIXEL_SIZE * cols
        max_y = GRID_PIXEL_SIZE * rows
        limit_y = max_y > self.window.height
        
        self.camera_bounds = arcade.LRBT(
            self.window.width / 2.0,
            max_x - self.window.width / 2.0,
            self.window.height / 2.0,
            max_y - (self.window.height / 2.0 if limit_y else 0.0)
        )

        self.window.background_color = arcade.color.BLACK
        self.game_over = False

    def on_draw(self):
        """Render the screen."""
        self.clear()

        with self.game_camera.activate():
            self.wall_list.draw()
            self.player_list.draw()

        with self.gui_camera.activate():
            output = f"FPS: {1/self.window.delta_time:.0f}" if self.window.delta_time > 0 else "FPS: 0"
            arcade.Text(
                output, 10, 20, arcade.color.WHITE, 14
            ).draw()

            if self.game_over:
                self.game_over_text.draw()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        
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
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_sprite.change_y = 0

    def on_update(self, delta_time):
        """Movement and game logic, including animation loops."""

        # Trigger Game Over if player reaches the right edge
        if self.player_sprite.right >= self.end_of_map:
            self.game_over = True

        if not self.game_over:
            # Update position based on velocity and handle collisions
            self.physics_engine.update()
            
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
                self.current_texture_index = 0

            if self.current_direction == DIR_RIGHT:
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = 0
                
            elif self.current_direction == DIR_LEFT:
                self.player_sprite.texture = self.moving_left[self.current_texture_index]
                self.player_sprite.angle = 0
                
            elif self.current_direction == DIR_UP:
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = 90
                
            elif self.current_direction == DIR_DOWN:
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = -90