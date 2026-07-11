import sys
from pydantic import ValidationError
from pprint import pprint               # Do not forget to delete when the project is done
from mazegenerator import MazeGenerator
from src.models.config import PacmanConfig

def parse_config(path: str) -> PacmanConfig:
    with open("config.json", 'r') as f:
        content = f.read()
        config = PacmanConfig.model_validate_json(content)

if __name__ == "__main__":
    maze = MazeGenerator((15, 15))
    maze.generate()
    if len(sys.argv) != 2:
        print("Only one arg is required: config file path ending with json.", sys.stderr)
    try:
        parse_config(sys.argv[1])
    except ValidationError as e:
        print(e)