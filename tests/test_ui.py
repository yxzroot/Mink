import unittest
import curses
from unittest.mock import patch

from mink.ui import ALEX_FRAMES, MinkUI
from mink.launcher import COMMANDS


class UITests(unittest.TestCase):
    def test_alex_g_matching_is_case_insensitive_and_exact(self):
        self.assertTrue(MinkUI._is_alex_g("Alex G"))
        self.assertTrue(MinkUI._is_alex_g("alex g"))
        self.assertTrue(MinkUI._is_alex_g(" ALEX G "))
        self.assertTrue(MinkUI._is_alex_g("ALEX G, guest artist"))
        self.assertTrue(MinkUI._is_alex_g("guest artist; Alex G"))
        self.assertTrue(MinkUI._is_alex_g("['Alex G', 'guest artist']"))
        self.assertFalse(MinkUI._is_alex_g("Alexander G"))
        self.assertTrue(MinkUI._is_alex_g("kaden", "east coast - alex g"))
        self.assertFalse(MinkUI._is_alex_g("kaden", "Alex G cover"))

    def test_alex_g_face_keeps_the_full_pet_shape(self):
        self.assertTrue(all("( ^.^ )" in frame for frame in ALEX_FRAMES))
        self.assertTrue(all("^^" not in frame for frame in ALEX_FRAMES))

    def test_close_is_a_global_control_command(self):
        self.assertIn("close", COMMANDS)

    def test_input_setup_enables_curses_mouse_reporting(self):
        class Screen:
            def nodelay(self, _enabled):
                pass

        ui = MinkUI(Screen())
        with patch("mink.ui.curses.mousemask") as mousemask, \
                patch("mink.ui.curses.mouseinterval"), \
                patch.object(ui.screen, "nodelay"):
            ui._configure_input()

        mousemask.assert_called_once_with(curses.ALL_MOUSE_EVENTS)

    def test_mouse_events_are_consumed_without_blocking_later_mouse_events(self):
        class Screen:
            def __init__(self):
                self.keys = [curses.KEY_MOUSE, ord("q"), curses.KEY_MOUSE, -1]

            def getch(self):
                return self.keys.pop(0)

        screen = Screen()
        ui = MinkUI(screen)
        with patch("mink.ui.curses.getmouse") as getmouse:
            ui._consume_input()

        self.assertEqual(getmouse.call_count, 2)


if __name__ == "__main__":
    unittest.main()
