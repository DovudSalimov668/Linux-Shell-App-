"""DashboardScreen — main monitoring grid with top navigation bar."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from argus.widgets.clock import ClockWidget
from argus.widgets.cpu_graph import CpuGraphWidget
from argus.widgets.disk_widget import DiskWidget
from argus.widgets.git_panel import GitPanelWidget
from argus.widgets.log_viewer import LogViewerWidget
from argus.widgets.net_monitor import NetMonitorWidget
from argus.widgets.process_table import ProcessTableWidget
from argus.widgets.statusbar import StatusBar
from argus.widgets.system_monitor import SystemMonitorWidget
from argus.widgets.todo import TodoWidget


class LivePanel(Widget):
    """Bordered panel with a title label and a child widget."""

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


class ClockPanel(Widget):
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
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("  Clock", classes="panel-title")
        yield ClockWidget()


class DashboardScreen(Screen):
    """Main dashboard: navigation bar + 3×3 live monitoring grid."""

    BINDINGS = [
        ("ctrl+z", "app.navigate('processes')", "Processes"),
        ("ctrl+x", "app.navigate('git')", "Git"),
        ("ctrl+f", "app.navigate('files')", "Files"),
        ("ctrl+g", "app.navigate('games')", "Games"),
        ("ctrl+w", "app.navigate('tools')", "Tools"),
        ("ctrl+i", "app.navigate('sysinfo')", "SysInfo"),
    ]

    DEFAULT_CSS = """
    DashboardScreen {
        layout: vertical;
        background: $background;
    }

    /* ── top nav bar ─────────────────────────────────────────────────────── */
    #dash-header {
        height: 7;
        background: $panel;
        border-bottom: solid $border;
        layout: vertical;
        padding: 0 2;
    }
    #dash-title-row {
        height: 3;
        layout: horizontal;
        align: left middle;
    }
    #dash-logo {
        color: $primary;
        text-style: bold;
        width: auto;
        content-align: left middle;
        padding: 0 1;
    }
    #dash-subtitle {
        color: $text-muted;
        width: 1fr;
        content-align: left middle;
    }
    #dash-hint {
        color: $text-muted;
        width: auto;
        content-align: right middle;
        padding: 0 1;
    }
    #dash-nav {
        height: 3;
        layout: horizontal;
        align: left middle;
    }
    .nav-btn {
        width: auto;
        min-width: 14;
        margin-right: 1;
        height: 3;
    }
    .nav-btn-accent {
        width: auto;
        min-width: 14;
        margin-right: 1;
        height: 3;
    }

    /* ── monitoring grid ─────────────────────────────────────────────────── */
    #dash-grid {
        height: 1fr;
        layout: grid;
        grid-size: 3;
        grid-rows: 1fr 1fr 1fr;
        grid-gutter: 1;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dash-header"):
            with Horizontal(id="dash-title-row"):
                yield Label("  ARGUS", id="dash-logo")
                yield Label("Terminal Command Center", id="dash-subtitle")
                yield Label("? Help  Ctrl+T Theme  Ctrl+P Palette", id="dash-hint")
            with Horizontal(id="dash-nav"):
                yield Button("⚡ SysInfo",   id="nav-sysinfo",   variant="default",  classes="nav-btn")
                yield Button("🔧 Tools",     id="nav-tools",     variant="default",  classes="nav-btn")
                yield Button("📋 Processes", id="nav-processes", variant="default",  classes="nav-btn")
                yield Button("🔀 Git",       id="nav-git",       variant="default",  classes="nav-btn")
                yield Button("📁 Files",     id="nav-files",     variant="default",  classes="nav-btn")
                yield Button("🎮 Games",     id="nav-games",     variant="success",  classes="nav-btn-accent")
                yield Button("⚙ Settings",  id="nav-settings",  variant="warning",  classes="nav-btn-accent")

        with Vertical(id="dash-grid"):
            # Row 1
            yield LivePanel(" System Monitor",  SystemMonitorWidget(),  id="panel-system")
            yield LivePanel(" CPU Graph",        CpuGraphWidget(),       id="panel-cpugraph")
            yield LivePanel(" Processes",        ProcessTableWidget(),   id="panel-processes")
            # Row 2
            yield LivePanel(" Network",          NetMonitorWidget(),     id="panel-network")
            yield ClockPanel(id="panel-clock")
            yield LivePanel(" Git",              GitPanelWidget(),       id="panel-git")
            # Row 3
            yield LivePanel("  Disk",            DiskWidget(),           id="panel-disk")
            yield LivePanel(" Todo",             TodoWidget(),           id="panel-todo")
            yield LivePanel(" Logs",             LogViewerWidget(),      id="panel-logs")

        yield StatusBar()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        nav_map = {
            "nav-sysinfo":   "sysinfo",
            "nav-tools":     "tools",
            "nav-processes": "processes",
            "nav-git":       "git",
            "nav-files":     "files",
            "nav-games":     "games",
            "nav-settings":  "settings",
        }
        dest = nav_map.get(event.button.id or "")
        if dest:
            self.app.action_navigate(dest)
