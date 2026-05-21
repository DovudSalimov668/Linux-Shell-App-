"""Snake game widget."""
from __future__ import annotations
import random
from collections import deque
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive


class SnakeGame(Widget):
    """Classic Snake game."""

    WIDTH = 30
    HEIGHT = 15

    DEFAULT_CSS = """
    SnakeGame {
        height: 100%;
        align: center middle;
    }
    #snake-board {
        border: round $border;
        width: 62;
        height: 17;
        content-align: center middle;
    }
    #snake-info {
        width: 62;
        content-align: center middle;
        color: $secondary;
    }
    """

    _score: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        yield Static("", id="snake-board")
        yield Static("", id="snake-info")

    def on_mount(self) -> None:
        self._reset()
        self._timer = self.set_interval(0.15, self._tick)

    def _reset(self) -> None:
        cx, cy = self.WIDTH // 2, self.HEIGHT // 2
        self._snake: deque[tuple[int, int]] = deque([(cx, cy), (cx - 1, cy), (cx - 2, cy)])
        self._direction = (1, 0)
        self._next_dir = (1, 0)
        self._score = 0
        self._alive = True
        self._place_food()
        self._render()

    def _place_food(self) -> None:
        snake_set = set(self._snake)
        free = [(x, y) for x in range(self.WIDTH) for y in range(self.HEIGHT) if (x, y) not in snake_set]
        self._food = random.choice(free) if free else (0, 0)

    def _tick(self) -> None:
        if not self._alive:
            return
        self._direction = self._next_dir
        head = self._snake[0]
        new_head = (
            (head[0] + self._direction[0]) % self.WIDTH,
            (head[1] + self._direction[1]) % self.HEIGHT,
        )

        if new_head in self._snake:
            self._alive = False
            self._render()
            return

        self._snake.appendleft(new_head)
        if new_head == self._food:
            self._score += 10
            self._place_food()
        else:
            self._snake.pop()

        self._render()

    def _render(self) -> None:
        snake_set = set(self._snake)
        head = self._snake[0]
        rows = []
        for y in range(self.HEIGHT):
            row = []
            for x in range(self.WIDTH):
                if (x, y) == head:
                    row.append("@")
                elif (x, y) in snake_set:
                    row.append("█")
                elif (x, y) == self._food:
                    row.append("●")
                else:
                    row.append("·")
            rows.append("".join(row))

        board = "\n".join(rows)
        if not self._alive:
            board = f"[red]GAME OVER[/]\nScore: {self._score}\n\n[dim]Press r to restart[/]"

        try:
            self.query_one("#snake-board", Static).update(board)
            self.query_one("#snake-info", Static).update(
                f"Score: {self._score}  [dim]WASD/Arrows to move  r restart[/]"
            )
        except Exception:
            pass

    def on_key(self, event) -> None:
        dirs = {
            "up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0),
            "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
        }
        if event.key in dirs:
            new_dir = dirs[event.key]
            # Prevent reversing
            if (new_dir[0] + self._direction[0], new_dir[1] + self._direction[1]) != (0, 0):
                self._next_dir = new_dir
        elif event.key == "r":
            self._reset()
