from typing import Type, TypeVar
from pydantic import BaseModel, Field, field_validator

from src.logger import log_message, LogType


# Type variable to ensure strict type return in parse()
T = TypeVar('T', bound=BaseModel)


class PacmanConfig(BaseModel):
    """Pydantic model representing the game's configuration settings."""

    highscore_filename: str = Field(default="highscore.json")
    width: int = Field(gt=8, default=15)
    height: int = Field(gt=8, default=15)
    lives: int = Field(gt=0, default=3)
    points_per_pacgum: int = Field(ge=0, default=10)
    points_per_super_pacgum: int = Field(ge=0, default=50)
    points_per_ghost: int = Field(ge=0, default=200)
    level_max_time: int = Field(gt=0, default=90)

    @field_validator('highscore_filename')
    @classmethod
    def check_json_extension(cls, path: str) -> str:
        """Ensure the highscore filename ends with .json."""
        if not path.endswith(".json"):
            raise ValueError("Highscore must end with .json")
        return path


class ConfigParser:
    """Handle the parsing and validation of the configuration file."""

    def __init__(self, filepath: str) -> None:
        """Initialize the parser with the given filepath."""
        self.filepath = filepath
        self.comment_prefixes = ('#', '//', '/*', '*')

    def _check_json_extension(self) -> bool:
        """Check if the provided file path has a .json extension."""
        return self.filepath.endswith(".json")

    def _clean_content(self) -> str:
        """Strip # and C/cpp style comments, including inline comments."""
        cleaned_lines = []

        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if '//' in line:
                    line = line.split('//')[0] + '\n'
                if '#' in line:
                    line = line.split('#')[0] + '\n'

                stripped = line.lstrip()
                if stripped.startswith(self.comment_prefixes) or not stripped:
                    continue

                cleaned_lines.append(line)

        return "".join(cleaned_lines)

    def parse(self, model_class: Type[T]) -> T:
        """
        Check extension, clean content, and validate the Pydantic model.
        Logs a warning for any missing fields that fallback to defaults.
        """
        if not self._check_json_extension():
            raise ValueError("You must provide a .json file.")

        content = self._clean_content()
        config = model_class.model_validate_json(content)

        default_fields = (
            set(config.model_fields.keys()) - config.model_fields_set
        )

        for field in default_fields:
            fallback_val = getattr(config, field)
            log_message(
                f"Config parameter '{field}' missing. "
                f"Falling back to default: {fallback_val}",
                LogType.WARNING
            )

        return config
