"""Conway's Game of Life widget."""
from __future__ import annotations
import random
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive


class GameOfLife(Widget):
    """Conway's Game of Life."""

    WIDTH = 50
    HEIGHT = 25

    DEFAULT_CSS = """
    GameOfLife {
        height: 100%;
        align: center middle;
    }
    #gol-board {
        width: 52;
        height: 27;
        border: round $border;
        content-align: center middle;
    }
    #gol-info {
        width: 52;
        content-align: center middle;
        color: $text-muted;
    }
    """

    _generation: reactive[int] = reactive(0)
    _running: reactive[bool] = reactive(True)

    def compose(self) -> ComposeResult:
        yield Static("", id="gol-board")
        yield Static("", id="gol-info")

    def on_mount(self) -> None:
        self._randomize()
        self.set_interval(0.1, self._step)

    def _randomize(self) -> None:
        self._grid = [[random.random() < 0.3 for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
        self._generation = 0

    def _step(self) -> None:
        if not self._running:
            return
        new_grid = []
        for y in range(self.HEIGHT):
            row = []
            for x in range(self.WIDTH):
                neighbors = sum(
                    self._grid[(y + dy) % self.HEIGHT][(x + dx) % self.WIDTH]
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                    if (dy, dx) != (0, 0)
                )
                alive = self._grid[y][x]
                row.append(neighbors == 3 or (alive and neighbors == 2))
            new_grid.append(row)
        self._grid = new_grid
        self._generation += 1
        self._update_display()

    def _update_display(self) -> None:
        rows = []
        for y in range(self.HEIGHT):
            row = "".join("█" if self._grid[y][x] else " " for x in range(self.WIDTH))
            rows.append(row)
        try:
            self.query_one("#gol-board", Static).update("\n".join(rows))
            state = "▶ Running" if self._running else "⏸ Paused"
            self.query_one("#gol-info", Static).update(
                f"Gen {self._generation}  {state}  [dim]Space pause  r random  c clear[/]"
            )
        except Exception:
            pass

    def on_key(self, event) -> None:
        if event.key == "space":
            self._running = not self._running
        elif event.key == "r":
            self._randomize()
        elif event.key == "c":
            self._grid = [[False] * self.WIDTH for _ in range(self.HEIGHT)]
            self._generation = 0
