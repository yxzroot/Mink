"""Pure media parsing and the small three-mode Mink animation clock."""

from dataclasses import dataclass
from enum import Enum
import random
import time
from typing import Optional


@dataclass(frozen=True)
class Track:
    title: str = ""
    artist: str = ""
    status: str = "Stopped"
    position: float = 0.0
    duration: float = 0.0

    @property
    def available(self) -> bool:
        return bool(self.title or self.artist) and self.status != "Stopped"

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 0.0
        return max(0.0, min(1.0, self.position / self.duration))


def _seconds(value: str) -> float:
    try:
        number = max(0.0, float(value))
        return number / 1_000_000 if number > 100_000 else number
    except (TypeError, ValueError):
        return 0.0


def parse_playerctl_line(line: str) -> Track:
    fields = (line.rstrip("\n").split("\t") + [""] * 5)[:5]
    return Track(fields[0], fields[1], fields[2] or "Stopped",
                 _seconds(fields[3]), _seconds(fields[4]))


class PetState(Enum):
    """The three persistent visual modes; reactions are temporary overlays."""

    IDLE = "idle"
    MUSIC = "music"
    SLEEP = "sleep"
    SLEEPING = "sleep"


class Pet:
    """Non-blocking pet clock: rest most of the time, react occasionally."""

    IDLE_FRAMES = 1
    MUSIC_FRAMES = 1
    SLEEP_FRAMES = 1
    SLEEP_AFTER = 22.0

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.state = PetState.IDLE
        self.frame = 0
        self.reaction: Optional[str] = None
        self.reaction_until = 0.0
        self._clock = time.monotonic()
        self._last_activity = self._clock
        self._next_reaction = self._clock + 5.0
        self._last_tick = self._clock
        self._rng = rng or random.Random()
        self._playing = False

    @property
    def frame_count(self) -> int:
        if self.reaction:
            return 2
        return {
            PetState.IDLE: self.IDLE_FRAMES,
            PetState.MUSIC: self.MUSIC_FRAMES,
            PetState.SLEEP: self.SLEEP_FRAMES,
        }[self.state]

    def _set_mode(self, state: PetState, now: float) -> None:
        if self.state != state:
            self.state = state
            self.frame = 0
            self.reaction = None
            self._schedule_reaction(now)

    def _schedule_reaction(self, now: float) -> None:
        delays = {
            PetState.IDLE: (4.0, 10.0),
            PetState.MUSIC: (8.0, 18.0),
            PetState.SLEEP: (18.0, 35.0),
        }
        low, high = delays[self.state]
        self._next_reaction = now + self._rng.uniform(low, high)

    def _start_reaction(self, now: float) -> None:
        reactions = {
            PetState.IDLE: ("blink", "look_left", "look_right"),
            PetState.MUSIC: ("music_vibe",),
            PetState.SLEEP: ("sleep_breathe",),
        }
        self.reaction = self._rng.choice(reactions[self.state])
        durations = {
            "blink": 0.45,
            "look_left": 0.9,
            "look_right": 0.9,
            "music_vibe": 1.2,
            "sleep_breathe": 2.0,
        }
        self.reaction_until = now + durations[self.reaction]
        self.frame = 0

    def event(self, name: str, now: Optional[float] = None) -> None:
        now = time.monotonic() if now is None else now
        self._last_activity = now
        if name == "playing":
            self._playing = True
            self._set_mode(PetState.MUSIC, now)
        elif name in {"paused", "stopped"}:
            self._playing = False
            self._set_mode(PetState.IDLE, now)
        elif name == "terminal":
            self.reaction = "terminal"
            self.reaction_until = now + 0.75
            self.frame = 0
        elif name == "alex_g":
            self.reaction = "alex_g"
            self.reaction_until = now + 30.0
            self.frame = 0

    def trigger_alex_g(self, now: Optional[float] = None) -> None:
        self.event("alex_g", now)

    def tick(self, now: Optional[float] = None,
             playing: Optional[bool] = None) -> PetState:
        now = time.monotonic() if now is None else now
        if now < self._clock:
            self._clock = now
            self._last_activity = now
            self._next_reaction = now + 5.0
        if now < self._last_tick:
            self._last_tick = now
        if playing is not None and playing != self._playing:
            self.event("playing" if playing else "paused", now)
        if self.reaction and now >= self.reaction_until:
            self.reaction = None
            self.frame = 0
            self._schedule_reaction(now)
        if not self._playing and self.reaction is None:
            if now - self._last_activity >= self.SLEEP_AFTER:
                self._set_mode(PetState.SLEEP, now)
            else:
                self._set_mode(PetState.IDLE, now)
        elif self._playing:
            self._set_mode(PetState.MUSIC, now)
        if self.reaction is None and now >= self._next_reaction:
            self._start_reaction(now)
        elif self.reaction is not None:
            interval = 0.18 if self.reaction == "music_vibe" else 0.3
            if now - self._last_tick >= interval:
                self.frame = min(1, self.frame + 1)
                self._last_tick = now
        return self.state
