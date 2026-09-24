"""Centralized, immutable visual theme definitions."""

from dataclasses import dataclass
from typing import Mapping, Tuple

Frame = Tuple[str, ...]


@dataclass(frozen=True)
class Theme:
    idle: Tuple[Frame, ...]
    music: Tuple[Frame, ...]
    sleeping: Tuple[Frame, ...]
    reactions: Mapping[str, Tuple[Frame, ...]]
    colors: Mapping[str, int] = None


DEFAULT_THEME = Theme(
    idle=(("/\\_/\\\\", "( o.o )", " > ^ <"),
          ("/\\_/\\\\", "( -.- )", " > ^ <"),
          ("/\\_/\\\\", "( -.o )", " > ^ <")),
    music=((" /\\_/\\\\", "( o.o )", "  > ^ <"),
           ("/\\_/\\\\", "( ^.^ )", " > ^ <"),
           (" /\\_/\\\\", "( o.o )", "  > ^ <"),
           ("/\\_/\\\\", "( ^o^ )", " > ^ <")),
    sleeping=(("/\\_/\\\\", "( -.- )", " > ^ <", "   z"),
              (" /\\_/\\\\", "( -.- )", "  > ^ <", "    z"),
              ("/\\_/\\\\", "( -.- )", " > ^ <", "   Z")),
    reactions={
        "blink": (("/\\_/\\\\", "( -.- )", " > ^ <"),),
        "look_left": (("/\\_/\\\\", "( o.- )", " > ^ <"),),
        "look_right": (("/\\_/\\\\", "( -.o )", " > ^ <"),),
        "music_vibe": (("/\\_/\\\\", "( ^.^ )", " > ^ <"),),
        "sleep_breathe": (("/\\_/\\\\", "( -.- )", " > ^ <"),),
        "happy": (("/\\_/\\\\", "( ^.^ )", " > ^ <"),),
        "annoyed": (("/\\_/\\\\", "( >.< )", " > ^ <"),),
        "excited": (("/\\_/\\\\", "( ^o^ )", " > ^ <"),),
    },
    colors={"cyan": 1, "purple": 2, "soft": 3},
)

THEMES = {
    "default": DEFAULT_THEME,
    "mink": DEFAULT_THEME,
    "catppuccin-mocha": Theme(
        DEFAULT_THEME.idle, DEFAULT_THEME.music, DEFAULT_THEME.sleeping,
        DEFAULT_THEME.reactions, {"cyan": 6, "purple": 5, "soft": 7}),
    "tokyo-night": Theme(
        DEFAULT_THEME.idle, DEFAULT_THEME.music, DEFAULT_THEME.sleeping,
        DEFAULT_THEME.reactions, {"cyan": 6, "purple": 4, "soft": 7}),
    "dracula": Theme(
        DEFAULT_THEME.idle, DEFAULT_THEME.music, DEFAULT_THEME.sleeping,
        DEFAULT_THEME.reactions, {"cyan": 5, "purple": 5, "soft": 7}),
    "nord": Theme(
        DEFAULT_THEME.idle, DEFAULT_THEME.music, DEFAULT_THEME.sleeping,
        DEFAULT_THEME.reactions, {"cyan": 6, "purple": 4, "soft": 7}),
    "forest": Theme(
        DEFAULT_THEME.idle, DEFAULT_THEME.music, DEFAULT_THEME.sleeping,
        DEFAULT_THEME.reactions, {"cyan": 2, "purple": 3, "soft": 7}),
    "sunset": Theme(
        DEFAULT_THEME.idle, DEFAULT_THEME.music, DEFAULT_THEME.sleeping,
        DEFAULT_THEME.reactions, {"cyan": 3, "purple": 5, "soft": 7}),
}


def get_theme(name: str = "default") -> Theme:
    """Return a named theme; unknown names safely use the default."""
    return THEMES.get((name or "default").casefold(), DEFAULT_THEME)
