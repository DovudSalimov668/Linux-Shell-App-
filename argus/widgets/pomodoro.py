"""PomodoroWidget — Pomodoro timer widget for the ARGUS dashboard."""

from __future__ import annotations

from enum import Enum

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class PomodoroState(Enum):
    IDLE = "idle"
    WORK = "work"
    BREAK = "break"


class PomodoroWidget(Widget):
    """Pomodoro timer widget.

    Keyboard bindings (active when the widget has focus):
      Space  — start / pause
      r      — reset to idle
      n      — skip to next phase immediately
    """

    WORK_DURATION: int = 25 * 60   # 1 500 seconds
    SHORT_BREAK: int = 5 * 60      # 300 seconds
    LONG_BREAK: int = 15 * 60      # 900 seconds

    DEFAULT_CSS = """
    PomodoroWidget {
        height: 100%;
        align: center middle;
        padding: 0 1;
    }
    #pomo-display {
        width: 100%;
        content-align: center middle;
        text-style: bold;
    }
    #pomo-status {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
    }
    #pomo-sessions {
        width: 100%;
        content-align: center middle;
        color: $secondary;
    }
    #pomo-controls {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
    }
    """

    _remaining: reactive[int] = reactive(25 * 60)
    _state: reactive[str] = reactive("idle")
    _sessions: reactive[int] = reactive(0)
    _running: reactive[bool] = reactive(False)

    # ── Compose / mount ───────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static("25:00", id="pomo-display")
        yield Static("IDLE — Press Space to start", id="pomo-status")
        yield Static("Sessions: 0", id="pomo-sessions")
        yield Static("[dim]Space Start/Pause  r Reset  n Next[/]", id="pomo-controls")

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)

    # ── Timer logic ───────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if not self._running:
            return
        if self._remaining > 0:
            self._remaining -= 1
        else:
            self._complete_phase()

    def _complete_phase(self) -> None:
        # System bell
        print("\a", end="", flush=True)
        if self._state == "work":
            self._sessions += 1
            self._state = "break"
            # Long break every 4th session
            self._remaining = (
                self.LONG_BREAK if self._sessions % 4 == 0 else self.SHORT_BREAK
            )
        else:
            self._state = "work"
            self._remaining = self.WORK_DURATION

    # ── Reactive watchers ─────────────────────────────────────────────────────

    def watch__remaining(self, val: int) -> None:
        mins, secs = divmod(val, 60)
        state = self._state
        colour = "green" if state == "work" else ("cyan" if state == "break" else "white")
        try:
            self.query_one("#pomo-display", Static).update(
                f"[bold {colour}]{mins:02d}:{secs:02d}[/]"
            )
        except Exception:
            pass

    def watch__state(self, val: str) -> None:
        try:
            colour = (
                "green" if val == "work" else ("cyan" if val == "break" else "dim")
            )
            label_map = {"work": "WORK", "break": "BREAK", "idle": "IDLE"}
            label = label_map.get(val, val.upper())
            running = self._running
            suffix = "" if running else " — Press Space to start" if val == "idle" else " — Paused"
            self.query_one("#pomo-status", Static).update(
                f"[{colour}]{label}[/]{suffix}"
            )
        except Exception:
            pass

    def watch__sessions(self, val: int) -> None:
        try:
            dots = "🍅" * val
            self.query_one("#pomo-sessions", Static).update(
                f"Sessions: {val} {dots}"
            )
        except Exception:
            pass

    def watch__running(self, val: bool) -> None:
        # Re-trigger state watch to update status label suffix
        self.watch__state(self._state)

    # ── Key handling ──────────────────────────────────────────────────────────

    def on_key(self, event) -> None:
        if event.key == "space":
            self._running = not self._running
            if self._state == "idle":
                self._state = "work"
            event.stop()
        elif event.key == "r":
            self._running = False
            self._state = "idle"
            self._remaining = self.WORK_DURATION
            event.stop()
        elif event.key == "n":
            self._complete_phase()
            event.stop()
