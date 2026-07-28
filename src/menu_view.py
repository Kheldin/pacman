import arcade
import arcade.gui
from src.game import GameView
from src.highscore_view import HighscoreView
from src.logger import log_message, LogType
from mazegenerator import MazeGenerator


class MenuView(arcade.View):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()

        arcade.load_font("src/assets/Pacmania.ttf")

        self.pacman_list = arcade.SpriteList()
        self.pacgum_list = arcade.SpriteList()
        
        pacman_sheet = arcade.load_spritesheet("src/assets/PacManAssets-PacMan.png")
        self.pacman_textures = pacman_sheet.get_texture_grid(size=(32, 32), columns=4, count=4)
        
        self.giant_pacman = arcade.Sprite(scale=8.0)
        self.giant_pacman.texture = self.pacman_textures[0]
        self.giant_pacman.center_y = 150
        self.giant_pacman.right = 0
        self.pacman_list.append(self.giant_pacman)
        
        self.pacman_frame = 0
        self.time_since_last_frame = 0.0

        item_base_texture = arcade.load_texture("src/assets/PacManAssets-Items.png")
        self.pacgum_texture = item_base_texture.crop(0, 16, 16, 16)
        
        self.spawn_gums()

        button_style = {
            "normal": {
                "font_name": "Pacmania",
                "font_size": 14,
                "font_color": arcade.color.YELLOW,
                "bg_color": arcade.color.BLACK,
                "border_color": arcade.color.BLUE_SAPPHIRE,
                "border_width": 2,
            },
            "hover": {
                "font_name": "Pacmania",
                "font_size": 14,
                "font_color": arcade.color.WHITE,
                "bg_color": arcade.color.BLUE_SAPPHIRE,
                "border_color": arcade.color.YELLOW,
                "border_width": 2,
            },
            "press": {
                "font_name": "Pacmania",
                "font_size": 14,
                "font_color": arcade.color.BLACK,
                "bg_color": arcade.color.YELLOW,
                "border_color": arcade.color.YELLOW,
                "border_width": 2,
            }
        }

        self.start_button = arcade.gui.UIFlatButton(text="START GAME", width=250, style=button_style)
        self.start_button.on_click = self.on_click_start
        
        self.highscore_button = arcade.gui.UIFlatButton(text="HIGHSCORES", width=250, style=button_style)
        self.highscore_button.on_click = self.on_click_highscore
        
        self.instructions_button = arcade.gui.UIFlatButton(text="INSTRUCTIONS", width=250, style=button_style)
        self.instructions_button.on_click = self.on_click_instructions

        self.exit_button = arcade.gui.UIFlatButton(text="EXIT", width=250, style=button_style)
        self.exit_button.on_click = self.on_click_exit
        
        self.v_box = arcade.gui.UIBoxLayout(space_between=15)
        self.v_box.add(self.start_button)
        self.v_box.add(self.highscore_button)
        self.v_box.add(self.instructions_button)
        self.v_box.add(self.exit_button)

        self.uimanager.add(arcade.gui.UIAnchorLayout(children=[self.v_box]))

    def spawn_gums(self):
        self.pacgum_list.clear()
        for x in range(100, 2500, 150):
            gum = arcade.Sprite(self.pacgum_texture, scale=3.0)
            gum.center_x = x
            gum.center_y = 150
            self.pacgum_list.append(gum)

    def on_click_start(self, event) -> None:
        """start a game."""
        from src.pacman import WINDOW_WIDTH, WINDOW_HEIGHT

        maze = MazeGenerator((self.config.width, self.config.height))
        maze.generate()
        game = GameView()
        print(maze.maze)
        game.setup(maze.maze, self.config)
        self.window.show_view(game)
        log_message("Game started", log_type=LogType.INFO)

    def on_click_highscore(self, event):
        """Display highscore given in config file."""
        highscore = HighscoreView(self.config)
        self.window.show_view(highscore)
        log_message("Displaying highscore view.", log_type=LogType.INFO)

    def on_click_instructions(self, event):
        """Show controls and instructions."""
        from src.instruction_view import InstructionView
        instruction_view = InstructionView(self.config)
        self.window.show_view(instruction_view)
        log_message("Displaying instructions view.", log_type=LogType.INFO)

    def on_click_exit(self, event):
        """Quit the game"""
        arcade.exit()

    def on_show_view(self) -> None:
        """Define what happened when we display the view."""
        self.window.background_color = arcade.color.BLACK

    def on_hide_view(self) -> None:
        """Define what happened when we hide the view."""
        self.uimanager.disable()

    def on_update(self, delta_time: float):
        """Logique d'animation et de déplacement."""
        # Animation de la bouche
        self.time_since_last_frame += delta_time
        if self.time_since_last_frame >= 0.08:
            self.time_since_last_frame = 0.0
            self.pacman_frame = (self.pacman_frame + 1) % len(self.pacman_textures)
            self.giant_pacman.texture = self.pacman_textures[self.pacman_frame]

        # Déplacement horizontal
        self.giant_pacman.center_x += 250 * delta_time

        # Disparition des Pac-Gums
        gums_hit = arcade.check_for_collision_with_list(self.giant_pacman, self.pacgum_list)
        for gum in gums_hit:
            gum.remove_from_sprite_lists()

        # Réinitialisation quand Pac-Man sort de l'écran
        if self.giant_pacman.left > self.window.width:
            self.giant_pacman.right = -100
            self.spawn_gums()

    def on_draw(self) -> None:
        """Draw the view."""
        self.clear()
        
        # Dessin des sprites décoratifs
        self.pacgum_list.draw()
        self.pacman_list.draw()
        
        arcade.draw_text(
            "PACMAN 2026", 
            self.window.width / 2, 
            self.window.height - 150,
            arcade.color.YELLOW, 
            font_size=40, 
            anchor_x="center",
            font_name="Pacmania"
        )
        self.uimanager.draw()