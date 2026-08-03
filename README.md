*This project has been created as part of the 42 curriculum by kacherch, anrogard.*

# Pac-Man — Ghosts! More Ghosts!

## Description

This project is a Python implementation of the classic Pac-Man arcade game, built as part of the 42 school curriculum. The goal is to recreate the core experience of the original 1980 Namco arcade title: a player-controlled Pac-Man navigates a maze, collects pac-gums and super pac-gums, avoids (or eats) ghosts, and tries to achieve the highest score possible before time or lives run out.

The game is rendered using the **Arcade** library and is structured as a proper Python package under `src/`. Mazes are procedurally generated using the **A-Maze-ing** (`mazegenerator`) package — a third-party library vendored directly in the repository (version 2.1.0) that produces perfect, connected labyrinths from a given grid size. Configuration is fully externalised to a JSON file, and high scores are persisted across sessions.

Key features:

- Procedurally generated mazes via the `mazegenerator` package
- Multiple ghosts with individual behaviours
- Super pac-gums that temporarily allow Pac-Man to eat ghosts
- Persistent high score system stored as JSON
- Configurable game parameters (grid size, lives, point values, level timer)
- Per-level time limit
- Linting and type-checking toolchain (flake8 + mypy)
- Standalone executable packaged with PyInstaller and published on itch.io

## Instructions

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Kheldin/pacman.git
cd pacman
make install
```

This runs `uv sync`, which reads `pyproject.toml` and installs all required packages into an isolated virtual environment managed by `uv`.

### Running the game

```bash
make run
```

This executes `uv run python3 -m src.pacman config.json`, launching the game with the default configuration file.

### Debug mode

```bash
make debug
```

Runs the game under Python's built-in `pdb` debugger.

### Linting

```bash
make lint          # mypy + flake8 (standard mode)
make lint-strict   # mypy --strict + flake8
```

### Cleaning build artifacts

```bash
make clean
```

Removes `__pycache__`, `.mypy_cache`, `.pytest_cache`, and compiled `.pyc`/`.pyo` files.

## Configuration

The game is configured via a **`config.json`** file at the root of the repository. It is passed as a command-line argument when the game starts (`make run` handles this automatically).

```json
{
  "highscore_filename": "highscore.json",
  "width": 16,
  "height": 16,
  "lives": 5,
  "pacgum": 7,
  "points_per_pacgum": 10,
  "points_per_super_pacgum": 50,
  "points_per_ghost": 200,
  "level_masx_time": 90
}
```

| Key | Type | Default | Description |
|---|---|---|---|
| `highscore_filename` | string | `"highscore.json"` | Path to the file where high scores are persisted. |
| `width` | int | `16` | Number of columns in the maze grid. |
| `height` | int | `16` | Number of rows in the maze grid. |
| `lives` | int | `5` | Number of lives the player starts with. |
| `pacgum` | int | `7` | Number of super pac-gums placed in the maze per level. |
| `points_per_pacgum` | int | `10` | Points awarded for collecting a standard pac-gum. |
| `points_per_super_pacgum` | int | `50` | Points awarded for collecting a super pac-gum. |
| `points_per_ghost` | int | `200` | Points awarded for eating a frightened ghost. |
| `level_masx_time` | int | `90` | Maximum time allowed to complete a level, in seconds. |

To customise the game, edit `config.json` before launching. A different config file can be supplied by passing its path as an argument: `uv run python3 -m src.pacman my_config.json`.

## Highscore

### How it works

High scores are stored in a flat JSON file (path defined by `highscore_filename` in `config.json`, defaulting to `highscore.json`). The structure maps player names to a **list of scores**, allowing multiple sessions per player to be recorded:

```json
{
  "ANTOINE": [1400, 3130],
  "DRILL":   [1570],
  "DSA":     [170]
}
```

When a game session ends, the player is prompted to enter their name. Their final score is appended to the list associated with that name (or a new entry is created). The leaderboard displayed in-game shows the **best score per player**, sorted in descending order.

### Why this approach

A list-per-player design was chosen over storing only the single best score for two reasons. First, it lets players track their own progression over multiple sessions without losing historical data. Second, it keeps the storage format simple and human-readable — a plain JSON dictionary — avoiding the need for a database or any binary format while still supporting all required leaderboard features. Because the file is small and written only at the end of a session, no concurrency handling is needed.

## Maze Generation

Mazes are generated using the **A-Maze-ing** package (`mazegenerator`, version 2.1.0), which is vendored directly in the repository under the `mazegenerator/` directory and `mazegenerator-2.1.0.dist-info/`. Vendoring was chosen to guarantee reproducibility and avoid any dependency on network availability at runtime — the package is available on [PyPI](https://pypi.org/project/mazegenerator/) but is included locally so the game works out of the box after a single `uv sync`.

### How it is used

At the start of each level, the game calls the maze generator with the `width` and `height` values from `config.json`. The package returns a 2D grid representing the maze — a perfect (no loops), connected labyrinth where every cell is reachable. The game layer then post-processes this raw grid to:

1. Place Pac-Man's starting position.
2. Scatter standard pac-gums in every open cell.
3. Place the configured number of super pac-gums (`pacgum` in `config.json`) at specific strategic positions.
4. Designate ghost spawn positions.

Because a new maze is generated each level, no two playthroughs are identical, which increases replayability and prevents players from memorising fixed paths — a deliberate design choice in keeping with the 42 project's spirit of algorithmic thinking.

## Implementation

The game is implemented in Python 3.13 using the **Arcade** library (v3.3.3) for rendering and input handling, and **Pydantic** (v2.13.3) for parsing and validating the `config.json` file at startup.

Core game loop mechanics follow the standard Arcade `on_update` / `on_draw` / `on_key_press` model. Each frame, the game:

1. Updates Pac-Man's position based on current input direction and collision detection against maze walls.
2. Updates each ghost's position according to its individual movement strategy.
3. Checks for collisions between Pac-Man and pac-gums, super pac-gums, and ghosts.
4. Evaluates win/loss conditions (all pac-gums eaten, time expired, or lives exhausted).
5. Draws the maze, entities, HUD (score, lives, timer), and any overlay screens.

Ghost frightened state (triggered by a super pac-gum) is managed with a timer: ghosts switch to a "frightened" mode where they become edible and move slower, reverting to normal after the timer expires.

Maze wall collision uses the grid representation directly — movement is validated cell-by-cell to ensure no entity can pass through a wall tile.

## General Software Architecture

```
pacman/
├── config.json              # Runtime configuration (parsed by Pydantic)
├── highscore.json           # Persistent high scores (written at game end)
├── Makefile                 # Developer workflows: install, run, debug, lint, clean
├── pyproject.toml           # Project metadata & dependency declarations (uv/pip)
├── uv.lock                  # Locked dependency tree for reproducible installs
├── mazegenerator/           # Vendored A-Maze-ing package (maze generation logic)
├── mazegenerator-2.1.0.dist-info/  # Package metadata for the vendored package
└── src/                     # Application source code
    └── pacman/              # Main package (run as `python -m src.pacman`)
        ├── __main__.py      # Entry point: parses args, loads config, starts game
        ├── game.py          # Core Arcade Window/View: game loop, rendering, input
        ├── player.py        # Pac-Man entity: position, animation, movement logic
        ├── ghost.py         # Ghost entity base class: movement, state machine
        ├── maze.py          # Maze representation, wall queries, pac-gum placement
        ├── config.py        # Pydantic model for config.json validation & defaults
        └── highscore.py     # High score read/write logic (JSON persistence)
```

### Key relationships

- `__main__` loads `Config` (via `config.py`), instantiates the Arcade `Window`, and hands control to the game loop.
- `game.py` owns the top-level `on_update` / `on_draw` loop and coordinates all other objects.
- `Maze` is constructed once per level (using `mazegenerator`) and queried by both `Player` and `Ghost` for collision detection.
- `Player` and `Ghost` are independent entity classes that receive a reference to `Maze` and update their positions each frame.
- `HighScore` is read at startup and written when the game ends, decoupled from the game loop.

## Distribution

In addition to running from source, the game is packaged as a standalone executable using **PyInstaller** and published on **[itch.io](https://itch.io)**, so anyone can play it without installing Python or any dependencies.

The PyInstaller spec (`Pacman-42.spec`) bundles the entry point `src/pacman.py`, the `src/assets/` directory, and `config.json` into a self-contained folder named `Pacman-42`. The resulting build can be run directly by double-clicking the executable — no `uv`, no virtual environment, no setup required.

```
Pacman-42/          # produced by PyInstaller COLLECT
├── Pacman-42       # the standalone executable
├── src/assets/     # bundled game assets (sprites, sounds, …)
└── config.json     # default configuration, editable by the player
```

To rebuild the package locally, install PyInstaller (`pip install pyinstaller`) and run:

```bash
pyinstaller Pacman-42.spec
```

The output will be placed under `dist/Pacman-42/`.

## Project Management

The project was managed using GitHub's built-in tools: issues were created using the templates provided under `.github/ISSUE_TEMPLATE/`, and progress was tracked via the repository's Projects board.

A dedicated project management directory can be found at: [https://github.com/Kheldin/pacman/projects](https://github.com/Kheldin/pacman/projects)

Work was broken down into milestones corresponding to the main feature areas (maze generation, entity logic, ghost behaviours, scoring, configuration), with issues assigned and closed as each feature was completed and validated.

## Resources

### Documentation & references

- [Arcade library documentation](https://api.arcade.academy/en/latest/) — Python game framework used for rendering and input.
- [Pydantic v2 documentation](https://docs.pydantic.dev/latest/) — Used for configuration file validation.
- [The Pac-Man Dossier](https://www.gamasutra.com/view/feature/3938/the_pacman_dossier.php) — Exhaustive reverse-engineering of the original Pac-Man arcade ROM, covering ghost AI, timing, and game mechanics.
- [Understanding Pac-Man Ghost Behavior (gameinternals.com)](https://gameinternals.com/understanding-pac-man-ghost-behavior) — Clear explanation of the four classic ghost personalities (Blinky, Pinky, Inky, Clyde).
- [Python `uv` documentation](https://docs.astral.sh/uv/) — Package and environment manager used for dependency management.
- [mazegenerator on PyPI](https://pypi.org/project/mazegenerator/) — The A-Maze-ing package used for procedural maze generation.

### AI usage

Claude (Anthropic) was used as a development aid during this project in the following ways:

- **Architecture discussion:** Exploring how to structure the Arcade-based game loop alongside independent entity classes, and how to cleanly separate configuration, persistence, and game logic into distinct modules.
- **Pydantic model design:** Getting examples of Pydantic v2 models with default values for configuration file parsing.
- **Ghost behaviour research:** Summarising the ghost AI behaviours from the original Pac-Man and how to adapt them to a procedurally generated maze (where fixed target tiles do not apply directly).
- **README drafting:** This README was initially drafted with AI assistance and then reviewed and adjusted to accurately reflect the project's implementation.

AI was **not** used to generate game logic code directly; all implementation decisions and the source code itself were written by the project authors.