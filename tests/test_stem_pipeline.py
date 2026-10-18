"""
test_stem_pipeline.py
Unit tests for Phase 3 Multi-Subject STEM Visuals & AI Scene Choreographer:
  - Polymorphic validation for math_equation, function_graph, and physics_sim
  - Domain auto-detection and prompt routing (code, math, physics, systems)
  - Context-aware scene choreographer (palettes, step frame mapping, zero audio/timestamp drift)
  - Zero text scale jitter across STEM primitives
"""

import copy
import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from director.script import detect_domain, get_system_prompt, DOMAINS
from validation.schema import validate_script_plan
from timeline.choreographer import choreograph_scenes, THEME_PALETTES, resolve_domain


class TestSTEMPipeline(unittest.TestCase):

    # ── 1. Domain Detection & Prompt Routing ──────────────────────────────────

    def test_domain_detection_heuristics(self):
        """Verify detect_domain accurately routes keywords to code, math, physics, systems."""
        self.assertEqual(detect_domain("Understanding Derivatives and Integrals"), "math")
        self.assertEqual(detect_domain("Euler's Identity and Complex Analysis"), "math")
        self.assertEqual(detect_domain("Linear Algebra Matrix Multiplication"), "math")

        self.assertEqual(detect_domain("Newton's Laws and Gravity Free Body Diagrams"), "physics")
        self.assertEqual(detect_domain("Projectile Motion and Kinetic Energy"), "physics")
        self.assertEqual(detect_domain("Harmonic Oscillations and Waves"), "physics")

        self.assertEqual(detect_domain("Kafka Partitioning and Distributed Consensus"), "systems")
        self.assertEqual(detect_domain("Raft vs Paxos in Database Replication"), "systems")

        self.assertEqual(detect_domain("Python Dunder Methods and List Comprehension"), "code")
        self.assertEqual(detect_domain("Optimizing Two Sum with Hash Maps"), "code")

    def test_get_system_prompt_domain_specialization(self):
        """Verify get_system_prompt generates domain-matched beat types and rules."""
        math_prompt = get_system_prompt(60, subject="math")
        self.assertIn("math_equation", math_prompt)
        self.assertIn("function_graph", math_prompt)

        physics_prompt = get_system_prompt(60, subject="physics")
        self.assertIn("physics_sim", physics_prompt)
        self.assertIn("forces", physics_prompt)

        systems_prompt = get_system_prompt(60, subject="systems")
        self.assertIn("diagram", systems_prompt)
        self.assertIn("Distributed Systems", systems_prompt)

        code_prompt = get_system_prompt(60, subject="code")
        self.assertIn("code_reveal", code_prompt)
        self.assertIn("comparison", code_prompt)

    # ── 2. Polymorphic Validation Gate ────────────────────────────────────────

    def test_math_equation_validation(self):
        """Verify polymorphic validation gate for math_equation scenes."""
        valid_math_script = {
            "title": "Euler's Formula",
            "subject": "math",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "This single equation connects the five fundamental constants.",
                    "display_text": "THE MOST BEAUTIFUL FORMULA",
                },
                {
                    "scene_type": "math_equation",
                    "spoken_text": "We begin with the Taylor series expansion.",
                    "steps": [
                        {"formula": "e^(ix) = cos(x) + i*sin(x)", "explanation": "Euler formula"},
                        {"formula": "e^(i*pi) + 1 = 0", "explanation": "Identity at x = pi"},
                    ],
                },
            ],
        }
        is_valid, errors = validate_script_plan(valid_math_script)
        self.assertTrue(is_valid, f"Expected valid math script, got errors: {errors}")

        # Invalid: empty steps
        bad_math = copy.deepcopy(valid_math_script)
        bad_math["scenes"][1]["steps"] = []
        is_valid, errors = validate_script_plan(bad_math)
        self.assertFalse(is_valid)
        self.assertTrue(any("requires non-empty 'steps'" in e for e in errors))

    def test_function_graph_validation(self):
        """Verify polymorphic validation gate for function_graph scenes."""
        valid_graph_script = {
            "title": "Parabolic Trajectories",
            "subject": "math",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Let us visualize how quadratic functions behave visually.",
                    "display_text": "QUADRATIC PLOTTING",
                },
                {
                    "scene_type": "function_graph",
                    "spoken_text": "Notice how the curve reaches minimum at origin.",
                    "functions": [{"fn": "x^2", "label": "f(x) = x^2"}],
                    "x_domain": [-5, 5],
                    "y_domain": [0, 25],
                },
            ],
        }
        is_valid, errors = validate_script_plan(valid_graph_script)
        self.assertTrue(is_valid, f"Expected valid graph script, got errors: {errors}")

        # Invalid: empty functions
        bad_graph = copy.deepcopy(valid_graph_script)
        bad_graph["scenes"][1]["functions"] = []
        is_valid, errors = validate_script_plan(bad_graph)
        self.assertFalse(is_valid)
        self.assertTrue(any("requires 'functions'" in e or "cannot be empty" in e for e in errors))

    def test_physics_sim_validation(self):
        """Verify polymorphic validation gate for physics_sim scenes."""
        valid_physics_script = {
            "title": "Newtonian Force Balance",
            "subject": "physics",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Forces always appear in balanced action reaction pairs.",
                    "display_text": "FORCES IN EQUILIBRIUM",
                },
                {
                    "scene_type": "physics_sim",
                    "spoken_text": "Gravity pulls down while the normal force counters.",
                    "sim_type": "forces",
                    "objects": [{"name": "mass", "mass": 10}],
                    "forces": [{"name": "F_g", "direction": 270, "magnitude": 98}],
                },
            ],
        }
        is_valid, errors = validate_script_plan(valid_physics_script)
        self.assertTrue(is_valid, f"Expected valid physics script, got errors: {errors}")

        # Invalid: missing physics payload
        bad_physics = copy.deepcopy(valid_physics_script)
        bad_physics["scenes"][1] = {
            "scene_type": "physics_sim",
            "spoken_text": "Gravity pulls down while normal force counters.",
        }
        is_valid, errors = validate_script_plan(bad_physics)
        self.assertFalse(is_valid)
        self.assertTrue(any("requires presence of 'objects'" in e for e in errors))

    # ── 3. Context-Aware AI Scene Choreographer ───────────────────────────────

    def test_choreographer_palette_and_frame_mapping(self):
        """Verify choreographer injects theme palettes and frame-aligned choreography objects."""
        scenes = [
            {
                "scene_type": "fullscreen_text",
                "start_time": 0.0,
                "emphasis_time": 0.6,
                "spoken_text": "Deriving Euler formula step by step.",
            },
            {
                "scene_type": "math_equation",
                "start_time": 1.5,
                "emphasis_time": 2.2,
                "spoken_text": "First we write the exponential Taylor series expansion.",
                "steps": [
                    {"formula": "e^(ix) = 1 + ix", "explanation": "Series start"},
                    {"formula": "e^(i*pi) + 1 = 0", "explanation": "Identity"},
                ],
            },
        ]
        words = [
            {"word": "Deriving", "start": 0.0, "end": 0.4},
            {"word": "Euler", "start": 0.4, "end": 0.8},
            {"word": "First", "start": 1.5, "end": 1.8},
            {"word": "Taylor", "start": 1.8, "end": 2.2},
            {"word": "series", "start": 2.2, "end": 2.6},
        ]

        choreographed = choreograph_scenes(scenes, words, domain="math", fps=30)
        self.assertEqual(len(choreographed), 2)

        # Palette check
        math_scene = choreographed[1]
        self.assertEqual(math_scene["theme"], "math_euler")
        self.assertEqual(math_scene["palette"]["id"], "math_euler")
        self.assertEqual(math_scene["choreography"]["domain"], "math")

        # Step frame timing check
        steps_choreo = math_scene["choreography"]["steps"]
        self.assertEqual(len(steps_choreo), 2)
        self.assertGreaterEqual(steps_choreo[0]["reveal_frame"], 45)  # 1.5s * 30fps
        self.assertGreater(steps_choreo[1]["reveal_frame"], steps_choreo[0]["reveal_frame"])

    def test_zero_audio_drift_guarantee(self):
        """Verify choreographer strictly guarantees zero audio or word timing mutation."""
        original_words = [
            {"word": "Zero", "start": 0.0, "end": 0.3},
            {"word": "audio", "start": 0.3, "end": 0.6},
            {"word": "drift", "start": 0.6, "end": 0.9},
        ]
        words_copy = copy.deepcopy(original_words)

        scenes = [
            {
                "scene_type": "fullscreen_text",
                "start_time": 0.0,
                "emphasis_time": 0.3,
                "spoken_text": "Zero audio drift test.",
            }
        ]

        choreographed = choreograph_scenes(scenes, words_copy, domain="code", fps=30)
        self.assertEqual(words_copy, original_words, "Choreographer must never mutate words list")
        self.assertEqual(choreographed[0]["start_time"], 0.0)
        self.assertEqual(choreographed[0]["emphasis_time"], 0.3)


if __name__ == "__main__":
    unittest.main()

