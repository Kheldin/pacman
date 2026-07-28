import os
import json
import re
import arcade
import arcade.gui


class HighscoreView(arcade.View):
    def __init__(self, config): 
        super().__init__()
        self.config = config
        self.path = config.highscore_filename
        self.highscores = {}
        self.text_objects = []

        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()

        self.back_button = arcade.gui.UIFlatButton(text="MAIN MENU", width=180, height=40)
        self.back_button.on_click = self.on_click_back

        anchor_layout = arcade.gui.UIAnchorLayout()
        anchor_layout.add(
            child=self.back_button,
            anchor_x="center_x",
            anchor_y="bottom",
            align_y=30
        )
        self.uimanager.add(anchor_layout)

    def on_click_back(self, event):
        """Return to the main menu."""
        from src.menu_view import MenuView
        menu_view = MenuView(self.config)
        self.window.show_view(menu_view)

    def _is_valid_name(self, name: str) -> bool:
        if not isinstance(name, str) or not (1 <= len(name) <= 10):
            return False
        return bool(re.match(r"^[a-zA-Z0-9 ]+$", name))

    def _is_valid_score(self, score: int) -> bool:
        return isinstance(score, int) and not isinstance(score, bool) and score >= 0

    def _read_file(self):
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        valid_scores = {}
                        for name, score in data.items():
                            if self._is_valid_name(name) and self._is_valid_score(score):
                                valid_scores[name] = score
                        self.highscores = valid_scores
                    else:
                        self.highscores = {}
                        self._reset_file()
            else:
                self.highscores = {}
                self._reset_file()
        except Exception:
            self.highscores = {}
            self._reset_file()

    def _reset_file(self):
        with open(self.path, "w") as f:
            json.dump({}, f)

    def add_highscore(self, name: str, score: int) -> bool:
        """Add a highscore to the highscore file."""
        clean_name = name.strip()

        if not self._is_valid_name(clean_name) or not self._is_valid_score(score):
            return False

        if clean_name in self.highscores:
            self.highscores[clean_name] = max(self.highscores[clean_name], score)
        else:
            self.highscores[clean_name] = score

        with open(self.path, "w") as f:
            json.dump(self.highscores, f, indent=4)
        
        return True

    def on_show_view(self) -> None:
        
        self.uimanager.enable()
        self.window.background_color = arcade.color.DARK_BLUE
        
        self._read_file()
        self.text_objects.clear()

        title_text = arcade.Text(
            "HIGHSCORES", 
            self.window.width / 2, 
            self.window.height - 70,
            arcade.color.YELLOW, 
            font_size=28, 
            anchor_x="center",
            bold=True
        )
        self.text_objects.append(title_text)

        sorted_scores = sorted(self.highscores.items(), key=lambda item: item[1], reverse=True)

        start_y = self.window.height - 140
        line_height = 35

        if not sorted_scores:
            empty_text = arcade.Text(
                "No highscores yet!",
                self.window.height / 2,
                start_y,
                arcade.color.WHITE,
                font_size=16,
                anchor_x="center"
            )
            self.text_objects.append(empty_text)
        else:
            for i, (name, score) in enumerate(sorted_scores[:10]):
                y_pos = start_y - (i * line_height)
                
                entry_text = arcade.Text(
                    f"{i + 1}.  {name.upper()}  -  {score}",
                    self.window.width / 2,
                    y_pos,
                    arcade.color.WHITE,
                    font_size=18,
                    anchor_x="center"
                )
                self.text_objects.append(entry_text)

    def on_hide_view(self) -> None:
        self.uimanager.disable()

    def on_draw(self) -> None:
        self.clear()
        
        for text in self.text_objects:
            text.draw()

        self.uimanager.draw()