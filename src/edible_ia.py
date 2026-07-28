def best_dir_to_run_away(pacman_x: int, pacman_y: int, ghost_x: int, ghost_y: int, maze_data):
    total_rows = len(maze_data)
    maze_array_row = (total_rows - 1) - ghost_y

    if maze_array_row < 0 or maze_array_row >= total_rows or ghost_x < 0 or ghost_x >= len(maze_data[0]):
        return None

    current_cell = maze_data[maze_array_row][ghost_x]
    possible_moves = []

    if current_cell in [0, 2, 4, 6, 8, 10, 12, 14]: # north
        possible_moves.append((ghost_x, ghost_y + 1, 2))

    if current_cell in [0, 1, 4, 5, 8, 9, 12, 13]: # east
        possible_moves.append((ghost_x + 1, ghost_y, 0))

    if current_cell in [0, 1, 2, 3, 8, 9, 10, 11]: # south
        possible_moves.append((ghost_x, ghost_y - 1, 3))

    if current_cell in [0, 1, 2, 3, 4, 5, 6, 7]: # west
        possible_moves.append((ghost_x - 1, ghost_y, 1))

    if not possible_moves:
        return None

    best_dir = None
    max_distance = -1

    for next_x, next_y, direction in possible_moves:
        distance = abs(pacman_x - next_x) + abs(pacman_y - next_y)

        if distance > max_distance:
            max_distance = distance
            best_dir = direction

    return best_dir