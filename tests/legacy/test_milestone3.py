import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
PUBLIC_DIR = REPO_DIR / "video" / "public"
RUNS_DIR = PUBLIC_DIR / "runs"

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))

import torch
from engine.audio import (
    generate_voice,
    verify_audio_file,
    get_whisper_device,
    get_whisper_model,
    reset_whisper_cache,
    validate_and_sanitize_word_timestamps,
)
from engine.timeline.beats import align_timeline, MIN_SCENE_DURATION
import generate as gen_module


class TestMilestone3(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_m3_")
        self.temp_path = Path(self.temp_dir)
        reset_whisper_cache()

    def tearDown(self):
        reset_whisper_cache()
        if "WHISPER_DEVICE" in os.environ:
            del os.environ["WHISPER_DEVICE"]
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Whisper Device Detection & In-Process Caching
    # -----------------------------------------------------------------------

    def test_whisper_device_detection_default(self):
        """Verify device detection selects 'cpu' or 'cuda' based on functional kernel check."""
        if "WHISPER_DEVICE" in os.environ:
            del os.environ["WHISPER_DEVICE"]
        device = get_whisper_device()
        self.assertIn(device, ["cuda", "cpu"])
        try:
            _ = torch.zeros(1, device="cuda") + 1
            cuda_functional = True
        except Exception:
            cuda_functional = False
        expected = "cuda" if (torch.cuda.is_available() and cuda_functional) else "cpu"
        self.assertEqual(device, expected)

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.zeros")
    def test_whisper_device_fallback_on_incompatible_cuda_kernel(self, mock_zeros, mock_avail):
        """Verify device detection falls back to 'cpu' when CUDA is available but kernel execution raises."""
        if "WHISPER_DEVICE" in os.environ:
            del os.environ["WHISPER_DEVICE"]
        mock_zeros.side_effect = RuntimeError("CUDA error: no kernel image is available for execution on the device")
        device = get_whisper_device()
        self.assertEqual(device, "cpu")

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.zeros")
    def test_whisper_device_selects_cuda_when_kernel_succeeds(self, mock_zeros, mock_avail):
        """Verify device detection selects 'cuda' when CUDA is available and kernel execution succeeds."""
        if "WHISPER_DEVICE" in os.environ:
            del os.environ["WHISPER_DEVICE"]
        mock_zeros.return_value = MagicMock()
        device = get_whisper_device()
        self.assertEqual(device, "cuda")

    def test_whisper_device_detection_env_override(self):
        """Verify WHISPER_DEVICE environment variable overrides dynamic detection."""
        os.environ["WHISPER_DEVICE"] = "cpu"
        self.assertEqual(get_whisper_device(), "cpu")

        os.environ["WHISPER_DEVICE"] = "cuda"
        self.assertEqual(get_whisper_device(), "cuda")

    @patch("whisper.load_model")
    def test_whisper_in_process_model_caching(self, mock_load):
        """Verify get_whisper_model caches in-process and avoids re-loading weights."""
        os.environ["WHISPER_DEVICE"] = "cpu"
        dummy_model = MagicMock()
        mock_load.return_value = dummy_model

        model1 = get_whisper_model("base")
        model2 = get_whisper_model("base")

        self.assertIs(model1, model2)
        mock_load.assert_called_once_with("base", device="cpu")

    @patch("whisper.load_model")
    def test_whisper_cache_reloads_on_device_change(self, mock_load):
        """Verify switching device invalidates previous cache and reloads on new device."""
        model_cpu = MagicMock(name="cpu_model")
        model_cuda = MagicMock(name="cuda_model")
        mock_load.side_effect = [model_cpu, model_cuda]

        os.environ["WHISPER_DEVICE"] = "cpu"
        m1 = get_whisper_model("base")
        self.assertIs(m1, model_cpu)

        os.environ["WHISPER_DEVICE"] = "cuda"
        m2 = get_whisper_model("base")
        self.assertIs(m2, model_cuda)

        self.assertEqual(mock_load.call_count, 2)

    # -----------------------------------------------------------------------
    # Audio Integrity & Playability Checks
    # -----------------------------------------------------------------------

    def test_verify_audio_file_non_existent(self):
        """Verify non-existent audio file fails validation with descriptive error."""
        non_existent = self.temp_path / "missing.mp3"
        valid, err = verify_audio_file(str(non_existent))
        self.assertFalse(valid)
        self.assertIn("does not exist", err.lower())

    def test_verify_audio_file_zero_bytes(self):
        """Verify zero-byte audio file fails validation."""
        empty_file = self.temp_path / "empty.mp3"
        empty_file.touch()
        valid, err = verify_audio_file(str(empty_file))
        self.assertFalse(valid)
        self.assertIn("zero bytes", err.lower())

    def test_verify_audio_file_corrupt_data(self):
        """Verify corrupted text or invalid bytes disguised as mp3 fails verification."""
        corrupt_file = self.temp_path / "corrupt.mp3"
        corrupt_file.write_text("This is not a real audio file\n")
        valid, err = verify_audio_file(str(corrupt_file))
        self.assertFalse(valid)
        self.assertIsNotNone(err)

    def test_verify_audio_file_valid_mp3(self):
        """Verify an authentic playable MP3 passes verification with duration > 0."""
        valid_mp3 = self.temp_path / "valid.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=0.5",
            "-c:a", "libmp3lame",
            str(valid_mp3)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"FFmpeg failed to create test fixture: {proc.stderr}")

        valid, err = verify_audio_file(str(valid_mp3))
        self.assertTrue(valid, f"Expected valid audio to pass verification: {err}")
        self.assertIsNone(err)

    # -----------------------------------------------------------------------
    # Edge-TTS Retry & Backoff
    # -----------------------------------------------------------------------

    @patch("edge_tts.Communicate.save")
    def test_generate_voice_retries_on_failure(self, mock_save):
        """Verify generate_voice retries up to max_retries before raising error."""
        mock_save.side_effect = RuntimeError("WebSocket drop")
        out_file = self.temp_path / "failed_tts.mp3"

        with self.assertRaises(RuntimeError) as ctx:
            asyncio.run(generate_voice("Test prompt", str(out_file), max_retries=3))

        self.assertIn("failed after 3 attempts", str(ctx.exception))
        self.assertEqual(mock_save.call_count, 3)
        self.assertFalse(out_file.exists(), "Corrupt/failed audio file must not linger")

    # -----------------------------------------------------------------------
    # Word Timestamp Monotonicity & Sanitization
    # -----------------------------------------------------------------------

    def test_validate_and_sanitize_word_timestamps(self):
        """Verify negative, zero-duration, and out-of-order timestamps are strictly sanitized."""
        raw_words = [
            {"word": "first", "start": -0.5, "end": 0.2},
            {"word": "second", "start": 0.1, "end": 0.05},  # inverted duration & regression
            {"word": "third", "start": 0.15, "end": 0.8},   # regression relative to sanitized second
            {"word": "fourth", "start": 1.0, "end": 1.4},
        ]

        sanitized = validate_and_sanitize_word_timestamps(raw_words)
        self.assertEqual(len(sanitized), 4)

        for i, w in enumerate(sanitized):
            self.assertGreaterEqual(w["start"], 0.0, f"Word {i} has negative start time")
            self.assertGreater(w["end"], w["start"], f"Word {i} end not greater than start")
            if i > 0:
                self.assertGreaterEqual(
                    w["start"],
                    sanitized[i - 1]["end"],
                    f"Word {i} start violates monotonicity with previous word end"
                )

    def test_validate_and_sanitize_empty_words_raises(self):
        """Verify empty word lists raise explicit ValueError."""
        with self.assertRaises(ValueError):
            validate_and_sanitize_word_timestamps([])

        with self.assertRaises(ValueError):
            validate_and_sanitize_word_timestamps([{"word": "   ", "start": 0.0, "end": 1.0}])

    # -----------------------------------------------------------------------
    # Timeline Beats Alignment & Stall Protection
    # -----------------------------------------------------------------------

    def test_align_timeline_mismatched_words_no_zero_duration_collapse(self):
        """
        Verify scenes whose first words do not match Whisper transcription
        never collapse to zero duration and maintain strict monotonicity.
        """
        scenes = [
            {"spoken_text": "Did you know lists are mutable?", "emphasis_word": "mutable"},
            {"spoken_text": "However tuples cannot ever change.", "emphasis_word": "tuples"},
            {"spoken_text": "Therefore use tuples as dict keys.", "emphasis_word": "keys"},
        ]
        # Whisper words that don't match first words ("did", "however", "therefore")
        words = [
            {"word": "unmatched_token_1", "start": 0.0, "end": 0.4},
            {"word": "unmatched_token_2", "start": 0.4, "end": 0.8},
            {"word": "unmatched_token_3", "start": 0.8, "end": 1.2},
            {"word": "mutable", "start": 1.5, "end": 1.9},
            {"word": "tuples", "start": 2.2, "end": 2.6},
            {"word": "keys", "start": 3.0, "end": 3.5},
        ]

        timed = align_timeline(scenes, words)
        self.assertEqual(len(timed), 3)

        for i in range(len(timed)):
            self.assertGreaterEqual(timed[i]["start_time"], 0.0)
            self.assertGreaterEqual(
                timed[i]["emphasis_time"],
                timed[i]["start_time"],
                f"Scene {i} emphasis time must be >= start time"
            )
            if i > 0:
                duration = timed[i]["start_time"] - timed[i - 1]["start_time"]
                self.assertGreaterEqual(
                    duration,
                    MIN_SCENE_DURATION,
                    f"Scene {i-1} collapsed to duration {duration}s (< {MIN_SCENE_DURATION}s)"
                )
                self.assertGreater(
                    timed[i]["start_time"],
                    timed[i - 1]["start_time"],
                    f"Scene {i} start_time must be strictly greater than Scene {i-1}"
                )

    def test_align_timeline_empty_words_graceful_handling(self):
        """Verify align_timeline handles empty words list safely without zero-duration collapse."""
        scenes = [
            {"spoken_text": "Scene one spoken words.", "emphasis_word": "one"},
            {"spoken_text": "Scene two spoken words.", "emphasis_word": "two"},
        ]

        timed = align_timeline(scenes, [])
        self.assertEqual(len(timed), 2)
        self.assertGreater(timed[1]["start_time"], timed[0]["start_time"])
        self.assertGreaterEqual(timed[0]["emphasis_time"], timed[0]["start_time"])
        self.assertGreaterEqual(timed[1]["emphasis_time"], timed[1]["start_time"])

    # -----------------------------------------------------------------------
    # Run Cleanup on Failure
    # -----------------------------------------------------------------------

    def test_cleanup_run_artifacts_deletes_directory(self):
        """Verify cleanup_run_artifacts removes the targeted run directory cleanly."""
        test_run_dir = RUNS_DIR / "run_test_cleanup_failure_123"
        test_run_dir.mkdir(parents=True, exist_ok=True)
        (test_run_dir / "audio.mp3").write_text("partial audio")
        (test_run_dir / "data.json").write_text("partial json")

        self.assertTrue(test_run_dir.exists())
        gen_module.cleanup_run_artifacts(test_run_dir)
        self.assertFalse(test_run_dir.exists(), "cleanup_run_artifacts failed to remove run directory")

    def test_cleanup_run_artifacts_non_existent_safe(self):
        """Verify cleanup_run_artifacts does not raise when directory does not exist."""
        test_run_dir = RUNS_DIR / "run_non_existent_456"
        try:
            gen_module.cleanup_run_artifacts(test_run_dir)
        except Exception as e:
            self.fail(f"cleanup_run_artifacts raised unexpected exception on non-existent dir: {e}")


if __name__ == "__main__":
    unittest.main()

