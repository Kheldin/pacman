import arcade
import arcade.gui
from src.game import GameView
from src.highscore_view import HighscoreView
from src.logger import log_message, LogType
from mazegenerator import MazeGenerator



# button_style = {
#     "bg_color": arcade.color.BLUE,
#     "bg_color_pressed": arcade.color.LIGHT_BLUE,
#     "font_color": arcade.color.WHITE,
#     "border_color": arcade.color.BLACK,
#     "border_width": 2,
# }

class MenuView(arcade.View):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()

        self.start_button = arcade.gui.UIFlatButton(text="Start Game", width=200)
        self.start_button.on_click = self.on_click_start
        self.highscore_button = arcade.gui.UIFlatButton(text="highscores", width=200)
        self.highscore_button.on_click = self.on_click_highscore
        self.exit_button = arcade.gui.UIFlatButton(text="exit", width=200)
        self.exit_button.on_click = self.on_click_exit
        self.instructions_button = arcade.gui.UIFlatButton(text="instructions", width=200)
        self.instructions_button.on_click = self.on_click_instructions

        self.v_box = arcade.gui.UIBoxLayout()
        self.v_box.add(self.start_button)
        self.v_box.add(self.highscore_button)
        self.v_box.add(self.instructions_button)
        self.v_box.add(self.exit_button)

        self.uimanager.add(
            arcade.gui.UIAnchorLayout(children=[self.v_box])
        )

    def on_click_start(self, event) -> None:
        """start a game."""
        from src.pacman import WINDOW_WIDTH, WINDOW_HEIGHT
        maze = MazeGenerator((self.config.width, self.config.height))
        maze.generate()
        game = GameView()
        game.setup(maze.maze, self.config)
        self.uimanager.disable()
        self.window.show_view(game)
        log_message("Game started", log_type=LogType.INFO)


    def on_click_highscore(self, event):
        """Display highscore given in config file."""
        highscore = HighscoreView(self.config.highscore_filename)
        self.window.show_view(highscore)
        log_message("Displaying highscore view.", log_type=LogType.INFO)


    
    def on_click_instructions(self, event):
        """Show controls and instructions."""
        pass

    def on_click_exit(self, event):
        """Quit the game"""
        arcade.exit()


    def on_show_view(self) -> None:
        """Define what happened when we display the view."""
        self.window.background_color = arcade.color.DARK_BLUE
        self.uimanager.enable()

    def on_draw(self) -> None:
        """Draw the view."""
        self.clear()
        # text = arcade.Text(
        #     "Welcome To Pacman2026", WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2,
        #     arcade.color.YELLOW, font_size=20, anchor_x="center",

        # )
        # text.draw()
        self.uimanager.draw()
    
    def on_mouse_press(self, _x, _y, _button, _modifiers):
        pass