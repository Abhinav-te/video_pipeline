import unittest
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from engine.timeline.choreographer import (
    choreograph_scenes,
    synthesize_math_steps,
    synthesize_math_intuition,
    COMPARISON_FOOTERS,
    DOMAIN_MATH_STEPS,
    DOMAIN_MATH_INTUITION,
)


class TestPhase13ProductionLock(unittest.TestCase):
    def test_math_steps_and_intuition_domain_dehardcoding(self):
        """Verify choreographer never outputs Euler's identity or imaginary unit text unless Euler is mentioned."""
        domains = ["electrical", "mechanics", "quantum_physics", "chemistry", "physics", "ml", "code"]

        for domain in domains:
            scene = {
                "title": f"Optimal Operations in {domain.replace('_', ' ').title()}",
                "spoken_text": f"Analyzing key mathematical bounds and equations in {domain}.",
                "narration": f"Rigorous proof of fundamental theorems in {domain}.",
            }
            steps = synthesize_math_steps(scene, domain=domain)
            intuition = synthesize_math_intuition(scene, domain=domain)

            # 1. Must never return Euler's identity unless Euler is in prompt
            step_formulas = [s.get("formula", "") for s in steps]
            for f in step_formulas:
                self.assertNotIn("e^{i\\pi}", f, f"Euler formula leaked into {domain}: {f}")
                self.assertNotEqual("f(x) = y", f, f"Generic f(x)=y placeholder in {domain}")

            # 2. Must never return imaginary unit i rotation paragraph
            intuition_text = intuition.get("text", "") if isinstance(intuition, dict) else str(intuition)
            self.assertNotIn("imaginary unit", intuition_text.lower(), f"Imaginary unit i leaked into {domain}: {intuition_text}")
            self.assertNotIn("complex plane", intuition_text.lower(), f"Complex plane leaked into {domain}: {intuition_text}")

        # Specific domain formulas verification:
        elec_scene = {"title": "Transmission Limits", "spoken_text": "Economic dispatch optimization."}
        elec_steps = synthesize_math_steps(elec_scene, domain="electrical")
        self.assertTrue(any("P_{Gi}" in s["formula"] for s in elec_steps), "Electrical math steps missing active power balance")
        self.assertTrue(any("S_{ij}" in s["formula"] for s in elec_steps), "Electrical math steps missing line thermal limit")

        mech_scene = {"title": "Beam Equilibrium", "spoken_text": "Reaction forces."}
        mech_steps = synthesize_math_steps(mech_scene, domain="mechanics")
        self.assertTrue(any("F_y" in s["formula"] for s in mech_steps), "Mechanics math steps missing force equilibrium")
        self.assertTrue(any("\\tau_A" in s["formula"] for s in mech_steps), "Mechanics math steps missing torque balance")

        quantum_scene = {"title": "Wavepacket Tunneling", "spoken_text": "Barrier transmission decay."}
        q_steps = synthesize_math_steps(quantum_scene, domain="quantum_physics")
        self.assertTrue(any("\\kappa" in s["formula"] for s in q_steps), "Quantum math steps missing attenuation constant")
        self.assertTrue(any("e^{-2\\kappa L}" in s["formula"] for s in q_steps), "Quantum math steps missing transmission decay")

        chem_scene = {"title": "SN2 vs SN1 Kinetics", "spoken_text": "Reaction rates and activation barriers."}
        chem_steps = synthesize_math_steps(chem_scene, domain="chemistry")
        self.assertTrue(any("Rate" in s["formula"] for s in chem_steps), "Chemistry math steps missing rate law")
        self.assertTrue(any("E_a" in s["formula"] for s in chem_steps), "Chemistry math steps missing Arrhenius barrier")

    def test_euler_only_when_explicitly_requested(self):
        """Verify Euler derivation is only returned when Euler is explicitly in the prompt."""
        scene = {
            "title": "Euler's Formula and Identity",
            "spoken_text": "Multiplication on the complex unit circle.",
        }
        steps = synthesize_math_steps(scene, domain="math")
        self.assertTrue(any("e^{i\\pi}" in s["formula"] for s in steps))

    def test_eleven_scene_script_single_bento_grid_at_last_index(self):
        """Verify that on an 11-scene script, bento_grid appears strictly at scenes[-1] and never at scenes[-2] or scenes[-3]."""
        subjects = ["electrical", "mechanics", "quantum_physics", "chemistry"]

        for subj in subjects:
            raw_scenes = [
                {
                    "scene_index": i,
                    "title": f"{subj} Scene {i}",
                    "spoken_text": f"Detailed spoken explanation of {subj} principle {i} with key technical terminology.",
                    "narration": f"Narration for section {i}.",
                    "start_time": float(i * 5.5),
                    "end_time": float((i + 1) * 5.5),
                }
                for i in range(11)
            ]

            enriched = choreograph_scenes(raw_scenes, [], domain=subj, fps=30)
            self.assertEqual(len(enriched), 11)

            # Bento grid must be assigned ONLY to the final scene (index 10)
            bento_indices = [idx for idx, s in enumerate(enriched) if s.get("visual_type") == "bento_grid"]
            self.assertEqual(bento_indices, [10], f"Subject {subj} had bento_grid at {bento_indices}, expected [10]")

            # Scenes 7, 8, 9 must NOT be bento_grid
            self.assertNotEqual(enriched[7].get("visual_type"), "bento_grid")
            self.assertNotEqual(enriched[8].get("visual_type"), "bento_grid")
            self.assertNotEqual(enriched[9].get("visual_type"), "bento_grid")

    def test_llm_multiple_bento_grid_demoted_to_domain_visuals(self):
        """Verify that even if incoming raw script sets visual_type='bento_grid' on scenes 7, 8, 9, 10, only index 10 remains bento_grid."""
        raw_scenes = [
            {
                "scene_index": i,
                "title": f"Electrical Concept {i}",
                "spoken_text": f"Explanation of electrical principles {i}.",
                "visual_type": "bento_grid" if i >= 7 else "electrical_grid",
                "start_time": float(i * 5.5),
                "end_time": float((i + 1) * 5.5),
            }
            for i in range(11)
        ]

        enriched = choreograph_scenes(raw_scenes, [], domain="electrical", fps=30)
        bento_indices = [idx for idx, s in enumerate(enriched) if s.get("visual_type") == "bento_grid"]
        self.assertEqual(bento_indices, [10], f"Expected only [10] to be bento_grid, got {bento_indices}")
        self.assertIn(enriched[7].get("visual_type"), ["electrical_grid", "function_graph", "comparison", "math_equation"])
        self.assertIn(enriched[8].get("visual_type"), ["electrical_grid", "function_graph", "comparison", "math_equation"])
        self.assertIn(enriched[9].get("visual_type"), ["electrical_grid", "function_graph", "comparison", "math_equation"])

    def test_comparison_footers_clean_single_sentence(self):
        """Verify comparison footers never contain pipe '|' duplicate suffixes and start with 'KEY TAKEAWAY:'."""
        for domain, footer in COMPARISON_FOOTERS.items():
            self.assertNotIn("|", footer, f"Domain {domain} comparison footer contains duplicate pipe suffix: {footer}")
            self.assertTrue(footer.startswith("KEY TAKEAWAY:"), f"Domain {domain} footer does not start with 'KEY TAKEAWAY:': {footer}")

        # Check choreographed comparison scene
        raw_scenes = [
            {
                "scene_index": 0,
                "title": "Comparison Hook",
                "spoken_text": "Contrasting conventional mesh analysis with Thevenin equivalence.",
                "visual_type": "comparison",
                "comparison_footer": "NETWORK EQUIVALENCE: Linear network reduction simplifies multi-bus OPF solver complexity by 100x | NETWORK EQUIVALENCE: V_th = V_oc",
                "start_time": 0.0,
                "end_time": 5.0,
            },
            {
                "scene_index": 1,
                "title": "Final Summary",
                "spoken_text": "Concluding electrical power grid architecture.",
                "start_time": 5.0,
                "end_time": 10.0,
            },
        ]
        enriched = choreograph_scenes(raw_scenes, [], domain="electrical", fps=30)
        footer = enriched[0].get("comparison_footer", "")
        self.assertNotIn("|", footer, f"Choreographer did not strip pipe suffix from comparison footer: {footer}")
        self.assertTrue(footer.startswith("KEY TAKEAWAY:"), f"Choreographer footer missing KEY TAKEAWAY prefix: {footer}")


if __name__ == "__main__":
    unittest.main()

