"""
Unit Tests for Phase 5:
Vertical Space Maximization (80-90% Fill), Scene Timing Continuity & Rich Animations.

Validates:
1. Contiguous scene intervals:
   - scene[0].start_time == 0.0
   - For all i: scene[i].end_time == scene[i+1].start_time
   - scene[-1].end_time >= total_duration
2. Minimum scene duration enforcement:
   - Every scene has duration >= 2.5s (eliminating 0.3s flash cuts).
3. Intelligent context-aware scene routing in Choreographer:
   - Narration mentioning neural networks, autoencoders, latent spaces, backpropagation routes to 'neural_code_split'.
4. Unicode emoji glyph stripping:
   - Palettes and scene badges contain no raw Unicode emojis that render as tofu [▯] in headless Linux Chromium.
"""

import unittest
from engine.timeline.beats import align_timeline
from engine.timeline.choreographer import choreograph_scenes, THEME_PALETTES


class TestPhase5VerticalAndContinuity(unittest.TestCase):

    def setUp(self):
        # 12 words spanning 10.0 seconds
        self.sample_words = [
            {"word": "Most", "start": 0.4, "end": 0.8},
            {"word": "engineers", "start": 0.9, "end": 1.4},
            {"word": "pick", "start": 1.5, "end": 1.8},
            {"word": "the", "start": 1.9, "end": 2.2},
            {"word": "wrong", "start": 2.3, "end": 2.7},
            {"word": "clustering", "start": 2.8, "end": 3.4},
            {"word": "model", "start": 3.5, "end": 4.0},
            {"word": "for", "start": 4.2, "end": 4.6},
            {"word": "arbitrary", "start": 4.8, "end": 5.4},
            {"word": "dense", "start": 5.6, "end": 6.2},
            {"word": "shapes", "start": 6.4, "end": 7.0},
            {"word": "today", "start": 7.2, "end": 8.0},
        ]
        self.total_duration = 10.0

    def test_contiguous_scene_intervals_zero_gaps(self):
        """Verify that align_beats_with_scenes produces 100% contiguous scene intervals from 0.0 to total_duration."""
        scenes = [
            {
                "scene_type": "concept",
                "title": "Hook",
                "spoken_text": "Most engineers pick the wrong clustering model.",
            },
            {
                "scene_type": "bento_grid",
                "title": "ML Overview",
                "spoken_text": "for arbitrary dense shapes today.",
            },
        ]

        timed = align_timeline(scenes, self.sample_words, self.total_duration)

        self.assertGreaterEqual(len(timed), 2)
        # 1. First scene start_time must be exactly 0.0
        self.assertEqual(timed[0]["start_time"], 0.0)

        # 2. Every scene i end_time must equal scene i+1 start_time
        for i in range(len(timed) - 1):
            self.assertEqual(
                timed[i]["end_time"],
                timed[i + 1]["start_time"],
                f"Scene {i} end_time ({timed[i]['end_time']}) does not match scene {i+1} start_time ({timed[i+1]['start_time']})"
            )

        # 3. Last scene end_time must cover the full duration
        self.assertGreaterEqual(timed[-1]["end_time"], self.total_duration)

    def test_minimum_scene_duration_eliminates_flash_cuts(self):
        """Verify that every timed scene has duration >= 2.5s, preventing 0.3s flash cuts."""
        # 4 scenes with short word mappings
        scenes = [
            {"scene_type": "concept", "spoken_text": "Most engineers"},
            {"scene_type": "bento_grid", "spoken_text": "pick the"},
            {"scene_type": "algorithm_explorer", "spoken_text": "wrong clustering model"},
            {"scene_type": "concept", "spoken_text": "for arbitrary dense shapes today"},
        ]

        timed = align_timeline(scenes, self.sample_words)

        for i, s in enumerate(timed):
            duration = s["end_time"] - s["start_time"]
            self.assertGreaterEqual(
                duration,
                2.5,
                f"Scene {i} duration ({duration:.2f}s) is less than the mandatory minimum 2.5s!"
            )

    def test_choreographer_auto_routes_neural_narration(self):
        """Verify that narration mentioning neural networks, autoencoders, or latent space routes to neural_code_split."""
        timeline_data = {
            "total_duration": 12.0,
            "scenes": [
                {
                    "scene_type": "concept",
                    "title": "Deep Learning Bottleneck",
                    "spoken_text": "An autoencoder compresses high dimensional inputs down to a compact latent space representation.",
                    "start_time": 0.0,
                    "end_time": 6.0,
                },
                {
                    "scene_type": "concept",
                    "title": "Backprop",
                    "spoken_text": "Backpropagation computes the gradient of loss layer by layer across our neural network weights.",
                    "start_time": 6.0,
                    "end_time": 12.0,
                },
            ],
            "words": [
                {"word": "An", "start": 0.5, "end": 1.0},
                {"word": "autoencoder", "start": 1.1, "end": 2.0},
            ]
        }

        scenes = choreograph_scenes(timeline_data["scenes"], timeline_data["words"], domain="systems", fps=30)

        self.assertEqual(scenes[0]["scene_type"], "neural_code_split")
        self.assertEqual(scenes[1]["scene_type"], "neural_code_split")
        self.assertIn("neural", scenes[0]["choreography"])

    def test_no_raw_unicode_emojis_in_palettes(self):
        """Verify that THEME_PALETTES contain no raw Unicode emojis that turn into tofu boxes [▯] on headless Linux."""
        for name, palette in THEME_PALETTES.items():
            badge_tag = palette.get("badge_tag", "")
            for ch in badge_tag:
                code_point = ord(ch)
                # Check for standard emoji Unicode ranges (0x1F300 - 0x1FAFF)
                self.assertFalse(
                    0x1F300 <= code_point <= 0x1FAFF or 0x2600 <= code_point <= 0x27BF,
                    f"Palette '{name}' contains raw emoji glyph '{ch}' in badge_tag '{badge_tag}'!"
                )


if __name__ == "__main__":
    unittest.main()

