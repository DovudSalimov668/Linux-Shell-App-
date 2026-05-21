"""NetMonitorWidget — live network upload/download meters with sparklines."""
from __future__ import annotations

import socket
import time
from collections import deque

import psutil

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from argus.utils.formatters import braille_sparkline, fmt_bytes, fmt_bytes_rate


class NetMonitorWidget(Widget):
    """Live network upload/download meters with braille sparklines.

    Tracks upload/download rates, total session bytes, active interfaces,
    and local IP.  Updates every second.
    """

    DEFAULT_CSS = """
    NetMonitorWidget {
        height: 100%;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        self._up_history: deque[float] = deque(maxlen=60)
        self._down_history: deque[float] = deque(maxlen=60)
        self._prev_sent: int = 0
        self._prev_recv: int = 0
        self._prev_ts: float = time.monotonic()

        # Seed initial counters
        try:
            net = psutil.net_io_counters()
            self._prev_sent = net.bytes_sent
            self._prev_recv = net.bytes_recv
        except Exception:
            pass

        # Session accumulators
        self._session_sent: float = 0.0
        self._session_recv: float = 0.0

        self.set_interval(1.0, self._refresh_net)

    def compose(self) -> ComposeResult:
        yield Static("Initialising…", id="netmon-content")

    async def _refresh_net(self) -> None:
        """Poll network counters and redraw."""
        now = time.monotonic()
        elapsed = now - self._prev_ts
        self._prev_ts = now

        lines: list[str] = []

        try:
            net = psutil.net_io_counters()
            sent = net.bytes_sent
            recv = net.bytes_recv

            if elapsed > 0:
                up_rate = max(0.0, (sent - self._prev_sent) / elapsed)
                down_rate = max(0.0, (recv - self._prev_recv) / elapsed)
            else:
                up_rate = 0.0
                down_rate = 0.0

            # Accumulate session totals (delta from previous reading)
            self._session_sent += max(0.0, sent - self._prev_sent)
            self._session_recv += max(0.0, recv - self._prev_recv)

            self._prev_sent = sent
            self._prev_recv = recv

            self._up_history.append(up_rate)
            self._down_history.append(down_rate)

            # Compute max for sparkline scale
            up_max = max(1.0, max(self._up_history))
            down_max = max(1.0, max(self._down_history))

            inner_w = 28
            try:
                inner_w = max(10, self.size.width - 4)
            except Exception:
                pass

            up_spark = braille_sparkline(list(self._up_history), width=inner_w, max_val=up_max)
            down_spark = braille_sparkline(list(self._down_history), width=inner_w, max_val=down_max)

            lines.append("[bold]Network[/bold]")
            lines.append("")
            lines.append("  [bold green]↑ Upload[/bold green]")
            lines.append(f"  [green]{up_spark}[/]")
            lines.append(f"  Rate    : [green]{fmt_bytes_rate(up_rate)}[/]")
            lines.append(f"  Session : [dim]{fmt_bytes(int(self._session_sent))}[/]")
            lines.append("")
            lines.append("  [bold cyan]↓ Download[/bold cyan]")
            lines.append(f"  [cyan]{down_spark}[/]")
            lines.append(f"  Rate    : [cyan]{fmt_bytes_rate(down_rate)}[/]")
            lines.append(f"  Session : [dim]{fmt_bytes(int(self._session_recv))}[/]")
            lines.append("")
            lines.append(
                f"  Total ↑ : [dim]{fmt_bytes(sent)}[/]"
            )
            lines.append(
                f"  Total ↓ : [dim]{fmt_bytes(recv)}[/]"
            )

        except Exception as exc:
            lines.append(f"[red]Network error: {exc}[/]")

        # ── Interfaces ────────────────────────────────────────────────────────
        lines.append("")
        lines.append("[bold]Interfaces[/bold]")
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for iface, addr_list in list(addrs.items())[:6]:
                is_up = stats[iface].isup if iface in stats else False
                if not is_up:
                    continue
                for addr in addr_list:
                    if addr.family == socket.AF_INET:
                        lines.append(
                            f"  [cyan]{iface:<10}[/] {addr.address}"
                        )
                        break
        except Exception:
            pass

        # ── Local hostname / IP ───────────────────────────────────────────────
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            lines.append("")
            lines.append(f"  Host    : [dim]{hostname}[/]")
            lines.append(f"  IP      : [cyan]{local_ip}[/]")
        except Exception:
            pass

        content = "\n".join(lines)
        try:
            self.query_one("#netmon-content", Static).update(content)
        except Exception:
            pass
