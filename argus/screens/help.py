"""ARGUS help overlay screen — full-screen keybindings reference."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Label
from textual.binding import Binding

KEYBINDINGS = [
    ("Global", [
        ("Ctrl+Q", "Quit ARGUS"),
        ("Ctrl+T", "Cycle through themes"),
        ("Ctrl+P", "Open command palette"),
        ("Ctrl+G", "Open games launcher"),
        ("Ctrl+F", "Open file explorer"),
        ("Ctrl+W", "Open tools (shell, calc, network, notes…)"),
        ("Ctrl+D", "Go back to dashboard"),
        ("Ctrl+Z", "Open process manager"),
        ("Ctrl+X", "Open git dashboard"),
        ("Ctrl+S", "Open settings"),
        ("?", "Toggle this help overlay"),
    ]),
    ("Navigation", [
        ("↑ ↓ j k", "Move cursor / scroll"),
        ("Enter", "Select / confirm"),
        ("Escape / q", "Go back / close"),
        ("Tab", "Next focusable widget"),
        ("Shift+Tab", "Previous focusable widget"),
    ]),
    ("Tools Screen  (Ctrl+W)", [
        ("Tab / Shift+Tab", "Switch between tool tabs"),
    ]),
    ("Process Manager", [
        ("k", "Kill selected process"),
        ("r", "Renice selected process"),
        ("f", "Focus filter input"),
        ("Ctrl+R", "Force refresh"),
    ]),
    ("File Explorer", [
        ("/", "Focus search"),
        ("d", "Delete selected"),
        ("n", "New directory"),
    ]),
    ("Git", [
        ("p", "Pull"),
        ("P", "Push"),
        ("Ctrl+R", "Refresh"),
    ]),
    ("Pomodoro", [
        ("Space", "Start / pause"),
        ("r", "Reset timer"),
        ("n", "Skip to next phase"),
    ]),
    ("Snake", [
        ("W A S D / Arrows", "Move"),
        ("r", "Restart"),
    ]),
    ("Game of Life", [
        ("Space", "Pause / resume"),
        ("r", "Randomize"),
        ("c", "Clear board"),
    ]),
]


class HelpScreen(Screen):
    BINDINGS = [
        Binding("escape,question_mark,q", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
        background: $background 85%;
    }
    #help-box {
        background: $panel;
        border: round $primary;
        padding: 1 3;
        width: 70;
        height: 38;
        overflow-y: auto;
    }
    #help-title {
        color: $primary;
        text-style: bold;
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    .help-section {
        color: $secondary;
        text-style: bold;
        margin-top: 1;
    }
    .help-row {
        color: $foreground;
        margin-left: 2;
    }
    .help-key {
        color: $accent;
        text-style: bold;
    }
    #help-footer {
        color: $text-muted;
        content-align: center middle;
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Static(id="help-box"):
            yield Label("  ARGUS — Keyboard Reference", id="help-title")
            for section, bindings in KEYBINDINGS:
                yield Label(f"▸ {section}", classes="help-section")
                for key, desc in bindings:
                    yield Label(f"  [{key}]  {desc}", classes="help-row")
            yield Label("[dim]Press Escape or ? to close[/]", id="help-footer")

    def action_dismiss(self) -> None:
        self.app.pop_screen()
