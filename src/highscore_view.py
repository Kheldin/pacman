import arcade
import arcade.gui
import os
import json


class HighscoreView(arcade.View):
    def __init__(self, path: str): 
        super().__init__()
        self.path = path
        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()

        # self.score_list = arcade.gui.

    def _read_file(self):
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r") as f:
                    self.highscores = json.loads(f.read())
            else:
                with open(self.path, "w+") as f:
                    f.write("{}")
                    self.highscores = {}
        except Exception as e:
            with open(self.path, "w+") as f:
                f.write("{}")
                self.highscores = {}
        
        if self.highscores != {}:
            for value in self.highscores.values():
                if not isinstance(value, int):
                    with open(self.path, "w+") as f:
                        f.write("{}")
                        self.highscores = {}

    def on_show_view(self) -> None:
        self._read_file()

    def on_draw(self) -> None:
        from src.pacman import WINDOW_HEIGHT, WINDOW_WIDTH
        self.clear()
        text = arcade.Text(
            "Highscores", WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2,
            arcade.color.YELLOW, font_size=20, anchor_x="center",
            )
        text.draw()
