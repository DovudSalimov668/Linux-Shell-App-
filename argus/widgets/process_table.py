"""ProcessTableWidget — compact process table for the ARGUS dashboard panel."""

from __future__ import annotations

import psutil
from rich.table import Table
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class ProcessTableWidget(Widget):
    """Compact top-process table suitable for embedding in a dashboard panel.

    Shows the top 8 processes by CPU usage, refreshed every 2 seconds.
    Renders via a Rich Table passed into a Static widget — no DataTable
    overhead, keeps the dashboard light.
    """

    DEFAULT_CSS = """
    ProcessTableWidget {
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="proctable-content")

    def on_mount(self) -> None:
        # Seed cpu_percent so first real reading is meaningful
        psutil.cpu_percent(interval=None)
        self._refresh()
        self.set_interval(2.0, self._refresh)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        """Collect top-8 processes by CPU and render a compact Rich table."""
        procs: list[dict] = []
        attrs = ["pid", "name", "cpu_percent", "memory_percent", "status", "username"]
        for p in psutil.process_iter(attrs):
            try:
                info = p.info
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(key=lambda p: p.get("cpu_percent") or 0.0, reverse=True)
        top = procs[:8]

        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=None,
            padding=(0, 1),
            expand=True,
        )
        table.add_column("PID", style="dim", width=7, no_wrap=True)
        table.add_column("Name", width=18, no_wrap=True)
        table.add_column("CPU%", width=6, justify="right", no_wrap=True)
        table.add_column("MEM%", width=6, justify="right", no_wrap=True)
        table.add_column("Status", width=10, no_wrap=True)

        for p in top:
            cpu = p.get("cpu_percent") or 0.0
            mem = p.get("memory_percent") or 0.0
            name = (p.get("name") or "")[:18]
            status = str(p.get("status") or "")[:10]

            # Colour CPU value
            if cpu >= 60.0:
                cpu_str = f"[red]{cpu:5.1f}[/]"
            elif cpu >= 20.0:
                cpu_str = f"[yellow]{cpu:5.1f}[/]"
            else:
                cpu_str = f"[green]{cpu:5.1f}[/]"

            # Colour MEM value
            if mem >= 20.0:
                mem_str = f"[red]{mem:5.1f}[/]"
            elif mem >= 5.0:
                mem_str = f"[yellow]{mem:5.1f}[/]"
            else:
                mem_str = f"[green]{mem:5.1f}[/]"

            table.add_row(
                str(p.get("pid", "")),
                name,
                cpu_str,
                mem_str,
                status,
            )

        # Show aggregate stats below the table
        try:
            total_procs = len(procs)
            running = sum(
                1 for p in procs if p.get("status") == psutil.STATUS_RUNNING
            )
            summary = (
                f"[dim]Total: [/][cyan]{total_procs}[/]"
                f"[dim]  Running: [/][green]{running}[/]"
            )
        except Exception:
            summary = ""

        content: list[object] = [table]
        if summary:
            content.append(f"\n{summary}")

        try:
            static = self.query_one("#proctable-content", Static)
            # Render table then optional summary line
            from rich.console import Group
            static.update(Group(*content))  # type: ignore[arg-type]
        except Exception:
            pass
