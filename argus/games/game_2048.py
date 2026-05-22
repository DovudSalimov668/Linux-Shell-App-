"""2048 sliding puzzle widget."""
from __future__ import annotations
import random
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive

class Game2048(Widget):
    DEFAULT_CSS = """
    Game2048 {
        height: 100%;
        align: center middle;
    }
    #g2048-board { border: round $border; width: 36; height: 12; content-align: center middle; }
    #g2048-info  { width: 36; content-align: center middle; color: $secondary; }
    """
    _score: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        yield Static("", id="g2048-board")
        yield Static("", id="g2048-info")

    def on_mount(self) -> None:
        self._reset()

    def _reset(self) -> None:
        self._grid = [[0]*4 for _ in range(4)]
        self._score = 0
        self._won = False
        self._over = False
        self._add_tile()
        self._add_tile()
        self._update_display()

    def _add_tile(self) -> None:
        empty = [(r, c) for r in range(4) for c in range(4) if self._grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self._grid[r][c] = 4 if random.random() < 0.1 else 2

    def _slide_row(self, row: list[int]) -> list[int]:
        nums = [x for x in row if x]
        result = []
        i = 0
        while i < len(nums):
            if i + 1 < len(nums) and nums[i] == nums[i + 1]:
                merged = nums[i] * 2
                result.append(merged)
                self._score += merged
                i += 2
            else:
                result.append(nums[i])
                i += 1
        return result + [0] * (4 - len(result))

    def _move(self, direction: str) -> None:
        old = [row[:] for row in self._grid]
        if direction == "left":
            self._grid = [self._slide_row(r) for r in self._grid]
        elif direction == "right":
            self._grid = [self._slide_row(r[::-1])[::-1] for r in self._grid]
        elif direction == "up":
            cols = [[self._grid[r][c] for r in range(4)] for c in range(4)]
            slid = [self._slide_row(col) for col in cols]
            self._grid = [[slid[c][r] for c in range(4)] for r in range(4)]
        elif direction == "down":
            cols = [[self._grid[r][c] for r in range(4)] for c in range(4)]
            slid = [self._slide_row(col[::-1])[::-1] for col in cols]
            self._grid = [[slid[c][r] for c in range(4)] for r in range(4)]
        if self._grid != old:
            self._add_tile()
        if any(self._grid[r][c] == 2048 for r in range(4) for c in range(4)):
            self._won = True
        if not any(self._grid[r][c] == 0 for r in range(4) for c in range(4)):
            self._over = True

    def _tile_color(self, v: int) -> str:
        colors = {
            0: "dim", 2: "white", 4: "green", 8: "yellow",
            16: "bright_yellow", 32: "orange", 64: "red",
            128: "magenta", 256: "bright_magenta",
            512: "cyan", 1024: "bright_cyan", 2048: "bright_white",
        }
        return colors.get(v, "bold bright_white")

    def _update_display(self) -> None:
        lines = []
        for row in self._grid:
            parts = []
            for v in row:
                c = self._tile_color(v)
                s = str(v) if v else "·"
                parts.append(f"[{c}]{s:>5}[/]")
            lines.append(" ".join(parts))
        board = "\n".join(lines)
        if self._won:
            board += "\n[bold yellow]YOU WIN! 🎉[/]  [dim]Keep going or r to restart[/]"
        if self._over and not self._won:
            board = "[red]GAME OVER[/]\n\n" + board
        try:
            self.query_one("#g2048-board", Static).update(board)
            self.query_one("#g2048-info", Static).update(
                f"Score: [bold]{self._score}[/]  [dim]Arrow keys move  r restart[/]"
            )
        except Exception:
            pass

    def on_key(self, event) -> None:
        if event.key == "r":
            self._reset()
            return
        dir_map = {
            "up": "up", "down": "down", "left": "left", "right": "right",
            "w": "up", "s": "down", "a": "left", "d": "right",
        }
        if event.key in dir_map:
            self._move(dir_map[event.key])
            self._update_display()
