import subprocess
import unittest
from unittest.mock import patch

from mink.media import Player


class MediaTests(unittest.TestCase):
    def test_no_player_is_stopped(self):
        player = Player()
        player.binary = "/usr/bin/playerctl"
        with patch("mink.media.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       [], 1, "", "")):
            track = player.read()
        self.assertEqual(track.status, "Stopped")
        self.assertIsNone(player.selected_player)

    def test_playing_player_wins_when_multiple_are_available(self):
        player = Player()
        player.binary = "/usr/bin/playerctl"

        def run(command, **_kwargs):
            if "--list-all" in command:
                return subprocess.CompletedProcess(command, 0, "paused\nplaying\n", "")
            name = command[command.index("--player") + 1]
            status = "Paused" if name == "paused" else "Playing"
            output = f"Song {name}\tArtist\t{status}\t30000000\t120000000\n"
            return subprocess.CompletedProcess(command, 0, output, "")

        with patch("mink.media.subprocess.run", side_effect=run):
            track = player.read()
        self.assertEqual(track.status, "Playing")
        self.assertEqual(player.selected_player, "playing")


if __name__ == "__main__":
    unittest.main()
