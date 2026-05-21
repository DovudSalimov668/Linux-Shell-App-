"""Shell command runner pane."""

from __future__ import annotations

import asyncio
import re
from collections import deque

from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Label, Static


# ── Destructive command guard ─────────────────────────────────────────────────
# Patterns that could irreversibly destroy data or the system.
# These require explicit confirmation rather than a hard block (the user owns
# this machine), but we refuse to run them silently.
_DESTROY_PATTERNS = re.compile(
    r"""
    \b(
        rm\s+.*-[a-zA-Z]*r[a-zA-Z]*f   # rm -rf / rm -fr
        | rm\s+.*-[a-zA-Z]*f[a-zA-Z]*r   # rm -fr
        | mkfs\b                          # format filesystem
        | dd\s+.*of=/dev/                 # dd to raw device
        | >\s*/dev/sd                     # redirect to block device
        | shred\b                         # secure delete
        | wipefs\b                        # wipe filesystem
        | :\(\)\{.*\};\s*:               # fork bomb
        | chmod\s+-R\s+[0-7]*0+\s+/     # remove all perms from /
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

_BLOCKED_PATTERNS = re.compile(
    r"""
    \b(
        :\(\)\{.*\};\s*:                 # fork bomb — hard block, not just warn
    )
    """,
    re.VERBOSE,
)


class ShellPane(Widget):
    """Interactive shell command runner.

    Runs commands as the current user inside an async subprocess.
    Destructive patterns trigger a confirmation prompt.
    """

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
    #shell-hint  {
        height: 1;
        dock: bottom;
        color: $text-muted;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="shell-output")
        yield Label(
            "[dim]Enter run  ↑↓ history  runs as your user[/]",
            id="shell-hint",
        )
        yield Input(placeholder="$ enter command…", id="shell-input")

    def on_mount(self) -> None:
        self._lines: deque[str] = deque(maxlen=200)
        self._history: list[str] = []
        self._hist_idx: int = -1
        self._pending_cmd: str | None = None
        self._add_line(
            "[dim]Shell pane — commands run as your user in the current directory.[/]"
        )
        self._add_line("[dim]Type a command and press Enter.[/]")

    # ── Output helpers ────────────────────────────────────────────────────────

    def _add_line(self, line: str) -> None:
        self._lines.append(line)
        try:
            self.query_one("#shell-output", Static).update(
                "\n".join(self._lines)
            )
        except Exception:
            pass

    # ── Input handling ────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return

        # Hard block: fork bomb and similar immediate-doom patterns
        if _BLOCKED_PATTERNS.search(cmd):
            self._add_line(
                f"[bold red]BLOCKED:[/] [red]{cmd}[/]\n"
                "[red]This command is blocked — it would crash or damage the system.[/]"
            )
            event.input.value = ""
            return

        # Soft guard: destructive but user-confirmable
        if _DESTROY_PATTERNS.search(cmd):
            self._pending_cmd = cmd
            self._add_line(
                f"[bold yellow]WARNING:[/] [yellow]{cmd}[/]\n"
                "[yellow]This command looks destructive. "
                "Type [bold]yes[/bold] to confirm, anything else to cancel.[/]"
            )
            event.input.value = ""
            return

        # Check for pending confirmation
        if self._pending_cmd is not None:
            if cmd.lower() == "yes":
                confirmed = self._pending_cmd
                self._pending_cmd = None
                event.input.value = ""
                self._add_line(f"[bold green]$[/] {confirmed}")
                self._run_command(confirmed)
            else:
                self._pending_cmd = None
                self._add_line("[dim]Cancelled.[/]")
                event.input.value = ""
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
                try:
                    self.query_one(Input).value = self._history[-(self._hist_idx + 1)]
                except Exception:
                    pass
        elif event.key == "down":
            if self._hist_idx > 0:
                self._hist_idx -= 1
                try:
                    self.query_one(Input).value = self._history[-(self._hist_idx + 1)]
                except Exception:
                    pass
            elif self._hist_idx == 0:
                self._hist_idx = -1
                try:
                    self.query_one(Input).value = ""
                except Exception:
                    pass

    # ── Async command runner ──────────────────────────────────────────────────

    @work(exclusive=False)
    async def _run_command(self, cmd: str) -> None:
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 64,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                self._add_line("[red]Timeout (30s) — process killed.[/]")
                return

            if stdout:
                for line in stdout.decode("utf-8", errors="replace").splitlines():
                    self._add_line(line)
            if stderr:
                for line in stderr.decode("utf-8", errors="replace").splitlines():
                    self._add_line(f"[red]{line}[/]")
            rc = proc.returncode
            color = "green" if rc == 0 else "red"
            self._add_line(f"[{color}][Exit {rc}][/]")
        except Exception as e:
            self._add_line(f"[red]Error: {e}[/]")
