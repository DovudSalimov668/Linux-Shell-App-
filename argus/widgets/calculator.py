from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static, Input
import math


class CalculatorWidget(Widget):
    """Expression evaluator with history."""

    DEFAULT_CSS = """
    CalculatorWidget {
        height: 100%;
        layout: vertical;
        padding: 0 1;
    }
    #calc-history {
        height: 1fr;
        overflow-y: auto;
    }
    #calc-input {
        height: 3;
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="calc-history")
        yield Input(placeholder="Enter expression... (e.g. 2**10, sin(pi/2))", id="calc-input")

    def on_mount(self) -> None:
        self._history: list[str] = []

    def on_input_submitted(self, event: Input.Submitted) -> None:
        expr = event.value.strip()
        if not expr:
            return
        try:
            # Safe eval with math functions
            result = eval(expr, {"__builtins__": {}}, {
                **{k: v for k, v in math.__dict__.items() if not k.startswith("_")},
                "abs": abs, "round": round, "min": min, "max": max,
                "int": int, "float": float, "hex": hex, "bin": bin, "oct": oct,
            })
            self._history.append(f"[green]{expr}[/] [dim]=[/] [bold]{result}[/]")
        except Exception as e:
            self._history.append(f"[red]{expr}[/] [dim]→[/] [yellow]{e}[/]")

        self.query_one("#calc-history", Static).update("\n".join(self._history[-20:]))
        event.input.value = ""
