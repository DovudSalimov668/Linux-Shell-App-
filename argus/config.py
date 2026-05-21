"""ARGUS configuration — load/save ~/.config/argus/config.toml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tomlkit

CONFIG_DIR = Path.home() / ".config" / "argus"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class ArgusConfig:
    theme: str = "dracula"
    refresh_rate: float = 1.0
    city: str = "London"
    extra: dict = field(default_factory=dict)


def _defaults() -> dict:
    return {
        "theme": "dracula",
        "refresh_rate": 1.0,
        "city": "London",
    }


def load_config() -> ArgusConfig:
    """Load config from disk, creating defaults if absent."""
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cfg = ArgusConfig()
        save_config(cfg)
        return cfg

    with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
        data = tomlkit.load(fh)

    defaults = _defaults()
    defaults.update({k: v for k, v in data.items() if k in {"theme", "refresh_rate", "city"}})

    return ArgusConfig(
        theme=str(defaults["theme"]),
        refresh_rate=float(defaults["refresh_rate"]),
        city=str(defaults["city"]),
        extra={k: v for k, v in data.items() if k not in {"theme", "refresh_rate", "city"}},
    )


def save_config(cfg: ArgusConfig) -> None:
    """Persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    doc = tomlkit.document()
    doc.add("theme", cfg.theme)
    doc.add("refresh_rate", cfg.refresh_rate)
    doc.add("city", cfg.city)
    for key, val in cfg.extra.items():
        doc.add(key, val)

    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        tomlkit.dump(doc, fh)
