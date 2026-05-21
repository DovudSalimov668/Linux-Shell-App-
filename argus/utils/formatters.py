"""ARGUS formatting helpers."""
from __future__ import annotations

# ── Braille density chars (space → full block, 10 levels) ────────────────────
_BRAILLE_CHARS = " ⣀⣄⣆⣇⡇⡏⡟⡿⣿"  # 10 levels, index 0 = empty


def fmt_bytes(n: int) -> str:
    """Format an integer byte count as a human-readable string.

    Examples: 1_234_567_890 → "1.15 GB", 456_789_012 → "435.6 MB"
    """
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < 1024.0:
            if unit == "B":
                return f"{n} {unit}"
            return f"{n:.2f} {unit}"
        n /= 1024.0  # type: ignore[assignment]
    return f"{n:.2f} EB"


def fmt_bytes_rate(n: float) -> str:
    """Format a bytes-per-second rate as a human-readable string.

    Example: 1_234_567.0 → "1.18 MB/s"
    """
    for unit in ("B/s", "KB/s", "MB/s", "GB/s", "TB/s"):
        if abs(n) < 1024.0:
            if unit == "B/s":
                return f"{n:.0f} {unit}"
            return f"{n:.2f} {unit}"
        n /= 1024.0
    return f"{n:.2f} PB/s"


def fmt_uptime(seconds: int) -> str:
    """Format uptime seconds as a readable string.

    Example: 277_320 → "3d 4h 2m"
    """
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def make_bar(percent: float, width: int = 20) -> str:
    """Return a Rich markup bar string.

    Colour: green <60 %, yellow 60–80 %, red >80 %.
    Uses full-block (█) for filled portion and light-shade (░) for empty.
    """
    percent = max(0.0, min(100.0, percent))
    filled = int(round(percent / 100.0 * width))
    empty = width - filled

    if percent < 60.0:
        colour = "green"
    elif percent < 80.0:
        colour = "yellow"
    else:
        colour = "red"

    bar_filled = "█" * filled
    bar_empty = "░" * empty
    return f"[{colour}]{bar_filled}[/][dim]{bar_empty}[/]"


def braille_sparkline(
    values: list[float], width: int = 20, max_val: float = 100.0
) -> str:
    """Convert a list of float values to a braille-character sparkline string.

    The most-recent values are on the right.  Values are bucketed to *width*
    columns by sampling the tail of the list.
    """
    if not values:
        return " " * width

    # Take the last *width* values so the newest appear on the right
    tail = list(values[-width:])
    # Pad on the left if we have fewer values than width
    if len(tail) < width:
        tail = [0.0] * (width - len(tail)) + tail

    result: list[str] = []
    n_levels = len(_BRAILLE_CHARS) - 1  # 9
    safe_max = max_val if max_val > 0 else 1.0
    for v in tail:
        level = int((v / safe_max) * n_levels)
        level = max(0, min(level, n_levels))
        result.append(_BRAILLE_CHARS[level])
    return "".join(result)
