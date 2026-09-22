import unittest

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


if __name__ == "__main__":
    unittest.main()
