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