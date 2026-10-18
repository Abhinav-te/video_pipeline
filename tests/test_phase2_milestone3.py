"""
tests/test_phase2_milestone3.py

Unit and integration tests for Phase 2 Milestone 3: Semantic Visual Enhancer Pass.
Verifies:
  1. Semantic Classification & Tagging (anti_pattern, solution, performance, insight, comparison).
  2. Strictly Additive Engine Pass (zero timestamp alterations, zero audio drift, preserved scene order).
  3. Defensive Fallbacks & Custom Badge Preservation.
  4. SceneBadge Remotion component integration & damped spring physics.
  5. End-to-end integration with Stage 4 timeline assembly.
"""

import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR = REPO_DIR / "video"
SRC_DIR = VIDEO_DIR / "src"
COMPONENTS_DIR = SRC_DIR / "components"
ENGINE_DIR = REPO_DIR / "engine"

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))

from timeline.enhancer import (
    classify_scene,
    enhance_scenes,
    SEMANTIC_BADGES,
)
from timeline import align_timeline


class TestPhase2Milestone3SemanticEnhancer(unittest.TestCase):

    # --------------------------------------------------------------------------
    # 1. Deterministic Semantic Classification Tests
    # --------------------------------------------------------------------------

    def test_classify_anti_pattern_scene(self):
        """Verify anti-pattern detection on bug/mistake/redundancy keywords."""
        scenes = [
            {"spoken_text": "Stop writing redundant lines just to check values.", "scene_type": "fullscreen_text"},
            {"spoken_text": "This slow approach causes a serious memory leak.", "code_snippet": "items = []"},
            {"spoken_text": "A common mistake beginners make with mutable defaults.", "scene_type": "code_reveal"},
            {"spoken_text": "Avoid this ugly duplicated code block.", "scene_type": "code_transform"},
        ]
        for s in scenes:
            badge = classify_scene(s)
            self.assertIsNotNone(badge, f"Failed to classify anti-pattern: {s}")
            self.assertEqual(badge["category"], "anti_pattern")
            self.assertEqual(badge["type"], "warning")
            self.assertEqual(badge["icon"], "⚠️")
            self.assertEqual(badge["label"], "Anti-Pattern")

    def test_classify_solution_scene(self):
        """Verify solution detection on best practice, clean idiomatic fixes."""
        scenes = [
            {"spoken_text": "Here is the better way using walrus operators.", "scene_type": "code_reveal"},
            {"spoken_text": "An idiomatic pythonic solution that fixes the issue.", "code_snippet": "val = (x := 42)"},
            {"spoken_text": "The recommended clean one-liner approach.", "scene_type": "code_reveal"},
            {"spoken_text": "Transforms the loop cleanly.", "scene_type": "code_transform"},
        ]
        for s in scenes:
            badge = classify_scene(s)
            self.assertIsNotNone(badge, f"Failed to classify solution: {s}")
            self.assertEqual(badge["category"], "solution")
            self.assertEqual(badge["type"], "success")
            self.assertEqual(badge["icon"], "✨")
            self.assertIn(badge["label"], ("Better Way", "Best Practice"))

    def test_classify_performance_scene(self):
        """Verify performance detection on algorithmic speed, complexity, and latency."""
        scenes = [
            {"spoken_text": "This optimization runs in O(1) time complexity.", "code_snippet": "lookup[k]"},
            {"spoken_text": "Faster throughput with zero cache overhead.", "scene_type": "code_reveal"},
            {"spoken_text": "Benchmarking CPU latency and memory allocation.", "scene_type": "terminal"},
        ]
        for s in scenes:
            badge = classify_scene(s)
            self.assertIsNotNone(badge, f"Failed to classify performance: {s}")
            self.assertEqual(badge["category"], "performance")
            self.assertIn(badge["type"], ("performance", "accent"))
            self.assertEqual(badge["icon"], "⚡")
            self.assertEqual(badge["label"], "Performance")

    def test_classify_insight_scene(self):
        """Verify insight detection on diagrams, core principles, and mental models."""
        diagram_scene = {
            "scene_type": "diagram",
            "spoken_text": "Under the hood it allocates an inner buffer.",
            "nodes": ["A", "B"],
        }
        badge = classify_scene(diagram_scene)
        self.assertIsNotNone(badge)
        self.assertEqual(badge["category"], "insight")
        self.assertIn(badge["type"], ("insight", "info"))
        self.assertEqual(badge["icon"], "💡")
        self.assertIn(badge["label"], ("Key Insight", "Key Concept"))

        pro_tip_scene = {
            "scene_type": "code_reveal",
            "spoken_text": "Remember this pro tip for production architecture.",
        }
        badge2 = classify_scene(pro_tip_scene)
        self.assertEqual(badge2["category"], "insight")

    def test_classify_comparison_scene(self):
        """Verify comparison detection for comparison scene types."""
        comp_scene = {
            "scene_type": "comparison",
            "spoken_text": "Compare both approaches side by side.",
            "problem_code": "bad = 1",
            "solution_code": "good = 2",
        }
        badge = classify_scene(comp_scene)
        self.assertIsNotNone(badge)
        self.assertEqual(badge["category"], "comparison")
        self.assertEqual(badge["type"], "info")
        self.assertEqual(badge["icon"], "⚖️")
        self.assertEqual(badge["label"], "Comparison")

    def test_classify_comparison_with_performance_focus(self):
        """Verify comparison scenes focusing on speed/faster get performance badge."""
        comp_scene = {
            "scene_type": "comparison",
            "spoken_text": "Notice how much faster the hash table executes.",
            "problem_code": "bad = 1",
            "solution_code": "good = 2",
        }
        badge = classify_scene(comp_scene)
        self.assertIsNotNone(badge)
        self.assertEqual(badge["category"], "performance")
        self.assertEqual(badge["icon"], "⚡")

    def test_classify_preserves_custom_badge(self):
        """Verify that pre-existing custom badges on scenes are strictly preserved."""
        custom_badge = {"label": "Security Audit", "type": "warning", "icon": "🔒"}
        scene = {
            "scene_type": "code_reveal",
            "spoken_text": "Check your input sanitization routines.",
            "badge": custom_badge,
        }
        badge = classify_scene(scene)
        self.assertEqual(badge, custom_badge)

    def test_classify_unmatched_fallback(self):
        """Verify that neutral scenes with no semantic keywords return None without crashing."""
        neutral_scene = {
            "scene_type": "fullscreen_text",
            "spoken_text": "Hello world welcome to this quick overview video.",
        }
        badge = classify_scene(neutral_scene)
        self.assertIsNone(badge)

    # --------------------------------------------------------------------------
    # 2. Additive Data Integrity & Zero Drift Tests
    # --------------------------------------------------------------------------

    def test_enhance_scenes_strictly_additive(self):
        """Verify enhance_scenes does not alter timestamps, order, or mutate inputs."""
        input_scenes = [
            {"scene_type": "fullscreen_text", "spoken_text": "Avoid this bad mistake.", "start_time": 0.0, "emphasis_time": 0.5},
            {"scene_type": "code_reveal", "spoken_text": "The better way solves it.", "start_time": 3.2, "emphasis_time": 3.6},
            {"scene_type": "comparison", "spoken_text": "Compare the difference now.", "start_time": 7.0, "emphasis_time": 7.4},
        ]

        enhanced = enhance_scenes(input_scenes)

        self.assertEqual(len(enhanced), len(input_scenes))
        for orig, enh in zip(input_scenes, enhanced):
            # Timestamps must be exactly identical
            self.assertEqual(orig["start_time"], enh["start_time"])
            self.assertEqual(orig["emphasis_time"], enh["emphasis_time"])
            self.assertEqual(orig["spoken_text"], enh["spoken_text"])
            self.assertEqual(orig["scene_type"], enh["scene_type"])
            # Badge field added
            self.assertIn("badge", enh)
            self.assertIsInstance(enh["badge"], dict)

        # Immutability check: input_scenes was not mutated
        for orig in input_scenes:
            self.assertNotIn("badge", orig)

    def test_align_timeline_preserves_badge(self):
        """Verify align_timeline carries over existing badge attributes."""
        test_scenes = [
            {
                "scene_type": "fullscreen_text",
                "spoken_text": "Stop writing bad code today.",
                "emphasis_word": "bad",
                "badge": {"label": "Anti-Pattern", "type": "warning", "icon": "⚠️"},
            },
            {
                "scene_type": "code_reveal",
                "spoken_text": "Here is the clean solution.",
                "emphasis_word": "clean",
            },
        ]
        test_words = [
            {"word": "Stop", "start": 0.0, "end": 0.3},
            {"word": "writing", "start": 0.3, "end": 0.6},
            {"word": "bad", "start": 0.6, "end": 0.9},
            {"word": "code", "start": 0.9, "end": 1.1},
            {"word": "today", "start": 1.1, "end": 1.4},
            {"word": "Here", "start": 1.6, "end": 1.9},
            {"word": "is", "start": 1.9, "end": 2.1},
            {"word": "the", "start": 2.1, "end": 2.3},
            {"word": "clean", "start": 2.3, "end": 2.6},
            {"word": "solution", "start": 2.6, "end": 3.0},
        ]

        timed = align_timeline(test_scenes, test_words)
        self.assertIn("badge", timed[0])
        self.assertEqual(timed[0]["badge"]["label"], "Anti-Pattern")

    # --------------------------------------------------------------------------
    # 3. Stage 4 Orchestration Integration
    # --------------------------------------------------------------------------

    def test_generate_py_imports_and_calls_enhancer(self):
        """Verify engine/generate.py imports and runs enhance_scenes in Stage 4."""
        generate_py = (ENGINE_DIR / "generate.py").read_text(encoding="utf-8")
        self.assertIn("from timeline.enhancer import enhance_scenes", generate_py)
        self.assertIn("timed_scenes = enhance_scenes(timed_scenes)", generate_py)
        self.assertIn("Attached semantic badges to", generate_py)

    # --------------------------------------------------------------------------
    # 4. React / Remotion Component & Node Physics Unit Tests
    # --------------------------------------------------------------------------

    def test_scenebadge_component_and_utils_exist(self):
        """Verify SceneBadge.jsx and badgeUtils.js exist in expected video paths."""
        badge_component = COMPONENTS_DIR / "SceneBadge.jsx"
        badge_utils = SRC_DIR / "badgeUtils.js"
        self.assertTrue(badge_component.exists(), f"Missing {badge_component}")
        self.assertTrue(badge_utils.exists(), f"Missing {badge_utils}")

    def test_codingshort_integrates_scenebadge(self):
        """Verify CodingShort.jsx imports and uses SceneBadge across scenes."""
        coding_short = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertIn("import { SceneBadge } from './components/SceneBadge';", coding_short)
        self.assertIn("<SceneBadge badge={activeScene.badge}", coding_short)
        self.assertIn("sceneStartFrame", coding_short)

    def test_node_scenebadge_unit_test_suite_passes(self):
        """Run Node test suite verifying damped springs, theme palettes, and tokens."""
        test_script = VIDEO_DIR / "test_scene_badge.mjs"
        self.assertTrue(test_script.exists())

        proc = subprocess.run(
            ["node", str(test_script)],
            cwd=str(VIDEO_DIR),
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            proc.returncode, 0,
            f"Node SceneBadge test failed with code {proc.returncode}:\n{proc.stderr}\n{proc.stdout}"
        )
        self.assertIn("All SceneBadge unit tests passed successfully!", proc.stdout)


if __name__ == "__main__":
    unittest.main()

