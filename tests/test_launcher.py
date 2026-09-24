import sys
import unittest
from unittest.mock import patch

from mink import launcher


class LauncherTests(unittest.TestCase):
    def test_version_command(self):
        with patch.object(sys, "argv", ["mink", "--version"]):
            with patch("builtins.print") as output:
                self.assertEqual(launcher.main(), 0)
        output.assert_called_once_with("Mink 0.1.2")

    def test_unknown_command_is_rejected(self):
        with patch.object(sys, "argv", ["mink", "unknown"]):
            with patch("builtins.print") as output:
                self.assertEqual(launcher.main(), 2)
        self.assertTrue(output.called)


if __name__ == "__main__":
    unittest.main()
