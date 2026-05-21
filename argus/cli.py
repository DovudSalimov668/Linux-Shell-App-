"""ARGUS CLI entry point."""

from __future__ import annotations


def main() -> None:
    """Launch the ARGUS TUI."""
    from argus.app import ArgusApp

    app = ArgusApp()
    app.run()


if __name__ == "__main__":
    main()
