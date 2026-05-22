"""ARGUS VS Code-style fuzzy command palette."""

from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, ListView, ListItem, Label
from textual.binding import Binding

COMMANDS = [
    # Navigation
    ("Go to Dashboard", "Switch to the main dashboard", "goto_dashboard"),
    ("Go to Process Manager", "Open the process manager", "goto_processes"),
    ("Go to File Explorer", "Open the file browser", "goto_files"),
    ("Go to Git Dashboard", "Open git status and log", "goto_git"),
    ("Go to Games", "Open games launcher", "goto_games"),
    ("Go to Tools", "Shell, calculator, network, notes, pomodoro (Ctrl+W)", "goto_tools"),
    ("Go to System Info", "Full hardware/OS deep-dive (Ctrl+I)", "goto_sysinfo"),
    ("Go to Settings", "Open settings screen", "goto_settings"),
    # Theme
    ("Cycle Theme", "Switch to next color theme (Ctrl+T)", "cycle_theme"),
    ("Theme: Dracula", "Switch to Dracula theme", "theme_dracula"),
    ("Theme: Catppuccin", "Switch to Catppuccin theme", "theme_catppuccin"),
    ("Theme: Nord", "Switch to Nord theme", "theme_nord"),
    ("Theme: Gruvbox", "Switch to Gruvbox theme", "theme_gruvbox"),
    ("Theme: Tokyo Night", "Switch to Tokyo Night theme", "theme_tokyonight"),
    ("Theme: Synthwave", "Switch to Synthwave theme", "theme_synthwave"),
    ("Theme: Matrix", "Switch to Matrix theme", "theme_matrix"),
    # Actions
    ("Show Help", "Open keyboard shortcuts reference", "show_help"),
    ("Quit ARGUS", "Exit the application", "quit"),
]


def _fuzzy_match(query: str, text: str) -> bool:
    """Simple fuzzy match: all query chars appear in order in text."""
    if not query:
        return True
    q = query.lower()
    t = text.lower()
    it = iter(t)
    return all(c in it for c in q)


class CommandPaletteScreen(Screen):
    """VS Code-style fuzzy command palette."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    CommandPaletteScreen {
        align: center middle;
        background: $background 75%;
    }
    #cp-box {
        background: $panel;
        border: round $primary;
        padding: 1 2;
        width: 70;
        height: 24;
    }
    #cp-title {
        color: $primary;
        text-style: bold;
        content-align: center middle;
        width: 100%;
        margin-bottom: 1;
    }
    #cp-input {
        width: 100%;
        margin-bottom: 1;
    }
    #cp-list {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Static(id="cp-box"):
            yield Label("  Command Palette", id="cp-title")
            yield Input(placeholder="Type to search commands...", id="cp-input")
            yield ListView(id="cp-list")

    def on_mount(self) -> None:
        # _matched tracks which action key corresponds to each visible row
        self._matched: list[str] = []
        self._populate("")
        self.query_one(Input).focus()

    @work(exclusive=True)
    async def _populate(self, query: str) -> None:
        # Label matches rank above description-only matches
        label_hits = [(l, d, k) for l, d, k in COMMANDS if _fuzzy_match(query, l)]
        desc_hits  = [(l, d, k) for l, d, k in COMMANDS if not _fuzzy_match(query, l) and _fuzzy_match(query, d)]
        matched = label_hits + desc_hits
        lv = self.query_one(ListView)
        await lv.clear()
        # Use no IDs on items — track order in self._matched instead
        items = [
            ListItem(Label(f"[bold]{label}[/]  [dim]{desc}[/]"))
            for label, desc, key in matched
        ]
        self._matched = [key for _, _, key in matched]
        if items:
            await lv.mount(*items)
            lv.index = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        self._populate(event.value)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._matched):
            self._execute(self._matched[idx])

    def on_key(self, event) -> None:
        if event.key == "enter":
            lv = self.query_one(ListView)
            idx = lv.index
            if idx is not None and 0 <= idx < len(self._matched):
                self._execute(self._matched[idx])

    def _execute(self, key: str) -> None:
        self.app.pop_screen()

        theme_map = {
            "theme_dracula":    "dracula",
            "theme_catppuccin": "catppuccin",
            "theme_nord":       "nord",
            "theme_gruvbox":    "gruvbox",
            "theme_tokyonight": "tokyonight",
            "theme_synthwave":  "synthwave",
            "theme_matrix":     "matrix",
        }
        screen_map = {
            "goto_processes": "processes",
            "goto_files":     "files",
            "goto_git":       "git",
            "goto_games":     "games",
            "goto_tools":     "tools",
            "goto_sysinfo":   "sysinfo",
            "goto_settings":  "settings",
            "goto_dashboard": "dashboard",
        }

        if key in theme_map:
            self.app._apply_theme(theme_map[key])
        elif key in screen_map:
            self.app.action_navigate(screen_map[key])
        elif key == "cycle_theme":
            self.app.action_cycle_theme()
        elif key == "show_help":
            self.app.action_help_overlay()
        elif key == "quit":
            self.app.action_quit()

    def action_dismiss(self) -> None:
        self.app.pop_screen()
