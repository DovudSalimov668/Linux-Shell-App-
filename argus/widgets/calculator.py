"""Calculator widget — safe AST-based expression evaluator."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

from rich.markup import escape as mu_escape
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Static


# ── Safe AST evaluator ────────────────────────────────────────────────────────
# Whitelist of allowed AST node types and operators.  No eval(), no exec(),
# no attribute access, no imports, no function calls beyond the math whitelist.

_SAFE_NODES = (
    ast.Expression,
    ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv,
    ast.UAdd, ast.USub,
    ast.Call, ast.Name,
)

_BINARY_OPS: dict[type, Any] = {
    ast.Add:      operator.add,
    ast.Sub:      operator.sub,
    ast.Mult:     operator.mul,
    ast.Div:      operator.truediv,
    ast.Mod:      operator.mod,
    ast.Pow:      operator.pow,
    ast.FloorDiv: operator.floordiv,
}

_UNARY_OPS: dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_SAFE_FUNCS: dict[str, Any] = {
    "abs": abs, "round": round, "min": min, "max": max,
    "int": int, "float": float,
    "hex": hex, "bin": bin, "oct": oct,
    "sqrt": math.sqrt, "cbrt": getattr(math, "cbrt", lambda x: x ** (1/3)),
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan, "atan2": math.atan2,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "log": math.log, "log2": math.log2, "log10": math.log10,
    "exp": math.exp, "pow": math.pow,
    "ceil": math.ceil, "floor": math.floor, "trunc": math.trunc,
    "factorial": math.factorial, "gcd": math.gcd,
    "degrees": math.degrees, "radians": math.radians,
    "hypot": math.hypot,
}

_SAFE_NAMES: dict[str, Any] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
    "nan": math.nan,
}


def _eval_node(node: ast.AST) -> Any:
    """Recursively evaluate an AST node. Raises ValueError on unsafe input."""
    if not isinstance(node, _SAFE_NODES):
        raise ValueError(f"Unsupported operation: {type(node).__name__}")

    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float, complex)):
            raise ValueError("Only numeric constants allowed")
        return node.value

    if isinstance(node, ast.BinOp):
        op_fn = _BINARY_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        # Guard against giant exponents (DoS)
        if isinstance(node.op, ast.Pow) and isinstance(right, (int, float)):
            if abs(right) > 1000:
                raise ValueError("Exponent too large (max 1000)")
        return op_fn(left, right)

    if isinstance(node, ast.UnaryOp):
        op_fn = _UNARY_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_fn(_eval_node(node.operand))

    if isinstance(node, ast.Name):
        if node.id not in _SAFE_NAMES:
            raise ValueError(f"Unknown name: {node.id!r}")
        return _SAFE_NAMES[node.id]

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only named functions are allowed")
        fn = _SAFE_FUNCS.get(node.func.id)
        if fn is None:
            raise ValueError(f"Unknown function: {node.func.id!r}")
        if node.keywords:
            raise ValueError("Keyword arguments not supported")
        args = [_eval_node(a) for a in node.args]
        return fn(*args)

    raise ValueError(f"Unsupported node: {type(node).__name__}")


def safe_eval(expr: str) -> Any:
    """Parse and evaluate a math expression safely (no eval, no exec)."""
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty expression")
    if len(expr) > 500:
        raise ValueError("Expression too long")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error: {e}") from e
    return _eval_node(tree)


# ── Widget ────────────────────────────────────────────────────────────────────

class CalculatorWidget(Widget):
    """Safe expression calculator with history."""

    DEFAULT_CSS = """
    CalculatorWidget {
        height: 100%;
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
        yield Input(
            placeholder="2**10, sin(pi/2), sqrt(144), log(e)…",
            id="calc-input",
        )

    def on_mount(self) -> None:
        self._history: list[str] = []

    def on_input_submitted(self, event: Input.Submitted) -> None:
        expr = event.value.strip()
        if not expr:
            return
        try:
            result = safe_eval(expr)
            # Format nicely
            if isinstance(result, float) and result.is_integer():
                formatted = str(int(result))
            elif isinstance(result, float):
                formatted = f"{result:.10g}"
            else:
                formatted = str(result)
            self._history.append(
                f"[green]{mu_escape(expr)}[/] [dim]=[/] [bold]{mu_escape(formatted)}[/]"
            )
        except Exception as e:
            self._history.append(f"[red]{mu_escape(expr)}[/] [dim]→[/] [yellow]{mu_escape(str(e))}[/]")

        try:
            self.query_one("#calc-history", Static).update(
                "\n".join(self._history[-20:])
            )
        except Exception:
            pass
        event.input.value = ""
