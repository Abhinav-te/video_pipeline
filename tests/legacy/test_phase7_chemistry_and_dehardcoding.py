"""
Phase 7 Unit Tests: Multi-Subject De-Hardcoding & Chemistry Reaction Engine.

Verifies:
  1. Script spelling preservation over Whisper phonetic mishears (DBSCAN, partitions, SN2, Nucleophile).
  2. Elimination of < 2.5s flash scenes (redistributing boundary timestamps so all scenes are >= 2.5s).
  3. De-hardcoding of concept scenes: non-autoencoder scenes NEVER receive Autoencoder or 784 dims.
  4. Concluding/takeaway scenes do NOT route to neural_code_split.
  5. Chemistry Reaction Visualization Engine: schema validation, mode detection, payload synthesis, and choreography.
"""

import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from director.script import detect_domain
from timeline.beats import (
    align_script_tokens_to_whisper,
    enforce_minimum_scene_durations,
)
from timeline.choreographer import (
    choreograph_scenes,
    detect_chemistry_mode,
    synthesize_chemistry_payload,
    synthesize_concept_card,
)
from validation.schema import validate_script_plan


class TestPhase7ChemistryAndDehardcoding(unittest.TestCase):

    def test_whisper_phonetic_override_preserves_script_spelling(self):
        """
        Verify that script tokens (DBSCAN, partitions, Nucleophile, SN2)
        override Whisper's phonetic mishears (DISCAN, PETITIONS, etc.).
        """
        script_text = "DBSCAN clusters data by density partitions instead of centroids for SN2 Nucleophile substitution."
        whisper_words = [
            {"word": "DISCAN", "start": 0.0, "end": 0.4},
            {"word": "clusters", "start": 0.4, "end": 0.8},
            {"word": "data", "start": 0.8, "end": 1.1},
            {"word": "by", "start": 1.1, "end": 1.3},
            {"word": "density", "start": 1.3, "end": 1.7},
            {"word": "PETITIONS", "start": 1.7, "end": 2.2},
            {"word": "instead", "start": 2.2, "end": 2.5},
            {"word": "of", "start": 2.5, "end": 2.7},
            {"word": "centroids", "start": 2.7, "end": 3.2},
            {"word": "for", "start": 3.2, "end": 3.4},
            {"word": "S", "start": 3.4, "end": 3.5},
            {"word": "N", "start": 3.5, "end": 3.6},
            {"word": "two", "start": 3.6, "end": 3.8},
            {"word": "nuclear", "start": 3.8, "end": 4.1},
            {"word": "file", "start": 4.1, "end": 4.4},
            {"word": "substitution", "start": 4.4, "end": 5.0},
        ]

        aligned = align_script_tokens_to_whisper(script_text, whisper_words)
        aligned_words = [w["word"] for w in aligned]

        # Script spelling must be strictly preserved
        self.assertIn("DBSCAN", aligned_words, "Failed to preserve 'DBSCAN' over Whisper 'DISCAN'")
        self.assertNotIn("DISCAN", aligned_words, "Whisper mishear 'DISCAN' was erroneously preserved")

        self.assertIn("partitions", aligned_words, "Failed to preserve 'partitions' over Whisper 'PETITIONS'")
        self.assertNotIn("PETITIONS", aligned_words, "Whisper mishear 'PETITIONS' was erroneously preserved")

        self.assertIn("SN2", aligned_words, "Failed to preserve 'SN2'")
        self.assertIn("Nucleophile", aligned_words, "Failed to preserve 'Nucleophile'")

        # Timestamps must remain monotonically non-decreasing
        for i in range(len(aligned) - 1):
            self.assertLessEqual(aligned[i]["start"], aligned[i]["end"])
            self.assertLessEqual(aligned[i]["start"], aligned[i + 1]["start"])

    def test_enforce_minimum_scene_durations_eliminates_flash_cuts(self):
        """
        Verify that short scenes (< 2.5s, e.g. a 0.7s flash scene at 00:18)
        have their boundaries redistributed or merged so every scene is strictly >= 2.5s.
        """
        raw_scenes = [
            {"scene_type": "fullscreen_text", "start_time": 0.0, "end_time": 10.0},
            {"scene_type": "bento_grid", "start_time": 10.0, "end_time": 18.0},
            {"scene_type": "concept", "start_time": 18.0, "end_time": 18.7},  # 0.7s Flash Scene!
            {"scene_type": "algorithm_explorer", "start_time": 18.7, "end_time": 28.0},
            {"scene_type": "comparison", "start_time": 28.0, "end_time": 35.0},
        ]

        cleaned = enforce_minimum_scene_durations(raw_scenes, min_duration=2.5, total_duration=35.0)

        # Confirm every scene in cleaned is strictly >= 2.5s
        for idx, scene in enumerate(cleaned):
            dur = scene["end_time"] - scene["start_time"]
            self.assertGreaterEqual(
                dur, 2.49,
                f"Scene {idx} ({scene.get('scene_type')}) duration {dur:.2f}s is below 2.5s minimum!"
            )

        # Confirm 100% contiguity: scene[i].end_time == scene[i+1].start_time
        for i in range(len(cleaned) - 1):
            self.assertAlmostEqual(
                cleaned[i]["end_time"],
                cleaned[i + 1]["start_time"],
                places=2,
                msg=f"Gaps found between scene {i} and {i+1}!"
            )

        # Confirm timeline starts at 0.0 and ends at total_duration
        self.assertEqual(cleaned[0]["start_time"], 0.0)
        self.assertEqual(cleaned[-1]["end_time"], 35.0)

    def test_concept_dehardcoding_never_injects_autoencoder_into_other_topics(self):
        """
        Verify that choreographer and synthesize_concept_card NEVER inject
        'autoencoder' diagram_mode or '784 dims' / autoencoder bullets into non-autoencoder scenes.
        """
        test_scenes = [
            {
                "scene_type": "concept",
                "title": "Density Reachability in DBSCAN",
                "spoken_text": "Points within epsilon distance form contiguous dense clusters that trace arbitrary geometric shapes.",
                "start_time": 0.0,
                "end_time": 4.0,
            },
            {
                "scene_type": "concept",
                "title": "Raft Consensus Invariant",
                "spoken_text": "The leader log is monotonically appended and committed only after majority quorum confirmation.",
                "start_time": 4.0,
                "end_time": 8.0,
            },
            {
                "scene_type": "concept",
                "title": "SN2 Backside Attack Geometry",
                "spoken_text": "The nucleophile attacks directly opposite the carbon halogen bond creating umbrella inversion.",
                "start_time": 8.0,
                "end_time": 12.0,
            },
        ]

        choreographed = choreograph_scenes(test_scenes, [], domain="auto")

        for idx, sc in enumerate(choreographed):
            # diagram_mode must NOT be autoencoder
            self.assertNotEqual(
                sc.get("diagram_mode"), "autoencoder",
                f"Scene {idx} ('{sc.get('title')}') erroneously received 'autoencoder' diagram_mode!"
            )
            if sc.get("visual_type") == "concept":
                self.assertIn(sc.get("diagram_mode"), {"concept_card", "benchmark", "arena"})
            elif sc.get("visual_type") == "chemistry_reaction":
                self.assertIn(sc.get("chemistry_mode"), {"sn2_substitution", "sn1_carbocation", "addition_alkene", "redox_combustion"})

            # Bullets and points must NOT mention autoencoders or 784 dims
            points = sc.get("points") or sc.get("bullets") or sc.get("takeaways") or []
            combined_text = " ".join(points).lower()
            self.assertNotIn("autoencoder", combined_text)
            self.assertNotIn("784 dims", combined_text)
            self.assertNotIn("bottleneck layer", combined_text)
            self.assertNotIn("reconstruction loss", combined_text)

            # Concept nodes must be populated on concept scenes
            if sc.get("visual_type") == "concept":
                self.assertIn("concept_nodes", sc)
                self.assertGreaterEqual(len(sc["concept_nodes"]), 2)

    def test_concluding_scenes_do_not_route_to_neural_code_split(self):
        """
        Verify that concluding scenes mentioning deep learning bloat as a negative contrast
        route to comparison or concept, NEVER to neural_code_split.
        """
        scenes = [
            {
                "scene_type": "fullscreen_text",
                "start_time": 0.0,
                "end_time": 4.0,
                "spoken_text": "Why DBSCAN beats K-Means every single time.",
            },
            {
                "scene_type": "algorithm_explorer",
                "start_time": 4.0,
                "end_time": 8.0,
                "spoken_text": "Epsilon distance scanning traces the contiguous manifold.",
            },
            {
                "scene_type": "concept",
                "title": "Summary & Takeaways",
                "start_time": 8.0,
                "end_time": 13.0,
                # Narration mentions deep learning as negative contrast
                "spoken_text": "Geometry beats deep learning bloat. Avoid burning GPU hours when simple density clustering converges in milliseconds.",
            },
        ]

        choreographed = choreograph_scenes(scenes, [], domain="ml")
        closing_scene = choreographed[-1]

        # Must NOT be neural_code_split!
        self.assertNotEqual(
            closing_scene["visual_type"], "neural_code_split",
            "Concluding scene erroneously routed to neural_code_split due to 'deep learning' keyword!"
        )
        self.assertIn(closing_scene["visual_type"], {"comparison", "concept"})

    def test_chemistry_domain_detection_and_validation(self):
        """Verify that chemistry topics auto-detect as 'chemistry' and pass schema validation."""
        chem_topics = [
            "SN2 Reaction Mechanism of Alkyl Halides",
            "Electrophilic Addition across Alkene Double Bonds",
            "Carbocation Stability in SN1 Solvolysis",
            "Acid-Base Neutralization and Enthalpy",
        ]
        for topic in chem_topics:
            self.assertEqual(detect_domain(topic), "chemistry", f"Failed to detect chemistry domain for '{topic}'")

        # Validate chemistry_reaction script plan (max 11 words per beat)
        valid_chem_plan = {
            "title": "Mastering SN2 Reaction Mechanisms",
            "domain": "chemistry",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "display_text": "Why SN2 Reactions Invert Stereocenters",
                    "spoken_text": "Every organic chemist must understand concerted backside attack.",
                },
                {
                    "scene_type": "chemistry_reaction",
                    "title": "SN2 Bimolecular Substitution",
                    "spoken_text": "Hydroxide attacks opposite carbon bromine bond causing inversion.",
                    "reaction_name": "SN2 Bimolecular Substitution",
                    "mode": "sn2_substitution",
                },
                {
                    "scene_type": "comparison",
                    "title": "SN1 vs SN2 Comparison",
                    "spoken_text": "SN2 is concerted while SN1 forms a carbocation.",
                    "comparison_sides": {
                        "left": {"tag": "SN1", "title": "Two-Step Mechanism", "metric": "Racemization"},
                        "right": {"tag": "SN2", "title": "Concerted Backside Attack", "metric": "100% Inversion"},
                    },
                },
            ]
        }
        is_valid, errs = validate_script_plan(valid_chem_plan)
        self.assertTrue(is_valid, f"Chemistry script plan validation failed: {errs}")

    def test_chemistry_payload_and_choreography_synthesis(self):
        """Verify detect_chemistry_mode, synthesize_chemistry_payload, and choreography 3-phase intervals."""
        # 1. Mode Detection
        self.assertEqual(detect_chemistry_mode({"spoken_text": "Forms a carbocation intermediate in solvolysis"}), "sn1_carbocation")
        self.assertEqual(detect_chemistry_mode({"spoken_text": "Addition across alkene double bond with Markovnikov rule"}), "addition_alkene")
        self.assertEqual(detect_chemistry_mode({"spoken_text": "Exothermic redox combustion and proton exchange"}), "redox_combustion")
        self.assertEqual(detect_chemistry_mode({"spoken_text": "Nucleophile backside attack on alkyl halide"}), "sn2_substitution")

        # 2. Payload Synthesis
        sn2_payload = synthesize_chemistry_payload({"spoken_text": "SN2 reaction with heat delta applied"}, "sn2_substitution")
        self.assertEqual(sn2_payload["mode"], "sn2_substitution")
        self.assertTrue(sn2_payload["heat_applied"])
        self.assertEqual(sn2_payload["temperature_kelvin"], 355)
        self.assertIn("energy_profile", sn2_payload)

        # 3. Choreography 3-Phase Animation Boundaries
        chem_scenes = [
            {
                "scene_type": "chemistry_reaction",
                "title": "SN2 Mechanism",
                "spoken_text": "Hydroxide attacks opposite bromine causing Walden inversion.",
                "start_time": 0.0,
                "end_time": 6.0,
            }
        ]
        choreographed = choreograph_scenes(chem_scenes, [], domain="chemistry", fps=30)
        choreo = choreographed[0]["choreography"]

        self.assertIn("chemistry", choreo)
        chem_choreo = choreo["chemistry"]
        self.assertEqual(chem_choreo["mode"], "sn2_substitution")
        self.assertGreater(chem_choreo["phase1_end_frame"], choreo["scene_start_frame"])
        self.assertGreater(chem_choreo["phase2_end_frame"], chem_choreo["phase1_end_frame"])
        self.assertGreaterEqual(chem_choreo["phase3_end_frame"], chem_choreo["phase2_end_frame"])


if __name__ == "__main__":
    unittest.main()
