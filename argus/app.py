"""ArgusApp — root Textual application."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding

from argus.config import ArgusConfig, load_config, save_config

THEMES = ["dracula", "catppuccin", "nord", "gruvbox", "tokyonight", "synthwave", "matrix"]
_THEMES_DIR = Path(__file__).parent / "themes"


class ArgusApp(App):
    """ARGUS — Terminal Command Center."""

    TITLE = "ARGUS"
    SUB_TITLE = "Terminal Command Center"

    BINDINGS = [
        Binding("ctrl+t", "cycle_theme", "Theme", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("question_mark", "help_overlay", "Help", show=True),
    ]

    def __init__(self) -> None:
        self.argus_config: ArgusConfig = load_config()
        theme = self.argus_config.theme
        if theme not in THEMES:
            theme = "dracula"
        super().__init__(css_path=str(_THEMES_DIR / f"{theme}.tcss"))

    def on_mount(self) -> None:
        from argus.screens.dashboard import DashboardScreen
        self.push_screen(DashboardScreen())

    def compose(self) -> ComposeResult:
        return iter([])

    # ── Actions ────────────────────────────────────────────────────────────

    def action_cycle_theme(self) -> None:
        current = self.argus_config.theme
        idx = THEMES.index(current) if current in THEMES else 0
        new_theme = THEMES[(idx + 1) % len(THEMES)]
        self._apply_theme(new_theme)

    def _apply_theme(self, theme_name: str) -> None:
        theme_path = _THEMES_DIR / f"{theme_name}.tcss"
        if not theme_path.exists():
            self.notify(f"Theme file not found: {theme_name}", severity="error")
            return

        with open(theme_path, encoding="utf-8") as fh:
            css = fh.read()

        self.stylesheet.read_all([str(theme_path)])
        self.stylesheet.reparse()
        self.refresh(layout=True)

        self.argus_config.theme = theme_name
        save_config(self.argus_config)

        # Update status bar if present
        try:
            from argus.widgets.statusbar import StatusBar
            for sb in self.query(StatusBar):
                sb.set_theme(theme_name)
        except Exception:
            pass

        self.notify(f"Theme: {theme_name}", title="Theme Changed")

    def action_help_overlay(self) -> None:
        self.notify(
            "^T Theme  ^Q Quit  ? Help\nMore screens coming in future phases.",
            title="ARGUS Help",
            timeout=5,
        )
