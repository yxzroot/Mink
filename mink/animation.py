"""Small, data-driven animation catalog for the terminal pet."""

from dataclasses import dataclass
from typing import Dict, Tuple

Frame = Tuple[str, ...]


@dataclass(frozen=True)
class Animation:
    name: str
    frames: Tuple[Frame, ...]
    frame_duration: float
    loop: bool = True


def _face(eyes: str, feet: str = " > ^ <") -> Frame:
    return ("/\\_/\\\\", f"( {eyes} )", feet)


ANIMATIONS: Dict[str, Animation] = {
    "idle": Animation("idle", (
        _face("o.o"), _face("o.o", " > v <"),
        _face("o.o"), _face("o.o", " > ^ <"),
    ), 0.32),
    "blink": Animation("blink", (_face("o.o"), _face("-.-"), _face("o.o")),
                        0.08, False),
    "sleepy": Animation("sleepy", (
        _face("o.o"), _face("-.o"), _face("-.-"),
        _face("-.-", " > v <"), _face("-.-", " > ^ <"),
    ), 0.18, False),
    "sleeping": Animation("sleeping", (
        ("/\\_/\\\\", "( -.- )", " > ^ <", "   z"),
        ("/\\_/\\\\", "( -.- )", " > v <", "   z"),
        ("/\\_/\\\\", "( -.- )", " > ^ <"),
        ("/\\_/\\\\", "( -.- )", " > v <"),
        ("/\\_/\\\\", "( -.- )", " > ^ <", "   Z"),
        ("/\\_/\\\\", "( -.- )", " > v <", "   z"),
    ), 0.45),
    "waking": Animation("waking", (
        ("/\\_/\\\\", "( -.- )", " > ^ <", "   z"),
        _face("-.-", " > v <"), _face("-.o"), _face("o.o"),
        _face("o.o", " > v <"), _face("o.o", " < ^ >"), _face("o.o"),
    ), 0.14, False),
    "happy": Animation("happy", (
        _face("^.^"), _face("^.^", " > v <"), _face("^.^", " > ^ <"),
        _face("^o^", " > v <"), _face("^o^", " > ^ <"), _face("^.^"),
    ), 0.16),
    "excited": Animation("excited", (
        _face("^.^"), _face("^.^", " > v <"), _face("^o^", " > ^ <"),
        _face("^o^", " > v <"), _face("^o^", " > ^ <"),
        _face("^.^", " > v <"), _face("^.^", " > ^ <"), _face("^.^"),
    ), 0.11),
    "annoyed": Animation("annoyed", (
        _face("o.o"), _face(">.<"), _face(">.<"),
        _face(">.<", " > v <"), _face(">.<"),
    ), 0.18, False),
    "angry": Animation("angry", (
        _face(">.<"), _face(">.<", " < ^ <"), _face(">.<"),
        _face(">.<", " > ^ >"), _face(">.<"), _face(">.<"),
    ), 0.16),
    "surprised": Animation("surprised", (
        _face("o.o"), _face("O.O"), _face("O.O"),
        _face("O.O", " > v <"), _face("o.o"),
    ), 0.14, False),
    "looking_around": Animation("looking_around", (
        _face("o.o"), _face("o.-"), _face("-.o"), _face("o.o"),
        _face("-.o"), _face("o.-"), _face("o.o"), _face("o.o"),
    ), 0.2, False),
    "stretching": Animation("stretching", (
        _face("o.o"), _face("o.o", " > v <"), _face("o.o", " < ^ <"),
        _face("o.o", " < ^ >"), _face("o.o", " < ^ >"),
        _face("o.o", " > ^ >"), _face("o.o", " > v <"), _face("o.o"),
    ), 0.18, False),
    "dancing": Animation("dancing", (
        _face("o.o"), _face("^.^", " < ^ <"), _face("o.o"),
        _face("^.^", " > ^ >"), _face("^.^", " > v <"),
        _face("^.^", " < ^ <"), _face("o.o"), _face("^.^", " > ^ >"),
    ), 0.16),
    "walking": Animation("walking", (
        _face("o.o", " < ^ <"), _face("o.o"),
        _face("o.o", " > ^ >"), _face("o.o"),
        _face("o.o", " < ^ <"), _face("o.o"),
        _face("o.o", " > ^ >"), _face("o.o"),
    ), 0.18),
    "eating": Animation("eating", (
        _face("o.o"), _face("-.o", " > v <"), _face("^^"),
        _face("^^", " > v <"), _face("^^"), _face("^^", " > v <"),
        _face("^.^"), _face("o.o"),
    ), 0.16, False),
    "drinking": Animation("drinking", (
        _face("o.o"), _face("-.o", " > v <"), _face("o.o"),
        _face("o.o", " > v <"), _face("o.o"), _face("^.^", " > v <"),
        _face("o.o"),
    ), 0.17, False),
    "playing": Animation("playing", (
        _face("o.o"), _face("^.^"), _face("^o^", " > v <"),
        _face("^.^"), _face("^.^", " < ^ <"), _face("^o^", " > v <"),
        _face("^.^"), _face("o.o"), _face("^.^"), _face("o.o"),
    ), 0.12),
    "love": Animation("love", (
        _face("^.^"), _face("^.^", " > v <"), _face("^.^"),
        ("  <3", "( ^.^ )", " > ^ <"), _face("^o^", " > v <"),
        ("  <3", "( ^.^ )", " > ^ <"), _face("^.^"), _face("o.o"),
    ), 0.16),
    "goodbye": Animation("goodbye", (
        _face("o.o"), _face("^.^", " > v <"), _face("^.^", " > ^ <"),
        _face("^.^", " > v <"), _face("-.-"), ("", "( -.- )", ""),
    ), 0.14, False),
}


def get_animation(name: str) -> Animation:
    return ANIMATIONS.get(name, ANIMATIONS["idle"])
