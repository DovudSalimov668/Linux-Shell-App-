"""GitPanelWidget — compact git status widget for the dashboard."""

from __future__ import annotations

import subprocess
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class GitPanelWidget(Widget):
    """Compact git status for the dashboard.

    Displays branch name, staged/modified/untracked file counts, and the
    most recent commit message.  Refreshes every 10 seconds.
    """

    DEFAULT_CSS = """
    GitPanelWidget {
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="git-panel-content")

    def on_mount(self) -> None:
        self._refresh()
        self.set_interval(10.0, self._refresh)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_git_summary(self) -> dict:
        cwd = Path.cwd()
        result: dict = {}
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, cwd=cwd,
            )
            if r.returncode != 0:
                result["error"] = "not a git repo"
                return result
            result["branch"] = r.stdout.strip() or "unknown"

            # Status counts
            r = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=cwd,
            )
            lines = r.stdout.strip().split("\n") if r.stdout.strip() else []
            result["staged"] = sum(1 for l in lines if l and l[0] in "MADRC")
            result["modified"] = sum(1 for l in lines if l and l[1] in "MD")
            result["untracked"] = sum(1 for l in lines if l.startswith("??"))

            # Last commit
            r = subprocess.run(
                ["git", "log", "-1", "--format=%s|%an|%ar"],
                capture_output=True, text=True, cwd=cwd,
            )
            if r.returncode == 0 and r.stdout.strip():
                parts = r.stdout.strip().split("|", 2)
                result["last_msg"] = parts[0] if len(parts) > 0 else ""
                result["last_author"] = parts[1] if len(parts) > 1 else ""
                result["last_when"] = parts[2] if len(parts) > 2 else ""
            else:
                result["last_msg"] = ""

            # Ahead / behind
            try:
                r = subprocess.run(
                    ["git", "rev-list", "--count", "--left-right", "HEAD...@{upstream}"],
                    capture_output=True, text=True, cwd=cwd,
                )
                if r.returncode == 0 and r.stdout.strip():
                    ab = r.stdout.strip().split()
                    result["ahead"] = int(ab[0]) if len(ab) > 0 else 0
                    result["behind"] = int(ab[1]) if len(ab) > 1 else 0
                else:
                    result["ahead"] = 0
                    result["behind"] = 0
            except Exception:
                result["ahead"] = 0
                result["behind"] = 0

        except FileNotFoundError:
            result["error"] = "git not found"
        except Exception as exc:
            result["error"] = str(exc)

        return result

    def _refresh(self) -> None:
        info = self._get_git_summary()
        lines: list[str] = []

        if "error" in info:
            lines.append(f"[dim]{info['error']}[/]")
        else:
            branch = info.get("branch", "unknown")
            ahead = info.get("ahead", 0)
            behind = info.get("behind", 0)

            branch_line = f"[bold primary] {branch}[/]"
            if ahead:
                branch_line += f"  [green]↑{ahead}[/]"
            if behind:
                branch_line += f"  [yellow]↓{behind}[/]"
            lines.append(branch_line)
            lines.append("")

            staged = info.get("staged", 0)
            modified = info.get("modified", 0)
            untracked = info.get("untracked", 0)

            if staged:
                lines.append(f"[green]● Staged    {staged:>3}[/]")
            if modified:
                lines.append(f"[yellow]● Modified  {modified:>3}[/]")
            if untracked:
                lines.append(f"[dim]● Untracked {untracked:>3}[/]")
            if not staged and not modified and not untracked:
                lines.append("[dim green]✓ Clean[/]")

            last_msg = info.get("last_msg", "")
            if last_msg:
                lines.append("")
                lines.append("[dim]Last commit:[/]")
                short = last_msg[:40] + "…" if len(last_msg) > 40 else last_msg
                lines.append(f"  [dim]{short}[/]")
                when = info.get("last_when", "")
                if when:
                    lines.append(f"  [dim]{when}[/]")

        try:
            self.query_one("#git-panel-content", Static).update("\n".join(lines))
        except Exception:
            pass
