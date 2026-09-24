"""Configuration loading for Mink.

The configuration is deliberately small and dependency-free.  Values may be
provided in a JSON file (``~/.config/mink/config.json`` by default) and
overridden with ``MINK_`` environment variables.
"""

from dataclasses import dataclass, fields
import json
import os
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class Config:
    sleep_after: float = 22.0
    tick_interval: float = 0.08
    animation_speed: float = 1.0
    poll_interval: float = 1.0
    theme: str = "default"
    animation: bool = True
    random_idle: bool = True
    music_visible: bool = True
    status_bar: bool = False
    status_items: str = "song,uptime,hostname"
    layout: str = "auto"
    startup_animation: bool = True

    @classmethod
    def load(cls, path: Optional[os.PathLike] = None) -> "Config":
        filename = Path(path) if path is not None else Path(
            os.environ.get("MINK_CONFIG", "~/.config/mink/config.json")
        ).expanduser()
        values: dict[str, Any] = {}
        try:
            with filename.open(encoding="utf-8") as stream:
                loaded = json.load(stream)
            if isinstance(loaded, dict):
                values.update(loaded)
        except (OSError, ValueError, TypeError):
            pass
        for field in fields(cls):
            key = f"MINK_{field.name.upper()}"
            if key in os.environ:
                values[field.name] = os.environ[key]
        for name in ("sleep_after", "tick_interval", "poll_interval",
                     "animation_speed"):
            try:
                values[name] = float(values[name])
                if values[name] <= 0:
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                values.pop(name, None)
        for name in ("animation", "random_idle", "music_visible", "status_bar",
                     "startup_animation"):
            value = values.get(name)
            if isinstance(value, str):
                normalized = value.casefold()
                if normalized in {"1", "true", "yes", "on"}:
                    values[name] = True
                elif normalized in {"0", "false", "no", "off"}:
                    values[name] = False
                else:
                    values.pop(name, None)
            elif value is not None and not isinstance(value, bool):
                values.pop(name, None)
        if values.get("layout") not in {None, "auto", "stacked", "columns"}:
            values.pop("layout", None)
        if not isinstance(values.get("status_items"), str):
            values.pop("status_items", None)
        return cls(**{field.name: values[field.name]
                      for field in fields(cls) if field.name in values})


def load_config(path: Optional[os.PathLike] = None) -> Config:
    """Load the process configuration, retaining safe defaults on errors."""
    return Config.load(path)
