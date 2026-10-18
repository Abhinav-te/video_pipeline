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

sys.path.insert(0, str(REPO_DIR / "engine"))
sys.path.insert(0, str(REPO_DIR))


class TestPhase2Milestone2KineticCallout(unittest.TestCase):
    def test_callout_component_and_utils_exist(self):
        """Verify KineticCallout.jsx and calloutUtils.js exist in expected locations."""
        callout_file = COMPONENTS_DIR / "KineticCallout.jsx"
        utils_file = SRC_DIR / "calloutUtils.js"
        self.assertTrue(callout_file.exists(), f"Missing {callout_file}")
        self.assertTrue(utils_file.exists(), f"Missing {utils_file}")

    def test_callout_utils_exports_and_spring_physics(self):
        """Verify calloutUtils.js exports critically damped spring physics and style presets."""
        content = (SRC_DIR / "calloutUtils.js").read_text(encoding="utf-8")
        self.assertIn("damping: 18", content)
        self.assertIn("stiffness: 80", content)
        self.assertIn("mass: 0.6", content)
        self.assertIn("CALLOUT_STYLES", content)
        self.assertIn("pill", content)
        self.assertIn("box_glow", content)
        self.assertIn("badge", content)
        self.assertIn("findTokenMatch", content)
        self.assertIn("splitCodeByToken", content)
        self.assertIn("resolveCalloutTiming", content)

    def test_kinetic_callout_spring_entrance_and_exit_fade(self):
        """Verify KineticCallout implements spring scale/opacity entrance and exit fade."""
        content = (COMPONENTS_DIR / "KineticCallout.jsx").read_text(encoding="utf-8")
        self.assertIn("spring({", content)
        self.assertIn("interpolate(", content)
        self.assertIn("[0.8, 1.0]", content)
        self.assertIn("exitProgress", content)
        self.assertIn("willChange", content)

    def test_subpixel_stabilization_and_hardware_acceleration(self):
        """Verify static-grid transform: none, backfaceVisibility: hidden, and overshoot clamping are present."""
        callout_content = (COMPONENTS_DIR / "KineticCallout.jsx").read_text(encoding="utf-8")
        self.assertIn("transform: 'none'", callout_content)
        self.assertIn("backfaceVisibility", callout_content)
        self.assertIn("boxSizing", callout_content)
        self.assertIn("Math.min(springVal, 1.0)", callout_content)

        coding_short = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertIn("translateZ(0)", coding_short)
        self.assertIn("backfaceVisibility", coding_short)
        self.assertIn("lineHeight", coding_short)

    def test_codingshort_integrates_kinetic_callout_and_codeblock(self):
        """Verify CodingShort.jsx integrates KineticCallout across code scenes."""
        coding_short = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertIn("import { KineticCallout } from './components/KineticCallout';", coding_short)
        self.assertIn("import { splitCodeByToken, resolveCalloutTiming } from './calloutUtils';", coding_short)
        self.assertIn("<KineticCallout", coding_short)
        # Verify CodeBlock integration in code_reveal, code_transform, comparison
        self.assertIn("styleVariant=", coding_short)
        self.assertIn("problem_code", coding_short)
        self.assertIn("solution_code", coding_short)

    def test_node_kinetic_callouts_unit_test_suite_passes(self):
        """Run Node test suite verifying fuzzy matching, code splitting, and Whisper timing alignment."""
        test_script = VIDEO_DIR / "test_kinetic_callouts.mjs"
        self.assertTrue(test_script.exists())

        proc = subprocess.run(
            ["node", str(test_script)],
            cwd=str(VIDEO_DIR),
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            proc.returncode, 0,
            f"Node test failed with code {proc.returncode}:\n{proc.stderr}\n{proc.stdout}"
        )
        self.assertIn("All Kinetic Callout unit tests passed successfully!", proc.stdout)

    def test_zero_audio_drift_and_contract_preservation(self):
        """Verify that audio generation and timeline alignment contracts are not altered."""
        from timeline.beats import align_timeline

        test_scenes = [
            {"spoken_text": "First scene words for test", "emphasis_word": "words"},
            {"spoken_text": "Second scene words for test", "emphasis_word": "scene"},
        ]
        test_words = [
            {"word": "First", "start": 0.0, "end": 0.3},
            {"word": "scene", "start": 0.3, "end": 0.6},
            {"word": "words", "start": 0.6, "end": 0.9},
            {"word": "for", "start": 0.9, "end": 1.1},
            {"word": "test", "start": 1.1, "end": 1.4},
            {"word": "Second", "start": 1.6, "end": 1.9},
            {"word": "scene", "start": 1.9, "end": 2.2},
            {"word": "words", "start": 2.2, "end": 2.5},
            {"word": "for", "start": 2.5, "end": 2.7},
            {"word": "test", "start": 2.7, "end": 3.0},
        ]
        timed = align_timeline(test_scenes, test_words)
        self.assertEqual(len(timed), 2)
        self.assertEqual(timed[0]["start_time"], 0.0)
        self.assertEqual(timed[0]["emphasis_time"], 0.6)
        self.assertEqual(timed[1]["start_time"], 1.6)
        self.assertEqual(timed[1]["emphasis_time"], 1.9)


if __name__ == "__main__":
    unittest.main()

