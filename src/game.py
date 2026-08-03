import arcade
import json
import os
import math
from typing import Any, Optional
from collections import deque
from src.maze_sprites import create_maze_sprites
from src.edible_ai import best_dir_to_run_away
from src.random_ai import random_dir

TILE_SOURCE_SIZE = 16
PLAYER_SOURCE_SIZE = 32
ITEM_SOURCE_SIZE = 16

TILE_SPRITE_SCALING = 2.5
PLAYER_SCALING = 1.3

GRID_PIXEL_SIZE = TILE_SOURCE_SIZE * TILE_SPRITE_SCALING

WALL_THICKNESS = 2
WALL_COLOR = arcade.color.BLUE_SAPPHIRE

CAMERA_PAN_SPEED = 0.15
GHOST_SPEED = 2.0

DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3


def bfs_shortest_path_direction(
    start_col: int,
    start_row: int,
    target_col: int,
    target_row: int,
    maze_data: list[list[int]]
) -> Optional[int]:
    """
    Breadth-First Search (BFS) algorithm to find the shortest path in a grid.
    Returns the first direction the ghost should take to reach the target.
    """
    if (start_col, start_row) == (target_col, target_row):
        return None

    total_rows = len(maze_data)
    total_cols = len(maze_data[0]) if total_rows > 0 else 0

    search_queue: deque[tuple[int, int, list[int]]] = deque()
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

        if not (cell_wall_data & 1):
            next_col, next_row = current_col, current_row + 1
            if (next_col, next_row) not in visited_cells:
                visited_cells.add((next_col, next_row))
                search_queue.append(
                    (next_col, next_row, path_taken + [DIR_UP]))

        if not (cell_wall_data & 2):
            next_col, next_row = current_col + 1, current_row
            if (next_col, next_row) not in visited_cells:
                visited_cells.add((next_col, next_row))
                search_queue.append(
                    (next_col, next_row, path_taken + [DIR_RIGHT]))

        if not (cell_wall_data & 4):
            next_col, next_row = current_col, current_row - 1
            if (next_col, next_row) not in visited_cells:
                visited_cells.add((next_col, next_row))
                search_queue.append(
                    (next_col, next_row, path_taken + [DIR_DOWN]))

        if not (cell_wall_data & 8):
            next_col, next_row = current_col - 1, current_row
            if (next_col, next_row) not in visited_cells:
                visited_cells.add((next_col, next_row))
                search_queue.append(
                    (next_col, next_row, path_taken + [DIR_LEFT]))

    return None


class GridSprite(arcade.Sprite):
    """
    Base grid class to manage the centering of entities and collisions.
    Ensures that sprites move strictly along the grid lines.
    """

    def __init__(self, scale: float = 1.0) -> None:
        """Initialize the grid sprite."""
        super().__init__(scale=scale)
        self.current_direction: Optional[int] = None
        self.next_direction: Optional[int] = None

    def try_turning(self, maze_data: list[list[int]]) -> None:
        """Evaluate if the sprite can turn based on grid constraints."""
        if (self.next_direction is None or
                self.next_direction == self.current_direction):
            return

        opposite_directions = {
            DIR_UP: DIR_DOWN,
            DIR_DOWN: DIR_UP,
            DIR_LEFT: DIR_RIGHT,
            DIR_RIGHT: DIR_LEFT,
        }

        if (self.current_direction is not None and
                self.next_direction == opposite_directions.get(
                    self.current_direction)):
            self.current_direction = self.next_direction
            self.next_direction = None
            return

        # Indique explicitement à Mypy que ces valeurs sont des float
        cx: float = self.center_x  # type: ignore[has-type]
        cy: float = self.center_y  # type: ignore[has-type]

        current_col = int(
            round((cx - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE)
        )
        grid_row_bottom_up = int(
            round((cy - (GRID_PIXEL_SIZE / 2)) / GRID_PIXEL_SIZE)
        )

        total_rows = len(maze_data)
        maze_array_row = (total_rows - 1) - grid_row_bottom_up

        cell_wall_data = maze_data[maze_array_row][current_col]

        cell_center_x = current_col * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
        cell_center_y = grid_row_bottom_up * GRID_PIXEL_SIZE + (
            GRID_PIXEL_SIZE / 2
        )

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
            elif self.current_direction == DIR_RIGHT and cx >= cell_center_x:
                can_execute_turn = True
            elif self.current_direction == DIR_LEFT and cx <= cell_center_x:
                can_execute_turn = True
            elif self.current_direction == DIR_UP and cy >= cell_center_y:
                can_execute_turn = True
            elif self.current_direction == DIR_DOWN and cy <= cell_center_y:
                can_execute_turn = True

            if can_execute_turn:
                if self.next_direction in [DIR_UP, DIR_DOWN]:
                    self.center_x = cell_center_x
                elif self.next_direction in [DIR_LEFT, DIR_RIGHT]:
                    self.center_y = cell_center_y

                self.current_direction = self.next_direction
                self.next_direction = None


class Ghost(GridSprite):
    """
    Represents an enemy Ghost within the maze.
    """

    def __init__(
        self,
        start_position: tuple[float, float],
        color_index: int,
        all_body_textures: list[arcade.Texture],
        all_faces_textures: list[arcade.Texture],
        scale: float = 1.3
    ) -> None:
        """Initialize the ghost's textures, mode, and start position."""
        super().__init__(scale=scale)

        self.start_position = start_position
        self.mode = "chase" if color_index % 2 else "random"
        self.last_cell: Optional[tuple[int, int]] = None

        start = color_index * 4
        self.respawn_time: Optional[float] = None
        self.base_textures = all_body_textures[start: start + 4]
        self.base_texture = self.base_textures[0]
        self.edible_textures = all_body_textures[35: 36]
        self.edible_texture = self.edible_textures[0]

        self.texture = self.base_texture
        self.face_sprite = arcade.Sprite(scale=scale)
        self.face_textures = all_faces_textures
        self.face_sprite.texture = self.face_textures[color_index]
        self.current_direction = None

    def sync_faces(self) -> None:
        """Keep the face texture aligned with the ghost's body."""
        self.face_sprite.center_x = self.center_x
        self.face_sprite.center_y = self.center_y + 7

    def sync_edible_textures(self) -> None:
        """Synchronize textures when the ghost is edible."""
        pass


class Pacman(GridSprite):
    """
    Represents the main player character, Pac-Man.
    """

    def __init__(self, scale: float = 1.3) -> None:
        """Initialize Pac-Man's sprites and animation speeds."""
        super().__init__(scale=scale)

        sprite_sheet = arcade.load_spritesheet(
            "src/assets/PacManAssets-PacMan.png"
        )
        all_textures = sprite_sheet.get_texture_grid(
            size=(32, 32), columns=4, count=11
        )

        self.moving_right = all_textures[0:4]
        self.moving_left = [tex.flip_left_right() for tex in self.moving_right]

        self.texture = self.moving_right[0]
        self.current_texture_index = 0
        self.time_since_last_frame = 0.0
        self.normal_animation_speed = 0.05
        self.animation_speed = self.normal_animation_speed
        self.normal_speed = 5
        self.speed = self.normal_speed

    def reset_normal(self) -> None:
        """Reset Pac-Man to default speed and animation."""
        self.animation_speed = self.normal_animation_speed
        self.speed = self.normal_speed

    def cheat_mode_activation(self) -> None:
        """Activate faster speed for cheat mode."""
        self.animation_speed = 0.01
        self.speed = 10

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        """Update Pac-Man's sprite based on movement and direction."""
        is_moving = self.change_x != 0 or self.change_y != 0

        if is_moving:
            self.time_since_last_frame += delta_time
            if self.time_since_last_frame >= self.animation_speed:
                self.time_since_last_frame = 0.0
                self.current_texture_index = (
                    self.current_texture_index + 1
                ) % len(self.moving_right)
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
    """
    Main Game View managing the gameplay loop, rendering, and logic.
    """

    def __init__(self) -> None:
        """Initialize the game view variables."""
        super().__init__()

        self.wall_list: Optional[arcade.SpriteList] = None
        self.player_list: Optional[arcade.SpriteList] = None
        self.ghosts_list: Optional[arcade.SpriteList] = None
        self.ghosts_save_list: Optional[arcade.SpriteList] = None
        self.faces_list: Optional[arcade.SpriteList] = None
        self.pacgum_list: Optional[arcade.SpriteList] = None
        self.super_pacgum_list: Optional[arcade.SpriteList] = None

        self.fps_text: Optional[arcade.Text] = None
        self.score_text: Optional[arcade.Text] = None
        self.lives_text: Optional[arcade.Text] = None
        self.time_text: Optional[arcade.Text] = None
        self.level_text: Optional[arcade.Text] = None

        self.ghosts_edible: bool = False
        self.start_edible_mode: float = 0.0
        self.pause: bool = False

        self.score: int = 0
        self.lives: int = 3
        self.time_left: float = 60.0
        self.score_per_gum: int = 10
        self.score_per_super_gum: int = 50

        self.player_sprite: Optional[Pacman] = None
        self.player_start_pos: tuple[float, float] = (0, 0)

        self.physics_engine: Optional[arcade.PhysicsEngineSimple] = None
        self.ghost_physics_engines: list[arcade.PhysicsEngineSimple] = []
        self.game_over: bool = False
        self.win: bool = False
        self.player_name: str = ""

        self.level: int = 1

    def setup(self, maze_data: list[list[int]], config: Any) -> None:
        """Set up the game level and initialize the entities."""
        self.maze_data = maze_data
        self.config = config

        def get_conf(key: str, default: Any) -> Any:
            if hasattr(config, key):
                return getattr(config, key)
            if isinstance(config, dict) and key in config:
                return config[key]
            return default

        self.score = 0
        self.cheat_mode = False
        self.lives = get_conf("lives", 3)
        self.time_left = get_conf("time", 60.0)
        self.score_per_gum = get_conf("points_per_pacgum", 10)
        self.score_per_super_gum = get_conf("points_per_super_pacgum", 50)

        self.player_list = arcade.SpriteList()
        self.ghosts_list = arcade.SpriteList()
        self.ghosts_save_list = arcade.SpriteList()
        self.faces_list = arcade.SpriteList()

        item_base_texture = arcade.load_texture(
            "src/assets/PacManAssets-Items.png"
        )
        pacgum_texture = item_base_texture.crop(
            0, ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE
        )
        super_pacgum_texture = item_base_texture.crop(
            ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE,
            ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE
        )

        (
            self.wall_list,
            self.pacgum_list,
            self.super_pacgum_list
        ) = create_maze_sprites(
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
        self.player_sprite.center_y = (
            center_row * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
        )
        self.player_list.append(self.player_sprite)
        self.player_start_pos = (
            self.player_sprite.center_x,
            self.player_sprite.center_y,
        )

        ghosts_bss = arcade.load_spritesheet(
            "src/assets/PacManAssets-Ghosts_Bodys.png"
        )
        ghosts_body_textures = ghosts_bss.get_texture_grid(
            size=(32, 32), columns=4, count=40
        )
        ghosts_fss = arcade.load_spritesheet(
            "src/assets/PacManAssets-Ghosts_Faces.png"
        )
        ghosts_face_textures = ghosts_fss.get_texture_grid(
            size=(16, 16), columns=8, count=16
        )

        ghost_positions = [
            (cols * GRID_PIXEL_SIZE - GRID_PIXEL_SIZE / 2,
             GRID_PIXEL_SIZE / 2),
            (GRID_PIXEL_SIZE / 2, GRID_PIXEL_SIZE / 2),
            (GRID_PIXEL_SIZE / 2,
             rows * GRID_PIXEL_SIZE - GRID_PIXEL_SIZE / 2),
            (cols * GRID_PIXEL_SIZE - GRID_PIXEL_SIZE / 2,
             rows * GRID_PIXEL_SIZE - GRID_PIXEL_SIZE / 2),
        ]

        self.ghost_physics_engines = []
        for i, pos in enumerate(ghost_positions):
            ghost = Ghost(
                start_position=pos,
                color_index=i,
                all_body_textures=ghosts_body_textures,
                all_faces_textures=ghosts_face_textures,
                scale=PLAYER_SCALING,
            )
            ghost.center_x, ghost.center_y = pos
            ghost.sync_faces()
            self.ghosts_list.append(ghost)
            self.ghosts_save_list.append(ghost)
            self.faces_list.append(ghost.face_sprite)
            self.ghost_physics_engines.append(
                arcade.PhysicsEngineSimple(ghost, self.wall_list)
            )

        self.game_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()
        self.game_camera.position = self.player_sprite.position

        retro_font = "Pacmania"
        arcade.load_font("src/assets/Pacmania.ttf")

        self.up1_text = arcade.Text(
            "1UP", 40, self.window.height - 25,
            arcade.color.WHITE, 16, font_name=retro_font
        )
        self.score_text = arcade.Text(
            str(self.score), 40, self.window.height - 45,
            arcade.color.WHITE, 16, font_name=retro_font
        )

        self.high_score_header = arcade.Text(
            "HIGH SCORE", self.window.width / 2, self.window.height - 25,
            arcade.color.WHITE, 16, anchor_x="center", font_name=retro_font
        )
        self.high_score_text = arcade.Text(
            "10000", self.window.width / 2, self.window.height - 45,
            arcade.color.WHITE, 16, anchor_x="center", font_name=retro_font
        )

        self.lives_text = arcade.Text(
            f"LIVES: {self.lives}", 20, 15,
            arcade.color.YELLOW, 16, font_name=retro_font
        )
        self.level_text = arcade.Text(
            f"NIV: {self.level}", self.window.width - 20, 15,
            arcade.color.YELLOW, 16, anchor_x="right", font_name=retro_font
        )

        self.time_text = arcade.Text(
            f"TIME: {int(self.time_left)}",
            self.window.width - 150, self.window.height - 45,
            arcade.color.WHITE, 16, font_name=retro_font
        )
        self.fps_text = arcade.Text(
            "FPS: 0", self.window.width - 20, 50,
            arcade.color.GRAY, 12, anchor_x="right"
        )

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite, self.wall_list
        )
        self.window.background_color = arcade.color.BLACK
        self.game_over = False

    def on_draw(self) -> None:
        """Render the screen objects and text."""
        self.clear()

        with self.game_camera.activate():
            if self.wall_list:
                self.wall_list.draw()
            if self.pacgum_list:
                self.pacgum_list.draw()
            if self.super_pacgum_list:
                self.super_pacgum_list.draw()
            if self.ghosts_list:
                self.ghosts_list.draw()
            if self.faces_list:
                self.faces_list.draw()
            if self.player_list:
                self.player_list.draw()

        with self.gui_camera.activate():
            if self.up1_text:
                self.up1_text.draw()
            if self.score_text:
                self.score_text.draw()
            if self.high_score_header:
                self.high_score_header.draw()
            if self.high_score_text:
                self.high_score_text.draw()

            if self.fps_text:
                fps = (1 / self.window.delta_time
                       if self.window.delta_time > 0 else 0)
                self.fps_text.text = f"FPS: {fps:.0f}"
                self.fps_text.draw()

            if self.time_text:
                self.time_text.draw()
            if self.lives_text:
                self.lives_text.draw()
            if self.level_text:
                self.level_text.draw()

            cheat_text = "ON" if getattr(self, 'cheat_mode', False) else "OFF"
            pause_text = "ON" if self.pause else "OFF"

            arcade.Text(
                f"CHEAT MODE: {cheat_text} (Press C)",
                self.window.width - 150, self.window.height - 150,
                arcade.color.YELLOW, font_size=10, anchor_x="center"
            ).draw()

            arcade.Text(
                f"PAUSE MODE: {pause_text} (Press SPACE)",
                self.window.width - 140, self.window.height - 180,
                arcade.color.YELLOW, font_size=10, anchor_x="center"
            ).draw()

            if self.pause:
                arcade.Text(
                    "PAUSE",
                    self.window.width / 2, self.window.height / 2,
                    arcade.color.YELLOW, font_size=90,
                    anchor_x="center", font_name="Pacmania"
                ).draw()

                arcade.Text(
                    "PRESS 'M' FOR MENU",
                    self.window.width / 2, self.window.height / 2 - 80,
                    arcade.color.WHITE, font_size=20,
                    anchor_x="center", font_name="Pacmania"
                ).draw()

            arcade.Text(
                f"LEVEL: {self.level}",
                self.window.width / 2, self.window.height / 1.2,
                arcade.color.YELLOW, font_size=20,
                anchor_x="center", font_name="Pacmania"
            ).draw()

            if self.game_over:
                arcade.Text(
                    "GAME OVER",
                    self.window.width / 2, self.window.height / 2 + 50,
                    arcade.color.YELLOW, font_size=70,
                    anchor_x="center", font_name="Pacmania"
                ).draw()

            if self.win:
                arcade.Text(
                    "YOU WIN!",
                    self.window.width / 2, self.window.height / 2 + 50,
                    arcade.color.GREEN, font_size=60,
                    anchor_x="center", font_name="Pacmania"
                ).draw()

            if self.win or self.game_over:
                arcade.Text(
                    f"NAME: {self.player_name}_",
                    self.window.width / 2, self.window.height / 2 - 20,
                    arcade.color.WHITE, font_size=30,
                    anchor_x="center", font_name="Pacmania"
                ).draw()

                arcade.Text(
                    "PRESS ENTER TO SAVE",
                    self.window.width / 2, self.window.height / 2 - 70,
                    arcade.color.WHITE, font_size=15,
                    anchor_x="center", font_name="Pacmania"
                ).draw()

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Handle player keyboard input."""
        if self.win or self.game_over:
            if key == arcade.key.ENTER and len(self.player_name) > 0:
                score_file = self.config.highscore_filename
                scores_data: dict[str, list[int]] = {}

                if os.path.exists(score_file):
                    try:
                        with open(score_file, "r") as file:
                            scores_data = json.load(file)
                    except json.JSONDecodeError:
                        pass

                if self.player_name in scores_data:
                    scores_data[self.player_name].append(self.score)
                else:
                    scores_data[self.player_name] = [self.score]

                with open(score_file, "w") as file:
                    json.dump(scores_data, file, indent=4)

                from src.menu_view import MenuView
                menu = MenuView(self.config)
                self.window.show_view(menu)

            elif key == arcade.key.BACKSPACE:
                self.player_name = self.player_name[:-1]
            elif arcade.key.A <= key <= arcade.key.Z:
                if len(self.player_name) < 10:
                    self.player_name += chr(key).upper()
            return

        if not self.player_sprite:
            return

        if key == arcade.key.UP:
            self.player_sprite.next_direction = DIR_UP
        elif key == arcade.key.DOWN:
            self.player_sprite.next_direction = DIR_DOWN
        elif key == arcade.key.LEFT:
            self.player_sprite.next_direction = DIR_LEFT
        elif key == arcade.key.RIGHT:
            self.player_sprite.next_direction = DIR_RIGHT
        elif key == arcade.key.ESCAPE:
            exit()
        elif key == arcade.key.C:
            if getattr(self, 'cheat_mode', False):
                self.cheat_mode = False
                self.player_sprite.reset_normal()
            else:
                self.cheat_mode = True
                self.player_sprite.cheat_mode_activation()
        elif key == arcade.key.SPACE:
            self.pause = not self.pause
        elif key == arcade.key.M and self.pause:
            from src.menu_view import MenuView
            menu = MenuView(self.config)
            self.window.show_view(menu)
        elif key == arcade.key.S and getattr(self, 'cheat_mode', False):
            self.load_next_level()
            self.level += 1

    def load_next_level(self) -> None:
        """Generate and load the next maze level."""
        from mazegenerator import MazeGenerator

        maze = MazeGenerator((self.config.width, self.config.height))
        maze.generate()
        self.maze_data = maze.maze

        if self.wall_list:
            self.wall_list.clear()
        if self.pacgum_list:
            self.pacgum_list.clear()
        if self.super_pacgum_list:
            self.super_pacgum_list.clear()

        item_base_texture = arcade.load_texture(
            "src/assets/PacManAssets-Items.png"
        )
        pacgum_texture = item_base_texture.crop(
            0, ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE
        )
        super_pacgum_texture = item_base_texture.crop(
            ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE,
            ITEM_SOURCE_SIZE, ITEM_SOURCE_SIZE
        )

        (
            self.wall_list,
            self.pacgum_list,
            self.super_pacgum_list
        ) = create_maze_sprites(
            self.maze_data, pacgum_texture, super_pacgum_texture
        )

        if self.player_sprite and self.wall_list:
            self.physics_engine = arcade.PhysicsEngineSimple(
                self.player_sprite, self.wall_list
            )

        self.ghost_physics_engines = []
        if self.ghosts_list and self.wall_list:
            for ghost in self.ghosts_list:
                self.ghost_physics_engines.append(
                    arcade.PhysicsEngineSimple(ghost, self.wall_list)
                )

        if self.player_sprite:
            (self.player_sprite.center_x,
             self.player_sprite.center_y) = self.player_start_pos
            self.player_sprite.current_direction = None
            self.player_sprite.next_direction = None

        if self.ghosts_list:
            for ghost in self.ghosts_list:
                ghost.center_x, ghost.center_y = ghost.start_position
                ghost.current_direction = None
                ghost.next_direction = None
                ghost.respawn_time = None
                ghost.last_cell = None
                ghost.sync_faces()

        def get_conf(key: str, default: Any) -> Any:
            if hasattr(self.config, key):
                return getattr(self.config, key)
            if isinstance(self.config, dict) and key in self.config:
                return self.config[key]
            return default

        self.time_left = get_conf("time", 60.0)

    def on_update(self, delta_time: float) -> None:
        """Update game state, logic, and physics."""
        if self.level > 10:
            self.win = True

        if self.game_over or self.pause or self.win:
            return

        if (self.ghosts_edible and
                self.start_edible_mode - self.time_left >= 10):
            self.ghosts_edible = False

        self.time_left -= delta_time
        if self.time_left <= 0:
            self.time_left = 0
            self.game_over = True

        if not self.player_sprite:
            return

        self.player_sprite.try_turning(self.maze_data)
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        if self.player_sprite.current_direction == DIR_UP:
            self.player_sprite.change_y = self.player_sprite.speed
        elif self.player_sprite.current_direction == DIR_DOWN:
            self.player_sprite.change_y = -self.player_sprite.speed
        elif self.player_sprite.current_direction == DIR_LEFT:
            self.player_sprite.change_x = -self.player_sprite.speed
        elif self.player_sprite.current_direction == DIR_RIGHT:
            self.player_sprite.change_x = self.player_sprite.speed

        if self.physics_engine:
            self.physics_engine.update()

        target_col = int(
            round(
                (self.player_sprite.center_x - (GRID_PIXEL_SIZE / 2))
                / GRID_PIXEL_SIZE
            )
        )
        target_row = int(
            round(
                (self.player_sprite.center_y - (GRID_PIXEL_SIZE / 2))
                / GRID_PIXEL_SIZE
            )
        )

        cheat_mode_active = getattr(self, 'cheat_mode', False)

        if not cheat_mode_active and self.ghosts_list:
            for i, ghost in enumerate(self.ghosts_list):
                if ghost.respawn_time is not None:
                    if self.time_left <= ghost.respawn_time:
                        ghost.respawn_time = None
                        ghost.center_x, ghost.center_y = ghost.start_position
                        ghost.sync_faces()
                    else:
                        continue

                ghost_col = int(
                    round(
                        (ghost.center_x - (GRID_PIXEL_SIZE / 2))
                        / GRID_PIXEL_SIZE
                    )
                )
                ghost_row = int(
                    round(
                        (ghost.center_y - (GRID_PIXEL_SIZE / 2))
                        / GRID_PIXEL_SIZE
                    )
                )
                current_cell = (ghost_col, ghost_row)

                if ghost.last_cell != current_cell:
                    if self.ghosts_edible:
                        best_dir = best_dir_to_run_away(
                            target_col, target_row, ghost_col, ghost_row,
                            self.maze_data, current_dir=ghost.current_direction
                        )
                    else:
                        if ghost.mode == "chase":
                            best_dir = bfs_shortest_path_direction(
                                ghost_col, ghost_row, target_col, target_row,
                                self.maze_data
                            )
                        else:
                            best_dir = random_dir(
                                ghost_x=ghost_col, ghost_y=ghost_row,
                                maze_data=self.maze_data,
                                current_dir=ghost.current_direction
                            )

                    if best_dir is not None:
                        ghost.next_direction = best_dir

                    ghost.last_cell = current_cell

                ghost.try_turning(self.maze_data)
                ghost.change_x = 0
                ghost.change_y = 0

                if self.ghosts_edible:
                    ghost.texture = ghost.edible_texture
                else:
                    ghost.texture = ghost.base_texture

                if ghost.current_direction == DIR_UP:
                    ghost.change_y = GHOST_SPEED
                elif ghost.current_direction == DIR_DOWN:
                    ghost.change_y = -GHOST_SPEED
                elif ghost.current_direction == DIR_LEFT:
                    ghost.change_x = -GHOST_SPEED
                elif ghost.current_direction == DIR_RIGHT:
                    ghost.change_x = GHOST_SPEED

                if i < len(self.ghost_physics_engines):
                    self.ghost_physics_engines[i].update()
                ghost.sync_faces()

            ghosts_hit = arcade.check_for_collision_with_list(
                self.player_sprite, self.ghosts_list
            )

            if ghosts_hit:
                if self.ghosts_edible:
                    for ghost in ghosts_hit:
                        ghost.respawn_time = self.time_left - 10
                        ghost.center_x = -1000
                        ghost.center_y = -1000
                        ghost.sync_faces()
                        self.score += 200
                else:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.lives = 0
                        self.game_over = True
                    else:
                        (self.player_sprite.center_x,
                         self.player_sprite.center_y) = self.player_start_pos
                        self.player_sprite.current_direction = None
                        self.player_sprite.next_direction = None

                        for i, ghost in enumerate(self.ghosts_list):
                            (ghost.center_x,
                             ghost.center_y) = ghost.start_position
                            ghost.current_direction = None
                            ghost.next_direction = None
                            ghost.respawn_time = None
                            ghost.sync_faces()

        if (cheat_mode_active and self.pacgum_list is not None and
                self.super_pacgum_list is not None):
            aura_rad = GRID_PIXEL_SIZE * 3
            gums_hit = [
                gum for gum in self.pacgum_list
                if math.hypot(
                    self.player_sprite.center_x - gum.center_x,
                    self.player_sprite.center_y - gum.center_y
                ) < aura_rad
            ]
            super_gums_hit = [
                sgum for sgum in self.super_pacgum_list
                if math.hypot(
                    self.player_sprite.center_x - sgum.center_x,
                    self.player_sprite.center_y - sgum.center_y
                ) < aura_rad
            ]
        else:
            if self.pacgum_list:
                gums_hit = arcade.check_for_collision_with_list(
                    self.player_sprite, self.pacgum_list
                )
            else:
                gums_hit = []

            if self.super_pacgum_list:
                super_gums_hit = arcade.check_for_collision_with_list(
                    self.player_sprite, self.super_pacgum_list
                )
            else:
                super_gums_hit = []

        for gum in gums_hit:
            gum.remove_from_sprite_lists()
            self.score += self.score_per_gum

        if super_gums_hit:
            self.ghosts_edible = True
            self.start_edible_mode = self.time_left

        for sgum in super_gums_hit:
            sgum.remove_from_sprite_lists()
            self.score += self.score_per_super_gum

        if self.pacgum_list is not None and self.super_pacgum_list is not None:
            if (len(self.pacgum_list) == 0 and
                    len(self.super_pacgum_list) == 0):
                self.level += 1
                self.load_next_level()
                return

        if self.score_text:
            self.score_text.text = str(self.score)
        if self.time_text:
            self.time_text.text = f"TIME: {int(self.time_left)}"
        if self.lives_text:
            self.lives_text.text = f"LIVES: {self.lives}"

        self.player_sprite.update_animation(delta_time)

        self.game_camera.position = arcade.math.lerp_2d(
            self.game_camera.position,
            self.player_sprite.position,
            CAMERA_PAN_SPEED
        )
