"""
tests/test_phase6_semantic_accuracy.py

Unit and regression tests for Phase 6:
  1. Negative Imperatives Semantic Badge Polarity (engine/timeline/enhancer.py).
  2. Word Timestamp Hyphenation Sanitization (engine/audio/tts_whisper.py).
  3. Context-Driven Concept Scene Choreography (engine/timeline/choreographer.py).
"""

import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))

from timeline.enhancer import classify_scene, SEMANTIC_BADGES
from audio.tts_whisper import merge_hyphenated_tokens, validate_and_sanitize_word_timestamps
from timeline.choreographer import choreograph_scenes


class TestPhase6SemanticAccuracy(unittest.TestCase):
    # --------------------------------------------------------------------------
    # 1. Negative Imperatives Semantic Badge Polarity Tests
    # --------------------------------------------------------------------------

    def test_negative_imperatives_classify_as_warning(self):
        """
        Verify negative/warning imperatives ('stop', 'never', 'don't', 'avoid',
        'wrong', 'fails', 'breaks', 'waste', 'mistake') always force classification
        to 'Anti-Pattern' / warning, even when positive or neural keywords are present.
        """
        negative_scenes = [
            {
                "spoken_text": "Stop reaching for massive neural networks for simple clustering.",
                "title": "Neural Networks Gone Wrong",
                "scene_type": "code_reveal",
            },
            {
                "spoken_text": "Never burn expensive GPU compute when classical algorithms converge faster.",
                "title": "GPU Overkill",
                "scene_type": "terminal",
            },
            {
                "spoken_text": "Non-convex data breaks K-Means spherical Voronoi boundary.",
                "title": "Non-Convex Geometry",
                "scene_type": "concept",
            },
            {
                "spoken_text": "Don't waste compute training a transformer for tabular linear regression.",
                "title": "Wasted Compute",
                "scene_type": "comparison",
            },
            {
                "spoken_text": "Avoid this naive clustering mistake on curved manifolds.",
                "title": "Common Mistake",
                "scene_type": "code_reveal",
            },
            {
                "spoken_text": "The wrong approach is trying to force linear hyperplanes onto moons.",
                "title": "Wrong Model Selection",
                "scene_type": "concept",
            },
            {
                "spoken_text": "K-Means fails miserably on interlocking half-moon geometries.",
                "title": "Voronoi Partition Failure",
                "scene_type": "concept",
            },
        ]

        for scene in negative_scenes:
            badge = classify_scene(scene)
            self.assertIsNotNone(badge, f"Failed to attach badge to scene: {scene['spoken_text']}")
            self.assertEqual(
                badge["type"],
                "warning",
                f"Expected warning badge for negative imperative: '{scene['spoken_text']}', got {badge['type']}",
            )
            self.assertEqual(
                badge["category"],
                "anti_pattern",
                f"Expected category 'anti_pattern', got {badge['category']}",
            )
            self.assertEqual(badge["label"], "Anti-Pattern")

    def test_positive_imperatives_still_classify_as_solution(self):
        """Verify positive solutions without negative words still classify as best practice."""
        positive_scenes = [
            {
                "spoken_text": "Here is the recommended pythonic one-liner with walrus operator.",
                "scene_type": "code_transform",
            },
            {
                "spoken_text": "This optimal clean solution eliminates the inner loop.",
                "scene_type": "code_reveal",
            },
        ]
        for scene in positive_scenes:
            badge = classify_scene(scene)
            self.assertIsNotNone(badge)
            self.assertEqual(badge["type"], "success")
            self.assertEqual(badge["category"], "solution")

    # --------------------------------------------------------------------------
    # 2. Subtitle Hyphenation & Whisper Token Sanitization Tests
    # --------------------------------------------------------------------------

    def test_merge_hyphenated_compound_pairs(self):
        """Verify known compound pairs like K-MEANS, T-SNE, AUTO-ENCODERS are merged into single tokens."""
        raw_tokens = [
            {"word": "use", "start": 0.0, "end": 0.3},
            {"word": "k", "start": 0.35, "end": 0.5},
            {"word": "means", "start": 0.52, "end": 0.85},
            {"word": "for", "start": 0.9, "end": 1.1},
            {"word": "non", "start": 1.2, "end": 1.4},
            {"word": "convex", "start": 1.42, "end": 1.7},
            {"word": "data", "start": 1.75, "end": 2.0},
        ]
        merged = merge_hyphenated_tokens(raw_tokens)
        words = [t["word"] for t in merged]

        self.assertIn("K-MEANS", words)
        self.assertIn("NON-CONVEX", words)
        self.assertEqual(len(merged), 5)

        # Check preserved timestamps
        kmeans_token = next(t for t in merged if t["word"] == "K-MEANS")
        self.assertEqual(kmeans_token["start"], 0.35)
        self.assertEqual(kmeans_token["end"], 0.85)

    def test_merge_isolated_and_trailing_hyphens(self):
        """Verify isolated hyphens and trailing/leading hyphens are merged without split chunks."""
        raw_tokens = [
            {"word": "high-", "start": 0.0, "end": 0.3},
            {"word": "dimensional", "start": 0.32, "end": 0.7},
            {"word": "latent", "start": 0.75, "end": 1.0},
            {"word": "auto", "start": 1.1, "end": 1.3},
            {"word": "-", "start": 1.32, "end": 1.35},
            {"word": "encoders", "start": 1.36, "end": 1.8},
        ]
        merged = merge_hyphenated_tokens(raw_tokens)
        words = [t["word"] for t in merged]

        self.assertTrue(any("high-dimensional" in w.lower() for w in words))
        self.assertTrue(any("auto-encoder" in w.lower() for w in words))

    def test_validate_and_sanitize_word_timestamps_hyphenation(self):
        """Verify validate_and_sanitize_word_timestamps automatically merges split hyphens."""
        words = [
            {"word": "K", "start": 0.1, "end": 0.3},
            {"word": "-means", "start": 0.3, "end": 0.6},
        ]
        sanitized = validate_and_sanitize_word_timestamps(words)
        self.assertEqual(len(sanitized), 1)
        self.assertEqual(sanitized[0]["word"], "K-MEANS")
        self.assertEqual(sanitized[0]["start"], 0.1)
        self.assertEqual(sanitized[0]["end"], 0.6)

    # --------------------------------------------------------------------------
    # 3. Context-Driven Concept Scene Choreography Tests
    # --------------------------------------------------------------------------

    def test_concept_scenes_generate_distinct_diagrams_and_takeaways(self):
        """
        Verify that Concept scenes do NOT repeat identical hardcoded autoencoder diagrams
        or identical takeaway bullets. Instead, they dynamically resolve:
          - 'arena' mode when discussing non-convex / K-Means failure
          - 'benchmark' mode when discussing compute / latency / VRAM
          - 'autoencoder' mode when discussing latent compression
        """
        scenes = [
            {
                "scene_type": "concept",
                "title": "Non-Convex Data Breaks K-Means",
                "spoken_text": "Non-convex data breaks K-Means because linear Voronoi cuts fail on curved geometry.",
                "start_time": 0.0,
                "end_time": 4.0,
            },
            {
                "scene_type": "concept",
                "title": "Don't Waste Compute",
                "spoken_text": "Don't waste expensive GPU compute when classical algorithms run in milliseconds.",
                "start_time": 4.0,
                "end_time": 8.0,
            },
            {
                "scene_type": "concept",
                "title": "Latent Space Compression",
                "diagram_mode": "autoencoder",
                "spoken_text": "Compressing high dimensional manifolds into a low dimensional bottleneck.",
                "start_time": 8.0,
                "end_time": 12.0,
            },
        ]

        words = [
            {"word": "test", "start": 0.0, "end": 12.0},
        ]

        choreographed = choreograph_scenes(scenes, words, domain="auto", fps=30)
        self.assertEqual(len(choreographed), 3)

        arena_scene = choreographed[0]
        benchmark_scene = choreographed[1]
        autoencoder_scene = choreographed[2]

        # Check diagram modes
        self.assertEqual(arena_scene["diagram_mode"], "arena")
        self.assertEqual(benchmark_scene["diagram_mode"], "benchmark")
        self.assertEqual(autoencoder_scene["diagram_mode"], "autoencoder")

        # Check takeaway bullets are distinct across all 3 scenes
        arena_points = arena_scene.get("points") or arena_scene.get("bullets") or []
        benchmark_points = benchmark_scene.get("points") or benchmark_scene.get("bullets") or []
        autoencoder_points = autoencoder_scene.get("points") or autoencoder_scene.get("bullets") or []

        self.assertGreaterEqual(len(arena_points), 3)
        self.assertGreaterEqual(len(benchmark_points), 3)
        self.assertGreaterEqual(len(autoencoder_points), 3)

        # Confirm non-identical content
        self.assertNotEqual(arena_points, benchmark_points)
        self.assertNotEqual(arena_points, autoencoder_points)
        self.assertNotEqual(benchmark_points, autoencoder_points)

        # Verify semantic content matching domain
        self.assertTrue(any("spherical" in p.lower() or "curvature" in p.lower() for p in arena_points))
        self.assertTrue(any("gpu" in p.lower() or "milliseconds" in p.lower() for p in benchmark_points))
        self.assertTrue(any("compress" in p.lower() or "manifold" in p.lower() for p in autoencoder_points))


if __name__ == "__main__":
    unittest.main()
