"""GitScreen — full-screen git dashboard for the current working directory."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from rich.markup import escape as mu_escape
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import Button, DataTable, Label, Static, TabbedContent, TabPane


class GitScreen(Screen):
    """Full-screen git dashboard: status, log, and diff viewer."""

    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("p", "pull", "Pull"),
        Binding("P", "push", "Push"),
    ]

    DEFAULT_CSS = """
    GitScreen {
        layout: vertical;
        background: $background;
    }
    #git-header {
        height: 3;
        background: $panel;
        padding: 0 2;
        layout: horizontal;
        align: left middle;
        border-bottom: solid $border;
    }
    #git-header-title {
        width: 1fr;
        color: $primary;
        text-style: bold;
        content-align: left middle;
    }
    #git-back-btn {
        width: auto;
        min-width: 12;
        height: 3;
    }
    #git-body {
        height: 1fr;
        layout: horizontal;
    }
    #git-left {
        width: 40%;
        layout: vertical;
    }
    #git-right {
        width: 60%;
        border-left: solid $border;
        padding: 0 1;
        overflow-y: auto;
    }
    .git-section {
        border: round $border;
        background: $panel;
        margin: 0 1 1 1;
        padding: 0 1;
        height: auto;
    }
    .git-section-title {
        color: $primary;
        text-style: bold;
    }
    #git-footer {
        height: 1;
        background: $surface;
        content-align: center middle;
        color: $foreground;
    }
    #git-commits {
        height: 1fr;
        margin: 0 1 1 1;
    }
    """

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Horizontal(id="git-header"):
            yield Label("🔀 Git Dashboard", id="git-header-title")
            yield Button("← Back", id="git-back-btn", variant="default")
        with TabbedContent(id="git-body"):
            with TabPane("Overview", id="tab-overview"):
                yield Static("", id="git-overview-left")
                yield Static("", id="git-diff-content")
            with TabPane("Log", id="tab-log"):
                table = DataTable(id="git-commits", cursor_type="row")
                table.add_columns("Hash", "Message", "Author", "When")
                yield table
            with TabPane("Diff", id="tab-diff"):
                yield Static("", id="git-diff-full")
        yield Static(
            "[dim]Escape/Q Back  Ctrl+R Refresh  p Pull  P Push[/]",
            id="git-footer",
        )

    def on_mount(self) -> None:
        self._load()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _get_git_info(self) -> dict:
        cwd = Path.cwd()
        result: dict = {}
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, cwd=cwd, timeout=5,
            )
            if r.returncode != 0:
                result["error"] = "Not a git repository"
                return result
            result["branch"] = r.stdout.strip() or "unknown"

            # Repo name from toplevel
            r2 = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, cwd=cwd, timeout=5,
            )
            result["repo_name"] = Path(r2.stdout.strip()).name if r2.returncode == 0 else ""

            # Ahead / behind
            try:
                r3 = subprocess.run(
                    ["git", "rev-list", "--count", "--left-right", "HEAD...@{upstream}"],
                    capture_output=True, text=True, cwd=cwd, timeout=5,
                )
                if r3.returncode == 0 and r3.stdout.strip():
                    parts = r3.stdout.strip().split()
                    result["ahead"] = int(parts[0]) if len(parts) > 0 else 0
                    result["behind"] = int(parts[1]) if len(parts) > 1 else 0
                else:
                    result["ahead"] = 0
                    result["behind"] = 0
            except Exception:
                result["ahead"] = 0
                result["behind"] = 0

            # Status
            r = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=cwd, timeout=5,
            )
            lines = r.stdout.strip().split("\n") if r.stdout.strip() else []
            staged = [l for l in lines if l and l[0] in "MADRC"]
            modified = [l for l in lines if l and l[1] in "MD"]
            untracked = [l for l in lines if l.startswith("??")]
            result["staged"] = staged
            result["modified"] = modified
            result["untracked"] = untracked

            # Commits
            r = subprocess.run(
                ["git", "log", "--format=%h|%s|%an|%ar", "-20"],
                capture_output=True, text=True, cwd=cwd, timeout=5,
            )
            commits = []
            for line in r.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        commits.append(parts)
            result["commits"] = commits

            # Diff stat
            r = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True, text=True, cwd=cwd, timeout=5,
            )
            result["diff_stat"] = r.stdout.strip()

            # Full diff (truncated for display)
            r = subprocess.run(
                ["git", "diff"],
                capture_output=True, text=True, cwd=cwd, timeout=10,
            )
            diff_lines = r.stdout.split("\n")
            result["diff_full"] = "\n".join(diff_lines[:300])

        except FileNotFoundError:
            result["error"] = "git not found"
        except Exception as e:
            result["error"] = str(e)

        return result

    @work(exclusive=True)
    async def _load(self) -> None:
        info = await asyncio.to_thread(self._get_git_info)

        if "error" in info:
            self.query_one("#git-header-title", Label).update(
                f"[bold red]🔀 Git[/]  [dim]{mu_escape(info['error'])}[/]"
            )
            return

        branch = info.get("branch", "unknown")
        repo = info.get("repo_name", "")
        ahead = info.get("ahead", 0)
        behind = info.get("behind", 0)

        # Build header
        ahead_str = f"[green]↑{ahead}[/]" if ahead else ""
        behind_str = f"[yellow]↓{behind}[/]" if behind else ""
        sync_info = f"  {ahead_str} {behind_str}".strip() if (ahead or behind) else "  [dim]in sync[/]"
        header_text = (
            f"[bold]🔀 Git[/]  [primary]{mu_escape(branch)}[/]{sync_info}"
            + (f"  [dim]{mu_escape(repo)}[/]" if repo else "")
        )
        self.query_one("#git-header-title", Label).update(header_text)

        # Build overview (left side status)
        staged = info.get("staged", [])
        modified = info.get("modified", [])
        untracked = info.get("untracked", [])
        diff_stat = info.get("diff_stat", "")

        status_lines: list[str] = []

        if staged:
            status_lines.append("[bold green]Staged[/]")
            for f in staged:
                status_lines.append(f"  [green]{mu_escape(f.strip())}[/]")
            status_lines.append("")

        if modified:
            status_lines.append("[bold yellow]Modified[/]")
            for f in modified:
                status_lines.append(f"  [yellow]{mu_escape(f.strip())}[/]")
            status_lines.append("")

        if untracked:
            status_lines.append("[bold dim]Untracked[/]")
            for f in untracked[:10]:
                status_lines.append(f"  [dim]{mu_escape(f[3:].strip())}[/]")
            if len(untracked) > 10:
                status_lines.append(f"  [dim]… and {len(untracked) - 10} more[/]")
            status_lines.append("")

        if not staged and not modified and not untracked:
            status_lines.append("[dim green]Working tree clean[/]")

        self.query_one("#git-overview-left", Static).update(
            "\n".join(status_lines)
        )

        # Diff stat on the right
        if diff_stat:
            self.query_one("#git-diff-content", Static).update(
                f"[bold]Diff stat[/]\n[dim]{mu_escape(diff_stat)}[/]"
            )
        else:
            self.query_one("#git-diff-content", Static).update(
                "[dim]No unstaged changes[/]"
            )

        # Commits table
        table = self.query_one("#git-commits", DataTable)
        table.clear()
        for commit in info.get("commits", []):
            h, msg, author, when = commit
            short_msg = msg[:55] + "…" if len(msg) > 55 else msg
            table.add_row(
                f"[cyan]{mu_escape(h)}[/]",
                mu_escape(short_msg),
                f"[dim]{mu_escape(author)}[/]",
                f"[dim]{mu_escape(when)}[/]",
            )

        # Full diff
        diff_full = info.get("diff_full", "")
        if diff_full:
            # Colour diff lines simply
            coloured: list[str] = []
            for line in diff_full.split("\n"):
                safe = mu_escape(line)
                if line.startswith("+++") or line.startswith("---"):
                    coloured.append(f"[bold]{safe}[/]")
                elif line.startswith("+"):
                    coloured.append(f"[green]{safe}[/]")
                elif line.startswith("-"):
                    coloured.append(f"[red]{safe}[/]")
                elif line.startswith("@@"):
                    coloured.append(f"[cyan]{safe}[/]")
                else:
                    coloured.append(safe)
            rendered = "\n".join(coloured)
            try:
                self.query_one("#git-diff-full", Static).update(rendered)
            except Exception:
                # Fall back to plain text if markup parsing fails
                self.query_one("#git-diff-full", Static).update(diff_full[:10000])
        else:
            self.query_one("#git-diff-full", Static).update(
                "[dim]No diff to display[/]"
            )

    # ── Actions ───────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "git-back-btn":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self._load()
        self.app.notify("Git status refreshed", timeout=2)

    @work(exclusive=True)
    async def _run_git(self, *args: str) -> None:
        """Run a git command in a thread and notify the result."""
        cwd = Path.cwd()
        try:
            r = await asyncio.to_thread(
                subprocess.run,
                ["git", *args],
                capture_output=True, text=True, cwd=cwd, timeout=60,
            )
            if r.returncode == 0:
                self.app.notify(
                    r.stdout.strip() or f"git {args[0]} OK",
                    timeout=3,
                )
            else:
                self.app.notify(
                    r.stderr.strip() or f"git {args[0]} failed",
                    severity="error",
                    timeout=5,
                )
        except subprocess.TimeoutExpired:
            self.app.notify(f"git {args[0]} timed out", severity="error", timeout=5)
        except Exception as exc:
            self.app.notify(str(exc), severity="error", timeout=5)
        self._load()

    def action_pull(self) -> None:
        self._run_git("pull")

    def action_push(self) -> None:
        self._run_git("push")
