import arcade

TILE_SOURCE_SIZE = 16 
PLAYER_SOURCE_SIZE = 32 
ITEM_SOURCE_SIZE = 16

TILE_SPRITE_SCALING = 2.5
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
    """Main game view handling logic, rendering, and physics."""

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
        
        self.current_direction = None
        self.next_direction = None

    def setup(self, maze_data, config):
        """Initialize the map, sprites, UI, and configuration variables."""
        self.maze_data = maze_data

        def get_conf(key, default):
            if hasattr(config, key): return getattr(config, key)
            if isinstance(config, dict) and key in config: return config[key]
            return default

        self.score = 0
        self.lives = get_conf("lives", 3)
        self.time_left = get_conf("time", 60.0)
        self.score_per_gum = get_conf("points_per_pacgum", 10)
        self.score_per_super_gum = get_conf("points_per_super_pacgum", 50)

        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.pacgum_list = arcade.SpriteList()
        self.super_pacgum_list = arcade.SpriteList()
        
        sprite_sheet = arcade.load_spritesheet("src/assets/PacManAssets-PacMan.png")
        all_textures = sprite_sheet.get_texture_grid(size=(32, 32), columns=4, count=11)

        self.moving_right = all_textures[0:4]
        self.moving_left = [tex.flip_left_right() for tex in self.moving_right]
        self.destroying_right = all_textures[4:8]
        self.destroying_right2 = all_textures[8:11]

        self.player_sprite = arcade.Sprite(scale=PLAYER_SCALING)
        self.player_sprite.texture = self.moving_right[0]
        
        self.current_texture_index = 0
        self.time_since_last_frame = 0.0
        
        self.current_direction = None
        self.next_direction = None

        item_base_texture = arcade.load_texture("src/assets/PacManAssets-Items.png")
        
        self.pacgum_texture = item_base_texture.crop(
            x=0, y=ITEM_SOURCE_SIZE, width=ITEM_SOURCE_SIZE, height=ITEM_SOURCE_SIZE
        )
        self.super_pacgum_texture = item_base_texture.crop(
            x=ITEM_SOURCE_SIZE, y=ITEM_SOURCE_SIZE, width=ITEM_SOURCE_SIZE, height=ITEM_SOURCE_SIZE
        )

        rows = len(maze_data)
        cols = len(maze_data[0]) if rows > 0 else 0
        
        for row_index, row in enumerate(maze_data):
            for col_index, cell_value in enumerate(row):
                
                cx = col_index * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
                cy = (rows - 1 - row_index) * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
                
                is_corner = (row_index == 0 and col_index == 0) or \
                            (row_index == 0 and col_index == cols - 1) or \
                            (row_index == rows - 1 and col_index == 0) or \
                            (row_index == rows - 1 and col_index == cols - 1)

                if maze_data[row_index][col_index] != 15:
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
                
                # Physical walls
                if cell_value & 1:
                    wall = arcade.SpriteSolidColor(width=int(GRID_PIXEL_SIZE), height=WALL_THICKNESS, color=WALL_COLOR)
                    wall.center_x, wall.center_y = cx, cy + (GRID_PIXEL_SIZE / 2) - (WALL_THICKNESS / 2)
                    self.wall_list.append(wall)
                
                if cell_value & 2:
                    wall = arcade.SpriteSolidColor(width=WALL_THICKNESS, height=int(GRID_PIXEL_SIZE), color=WALL_COLOR)
                    wall.center_x, wall.center_y = cx + (GRID_PIXEL_SIZE / 2) - (WALL_THICKNESS / 2), cy
                    self.wall_list.append(wall)
                
                if cell_value & 4:
                    wall = arcade.SpriteSolidColor(width=int(GRID_PIXEL_SIZE), height=WALL_THICKNESS, color=WALL_COLOR)
                    wall.center_x, wall.center_y = cx, cy - (GRID_PIXEL_SIZE / 2) + (WALL_THICKNESS / 2)
                    self.wall_list.append(wall)
                
                if cell_value & 8:
                    wall = arcade.SpriteSolidColor(width=WALL_THICKNESS, height=int(GRID_PIXEL_SIZE), color=WALL_COLOR)
                    wall.center_x, wall.center_y = cx - (GRID_PIXEL_SIZE / 2) + (WALL_THICKNESS / 2), cy
                    self.wall_list.append(wall)

        self.game_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        self.level_text = arcade.Text(f"Level: {self.level}", 10, self.window.height - 30, arcade.color.YELLOW, 18)
        self.time_text = arcade.Text(f"Time: {int(self.time_left)}", 10, self.window.height - 60, arcade.color.YELLOW, 18)
        self.score_text = arcade.Text(f"Score: {self.score}", 20, 20, arcade.color.YELLOW, 18)
        self.fps_text = arcade.Text('FPS:', self.window.width - 20, self.window.height - 20, arcade.color.WHITE, 14, anchor_x="right")
        self.lives_text = arcade.Text(f"Lives: {self.lives}", self.window.width - 20, 20, arcade.color.RED, 18, anchor_x="right")
        
        self.game_over_text = arcade.Text(
            'GAME OVER',
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE, 
            font_size=50,
            anchor_x='center',
            anchor_y='center'
        )

        center_col = cols // 2
        center_row = rows // 2
        
        if not rows % 2:
            self.player_sprite.center_x = center_col * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2) - GRID_PIXEL_SIZE
        else:
            self.player_sprite.center_x = center_col * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
        self.player_sprite.center_y = center_row * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
        self.player_list.append(self.player_sprite)

        self.game_camera.position = self.player_sprite.position

        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        
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
            self.level_text.draw()
            # self.level

            if self.game_over:
                self.game_over_text.draw()

    def try_turning(self):
        """Authentic Pac-Man infinite queue & grid-snapping logic."""
        if self.next_direction is None or self.next_direction == self.current_direction:
            return

        opposites = {DIR_UP: DIR_DOWN, DIR_DOWN: DIR_UP, DIR_LEFT: DIR_RIGHT, DIR_RIGHT: DIR_LEFT}
        if self.current_direction is not None and self.next_direction == opposites.get(self.current_direction):
            self.current_direction = self.next_direction
            self.next_direction = None
            return

        col = int(round((self.player_sprite.center_x - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE))
        row_from_bottom = int(round((self.player_sprite.center_y - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE))
        
        rows = len(self.maze_data)
        cols = len(self.maze_data[0]) if rows > 0 else 0
        maze_row = (rows - 1) - row_from_bottom

        if col < 0 or col >= cols or maze_row < 0 or maze_row >= rows:
            return

        cell_value = self.maze_data[maze_row][col]
        cx = col * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
        cy = row_from_bottom * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)

        blocked = False
        if self.next_direction == DIR_UP and (cell_value & 1): blocked = True
        if self.next_direction == DIR_RIGHT and (cell_value & 2): blocked = True
        if self.next_direction == DIR_DOWN and (cell_value & 4): blocked = True
        if self.next_direction == DIR_LEFT and (cell_value & 8): blocked = True

        if not blocked:
            can_turn = False
            
            if self.current_direction is None:
                can_turn = True
            elif self.current_direction == DIR_RIGHT and self.player_sprite.center_x >= cx:
                can_turn = True
            elif self.current_direction == DIR_LEFT and self.player_sprite.center_x <= cx:
                can_turn = True
            elif self.current_direction == DIR_UP and self.player_sprite.center_y >= cy:
                can_turn = True
            elif self.current_direction == DIR_DOWN and self.player_sprite.center_y <= cy:
                can_turn = True
            elif self.player_sprite.change_x == 0 and self.player_sprite.change_y == 0:
                can_turn = True

            if can_turn:
                if self.next_direction in [DIR_UP, DIR_DOWN]:
                    self.player_sprite.center_x = cx  
                elif self.next_direction in [DIR_LEFT, DIR_RIGHT]:
                    self.player_sprite.center_y = cy  
                    
                self.current_direction = self.next_direction
                self.next_direction = None

    def on_key_press(self, key, modifiers):
        """Queue the intended direction indefinitely until it can be executed."""
        if key == arcade.key.UP:
            self.next_direction = DIR_UP
        elif key == arcade.key.DOWN:
            self.next_direction = DIR_DOWN
        elif key == arcade.key.LEFT:
            self.next_direction = DIR_LEFT
        elif key == arcade.key.RIGHT:
            self.next_direction = DIR_RIGHT

    def on_update(self, delta_time):
        """Movement, collision, and game logic loop."""
        if self.game_over:
            return
            
        self.time_left -= delta_time
        if self.time_left <= 0:
            self.time_left = 0
            self.game_over = True
        
        self.try_turning()

        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        
        if self.current_direction == DIR_UP:
            self.player_sprite.change_y = MOVEMENT_SPEED
        elif self.current_direction == DIR_DOWN:
            self.player_sprite.change_y = -MOVEMENT_SPEED
        elif self.current_direction == DIR_LEFT:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif self.current_direction == DIR_RIGHT:
            self.player_sprite.change_x = MOVEMENT_SPEED

        # Physics engine handles wall collisions
        self.physics_engine.update()
        
        is_moving = self.player_sprite.change_x != 0 or self.player_sprite.change_y != 0

        gums_hit = arcade.check_for_collision_with_list(self.player_sprite, self.pacgum_list)
        for gum in gums_hit:
            gum.remove_from_sprite_lists()
            self.score += self.score_per_gum

        super_gums_hit = arcade.check_for_collision_with_list(self.player_sprite, self.super_pacgum_list)
        for sgum in super_gums_hit:
            sgum.remove_from_sprite_lists()
            self.score += self.score_per_super_gum
            
        self.score_text.text = f"Score: {self.score}"
        self.time_text.text = f"Time: {int(self.time_left)}"
        self.lives_text.text = f"Lives: {self.lives}"

        if is_moving:
            self.time_since_last_frame += delta_time
            if self.time_since_last_frame >= self.animation_speed:
                self.time_since_last_frame = 0.0
                self.current_texture_index += 1
                
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
            self.player_sprite.angle = -90
        elif self.current_direction == DIR_DOWN:
            self.player_sprite.texture = self.moving_right[self.current_texture_index]
            self.player_sprite.angle = 90
    
        target_position = self.player_sprite.position
        self.game_camera.position = arcade.math.lerp_2d(
            self.game_camera.position, 
            target_position, 
            CAMERA_PAN_SPEED
        )