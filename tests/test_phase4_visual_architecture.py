"""
test_phase4_visual_architecture.py
Unit tests for Phase 4 Visual Architecture Overhaul & Critical Bug Fixes:
  - Bug 1: Non-empty fallback guarantees for Math, Graph, Physics, and ML scenes
  - Bug 2: Physics simulation mode switching (projectile vs wave vs forces) based on narration
  - ML domain detection, prompts, and polymorphic validation (bento_grid, algorithm_explorer, neural_code_split)
  - Zero audio drift guarantees across all new layouts
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
from timeline.choreographer import (
    choreograph_scenes,
    detect_physics_mode,
    synthesize_math_steps,
    synthesize_function_graph,
    synthesize_physics_payload,
    synthesize_ml_bento_cards,
    synthesize_algorithm_explorer,
    synthesize_neural_code_split,
    THEME_PALETTES,
    resolve_domain,
)


class TestPhase4VisualArchitecture(unittest.TestCase):

    # ── 1. Domain Detection & ML Prompts ──────────────────────────────────────

    def test_ml_domain_detection(self):
        """Verify detect_domain routes Machine Learning and Deep Learning topics to 'ml'."""
        self.assertIn("ml", DOMAINS)
        self.assertEqual(detect_domain("Unsupervised Machine Learning Algorithms"), "ml")
        self.assertEqual(detect_domain("DBSCAN Clustering vs K-Means"), "ml")
        self.assertEqual(detect_domain("Principal Component Analysis PCA and t-SNE"), "ml")
        self.assertEqual(detect_domain("Deep Learning Neural Network from Scratch in Python"), "ml")
        self.assertEqual(detect_domain("Backpropagation and Gradient Descent Optimization"), "ml")

    def test_ml_system_prompt_specialization(self):
        """Verify get_system_prompt generates bento_grid, algorithm_explorer, and neural_code_split."""
        prompt = get_system_prompt(60, subject="ml")
        self.assertIn("bento_grid", prompt)
        self.assertIn("algorithm_explorer", prompt)
        self.assertIn("neural_code_split", prompt)
        self.assertIn("Data Science", prompt)

    # ── 2. Polymorphic Validation Gate ────────────────────────────────────────

    def test_bento_grid_validation(self):
        """Verify polymorphic validation gate for bento_grid scenes."""
        valid_bento = {
            "title": "Unsupervised Learning Algorithms",
            "subject": "ml",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "These four machine learning algorithms power modern data science.",
                    "display_text": "4 ESSENTIAL ML ALGORITHMS",
                },
                {
                    "scene_type": "bento_grid",
                    "spoken_text": "Clustering groups unlabeled data points by spatial density proximity.",
                    "section_title": "UNSUPERVISED ML ALGORITHMS",
                    "subtitle": "You Need To Know",
                    "cards": [
                        {"title": "K-Means", "algo_type": "kmeans", "category": "CLUSTERING"},
                        {"title": "DBSCAN", "algo_type": "dbscan", "category": "CLUSTERING"},
                    ],
                },
            ],
        }
        is_valid, errors = validate_script_plan(valid_bento)
        self.assertTrue(is_valid, f"Validation failed: {errors}")

    def test_algorithm_explorer_validation(self):
        """Verify polymorphic validation gate for algorithm_explorer scenes."""
        valid_explorer = {
            "title": "DBSCAN Deep Dive",
            "subject": "ml",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "DBSCAN finds dense clusters without assuming spherical shapes.",
                    "display_text": "DBSCAN EXPLAINED",
                },
                {
                    "scene_type": "algorithm_explorer",
                    "spoken_text": "Points with at least minPts neighbors become dense core points.",
                    "algorithm": "dbscan",
                    "parameters": {"epsilon": "0.4", "min_points": "4"},
                },
            ],
        }
        is_valid, errors = validate_script_plan(valid_explorer)
        self.assertTrue(is_valid, f"Validation failed: {errors}")

    def test_neural_code_split_validation(self):
        """Verify polymorphic validation gate for neural_code_split scenes."""
        valid_split = {
            "title": "Neural Network from Scratch",
            "subject": "ml",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Building a multilayer neural network takes just two key passes.",
                    "display_text": "NEURAL NET FROM SCRATCH",
                },
                {
                    "scene_type": "neural_code_split",
                    "spoken_text": "Forward pass multiplies weights and applies nonlinear activation functions.",
                    "model_name": "Neural Network",
                    "code_snippet": "def forward(x, W, b):\n    return softmax(x @ W + b)",
                },
            ],
        }
        is_valid, errors = validate_script_plan(valid_split)
        self.assertTrue(is_valid, f"Validation failed: {errors}")

        # Invalid syntax in neural_code_split code_snippet should be rejected
        invalid_split = copy.deepcopy(valid_split)
        invalid_split["scenes"][1]["code_snippet"] = "def forward(x W b): return x"
        is_valid, errors = validate_script_plan(invalid_split)
        self.assertFalse(is_valid)
        self.assertTrue(any("syntax check failed" in err for err in errors))

    # ── 3. Critical Bug 1: Non-Empty Card Guarantees ──────────────────────────

    def test_non_empty_math_equation_synthesis(self):
        """Verify choreographer guarantees non-empty steps for math_equation even if LLM omits them."""
        bare_scene = {
            "scene_type": "math_equation",
            "title": "Euler's Identity",
            "spoken_text": "Euler's formula connects exponential growth with complex rotation.",
            "start_time": 0.0,
            "emphasis_time": 1.0,
        }
        choreographed = choreograph_scenes([bare_scene], [], domain="math")
        scene_result = choreographed[0]

        # Scene must contain populated steps
        self.assertIn("steps", scene_result)
        self.assertGreater(len(scene_result["steps"]), 0)
        self.assertIn("steps", scene_result["choreography"])
        self.assertGreater(len(scene_result["choreography"]["steps"]), 0)

        # Check synthesized content quality
        first_step = scene_result["choreography"]["steps"][0]
        self.assertTrue(len(first_step["formula"]) > 0)
        self.assertIn("reveal_frame", first_step)

    def test_non_empty_function_graph_synthesis(self):
        """Verify choreographer guarantees non-empty functions for function_graph."""
        bare_scene = {
            "scene_type": "function_graph",
            "title": "Parabolic Trajectory",
            "spoken_text": "The projectile traces a smooth quadratic curve across time.",
            "start_time": 0.0,
        }
        choreographed = choreograph_scenes([bare_scene], [], domain="math")
        scene_result = choreographed[0]

        self.assertIn("functions", scene_result)
        self.assertGreater(len(scene_result["functions"]), 0)
        self.assertIn("graph", scene_result["choreography"])

    def test_non_empty_ml_scenes_synthesis(self):
        """Verify choreographer populates full payload for bare bento_grid, algorithm_explorer, neural_code_split."""
        bare_scenes = [
            {
                "scene_type": "bento_grid",
                "spoken_text": "Let us survey four fundamental unsupervised clustering algorithms.",
                "start_time": 0.0,
            },
            {
                "scene_type": "algorithm_explorer",
                "spoken_text": "DBSCAN clusters points by measuring spatial epsilon neighborhoods.",
                "start_time": 3.0,
            },
            {
                "scene_type": "neural_code_split",
                "spoken_text": "Here is the exact forward and backward pass implementation.",
                "start_time": 6.0,
            },
        ]
        choreographed = choreograph_scenes(bare_scenes, [], domain="ml")

        # Bento grid has populated cards and illumination frames
        self.assertIn("cards", choreographed[0])
        self.assertGreaterEqual(len(choreographed[0]["cards"]), 4)
        self.assertIn("active_card_frames", choreographed[0]["choreography"])

        # Algorithm explorer has parameters and point types
        self.assertIn("parameters", choreographed[1])
        self.assertIn("point_types", choreographed[1])
        self.assertIn("explorer", choreographed[1]["choreography"])

        # Neural code split has valid python code_snippet and sweeping line frames
        self.assertIn("code_snippet", choreographed[2])
        self.assertIn("neural", choreographed[2]["choreography"])
        self.assertIn("line_highlight_frames", choreographed[2]["choreography"]["neural"])

    # ── 4. Critical Bug 2: Physics Mode Detection ─────────────────────────────

    def test_physics_mode_detection_from_narration(self):
        """Verify automatic mode selection (projectile vs wave vs forces) based on spoken narration."""
        projectile_scene = {
            "scene_type": "physics_sim",
            "spoken_text": "The horizontal velocity vector vx stays constant while vertical vy changes.",
        }
        self.assertEqual(detect_physics_mode(projectile_scene), "projectile")

        wave_scene = {
            "scene_type": "physics_sim",
            "spoken_text": "Harmonic oscillation creates a propagating sine wave with frequency f.",
        }
        self.assertEqual(detect_physics_mode(wave_scene), "wave")

        forces_scene = {
            "scene_type": "physics_sim",
            "spoken_text": "Normal force balances downward gravity in static free body equilibrium.",
        }
        self.assertEqual(detect_physics_mode(forces_scene), "forces")

    def test_physics_choreographer_sim_payload_injection(self):
        """Verify choreographer populates projectile trajectory and velocity parameters when in projectile mode."""
        scene = {
            "scene_type": "physics_sim",
            "spoken_text": "Watch the vertical velocity vector drop to zero at peak parabola.",
            "start_time": 0.0,
        }
        choreographed = choreograph_scenes([scene], [], domain="physics")
        phys_scene = choreographed[0]

        self.assertEqual(phys_scene["sim_type"], "projectile")
        self.assertIn("trajectory", phys_scene)
        self.assertIn("v_x", phys_scene)
        self.assertIn("v_y", phys_scene)
        self.assertEqual(phys_scene["choreography"]["physics"]["sim_type"], "projectile")

    # ── 5. Zero Audio Drift ───────────────────────────────────────────────────

    def test_zero_audio_drift_guarantee(self):
        """Verify choreographer strictly guarantees zero audio or word timing mutation."""
        original_words = [
            {"word": "clustering", "start": 0.2, "end": 0.8},
            {"word": "algorithms", "start": 0.9, "end": 1.4},
        ]
        words_copy = copy.deepcopy(original_words)

        scenes = [
            {
                "scene_type": "bento_grid",
                "spoken_text": "clustering algorithms",
                "start_time": 0.0,
            }
        ]

        choreographed = choreograph_scenes(scenes, words_copy, domain="ml")

        # Words array must be strictly identical
        self.assertEqual(words_copy, original_words)
        # Scene start_time must not change
        self.assertEqual(choreographed[0]["start_time"], 0.0)


if __name__ == "__main__":
    unittest.main()

