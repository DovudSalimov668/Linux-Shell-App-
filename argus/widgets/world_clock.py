"""World clock and stopwatch widget."""
from __future__ import annotations
from datetime import datetime, timezone
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static

WORLD_ZONES = [
    ("UTC",         "UTC"),
    ("New York",    "America/New_York"),
    ("London",      "Europe/London"),
    ("Berlin",      "Europe/Berlin"),
    ("Moscow",      "Europe/Moscow"),
    ("Dubai",       "Asia/Dubai"),
    ("Mumbai",      "Asia/Kolkata"),
    ("Singapore",   "Asia/Singapore"),
    ("Tokyo",       "Asia/Tokyo"),
    ("Sydney",      "Australia/Sydney"),
    ("Los Angeles", "America/Los_Angeles"),
]


class WorldClockWidget(Widget):
    """World clocks with a built-in stopwatch."""
    DEFAULT_CSS = """
    WorldClockWidget {
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    #wc-content { width: 100%; }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="wc-content")

    def on_mount(self) -> None:
        self._sw_running = False
        self._sw_start: float | None = None
        self._sw_elapsed: float = 0.0
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        if self._sw_running:
            pass  # elapsed computed on render
        self._update_display()

    def _update_display(self) -> None:
        now_utc = datetime.now(timezone.utc)
        lines = ["[bold]World Clocks[/]", ""]

        for name, tz_name in WORLD_ZONES:
            try:
                tz = ZoneInfo(tz_name)
                local = now_utc.astimezone(tz)
                time_str = local.strftime("%H:%M")
                date_str = local.strftime("%a %d %b")
                lines.append(f"  [dim]{name:<12}[/] [bold]{time_str}[/]  [dim]{date_str}[/]")
            except (ZoneInfoNotFoundError, Exception):
                lines.append(f"  [dim]{name:<12}[/] [yellow]N/A[/]")

        lines.append("")
        lines.append("[bold]Stopwatch[/]")
        if self._sw_running and self._sw_start:
            elapsed = self._sw_elapsed + (time.time() - self._sw_start)
        else:
            elapsed = self._sw_elapsed

        h = int(elapsed // 3600)
        m = int((elapsed % 3600) // 60)
        s = int(elapsed % 60)
        cs = int((elapsed * 100) % 100)
        state = "[green]▶ Running[/]" if self._sw_running else "[dim]⏸ Paused[/]"
        lines.append(f"  [bold]{h:02d}:{m:02d}:{s:02d}.{cs:02d}[/]  {state}")
        lines.append("  [dim]Space start/stop  r reset[/]")

        try:
            self.query_one("#wc-content", Static).update("\n".join(lines))
        except Exception:
            pass

    def on_key(self, event) -> None:
        if event.key == "space":
            if self._sw_running:
                self._sw_elapsed += time.time() - (self._sw_start or time.time())
                self._sw_running = False
                self._sw_start = None
            else:
                self._sw_start = time.time()
                self._sw_running = True
        elif event.key == "r":
            self._sw_running = False
            self._sw_start = None
            self._sw_elapsed = 0.0
        self._update_display()
