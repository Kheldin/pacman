import os
import json
import re
from typing import Any, Dict, List, Tuple

import arcade
import arcade.gui


class HighscoreView(arcade.View):
    """View responsible for displaying and managing the highscores."""

    def __init__(self, config: Any) -> None:
        """Initialize the HighscoreView and its UI components."""
        super().__init__()
        self.config = config

        if isinstance(config, dict):
            self.path: str = config.get("highscore_filename", "scores.json")
        else:
            self.path = getattr(config, "highscore_filename", "scores.json")

        self.highscores: Dict[str, List[int]] = {}
        self.text_objects: List[arcade.Text] = []

        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()

        self.back_button = arcade.gui.UIFlatButton(
            text="MAIN MENU", width=180, height=40
        )
        self.back_button.on_click = self.on_click_back

        anchor_layout = arcade.gui.UIAnchorLayout()
        anchor_layout.add(
            child=self.back_button,
            anchor_x="center_x",
            anchor_y="bottom",
            align_y=30
        )
        self.uimanager.add(anchor_layout)

    def on_click_back(self, event: Any) -> None:
        """Return to the main menu when the back button is clicked."""
        from src.menu_view import MenuView
        menu_view = MenuView(self.config)
        self.window.show_view(menu_view)

    def _is_valid_name(self, name: str) -> bool:
        """Check if the provided name is valid (alphanumeric, 1-10 chars)."""
        if not isinstance(name, str) or not (1 <= len(name) <= 10):
            return False
        return bool(re.match(r"^[a-zA-Z0-9 ]+$", name))

    def _read_file(self) -> None:
        """Read highscores from the JSON file and format them."""
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        valid_scores: Dict[str, List[int]] = {}
                        for name, scores in data.items():
                            if self._is_valid_name(name):
                                if isinstance(scores, int):
                                    valid_scores[name] = [scores]
                                elif isinstance(scores, list):
                                    # Force casting to integer for Mypy
                                    valid_scores[name] = [
                                        int(s) for s in scores
                                        if isinstance(s, (int, float, str))
                                    ]
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

    def _reset_file(self) -> None:
        """Reset the highscore file to an empty JSON object."""
        with open(self.path, "w") as f:
            json.dump({}, f)

    def add_highscore(self, name: str, score: int) -> bool:
        """Add a new highscore for a given player name and save to file."""
        clean_name = name.strip()

        if not self._is_valid_name(clean_name):
            return False

        if clean_name in self.highscores:
            self.highscores[clean_name].append(score)
        else:
            self.highscores[clean_name] = [score]

        with open(self.path, "w") as f:
            json.dump(self.highscores, f, indent=4)

        return True

    def on_show_view(self) -> None:
        """Prepare and format the view before it is displayed."""
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

        all_scores: List[Tuple[str, int]] = []
        for name, scores in self.highscores.items():
            for score in scores:
                all_scores.append((name, score))

        sorted_scores = sorted(
            all_scores, key=lambda item: item[1], reverse=True
        )

        start_y = self.window.height - 140
        line_height = 35

        if not sorted_scores:
            empty_text = arcade.Text(
                "No highscores yet!",
                self.window.width / 2,
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
        """Disable the UI manager when the view is hidden."""
        self.uimanager.disable()

    def on_draw(self) -> None:
        """Render the screen objects."""
        self.clear()

        for text in self.text_objects:
            text.draw()

        self.uimanager.draw()
