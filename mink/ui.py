"""Compact curses UI for Mink's dedicated tmux pane."""

import curses
import os
import re
import socket
import subprocess
import time
from typing import Optional

from .core import Pet, PetState, Track
from .media import Player


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
REACTION_FRAMES = (
    ("/\\_/\\\\", "( >.< )", " > ^ <"),
    ("/\\_/\\\\", "( >.< )", " > ^ <"),
)
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


class MinkUI:
    def __init__(self, stdscr: "curses.window", player: Optional[Player] = None):
        self.screen = stdscr
        self.player = player or Player()
        self.pet = Pet()
        self.track = Track()
        self.previous_track = Track()
        self.socket_path = os.environ.get("MINK_SOCKET", "")
        self.command_socket: Optional[socket.socket] = None
        self._last_pane_command = ""
        self._last_draw = 0.0

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
            if 0 <= y < self.screen.getmaxyx()[0] and x < width - 1:
                self.screen.addnstr(y, x, text, width - x - 1, attr)
        except curses.error:
            pass

    def _pet_frames(self):
        if self.pet.reaction == "alex_g":
            return ALEX_FRAMES
        if self.pet.reaction == "terminal":
            return (("/\\_/\\\\", "( >.< )", " > ^ <"),
                    ("/\\_/\\\\", "( o.o )", " > ^ <"))
        if self.pet.reaction in REACTION_FRAMES:
            return REACTION_FRAMES[self.pet.reaction]
        return {
            PetState.IDLE: IDLE_FRAMES,
            PetState.MUSIC: MUSIC_FRAMES,
            PetState.SLEEP: SLEEP_FRAMES,
        }[self.pet.state]

    def draw(self) -> None:
        height, width = self.screen.getmaxyx()
        self.screen.erase()
        if height < 5 or width < 12:
            self._safe(0, 0, "mink")
            self.screen.refresh()
            return
        cyan = curses.color_pair(1)
        purple = curses.color_pair(2)
        soft = curses.color_pair(3)
        frames = self._pet_frames()
        lines = frames[self.pet.frame % len(frames)]
        # Mink lives in the top-right corner; leave the rest of the pane quiet.
        top = 1
        for row, line in enumerate(lines):
            self._safe(top + row, _center(line, width), line,
                       cyan if row else purple)
        if self.pet.reaction == "alex_g" and height >= 8:
            message = "dev: i love alex g too <3"
            self._safe(top + len(lines) + 1, _center(message, width),
                       _clip(message, width - 1), purple)
        if width >= 18 and height >= 9:
            status = "♫  playing  ♫" if self.track.status == "Playing" else (
                "·  paused  ·" if self.track.status == "Paused" else "·  waiting  ·")
            info_top = top + len(lines) + 2
            self._safe(info_top, _center(status, width), status, purple)
            if self.track.available and info_top + 4 < height:
                artist = _clip(self.track.artist or "unknown artist", width - 4)
                title = _clip(self.track.title or "untitled", width - 4)
                self._safe(info_top + 1, _center(artist, width), artist, soft)
                self._safe(info_top + 2, _center(title, width), title, soft)
                if self.track.status == "Playing":
                    progress = _bar(self.track.progress, width - 4)
                    self._safe(info_top + 3, _center(progress, width), progress, cyan)
                    timing = f"{_time(self.track.position)} / {_time(self.track.duration)}"
                    self._safe(info_top + 4, _center(timing, width), timing, soft)
        self.screen.refresh()

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
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
        self._open_commands()
        next_poll = 0.0
        try:
            while True:
                now = time.monotonic()
                for command in self._commands():
                    if command in {"quit", "close"}:
                        return
                    self._command(command)
                if now >= next_poll:
                    self.update(now)
                    next_poll = now + 1.0
                if now - self._last_draw >= 0.08:
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


def run_ui() -> None:
    curses.wrapper(lambda screen: MinkUI(screen).run())
