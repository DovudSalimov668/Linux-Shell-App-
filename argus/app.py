"""ArgusApp — root Textual application for ARGUS command center."""

from __future__ import annotations

import time
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

    _last_activity: float = 0.0
    _screensaver_active: bool = False

    CSS_PATH = [str(_SHARED_CSS)]

    BINDINGS = [
        Binding("ctrl+t", "cycle_theme", "Theme", show=True),
        Binding("ctrl+p", "command_palette", "Palette", show=True),
        Binding("ctrl+g", "navigate('games')", "Games", show=True),
        Binding("ctrl+f", "navigate('files')", "Files", show=True),
        Binding("ctrl+z", "navigate('processes')", "Processes", show=False),
        Binding("ctrl+x", "navigate('git')", "Git", show=False),
        Binding("ctrl+s", "navigate('settings')", "Settings", show=False),
        Binding("question_mark", "help_overlay", "Help", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.argus_config: ArgusConfig = load_config()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        for custom_theme in _CUSTOM_THEMES:
            self.register_theme(custom_theme)
        self._apply_theme(self.argus_config.theme, notify=False)
        self._last_activity = time.time()
        self.set_interval(30.0, self._check_screensaver)
        from argus.screens.boot import BootScreen
        self.push_screen(BootScreen())

    def compose(self) -> ComposeResult:
        return iter([])

    # ── Activity tracking / screensaver ───────────────────────────────────────

    def on_key(self, event) -> None:
        self._last_activity = time.time()

    def on_mouse_move(self, event) -> None:
        self._last_activity = time.time()

    def _check_screensaver(self) -> None:
        if self._screensaver_active:
            return
        idle = time.time() - self._last_activity
        if idle > 120:
            self._screensaver_active = True
            from argus.screens.screensaver import ScreensaverScreen
            self.push_screen(ScreensaverScreen())

    # ── Theme helpers ─────────────────────────────────────────────────────────

    def _textual_theme_name(self, argus_name: str) -> str:
        return _BUILTIN_MAP.get(argus_name, argus_name)

    def _apply_theme(self, argus_name: str, *, notify: bool = True) -> None:
        textual_name = self._textual_theme_name(argus_name)
        if textual_name in self.available_themes:
            self.theme = textual_name
        else:
            self.theme = "dracula"

        self.argus_config.theme = argus_name
        self._push_theme_to_statusbar(argus_name)

        if notify:
            self.notify(f"Theme: {argus_name}", title="Theme Changed", timeout=2)

    def _push_theme_to_statusbar(self, theme_name: str) -> None:
        try:
            from argus.widgets.statusbar import StatusBar
            for sb in self.screen.query(StatusBar):
                sb.set_theme(theme_name)
        except Exception:
            pass

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_cycle_theme(self) -> None:
        current = self.argus_config.theme
        try:
            idx = THEMES.index(current)
        except ValueError:
            idx = 0
        new_name = THEMES[(idx + 1) % len(THEMES)]
        save_config(self.argus_config)
        self._apply_theme(new_name, notify=True)

    def action_navigate(self, destination: str) -> None:
        """Push a named screen onto the stack."""
        screen_map = {
            "processes": "argus.screens.processes.ProcessScreen",
            "files":     "argus.screens.files.FilesScreen",
            "git":       "argus.screens.git.GitScreen",
            "games":     "argus.screens.games.GamesScreen",
            "settings":  "argus.screens.settings.SettingsScreen",
            "dashboard": "argus.screens.dashboard.DashboardScreen",
        }
        fqn = screen_map.get(destination)
        if not fqn:
            self.notify(f"Unknown screen: {destination}", severity="warning")
            return
        module_path, class_name = fqn.rsplit(".", 1)
        try:
            import importlib
            mod = importlib.import_module(module_path)
            screen_cls = getattr(mod, class_name)
            self.push_screen(screen_cls())
        except Exception as e:
            self.notify(f"Cannot open {destination}: {e}", severity="error")

    def action_command_palette(self) -> None:
        from argus.widgets.command_palette import CommandPaletteScreen
        self.push_screen(CommandPaletteScreen())

    def action_help_overlay(self) -> None:
        from argus.screens.help import HelpScreen
        self.push_screen(HelpScreen())
