import arcade

def create_maze_sprites(maze_data, pacgum_texture, super_pacgum_texture):
    from src.game import GRID_PIXEL_SIZE, WALL_COLOR, WALL_THICKNESS
    wall_list = arcade.SpriteList()
    pacgum_list = arcade.SpriteList()
    super_pacgum_list = arcade.SpriteList()

    rows = len(maze_data)
    cols = len(maze_data[0]) if rows > 0 else 0

    for row_index, row in enumerate(maze_data):
        for col_index, cell_value in enumerate(row):
            
            cx = col_index * GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)
            cy = (rows - 1 - row_index) * \
                GRID_PIXEL_SIZE + (GRID_PIXEL_SIZE / 2)

            is_corner = (row_index == 0 and col_index == 0) or \
                        (row_index == 0 and col_index == cols - 1) or \
                        (row_index == rows - 1 and col_index == 0) or \
                        (row_index == rows - 1 and col_index == cols - 1)

            if cell_value != 15:
                if is_corner:
                    super_gum = arcade.Sprite(super_pacgum_texture, scale=1.0)
                    super_gum.center_x = cx
                    super_gum.center_y = cy
                    super_pacgum_list.append(super_gum)
                else:
                    pacgum = arcade.Sprite(pacgum_texture, scale=1.0)
                    pacgum.center_x = cx
                    pacgum.center_y = cy
                    pacgum_list.append(pacgum)

            if cell_value & 1:
                wall = arcade.SpriteSolidColor(
                    width=int(GRID_PIXEL_SIZE), height=WALL_THICKNESS, color=WALL_COLOR)
                wall.center_x, wall.center_y = cx, cy + \
                    (GRID_PIXEL_SIZE / 2) - (WALL_THICKNESS / 2)
                wall_list.append(wall)

            if cell_value & 2:
                wall = arcade.SpriteSolidColor(
                    width=WALL_THICKNESS, height=int(GRID_PIXEL_SIZE), color=WALL_COLOR)
                wall.center_x, wall.center_y = cx + \
                    (GRID_PIXEL_SIZE / 2) - (WALL_THICKNESS / 2), cy
                wall_list.append(wall)

            if cell_value & 4:
                wall = arcade.SpriteSolidColor(
                    width=int(GRID_PIXEL_SIZE), height=WALL_THICKNESS, color=WALL_COLOR)
                wall.center_x, wall.center_y = cx, cy - \
                    (GRID_PIXEL_SIZE / 2) + (WALL_THICKNESS / 2)
                wall_list.append(wall)

            if cell_value & 8:
                wall = arcade.SpriteSolidColor(
                    width=WALL_THICKNESS, height=int(GRID_PIXEL_SIZE), color=WALL_COLOR)
                wall.center_x, wall.center_y = cx - \
                    (GRID_PIXEL_SIZE / 2) + (WALL_THICKNESS / 2), cy
                wall_list.append(wall)

    return wall_list, pacgum_list, super_pacgum_list
