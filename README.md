# ARGUS — Terminal Command Center

A full-screen TUI dashboard for Linux. Live system metrics, process management,
file browsing, git status, games, and a suite of productivity tools — all
keyboard-driven, all in one terminal window.

Built on [Textual](https://github.com/Textualize/textual), [Rich](https://github.com/Textualize/rich), and psutil.

---

## Install

```bash
git clone https://github.com/dovudsalimov668/linux-shell-app-
cd linux-shell-app-
pip install -e .
```

Then run it:

```bash
argus
```

Requires Python 3.11+ and a 256-color terminal. Nerd Fonts are optional but
make the icons look right.

Optional GPU monitoring (NVIDIA):

```bash
pip install -e ".[gpu]"
```

---

## What you get

On launch you land on the main dashboard — a 3×3 grid of live panels that
update every second. From there you can jump to any other screen with a
keyboard shortcut or the command palette.

The screensaver kicks in after 2 minutes of no input (matrix rain). Any key
brings you back.

---

## Navigation

These work from anywhere in the app:

| Key | Where it goes |
|-----|--------------|
| `Ctrl+D` | Dashboard |
| `Ctrl+Z` | Process manager |
| `Ctrl+F` | File explorer |
| `Ctrl+X` | Git dashboard |
| `Ctrl+G` | Games |
| `Ctrl+W` | Tools (shell, calc, network, notes, pomodoro…) |
| `Ctrl+I` | System info |
| `Ctrl+S` | Settings |
| `Ctrl+P` | Command palette |
| `Ctrl+T` | Cycle theme |
| `?` | Keyboard reference |
| `Ctrl+Q` | Quit |

`Escape` or `q` goes back to the previous screen in most places.

---

## Dashboard

The dashboard shows nine live panels arranged in a 3×3 grid.

**Row 1**

- **System Monitor** — CPU percentage bars per core, RAM and swap usage meters
  with sparkline history, temperature readout if sensors are available.

- **CPU Graph** — scrolling braille sparkline of aggregate CPU usage over time,
  with mini per-core bars below it.

- **Processes** — top 8 processes by CPU, refreshed every second. A snapshot,
  not interactive — use `Ctrl+Z` for the full process manager.

**Row 2**

- **Network** — live upload/download rates with sparklines, session totals, and
  local IP address.

- **Clock** — current time and date in the active timezone.

- **Git** — branch name, ahead/behind count relative to remote, last commit
  message. Refreshes every 10 seconds. Non-blocking — a slow or absent remote
  doesn't freeze the UI.

**Row 3**

- **Disk** — usage bar for each mounted filesystem.

- **Todo** — persistent task list stored in `~/.config/argus/todo.json`.
  `Enter` adds a task, `Space` toggles done, `j`/`k` moves selection, `d`
  deletes.

- **Logs** — tail of `/var/log/syslog` (or equivalent), color-coded by
  severity keyword.

---

## System Info (`Ctrl+I`)

Nine tabs of hardware and OS detail, loaded in parallel in background threads
so the UI never blocks:

| Tab | Contents |
|-----|----------|
| Overview | Hostname, OS, kernel, architecture, Python version, uptime, shell, terminal |
| CPU | Model, core count, frequency, per-core usage bars, load average, cache sizes |
| Memory | RAM and swap usage bars, total/used/free/available, buffer/cache breakdown |
| Storage | Per-device usage bar, filesystem type, mount point, read/write stats |
| Network | All interfaces — IP, MAC, MTU, bytes sent/received, packets, errors |
| Sensors | CPU temperatures per package and core (requires `lm-sensors` or kernel hwmon) |
| Processes | Top 20 processes by CPU — PID, name, CPU%, memory, user, state |
| Services | Status of common system services via `systemctl` |
| Hardware | DMI/SMBIOS board info, CPU brand string, memory slots |

The live overview, CPU, memory, and process tabs auto-refresh every 5 seconds.

---

## Tools (`Ctrl+W`)

A tabbed utility screen. `Tab` / `Shift+Tab` switch between tabs.

### Shell

Runs commands as the current user in an async subprocess. Output appends to a
scrollable history. Up arrow recalls the last command.

Destructive commands (`rm -rf`, `mkfs`, `dd` to a block device, fork bombs)
trigger a confirmation prompt. Fork bombs are blocked outright.

### Calculator

Expression evaluator using Python's AST parser — no `eval()`, no `exec()`.
Supports the usual arithmetic operators plus a whitelist of math functions:
`sin`, `cos`, `tan`, `sqrt`, `log`, `log2`, `log10`, `abs`, `round`,
`hex`, `bin`, `oct`, and the constants `pi` and `e`.

Examples:
```
2 ** 32
sin(pi / 6)
log2(1024)
hex(255)
```

### Network

Enter a hostname or `host:port` and hit **Ping** or **Port**. Ping runs
`ping -c 3` via subprocess. Port check is a plain TCP connect with a 5-second
timeout. Results appear in the output pane below.

### Notes

Full-screen text editor backed by `~/.config/argus/notes.md`. Supports
markdown syntax. `Ctrl+S` saves to disk.

### Pomodoro

25-minute work / 5-minute break timer. After every 4 work sessions it switches
to a 15-minute long break.

| Key | Action |
|-----|--------|
| `Space` | Start / pause |
| `r` | Reset to idle |
| `n` | Skip to next phase |

### Calendar

Month view calendar widget. Browse months with left/right arrow keys.

### Clocks

Side-by-side clocks for multiple time zones.

### Weather

Current conditions and 3-day forecast from the open-meteo API. No API key
required. Set your city in settings or `~/.config/argus/config.toml`. Updates
every 30 minutes. Shows gracefully offline if the request fails.

---

## Process Manager (`Ctrl+Z`)

Sortable table of running processes: PID, name, CPU%, memory, user, and state.
Filter by name with `f`. Refreshes every 2 seconds.

| Key | Action |
|-----|--------|
| `k` | Kill selected process (confirmation dialog) |
| `r` | Renice selected process |
| `f` | Focus the filter input |
| `Ctrl+R` | Force refresh |
| `↑ ↓ j k` | Move selection |

---

## File Explorer (`Ctrl+F`)

Two-pane layout. Left pane: directory tree. Right pane: file preview with
syntax highlighting for source files and rendered output for Markdown.

| Key | Action |
|-----|--------|
| `/` | Focus search box |
| `d` | Delete selected file or directory (confirmation dialog) |
| `n` | New directory |
| `Backspace` | Go to parent directory |
| `Enter` | Open / expand |

---

## Git Dashboard (`Ctrl+X`)

Three tabs for the git repository in the current working directory.

**Overview** — staged, modified, and untracked file lists on the left; diff
stat on the right.

**Log** — last 20 commits as a table with hash, message, author, and relative
time. Scrollable.

**Diff** — full `git diff` output with syntax coloring. Added lines green,
removed lines red, hunk headers cyan.

All git operations run in background threads — opening the screen never blocks
even in repos with large diffs.

| Key | Action |
|-----|--------|
| `p` | Pull (with 60-second timeout) |
| `P` | Push (with 60-second timeout) |
| `Ctrl+R` | Refresh |

---

## Games (`Ctrl+G`)

Six games. Pick one from the sidebar, play it on the right. Press `Escape` or
`q` to leave.

| Game | Description |
|------|-------------|
| Snake | Classic snake — grows when it eats, dies when it hits a wall or itself |
| Game of Life | Conway's Game of Life. Space pauses, `r` randomizes, `c` clears |
| Typing Test | Shows a random word list, measures WPM and accuracy |
| Tetris | Falling blocks |
| 2048 | Sliding number tiles |
| Minesweeper | Mine detection on a grid |

Snake controls: `W A S D` or arrow keys. `r` restarts.

---

## Command Palette (`Ctrl+P`)

Fuzzy search over all navigation targets and actions. Type any part of the
command name or description. Results rank by label matches first, then
description matches. `Enter` runs the selected item, `Escape` closes.

Available actions: navigate to any screen, switch to a specific theme, cycle
theme, open help, quit.

---

## Themes

`Ctrl+T` cycles through all seven themes in order. The choice is saved and
restored on next launch. Themes can also be set via the command palette or
settings screen.

| Theme | Look |
|-------|------|
| `dracula` | Purple and pink on dark grey |
| `catppuccin` | Catppuccin Mocha — soft pastels on dark |
| `nord` | Arctic blues and greys |
| `gruvbox` | Warm brown and yellow tones |
| `tokyonight` | Deep navy with bright accent colors |
| `synthwave` | Neon magenta and cyan on deep purple |
| `matrix` | Green on black |

---

## Settings (`Ctrl+S`)

- **Theme** — dropdown picker
- **City** — used by the weather widget
- **Refresh rate** — dashboard update interval in seconds
- **Pomodoro durations** — work, short break, long break

`Ctrl+S` saves. `Escape` cancels.

---

## Configuration

Config file: `~/.config/argus/config.toml`

```toml
theme = "dracula"
refresh_rate = 1.0
city = "London"
```

Other files ARGUS writes:

| Path | Contents |
|------|----------|
| `~/.config/argus/todo.json` | Todo list items with done state |
| `~/.config/argus/notes.md` | Notes scratchpad text |

The config directory is created automatically on first run.

---

## Architecture

```
argus/
├── app.py              # Root app — bindings, theme management, screen routing
├── config.py           # Load/save config.toml via tomlkit
├── cli.py              # `argus` entry point
├── screens/
│   ├── boot.py         # Splash / boot animation
│   ├── dashboard.py    # 3×3 grid, LivePanel container
│   ├── processes.py    # Process manager + kill/renice dialogs
│   ├── files.py        # Two-pane file explorer + delete/mkdir dialogs
│   ├── git.py          # Git dashboard — status, log, diff
│   ├── games.py        # Game launcher shell
│   ├── tools.py        # Tabbed utility hub
│   ├── sysinfo.py      # 9-tab hardware deep-dive
│   ├── settings.py     # Settings form
│   ├── help.py         # Keyboard reference overlay
│   └── screensaver.py  # Matrix rain idle screen
├── widgets/
│   ├── system_monitor.py   # CPU + RAM bars, temperatures
│   ├── cpu_graph.py        # Scrolling braille sparkline
│   ├── process_table.py    # Top-N processes by CPU
│   ├── net_monitor.py      # Network sparklines and totals
│   ├── disk_widget.py      # Filesystem usage bars
│   ├── git_panel.py        # Compact git status for dashboard
│   ├── clock.py            # Live clock
│   ├── todo.py             # Persistent todo list
│   ├── log_viewer.py       # Syslog tail
│   ├── weather.py          # open-meteo weather (no key)
│   ├── crypto_ticker.py    # CoinGecko price ticker
│   ├── shell_pane.py       # Async command runner with destructive guards
│   ├── calculator.py       # AST-safe expression evaluator
│   ├── network_tools.py    # Ping and port-check tools
│   ├── notes.py            # Markdown scratchpad
│   ├── pomodoro.py         # Pomodoro timer
│   ├── command_palette.py  # Fuzzy command palette
│   └── statusbar.py        # Bottom status bar
├── games/
│   ├── snake.py
│   ├── game_of_life.py
│   ├── typing_test.py
│   ├── tetris.py
│   ├── game_2048.py
│   └── minesweeper.py
├── data/
│   └── system_worker.py    # Async psutil snapshot collector
└── utils/
    └── formatters.py       # fmt_bytes, make_bar, braille_sparkline, fmt_uptime
```

Screen navigation uses a stack (`push_screen` / `pop_screen`). `Escape` pops
the current screen, returning to whatever was underneath. The dashboard is
always the base.

All blocking I/O — subprocess calls, HTTP requests, disk reads — runs in
background threads via `asyncio.to_thread()` wrapped in Textual `@work`
workers. The main event loop never blocks.

---

## Adding a panel widget

1. Create `argus/widgets/my_widget.py` subclassing `Widget`.
2. Yield a `Static` in `compose()` and call `set_interval()` in `on_mount()`.
3. Add it to `DashboardScreen.compose()` in `screens/dashboard.py` wrapped in a
   `LivePanel`.

```python
# argus/widgets/my_widget.py
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static

class MyWidget(Widget):
    DEFAULT_CSS = "MyWidget { height: 1fr; padding: 0 1; }"

    def compose(self) -> ComposeResult:
        yield Static("", id="my-content")

    def on_mount(self) -> None:
        self.set_interval(2.0, self._refresh)

    def _refresh(self) -> None:
        self.query_one("#my-content", Static).update("live data")
```

Colors inherit from the active theme automatically — use `$primary`,
`$background`, `$panel`, `$foreground`, `$accent`, etc. in your CSS.

If your widget does any I/O, move it to a thread:

```python
from textual import work
import asyncio

@work(exclusive=True)
async def _refresh(self) -> None:
    data = await asyncio.to_thread(self._collect)
    self.query_one("#my-content", Static).update(data)

def _collect(self) -> str:
    # runs in a thread pool — safe to block here
    return "result"
```

---

## Requirements

- Python 3.11 or later
- A terminal with 256-color support (xterm-256color, most modern emulators)
- `git` in PATH for the git dashboard and git panel widget
- `lm-sensors` or kernel hwmon for temperature readings in system info
- `systemctl` for the services tab in system info (systemd systems only)

Python packages (installed automatically via pip):

```
textual >= 0.80
rich >= 13
psutil >= 5.9
GitPython >= 3.1
httpx >= 0.27
plotext >= 5.2
tomlkit >= 0.13
pyfiglet >= 1.0
```

Optional:

```
nvidia-ml-py >= 12.0   # pip install "argus[gpu]" for NVIDIA GPU stats
```

Tested on Python 3.11 and 3.12. The app runs fully offline — weather and crypto
widgets fall back gracefully when there's no network.
