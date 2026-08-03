def best_dir_to_run_away(
    pacman_x: int,
    pacman_y: int,
    ghost_x: int,
    ghost_y: int,
    maze_data: list[list[int]],
    current_dir: int
) -> int | None:
    """
    Calculate the best direction for the ghost to run away from Pac-Man.

    This function evaluates all valid adjacent cells based on the maze walls
    and the ghost's current direction (to avoid 180-degree reversals).
    It returns the direction that maximizes the Manhattan distance to Pac-Man.

    Args:
        pacman_x (int): The x-coordinate of Pac-Man in the grid.
        pacman_y (int): The y-coordinate of Pac-Man in the grid.
        ghost_x (int): The x-coordinate of the ghost in the grid.
        ghost_y (int): The y-coordinate of the ghost in the grid.
        maze_data (list[list[int]]): 2D array representing the maze structure.
        current_dir (int): The current direction the ghost is facing.

    Returns:
        int | None: The integer representing the best direction to flee
        (0: East, 1: West, 2: North, 3: South), or None if no move is possible.
    """
    total_rows = len(maze_data)
    maze_array_row = (total_rows - 1) - ghost_y

    if (maze_array_row < 0 or maze_array_row >= total_rows or
            ghost_x < 0 or ghost_x >= len(maze_data[0])):
        return None

    current_cell = maze_data[maze_array_row][ghost_x]
    possible_moves: list[tuple[int, int, int]] = []

    if current_cell in [0, 2, 4, 6, 8, 10, 12, 14] and current_dir != 3:
        possible_moves.append((ghost_x, ghost_y + 1, 2))  # north

    if current_cell in [0, 1, 4, 5, 8, 9, 12, 13] and current_dir != 1:
        possible_moves.append((ghost_x + 1, ghost_y, 0))  # east

    if current_cell in [0, 1, 2, 3, 8, 9, 10, 11] and current_dir != 2:
        possible_moves.append((ghost_x, ghost_y - 1, 3))  # south

    if current_cell in [0, 1, 2, 3, 4, 5, 6, 7] and current_dir != 0:
        possible_moves.append((ghost_x - 1, ghost_y, 1))  # west

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
