"""ProcessScreen — full-screen process manager for ARGUS."""

from __future__ import annotations

import signal

import psutil
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Input, Label, Static


# ── Confirmation dialog ───────────────────────────────────────────────────────

class ConfirmKill(ModalScreen[bool]):
    """Modal confirmation dialog for killing a process."""

    DEFAULT_CSS = """
    ConfirmKill {
        align: center middle;
        background: $background 80%;
    }
    #confirm-box {
        background: $panel;
        border: round $error;
        padding: 2 3;
        width: 52;
        height: 9;
        align: center middle;
    }
    #confirm-label {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #confirm-dim {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        margin-bottom: 1;
    }
    #confirm-buttons {
        layout: horizontal;
        align: center middle;
        width: 100%;
        height: auto;
    }
    #confirm-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, pid: int, name: str) -> None:
        super().__init__()
        self._pid = pid
        self._name = name

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(
                f"[bold red]Kill process {self._pid}?[/]",
                id="confirm-label",
            )
            yield Label(
                f"[dim]{self._name[:40]}[/]",
                id="confirm-dim",
            )
            with Horizontal(id="confirm-buttons"):
                yield Button("Kill", variant="error", id="btn-kill")
                yield Button("Cancel", variant="default", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-kill")


# ── Renice dialog ─────────────────────────────────────────────────────────────

class ReniceDialog(ModalScreen[int | None]):
    """Modal dialog for entering a new nice value."""

    DEFAULT_CSS = """
    ReniceDialog {
        align: center middle;
        background: $background 80%;
    }
    #renice-box {
        background: $panel;
        border: round $primary;
        padding: 2 3;
        width: 52;
        height: 9;
        align: center middle;
    }
    #renice-label {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #renice-input {
        width: 20;
        margin-bottom: 1;
    }
    #renice-buttons {
        layout: horizontal;
        align: center middle;
        width: 100%;
        height: auto;
    }
    #renice-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, pid: int, name: str, current_nice: int) -> None:
        super().__init__()
        self._pid = pid
        self._name = name
        self._current_nice = current_nice

    def compose(self) -> ComposeResult:
        with Vertical(id="renice-box"):
            yield Label(
                f"[bold]Renice: {self._name[:30]} (PID {self._pid})[/]\n"
                f"[dim]Current nice: {self._current_nice}  |  Range: -20 (high) to 19 (low)[/]",
                id="renice-label",
            )
            yield Input(
                placeholder="Nice value (-20 to 19)",
                id="renice-input",
            )
            with Horizontal(id="renice-buttons"):
                yield Button("Apply", variant="primary", id="btn-apply")
                yield Button("Cancel", variant="default", id="btn-cancel")

    def on_mount(self) -> None:
        self.query_one("#renice-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-apply":
            raw = self.query_one("#renice-input", Input).value.strip()
            try:
                val = int(raw)
                val = max(-20, min(19, val))
                self.dismiss(val)
            except ValueError:
                self.app.notify("Invalid nice value — must be -20 to 19", severity="error")
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:  # noqa: D401
        """Submit on Enter key inside the input field."""
        self.query_one("#btn-apply", Button).press()


# ── Process Screen ────────────────────────────────────────────────────────────

class ProcessScreen(Screen):
    """Full-screen sortable/filterable process manager."""

    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("k", "kill_process", "Kill"),
        Binding("r", "renice_process", "Renice"),
        Binding("f", "filter_focus", "Filter"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("t", "toggle_tree", "Tree"),
    ]

    DEFAULT_CSS = """
    ProcessScreen {
        layout: vertical;
        background: $background;
    }
    #proc-header {
        height: 3;
        background: $panel;
        padding: 0 2;
        layout: horizontal;
        align: left middle;
    }
    #proc-title {
        width: auto;
        content-align: left middle;
        color: $primary;
        text-style: bold;
        margin-right: 2;
    }
    #proc-filter {
        width: 36;
        margin: 0 1;
    }
    #proc-info {
        width: 1fr;
        content-align: right middle;
        color: $text-muted;
        margin: 0 2;
    }
    #proc-table {
        height: 1fr;
        border: round $border;
        margin: 0 1;
    }
    #proc-footer {
        height: 1;
        background: $surface;
        color: $foreground;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="proc-header"):
            yield Label(" ⚙ Process Manager", id="proc-title")
            yield Input(placeholder="Filter processes...", id="proc-filter")
            yield Label("", id="proc-info")
        table = DataTable(id="proc-table", zebra_stripes=True, cursor_type="row")
        table.add_columns("PID", "Name", "CPU%", "MEM%", "Status", "User")
        yield table
        yield Label(
            "k Kill  r Renice  f Filter  t Tree  Ctrl+R Refresh  Esc/q Back",
            id="proc-footer",
        )

    def on_mount(self) -> None:
        self._sort_col: str = "cpu"
        self._sort_reverse: bool = True
        self._filter: str = ""
        self._tree_mode: bool = False
        self._refresh_data()
        self.set_interval(2.0, self._refresh_data)

    # ── Data loading ──────────────────────────────────────────────────────────

    def _refresh_data(self) -> None:
        table = self.query_one(DataTable)
        table.clear()

        procs: list[dict] = []
        attrs = ["pid", "name", "cpu_percent", "memory_percent", "status", "username"]
        for p in psutil.process_iter(attrs):
            try:
                info = p.info
                name = info.get("name") or ""
                if self._filter and self._filter.lower() not in name.lower():
                    continue
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(key=lambda p: p.get("cpu_percent") or 0.0, reverse=True)

        for p in procs[:200]:
            cpu = p.get("cpu_percent") or 0.0
            mem = p.get("memory_percent") or 0.0
            cpu_color = "green" if cpu < 20 else ("yellow" if cpu < 60 else "red")
            mem_color = "green" if mem < 5 else ("yellow" if mem < 20 else "red")
            table.add_row(
                str(p.get("pid", "")),
                (p.get("name") or "")[:30],
                f"[{cpu_color}]{cpu:5.1f}[/]",
                f"[{mem_color}]{mem:5.1f}[/]",
                str(p.get("status") or ""),
                (p.get("username") or "")[:15],
            )

        # Update info label
        try:
            total = len(list(psutil.process_iter()))
            shown = min(len(procs), 200)
            self.query_one("#proc-info", Label).update(
                f"{shown}/{total} processes"
            )
        except Exception:
            pass

    # ── Input handlers ────────────────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "proc-filter":
            self._filter = event.value
            self._refresh_data()

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self._refresh_data()

    def action_filter_focus(self) -> None:
        self.query_one("#proc-filter", Input).focus()

    def action_toggle_tree(self) -> None:
        self._tree_mode = not self._tree_mode
        mode = "tree" if self._tree_mode else "flat"
        self.app.notify(f"Process view: {mode} (tree view is visual-only in this phase)", timeout=2)
        self._refresh_data()

    def _get_cursor_pid_and_name(self) -> tuple[int, str] | None:
        """Return (pid, name) for the currently highlighted row, or None."""
        table = self.query_one(DataTable)
        row_idx = table.cursor_row
        if row_idx < 0:
            return None
        try:
            row = table.get_row_at(row_idx)
            # row[0] is the PID cell (may contain Rich markup — strip it)
            pid_raw = str(row[0])
            pid = int(pid_raw.strip())
            name_raw = str(row[1])
            return pid, name_raw
        except Exception:
            return None

    def action_kill_process(self) -> None:
        result = self._get_cursor_pid_and_name()
        if result is None:
            return
        pid, name = result

        def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                try:
                    psutil.Process(pid).kill()
                    self.app.notify(f"Killed PID {pid} ({name})", severity="warning")
                except psutil.NoSuchProcess:
                    self.app.notify(f"PID {pid} no longer exists", severity="warning")
                except psutil.AccessDenied:
                    self.app.notify(f"Permission denied: cannot kill PID {pid}", severity="error")
                except Exception as exc:
                    self.app.notify(f"Failed: {exc}", severity="error")
                self._refresh_data()

        self.app.push_screen(ConfirmKill(pid, name), _on_confirm)

    def action_renice_process(self) -> None:
        result = self._get_cursor_pid_and_name()
        if result is None:
            return
        pid, name = result

        try:
            current_nice = psutil.Process(pid).nice()
        except Exception:
            current_nice = 0

        def _on_value(nice_val: int | None) -> None:
            if nice_val is None:
                return
            try:
                psutil.Process(pid).nice(nice_val)
                self.app.notify(f"Reniced PID {pid} to {nice_val}", severity="information")
            except psutil.AccessDenied:
                self.app.notify(f"Permission denied: cannot renice PID {pid}", severity="error")
            except psutil.NoSuchProcess:
                self.app.notify(f"PID {pid} no longer exists", severity="warning")
            except Exception as exc:
                self.app.notify(f"Renice failed: {exc}", severity="error")
            self._refresh_data()

        self.app.push_screen(ReniceDialog(pid, name, current_nice), _on_value)
