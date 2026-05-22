"""DiskWidget — per-mount disk usage panel."""
from __future__ import annotations

import psutil
from rich.markup import escape as mu_escape

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from argus.utils.formatters import fmt_bytes, make_bar


class DiskWidget(Widget):
    """Live disk usage bars for all mounted filesystems."""

    DEFAULT_CSS = """
    DiskWidget {
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="disk-content")

    def on_mount(self) -> None:
        self._refresh()
        self.set_interval(10.0, self._refresh)

    def _refresh(self) -> None:
        lines: list[str] = ["[bold]Disk Usage[/bold]", ""]
        try:
            partitions = psutil.disk_partitions(all=False)
            shown = 0
            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                except (PermissionError, OSError):
                    continue
                pct = usage.percent
                colour = "green" if pct < 70 else ("yellow" if pct < 90 else "red")
                bar = make_bar(pct, 16)
                mount = p.mountpoint if len(p.mountpoint) <= 16 else "…" + p.mountpoint[-15:]
                lines.append(f"  [{colour}]{mount}[/]")
                lines.append(f"  {bar} [{colour}]{pct:.1f}%[/]")
                lines.append(
                    f"  [dim]{fmt_bytes(usage.used)} / {fmt_bytes(usage.total)}[/]"
                )
                lines.append("")
                shown += 1
            if shown == 0:
                lines.append("[dim]No mounted filesystems found[/]")
        except Exception as exc:
            lines.append(f"[red]{mu_escape(str(exc))}[/]")

        # ── I/O stats ─────────────────────────────────────────────────────────
        try:
            io = psutil.disk_io_counters()
            if io:
                lines.append("[bold]I/O Totals[/bold]")
                lines.append(f"  Read  : [cyan]{fmt_bytes(io.read_bytes)}[/]")
                lines.append(f"  Write : [cyan]{fmt_bytes(io.write_bytes)}[/]")
        except Exception:
            pass

        try:
            self.query_one("#disk-content", Static).update("\n".join(lines))
        except Exception:
            pass
