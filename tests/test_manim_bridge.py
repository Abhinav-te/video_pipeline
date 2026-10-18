"""
Unit and integration tests for Phase 14: Hybrid Manim Community (manimce) Sub-Renderer Integration.
Verifies template resolution, safe LaTeX fallback, max clips capping, graceful subprocess fallback,
and deterministic MP4 clip generation.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))

from engine.renderer.manim_bridge import (
    is_manim_available,
    resolve_manim_template,
    render_manim_clips_for_timeline,
)
from engine.renderer.manim_templates import (
    safe_math_tex,
    ManimEquationMorphScene,
    ManimCalculusGraphScene,
    ManimLinearVectorScene,
    ManimQuantumWaveScene,
    MANIM_AVAILABLE,
)


class TestManimBridge(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_manim_bridge_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_manim_availability(self):
        """Verifies that Manim Community is detected in the environment."""
        self.assertTrue(is_manim_available(), "Expected Manim Community to be available in engine environment.")
        self.assertTrue(MANIM_AVAILABLE)

    def test_template_resolution_all_four_types(self):
        """Verifies template resolution and parameter extraction for all 4 Manim templates."""
        # 1. Equation Morph
        sc_eq = {
            "scene_index": 0,
            "visual_type": "math_equation",
            "sub_mode": "equation_morph",
            "steps": [
                {"latex": r"e^{i\pi} + 1 = 0", "label": "Euler's Identity"},
                {"latex": r"e^{i\theta} = \cos\theta + i\sin\theta", "label": "Euler Formula"},
            ],
            "start_time": 0.0,
            "end_time": 4.0,
        }
        t1, p1 = resolve_manim_template(sc_eq)
        self.assertEqual(t1, "equation_morph")
        self.assertEqual(len(p1["steps"]), 2)
        self.assertAlmostEqual(p1["duration"], 4.0)

        # 2. Calculus Graph
        sc_calc = {
            "scene_index": 1,
            "visual_type": "function_graph",
            "sub_mode": "calculus_graph",
            "curves": ["0.4 * x**2 + 0.2"],
            "start_time": 4.0,
            "end_time": 7.5,
        }
        t2, p2 = resolve_manim_template(sc_calc)
        self.assertEqual(t2, "calculus_graph")
        self.assertIn("x**2", p2["fn_str"])
        self.assertAlmostEqual(p2["duration"], 3.5)

        # 3. Linear Vector Field
        sc_vec = {
            "scene_index": 2,
            "visual_type": "manim_scene",
            "sub_mode": "vector_field",
            "matrix": [[2.0, 1.0], [0.0, 1.5]],
            "start_time": 7.5,
            "end_time": 11.5,
        }
        t3, p3 = resolve_manim_template(sc_vec)
        self.assertEqual(t3, "vector_field")
        self.assertEqual(p3["matrix"], [[2.0, 1.0], [0.0, 1.5]])

        # 4. Quantum Wavepacket
        sc_qw = {
            "scene_index": 3,
            "visual_type": "quantum_sim",
            "sub_mode": "quantum_wave",
            "barrier_x": 0.5,
            "start_time": 11.5,
            "end_time": 15.0,
        }
        t4, p4 = resolve_manim_template(sc_qw)
        self.assertEqual(t4, "quantum_wave")
        self.assertEqual(p4["barrier_x"], 0.5)

    def test_safe_math_tex_fallback(self):
        """Verifies that invalid LaTeX syntax cleanly falls back to Text without raising ValueError."""
        # Valid LaTeX
        mob_valid = safe_math_tex(r"\sum_{i=1}^n i = \frac{n(n+1)}{2}")
        self.assertIsNotNone(mob_valid)

        # Intentionally invalid LaTeX
        mob_fallback = safe_math_tex(r"\brokenmacro{undefined} & % #")
        self.assertIsNotNone(mob_fallback)
        self.assertEqual(mob_fallback.__class__.__name__, "Text")

    def test_graceful_fallback_when_disabled(self):
        """Calling with enable_manim=False must leave timeline data completely unchanged."""
        timeline = {
            "scenes": [
                {
                    "scene_index": 0,
                    "visual_type": "math_equation",
                    "sub_mode": "equation_morph",
                    "steps": [{"latex": "x = 1"}],
                }
            ]
        }
        res = render_manim_clips_for_timeline(timeline, self.test_dir, enable_manim=False)
        self.assertNotIn("manim_video_src", res["scenes"][0])

    @patch("engine.renderer.manim_bridge._run_manim_clip_subprocess")
    def test_graceful_fallback_on_subprocess_error_or_timeout(self, mock_subproc):
        """When Manim subprocess fails or times out, the scene gracefully retains native Remotion SVG fallback."""
        mock_subproc.return_value = False  # Simulates timeout / error

        timeline = {
            "scenes": [
                {
                    "scene_index": 0,
                    "visual_type": "math_equation",
                    "sub_mode": "equation_morph",
                    "steps": [{"latex": "x = 1"}],
                    "start_time": 0.0,
                    "end_time": 3.0,
                }
            ]
        }
        res = render_manim_clips_for_timeline(timeline, self.test_dir, enable_manim=True)
        self.assertNotIn("manim_video_src", res["scenes"][0])

    @patch("engine.renderer.manim_bridge._run_manim_clip_subprocess")
    def test_max_clips_capping(self, mock_subproc):
        """At most 2 key scenes per video are selected for Manim sub-rendering."""
        mock_subproc.return_value = True

        scenes = [
            {"scene_index": i, "visual_type": "math_equation", "start_time": i * 3.0, "end_time": (i + 1) * 3.0}
            for i in range(5)
        ]
        timeline = {"scenes": scenes}

        res = render_manim_clips_for_timeline(timeline, self.test_dir, enable_manim=True, max_clips=2)
        manim_rendered_count = sum(1 for s in res["scenes"] if "manim_video_src" in s)
        self.assertEqual(manim_rendered_count, 2)
        self.assertEqual(mock_subproc.call_count, 2)

    def test_actual_manim_clip_generation(self):
        """Generates an actual 2.5s Manim MP4 clip and verifies file existence and format."""
        timeline = {
            "scenes": [
                {
                    "scene_index": 0,
                    "title": "Quantum Wavepacket Tunneling",
                    "visual_type": "quantum_sim",
                    "sub_mode": "quantum_wave",
                    "barrier_x": 0.0,
                    "start_time": 0.0,
                    "end_time": 2.5,
                }
            ]
        }
        res = render_manim_clips_for_timeline(timeline, self.test_dir, enable_manim=True, max_clips=1)
        sc0 = res["scenes"][0]
        self.assertIn("manim_video_src", sc0)
        self.assertTrue(sc0["manim_video_src"].endswith("manim_scene_0.mp4"))

        out_clip = self.test_dir / "manim_scene_0.mp4"
        self.assertTrue(out_clip.exists(), f"Expected {out_clip} to exist")
        self.assertGreater(out_clip.stat().st_size, 5000, "Expected generated MP4 to be > 5KB")


if __name__ == "__main__":
    unittest.main()
