"""ARGUS settings screen — theme picker, toggles, and text inputs."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Button, Input, Select
from textual.binding import Binding
from textual.containers import Vertical, Horizontal

THEME_CHOICES = [
    ("dracula", "Dracula — purple/pink dark"),
    ("catppuccin", "Catppuccin Mocha — pastel dark"),
    ("nord", "Nord — arctic blue"),
    ("gruvbox", "Gruvbox — warm retro"),
    ("tokyonight", "Tokyo Night — deep navy"),
    ("synthwave", "Synthwave — neon magenta/cyan"),
    ("matrix", "Matrix — green on black"),
]


class SettingsScreen(Screen):
    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("ctrl+s", "save_settings", "Save"),
    ]

    DEFAULT_CSS = """
    SettingsScreen {
        layout: vertical;
        background: $background;
    }
    #settings-header {
        height: 3;
        background: $panel;
        padding: 0 2;
        color: $primary;
        text-style: bold;
        content-align: left middle;
    }
    #settings-body {
        height: 1fr;
        padding: 1 3;
        overflow-y: auto;
    }
    .settings-section-title {
        color: $secondary;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }
    .settings-row {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
    }
    .settings-label {
        width: 30;
        content-align: left middle;
        color: $foreground;
    }
    .settings-control {
        width: 40;
    }
    #settings-footer {
        height: 1;
        background: $surface;
        content-align: center middle;
        color: $foreground;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(" ⚙ Settings", id="settings-header")

        with Vertical(id="settings-body"):
            yield Label("Appearance", classes="settings-section-title")

            with Horizontal(classes="settings-row"):
                yield Label("Theme:", classes="settings-label")
                yield Select(
                    [(label, value) for value, label in THEME_CHOICES],
                    id="setting-theme",
                    classes="settings-control",
                )

            yield Label("System Monitor", classes="settings-section-title")

            with Horizontal(classes="settings-row"):
                yield Label("Refresh rate (sec):", classes="settings-label")
                yield Input(value="1.0", id="setting-refresh", classes="settings-control")

            yield Label("Weather", classes="settings-section-title")

            with Horizontal(classes="settings-row"):
                yield Label("City:", classes="settings-label")
                yield Input(id="setting-city", classes="settings-control")

            yield Label("Productivity", classes="settings-section-title")

            with Horizontal(classes="settings-row"):
                yield Label("Pomodoro work (min):", classes="settings-label")
                yield Input(value="25", id="setting-pomo-work", classes="settings-control")

            with Horizontal(classes="settings-row"):
                yield Label("Pomodoro break (min):", classes="settings-label")
                yield Input(value="5", id="setting-pomo-break", classes="settings-control")

            yield Button("Save Settings", variant="primary", id="btn-save")

        yield Label("Ctrl+S Save  Esc Back", id="settings-footer")

    def on_mount(self) -> None:
        cfg = self.app.argus_config
        try:
            self.query_one("#setting-city", Input).value = cfg.city
            self.query_one("#setting-refresh", Input).value = str(cfg.refresh_rate)
            sel = self.query_one("#setting-theme", Select)
            sel.value = cfg.theme  # value IS the theme key e.g. "dracula"
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save_settings()

    def action_save_settings(self) -> None:
        from argus.config import save_config
        cfg = self.app.argus_config

        try:
            city_input = self.query_one("#setting-city", Input).value.strip()
            if city_input:
                cfg.city = city_input

            refresh_input = self.query_one("#setting-refresh", Input).value.strip()
            try:
                cfg.refresh_rate = float(refresh_input)
            except ValueError:
                pass

            theme_sel = self.query_one("#setting-theme", Select)
            if theme_sel.value and theme_sel.value != Select.BLANK:
                cfg.theme = str(theme_sel.value)
                self.app._apply_theme(str(theme_sel.value))

            save_config(cfg)
            self.app.notify("Settings saved!", timeout=2)
        except Exception as e:
            self.app.notify(f"Save error: {e}", severity="error")

    def action_go_back(self) -> None:
        self.app.pop_screen()
