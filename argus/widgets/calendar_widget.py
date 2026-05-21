"""Calendar widget showing current month with today highlighted."""
from __future__ import annotations
import calendar
from datetime import date, datetime
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static


class CalendarWidget(Widget):
    """Monthly calendar widget with today highlighted."""
    DEFAULT_CSS = """
    CalendarWidget {
        height: 100%;
        padding: 0 1;
        align: center middle;
    }
    #cal-content { width: 100%; content-align: center middle; }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="cal-content")

    def on_mount(self) -> None:
        self._render()
        self.set_interval(60.0, self._render)  # refresh every minute

    def _render(self) -> None:
        today = date.today()
        cal = calendar.monthcalendar(today.year, today.month)
        month_name = today.strftime("%B %Y")

        lines = [f"[bold primary]{month_name}[/]", ""]
        lines.append("[dim]Mo Tu We Th Fr Sa Su[/]")

        for week in cal:
            row = ""
            for day in week:
                if day == 0:
                    row += "   "
                elif day == today.day:
                    row += f"[bold reverse]{day:2d}[/] "
                else:
                    # Weekends (Sa=index 5, Su=index 6) in dim
                    idx = week.index(day)
                    if idx >= 5:
                        row += f"[dim]{day:2d}[/] "
                    else:
                        row += f"{day:2d} "
            lines.append(row)

        try:
            self.query_one("#cal-content", Static).update("\n".join(lines))
        except Exception:
            pass
