"""DashboardScreen — main 3-column grid of placeholder panels."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static

from argus.widgets.clock import ClockWidget
from argus.widgets.statusbar import StatusBar


class PlaceholderPanel(Static):
    """A titled panel with placeholder content."""

    DEFAULT_CSS = """
    PlaceholderPanel {
        border: round #6272a4;
        padding: 0 1;
        height: 100%;
    }
    PlaceholderPanel .panel-title {
        text-style: bold;
        width: 100%;
        content-align: center middle;
        padding-bottom: 1;
    }
    PlaceholderPanel .panel-body {
        color: #6272a4;
        width: 100%;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        title: str,
        body: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._title = title
        self._body = body

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="panel-title")
        yield Label(self._body, classes="panel-body")


class ClockPanel(Static):
    """Panel wrapper for the ClockWidget."""

    DEFAULT_CSS = """
    ClockPanel {
        border: round #6272a4;
        padding: 0 1;
        height: 100%;
    }
    ClockPanel .panel-title {
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

    DEFAULT_CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 3;
        grid-rows: 1fr 1fr 1fr;
        grid-gutter: 1;
        padding: 1 2;
        background: #282a36;
    }
    """

    def compose(self) -> ComposeResult:
        yield PlaceholderPanel(
            " System Monitor",
            "CPU · RAM · Load — coming soon",
            id="panel-system",
        )
        yield PlaceholderPanel(
            " Network",
            "↑ Upload · ↓ Download — coming soon",
            id="panel-network",
        )
        yield PlaceholderPanel(
            " Processes",
            "Top processes by CPU — coming soon",
            id="panel-processes",
        )
        yield PlaceholderPanel(
            " Git",
            "Branch · Status · Log — coming soon",
            id="panel-git",
        )
        yield ClockPanel(id="panel-clock")
        yield PlaceholderPanel(
            " Weather",
            "Conditions · Forecast — coming soon",
            id="panel-weather",
        )
        yield PlaceholderPanel(
            " Notes",
            "Scratch notes — coming soon",
            id="panel-notes",
        )
        yield PlaceholderPanel(
            " Todo",
            "Task list — coming soon",
            id="panel-todo",
        )
        yield PlaceholderPanel(
            " Logs",
            "System logs — coming soon",
            id="panel-logs",
        )
        yield StatusBar()
