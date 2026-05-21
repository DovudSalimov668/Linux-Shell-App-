"""ClockWidget — live ASCII-style clock for the dashboard panel."""

from __future__ import annotations

from datetime import datetime

from rich.align import Align
from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class ClockWidget(Widget):
    """A self-updating clock widget displaying time and date."""

    DEFAULT_CSS = """
    ClockWidget {
        align: center middle;
        height: 100%;
        width: 100%;
    }
    ClockWidget #clock-time {
        text-style: bold;
        width: 100%;
        content-align: center middle;
    }
    ClockWidget #clock-date {
        width: 100%;
        content-align: center middle;
    }
    """

    _time: reactive[str] = reactive("")
    _date: reactive[str] = reactive("")

    def on_mount(self) -> None:
        self._tick()
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        now = datetime.now()
        self._time = now.strftime("%H:%M:%S")
        self._date = now.strftime("%A, %B %d %Y")

    def compose(self) -> ComposeResult:
        yield Static("", id="clock-time")
        yield Static("", id="clock-date")

    def watch__time(self, value: str) -> None:
        try:
            time_widget = self.query_one("#clock-time", Static)
            # Build large-ish time display using Rich markup
            time_widget.update(Text(value, style="bold", justify="center"))
        except Exception:
            pass

    def watch__date(self, value: str) -> None:
        try:
            date_widget = self.query_one("#clock-date", Static)
            date_widget.update(Text(value, justify="center"))
        except Exception:
            pass
