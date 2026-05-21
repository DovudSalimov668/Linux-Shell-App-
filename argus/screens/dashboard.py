"""DashboardScreen — main 3-column grid with live monitoring panels."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Label, Static

from argus.widgets.clock import ClockWidget
from argus.widgets.cpu_graph import CpuGraphWidget
from argus.widgets.git_panel import GitPanelWidget
from argus.widgets.log_viewer import LogViewerWidget
from argus.widgets.net_monitor import NetMonitorWidget
from argus.widgets.process_table import ProcessTableWidget
from argus.widgets.statusbar import StatusBar
from argus.widgets.system_monitor import SystemMonitorWidget
from argus.widgets.todo import TodoWidget
from argus.widgets.weather import WeatherWidget


class LivePanel(Widget):
    """Panel with a title label and a child widget inside a styled border."""

    DEFAULT_CSS = """
    LivePanel {
        border: round $border;
        background: $panel;
        height: 100%;
        padding: 0 1;
    }
    LivePanel .lp-title {
        color: $primary;
        text-style: bold;
        width: 100%;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        title: str,
        child: Widget,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._title = title
        self._child = child

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="lp-title")
        yield self._child


class ClockPanel(Static):
    """Panel wrapper for the ClockWidget."""

    DEFAULT_CSS = """
    ClockPanel {
        border: round $border;
        background: $panel;
        padding: 0 1;
        height: 100%;
    }
    ClockPanel .panel-title {
        color: $primary;
        text-style: bold;
        width: 100%;
        content-align: center middle;
        padding-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("  Clock", classes="panel-title")
        yield ClockWidget()


class DashboardScreen(Screen):
    """Main dashboard screen with a 3-column responsive grid."""

    BINDINGS = [
        ("ctrl+z", "app.navigate('processes')", "Processes"),
        ("ctrl+x", "app.navigate('git')", "Git"),
        ("ctrl+f", "app.navigate('files')", "Files"),
        ("ctrl+g", "app.navigate('games')", "Games"),
    ]

    DEFAULT_CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 3;
        grid-rows: 1fr 1fr 1fr;
        grid-gutter: 1;
        padding: 1 2;
        background: $background;
    }
    """

    def compose(self) -> ComposeResult:
        # Row 1
        yield LivePanel(" System Monitor", SystemMonitorWidget(), id="panel-system")
        yield LivePanel(" CPU Graph", CpuGraphWidget(), id="panel-cpugraph")
        yield LivePanel(" Processes", ProcessTableWidget(), id="panel-processes")
        # Row 2
        yield LivePanel(" Network", NetMonitorWidget(), id="panel-network")
        yield ClockPanel(id="panel-clock")
        yield LivePanel(" Git", GitPanelWidget(), id="panel-git")
        # Row 3
        yield LivePanel(" Weather", WeatherWidget(), id="panel-weather")
        yield LivePanel(" Todo", TodoWidget(), id="panel-todo")
        yield LivePanel(" Logs", LogViewerWidget(), id="panel-logs")
        yield StatusBar()
