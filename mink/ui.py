"""Compact curses UI for Mink's dedicated tmux pane."""

import curses
import os
import re
import socket
import subprocess
import time
from typing import Optional

from .core import Pet, PetState, Track
from .config import Config, load_config
from .media import Player
from . import __version__
from .theme import Theme, get_theme
from .status import SystemStatus, read_status
from .animation import get_animation


IDLE_FRAMES = (
    ("/\\_/\\\\", "( o.o )", " > ^ <"),
    ("/\\_/\\\\", "( -.- )", " > ^ <"),
    ("/\\_/\\\\", "( -.o )", " > ^ <"),
)
MUSIC_FRAMES = (
    (" /\\_/\\\\", "( o.o )", "  > ^ <"),
    ("/\\_/\\\\", "( ^.^ )", " > ^ <"),
    (" /\\_/\\\\", "( o.o )", "  > ^ <"),
    ("/\\_/\\\\", "( ^o^ )", " > ^ <"),
)
SLEEP_FRAMES = (
    ("/\\_/\\\\", "( -.- )", " > ^ <", "   z"),
    (" /\\_/\\\\", "( -.- )", "  > ^ <", "    z"),
    ("/\\_/\\\\", "( -.- )", " > ^ <", "   Z"),
)
REACTION_FRAMES = {
    "blink": (IDLE_FRAMES[1], IDLE_FRAMES[0]),
    "look_left": (("/\\_/\\\\", "( o.- )", " > ^ <"),
                  IDLE_FRAMES[0]),
    "look_right": (("/\\_/\\\\", "( -.o )", " > ^ <"),
                   IDLE_FRAMES[0]),
    "music_vibe": MUSIC_FRAMES,
    "sleep_breathe": SLEEP_FRAMES,
}
ALEX_FRAMES = (
    ("/\\_/\\\\", "( ^.^ )", " > ^ <"),
    ("/\\_/\\\\", "( ^.^ )", " > ^ <"),
)


def _clip(text: str, width: int) -> str:
    return text[:max(0, width)]


def _center(text: str, width: int) -> int:
    return max(0, (width - len(text)) // 2)


def _bar(progress: float, width: int) -> str:
    if width < 7:
        return ""
    inner = width - 2
    filled = int(progress * inner)
    return "[" + "━" * filled + "·" * (inner - filled) + "]"


def _time(seconds: float) -> str:
    minutes, seconds = divmod(max(0, int(seconds)), 60)
    return f"{minutes}:{seconds:02d}"


def layout_mode(width: int, height: int, preference: str = "auto") -> str:
    if preference in {"stacked", "columns"}:
        return preference
    if width >= 80 and height >= 7:
        return "columns"
    return "stacked"


class MinkUI:
    def __init__(self, stdscr: "curses.window", player: Optional[Player] = None,
                 config: Optional[Config] = None,
                 theme: Optional[Theme] = None):
        self.screen = stdscr
        self.player = player or Player()
        self.config = config or load_config()
        self.theme = theme or get_theme(self.config.theme)
        self.pet = Pet(config=self.config)
        self.track = Track()
        self.previous_track = Track()
        self.socket_path = os.environ.get("MINK_SOCKET", "")
        self.command_socket: Optional[socket.socket] = None
        self._last_pane_command = ""
        self._last_draw = 0.0
        self._started = time.monotonic()
        self._status = SystemStatus("", "0m 00s", "CPU n/a", "RAM n/a")
        self._next_status = 0.0
        self._started_animation = self.config.startup_animation
        if self._started_animation:
            self.pet.event("waking", self._started)

    def _open_commands(self) -> None:
        if not self.socket_path:
            return
        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            self.command_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.command_socket.setblocking(False)
            self.command_socket.bind(self.socket_path)
            self.command_socket.listen(4)
        except OSError:
            self.command_socket = None

    def _commands(self) -> list:
        if not self.command_socket:
            return []
        commands = []
        while True:
            try:
                client, _ = self.command_socket.accept()
                with client:
                    command = client.recv(128).decode().strip()
                    commands.append(command)
                    if command == "status":
                        client.sendall(
                            f"{self.track.status}: {self.track.artist} - "
                            f"{self.track.title}\n".encode())
            except BlockingIOError:
                return commands
            except OSError:
                return commands

    def _terminal_active(self) -> bool:
        session = os.environ.get("MINK_SESSION")
        if not session:
            return False
        try:
            result = subprocess.run(
                ["tmux", "list-panes", "-t", f"{session}:0",
                 "-F", "#{pane_index}:#{pane_current_command}"],
                capture_output=True, text=True, timeout=0.15, check=False,
            )
            shell = os.environ.get("MINK_SHELL", "").split("/")[-1]
            for line in result.stdout.splitlines():
                if line.startswith("0:"):
                    command = line.split(":", 1)[1]
                    if command != self._last_pane_command:
                        self._last_pane_command = command
                        return bool(shell and command != shell)
        except (OSError, subprocess.TimeoutExpired):
            pass
        return False

    @staticmethod
    def _is_alex_g(artist: str, title: str = "") -> bool:
        """Match artist metadata, with a fallback for mislabeled player titles."""
        entries = re.split(r"[,;]", artist or "")
        normalized = []
        for entry in entries:
            value = " ".join(entry.split()).strip("[]'\"")
            normalized.append(value.casefold())
        if "alex g" in normalized:
            return True
        title_words = " ".join((title or "").split()).casefold()
        return bool(re.search(r"(?:^|\s[-–—]\s)alex\s+g$", title_words))

    def update(self, now: float) -> None:
        self.previous_track = self.track
        self.track = self.player.read()
        if self.track.status == "Playing" and self.previous_track.status != "Playing":
            self.pet.event("playing", now)
        elif self.track.status != "Playing" and self.previous_track.status == "Playing":
            self.pet.event("paused", now)
        entered_alex = (
            self.track.status == "Playing"
            and self._is_alex_g(self.track.artist, self.track.title)
            and not self._is_alex_g(self.previous_track.artist,
                                    self.previous_track.title)
        )
        if entered_alex:
            self.pet.trigger_alex_g(now)
        if self._terminal_active():
            self.pet.event("terminal", now)
        self.pet.tick(now, self.track.status == "Playing")

    def _safe(self, y: int, x: int, text: str, attr: int = 0) -> None:
        try:
            width = self.screen.getmaxyx()[1]
            if 0 <= y < self.screen.getmaxyx()[0] and 0 <= x < width:
                self.screen.addnstr(y, x, text, width - x, attr)
        except curses.error:
            pass

    def _pet_frames(self):
        if self.pet.reaction == "alex_g":
            return ALEX_FRAMES
        if self.pet.reaction == "terminal":
            return (("/\\_/\\\\", "( >.< )", " > ^ <"),
                    ("/\\_/\\\\", "( o.o )", " > ^ <"))
        if self.pet.animation_name in {
                "idle", "walking", "dancing", "sleeping", "happy",
                "annoyed", "excited", "waking", "blink", "sleepy",
                "angry", "surprised", "looking_around", "stretching",
                "eating", "drinking", "playing", "love", "goodbye"}:
            return get_animation(self.pet.animation_name).frames
        if self.pet.reaction in REACTION_FRAMES:
            return self.theme.reactions.get(
                self.pet.reaction, REACTION_FRAMES[self.pet.reaction])
        return {
            PetState.IDLE: self.theme.idle,
            PetState.MUSIC: self.theme.music,
            PetState.SLEEPING: self.theme.sleeping,
            PetState.HAPPY: self.theme.idle,
            PetState.ANNOYED: self.theme.reactions["annoyed"],
            PetState.EXCITED: self.theme.music,
            PetState.WAKING: self.theme.idle,
        }[self.pet.state]

    def _configure_input(self) -> None:
        """Route mouse reports to curses instead of the terminal scrollback."""
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS)
            curses.mouseinterval(0)
            self.screen.nodelay(True)
        except curses.error:
            pass

    def _consume_input(self) -> None:
        """Consume input owned by the display-only Mink pane."""
        while True:
            try:
                key = self.screen.getch()
            except curses.error:
                return
            if key == -1:
                return
            if key == curses.KEY_MOUSE:
                try:
                    _, _, _, _, buttons = curses.getmouse()
                    if buttons & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED):
                        self.pet.interact()
                except (curses.error, ValueError):
                    pass
                continue
            if key == curses.KEY_RESIZE:
                curses.update_lines_cols()
                continue
            if key in (ord("h"), ord("H"), ord(" ")):
                self.pet.interact()
            elif key in (ord("a"), ord("A")):
                self.pet.event("annoyed")
                self.pet.trigger_animation("annoyed")
            elif key in (ord("e"), ord("E")):
                self.pet.event("excited")
            elif key in (ord("w"), ord("W")):
                self.pet.event("waking")
            elif key in (ord("p"), ord("P")):
                self.pet.trigger_animation("playing")
            elif 32 <= key < 127:
                self.pet.trigger_animation("surprised")
            # Mink has no keyboard controls; do not leave a key ahead of
            # subsequent mouse reports in the curses input queue.

    def draw(self) -> None:
        height, width = self.screen.getmaxyx()
        self.screen.erase()
        if height < 4 or width < 12:
            self._safe(0, 0, "mink")
            self.screen.refresh()
            return
        cyan = curses.color_pair(1)
        purple = curses.color_pair(2)
        soft = curses.color_pair(3)
        if time.monotonic() >= self._next_status:
            self._status = read_status(self._started)
            self._next_status = time.monotonic() + 1.0
        frames = self._pet_frames()
        if self.pet.animation_name == "walking" and width < 40:
            frames = get_animation("idle").frames
        lines = frames[self.pet.frame % len(frames)]
        status = "♫  playing  ♫" if self.track.status == "Playing" else (
            "·  paused  ·" if self.track.status == "Paused" else "·  waiting  ·")
        artist = _clip(self.track.artist or "unknown artist", max(1, width - 4))
        title = _clip(self.track.title or "untitled", max(1, width - 4))

        if layout_mode(width, height, self.config.layout) == "columns":
            self._draw_columns(lines, status, artist, title, height, width,
                               cyan, purple, soft)
            self.screen.refresh()
            return

        # If tmux temporarily collapses the pane below the normal seven-row
        # layout, keep the pet and every playback field visible in columns.
        if height < 7:
            pet_width = min(8, max(1, width // 3))
            for row, line in enumerate(lines[:height]):
                clipped = _clip(line, pet_width)
                self._safe(row, max(0, (pet_width - len(clipped)) // 2),
                           clipped, cyan if row else purple)
            info_x = pet_width
            info_width = max(1, width - info_x)
            compact_rows = (
                _clip(status, info_width),
                _clip(artist, info_width),
                _clip(title, info_width),
                _clip(f"{_time(self.track.position)} / "
                      f"{_time(self.track.duration)}", info_width),
            )
            for row, text in enumerate(compact_rows[:height]):
                self._safe(row, info_x, text, purple if row == 0 else soft)
            self.screen.refresh()
            return

        # Build one vertical flow so the pet can never cover or displace metadata.
        # The launcher provides nine rows, but this also remains usable when tmux
        # temporarily gives the pane fewer rows during a resize.
        top = 1 if height >= 10 else 0
        for row, line in enumerate(lines):
            clipped = _clip(line, width)
            self._safe(top + row, _center(clipped, width), clipped,
                       cyan if row else purple)
        next_row = top + len(lines)
        if self.pet.reaction == "alex_g" and height >= 11:
            message = "dev: i love alex g too <3"
            message = _clip(message, width)
            self._safe(next_row, _center(message, width), message, purple)
            next_row += 1

        status = _clip(status, width)
        if self.config.music_visible:
            self._safe(next_row, _center(status, width), status, purple)
            next_row += 1
            self._safe(next_row, _center(artist, width), artist, soft)
            self._safe(next_row + 1, _center(title, width), title, soft)
            next_row += 2
        if self.config.music_visible and self.track.status == "Playing" and next_row < height:
            progress = _bar(self.track.progress, max(0, width - 4))
            timing = f"{_time(self.track.position)} / {_time(self.track.duration)}"
            if next_row == height - 1:
                timing = _clip(timing, width)
                compact_width = max(0, width - len(timing) - 1)
                compact_progress = _bar(self.track.progress, compact_width)
                compact = _clip(f"{compact_progress} {timing}", width)
                self._safe(next_row, _center(compact, width), compact, cyan)
                next_row += 1
            else:
                if progress:
                    self._safe(next_row, _center(progress, width), progress, cyan)
                next_row += 1
                if next_row < height:
                    self._safe(next_row, _center(_clip(timing, width), width),
                               _clip(timing, width), soft)
                    next_row += 1
        if self.config.status_bar and next_row < height:
            self._safe(next_row, 0, self._status_line(width), soft)
        self.screen.refresh()

    def _status_line(self, width: int) -> str:
        values = {
            "song": self.track.title or "no music",
            "uptime": self._status.uptime,
            "cpu": self._status.cpu,
            "ram": self._status.memory,
            "hostname": self._status.hostname,
            "version": f"Mink {__version__}",
        }
        items = [values[item.strip()]
                 for item in self.config.status_items.split(",")
                 if item.strip() in values]
        return _clip("  ".join(items), width)

    def _draw_columns(self, lines, status, artist, title, height, width,
                      cyan, purple, soft) -> None:
        pet_width = min(24, max(16, width // 3))
        for row, line in enumerate(lines[:height]):
            clipped = _clip(line, pet_width - 2)
            self._safe(row, _center(clipped, pet_width), clipped,
                       cyan if row else purple)
        info_x = pet_width
        info_width = max(1, width - info_x)
        rows = [status, artist, title]
        if self.track.status == "Playing":
            rows.append(_bar(self.track.progress, max(0, info_width - 2)))
            rows.append(f"{_time(self.track.position)} / "
                        f"{_time(self.track.duration)}")
        if not self.config.music_visible:
            rows = [status]
        for row, text in enumerate(rows[:height]):
            self._safe(row, info_x + 1, _clip(text, info_width - 1),
                       purple if row == 0 else soft)
        if self.config.status_bar and len(rows) + 1 < height:
            self._safe(len(rows) + 1, info_x + 1,
                       self._status_line(info_width - 1), soft)

    def _command(self, command: str) -> bool:
        if command == "play":
            return self.player.command("play")
        if command == "pause":
            return self.player.command("pause")
        if command in {"toggle", "play-pause"}:
            return self.player.command("play-pause")
        if command == "next":
            return self.player.command("next")
        if command in {"prev", "previous"}:
            return self.player.command("previous")
        if command.startswith("volume "):
            try:
                level = max(0, min(100, int(command.split()[1]))) / 100
            except (IndexError, ValueError):
                return False
            return self.player.set_volume(level)
        return command == "status"

    def run(self) -> None:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, self.theme.colors["cyan"], -1)
        curses.init_pair(2, self.theme.colors["purple"], -1)
        curses.init_pair(3, self.theme.colors["soft"], -1)
        self._configure_input()
        self._open_commands()
        next_poll = 0.0
        try:
            while True:
                now = time.monotonic()
                for command in self._commands():
                    if command in {"quit", "close"}:
                        self._goodbye()
                        return
                    self._command(command)
                self._consume_input()
                if now >= next_poll:
                    self.update(now)
                    next_poll = now + self.config.poll_interval
                if self.config.animation and now - self._last_draw >= self.config.tick_interval:
                    self.draw()
                    self._last_draw = now
                time.sleep(0.025)
        finally:
            if self.command_socket:
                self.command_socket.close()
            if self.socket_path:
                try:
                    os.unlink(self.socket_path)
                except FileNotFoundError:
                    pass

    def _goodbye(self) -> None:
        self.pet.trigger_animation("goodbye")
        for _ in range(6):
            self.draw()
            time.sleep(0.04)


def run_ui() -> None:
    curses.wrapper(lambda screen: MinkUI(screen).run())
