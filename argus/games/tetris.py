"""Tetris game widget."""
from __future__ import annotations
import random
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive

TETROMINOES = {
    "I": [[(0,1),(1,1),(2,1),(3,1)], [(2,0),(2,1),(2,2),(2,3)]],
    "O": [[(0,0),(1,0),(0,1),(1,1)]],
    "T": [[(0,1),(1,1),(2,1),(1,0)], [(1,0),(1,1),(1,2),(2,1)],
          [(0,1),(1,1),(2,1),(1,2)], [(1,0),(1,1),(1,2),(0,1)]],
    "S": [[(1,0),(2,0),(0,1),(1,1)], [(1,0),(1,1),(2,1),(2,2)]],
    "Z": [[(0,0),(1,0),(1,1),(2,1)], [(2,0),(1,1),(2,1),(1,2)]],
    "J": [[(0,0),(0,1),(1,1),(2,1)], [(1,0),(2,0),(1,1),(1,2)],
          [(0,1),(1,1),(2,1),(2,2)], [(1,0),(1,1),(0,2),(1,2)]],
    "L": [[(2,0),(0,1),(1,1),(2,1)], [(1,0),(1,1),(1,2),(2,2)],
          [(0,1),(1,1),(2,1),(0,2)], [(0,0),(1,0),(1,1),(1,2)]],
}

COLORS = {"I":"cyan","O":"yellow","T":"magenta","S":"green","Z":"red","J":"blue","L":"bright_red"}

BOARD_W, BOARD_H = 10, 20

class TetrisGame(Widget):
    DEFAULT_CSS = """
    TetrisGame {
        height: 100%;
        align: center middle;
    }
    #tetris-board { border: round $border; width: 24; height: 22; }
    #tetris-info  { width: 24; content-align: center middle; color: $secondary; }
    """
    _score: reactive[int] = reactive(0)
    _level: reactive[int] = reactive(1)

    def compose(self) -> ComposeResult:
        yield Static("", id="tetris-board")
        yield Static("", id="tetris-info")

    def on_mount(self) -> None:
        self._reset()

    def _reset(self) -> None:
        self._board = [[None]*BOARD_W for _ in range(BOARD_H)]
        self._score = 0
        self._level = 1
        self._lines = 0
        self._alive = True
        self._current = None
        self._cx = 0
        self._cy = 0
        self._rot = 0
        self._spawn()
        if hasattr(self, "_timer"):
            self._timer.stop()
        self._timer = self.set_interval(self._speed(), self._tick)

    def _speed(self) -> float:
        return max(0.1, 0.6 - (self._level - 1) * 0.05)

    def _spawn(self) -> None:
        piece = random.choice(list(TETROMINOES.keys()))
        self._current = piece
        self._rot = 0
        self._cx = BOARD_W // 2 - 2
        self._cy = 0
        if not self._valid(self._cx, self._cy, self._rot):
            self._alive = False
            self._render()

    def _cells(self, cx: int, cy: int, rot: int) -> list[tuple[int, int]]:
        shape = TETROMINOES[self._current]
        rot = rot % len(shape)
        return [(cx + dx, cy + dy) for dx, dy in shape[rot]]

    def _valid(self, cx: int, cy: int, rot: int) -> bool:
        for x, y in self._cells(cx, cy, rot):
            if x < 0 or x >= BOARD_W or y >= BOARD_H:
                return False
            if y >= 0 and self._board[y][x] is not None:
                return False
        return True

    def _lock(self) -> None:
        color = COLORS[self._current]
        for x, y in self._cells(self._cx, self._cy, self._rot):
            if 0 <= y < BOARD_H:
                self._board[y][x] = color
        # Clear full lines
        new_board = [row for row in self._board if any(c is None for c in row)]
        cleared = BOARD_H - len(new_board)
        self._board = [[None]*BOARD_W for _ in range(cleared)] + new_board
        self._lines += cleared
        self._score += [0, 100, 300, 500, 800][min(cleared, 4)]
        self._level = self._lines // 10 + 1
        self._spawn()

    def _tick(self) -> None:
        if not self._alive:
            return
        if self._valid(self._cx, self._cy + 1, self._rot):
            self._cy += 1
        else:
            self._lock()
        self._render()

    def _render(self) -> None:
        # Build display board
        display = [list(row) for row in self._board]
        if self._alive and self._current:
            color = COLORS[self._current]
            for x, y in self._cells(self._cx, self._cy, self._rot):
                if 0 <= y < BOARD_H and 0 <= x < BOARD_W:
                    display[y][x] = color
        rows = []
        for row in display:
            line = ""
            for cell in row:
                if cell:
                    line += f"[{cell}]█[/]"
                else:
                    line += "·"
            rows.append(line)
        board_text = "\n".join(rows)
        if not self._alive:
            board_text = "[red bold]GAME OVER[/]\n\n[dim]Press r to restart[/]"
        try:
            self.query_one("#tetris-board", Static).update(board_text)
            self.query_one("#tetris-info", Static).update(
                f"Score: [bold]{self._score}[/]  Level: [bold]{self._level}[/]  "
                f"[dim]←→↓ move  ↑ rotate  Space drop  r restart[/]"
            )
        except Exception:
            pass

    def on_key(self, event) -> None:
        if not self._alive:
            if event.key == "r":
                self._reset()
            return
        if event.key in ("left", "a"):
            if self._valid(self._cx - 1, self._cy, self._rot):
                self._cx -= 1
        elif event.key in ("right", "d"):
            if self._valid(self._cx + 1, self._cy, self._rot):
                self._cx += 1
        elif event.key in ("down", "s"):
            if self._valid(self._cx, self._cy + 1, self._rot):
                self._cy += 1
        elif event.key in ("up", "w"):
            nr = (self._rot + 1) % len(TETROMINOES[self._current])
            if self._valid(self._cx, self._cy, nr):
                self._rot = nr
        elif event.key == "space":
            while self._valid(self._cx, self._cy + 1, self._rot):
                self._cy += 1
            self._lock()
        elif event.key == "r":
            self._reset()
        self._render()
