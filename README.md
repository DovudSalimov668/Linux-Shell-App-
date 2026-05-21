# ARGUS — Terminal Command Center

A visually stunning TUI dashboard for Linux. `btop` meets a sci-fi cockpit meets a productivity suite — all in one terminal app.

Built with [Textual](https://github.com/Textualize/textual), [Rich](https://github.com/Textualize/rich), and `psutil`.

---

## Install

```bash
git clone <repo>
cd Linux-Shell-App-
pip install -e .
argus
```

Requires Python 3.11+ and a terminal with 256-color support. [Nerd Fonts](https://www.nerdfonts.com/) recommended for icons.

---

## Keybindings

### Global

| Key | Action |
|-----|--------|
| `Ctrl+T` | Cycle through themes |
| `Ctrl+P` | Open command palette |
| `Ctrl+G` | Open games launcher |
| `Ctrl+F` | Open file explorer |
| `Ctrl+Z` | Open process manager |
| `Ctrl+X` | Open git dashboard |
| `Ctrl+,` | Open settings |
| `?` | Help overlay |
| `Ctrl+Q` | Quit |

### Navigation

| Key | Action |
|-----|--------|
| `↑ ↓ j k` | Move / scroll |
| `Enter` | Select / confirm |
| `Escape / q` | Go back |
| `Tab / Shift+Tab` | Cycle focus |

### Process Manager

| Key | Action |
|-----|--------|
| `k` | Kill selected process |
| `r` | Renice selected process |
| `f` | Focus filter input |
| `Ctrl+R` | Force refresh |

### File Explorer

| Key | Action |
|-----|--------|
| `/` | Search |
| `d` | Delete selected |
| `n` | New directory |
| `r` | Rename |
| `Backspace` | Go to parent directory |

### Git Dashboard

| Key | Action |
|-----|--------|
| `p` | Pull |
| `P` | Push |
| `Ctrl+R` | Refresh |

### Pomodoro Timer

| Key | Action |
|-----|--------|
| `Space` | Start / pause |
| `r` | Reset |
| `n` | Skip to next phase |

### Games

| Key | Action |
|-----|--------|
| `W A S D` / Arrows | Snake movement |
| `Space` | Pause Game of Life |
| `r` | Randomize / restart |
| `c` | Clear Game of Life board |
| `Enter` | Restart typing test |

---

## Themes

Switch live with `Ctrl+T`. Theme is persisted across sessions.

| Name | Description |
|------|-------------|
| `dracula` | Classic purple/pink dark |
| `catppuccin` | Catppuccin Mocha pastel dark |
| `nord` | Arctic blue |
| `gruvbox` | Warm retro brown/yellow |
| `tokyonight` | Deep navy with vibrant accents |
| `synthwave` | Neon magenta/cyan on deep purple |
| `matrix` | Classic green on black |

---

## Dashboard Panels

The main dashboard is a 3×3 grid of live panels:

| Panel | Description |
|-------|-------------|
| System Monitor | CPU bars, sparkline history, RAM/swap meters, temperatures |
| CPU Graph | Scrolling braille history graph, per-core mini-bars |
| Processes | Top 8 processes by CPU, live-updating |
| Network | Upload/download sparklines, session totals, local IP |
| Clock | Live time and date |
| Git | Branch status, ahead/behind, last commit |
| Weather | Current conditions + 3-day forecast (open-meteo, no API key) |
| Todo | Persistent task list |
| Logs | System log tail with color-coded severity |

---

## Screens

- **Dashboard** — default view, 3×3 live panels
- **Process Manager** (`Ctrl+Z`) — sortable/filterable process table, kill/renice
- **File Explorer** (`Ctrl+F`) — directory tree + syntax-highlighted preview
- **Git Dashboard** (`Ctrl+X`) — status, log, diff viewer, pull/push
- **Games** (`Ctrl+G`) — Snake, Game of Life, Typing Test
- **Settings** (`Ctrl+,`) — theme picker, city, refresh rate, Pomodoro durations
- **Help** (`?`) — full keybinding reference
- **Command Palette** (`Ctrl+P`) — fuzzy search over all actions

---

## Configuration

Config is stored at `~/.config/argus/config.toml`:

```toml
theme = "dracula"
refresh_rate = 1.0
city = "London"
```

Other persisted data:
- `~/.config/argus/todo.json` — todo list
- `~/.config/argus/notes.md` — scratch notes

---

## Adding a New Panel Widget

1. Create `argus/widgets/my_widget.py` inheriting from `Widget`
2. Add `set_interval(n, self._refresh)` in `on_mount` for live updates
3. Add it to `argus/screens/dashboard.py` wrapped in a `LivePanel`

```python
# argus/widgets/my_widget.py
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static

class MyWidget(Widget):
    DEFAULT_CSS = "MyWidget { height: 100%; padding: 0 1; }"

    def on_mount(self):
        self.set_interval(1.0, self._refresh)

    def compose(self) -> ComposeResult:
        yield Static("", id="my-content")

    def _refresh(self):
        self.query_one("#my-content", Static).update("live data here")
```

Colors automatically follow the active theme via Textual's `$primary`, `$background`, `$panel` etc. CSS variables.

---

## Architecture

```
argus/
  app.py          # ArgusApp — root, bindings, theme switching, screen routing
  config.py       # load/save ~/.config/argus/config.toml
  cli.py          # entry point: argus command
  themes/         # 7 × .tcss theme files + argus.tcss shared layout
  screens/        # boot, dashboard, processes, files, git, games, help, settings
  widgets/        # 15+ reusable panel widgets
  games/          # snake, game_of_life, typing_test
  data/           # system_worker: async psutil snapshot collector
  utils/          # formatters: fmt_bytes, make_bar, braille_sparkline, …
```

---

## Requirements

- Python 3.11+
- textual ≥ 0.80
- rich ≥ 13
- psutil ≥ 5.9
- GitPython ≥ 3.1
- httpx ≥ 0.27
- plotext ≥ 5.2
- tomlkit ≥ 0.13
- pyfiglet ≥ 1.0
