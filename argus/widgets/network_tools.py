import asyncio
import socket
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, Label
from textual import work


class NetworkToolsWidget(Widget):
    """Network ping/port-check/IP tools."""

    DEFAULT_CSS = """
    NetworkToolsWidget {
        height: 100%;
        layout: vertical;
        padding: 0 1;
    }
    #net-output {
        height: 1fr;
        overflow-y: auto;
        border: round $border;
        padding: 0 1;
    }
    #net-input-row {
        height: 3;
        layout: horizontal;
    }
    #net-target {
        width: 1fr;
    }
    #net-btn-ping {
        width: 8;
    }
    #net-btn-port {
        width: 8;
    }
    #net-info {
        height: 3;
        color: $text-muted;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="net-output")
        with Static(id="net-input-row"):
            yield Input(placeholder="host or host:port", id="net-target")
            yield Button("Ping", id="net-btn-ping")
            yield Button("Port", id="net-btn-port")
        yield Label("", id="net-info")

    def on_mount(self) -> None:
        self._lines: list[str] = []
        # Show local IP info
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            self._add_line(f"[green]Local IP:[/] {local_ip}")
        except Exception:
            self._add_line("[yellow]Local IP: unknown[/]")

    def _add_line(self, line: str) -> None:
        self._lines.append(line)
        self._lines = self._lines[-50:]
        try:
            self.query_one("#net-output", Static).update("\n".join(self._lines))
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        target = self.query_one("#net-target", Input).value.strip()
        if not target:
            return
        if event.button.id == "net-btn-ping":
            self._do_ping(target)
        elif event.button.id == "net-btn-port":
            self._do_port_check(target)

    @work(exclusive=False)
    async def _do_ping(self, host: str) -> None:
        self._add_line(f"[dim]Pinging {host}...[/]")
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "4", "-W", "2", host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
            for line in stdout.decode().split("\n"):
                if line.strip():
                    self._add_line(f"[green]{line}[/]")
        except asyncio.TimeoutError:
            self._add_line("[red]Ping timeout[/]")
        except Exception as e:
            self._add_line(f"[red]Ping error: {e}[/]")

    @work(exclusive=False)
    async def _do_port_check(self, target: str) -> None:
        host, _, port_str = target.partition(":")
        port = int(port_str) if port_str.isdigit() else 80
        self._add_line(f"[dim]Checking {host}:{port}...[/]")
        try:
            loop = asyncio.get_event_loop()
            conn = loop.create_connection(asyncio.Protocol, host, port)
            transport, _ = await asyncio.wait_for(conn, timeout=5)
            transport.close()
            self._add_line(f"[green]{host}:{port} OPEN[/]")
        except asyncio.TimeoutError:
            self._add_line(f"[yellow]{host}:{port} TIMEOUT[/]")
        except Exception:
            self._add_line(f"[red]{host}:{port} CLOSED/REFUSED[/]")
