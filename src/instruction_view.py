import arcade
import arcade.gui


class InstructionView(arcade.View):
    def __init__(self, config):
        super().__init__()
        self.config = config
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

    def on_show_view(self) -> None:
        self.uimanager.enable()
        self.window.background_color = arcade.color.DARK_BLUE
        
        self.text_objects.clear()
        title_text = arcade.Text(
            "HOW TO PLAY", 
            self.window.width / 2, 
            self.window.height - 70,
            arcade.color.YELLOW, 
            font_size=28, 
            anchor_x="center",
            bold=True
        )
        self.text_objects.append(title_text)

        rules_title = arcade.Text(
            "RULES:", 
            self.window.width / 2, 
            self.window.height - 150,
            arcade.color.LIGHT_BLUE, 
            font_size=22, 
            anchor_x="center",
            bold=True
        )
        self.text_objects.append(rules_title)

        rules = [
            "• Eat all the dots to clear the maze.",
            "• Avoid the ghosts at all costs!",
            "• Eat a Power Pellet to turn ghosts blue",
            "  and eat them for extra points."
        ]
        start_y = self.height - 190
        for i, rule in enumerate(rules):
            rule_text = arcade.Text(
                rule,
                self.window.width / 2,
                start_y - (i * 35),
                arcade.color.WHITE,
                font_size=18,
                anchor_x="center"
            )
            self.text_objects.append(rule_text)

        controls_title = arcade.Text(
            "CONTROLS:", 
            self.window.width / 2, 
            start_y - 170,
            arcade.color.LIGHT_BLUE, 
            font_size=22, 
            anchor_x="center",
            bold=True
        )
        self.text_objects.append(controls_title)

        controls_text = arcade.Text(
            "Use ARROW KEYS to move",
            self.window.width / 2,
            start_y - 210,
            arcade.color.WHITE,
            font_size=18,
            anchor_x="center"
        )
        self.text_objects.append(controls_text)
        
        arrows_detail = arcade.Text(
            "( UP, DOWN, LEFT, RIGHT )",
            self.window.width / 2,
            start_y - 240,
            arcade.color.GRAY,
            font_size=14,
            anchor_x="center"
        )
        self.text_objects.append(arrows_detail)

    def on_hide_view(self) -> None:
        """Disable UIManager when leaving this view."""
        self.uimanager.disable()

    def on_draw(self) -> None:
        self.clear()
        
        for text in self.text_objects:
            text.draw()

        self.uimanager.draw()