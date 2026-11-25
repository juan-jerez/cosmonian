from src.game.menu_scene import MenuScene


class InfoScene(MenuScene):
    """Pantalla de solo texto (instrucciones o créditos); cualquier botón vuelve al título."""

    def on_accept(self):
        self.switch_scene("TITLE")

    def on_back(self):
        self.switch_scene("TITLE")
