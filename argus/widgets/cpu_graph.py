"""CpuGraphWidget — scrolling braille CPU history graph."""
from __future__ import annotations

from collections import deque

import psutil

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from argus.utils.formatters import braille_sparkline, make_bar


class CpuGraphWidget(Widget):
    """Scrolling braille CPU history graph.

    Keeps the last 120 readings and renders them as a braille sparkline that
    fills the widget width.  Also shows current %, peak %, and a colour bar.
    Updates every second.
    """

    DEFAULT_CSS = """
    CpuGraphWidget {
        height: 100%;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        self._history: deque[float] = deque(maxlen=120)
        self._peak: float = 0.0
        # Seed non-blocking
        psutil.cpu_percent(interval=None)
        self.set_interval(1.0, self._refresh_graph)

    def compose(self) -> ComposeResult:
        yield Static("Initialising…", id="cpugraph-content")

    async def _refresh_graph(self) -> None:
        """Collect one CPU reading and redraw the graph."""
        pct = psutil.cpu_percent(interval=None)
        self._history.append(pct)
        if pct > self._peak:
            self._peak = pct

        # Determine renderable width from widget size; fall back gracefully
        try:
            inner_w = max(10, self.size.width - 4)
        except Exception:
            inner_w = 30

        sparkline = braille_sparkline(list(self._history), width=inner_w)

        # Colour the sparkline based on current load
        if pct < 60.0:
            spark_colour = "green"
        elif pct < 80.0:
            spark_colour = "yellow"
        else:
            spark_colour = "red"

        lines: list[str] = []
        lines.append("[bold]CPU History[/bold]")
        lines.append("")
        lines.append(f"  [{spark_colour}]{sparkline}[/]")
        lines.append("")
        lines.append(
            f"  Current : {make_bar(pct, 20)} [bold]{pct:5.1f}%[/]"
        )
        lines.append(
            f"  Peak    : [dim]{self._peak:5.1f}%[/]"
        )

        # Count logical + physical cores
        try:
            logical = psutil.cpu_count(logical=True) or 1
            physical = psutil.cpu_count(logical=False) or logical
            lines.append("")
            lines.append(
                f"  Cores   : [cyan]{logical}[/] logical  "
                f"[dim]{physical} physical[/]"
            )
        except Exception:
            pass

        # Per-core mini-bars
        try:
            per_core: list[float] = psutil.cpu_percent(interval=None, percpu=True)  # type: ignore[assignment]
            lines.append("")
            lines.append("  Per-core:")
            for i, c_pct in enumerate(per_core):
                mini = make_bar(c_pct, 8)
                lines.append(f"    [{i:>2}] {mini} {c_pct:4.1f}%")
        except Exception:
            pass

        content = "\n".join(lines)
        try:
            self.query_one("#cpugraph-content", Static).update(content)
        except Exception:
            pass
