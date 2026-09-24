import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from mink.config import Config
from mink.core import Pet, PetState
from mink.theme import DEFAULT_THEME, get_theme
from mink.animation import ANIMATIONS, get_animation


class ConfigurationTests(unittest.TestCase):
    def test_json_and_environment_overrides(self):
        path = Path("tests/.config-test.json")
        try:
            path.write_text(json.dumps({"sleep_after": 3, "theme": "custom"}),
                            encoding="utf-8")
            with patch.dict(os.environ, {"MINK_SLEEP_AFTER": "5"}, clear=False):
                config = Config.load(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(config.sleep_after, 5)
        self.assertEqual(config.theme, "custom")


class ThemeTests(unittest.TestCase):
    def test_default_theme_is_complete_and_stable(self):
        self.assertIs(get_theme(), DEFAULT_THEME)
        self.assertTrue(DEFAULT_THEME.idle)
        self.assertTrue(DEFAULT_THEME.music)
        self.assertTrue(DEFAULT_THEME.sleeping)
        self.assertIn("happy", DEFAULT_THEME.reactions)

    def test_named_themes_fall_back_safely(self):
        self.assertNotEqual(get_theme("dracula"), DEFAULT_THEME)
        self.assertNotEqual(get_theme("tokyo-night"), DEFAULT_THEME)
        self.assertIs(get_theme("does-not-exist"), DEFAULT_THEME)

    def test_invalid_boolean_and_layout_use_defaults(self):
        path = Path("tests/.config-invalid.json")
        try:
            path.write_text(json.dumps({
                "animation": "not-bool", "layout": "diagonal",
                "poll_interval": -1,
                "status_bar": True,
            }), encoding="utf-8")
            config = Config.load(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertTrue(config.animation)
        self.assertEqual(config.layout, "auto")
        self.assertEqual(config.poll_interval, 1.0)
        self.assertTrue(config.status_bar)


class StateTests(unittest.TestCase):
    def test_animation_catalog_has_requested_sequences(self):
        for name in ("idle", "blink", "sleepy", "sleeping", "waking",
                     "happy", "excited", "annoyed", "angry", "surprised",
                     "looking_around", "stretching", "dancing", "goodbye"):
            animation = get_animation(name)
            self.assertEqual(animation.name, name)
            self.assertGreaterEqual(len(animation.frames), 3)
        self.assertGreaterEqual(len(get_animation("walking").frames), 8)
        for name in ("eating", "drinking", "playing", "love"):
            self.assertGreaterEqual(len(get_animation(name).frames), 6)
        self.assertFalse(ANIMATIONS["goodbye"].loop)
    def test_harmless_events_select_extended_states(self):
        pet = Pet()
        for event, expected in (
            ("happy", PetState.HAPPY),
            ("annoyed", PetState.ANNOYED),
            ("excited", PetState.EXCITED),
            ("waking", PetState.WAKING),
            ("sleeping", PetState.SLEEPING),
        ):
            pet.event(event, 1)
            self.assertEqual(pet.state, expected)

    def test_waking_returns_to_idle(self):
        pet = Pet()
        pet.event("waking", 1)
        pet.tick(1.6, False)
        self.assertEqual(pet.state, PetState.IDLE)

    def test_interaction_moods_are_temporary(self):
        pet = Pet()
        pet.event("happy", 1)
        self.assertEqual(pet.state, PetState.HAPPY)
        pet.tick(4, False)
        self.assertEqual(pet.state, PetState.IDLE)

    def test_live_animation_frames_advance_and_loop(self):
        pet = Pet()
        pet.event("happy", 1)
        pet.tick(1.5, False)
        first = pet.frame
        pet.tick(2.0, False)
        self.assertNotEqual(pet.frame, first)
        self.assertLess(pet.frame, len(get_animation("happy").frames))

    def test_one_shot_animation_returns_to_previous_animation(self):
        pet = Pet()
        self.assertTrue(pet.trigger_animation("blink", 1))
        pet.tick(1.3, False)
        self.assertEqual(pet.animation_name, "idle")
        self.assertFalse(pet.trigger_animation("missing", 2))

    def test_normal_interactions_escalate_and_reach_positive_animations(self):
        pet = Pet()
        self.assertEqual(pet.interact(1), "love")
        self.assertEqual(pet.animation_name, "love")
        self.assertEqual(pet.interact(2), "annoyed")
        self.assertEqual(pet.interact(3), "annoyed")
        self.assertEqual(pet.interact(4), "angry")

    def test_music_and_inactivity_map_to_dancing_sleepy_and_sleeping(self):
        pet = Pet()
        pet.event("playing", 1)
        self.assertEqual(pet.animation_name, "dancing")
        pet.event("paused", 2)
        pet.tick(16.5, False)
        self.assertEqual(pet.animation_name, "sleepy")
        pet.tick(23.5, False)
        self.assertEqual(pet.state, PetState.SLEEPING)
        self.assertEqual(pet.animation_name, "sleeping")

    def test_random_idle_can_be_disabled(self):
        pet = Pet(config=Config(random_idle=False))
        pet.tick(100, False)
        self.assertEqual(pet.animation_name, "idle")


if __name__ == "__main__":
    unittest.main()
