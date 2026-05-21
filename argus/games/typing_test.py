"""Typing speed test widget."""
from __future__ import annotations
import time
import random
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static, Input
from textual.reactive import reactive

WORDS = [
    "the quick brown fox jumps over the lazy dog",
    "to be or not to be that is the question",
    "all that glitters is not gold",
    "a journey of a thousand miles begins with a single step",
    "ask not what your country can do for you",
    "in the beginning god created the heavens and the earth",
    "it was the best of times it was the worst of times",
    "to infinity and beyond the stars are calling",
    "the only way to do great work is to love what you do",
    "stay hungry stay foolish never stop learning",
]


class TypingTest(Widget):
    """Words-per-minute typing test."""

    DEFAULT_CSS = """
    TypingTest {
        height: 100%;
        align: center middle;
        padding: 1 2;
    }
    #typing-prompt {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        height: 3;
        border: round $border;
        padding: 1;
    }
    #typing-input {
        width: 80%;
        margin-top: 1;
    }
    #typing-stats {
        width: 100%;
        content-align: center middle;
        color: $secondary;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="typing-prompt")
        yield Input(placeholder="Start typing...", id="typing-input")
        yield Static("[dim]WPM: — | Accuracy: — | Press Enter to restart[/]", id="typing-stats")

    def on_mount(self) -> None:
        self._new_prompt()

    def _new_prompt(self) -> None:
        self._target = random.choice(WORDS)
        self._start_time: float | None = None
        self._chars_typed = 0
        self._errors = 0
        try:
            self.query_one("#typing-prompt", Static).update(f"[bold]{self._target}[/]")
            inp = self.query_one(Input)
            inp.value = ""
            inp.focus()
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        typed = event.value
        if typed and self._start_time is None:
            self._start_time = time.time()

        if not typed:
            return

        # Colorize the prompt to show correct/incorrect
        target = self._target
        colored = []
        for i, ch in enumerate(target):
            if i < len(typed):
                if typed[i] == ch:
                    colored.append(f"[green]{ch}[/]")
                else:
                    colored.append(f"[red]{ch}[/]")
            else:
                colored.append(f"[dim]{ch}[/]")

        try:
            self.query_one("#typing-prompt", Static).update("".join(colored))
        except Exception:
            pass

        # Update stats
        if self._start_time:
            elapsed = max(0.01, time.time() - self._start_time)
            words = len(typed.split())
            wpm = int(words / (elapsed / 60))
            correct = sum(1 for a, b in zip(typed, target) if a == b)
            accuracy = int(100 * correct / max(1, len(typed)))
            try:
                self.query_one("#typing-stats", Static).update(
                    f"WPM: [bold]{wpm}[/] | Accuracy: [bold]{accuracy}%[/] | [dim]Enter restart[/]"
                )
            except Exception:
                pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._new_prompt()
