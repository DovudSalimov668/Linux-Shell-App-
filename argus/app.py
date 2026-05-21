"""ArgusApp — root Textual application for ARGUS command center."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.theme import Theme

from argus.config import ArgusConfig, load_config, save_config

# ── Theme cycle list (ARGUS names) ────────────────────────────────────────────
THEMES: list[str] = [
    "dracula",
    "catppuccin",
    "nord",
    "gruvbox",
    "tokyonight",
    "synthwave",
    "matrix",
]

# Map ARGUS names → Textual 8 built-in theme names
_BUILTIN_MAP: dict[str, str] = {
    "dracula":    "dracula",
    "catppuccin": "catppuccin-mocha",
    "nord":       "nord",
    "gruvbox":    "gruvbox",
    "tokyonight": "tokyo-night",
}

# Custom themes to register (not in Textual built-ins)
_CUSTOM_THEMES: list[Theme] = [
    Theme(
        name="synthwave",
        primary="#ff00ff",
        secondary="#00ffff",
        accent="#ff0099",
        warning="#ffcc00",
        error="#ff3300",
        success="#00ff99",
        foreground="#ffffff",
        background="#1a0033",
        surface="#200040",
        panel="#2a0050",
        dark=True,
        variables={
            "border":     "#cc00cc",
            "text-muted": "#cc88cc",
        },
    ),
    Theme(
        name="matrix",
        primary="#00ff00",
        secondary="#00cc00",
        accent="#00ff41",
        warning="#aaff00",
        error="#ff0000",
        success="#00ff00",
        foreground="#00ff00",
        background="#000000",
        surface="#001100",
        panel="#001a00",
        dark=True,
        variables={
            "border":     "#00aa00",
            "text-muted": "#006600",
        },
    ),
]

_THEMES_DIR = Path(__file__).parent / "themes"
_SHARED_CSS = _THEMES_DIR / "argus.tcss"


class ArgusApp(App[None]):
    """ARGUS — Terminal Command Center."""

    TITLE = "ARGUS"
    SUB_TITLE = "Terminal Command Center"

    # Shared layout CSS — colors flow in via the Textual Theme system
    CSS_PATH = [str(_SHARED_CSS)]

    BINDINGS = [
        Binding("ctrl+t", "cycle_theme", "Theme", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("question_mark", "help_overlay", "Help", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.argus_config: ArgusConfig = load_config()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        """Register custom themes and apply the saved theme."""
        for custom_theme in _CUSTOM_THEMES:
            self.register_theme(custom_theme)

        # Apply the saved theme (after custom themes are registered)
        self._apply_theme(self.argus_config.theme, notify=False)

        from argus.screens.dashboard import DashboardScreen
        self.push_screen(DashboardScreen())

    def compose(self) -> ComposeResult:
        return iter([])

    # ── Theme helpers ─────────────────────────────────────────────────────────

    def _textual_theme_name(self, argus_name: str) -> str:
        """Resolve an ARGUS theme name to a Textual registered theme name."""
        return _BUILTIN_MAP.get(argus_name, argus_name)

    def _apply_theme(self, argus_name: str, *, notify: bool = True) -> None:
        """Switch to a theme by ARGUS name."""
        textual_name = self._textual_theme_name(argus_name)
        if textual_name in self.available_themes:
            self.theme = textual_name
        else:
            self.theme = "dracula"  # graceful fallback

        self._push_theme_to_statusbar(argus_name)

        if notify:
            self.notify(f"Theme: {argus_name}", title="Theme Changed", timeout=2)

    def _push_theme_to_statusbar(self, theme_name: str) -> None:
        """Propagate theme name to the StatusBar widget."""
        try:
            from argus.widgets.statusbar import StatusBar

            # StatusBar lives in the current screen
            for sb in self.screen.query(StatusBar):
                sb.set_theme(theme_name)
        except Exception:
            pass

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_cycle_theme(self) -> None:
        """Cycle to the next theme."""
        current = self.argus_config.theme
        try:
            idx = THEMES.index(current)
        except ValueError:
            idx = 0
        new_name = THEMES[(idx + 1) % len(THEMES)]

        self.argus_config.theme = new_name
        save_config(self.argus_config)
        self._apply_theme(new_name, notify=True)

    def action_help_overlay(self) -> None:
        """Show a brief help notification."""
        self.notify(
            "Ctrl+T — cycle themes  |  Ctrl+Q — quit  |  ? — this help\n"
            "More screens coming in future phases.",
            title="ARGUS Help",
            timeout=5,
        )
