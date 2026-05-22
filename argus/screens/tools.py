"""ToolsScreen — tabbed utility hub: shell, calculator, network, notes, pomodoro, clocks."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Label, TabbedContent, TabPane

from argus.widgets.calculator import CalculatorWidget
from argus.widgets.calendar_widget import CalendarWidget
from argus.widgets.network_tools import NetworkToolsWidget
from argus.widgets.notes import NotesWidget
from argus.widgets.pomodoro import PomodoroWidget
from argus.widgets.shell_pane import ShellPane
from argus.widgets.weather import WeatherWidget
from argus.widgets.world_clock import WorldClockWidget


class ToolsScreen(Screen):
    """Tabbed utility hub — shell, calculator, network tools, notes, pomodoro, clocks."""

    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("ctrl+d", "app.navigate('dashboard')", "Dashboard"),
    ]

    DEFAULT_CSS = """
    ToolsScreen {
        background: $background;
    }
    #tools-header {
        height: 3;
        background: $panel;
        padding: 0 2;
        layout: horizontal;
        align: left middle;
        border-bottom: solid $border;
    }
    #tools-header-title {
        width: 1fr;
        color: $primary;
        text-style: bold;
        content-align: left middle;
    }
    #tools-back-btn {
        width: auto;
        min-width: 12;
        height: 3;
    }
    #tools-tabs {
        height: 1fr;
    }
    #tools-footer {
        height: 1;
        background: $surface;
        content-align: center middle;
        color: $foreground;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="tools-header"):
            yield Label("🔧 Tools", id="tools-header-title")
            yield Button("← Back", id="tools-back-btn", variant="default")
        with TabbedContent(id="tools-tabs"):
            with TabPane("Shell", id="tab-shell"):
                yield ShellPane()
            with TabPane("Calculator", id="tab-calc"):
                yield CalculatorWidget()
            with TabPane("Network", id="tab-net"):
                yield NetworkToolsWidget()
            with TabPane("Notes", id="tab-notes"):
                yield NotesWidget()
            with TabPane("Pomodoro", id="tab-pomo"):
                yield PomodoroWidget()
            with TabPane("World Clock", id="tab-clock"):
                yield WorldClockWidget()
            with TabPane("Calendar", id="tab-cal"):
                yield CalendarWidget()
            with TabPane("Weather", id="tab-weather"):
                yield WeatherWidget()
        yield Label(
            "Tab Next tab  Shift+Tab Prev tab  Ctrl+D Dashboard  Esc Back",
            id="tools-footer",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "tools-back-btn":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
