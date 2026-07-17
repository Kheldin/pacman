import sys
import arcade

from pydantic import ValidationError

from mazegenerator import MazeGenerator
from src.parser import ConfigParser, PacmanConfig
from src.logger import log_message, LogType
from src.game import GameView


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Not Pacman"


def main():
    if len(sys.argv) != 2:
        log_message("You must provide a valid config json file path", LogType.ERROR)
        sys.exit(1)
        
    parser = ConfigParser(sys.argv[1])
    try:
        log_message("Parsing config file...", LogType.INFO)
        config = parser.parse(PacmanConfig)
        log_message("Config file successfully parsed !", LogType.SUCCESS)
    except FileNotFoundError:
        log_message(f"Error : File '{parser.filepath}' not found.", LogType.ERROR)
    except ValidationError as e:
        if e.errors():
            log_message(repr(e.errors()[0]['msg']), LogType.ERROR)
        else:
            log_message("Validation Error occurred.", LogType.ERROR)
    except Exception as e:
        log_message(f"Error when parsing : {e}", LogType.ERROR)
    
    # Generate Maze
    maze = MazeGenerator((15, 15))
    maze.generate()
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    window.center_window()
    game = GameView()
    game.setup(maze.maze)

    window.show_view(game)
    window.run()


if __name__ == "__main__":
    main()