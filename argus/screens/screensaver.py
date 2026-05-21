"""Matrix rain screensaver screen — dismissed by any key."""
from __future__ import annotations
import time
from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from argus.widgets.matrix_rain import MatrixRainWidget


class ScreensaverScreen(Screen):
    """Full-screen matrix rain. Any key dismisses it."""

    DEFAULT_CSS = """
    ScreensaverScreen {
        background: #000000;
        layers: below above;
    }
    """

    def compose(self) -> ComposeResult:
        yield MatrixRainWidget()

    def on_key(self, event) -> None:
        event.stop()
        self.app._screensaver_active = False
        self.app._last_activity = time.time()
        self.app.pop_screen()
