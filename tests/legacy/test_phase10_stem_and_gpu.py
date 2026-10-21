"""
Unit tests for Phase 10: Hardware GPU Wiring, Domain-Aware Comparison Footer & Specialized STEM Engines.
Tests:
  1. Whisper CUDA acceleration detection helper & logging.
  2. Remotion subprocess GPU acceleration flags (--chrome-mode=chrome-for-testing, --gl=angle).
  3. Domain-aware comparison footer resolution (no O(n²) on chemistry/physics/quantum/mechanics/electrical).
  4. Schema validation for quantum_sim, mechanics_fbd, and electrical_grid visual types.
  5. Choreographer sub-mode routing, payload synthesis, and layout density for all 3 STEM engines.
"""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch, MagicMock

ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import torch
from engine.audio.tts_whisper import get_whisper_device
from engine.director.script import detect_domain, DOMAINS
from engine.validation.schema import validate_script_plan, VALID_SCENE_TYPES, STEM_SCENE_TYPES
from engine.timeline.choreographer import (
    choreograph_scenes,
    resolve_domain,
    detect_quantum_mode,
    synthesize_quantum_payload,
    detect_mechanics_mode,
    synthesize_mechanics_payload,
    detect_electrical_mode,
    synthesize_electrical_payload,
    COMPARISON_FOOTERS,
)


class TestPhase10StemAndGPU(unittest.TestCase):

    def test_whisper_cuda_device_detection_and_logging(self):
        """Confirms that when CUDA is available, get_whisper_device returns 'cuda' and logs rocket icon."""
        if torch.cuda.is_available():
            buf = io.StringIO()
            with redirect_stdout(buf):
                dev = get_whisper_device()
            out = buf.getvalue()
            self.assertEqual(dev, "cuda")
            self.assertIn("[AUDIO:INFO] 🚀 Whisper device: cuda", out)
        else:
            dev = get_whisper_device()
            self.assertEqual(dev, "cpu")

    def test_remotion_cmd_gpu_flags(self):
        """Verifies that generate_and_render.py uses clean fast default without WSL2 D3D12 contention flags."""
        with open("generate_and_render.py", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("--chrome-mode=chrome-for-testing", content)
        self.assertNotIn("--gl=angle", content)
        self.assertIn("--frames", content)
        self.assertIn("--fast-test", content)

    def test_domain_registration_and_detection(self):
        """Verifies DOMAINS set and detect_domain function recognize quantum, mechanics, and electrical."""
        self.assertIn("quantum_physics", DOMAINS)
        self.assertIn("mechanics", DOMAINS)
        self.assertIn("electrical", DOMAINS)

        self.assertEqual(detect_domain("Schrodinger wavepacket quantum tunneling"), "quantum_physics")
        self.assertEqual(detect_domain("Heisenberg uncertainty principle reciprocal squeeze"), "quantum_physics")
        self.assertEqual(detect_domain("Dirac equation relativistic bi-spinor atomic orbitals"), "quantum_physics")

        self.assertEqual(detect_domain("Structural beam weight distribution pin and roller reactions"), "mechanics")
        self.assertEqual(detect_domain("Inclined plane free body diagram friction threshold"), "mechanics")
        self.assertEqual(detect_domain("Vehicle chassis axle load transfer center of mass"), "mechanics")

        self.assertEqual(detect_domain("Kirchhoff KVL loop and KCL node mesh analysis"), "electrical")
        self.assertEqual(detect_domain("Thevenin equivalence network reduction max power transfer"), "electrical")
        self.assertEqual(detect_domain("Smart grid optimal power flow 765 kV transmission congestion"), "electrical")

    def test_schema_validation_new_primitives(self):
        """Verifies schema validation succeeds for quantum_sim, mechanics_fbd, and electrical_grid scenes."""
        self.assertIn("quantum_sim", VALID_SCENE_TYPES)
        self.assertIn("mechanics_fbd", VALID_SCENE_TYPES)
        self.assertIn("electrical_grid", VALID_SCENE_TYPES)
        self.assertIn("quantum_sim", STEM_SCENE_TYPES)
        self.assertIn("mechanics_fbd", STEM_SCENE_TYPES)
        self.assertIn("electrical_grid", STEM_SCENE_TYPES)

        plan = {
            "title": "Specialized STEM Engines Test",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Quantum mechanics reveals wavepacket tunneling through barriers.",
                    "display_text": "QUANTUM TUNNELING DISCOVERY",
                },
                {
                    "scene_type": "quantum_sim",
                    "sub_mode": "schrodinger_tunneling",
                    "spoken_text": "Wavepacket penetrates the potential barrier with exponential decay.",
                },
                {
                    "scene_type": "mechanics_fbd",
                    "sub_mode": "beam_weight_distribution",
                    "spoken_text": "Equilibrium rebalances reaction forces Ra and Rb dynamically.",
                },
                {
                    "scene_type": "electrical_grid",
                    "sub_mode": "thevenin_equivalence",
                    "spoken_text": "Linear network reduces to single Vth source in series.",
                },
            ],
        }
        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Validation failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_domain_aware_comparison_footer_mapping(self):
        """Verifies that comparison footer text matches the active subject domain without CS complexity leak."""
        self.assertIn("RATE LAW CONTRAST", COMPARISON_FOOTERS["chemistry"])
        self.assertNotIn("O(n²)", COMPARISON_FOOTERS["chemistry"])

        self.assertIn("EQUILIBRIUM CONDITION", COMPARISON_FOOTERS["physics"])
        self.assertIn("EQUILIBRIUM CONDITION", COMPARISON_FOOTERS["mechanics"])
        self.assertNotIn("O(n²)", COMPARISON_FOOTERS["mechanics"])

        self.assertIn("COMMUTATION RELATION", COMPARISON_FOOTERS["quantum_physics"])
        self.assertIn("UNCERTAINTY BOUND", COMPARISON_FOOTERS["quantum_physics"])
        self.assertNotIn("O(n²)", COMPARISON_FOOTERS["quantum_physics"])

        self.assertIn("NETWORK EQUIVALENCE", COMPARISON_FOOTERS["electrical"])
        self.assertIn("POWER FLOW", COMPARISON_FOOTERS["electrical"])
        self.assertNotIn("O(n²)", COMPARISON_FOOTERS["electrical"])

        self.assertIn("ASYMPTOTIC COMPLEXITY ANALYSIS", COMPARISON_FOOTERS["code"])

    def test_choreographer_quantum_physics_pipeline(self):
        """Verifies that choreographer injects rich quantum payload and domain-aware comparison footer."""
        scenes = [
            {"scene_type": "fullscreen_text", "spoken_text": "Quantum mechanics defies classical determinism completely.", "start_time": 0.0, "end_time": 4.0},
            {"scene_type": "quantum_sim", "spoken_text": "A wavepacket tunnels through a potential barrier exponentially.", "start_time": 4.0, "end_time": 9.0},
            {"scene_type": "quantum_sim", "spoken_text": "Heisenberg uncertainty forces momentum to explode under localization.", "start_time": 9.0, "end_time": 14.0},
            {"scene_type": "quantum_sim", "spoken_text": "Dirac relativistic spinors reveal spin and atomic probability clouds.", "start_time": 14.0, "end_time": 19.0},
            {"scene_type": "concept", "spoken_text": "In summary quantum mechanics governs subatomic energy regimes.", "start_time": 19.0, "end_time": 24.0},
        ]
        words = [
            {"word": "quantum", "start": 0.1, "end": 0.5},
            {"word": "tunneling", "start": 4.2, "end": 4.8},
            {"word": "regimes", "start": 23.5, "end": 24.0},
        ]
        enriched = choreograph_scenes(scenes, words, domain="quantum_physics")
        self.assertEqual(len(enriched), 5)

        # Scene 0 should be routed to comparison with domain-aware footer
        sc0 = enriched[0]
        self.assertEqual(sc0["visual_type"], "comparison")
        self.assertIn("COMMUTATION RELATION", sc0["comparison_footer"])
        self.assertNotIn("O(n²)", sc0["comparison_footer"])

        # Scene 1: quantum_sim with schrodinger_tunneling
        sc1 = enriched[1]
        self.assertEqual(sc1["visual_type"], "quantum_sim")
        self.assertEqual(sc1["sub_mode"], "schrodinger_tunneling")
        self.assertIn("tunneling_formula", sc1)
        self.assertEqual(sc1["theme"], "quantum_violet")

        # Scene 2: quantum_sim with heisenberg_uncertainty
        sc2 = enriched[2]
        self.assertEqual(sc2["visual_type"], "quantum_sim")
        self.assertEqual(sc2["sub_mode"], "heisenberg_uncertainty")
        self.assertIn("uncertainty_product", sc2)

        # Scene 3: quantum_sim with dirac_atomic_orbitals
        sc3 = enriched[3]
        self.assertEqual(sc3["visual_type"], "quantum_sim")
        self.assertEqual(sc3["sub_mode"], "dirac_atomic_orbitals")
        self.assertIn("quantum_numbers", sc3)

    def test_choreographer_mechanics_pipeline(self):
        """Verifies that choreographer enriches mechanics scenes with equilibrium payload and reactions."""
        scenes = [
            {"scene_type": "fullscreen_text", "spoken_text": "Equilibrium in bridge structures requires balance.", "start_time": 0.0, "end_time": 4.0},
            {"scene_type": "mechanics_fbd", "spoken_text": "Reaction forces at supports Ra and Rb balance the beam.", "start_time": 4.0, "end_time": 9.0},
            {"scene_type": "mechanics_fbd", "spoken_text": "Mass on an inclined plane accelerates past friction threshold.", "start_time": 9.0, "end_time": 14.0},
            {"scene_type": "mechanics_fbd", "spoken_text": "Chassis squat transfers dynamic load to the rear axle.", "start_time": 14.0, "end_time": 19.0},
            {"scene_type": "concept", "spoken_text": "In summary torque equilibrium prevents structural collapse.", "start_time": 19.0, "end_time": 24.0},
        ]
        enriched = choreograph_scenes(scenes, [], domain="mechanics")
        self.assertEqual(len(enriched), 5)

        sc0 = enriched[0]
        self.assertEqual(sc0["visual_type"], "comparison")
        self.assertIn("EQUILIBRIUM CONDITION", sc0["comparison_footer"])

        sc1 = enriched[1]
        self.assertEqual(sc1["sub_mode"], "beam_weight_distribution")
        self.assertIn("step1_torque", sc1)
        self.assertEqual(sc1["theme"], "mechanics_industrial")

        sc2 = enriched[2]
        self.assertEqual(sc2["sub_mode"], "inclined_plane_fbd")
        self.assertIn("friction_force", sc2)

        sc3 = enriched[3]
        self.assertEqual(sc3["sub_mode"], "axle_center_of_mass")
        self.assertIn("load_transfer", sc3)

    def test_choreographer_electrical_pipeline(self):
        """Verifies that choreographer enriches electrical scenes with Thevenin, KVL, and smart grid payload."""
        scenes = [
            {"scene_type": "fullscreen_text", "spoken_text": "Solving circuit networks requires systematic theorems.", "start_time": 0.0, "end_time": 4.0},
            {"scene_type": "electrical_grid", "spoken_text": "Kirchhoff voltage loop and current node equations solve currents.", "start_time": 4.0, "end_time": 9.0},
            {"scene_type": "electrical_grid", "spoken_text": "Thevenin theorem reduces complex circuits to Vth and Rth.", "start_time": 9.0, "end_time": 14.0},
            {"scene_type": "electrical_grid", "spoken_text": "Smart grid optimal power flow manages transmission congestion.", "start_time": 14.0, "end_time": 19.0},
            {"scene_type": "concept", "spoken_text": "In summary power conservation guarantees grid stability.", "start_time": 19.0, "end_time": 24.0},
        ]
        enriched = choreograph_scenes(scenes, [], domain="electrical")
        self.assertEqual(len(enriched), 5)

        sc0 = enriched[0]
        self.assertEqual(sc0["visual_type"], "comparison")
        self.assertIn("NETWORK EQUIVALENCE", sc0["comparison_footer"])

        sc1 = enriched[1]
        self.assertEqual(sc1["sub_mode"], "kvl_kcl_mesh")
        self.assertIn("kcl_equation", sc1)
        self.assertEqual(sc1["theme"], "electrical_neon")

        sc2 = enriched[2]
        self.assertEqual(sc2["sub_mode"], "thevenin_equivalence")
        self.assertIn("max_power", sc2)

        sc3 = enriched[3]
        self.assertEqual(sc3["sub_mode"], "smart_grid_opf")
        self.assertIn("lambda_cost", sc3)


if __name__ == "__main__":
    unittest.main()
