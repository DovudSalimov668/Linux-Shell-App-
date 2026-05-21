from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static, Label
from pathlib import Path
from collections import deque


class LogViewerWidget(Widget):
    """Live log file tail viewer."""

    DEFAULT_CSS = """
    LogViewerWidget {
        height: 100%;
        padding: 0 1;
    }
    #log-content {
        height: 1fr;
        overflow-y: auto;
    }
    #log-file-label {
        height: 1;
        color: $text-muted;
        content-align: center middle;
    }
    """

    LOG_FILES = [
        "/var/log/syslog",
        "/var/log/kern.log",
        "/var/log/auth.log",
        "/var/log/messages",
    ]

    def compose(self) -> ComposeResult:
        yield Label("No log file loaded", id="log-file-label")
        yield Static("", id="log-content")

    def on_mount(self) -> None:
        self._log_path: Path | None = None
        self._lines: deque[str] = deque(maxlen=100)
        self._file_pos: int = 0

        # Try to find a readable log file
        for lf in self.LOG_FILES:
            p = Path(lf)
            if p.exists() and p.is_file():
                self._log_path = p
                break

        if self._log_path:
            self._load_tail()
            self.set_interval(2.0, self._poll_new_lines)

    def _load_tail(self) -> None:
        if not self._log_path:
            return
        try:
            with open(self._log_path, "rb") as f:
                # Read last 4KB
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - 4096))
                data = f.read().decode("utf-8", errors="replace")
                self._file_pos = size
                lines = data.split("\n")[-50:]
                for line in lines:
                    if line.strip():
                        self._lines.append(self._colorize(line))
            self._update_display()
            self.query_one("#log-file-label", Label).update(f"[dim]{self._log_path}[/]")
        except Exception as e:
            self.query_one("#log-content", Static).update(f"[yellow]Cannot read log: {e}[/]")

    def _poll_new_lines(self) -> None:
        if not self._log_path:
            return
        try:
            with open(self._log_path, "rb") as f:
                f.seek(self._file_pos)
                data = f.read().decode("utf-8", errors="replace")
                self._file_pos = f.tell()
            for line in data.split("\n"):
                if line.strip():
                    self._lines.append(self._colorize(line))
            if data.strip():
                self._update_display()
        except Exception:
            pass

    def _colorize(self, line: str) -> str:
        lower = line.lower()
        if any(w in lower for w in ("error", "fail", "critical", "crit")):
            return f"[red]{line}[/]"
        elif any(w in lower for w in ("warn", "warning")):
            return f"[yellow]{line}[/]"
        elif any(w in lower for w in ("info", "notice")):
            return f"[green]{line}[/]"
        return f"[dim]{line}[/]"

    def _update_display(self) -> None:
        try:
            self.query_one("#log-content", Static).update("\n".join(self._lines))
        except Exception:
            pass
