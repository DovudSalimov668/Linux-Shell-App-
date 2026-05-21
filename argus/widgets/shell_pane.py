"""Shell command runner pane."""
from __future__ import annotations
import asyncio
import subprocess
from collections import deque
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static, Input, Label
from textual import work


class ShellPane(Widget):
    """Interactive shell command runner."""
    DEFAULT_CSS = """
    ShellPane {
        height: 100%;
        layout: vertical;
        padding: 0 1;
    }
    #shell-output {
        height: 1fr;
        overflow-y: auto;
        border: round $border;
        padding: 0 1;
        background: $background;
    }
    #shell-input { height: 3; dock: bottom; }
    #shell-hint  { height: 1; dock: bottom; color: $text-muted; content-align: center middle; }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="shell-output")
        yield Label("[dim]Enter to run  Ctrl+C cancel  ↑↓ history[/]", id="shell-hint")
        yield Input(placeholder="$ enter command...", id="shell-input")

    def on_mount(self) -> None:
        self._lines: deque[str] = deque(maxlen=200)
        self._history: list[str] = []
        self._hist_idx: int = -1
        self._add_line("[dim]Shell ready. Enter commands above.[/]")

    def _add_line(self, line: str) -> None:
        self._lines.append(line)
        try:
            self.query_one("#shell-output", Static).update("\n".join(self._lines))
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return
        self._history.append(cmd)
        self._hist_idx = -1
        event.input.value = ""
        self._add_line(f"[bold green]$[/] {cmd}")
        self._run_command(cmd)

    def on_key(self, event) -> None:
        if event.key == "up":
            if self._history:
                self._hist_idx = min(self._hist_idx + 1, len(self._history) - 1)
                cmd = self._history[-(self._hist_idx + 1)]
                try:
                    self.query_one(Input).value = cmd
                except Exception:
                    pass
        elif event.key == "down":
            if self._hist_idx > 0:
                self._hist_idx -= 1
                cmd = self._history[-(self._hist_idx + 1)]
                try:
                    self.query_one(Input).value = cmd
                except Exception:
                    pass
            elif self._hist_idx == 0:
                self._hist_idx = -1
                try:
                    self.query_one(Input).value = ""
                except Exception:
                    pass

    @work(exclusive=False)
    async def _run_command(self, cmd: str) -> None:
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 64,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            if stdout:
                for line in stdout.decode("utf-8", errors="replace").splitlines():
                    self._add_line(line)
            if stderr:
                for line in stderr.decode("utf-8", errors="replace").splitlines():
                    self._add_line(f"[red]{line}[/]")
            rc = proc.returncode
            color = "green" if rc == 0 else "red"
            self._add_line(f"[{color}][Exit {rc}][/]")
        except asyncio.TimeoutError:
            self._add_line("[red]Timeout (30s)[/]")
        except Exception as e:
            self._add_line(f"[red]Error: {e}[/]")
