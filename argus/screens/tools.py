"""ToolsScreen — tabbed utility hub: shell, calculator, network, notes, pomodoro, clocks."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Label, TabbedContent, TabPane

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
        color: $primary;
        text-style: bold;
        content-align: left middle;
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
        yield Label(" Tools", id="tools-header")
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

    def action_go_back(self) -> None:
        self.app.pop_screen()
