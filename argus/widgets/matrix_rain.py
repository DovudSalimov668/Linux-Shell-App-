"""Matrix rain screensaver widget."""
from __future__ import annotations
import random
import string
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static

CHARS = string.ascii_letters + string.digits + "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"

class MatrixRainWidget(Widget):
    """Animated matrix rain effect widget."""
    DEFAULT_CSS = """
    MatrixRainWidget {
        background: #000000;
        height: 100%;
        width: 100%;
    }
    #rain-canvas { height: 100%; width: 100%; background: #000000; }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="rain-canvas")

    def on_mount(self) -> None:
        self._cols: list[int] = []   # y position of each column's head
        self._speeds: list[int] = [] # how many ticks before moving
        self._ticks: list[int] = []  # current tick counter
        self._initialized = False
        self.set_interval(0.08, self._tick)

    def _ensure_init(self) -> None:
        try:
            w = max(10, self.size.width)
            h = max(5, self.size.height)
            if not self._initialized or len(self._cols) != w:
                self._cols = [random.randint(-h, 0) for _ in range(w)]
                self._speeds = [random.randint(1, 3) for _ in range(w)]
                self._ticks = [0] * w
                self._h = h
                self._w = w
                self._initialized = True
        except Exception:
            pass

    def _tick(self) -> None:
        self._ensure_init()
        if not self._initialized:
            return

        h, w = self._h, self._w
        # Build grid
        grid = [[(" ", False)] * w for _ in range(h)]

        for col in range(w):
            self._ticks[col] += 1
            if self._ticks[col] >= self._speeds[col]:
                self._ticks[col] = 0
                self._cols[col] += 1
                if self._cols[col] > h + random.randint(5, 20):
                    self._cols[col] = random.randint(-h, -5)
                    self._speeds[col] = random.randint(1, 3)

            head_y = self._cols[col]
            # Draw trail (last 15 chars)
            for i in range(15):
                y = head_y - i
                if 0 <= y < h:
                    ch = random.choice(CHARS)
                    is_head = (i == 0)
                    grid[y][col] = (ch, is_head)

        lines = []
        for row in grid:
            line = ""
            for ch, is_head in row:
                if is_head and ch != " ":
                    line += f"[bold bright_white]{ch}[/]"
                elif ch != " ":
                    line += f"[green]{ch}[/]"
                else:
                    line += " "
            lines.append(line)

        try:
            self.query_one("#rain-canvas", Static).update("\n".join(lines))
        except Exception:
            pass
