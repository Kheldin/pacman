from random import choice


def random_dir(ghost_x: int, ghost_y: int, maze_data, current_dir: int):
    total_rows = len(maze_data)
    maze_array_row = (total_rows - 1) - ghost_y

    if maze_array_row < 0 or maze_array_row >= total_rows or ghost_x < 0 or ghost_x >= len(maze_data[0]):
        return None

    current_cell = maze_data[maze_array_row][ghost_x]
    possible_moves = []

    if current_cell in [0, 2, 4, 6, 8, 10, 12, 14]:  # Nord
        possible_moves.append(2)

    if current_cell in [0, 1, 4, 5, 8, 9, 12, 13]:  # Est
        possible_moves.append(0)

    if current_cell in [0, 1, 2, 3, 8, 9, 10, 11]:  # Sud
        possible_moves.append(3)

    if current_cell in [0, 1, 2, 3, 4, 5, 6, 7]:  # Ouest
        possible_moves.append(1)

    opposites = {0: 1, 1: 0, 2: 3, 3: 2}

    if current_dir is not None:
        opposite_dir = opposites.get(current_dir)
        if opposite_dir in possible_moves and len(possible_moves) > 1:
            possible_moves.remove(opposite_dir)

    if not possible_moves:
        return None

    return choice(possible_moves)
