import arcade
import math
from collections import deque
from src.maze_sprites import create_maze_sprites

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
GHOST_SPEED = 2.0

DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3


def bfs_shortest_path_direction(
    start_col, start_row, target_col, target_row, maze_data
):
    """
    Breadth-First Search (BFS) algorithm to find the shortest path in a grid.
    Return the first direction the ghost should take to reach the target.
    """

    if (start_col, start_row) == (target_col, target_row):
        return None

    total_rows = len(maze_data)
    total_cols = len(maze_data[0]) if total_rows > 0 else 0

    # tuple(current_column, current_row, list_of_directions_taken_to_get_here)
    search_queue = deque()
    search_queue.append((start_col, start_row, []))

    visited_cells = set()
    visited_cells.add((start_col, start_row))

    while search_queue:
        current_col, current_row, path_taken = search_queue.popleft()

        if current_col == target_col and current_row == target_row:
            return path_taken[0] if path_taken else None

        maze_array_row = (total_rows - 1) - current_row
        if (
            maze_array_row < 0
            or maze_array_row >= total_rows
            or current_col < 0
            or current_col >= total_cols
        ):
            continue

        cell_wall_data = maze_data[maze_array_row][current_col]

        # Check UP
        if not (cell_wall_data & 1):
            next_col = current_col
            next_row = current_row + 1
            if (next_col, next_row) not in visited_cells:
                visited_cells.add((next_col, next_row))
                search_queue.append((next_col, next_row, path_taken + [DIR_UP]))

        # Check RIGHT
        if not (cell_wall_data & 2):
            next_col = current_col + 1
            next_row = current_row
            if (next_col, next_row) not in visited_cells:
                visited_cells.add((next_col, next_row))
                search_queue.append((next_col, next_row, path_taken + [DIR_RIGHT]))

        # Check DOWN
        if not (cell_wall_data & 4):
            next_col = current_col
            next_row = current_row - 1
            if (next_col, next_row) not in visited_cells:
                visited_cells.add((next_col, next_row))
                search_queue.append((next_col, next_row, path_taken + [DIR_DOWN]))

        # Check LEFT
        if not (cell_wall_data & 8):
            next_col = current_col - 1
            next_row = current_row
            if (next_col, next_row) not in visited_cells:
                visited_cells.add((next_col, next_row))
                search_queue.append((next_col, next_row, path_taken + [DIR_LEFT]))

    return None


class GridSprite(arcade.Sprite):
    """
    Grid class to manage the centering of entities and collisions.
    Ensures that sprites (Pac-Man and Ghosts) move strictly along the grid lines.
    """

    def __init__(self, scale=1.0):
        super().__init__(scale=scale)
        self.current_direction = None
        self.next_direction = None

    def try_turning(self, maze_data):
        if self.next_direction is None or self.next_direction == self.current_direction:
            return

        opposite_directions = {
            DIR_UP: DIR_DOWN,
            DIR_DOWN: DIR_UP,
            DIR_LEFT: DIR_RIGHT,
            DIR_RIGHT: DIR_LEFT,
        }
        
        if self.current_direction is not None and self.next_direction == opposite_directions.get(self.current_direction):
            self.current_direction = self.next_direction
            self.next_direction = None
            return

        # Calculate which grid cell the sprite is currently inside based on its pixel center
        current_col = int(round((self.center_x - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE))
        grid_row_bottom_up = int(round((self.center_y - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE))

        # Convert the bottom-up row index (used by Arcade coordinates) to top-down row index (used by maze array)
        total_rows = len(maze_data)
        total_cols = len(maze_data[0]) if total_rows > 0 else 0
        maze_array_row = (total_rows - 1) - grid_row_bottom_up

        cell_wall_data = maze_data[maze_array_row][current_col]
        
        # Calculate the exact pixel coordinates of the center of this grid cell
        cell_center_x = current_col * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
        cell_center_y = grid_row_bottom_up * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)

        is_path_blocked = False
        if self.next_direction == DIR_UP and (cell_wall_data & 1):
            is_path_blocked = True
        if self.next_direction == DIR_RIGHT and (cell_wall_data & 2):
            is_path_blocked = True
        if self.next_direction == DIR_DOWN and (cell_wall_data & 4):
            is_path_blocked = True
        if self.next_direction == DIR_LEFT and (cell_wall_data & 8):
            is_path_blocked = True

        if not is_path_blocked:
            can_execute_turn = False
            
            if self.current_direction is None:
                can_execute_turn = True
                
            elif self.current_direction == DIR_RIGHT and self.center_x >= cell_center_x:
                can_execute_turn = True
                
            elif self.current_direction == DIR_LEFT and self.center_x <= cell_center_x:
                can_execute_turn = True
                
            elif self.current_direction == DIR_UP and self.center_y >= cell_center_y:
                can_execute_turn = True
                
            elif self.current_direction == DIR_DOWN and self.center_y <= cell_center_y:
                can_execute_turn = True
                
            if can_execute_turn:
                # Snapping
                if self.next_direction in [DIR_UP, DIR_DOWN]:
                    self.center_x = cell_center_x  
                elif self.next_direction in [DIR_LEFT, DIR_RIGHT]:
                    self.center_y = cell_center_y

                self.current_direction = self.next_direction
                self.next_direction = None


class Ghost(GridSprite):
    def __init__(self, color_index, all_body_textures, scale=1.3):
        super().__init__(scale=scale)
        start = color_index * 4
        self.textures = all_body_textures[start : start + 4]
        self.texture = self.textures[0]


class Pacman(GridSprite):
    def __init__(self, scale=1.3):
        super().__init__(scale=scale)

        sprite_sheet = arcade.load_spritesheet("src/assets/PacManAssets-PacMan.png")
        all_textures = sprite_sheet.get_texture_grid(size=(32, 32), columns=4, count=11)

        self.moving_right = all_textures[0:4]
        self.moving_left = [tex.flip_left_right() for tex in self.moving_right]

        self.texture = self.moving_right[0]
        self.current_texture_index = 0
        self.time_since_last_frame = 0.0
        self.animation_speed = 0.05

    def update_animation(self, delta_time: float = 1 / 60):
        is_moving = self.change_x != 0 or self.change_y != 0

        if is_moving:
            self.time_since_last_frame += delta_time
            if self.time_since_last_frame >= self.animation_speed:
                self.time_since_last_frame = 0.0
                self.current_texture_index = (self.current_texture_index + 1) % len(
                    self.moving_right
                )
        else:
            self.current_texture_index = 0

        if self.current_direction == DIR_RIGHT:
            self.texture = self.moving_right[self.current_texture_index]
            self.angle = 0
        elif self.current_direction == DIR_LEFT:
            self.texture = self.moving_left[self.current_texture_index]
            self.angle = 0
        elif self.current_direction == DIR_UP:
            self.texture = self.moving_right[self.current_texture_index]
            self.angle = -90
        elif self.current_direction == DIR_DOWN:
            self.texture = self.moving_right[self.current_texture_index]
            self.angle = 90


class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        self.wall_list = None
        self.player_list = None
        self.ghosts_list = None
        self.pacgum_list = None
        self.super_pacgum_list = None

        self.score = 0
        self.lives = 3
        self.time_left = 60.0
        self.score_per_gum = 10
        self.score_per_super_gum = 50

        self.player_sprite = None
        self.player_start_pos = (0, 0)

        self.physics_engine = None
        self.ghost_physics_engines = []
        self.game_over = False

        self.fps_text = None
        self.game_over_text = None
        self.score_text = None
        self.lives_text = None
        self.time_text = None
        self.level_text = None

        self.level = 1
        self.max_level = 2

    def setup(self, maze_data, config):
        self.maze_data = maze_data

        def get_conf(key, default):
            if hasattr(config, key):
                return getattr(config, key)
            if isinstance(config, dict) and key in config:
                return config[key]
            return default

        self.score = 0
        self.lives = get_conf("lives", 3)
        self.time_left = get_conf("time", 60.0)
        self.score_per_gum = get_conf("points_per_pacgum", 10)
        self.score_per_super_gum = get_conf("points_per_super_pacgum", 50)

        self.player_list = arcade.SpriteList()
        self.ghosts_list = arcade.SpriteList()

        item_base_texture = arcade.load_texture("src/assets/PacManAssets-Items.png")
        pacgum_texture = item_base_texture.crop(
            0, ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE
        )
        super_pacgum_texture = item_base_texture.crop(
            ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE
        )

        self.wall_list, self.pacgum_list, self.super_pacgum_list = create_maze_sprites(
            maze_data, pacgum_texture, super_pacgum_texture
        )

        rows = len(maze_data)
        cols = len(maze_data[0]) if rows > 0 else 0

        self.player_sprite = Pacman(scale=PLAYER_SCALING)
        center_col, center_row = cols // 2, rows // 2
        offset = -GRID_PIXEL_SIZE if not rows % 2 else 0
        self.player_sprite.center_x = (
            center_col * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2) + offset
        )
        self.player_sprite.center_y = center_row * GRID_PIXEL_SIZE + (
            GRID_PIXEL_SIZE / 2
        )
        self.player_list.append(self.player_sprite)
        self.player_start_pos = (
            self.player_sprite.center_x,
            self.player_sprite.center_y,
        )

        ghosts_ss = arcade.load_spritesheet("src/assets/PacManAssets-Ghosts.png")
        ghosts_body_textures = ghosts_ss.get_texture_grid(
            size=(32, 32), columns=4, count=40
        )

        ghost_positions = [
            (cols * GRID_PIXEL_SIZE - GRID_PIXEL_SIZE / 2, GRID_PIXEL_SIZE / 2),
            (GRID_PIXEL_SIZE / 2, GRID_PIXEL_SIZE / 2),
            (GRID_PIXEL_SIZE / 2, rows * GRID_PIXEL_SIZE - GRID_PIXEL_SIZE / 2),
            (
                cols * GRID_PIXEL_SIZE - GRID_PIXEL_SIZE / 2,
                rows * GRID_PIXEL_SIZE - GRID_PIXEL_SIZE / 2,
            ),
        ]

        self.ghost_physics_engines = []
        for i, pos in enumerate(ghost_positions):
            ghost = Ghost(
                color_index=i,
                all_body_textures=ghosts_body_textures,
                scale=PLAYER_SCALING,
            )
            ghost.center_x, ghost.center_y = pos
            self.ghosts_list.append(ghost)
            self.ghost_physics_engines.append(
                arcade.PhysicsEngineSimple(ghost, self.wall_list)
            )

        self.game_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()
        self.game_camera.position = self.player_sprite.position

        self.level_text = arcade.Text(
            f"Level: {self.level}", 10, self.window.height - 30, arcade.color.YELLOW, 18
        )
        self.time_text = arcade.Text(
            f"Time: {int(self.time_left)}",
            10,
            self.window.height - 60,
            arcade.color.YELLOW,
            18,
        )
        self.score_text = arcade.Text(
            f"Score: {self.score}", 20, 20, arcade.color.YELLOW, 18
        )
        self.fps_text = arcade.Text(
            "FPS:",
            self.window.width - 20,
            self.window.height - 20,
            arcade.color.WHITE,
            14,
            anchor_x="right",
        )
        self.lives_text = arcade.Text(
            f"Lives: {self.lives}",
            self.window.width - 20,
            20,
            arcade.color.RED,
            18,
            anchor_x="right",
        )
        self.game_over_text = arcade.Text(
            "GAME OVER",
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE,
            font_size=50,
            anchor_x="center",
            anchor_y="center",
        )

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite, self.wall_list
        )
        self.window.background_color = arcade.color.BLACK
        self.game_over = False

    def on_draw(self):
        self.clear()

        with self.game_camera.activate():
            self.wall_list.draw()
            self.pacgum_list.draw()
            self.super_pacgum_list.draw()
            self.ghosts_list.draw()
            self.player_list.draw()

        with self.gui_camera.activate():
            self.fps_text.text = (
                f"FPS: {1/self.window.delta_time:.0f}"
                if self.window.delta_time > 0
                else "FPS: 0"
            )
            self.fps_text.draw()
            self.score_text.draw()
            self.time_text.draw()
            self.lives_text.draw()
            self.level_text.draw()

            if self.game_over:
                self.game_over_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.player_sprite.next_direction = DIR_UP
        elif key == arcade.key.DOWN:
            self.player_sprite.next_direction = DIR_DOWN
        elif key == arcade.key.LEFT:
            self.player_sprite.next_direction = DIR_LEFT
        elif key == arcade.key.RIGHT:
            self.player_sprite.next_direction = DIR_RIGHT

    def on_update(self, delta_time):
        if self.game_over:
            return

        self.time_left -= delta_time
        if self.time_left <= 0:
            self.time_left = 0
            self.game_over = True

        self.player_sprite.try_turning(self.maze_data)
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        if self.player_sprite.current_direction == DIR_UP:
            self.player_sprite.change_y = MOVEMENT_SPEED
        elif self.player_sprite.current_direction == DIR_DOWN:
            self.player_sprite.change_y = -MOVEMENT_SPEED
        elif self.player_sprite.current_direction == DIR_LEFT:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif self.player_sprite.current_direction == DIR_RIGHT:
            self.player_sprite.change_x = MOVEMENT_SPEED

        self.physics_engine.update()

        target_col = int(
            round(
                (self.player_sprite.center_x - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE
            )
        )
        target_row = int(
            round(
                (self.player_sprite.center_y - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE
            )
        )

        for i, ghost in enumerate(self.ghosts_list):
            ghost_col = int(
                round((ghost.center_x - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE)
            )
            ghost_row = int(
                round((ghost.center_y - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE)
            )

            best_dir = bfs_shortest_path_direction(
                ghost_col, ghost_row, target_col, target_row, self.maze_data
            )
            if best_dir is not None:
                ghost.next_direction = best_dir

            ghost.try_turning(self.maze_data)

            ghost.change_x = 0
            ghost.change_y = 0
            if ghost.current_direction == DIR_UP:
                ghost.change_y = GHOST_SPEED
            elif ghost.current_direction == DIR_DOWN:
                ghost.change_y = -GHOST_SPEED
            elif ghost.current_direction == DIR_LEFT:
                ghost.change_x = -GHOST_SPEED
            elif ghost.current_direction == DIR_RIGHT:
                ghost.change_x = GHOST_SPEED

            self.ghost_physics_engines[i].update()

        if arcade.check_for_collision_with_list(self.player_sprite, self.ghosts_list):
            self.lives -= 1
            if self.lives <= 0:
                self.lives = 0
                self.game_over = True
            else:
                self.player_sprite.center_x, self.player_sprite.center_y = (
                    self.player_start_pos
                )
                self.player_sprite.current_direction = None
                self.player_sprite.next_direction = None

        gums_hit = arcade.check_for_collision_with_list(
            self.player_sprite, self.pacgum_list
        )
        for gum in gums_hit:
            gum.remove_from_sprite_lists()
            self.score += self.score_per_gum

        super_gums_hit = arcade.check_for_collision_with_list(
            self.player_sprite, self.super_pacgum_list
        )
        for sgum in super_gums_hit:
            sgum.remove_from_sprite_lists()
            self.score += self.score_per_super_gum

        self.score_text.text = f"Score: {self.score}"
        self.time_text.text = f"Time: {int(self.time_left)}"
        self.lives_text.text = f"Lives: {self.lives}"

        self.player_sprite.update_animation(delta_time)

        self.game_camera.position = arcade.math.lerp_2d(
            self.game_camera.position, self.player_sprite.position, CAMERA_PAN_SPEED
        )
