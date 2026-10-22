"""
tests/test_enhancer.py

Comprehensive unit and invariant tests for Section 4: Active Execution — Phase 2 Final Push.
Verifies:
  1. Deterministic semantic classification matching AGENTS.md specifications:
     - Anti-Pattern: { "label": "Anti-Pattern", "type": "warning", "icon": "⚠️" }
     - Best Practice: { "label": "Best Practice", "type": "success", "icon": "✨" }
     - Performance: { "label": "Performance", "type": "accent", "icon": "⚡" }
     - Key Concept: { "label": "Key Concept", "type": "info", "icon": "💡" }
     - Comparison: { "label": "Comparison", "type": "info", "icon": "⚖️" }
  2. Multi-field scanning (visual_type, scene_type, code, narration, focus_phrase).
  3. Strictly additive timeline invariant (zero audio drift, zero timestamp alterations, preserved scene order).
  4. Defensive fallbacks & custom badge preservation.
  5. Stage 4 pipeline wiring in engine/generate.py and engine/timeline/.
  6. Visual polish & Remotion integration checks in CodingShort.jsx and SceneBadge.jsx.
"""

import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"
SRC_DIR = VIDEO_DIR / "src"
COMPONENTS_DIR = SRC_DIR / "components"

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))

from timeline.enhancer import (
    classify_scene,
    enhance_scenes,
    SEMANTIC_BADGES,
)
from timeline.beats import align_timeline


class TestSemanticEnhancerAndVisualPolish(unittest.TestCase):

    # --------------------------------------------------------------------------
    # 1. Deterministic Semantic Classification Tests (AGENTS.md Section 4 specs)
    # --------------------------------------------------------------------------

    def test_classify_warning_anti_pattern(self):
        """Verify warning badge: { label: 'Anti-Pattern', type: 'warning', icon: '⚠️' }."""
        sample_scenes = [
            {"spoken_text": "Avoid this redundant code pattern.", "scene_type": "code_reveal"},
            {"spoken_text": "This naive implementation creates an accidental memory leak.", "visual_type": "code_reveal"},
            {"spoken_text": "A common mistake beginners make when handling exceptions.", "focus_phrase": "except Exception:"},
            {"spoken_text": "Ugly duplicated logic that breaks easily.", "problem_label": "bad approach"},
        ]
        for scene in sample_scenes:
            badge = classify_scene(scene)
            self.assertIsNotNone(badge, f"Failed to classify anti-pattern: {scene}")
            self.assertEqual(badge["type"], "warning")
            self.assertEqual(badge["icon"], "⚠️")
            self.assertEqual(badge["label"], "Anti-Pattern")
            self.assertEqual(badge["category"], "anti_pattern")

    def test_classify_success_best_practice(self):
        """Verify success badge: { label: 'Best Practice', type: 'success', icon: '✨' }."""
        sample_scenes = [
            {"spoken_text": "Here is the best practice using list comprehensions.", "scene_type": "code_reveal"},
            {"spoken_text": "A cleaner idiomatic solution to parse the response.", "visual_type": "code_reveal"},
            {"spoken_text": "The recommended pythonic one-liner solves it.", "code_snippet": "val = (x := 42)"},
            {"spoken_text": "Transforms the loop cleanly.", "scene_type": "code_transform"},
        ]
        for scene in sample_scenes:
            badge = classify_scene(scene)
            self.assertIsNotNone(badge, f"Failed to classify solution: {scene}")
            self.assertEqual(badge["type"], "success")
            self.assertEqual(badge["icon"], "✨")
            self.assertEqual(badge["label"], "Best Practice")
            self.assertEqual(badge["category"], "solution")

    def test_classify_accent_performance(self):
        """Verify accent badge: { label: 'Performance', type: 'accent', icon: '⚡' }."""
        sample_scenes = [
            {"spoken_text": "This optimization achieves O(1) constant time lookup.", "code_snippet": "return table[key]"},
            {"spoken_text": "Significantly faster throughput with zero memory overhead.", "visual_type": "code_reveal"},
            {"spoken_text": "Eliminating the latency bottleneck in the pipeline.", "scene_type": "terminal"},
        ]
        for scene in sample_scenes:
            badge = classify_scene(scene)
            self.assertIsNotNone(badge, f"Failed to classify performance: {scene}")
            self.assertEqual(badge["type"], "accent")
            self.assertEqual(badge["icon"], "⚡")
            self.assertEqual(badge["label"], "Performance")
            self.assertEqual(badge["category"], "performance")

    def test_classify_info_key_concept(self):
        """Verify info badge: { label: 'Key Concept', type: 'info', icon: '💡' }."""
        diagram_scene = {
            "visual_type": "diagram",
            "spoken_text": "Under the hood it allocates an inner buffer.",
            "nodes": ["Source", "Sink"],
        }
        badge = classify_scene(diagram_scene)
        self.assertIsNotNone(badge)
        self.assertEqual(badge["type"], "info")
        self.assertEqual(badge["icon"], "💡")
        self.assertEqual(badge["label"], "Key Concept")
        self.assertEqual(badge["category"], "insight")

        concept_scene = {
            "scene_type": "code_reveal",
            "spoken_text": "Remember this core principle of immutable structures.",
        }
        badge2 = classify_scene(concept_scene)
        self.assertEqual(badge2["type"], "info")
        self.assertEqual(badge2["icon"], "💡")
        self.assertEqual(badge2["label"], "Key Concept")

    def test_classify_comparison_scene(self):
        """Verify comparison badge for comparison scenes."""
        comp_scene = {
            "scene_type": "comparison",
            "spoken_text": "Compare the two implementations side by side.",
            "problem_code": "a = 1",
            "solution_code": "b = 2",
        }
        badge = classify_scene(comp_scene)
        self.assertIsNotNone(badge)
        self.assertEqual(badge["type"], "info")
        self.assertEqual(badge["icon"], "⚖️")
        self.assertEqual(badge["label"], "Comparison")
        self.assertEqual(badge["category"], "comparison")

    def test_classify_visual_type_attribute_support(self):
        """Verify classifier inspects visual_type attribute as specified in AGENTS.md."""
        scene = {
            "visual_type": "diagram",
            "spoken_text": "The message lifecycle through queues.",
            "nodes": ["Queue", "Worker"],
        }
        badge = classify_scene(scene)
        self.assertIsNotNone(badge)
        self.assertEqual(badge["category"], "insight")

    def test_classify_preserves_custom_badge_without_override(self):
        """Verify explicit pre-existing badges are never overwritten."""
        custom_badge = {"label": "Security Audit", "type": "warning", "icon": "🔒"}
        scene = {
            "scene_type": "code_reveal",
            "spoken_text": "Validate all inputs before processing.",
            "badge": custom_badge,
        }
        badge = classify_scene(scene)
        self.assertEqual(badge, custom_badge)

    def test_classify_unmatched_fallback_returns_none(self):
        """Verify that neutral scenes with no semantic cues return None stably."""
        neutral_scene = {
            "scene_type": "fullscreen_text",
            "spoken_text": "Welcome everyone let us dive into the topic.",
        }
        badge = classify_scene(neutral_scene)
        self.assertIsNone(badge)

    # --------------------------------------------------------------------------
    # 2. Strictly Additive Invariant & Zero Audio Drift Tests
    # --------------------------------------------------------------------------

    def test_enhance_scenes_additive_invariants(self):
        """Verify enhance_scenes strictly preserves timestamps, ordering, and duration."""
        scenes = [
            {"scene_type": "fullscreen_text", "spoken_text": "Avoid this bad mistake.", "start_time": 0.0, "emphasis_time": 0.5},
            {"scene_type": "code_reveal", "spoken_text": "The best practice solves it.", "start_time": 3.2, "emphasis_time": 3.6},
            {"scene_type": "comparison", "spoken_text": "Notice how much faster it is.", "start_time": 7.0, "emphasis_time": 7.4},
        ]

        enhanced = enhance_scenes(scenes)

        self.assertEqual(len(enhanced), len(scenes), "Scene count must not change")
        for orig, enh in zip(scenes, enhanced):
            # Timestamps must be strictly identical (zero audio drift)
            self.assertEqual(orig["start_time"], enh["start_time"])
            self.assertEqual(orig["emphasis_time"], enh["emphasis_time"])
            self.assertEqual(orig["spoken_text"], enh["spoken_text"])
            self.assertEqual(orig["scene_type"], enh["scene_type"])
            self.assertIn("badge", enh)

        # Immutability check: input list was not mutated
        for orig in scenes:
            self.assertNotIn("badge", orig)

    def test_align_timeline_retains_badge(self):
        """Verify beats.py align_timeline carries over badge metadata."""
        scenes = [
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
        words = [
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

        timed = align_timeline(scenes, words)
        self.assertIn("badge", timed[0])
        self.assertEqual(timed[0]["badge"]["label"], "Anti-Pattern")

    # --------------------------------------------------------------------------
    # 3. Stage 4 Pipeline Orchestration Verification
    # --------------------------------------------------------------------------

    def test_stage4_generate_py_enhancer_wiring(self):
        """Verify engine/generate.py Stage 4 imports and executes enhance_scenes."""
        gen_content = (ENGINE_DIR / "generate.py").read_text(encoding="utf-8")
        self.assertIn("from timeline.enhancer import enhance_scenes", gen_content)
        self.assertIn("timed_scenes = enhance_scenes(timed_scenes)", gen_content)
        self.assertIn("Attached semantic badges to", gen_content)

    def test_timeline_init_exports_enhancer_symbols(self):
        """Verify engine/timeline/__init__.py exports classify_scene and enhance_scenes."""
        init_content = (ENGINE_DIR / "timeline" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("classify_scene", init_content)
        self.assertIn("enhance_scenes", init_content)
        self.assertIn("SEMANTIC_BADGES", init_content)

    # --------------------------------------------------------------------------
    # 4. Remotion Badge & Visual Polish Checks in CodingShort.jsx
    # --------------------------------------------------------------------------

    def test_scenebadge_component_exists_and_uses_critically_damped_spring(self):
        """Verify SceneBadge uses damping: 18, stiffness: 80, mass: 0.6."""
        badge_jsx = (COMPONENTS_DIR / "SceneBadge.jsx").read_text(encoding="utf-8")
        badge_utils = (SRC_DIR / "badgeUtils.js").read_text(encoding="utf-8")
        self.assertIn("damping: 18", badge_utils)
        self.assertIn("stiffness: 80", badge_utils)
        self.assertIn("mass: 0.6", badge_utils)
        self.assertIn("BADGE_THEMES", badge_utils)
        self.assertIn("accent", badge_utils)
        self.assertIn("warning", badge_utils)
        self.assertIn("success", badge_utils)
        self.assertIn("info", badge_utils)
        self.assertIn("translateZ(0)", badge_jsx)
        self.assertIn("backfaceVisibility", badge_jsx)

    def test_codingshort_visual_polish_elements(self):
        """Verify CodingShort includes ambient backdrop glow, 1px highlight border,
        scene micro-transitions, and blinking terminal cursor."""
        coding_short = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")

        # 1. Ambient backdrop glow
        self.assertIn("radial-gradient(ellipse at center", coding_short, "Missing ambient radial backdrop glow")
        self.assertIn("getGlowColor", coding_short, "Missing reactive glow color helper")

        # 2. Refined 1px highlight border & drop shadows
        self.assertIn("rgba(255, 255, 255, 0.1)", coding_short, "Missing 1px highlight border")
        self.assertIn("boxShadow:", coding_short, "Missing refined drop shadow")
        self.assertIn("maxWidth: '920px'", coding_short, "Must maintain 920px safe card bounds")

        # 3. Scene micro-transitions (6-8 frame entrance fade)
        self.assertIn("interpolate(", coding_short)
        self.assertIn("[0, 7]", coding_short, "Missing 6-8 frame micro-transition entrance interpolation")
        self.assertIn("sceneElapsedFrames", coding_short)

        # 4. Terminal cursor polish
        self.assertIn("TerminalCursor", coding_short, "Missing TerminalCursor component")
        self.assertIn("showCursor=", coding_short, "Missing showCursor prop integration on CodeBlock")


if __name__ == "__main__":
    unittest.main()

