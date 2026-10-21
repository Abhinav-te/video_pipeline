import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
PUBLIC_DIR = REPO_DIR / "video" / "public"
RUNS_DIR = PUBLIC_DIR / "runs"

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))

import generate as gen_module
import generate_and_render as gar_module


class TestMilestone1(unittest.TestCase):
    def test_run_id_format(self):
        """Verify generated run IDs match the required pattern run_YYYYMMDD_HHMMSS_<shortid>."""
        run_id1 = gen_module.generate_run_id()
        run_id2 = gar_module.generate_run_id()

        pattern = r"^run_\d{8}_\d{6}_[a-f0-9]{6}$"
        self.assertRegex(run_id1, pattern, f"Run ID {run_id1} does not match {pattern}")
        self.assertRegex(run_id2, pattern, f"Run ID {run_id2} does not match {pattern}")
        self.assertNotEqual(run_id1, run_id2, "Consecutive run IDs must be unique")

    def test_no_hardcoded_home_paths(self):
        """Verify that generate_and_render.py and engine/generate.py have no hardcoded ~/ or /home/ paths."""
        for script_name in ["generate_and_render.py", "engine/generate.py"]:
            script_path = REPO_DIR / script_name
            content = script_path.read_text(encoding="utf-8")
            self.assertNotIn("~/", content, f"Hardcoded tilde path found in {script_name}")
            self.assertNotIn("/home/", content, f"Hardcoded /home/ path found in {script_name}")

    def test_run_isolation_payload(self):
        """Verify that build_final_payload outputs isolated audio_file path without global collision."""
        run_id = gen_module.generate_run_id()
        script = {
            "title": "Test Title",
            "schema_version": "2.1",
            "scenes": [{"scene_type": "fullscreen_text", "spoken_text": "Hello world"}]
        }
        timed_scenes = script["scenes"]
        words = [{"word": "Hello", "start": 0.0, "end": 0.5}, {"word": "world", "start": 0.5, "end": 1.0}]

        payload = gen_module.build_final_payload(script, timed_scenes, words, run_id)

        self.assertEqual(payload["run_id"], run_id)
        self.assertEqual(payload["audio_file"], f"runs/{run_id}/audio.mp3")
        self.assertNotEqual(payload["audio_file"], "audio_current.mp3")

    def test_isolated_write_does_not_touch_global_files(self):
        """Verify write_data_file writes to dedicated run path and does not touch data_current.json."""
        run_id = gen_module.generate_run_id()
        target_dir = RUNS_DIR / run_id
        target_file = target_dir / "data.json"

        global_data_file = PUBLIC_DIR / "data_current.json"
        had_global_file = global_data_file.exists()

        payload = {
            "title": "Isolation Test",
            "run_id": run_id,
            "scenes": [],
            "words": [],
            "audio_file": f"runs/{run_id}/audio.mp3"
        }

        try:
            gen_module.write_data_file(payload, target_file)

            self.assertTrue(target_file.exists())
            self.assertGreater(target_file.stat().st_size, 0)
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["run_id"], run_id)

            if not had_global_file:
                self.assertFalse(global_data_file.exists(), "Global data_current.json should not be created")
        finally:
            if target_file.exists():
                target_file.unlink()
            if target_dir.exists():
                target_dir.rmdir()

    def test_fail_fast_error_propagation_missing_key(self):
        """Verify that running engine/generate.py without GEMINI_API_KEY prints [DIRECTOR:ERROR] and exits non-zero."""
        env = os.environ.copy()
        env.pop("GEMINI_API_KEY", None)

        python_exec = ENGINE_DIR / ".venv" / "bin" / "python"
        result = subprocess.run(
            [str(python_exec), str(ENGINE_DIR / "generate.py"), "--topic", "Python Decorators"],
            cwd=str(ENGINE_DIR),
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0, "Expected non-zero exit code when GEMINI_API_KEY is missing")
        self.assertIn("[DIRECTOR:ERROR]", result.stderr, f"Expected [DIRECTOR:ERROR] token in stderr. Got:\n{result.stderr}")

    def test_fail_fast_validation_error(self):
        """Verify that validate_script halts immediately with [VALIDATION:ERROR] on invalid scene schema."""
        invalid_script = {
            "title": "Bad Script",
            "scenes": [
                {
                    "scene_type": "invalid_unknown_type",
                    "spoken_text": "This should fail validation gate."
                }
            ]
        }

        with self.assertRaises(SystemExit) as cm:
            gen_module.validate_script(invalid_script)

        self.assertNotEqual(cm.exception.code, 0, "Expected non-zero exit code on validation failure")


if __name__ == "__main__":
    unittest.main()

