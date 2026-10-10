import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"
PUBLIC_DIR = VIDEO_DIR / "public"
RUNS_DIR = PUBLIC_DIR / "runs"
PYTHON_EXEC = ENGINE_DIR / ".venv" / "bin" / "python"
if not PYTHON_EXEC.exists():
    PYTHON_EXEC = Path(sys.executable)


class TestMilestone5IntegrationAndReliability(unittest.TestCase):
    def test_cli_help_flag(self):
        """Verify the orchestrator CLI displays help with exit code 0."""
        cmd = [str(PYTHON_EXEC), str(REPO_DIR / "generate_and_render.py"), "--help"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("usage:", proc.stdout.lower())
        self.assertIn("--topic", proc.stdout)
        self.assertIn("--length", proc.stdout)

    def test_cli_missing_arguments_fails_fast(self):
        """Verify running without required --topic fails fast with non-zero exit code."""
        cmd = [str(PYTHON_EXEC), str(REPO_DIR / "generate_and_render.py")]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("required", proc.stderr.lower())
        self.assertIn("--topic", proc.stderr)

    def test_cli_invalid_length_choice(self):
        """Verify invalid video lengths (not in 15, 30, 60) are rejected by argparse."""
        cmd = [
            str(PYTHON_EXEC), str(REPO_DIR / "generate_and_render.py"),
            "--topic", "Valid Topic",
            "--length", "45"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid choice", proc.stderr.lower())

    def test_cli_empty_topic_fails_fast(self):
        """Verify empty or whitespace-only --topic is rejected with structured error."""
        cmd = [
            str(PYTHON_EXEC), str(REPO_DIR / "generate_and_render.py"),
            "--topic", "    ",
            "--length", "60"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[PIPELINE:ERROR]", proc.stderr)
        self.assertIn("--topic cannot be empty", proc.stderr)

    def test_simulated_pipeline_failure_clean_halt(self):
        """
        Verify that a stage failure (e.g. missing API key) halts the pipeline
        cleanly and cleans up the run directory without stale file contamination.
        """
        run_id = f"test_halt_clean_{int(time.time())}"
        run_dir = RUNS_DIR / run_id

        # Clean prior run if present
        if run_dir.exists():
            shutil.rmtree(run_dir, ignore_errors=True)

        env = os.environ.copy()
        env.pop("GEMINI_API_KEY", None)

        cmd = [
            str(PYTHON_EXEC), str(REPO_DIR / "generate_and_render.py"),
            "--topic", "Simulated Failure Topic",
            "--length", "60",
            "--run-id", run_id,
            "--no-cache",
        ]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True)

        self.assertNotEqual(proc.returncode, 0, "Pipeline must exit with non-zero on failure")
        combined_output = proc.stdout + proc.stderr
        self.assertTrue(
            "[DIRECTOR:ERROR]" in combined_output or "[PIPELINE:ERROR]" in combined_output,
            f"Expected stage error token. Got:\n{combined_output}"
        )
        self.assertFalse(
            run_dir.exists(),
            f"Run directory {run_dir} must not linger after pipeline failure"
        )

    def test_full_test_suite_execution_speed(self):
        """Verify that the discovery test suite runs deterministically in under 30 seconds."""
        cmd = [
            str(PYTHON_EXEC), "-m", "unittest", "discover",
            "-s", str(REPO_DIR / "tests"),
            "-p", "test_milestone[1-4].py",
        ]
        start_time = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start_time

        self.assertEqual(proc.returncode, 0, f"Test suite discovery failed:\n{proc.stderr}")
        self.assertLess(
            elapsed, 30.0,
            f"Test discovery took {elapsed:.2f}s, exceeding 30.0s requirement"
        )


if __name__ == "__main__":
    unittest.main()

