"""NotesWidget — persistent markdown scratchpad for the ARGUS dashboard."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, TextArea

NOTES_FILE = Path.home() / ".config" / "argus" / "notes.md"


class NotesWidget(Widget):
    """Persistent markdown scratchpad.

    Keyboard:
      Ctrl+S — save the current content to disk
    """

    DEFAULT_CSS = """
    NotesWidget {
        height: 100%;
    }
    #notes-hint {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text-muted;
        content-align: center middle;
    }
    NotesWidget TextArea {
        height: 1fr;
    }
    """

    # ── Compose ───────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        content = ""
        try:
            if NOTES_FILE.exists():
                content = NOTES_FILE.read_text()
        except Exception:
            pass
        yield TextArea(content, id="notes-area", language="markdown")
        yield Static("[dim]Ctrl+S Save[/]", id="notes-hint")

    # ── Key handling ──────────────────────────────────────────────────────────

    def on_key(self, event) -> None:
        if event.key == "ctrl+s":
            self._save()
            event.stop()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
            content = self.query_one("#notes-area", TextArea).text
            NOTES_FILE.write_text(content)
            self.app.notify("Notes saved", timeout=2)
        except Exception as exc:
            self.app.notify(f"Save failed: {exc}", severity="error")
