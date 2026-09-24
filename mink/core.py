"""Pure media parsing and the small three-mode Mink animation clock."""

from dataclasses import dataclass
from enum import Enum
import random
import time
from typing import Optional
from .config import Config
from .animation import get_animation


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
    """Persistent modes.  MUSIC and SLEEP remain compatibility aliases."""

    IDLE = "idle"
    MUSIC = "music"
    SLEEP = "sleep"
    SLEEPING = "sleep"
    HAPPY = "happy"
    ANNOYED = "annoyed"
    EXCITED = "excited"
    WAKING = "waking"


class Pet:
    """Non-blocking pet clock: rest most of the time, react occasionally."""

    IDLE_FRAMES = 1
    MUSIC_FRAMES = 1
    SLEEP_FRAMES = 1
    SLEEP_AFTER = 22.0

    def __init__(self, rng: Optional[random.Random] = None,
                 config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self.state = PetState.IDLE
        self.frame = 0
        self.reaction: Optional[str] = None
        self.reaction_until = 0.0
        self._clock = time.monotonic()
        self._last_activity = self._clock
        self._activity_is_explicit = False
        self._next_reaction = self._clock + 5.0
        self._last_tick = self._clock
        self._rng = rng or random.Random()
        self._playing = False
        self._mood_until = 0.0
        self.animation_name = "idle"
        self._animation_last_tick = self._clock
        self._animation_return = None
        self._interaction_count = 0
        self._last_interaction = -999.0
        self._sleepy_started = False

    @property
    def frame_count(self) -> int:
        if self.reaction:
            return 2
        animation = get_animation(self.animation_name)
        return len(animation.frames)

    def _set_mode(self, state: PetState, now: float) -> None:
        if self.state != state:
            self.state = state
            self.frame = 0
            self.reaction = None
            self._schedule_reaction(now)
        if self._animation_return is None:
            self.animation_name = {
                PetState.IDLE: "idle",
                PetState.MUSIC: "dancing",
                PetState.SLEEPING: "sleeping",
                PetState.HAPPY: "happy",
                PetState.ANNOYED: "annoyed",
                PetState.EXCITED: "excited",
                PetState.WAKING: "waking",
            }[state]
        self._animation_last_tick = now

    def trigger_animation(self, name: str,
                          now: Optional[float] = None) -> bool:
        animation = get_animation(name)
        if animation.name != name:
            return False
        now = time.monotonic() if now is None else now
        self._animation_return = None if animation.loop else self.animation_name
        self.animation_name = name
        self.frame = 0
        self._animation_last_tick = now
        return True

    def interact(self, now: Optional[float] = None) -> str:
        """React to a user action, escalating only for rapid repetition."""
        now = time.monotonic() if now is None else now
        if now - self._last_interaction > 4.0:
            self._interaction_count = 0
        self._interaction_count += 1
        self._last_interaction = now
        if self._interaction_count >= 4:
            name = "angry"
            state = "annoyed"
        elif self._interaction_count >= 2:
            name = "annoyed"
            state = "annoyed"
        else:
            name = "love"
            state = "happy"
        self.event(state, now)
        self.trigger_animation(name, now)
        return name

    def _schedule_reaction(self, now: float) -> None:
        delays = {
            PetState.IDLE: (4.0, 10.0),
            PetState.MUSIC: (8.0, 18.0),
            PetState.SLEEPING: (18.0, 35.0),
            PetState.HAPPY: (4.0, 10.0),
            PetState.ANNOYED: (4.0, 10.0),
            PetState.EXCITED: (4.0, 10.0),
            PetState.WAKING: (4.0, 10.0),
        }
        low, high = delays[self.state]
        self._next_reaction = now + self._rng.uniform(low, high)

    def _start_reaction(self, now: float) -> None:
        reactions = {
            PetState.IDLE: ("blink", "look_left", "look_right"),
            PetState.MUSIC: ("music_vibe",),
            PetState.SLEEPING: ("sleep_breathe",),
            PetState.HAPPY: ("happy",),
            PetState.ANNOYED: ("annoyed",),
            PetState.EXCITED: ("excited",),
            PetState.WAKING: ("blink",),
        }
        self.reaction = self._rng.choice(reactions[self.state])
        durations = {
            "blink": 0.45,
            "look_left": 0.9,
            "look_right": 0.9,
            "music_vibe": 1.2,
            "sleep_breathe": 2.0,
            "happy": 1.0,
            "annoyed": 1.0,
            "excited": 1.0,
        }
        self.reaction_until = now + durations[self.reaction]
        self.frame = 0

    def event(self, name: str, now: Optional[float] = None) -> None:
        now = time.monotonic() if now is None else now
        self._last_activity = now
        self._activity_is_explicit = True
        if name == "playing":
            self._playing = True
            self._set_mode(PetState.MUSIC, now)
            self.trigger_animation("dancing", now)
        elif name in {"paused", "stopped"}:
            self._playing = False
            self._set_mode(PetState.IDLE, now)
        elif name in {"idle", "waking"}:
            self._playing = False
            self._set_mode(PetState.WAKING if name == "waking" else PetState.IDLE, now)
            if name == "waking":
                self._mood_until = now + 0.5
        elif name in {"sleeping", "sleep"}:
            self._playing = False
            self._set_mode(PetState.SLEEPING, now)
        elif name in {"happy", "annoyed", "excited"}:
            self._set_mode(PetState[name.upper()], now)
            self._mood_until = now + 2.0
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
            if not self._activity_is_explicit:
                self._last_activity = now
            self._next_reaction = now + 5.0
        if now < self._last_tick:
            self._last_tick = now
        if playing is not None and playing != self._playing:
            self.event("playing" if playing else "paused", now)
        animation_started = False
        if self.reaction and now >= self.reaction_until:
            self.reaction = None
            self.frame = 0
            self._schedule_reaction(now)
        animation = get_animation(self.animation_name)
        duration = animation.frame_duration / max(0.1, self.config.animation_speed)
        elapsed = now - self._animation_last_tick
        if elapsed >= duration - 1e-9:
            steps = max(1, int((elapsed + 1e-9) / duration))
            self._animation_last_tick += steps * duration
            if animation.loop:
                self.frame = (self.frame + steps) % len(animation.frames)
            else:
                self.frame = min(len(animation.frames) - 1,
                                 self.frame + steps)
            if (not animation.loop and self.frame == len(animation.frames) - 1
                    and self._animation_return is not None):
                self.animation_name = self._animation_return
                self._animation_return = None
                self.frame = 0
                self._animation_last_tick = now
        if self.state == PetState.WAKING:
            if now >= self._mood_until:
                self._set_mode(PetState.IDLE, now)
            else:
                return self.state
        if self.state in {PetState.HAPPY, PetState.ANNOYED, PetState.EXCITED}:
            if now >= self._mood_until:
                self._set_mode(PetState.MUSIC if self._playing else PetState.IDLE,
                               now)
            else:
                return self.state
        inactive = now - self._last_activity
        if (not self._playing and inactive >= self.config.sleep_after * 0.65
                and inactive < self.config.sleep_after):
            if not self._sleepy_started:
                self._sleepy_started = True
                self.trigger_animation("sleepy", now)
                animation_started = True
        if inactive < self.config.sleep_after * 0.65:
            self._sleepy_started = False
        if (not animation_started and not self._playing and self.reaction is None
                and self._animation_return is None):
            if (now - self._last_activity >= self.config.sleep_after
                    or self._sleepy_started):
                self._set_mode(PetState.SLEEPING, now)
                self.animation_name = "sleeping"
            else:
                if self.state == PetState.WAKING:
                    self._set_mode(PetState.IDLE, now)
                elif self.state not in {PetState.HAPPY, PetState.ANNOYED,
                                         PetState.EXCITED}:
                    self._set_mode(PetState.IDLE, now)
        elif self._playing and self._animation_return is None:
            self._set_mode(PetState.MUSIC, now)
        if (self.state == PetState.MUSIC and self.reaction is None
                and now >= self._next_reaction):
            self._start_reaction(now)
            self._schedule_reaction(now)
        if (self.config.random_idle and self.reaction is None
                and self.animation_name == "idle"
                and now >= self._next_reaction):
            name = self._rng.choice((
                "blink", "looking_around", "stretching", "walking",
                "eating", "drinking",
            ))
            self.reaction = name
            self.reaction_until = now + get_animation(name).frame_duration * len(
                get_animation(name).frames)
            self.trigger_animation(name, now)
            self._schedule_reaction(now)
        elif self.reaction is not None:
            interval = 0.18 if self.reaction == "music_vibe" else 0.3
            if now - self._last_tick >= interval:
                self.frame = min(1, self.frame + 1)
                self._last_tick = now
        return self.state
