from pydantic import BaseModel, Field, field_validator

class PacmanConfig(BaseModel):
    highscore_filename: str = Field(default="config.json")
    width: int = Field(gt=0, default=15)
    lenght: int = Field(gt=0, default=15)
    lives: int = Field(gt=0, default=4)
    pacgum: int = Field(ge=0, default=10)
    points_per_pacgum: int = Field(ge=0, default=10)
    points_per_super_pacgum: int = Field(ge=0, default=50)
    points_per_ghost: int = Field(ge=0, default=200)
    level_max_time: int = Field(gt=0, default=90)


    @field_validator('highscore_filename')
    @classmethod
    def check_json_extension(cls, path: str) -> str:
        if not path.endswith(".json"):
            raise ValueError("Highscore must end with .json")
        return path

class ConfigParser:
    """Handle the parsing of the config file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.comment_prefixes = ('#', '//', '/*', '*')

    def _check_json_extension(self) -> bool:
        """Check if the user provided a json file."""
        return self.filepath.endswith(".json")

    def _clean_content(self) -> str:
        """Strip # and C/cpp style comment."""
        cleaned_lines = []
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.lstrip()
                if stripped.startswith(self.comment_prefixes):
                    continue
                cleaned_lines.append(line)
                
        return "".join(cleaned_lines)

    def parse(self, model_class: type[BaseModel]) -> BaseModel:
        """Check .json extension and call the PacmanConfig Basemodel"""
        if not self._check_json_extension():
            raise ValueError("You must provide a .json file.")
        content = self._clean_content()
        return dict(model_class.model_validate_json(content))
