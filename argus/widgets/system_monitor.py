"""SystemMonitorWidget — live CPU / RAM / system stats panel."""
from __future__ import annotations

from collections import deque

import psutil

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from argus.utils.formatters import (
    braille_sparkline,
    fmt_bytes,
    fmt_uptime,
    make_bar,
)


class SystemMonitorWidget(Widget):
    """Live CPU / RAM / system stats panel.

    Polls psutil every second.  Keeps a 60-reading history for the CPU
    sparkline.  All output is rendered as Rich markup inside a single Static.
    """

    DEFAULT_CSS = """
    SystemMonitorWidget {
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def on_mount(self) -> None:
        self._history: deque[float] = deque(maxlen=60)
        # Seed with a non-blocking call so the first real poll has a base
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)
        self.set_interval(1.0, self._refresh_stats)

    def compose(self) -> ComposeResult:
        yield Static("Initialising…", id="sysmon-content")

    async def _refresh_stats(self) -> None:
        """Collect psutil data and update the rendered Static."""
        lines: list[str] = []

        # ── Overall CPU ───────────────────────────────────────────────────────
        cpu_total = psutil.cpu_percent(interval=None)
        self._history.append(cpu_total)
        sparkline = braille_sparkline(list(self._history), width=30)

        lines.append("[bold]CPU[/bold]")
        lines.append(
            f"  Overall : {make_bar(cpu_total, 20)} {cpu_total:5.1f}%"
        )
        lines.append(f"  History : [cyan]{sparkline}[/]")

        # ── Per-core CPU ──────────────────────────────────────────────────────
        try:
            per_core: list[float] = psutil.cpu_percent(interval=None, percpu=True)  # type: ignore[assignment]
            lines.append("  Cores   :")
            # Layout cores in two columns if there are many
            for i, pct in enumerate(per_core):
                bar = make_bar(pct, 10)
                lines.append(f"    C{i:<2}  {bar} {pct:5.1f}%")
        except Exception:
            pass

        # ── CPU frequency ─────────────────────────────────────────────────────
        try:
            freq = psutil.cpu_freq()
            if freq:
                lines.append(
                    f"  Freq    : [cyan]{freq.current / 1000:.2f} GHz[/]"
                )
        except Exception:
            pass

        # ── Load average ──────────────────────────────────────────────────────
        try:
            la = psutil.getloadavg()
            lines.append(
                f"  Load    : [green]{la[0]:.2f}[/] [yellow]{la[1]:.2f}[/]"
                f" [red]{la[2]:.2f}[/]  [dim](1m 5m 15m)[/]"
            )
        except AttributeError:
            pass

        lines.append("")

        # ── RAM ───────────────────────────────────────────────────────────────
        vm = psutil.virtual_memory()
        lines.append("[bold]Memory[/bold]")
        lines.append(
            f"  RAM     : {make_bar(vm.percent, 20)} {vm.percent:5.1f}%"
        )
        lines.append(
            f"            {fmt_bytes(vm.used)} / {fmt_bytes(vm.total)}"
        )

        # ── Swap ──────────────────────────────────────────────────────────────
        sw = psutil.swap_memory()
        if sw.total > 0:
            lines.append(
                f"  Swap    : {make_bar(sw.percent, 20)} {sw.percent:5.1f}%"
            )
            lines.append(
                f"            {fmt_bytes(sw.used)} / {fmt_bytes(sw.total)}"
            )

        lines.append("")

        # ── Uptime ────────────────────────────────────────────────────────────
        try:
            import time
            uptime_secs = int(time.time() - psutil.boot_time())
            lines.append(
                f"[bold]Uptime[/bold]  : [cyan]{fmt_uptime(uptime_secs)}[/]"
            )
        except Exception:
            pass

        # ── Temperatures ──────────────────────────────────────────────────────
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                lines.append("")
                lines.append("[bold]Temperatures[/bold]")
                for sensor, entries in list(temps.items())[:3]:
                    for entry in entries[:2]:
                        label = entry.label or sensor
                        t = entry.current
                        colour = "green" if t < 60 else ("yellow" if t < 80 else "red")
                        lines.append(
                            f"  {label[:14]:<14}: [{colour}]{t:.1f}°C[/]"
                        )
        except (AttributeError, Exception):
            pass

        # ── Battery ───────────────────────────────────────────────────────────
        try:
            batt = psutil.sensors_battery()
            if batt is not None:
                plug = "⚡" if batt.power_plugged else "🔋"
                colour = "green" if batt.percent > 40 else ("yellow" if batt.percent > 20 else "red")
                lines.append("")
                lines.append(
                    f"[bold]Battery[/bold] : [{colour}]{batt.percent:.0f}%[/] {plug}"
                )
        except (AttributeError, Exception):
            pass

        content = "\n".join(lines)
        try:
            self.query_one("#sysmon-content", Static).update(content)
        except Exception:
            pass
