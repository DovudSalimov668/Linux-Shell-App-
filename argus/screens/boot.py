"""ARGUS boot screen — animated startup sequence."""

from __future__ import annotations

import pyfiglet
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Label, ProgressBar, Static

BOOT_MESSAGES: list[str] = [
    "Initializing ARGUS core systems...",
    "Loading kernel modules... OK",
    "Mounting system monitors... OK",
    "Starting psutil data workers... OK",
    "Calibrating braille graph renderer... OK",
    "Connecting to network interfaces... OK",
    "Loading theme engine... OK",
    "Scanning git repositories... OK",
    "Initializing process manager... OK",
    "ARGUS v0.1.0 ready.",
]

_TICK_INTERVAL = 0.18   # seconds between boot log steps
_FINISH_DELAY  = 0.5    # seconds after last step before switching screens


class BootScreen(Screen):
    """Animated startup screen shown before the dashboard."""

    BINDINGS = [Binding("*", "skip", "Skip", show=False)]

    DEFAULT_CSS = """
    BootScreen {
        align: center middle;
        background: $background;
    }

    #boot-logo {
        width: 100%;
        content-align: center middle;
        color: $primary;
        text-style: bold;
    }

    #boot-log {
        width: 80%;
        height: 12;
        margin-top: 1;
        color: $secondary;
    }

    #boot-progress {
        width: 60%;
        margin-top: 1;
    }

    #boot-hint {
        color: $text-muted;
        margin-top: 1;
        content-align: center middle;
        width: 100%;
    }
    """

    # ── Compose ───────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        logo = pyfiglet.figlet_format("ARGUS", font="slant")
        yield Static(logo, id="boot-logo")
        yield Static("", id="boot-log")
        yield ProgressBar(total=100, show_eta=False, id="boot-progress")
        yield Static("[dim]Press any key to skip[/]", id="boot-hint")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._step: int = 0
        self._progress: int = 0
        self._log_lines: list[str] = []
        self._done: bool = False
        self.set_interval(_TICK_INTERVAL, self._tick)

    # ── Animation helpers ─────────────────────────────────────────────────────

    def _tick(self) -> None:
        """Advance the boot animation by one step."""
        if self._done:
            return

        step = self._step
        total = len(BOOT_MESSAGES)

        if step < total:
            self._log_lines.append(f"[green]▸[/] {BOOT_MESSAGES[step]}")
            # Keep at most 10 lines visible
            if len(self._log_lines) > 10:
                self._log_lines = self._log_lines[-10:]
            self.query_one("#boot-log", Static).update("\n".join(self._log_lines))

            new_progress = int(((step + 1) / total) * 100)
            delta = new_progress - self._progress
            if delta > 0:
                self.query_one(ProgressBar).advance(delta)
                self._progress = new_progress

        self._step += 1

        if self._step >= total:
            self._finish()

    def _finish(self) -> None:
        """Mark animation complete and schedule the screen transition."""
        if self._done:
            return
        self._done = True
        self.set_timer(_FINISH_DELAY, self._go_dashboard)

    def _go_dashboard(self) -> None:
        from argus.screens.dashboard import DashboardScreen
        self.app.switch_screen(DashboardScreen())

    # ── Input handlers ────────────────────────────────────────────────────────

    def action_skip(self) -> None:
        """Skip the boot animation immediately."""
        self._finish()

    def on_key(self) -> None:
        """Any keypress skips the animation."""
        self._finish()
