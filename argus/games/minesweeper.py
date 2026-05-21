"""Minesweeper widget."""
from __future__ import annotations
import random
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive

class Minesweeper(Widget):
    DEFAULT_CSS = """
    Minesweeper {
        height: 100%;
        align: center middle;
    }
    #ms-board { border: round $border; width: 50; height: 22; }
    #ms-info  { width: 50; content-align: center middle; color: $secondary; }
    """
    ROWS, COLS, MINES = 16, 16, 40

    def compose(self) -> ComposeResult:
        yield Static("", id="ms-board")
        yield Static("", id="ms-info")

    def on_mount(self) -> None:
        self._reset()

    def _reset(self) -> None:
        self._mines: set[tuple[int, int]] = set()
        self._revealed = [[False]*self.COLS for _ in range(self.ROWS)]
        self._flagged  = [[False]*self.COLS for _ in range(self.ROWS)]
        self._counts   = [[0]*self.COLS for _ in range(self.ROWS)]
        self._started  = False
        self._won = False
        self._dead = False
        self._cx = 0
        self._cy = 0
        self._render()

    def _start(self, avoid_r: int, avoid_c: int) -> None:
        # Place mines avoiding the first click cell and its immediate neighbours
        cells = [
            (r, c) for r in range(self.ROWS) for c in range(self.COLS)
            if abs(r - avoid_r) > 1 or abs(c - avoid_c) > 1
        ]
        for r, c in random.sample(cells, min(self.MINES, len(cells))):
            self._mines.add((r, c))
        # Compute adjacency counts
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if (r, c) not in self._mines:
                    self._counts[r][c] = sum(
                        1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                        if (r + dr, c + dc) in self._mines
                    )
        self._started = True

    def _reveal(self, r: int, c: int) -> None:
        if not (0 <= r < self.ROWS and 0 <= c < self.COLS):
            return
        if self._revealed[r][c] or self._flagged[r][c]:
            return
        self._revealed[r][c] = True
        if self._counts[r][c] == 0 and (r, c) not in self._mines:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    self._reveal(r + dr, c + dc)

    def _check_win(self) -> None:
        unrevealed = sum(
            1 for r in range(self.ROWS) for c in range(self.COLS)
            if not self._revealed[r][c]
        )
        if unrevealed == self.MINES:
            self._won = True

    def _render(self) -> None:
        COUNT_COLORS = ["", "blue", "green", "red", "dark_blue", "dark_red", "cyan", "black", "dim"]
        lines = []
        for r in range(self.ROWS):
            row = ""
            for c in range(self.COLS):
                is_cursor = (r == self._cy and c == self._cx)
                if self._dead and (r, c) in self._mines:
                    ch = "[red]✸[/]"
                elif self._revealed[r][c]:
                    if (r, c) in self._mines:
                        ch = "[red bold]✸[/]"
                    elif self._counts[r][c]:
                        col = COUNT_COLORS[min(self._counts[r][c], 8)]
                        ch = f"[{col}]{self._counts[r][c]}[/]"
                    else:
                        ch = "·"
                elif self._flagged[r][c]:
                    ch = "[red]⚑[/]"
                else:
                    ch = "[dim]▪[/]"
                row += f"[reverse]{ch}[/]" if is_cursor else ch
            lines.append(row)
        board = "\n".join(lines)
        flags = sum(self._flagged[r][c] for r in range(self.ROWS) for c in range(self.COLS))
        status = ""
        if self._won:
            status = " [bold green]YOU WIN! 🎉[/]"
        elif self._dead:
            status = " [bold red]BOOM! 💥[/]"
        try:
            self.query_one("#ms-board", Static).update(board)
            self.query_one("#ms-info", Static).update(
                f"💣 {self.MINES - flags}/{self.MINES}  {status}  "
                f"[dim]WASD/Arrows move  Enter reveal  f flag  r restart[/]"
            )
        except Exception:
            pass

    def on_key(self, event) -> None:
        if event.key == "r":
            self._reset()
            return
        if self._won or self._dead:
            return
        move_map = {
            "up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0),
            "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
        }
        if event.key in move_map:
            dx, dy = move_map[event.key]
            self._cx = max(0, min(self.COLS - 1, self._cx + dx))
            self._cy = max(0, min(self.ROWS - 1, self._cy + dy))
        elif event.key == "enter":
            r, c = self._cy, self._cx
            if not self._started:
                self._start(r, c)
            if (r, c) in self._mines:
                self._dead = True
            else:
                self._reveal(r, c)
                self._check_win()
        elif event.key == "f":
            r, c = self._cy, self._cx
            if not self._revealed[r][c]:
                self._flagged[r][c] = not self._flagged[r][c]
        self._render()
