"""Optional playerctl integration."""

import shutil
import subprocess
from typing import List, Optional, Tuple

from .core import Track, parse_playerctl_line


class Player:
    FORMAT = "{{title}}\t{{artist}}\t{{status}}\t{{position}}\t{{mpris:length}}"

    def __init__(self) -> None:
        self.binary = shutil.which("playerctl")
        self.selected_player: Optional[str] = None

    def _players(self) -> List[str]:
        if not self.binary:
            return []
        try:
            result = subprocess.run(
                [self.binary, "--list-all", "--no-messages"],
                capture_output=True, text=True, timeout=0.7, check=False,
            )
        except subprocess.TimeoutExpired:
            return []
        if result.returncode != 0:
            return []
        return [name.strip() for name in result.stdout.splitlines() if name.strip()]

    def _metadata(self, player: str) -> Optional[Track]:
        if not self.binary:
            return None
        try:
            result = subprocess.run(
                [self.binary, "--player", player, "--no-messages",
                 "--format", self.FORMAT, "metadata"],
                capture_output=True, text=True, timeout=0.7, check=False,
            )
        except subprocess.TimeoutExpired:
            return None
        if result.returncode != 0 or not result.stdout.strip():
            return Track(status="Stopped")
        return parse_playerctl_line(result.stdout.splitlines()[0])

    def read(self) -> Track:
        players = self._players()
        if not players:
            self.selected_player = None
            return Track(status="Stopped")

        metadata: List[Tuple[str, Track]] = []
        for player in players:
            track = self._metadata(player)
            if track is not None:
                metadata.append((player, track))
        if not metadata:
            self.selected_player = None
            return Track(status="Stopped")

        playing = next(
            ((name, track) for name, track in metadata
             if track.status == "Playing"),
            None,
        )
        selected = next(
            ((name, track) for name, track in metadata
             if name == self.selected_player),
            None,
        )
        name, track = playing or selected or metadata[0]
        self.selected_player = name
        return track

    def command(self, action: str) -> bool:
        if not self.binary:
            return False
        command = [self.binary]
        if self.selected_player:
            command.extend(["--player", self.selected_player])
        command.extend([action])
        try:
            return subprocess.run(
                command, capture_output=True, timeout=1, check=False,
            ).returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def volume(self, amount: float) -> bool:
        return self.set_volume(amount)

    def set_volume(self, level: float) -> bool:
        if not self.binary:
            return False
        command = [self.binary]
        if self.selected_player:
            command.extend(["--player", self.selected_player])
        command.extend(["volume", str(max(0.0, min(1.0, level)))])
        try:
            return subprocess.run(
                command, capture_output=True, timeout=1, check=False,
            ).returncode == 0
        except subprocess.TimeoutExpired:
            return False
