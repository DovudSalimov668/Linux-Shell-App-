"""GamesScreen — mini-game launcher for ARGUS."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Label


GAME_LIST = [
    ("Snake",         "Classic snake game",       "snake"),
    ("Game of Life",  "Conway's Game of Life",    "gol"),
    ("Typing Test",   "WPM typing test",          "typing"),
    ("Tetris",        "Block-stacking puzzle",    "tetris"),
    ("2048",          "Sliding number puzzle",    "g2048"),
    ("Minesweeper",   "Mine detection puzzle",    "minesweeper"),
]


class _GameArea(Widget):
    """Container that hosts the active game widget."""

    DEFAULT_CSS = """
    _GameArea {
        width: 1fr;
        height: 1fr;
        border: round $border;
        background: $panel;
        align: center middle;
    }
    """


class GamesScreen(Screen):
    """Full-screen games launcher."""

    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
    ]

    DEFAULT_CSS = """
    GamesScreen {
        layout: vertical;
        background: $background;
    }
    #games-header {
        height: 3;
        background: $panel;
        padding: 0 2;
        color: $primary;
        text-style: bold;
        content-align: left middle;
    }
    #games-body {
        layout: horizontal;
        height: 1fr;
    }
    #games-sidebar {
        width: 36;
        layout: vertical;
        border-right: solid $border;
        padding: 1;
    }
    .game-btn {
        width: 100%;
        margin-bottom: 1;
    }
    #games-main {
        width: 1fr;
        height: 1fr;
        align: center middle;
    }
    #games-footer {
        height: 1;
        background: $surface;
        content-align: center middle;
        color: $foreground;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(" 🎮 Games Launcher", id="games-header")
        with Horizontal(id="games-body"):
            with Vertical(id="games-sidebar"):
                yield Label("[bold]Select a game:[/]")
                for name, desc, gid in GAME_LIST:
                    yield Button(f"{name}", id=f"game-{gid}", classes="game-btn")
            yield _GameArea(id="games-main")
        yield Label(
            "WASD/Arrows move  Space pause  r restart  Esc back",
            id="games-footer",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        gid = event.button.id
        area = self.query_one("#games-main", _GameArea)

        # Remove existing game
        for child in list(area.children):
            child.remove()

        game_map = {
            "game-snake":      ("argus.games.snake",       "SnakeGame"),
            "game-gol":        ("argus.games.game_of_life","GameOfLife"),
            "game-typing":     ("argus.games.typing_test", "TypingTest"),
            "game-tetris":     ("argus.games.tetris",      "TetrisGame"),
            "game-g2048":      ("argus.games.game_2048",   "Game2048"),
            "game-minesweeper":("argus.games.minesweeper", "Minesweeper"),
        }

        if gid not in game_map:
            return

        module_path, class_name = game_map[gid]
        try:
            import importlib
            mod = importlib.import_module(module_path)
            game_cls = getattr(mod, class_name)
            area.mount(game_cls())
        except Exception as e:
            from textual.widgets import Static
            area.mount(Static(f"[red]Could not load game: {e}[/]"))

    def action_go_back(self) -> None:
        self.app.pop_screen()
