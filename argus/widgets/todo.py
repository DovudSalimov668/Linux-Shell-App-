"""TodoWidget — persistent todo list widget for the ARGUS dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Label, Static

TODO_FILE = Path.home() / ".config" / "argus" / "todo.json"


class TodoWidget(Widget):
    """Persistent todo list widget.

    Keyboard:
      Enter  — add the text in the input field as a new task
      Space  — toggle the selected task done / undone
      j/k    — move selection down/up
      d      — delete the selected task
    """

    DEFAULT_CSS = """
    TodoWidget {
        height: 100%;
        padding: 0 1;
    }
    #todo-input {
        height: 3;
        dock: bottom;
    }
    #todo-list {
        height: 1fr;
        overflow-y: auto;
    }
    #todo-hint {
        height: 1;
        color: $text-muted;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="todo-list")
        yield Label("[dim]Enter Add  Space Toggle  j/k Move  d Delete[/]", id="todo-hint")
        yield Input(placeholder="Add new task...", id="todo-input")

    def on_mount(self) -> None:
        self._todos: list[dict] = self._load()
        self._selected: int = 0
        self._render()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> list[dict]:
        try:
            TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
            if TODO_FILE.exists():
                return json.loads(TODO_FILE.read_text())
        except Exception:
            pass
        return []

    def _save(self) -> None:
        try:
            TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
            TODO_FILE.write_text(json.dumps(self._todos, indent=2))
        except Exception:
            pass

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render(self) -> None:
        if not self._todos:
            lines = ["[dim]No tasks. Add one below![/]"]
        else:
            lines = []
            for i, todo in enumerate(self._todos):
                done = todo.get("done", False)
                text = todo.get("text", "")
                icon = "[green]✓[/]" if done else "[dim]○[/]"
                if i == self._selected:
                    prefix = "[bold reverse] > [/]"
                else:
                    prefix = "   "
                if done:
                    lines.append(f"{prefix}{icon} [dim strike]{text}[/]")
                else:
                    lines.append(f"{prefix}{icon} {text}")
        try:
            self.query_one("#todo-list", Static).update("\n".join(lines))
        except Exception:
            pass

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self._todos.append({"text": text, "done": False})
            self._selected = len(self._todos) - 1
            self._save()
            self._render()
            event.input.value = ""

    def on_key(self, event) -> None:
        if not self._todos:
            return
        if event.key == "j" or event.key == "down":
            self._selected = min(self._selected + 1, len(self._todos) - 1)
            self._render()
            event.stop()
        elif event.key == "k" or event.key == "up":
            self._selected = max(self._selected - 1, 0)
            self._render()
            event.stop()
        elif event.key == "space":
            if 0 <= self._selected < len(self._todos):
                self._todos[self._selected]["done"] = not self._todos[self._selected].get("done", False)
                self._save()
                self._render()
                event.stop()
        elif event.key == "d":
            if 0 <= self._selected < len(self._todos):
                self._todos.pop(self._selected)
                self._selected = min(self._selected, len(self._todos) - 1)
                self._save()
                self._render()
                event.stop()
