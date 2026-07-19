import arcade

TILE_SOURCE_SIZE = 16 
PLAYER_SOURCE_SIZE = 32 
ITEM_SOURCE_SIZE = 16

TILE_SPRITE_SCALING = 3.0 
PLAYER_SCALING = 1.3 

GRID_PIXEL_SIZE = TILE_SOURCE_SIZE * TILE_SPRITE_SCALING

WALL_THICKNESS = 2
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
        super().__init__()

        self.wall_list = None
        self.player_list = None
        self.pacgum_list = None
        self.super_pacgum_list = None

        self.score = 0
        self.lives = 3
        self.time_left = 60.0
        self.score_per_gum = 10
        self.score_per_super_gum = 50
        self.player_sprite = None

        self.physics_engine = None
        self.game_over = False

        self.fps_text = None
        self.game_over_text = None
        self.score_text = None
        self.lives_text = None
        self.time_text = None

        self.level = 1
        self.max_level = 2
        
        self.current_texture_index = 0
        self.time_since_last_frame = 0.0
        self.animation_speed = 0.05 
        self.current_direction = DIR_RIGHT

    def setup(self, maze_data, config):
        """Set up the game and initialize all core variables, including the procedural maze."""

        # Safely extract values from either a dictionary or a Pydantic object
        def get_conf(key, default):
            if hasattr(config, key): return getattr(config, key)
            if isinstance(config, dict) and key in config: return config[key]
            return default

        self.score = 0
        self.lives = get_conf("lives", 3)
        self.time_left = get_conf("time", 60.0)
        self.score_per_gum = get_conf("score_per_gum", 10)
        self.score_per_super_gum = get_conf("points_per_super_pacgum", 50)

        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.pacgum_list = arcade.SpriteList()
        self.super_pacgum_list = arcade.SpriteList()
        
        # Load player sprites
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

        # Load item sprites
        item_base_texture = arcade.load_texture("src/assets/PacManAssets-Items.png")
        
        # Standard PacGum (Row 2, Column 1)
        self.pacgum_texture = item_base_texture.crop(
            x=0, 
            y=ITEM_SOURCE_SIZE, 
            width=ITEM_SOURCE_SIZE, 
            height=ITEM_SOURCE_SIZE
        )

        # Super PacGum (Row 2, Column 2)
        self.super_pacgum_texture = item_base_texture.crop(
            x=ITEM_SOURCE_SIZE, 
            y=ITEM_SOURCE_SIZE, 
            width=ITEM_SOURCE_SIZE, 
            height=ITEM_SOURCE_SIZE
        )

        rows = len(maze_data)
        cols = len(maze_data[0]) if rows > 0 else 0
        
        for row_index, row in enumerate(maze_data):
            for col_index, cell_value in enumerate(row):
                
                cx = col_index * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
                cy = (rows - 1 - row_index) * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
                
                # Identify corners to place Super PacGums
                is_corner = (row_index == 0 and col_index == 0) or \
                            (row_index == 0 and col_index == cols - 1) or \
                            (row_index == rows - 1 and col_index == 0) or \
                            (row_index == rows - 1 and col_index == cols - 1)

                if is_corner:
                    super_gum = arcade.Sprite(self.super_pacgum_texture, scale=1.0)
                    super_gum.center_x = cx
                    super_gum.center_y = cy
                    self.super_pacgum_list.append(super_gum)
                else:
                    pacgum = arcade.Sprite(self.pacgum_texture, scale=1.0)
                    pacgum.center_x = cx
                    pacgum.center_y = cy
                    self.pacgum_list.append(pacgum)
                
                # Generate wall boundaries based on bitmask
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

        self.game_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        # UI Initialization
        self.fps_text = arcade.Text('FPS:', 10, self.window.height - 20, arcade.color.WHITE, 14)
        self.score_text = arcade.Text(f"Score: {self.score}", 20, 20, arcade.color.YELLOW, 18, bold=True)
        self.time_text = arcade.Text(f"Time: {int(self.time_left)}", self.window.width / 2, 20, arcade.color.WHITE, 18, bold=True, anchor_x="center")
        self.lives_text = arcade.Text(f"Lives: {self.lives}", self.window.width - 20, 20, arcade.color.RED, 18, bold=True, anchor_x="right")
        
        self.game_over_text = arcade.Text(
            'GAME OVER',
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE, 
            font_size=50,
            anchor_x='center',
            anchor_y='center'
        )

        self.player_sprite.center_x = GRID_PIXEL_SIZE * 1.5
        self.player_sprite.center_y = GRID_PIXEL_SIZE * 1.5
        self.player_list.append(self.player_sprite)

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite,
            self.wall_list,
        )

        self.window.background_color = arcade.color.BLACK
        self.game_over = False

    def on_draw(self):
        """Render the screen."""
        self.clear()

        with self.game_camera.activate():
            self.pacgum_list.draw()
            self.super_pacgum_list.draw()
            self.wall_list.draw()
            self.player_list.draw()

        with self.gui_camera.activate():
            output = f"FPS: {1/self.window.delta_time:.0f}" if self.window.delta_time > 0 else "FPS: 0"
            self.fps_text.text = output
            self.fps_text.draw()
            
            self.score_text.draw()
            self.time_text.draw()
            self.lives_text.draw()

            if self.game_over:
                self.game_over_text.draw()

    def on_key_press(self, key, modifiers):
        """Track intended movement direction based on key press."""
        if key == arcade.key.UP:
            self.player_sprite.change_y = MOVEMENT_SPEED
            self.current_direction = DIR_UP
        elif key == arcade.key.DOWN:
            self.player_sprite.change_y = -MOVEMENT_SPEED
            self.current_direction = DIR_DOWN
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -MOVEMENT_SPEED
            self.current_direction = DIR_LEFT
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = MOVEMENT_SPEED
            self.current_direction = DIR_RIGHT

    def on_key_release(self, key, modifiers):
        """Halt movement when key is released."""
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_sprite.change_y = 0

    def on_update(self, delta_time):
        """Movement, collision, and game logic loop."""
        if not self.game_over:
            
            self.time_left -= delta_time
            if self.time_left <= 0:
                self.time_left = 0
                self.game_over = True
            
            self.physics_engine.update()
            is_moving = self.player_sprite.change_x != 0 or self.player_sprite.change_y != 0

            # Handle collision with standard gums
            gums_hit = arcade.check_for_collision_with_list(self.player_sprite, self.pacgum_list)
            for gum in gums_hit:
                gum.remove_from_sprite_lists()
                self.score += self.score_per_gum

            # Handle collision with super gums
            super_gums_hit = arcade.check_for_collision_with_list(self.player_sprite, self.super_pacgum_list)
            for sgum in super_gums_hit:
                sgum.remove_from_sprite_lists()
                self.score += self.score_per_super_gum
                
            self.score_text.text = f"Score: {self.score}"
            self.time_text.text = f"Time: {int(self.time_left)}"
            self.lives_text.text = f"Lives: {self.lives}"

            # Update animation frame timing
            if is_moving:
                self.time_since_last_frame += delta_time
                if self.time_since_last_frame >= self.animation_speed:
                    self.time_since_last_frame = 0.0
                    self.current_texture_index += 1
                    
                    if self.current_texture_index >= len(self.moving_right):
                        self.current_texture_index = 0
            else:
                self.current_texture_index = 0

            # Orient the player sprite based on movement direction
            if self.current_direction == DIR_RIGHT:
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = 0
                
            elif self.current_direction == DIR_LEFT:
                self.player_sprite.texture = self.moving_left[self.current_texture_index]
                self.player_sprite.angle = 0
                
            elif self.current_direction == DIR_UP:
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = -90
                
            elif self.current_direction == DIR_DOWN:
                self.player_sprite.texture = self.moving_right[self.current_texture_index]
                self.player_sprite.angle = 90
        
        # Apply smooth camera scrolling
        target_position = self.player_sprite.position
        self.game_camera.position = arcade.math.lerp_2d(
            self.game_camera.position, 
            target_position, 
            CAMERA_PAN_SPEED
        )