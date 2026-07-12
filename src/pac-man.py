import sys

from pydantic import ValidationError

from mazegenerator import MazeGenerator
from src.parser import ConfigParser, PacmanConfig
from src.logger import log_message, LogType

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("You must provide a valid config json file path", file=sys.stderr)
        sys.exit(1)

    maze = MazeGenerator((15, 15))
    maze.generate()
    parser = ConfigParser("config.json")
    
    try:
        log_message("Parsing config file...", LogType.INFO)
        config = parser.parse(PacmanConfig)
        log_message("Config file successfuly parsed !", LogType.SUCCESS)
    except FileNotFoundError:
        log_message(f"Error : File '{parser.filepath}' not found.", LogType.ERROR)
    except ValidationError as e:
        log_message(repr(e.errors()[0]['msg']), LogType.ERROR)
    except Exception as e:
        log_message(f"Error when parsing : {e}", LogType.ERROR)