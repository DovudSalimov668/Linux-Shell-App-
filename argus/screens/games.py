from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Label, Button
from textual.binding import Binding

GAME_LIST = [
    ("Snake", "Classic snake game", "snake"),
    ("Game of Life", "Conway's Game of Life", "gol"),
    ("Typing Test", "WPM typing test", "typing"),
]


class GamesScreen(Screen):
    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
    ]

    DEFAULT_CSS = """
    GamesScreen {
        layout: vertical;
        align: center middle;
        background: $background;
    }
    #games-title {
        width: 100%;
        content-align: center middle;
        color: $primary;
        text-style: bold;
        height: 3;
    }
    #games-list {
        layout: vertical;
        align: center middle;
        width: 60;
        height: auto;
    }
    .game-btn {
        width: 100%;
        margin: 0 0 1 0;
    }
    #game-area {
        width: 80%;
        height: 1fr;
        border: round $border;
        background: $panel;
    }
    #games-footer {
        height: 1;
        background: $surface;
        content-align: center middle;
        color: $foreground;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(" 🎮 Games Launcher", id="games-title")
        with Static(id="games-list"):
            for name, desc, gid in GAME_LIST:
                yield Button(f"{name} — {desc}", id=f"game-{gid}", classes="game-btn")
        yield Static("", id="game-area")
        yield Label("Esc Back  Arrow/WASD Controls  Space Pause", id="games-footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        gid = event.button.id
        area = self.query_one("#game-area", Static)
        # Unmount any existing game
        for child in list(area.children):
            child.remove()

        if gid == "game-snake":
            from argus.games.snake import SnakeGame
            area.mount(SnakeGame())
        elif gid == "game-gol":
            from argus.games.game_of_life import GameOfLife
            area.mount(GameOfLife())
        elif gid == "game-typing":
            from argus.games.typing_test import TypingTest
            area.mount(TypingTest())

    def action_go_back(self) -> None:
        self.app.pop_screen()
