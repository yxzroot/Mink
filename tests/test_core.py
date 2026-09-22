import unittest
import random

from mink.core import Pet, PetState, Track, parse_playerctl_line


class CoreTests(unittest.TestCase):
    def test_parse_metadata_and_progress(self):
        track = parse_playerctl_line("Song\tArtist\tPlaying\t30\t120000000")
        self.assertEqual(track.title, "Song")
        self.assertEqual(track.artist, "Artist")
        self.assertAlmostEqual(track.progress, 0.25)

    def test_malformed_metadata_is_safe(self):
        track = parse_playerctl_line("Song")
        self.assertEqual(track.status, "Stopped")
        self.assertEqual(track.duration, 0)

    def test_progress_is_clamped(self):
        self.assertEqual(Track(position=20, duration=10).progress, 1)

    def test_pet_reacts_and_sleeps(self):
        pet = Pet()
        pet.tick(0)
        pet.tick(1, False)
        self.assertEqual(pet.state, PetState.IDLE)
        pet.event("playing", 2)
        pet.tick(2.4, True)
        self.assertEqual(pet.state, PetState.MUSIC)
        pet.event("paused", 3)
        pet.tick(26, False)
        self.assertEqual(pet.state, PetState.SLEEPING)

    def test_animation_frames_actually_advance(self):
        pet = Pet(random.Random(1))
        pet.tick(0)
        first = pet.frame
        pet.tick(6.0, False)
        self.assertEqual(pet.frame, first)
        self.assertIsNotNone(pet.reaction)
        music = Pet(random.Random(1))
        music.event("playing", 0)
        music.tick(0.1, True)
        music_frame = music.frame
        music.tick(15.0, True)
        self.assertIsNotNone(music.reaction)
        music.tick(15.3, True)
        self.assertEqual(music.state, PetState.MUSIC)
        self.assertNotEqual(music.frame, music_frame)

    def test_alex_reaction_is_temporary(self):
        pet = Pet()
        pet.event("playing", 1)
        pet.trigger_alex_g(2)
        self.assertEqual(pet.reaction, "alex_g")
        pet.tick(33, True)
        self.assertIsNone(pet.reaction)
        self.assertEqual(pet.state, PetState.MUSIC)


if __name__ == "__main__":
    unittest.main()
