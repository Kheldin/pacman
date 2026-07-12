import sys
from pydantic import ValidationError
from mazegenerator import MazeGenerator
from src.parser import ConfigParser, PacmanConfig


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("You must provide a valid config json file path", file=sys.stderr)
        sys.exit(1)

    maze = MazeGenerator((15, 15))
    maze.generate()
    parser = ConfigParser("config.json")
    
    try:
        config = parser.parse(PacmanConfig)
        print(config)
    except FileNotFoundError:
        print(f"Error : File '{parser.filepath}' not found.")
    except Exception as e:
        print(f"Error when parsing : {e}")