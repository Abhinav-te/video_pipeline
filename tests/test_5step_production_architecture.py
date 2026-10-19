"""
tests/test_5step_production_architecture.py

Unit and integration tests for the 5-Step Production Architecture:
- Step 1: Mock Director Layer (all 6 subjects, 35s & 60s scripts)
- Step 2: TypeScript/Node Zod Validation Gate
- Step 3: Self-Correcting Reflection Loop & Auto-Healing
- Step 4: Headless Manim Pre-Compiler Bridge & OffthreadVideo integration
- Step 5: Remotion Serverless Lambda Architecture Scaffold
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"

import sys
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from director.mock_library import get_mock_script
from director.script import DEFAULT_MODEL_CHAIN, get_model_chain
from validation import validate_script_plan
from validation.reflection import (
    write_reflection_error,
    read_reflection_error,
    clear_reflection_error,
    auto_heal_timeline_payload,
)
from renderer.manim_compiler import (
    resolve_scene_manim_template,
    verify_manim_asset,
    compile_manim_scenes,
)
from renderer.lambda_dispatcher import (
    check_aws_lambda_credentials,
    dispatch_lambda_render,
)


class Test5StepProductionArchitecture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_5step_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Step 1: Mock Director Layer
    # -----------------------------------------------------------------------

    def test_mock_library_covers_all_subjects_and_lengths(self):
        """Verify that get_mock_script covers math, quantum_physics, electrical, mechanics, chemistry, and code."""
        subjects = ["math", "quantum_physics", "electrical", "mechanics", "chemistry", "code"]
        lengths = [35, 60]

        for subj in subjects:
            for length in lengths:
                script = get_mock_script(topic=f"Test {subj}", duration=length, subject=subj)
                self.assertIsInstance(script, dict)
                self.assertEqual(script["subject"], subj)
                self.assertEqual(script["duration"], length)
                self.assertTrue(len(script["scenes"]) >= 5)

                is_valid, errors = validate_script_plan(script)
                self.assertTrue(
                    is_valid,
                    f"Mock script failed validation for subject='{subj}', length={length}: {errors}"
                )

    def test_model_chain_contains_no_retired_1_5_models(self):
        """Verify that gemini-1.5-flash and retired 1.5 models are purged from DEFAULT_MODEL_CHAIN."""
        chain = get_model_chain()
        for model in chain:
            self.assertNotIn("1.5", model, f"Found retired 1.5 model in chain: {model}")

    # -----------------------------------------------------------------------
    # Step 2: Node.js Zod Validation Gate
    # -----------------------------------------------------------------------

    def test_node_zod_gate_cli_passes_on_valid_data(self):
        """Verify that validate_timeline.mjs exits 0 on valid timeline payload."""
        valid_payload = {
            "title": "Calculus Derivations",
            "schema_version": "2.0.0",
            "run_id": "test_run_123",
            "scenes": [
                {
                    "scene_id": 0,
                    "title": "Hook",
                    "visual_type": "fullscreen_text",
                    "spoken_text": "What if calculus was simple?",
                    "start_time": 0.0,
                    "end_time": 3.0,
                },
                {
                    "scene_id": 1,
                    "title": "Fundamental Theorem",
                    "visual_type": "math_equation",
                    "spoken_text": "Integration and differentiation are inverses.",
                    "start_time": 3.0,
                    "end_time": 6.5,
                },
            ],
            "words": [
                {"word": "What", "start": 0.0, "end": 0.4},
                {"word": "if", "start": 0.4, "end": 0.8},
            ],
            "audio_file": "runs/test/audio.mp3",
        }
        data_json = self.temp_dir / "data.json"
        with open(data_json, "w", encoding="utf-8") as f:
            json.dump(valid_payload, f)

        zod_script = VIDEO_DIR / "scripts" / "validate_timeline.mjs"
        res = subprocess.run(["node", str(zod_script), str(data_json)], cwd=str(VIDEO_DIR), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Zod gate failed unexpectedly:\n{res.stderr}\n{res.stdout}")
        self.assertIn("[ZOD:SUCCESS]", res.stdout)

    def test_node_zod_gate_cli_fails_and_writes_error_on_invalid_data(self):
        """Verify that validate_timeline.mjs exits non-zero and writes validation.error.json on invalid payload."""
        invalid_payload = {
            "title": "Corrupt Timeline",
            "scenes": [
                {
                    "scene_id": 0,
                    # missing visual_type
                    "spoken_text": "Broken scene.",
                    "start_time": 5.0,
                    "end_time": 2.0,  # invalid end < start
                }
            ],
            "words": [],
        }
        data_json = self.temp_dir / "data.json"
        with open(data_json, "w", encoding="utf-8") as f:
            json.dump(invalid_payload, f)

        zod_script = VIDEO_DIR / "scripts" / "validate_timeline.mjs"
        res = subprocess.run(["node", str(zod_script), str(data_json)], cwd=str(VIDEO_DIR), capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("[ZOD:ERROR]", res.stderr)

        err_file = self.temp_dir / "validation.error.json"
        self.assertTrue(err_file.exists())
        with open(err_file, "r", encoding="utf-8") as f:
            err_data = json.load(f)
        self.assertEqual(err_data["stage"], "zod_gate")

    # -----------------------------------------------------------------------
    # Step 3: Self-Correcting Reflection Loop & Auto-Healing
    # -----------------------------------------------------------------------

    def test_reflection_error_serialization_and_read(self):
        """Verify that reflection errors are written and read cleanly."""
        clear_reflection_error(self.temp_dir)
        err_file = write_reflection_error(
            run_dir=self.temp_dir,
            stage="zod_gate",
            message="Schema invariant broken",
            errors=["end_time must be greater than start_time"],
            scene_id=2,
            field_path="scenes[2].end_time",
        )
        self.assertTrue(err_file.exists())

        read_err = read_reflection_error(self.temp_dir)
        self.assertIsNotNone(read_err)
        self.assertEqual(read_err["stage"], "zod_gate")
        self.assertEqual(read_err["scene_id"], 2)

    def test_auto_heal_timeline_payload_repairs_bounds(self):
        """Verify that auto_heal_timeline_payload repairs negative start times and non-monotonic order."""
        corrupted_payload = {
            "scenes": [
                {"scene_id": 0, "start_time": -1.0, "end_time": 1.0, "spoken_text": "Hook"},
                {"scene_id": 1, "start_time": 4.0, "end_time": 3.0, "spoken_text": "Middle"},
            ],
            "words": [
                {"word": "Negative", "start": -0.5, "end": 0.2},
                {"word": "Backwards", "start": 0.8, "end": 0.6},
            ],
        }

        healed, was_modified = auto_heal_timeline_payload(corrupted_payload)
        self.assertTrue(was_modified)

        # Scene 0 start healed to >= 0
        self.assertEqual(healed["scenes"][0]["start_time"], 0.0)
        # Scene 0 end duration >= 2.5s
        self.assertGreaterEqual(healed["scenes"][0]["end_time"], 2.5)
        # Scene 1 end > start
        self.assertGreater(healed["scenes"][1]["end_time"], healed["scenes"][1]["start_time"])

        # Word checks
        self.assertGreaterEqual(healed["words"][0]["start"], 0.0)
        self.assertGreater(healed["words"][1]["end"], healed["words"][1]["start"])

    # -----------------------------------------------------------------------
    # Step 4: Headless Manim Pre-Compiler Bridge
    # -----------------------------------------------------------------------

    def test_resolve_scene_manim_template(self):
        """Verify template resolution maps scenes to proper Manim template configurations."""
        math_scene = {"visual_type": "math_equation", "steps": ["f(x) = x^2", "f'(x) = 2x"]}
        t_name, params = resolve_scene_manim_template(math_scene, subject="math")
        self.assertEqual(t_name, "equation_morph")
        self.assertEqual(len(params["steps"]), 2)

        graph_scene = {"visual_type": "function_graph", "curves": ["0.5 * x**2"]}
        t_name, params = resolve_scene_manim_template(graph_scene, subject="math")
        self.assertEqual(t_name, "calculus_graph")
        self.assertEqual(params["fn_str"], "0.5 * x**2")

        quantum_scene = {"visual_type": "quantum_sim", "barrier_x": 0.5}
        t_name, params = resolve_scene_manim_template(quantum_scene, subject="quantum_physics")
        self.assertEqual(t_name, "quantum_wave")
        self.assertEqual(params["barrier_x"], 0.5)

    def test_verify_manim_asset_guards_small_files(self):
        """Verify that verify_manim_asset rejects files smaller than 10KB."""
        tiny_file = self.temp_dir / "tiny.mp4"
        with open(tiny_file, "wb") as f:
            f.write(b"0" * 1024)  # 1KB
        is_valid, _, _ = verify_manim_asset(tiny_file)
        self.assertFalse(is_valid)

    # -----------------------------------------------------------------------
    # Step 5: Remotion Serverless Lambda Architecture Scaffold
    # -----------------------------------------------------------------------

    def test_lambda_credentials_check_and_fallback(self):
        """Verify check_aws_lambda_credentials reports false and dispatch falls back when env vars are unset."""
        with patch.dict(os.environ, {}, clear=True):
            ready, msg = check_aws_lambda_credentials()
            self.assertFalse(ready)
            self.assertIn("not set", msg)

            fallback = dispatch_lambda_render(
                data_file_path=self.temp_dir / "data.json",
                output_file_path=self.temp_dir / "out.mp4",
            )
            self.assertFalse(fallback, "Should return False when AWS credentials are not set")


if __name__ == "__main__":
    unittest.main()
