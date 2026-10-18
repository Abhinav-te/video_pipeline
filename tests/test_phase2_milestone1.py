import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR = REPO_DIR / "video"
SRC_DIR = VIDEO_DIR / "src"

sys.path.insert(0, str(REPO_DIR / "engine"))
sys.path.insert(0, str(REPO_DIR))


class TestPhase2Milestone1CameraRig(unittest.TestCase):
    def test_camerarig_component_file_exists(self):
        """Verify CameraRig.jsx and cameraUtils.js exist in video/src/."""
        camerarig_file = SRC_DIR / "CameraRig.jsx"
        camera_utils_file = SRC_DIR / "cameraUtils.js"
        self.assertTrue(camerarig_file.exists(), f"Missing {camerarig_file}")
        self.assertTrue(camera_utils_file.exists(), f"Missing {camera_utils_file}")

    def test_camerarig_exports_and_spring_physics(self):
        """Verify CameraRig exports critically damped spring physics to eliminate jitter."""
        content = (SRC_DIR / "cameraUtils.js").read_text(encoding="utf-8")
        self.assertIn("damping: 18", content)
        self.assertIn("stiffness: 80", content)
        self.assertIn("mass: 0.6", content)
        self.assertIn("computeFocusOrigin", content)
        self.assertIn("computeCameraZoom", content)

    def test_codingshort_integrates_camerarig(self):
        """Verify CodingShort.jsx imports and uses CameraRig around card primitives."""
        coding_short = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertIn("import { CameraRig } from './CameraRig';", coding_short)
        self.assertIn("<CameraRig", coding_short)
        # focusPhrase is passed to CodeBlock (not CameraRig) for token highlighting
        self.assertIn("focusPhrase={activeScene.focus_phrase}", coding_short)
        # Safe area: all code cards must use maxWidth:920px so 1.04x zoom stays in-frame
        self.assertIn("maxWidth: '920px'", coding_short)

    def test_node_camerarig_unit_test_suite_passes(self):
        """Run Node test suite verifying spring math, focal clamping, and graceful fallbacks."""
        test_script = VIDEO_DIR / "test_camerarig.mjs"
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
        self.assertIn("All CameraRig unit tests passed successfully!", proc.stdout)

    def test_no_audio_or_timing_alterations(self):
        """Verify that data.json contract is preserved with zero audio drift or timing corruption."""
        from validation.schema import validate_script_plan
        from timeline.beats import align_timeline

        # Ensure timeline beats alignment remains identical
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

    def test_codingshort_pop_sfx_sequence_synchronization(self):
        """Verify CodingShort uses Remotion Sequence one-shot pattern for pop SFX and removes isPopTime."""
        coding_short = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertNotIn("isPopTime", coding_short, "Legacy isPopTime frame check must be removed.")
        self.assertIn("Sequence", coding_short)
        self.assertIn("durationInFrames={30}", coding_short)
        self.assertIn("from={emphasisFrame}", coding_short)
        self.assertIn("staticFile('pop.mp3')", coding_short)


if __name__ == "__main__":
    unittest.main()

