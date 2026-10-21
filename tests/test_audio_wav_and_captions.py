"""tests/test_audio_wav_and_captions.py

Behavioral Test Suite for Neural Audio, WAV Normalization,
Spoken-to-Display Token Mapping, Word Timings, and Caption Chunking.
"""

import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from engine.audio.tts_whisper import (
    prepare_tts_text_with_token_map,
    collapse_spoken_word_boundaries,
    sanitize_spoken_narration,
)
from engine.audio.scene_audio import (
    get_audio_duration,
    concatenate_scene_audios,
)
from engine.timeline.timeline_mapper import (
    chunk_caption_words,
    resolve_word_timestamp,
    map_scene_timeline,
)


class TestAudioWavAndCaptions(unittest.TestCase):

    def test_spoken_to_display_token_mapping(self):
        """
        Verify technical code tokens (step.run(), inngest.createFunction(), @acme/sdk)
        are mapped to natural spoken English for TTS while preserving original display syntax.
        """
        display_text = "Wrap your logic in `step.run()` to guarantee safe retries. Then deploy @acme/sdk."
        spoken_text, mappings = prepare_tts_text_with_token_map(display_text)

        self.assertIn("step dot run", spoken_text)
        self.assertIn("the acme sdk package", spoken_text)
        self.assertNotIn("`", spoken_text)

        # Check mapping for step.run()
        step_mapping = next((m for m in mappings if "step.run()" in m["display_word"]), None)
        self.assertIsNotNone(step_mapping)
        self.assertEqual(step_mapping["spoken_words"], ["step", "dot", "run"])

        # Check mapping for @acme/sdk
        pkg_mapping = next((m for m in mappings if "@acme/sdk" in m["display_word"]), None)
        self.assertIsNotNone(pkg_mapping)
        self.assertEqual(pkg_mapping["spoken_words"], ["the", "acme", "sdk", "package"])

    def test_collapse_spoken_word_boundaries(self):
        """
        Verify multi-word Edge-TTS WordBoundary events are collapsed back into single display tokens.
        """
        raw_events = [
            {"word": "Wrap", "start": 0.1, "end": 0.3},
            {"word": "in", "start": 0.31, "end": 0.45},
            {"word": "step", "start": 0.46, "end": 0.7},
            {"word": "dot", "start": 0.71, "end": 0.9},
            {"word": "run", "start": 0.91, "end": 1.25},
            {"word": "safely", "start": 1.26, "end": 1.7},
        ]
        mappings = [
            {"display_word": "Wrap", "spoken_words": ["Wrap"]},
            {"display_word": "in", "spoken_words": ["in"]},
            {"display_word": "step.run()", "spoken_words": ["step", "dot", "run"]},
            {"display_word": "safely.", "spoken_words": ["safely"]},
        ]

        collapsed = collapse_spoken_word_boundaries(raw_events, mappings)
        self.assertEqual(len(collapsed), 4)

        step_col = collapsed[2]
        self.assertEqual(step_col["word"], "step.run()")
        self.assertEqual(step_col["start"], 0.46)
        self.assertEqual(step_col["end"], 1.25)

        last_col = collapsed[3]
        self.assertEqual(last_col["word"], "safely.")
        self.assertEqual(last_col["start"], 1.26)
        self.assertEqual(last_col["end"], 1.7)

    def test_caption_chunking_with_zero_cross_sentence_bleeding(self):
        """
        Verify caption_chunks hard-split strictly on sentence punctuation (. ! ?),
        never bleed across periods, and split long clauses cleanly.
        """
        words = [
            {"word": "First", "start": 0.0, "end": 0.3},
            {"word": "sentence", "start": 0.35, "end": 0.7},
            {"word": "ends", "start": 0.75, "end": 1.0},
            {"word": "here.", "start": 1.05, "end": 1.4},
            {"word": "Second", "start": 1.6, "end": 1.9},
            {"word": "sentence", "start": 1.95, "end": 2.2},
            {"word": "starts", "start": 2.25, "end": 2.5},
            {"word": "now.", "start": 2.55, "end": 2.9},
        ]

        chunks = chunk_caption_words(words)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["text"], "First sentence ends here.")
        self.assertEqual(chunks[0]["start"], 0.0)
        self.assertEqual(chunks[0]["end"], 1.4)

        self.assertEqual(chunks[1]["text"], "Second sentence starts now.")
        self.assertEqual(chunks[1]["start"], 1.6)
        self.assertEqual(chunks[1]["end"], 2.9)

    def test_timeline_mapper_exact_cumulative_sums(self):
        """
        Verify TimelineMapper calculates scene start_time and duration as exact cumulative sums
        without arbitrary duration clamping.
        """
        scenes = [
            {
                "scene_id": 1,
                "title": "Scene 1",
                "emphasis_word": "start",
                "narration": "Let us start now.",
            },
            {
                "scene_id": 2,
                "title": "Scene 2",
                "visual_type": "workflow_state_transition",
                "visual": {
                    "events": [
                        {"target": "step1", "action": "succeed", "at_word": "step"},
                    ]
                },
                "narration": "Execute the next step cleanly.",
            },
        ]
        scene_audio_results = [
            {
                "scene_id": 1,
                "duration": 2.15,
                "words": [
                    {"word": "Let", "start": 0.1, "end": 0.3},
                    {"word": "us", "start": 0.35, "end": 0.6},
                    {"word": "start", "start": 0.65, "end": 1.1},
                    {"word": "now.", "start": 1.15, "end": 1.5},
                ],
            },
            {
                "scene_id": 2,
                "duration": 3.42,
                "words": [
                    {"word": "Execute", "start": 0.1, "end": 0.5},
                    {"word": "the", "start": 0.55, "end": 0.7},
                    {"word": "next", "start": 0.75, "end": 1.0},
                    {"word": "step", "start": 1.05, "end": 1.4},
                    {"word": "cleanly.", "start": 1.45, "end": 1.9},
                ],
            },
        ]

        timed_scenes, master_words, master_chunks = map_scene_timeline(scenes, scene_audio_results)

        # Scene 1 checks
        self.assertEqual(timed_scenes[0]["start_time"], 0.0)
        self.assertEqual(timed_scenes[0]["duration"], 2.15)
        self.assertEqual(timed_scenes[0]["end_time"], 2.15)
        self.assertEqual(timed_scenes[0]["emphasis_time"], 0.65)

        # Scene 2 checks (starts exactly at 2.15)
        self.assertEqual(timed_scenes[1]["start_time"], 2.15)
        self.assertEqual(timed_scenes[1]["duration"], 3.42)
        self.assertEqual(timed_scenes[1]["end_time"], 5.57)

        # Event activation check (resolved from at_word "step": 2.15 + 1.05 = 3.20)
        ev = timed_scenes[1]["visual"]["events"][0]
        self.assertEqual(ev["timestamp_sec"], 3.2)

        # Caption chunks
        self.assertGreater(len(master_chunks), 0)


if __name__ == "__main__":
    unittest.main()

