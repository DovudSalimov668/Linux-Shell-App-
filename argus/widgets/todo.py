"""TodoWidget — persistent todo list widget for the ARGUS dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Label, ListItem, ListView, Static

TODO_FILE = Path.home() / ".config" / "argus" / "todo.json"


class TodoWidget(Widget):
    """Persistent todo list widget.

    Keyboard:
      Enter  — add the text in the input field as a new task
      Space  — toggle the selected task done / undone
      d      — delete the selected task
    """

    DEFAULT_CSS = """
    TodoWidget {
        height: 100%;
        padding: 0 1;
        layout: vertical;
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

    # ── Compose / mount ───────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield ListView(id="todo-list")
        yield Label("[dim]Enter Add  Space Toggle  d Delete[/]", id="todo-hint")
        yield Input(placeholder="Add new task...", id="todo-input")

    def on_mount(self) -> None:
        self._todos: list[dict] = self._load()
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
        try:
            lv = self.query_one("#todo-list", ListView)
        except Exception:
            return
        lv.clear()
        for i, todo in enumerate(self._todos):
            done = todo.get("done", False)
            text = todo.get("text", "")
            icon = "[green]✓[/]" if done else "[dim]○[/]"
            if done:
                item_label = Label(f"{icon} [dim strike]{text}[/]")
            else:
                item_label = Label(f"{icon} {text}")
            lv.append(ListItem(item_label, id=f"todo-{i}"))

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self._todos.append({"text": text, "done": False})
            self._save()
            self._render()
            event.input.value = ""

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Toggle the done state of the selected item."""
        if event.item.id is None:
            return
        try:
            idx = int(event.item.id.split("-")[1])
        except (IndexError, ValueError):
            return
        if 0 <= idx < len(self._todos):
            self._todos[idx]["done"] = not self._todos[idx].get("done", False)
            self._save()
            self._render()

    def on_key(self, event) -> None:
        if event.key == "d":
            try:
                lv = self.query_one("#todo-list", ListView)
                idx = lv.index
                if idx is not None and 0 <= idx < len(self._todos):
                    self._todos.pop(idx)
                    self._save()
                    self._render()
                    event.stop()
            except Exception:
                pass
