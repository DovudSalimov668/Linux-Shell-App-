"""StatusBar — Powerline-style bottom bar for ARGUS."""

from __future__ import annotations

from datetime import datetime

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


# Powerline separators
_SEP_RIGHT = ""   #
_SEP_LEFT  = ""   #
_SEP_THIN  = ""   #


class StatusBar(Widget):
    """Powerline-style status bar docked at the bottom of the screen."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        layout: horizontal;
    }
    StatusBar #sb-left {
        width: auto;
        height: 1;
        content-align: left middle;
    }
    StatusBar #sb-center {
        width: 1fr;
        height: 1;
        content-align: center middle;
    }
    StatusBar #sb-right {
        width: auto;
        height: 1;
        content-align: right middle;
    }
    """

    _clock: reactive[str] = reactive("")
    _theme_name: reactive[str] = reactive("dracula")
    _screen_name: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Static("", id="sb-left")
        yield Static("", id="sb-center")
        yield Static("", id="sb-right")

    def on_mount(self) -> None:
        self._tick()
        self.set_interval(1.0, self._tick)
        self._refresh_left()

    def _tick(self) -> None:
        self._clock = datetime.now().strftime("%H:%M:%S")

    def set_theme(self, theme_name: str) -> None:
        self._theme_name = theme_name

    def set_screen(self, name: str) -> None:
        self._screen_name = name

    def watch__clock(self, value: str) -> None:
        self._refresh_right()

    def watch__theme_name(self, value: str) -> None:
        self._refresh_left()

    def watch__screen_name(self, value: str) -> None:
        self._refresh_left()

    def _refresh_left(self) -> None:
        try:
            left = self.query_one("#sb-left", Static)
            theme_part = f" ● {self._theme_name}"
            screen_part = (
                f"  {_SEP_THIN}  [{self._screen_name}]" if self._screen_name else ""
            )
            hints = (
                f"{theme_part}{screen_part}"
                f"  {_SEP_THIN}  ^T Theme  ^P Palette  ^G Games  ^F Files  ? Help  ^Q Quit "
            )
            left.update(hints)
        except Exception:
            pass

    def _refresh_right(self) -> None:
        try:
            right = self.query_one("#sb-right", Static)
            right.update(f" {self._clock} ")
            center = self.query_one("#sb-center", Static)
            center.update("  ARGUS v0.1.0  ")
        except Exception:
            pass
