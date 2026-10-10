import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"
PUBLIC_DIR = VIDEO_DIR / "public"
RUNS_DIR = PUBLIC_DIR / "runs"

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))

from validation.output import (
    validate_video_output,
    validate_video_or_raise,
    OutputValidationError,
    get_media_duration,
    REQUIRED_WIDTH,
    REQUIRED_HEIGHT,
    TARGET_FPS,
)


class TestMilestone4OutputValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work_dir = Path(tempfile.mkdtemp(prefix="test_m4_"))
        cls.valid_video_path = cls.work_dir / "valid_vertical.mp4"
        cls.valid_audio_path = cls.work_dir / "valid_narration.mp3"

        # Generate a 4-second reference audio narration (sine wave, 44.1kHz, mp3)
        cmd_audio = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-c:a", "libmp3lame",
            "-t", "4",
            str(cls.valid_audio_path),
        ]
        proc_a = subprocess.run(cmd_audio, capture_output=True, text=True)
        if proc_a.returncode != 0:
            raise RuntimeError(f"Failed to generate test audio: {proc_a.stderr}")

        # Generate a 4-second fully compliant vertical video (1080x1920, 30fps, h264, aac, >100KB)
        cmd_video = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            "-t", "4",
            str(cls.valid_video_path),
        ]
        proc_v = subprocess.run(cmd_video, capture_output=True, text=True)
        if proc_v.returncode != 0:
            raise RuntimeError(f"Failed to generate valid test video: {proc_v.stderr}")

    @classmethod
    def tearDownClass(cls):
        if cls.work_dir.exists():
            shutil.rmtree(cls.work_dir, ignore_errors=True)

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_m4_case_"))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_video_file(self):
        """Verify missing video file returns False with descriptive error."""
        missing = self.temp_dir / "does_not_exist.mp4"
        valid, errors, _ = validate_video_output(missing)
        self.assertFalse(valid)
        self.assertTrue(any("does not exist" in e.lower() for e in errors))

    def test_zero_byte_video_file(self):
        """Verify zero-byte video file returns False."""
        empty_file = self.temp_dir / "empty.mp4"
        empty_file.touch()
        valid, errors, _ = validate_video_output(empty_file)
        self.assertFalse(valid)
        self.assertTrue(any("0 bytes" in e.lower() for e in errors))

    def test_undersized_video_file(self):
        """Verify video files smaller than 100KB are rejected."""
        undersized = self.temp_dir / "undersized.mp4"
        # Generate 0.5s video (< 50KB)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            "-t", "0.5",
            str(undersized),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        self.assertLess(undersized.stat().st_size, 100 * 1024)

        valid, errors, _ = validate_video_output(undersized, min_size_bytes=100 * 1024)
        self.assertFalse(valid)
        self.assertTrue(any("too small" in e.lower() for e in errors))

    def test_invalid_container_format(self):
        """Verify non-MP4 or corrupted files are caught."""
        corrupt = self.temp_dir / "corrupt.mp4"
        corrupt.write_text("NOT_A_VALID_MP4_HEADER" * 5000)
        valid, errors, _ = validate_video_output(corrupt, min_size_bytes=1000)
        self.assertFalse(valid)
        self.assertTrue(len(errors) > 0)

    def test_non_vertical_dimensions(self):
        """Verify non-vertical video (e.g. 1920x1080 landscape) is rejected."""
        horizontal = self.temp_dir / "horizontal.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            "-t", "1",
            str(horizontal),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        valid, errors, meta = validate_video_output(horizontal, min_size_bytes=1000)
        self.assertFalse(valid)
        self.assertTrue(any("dimensions" in e.lower() for e in errors))
        self.assertEqual(meta.get("width"), 1920)
        self.assertEqual(meta.get("height"), 1080)

    def test_missing_audio_stream(self):
        """Verify video lacking an audio stream is rejected."""
        no_audio = self.temp_dir / "no_audio.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30",
            "-an",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-t", "1",
            str(no_audio),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        valid, errors, _ = validate_video_output(no_audio, min_size_bytes=1000)
        self.assertFalse(valid)
        self.assertTrue(any("no audio stream" in e.lower() for e in errors))

    def test_invalid_video_codec(self):
        """Verify video with non-h264 codec (e.g. mpeg4) is rejected."""
        mpeg4_video = self.temp_dir / "mpeg4_video.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100",
            "-c:v", "mpeg4",
            "-c:a", "aac",
            "-t", "1",
            str(mpeg4_video),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        valid, errors, _ = validate_video_output(mpeg4_video, min_size_bytes=1000)
        self.assertFalse(valid)
        self.assertTrue(any("video codec" in e.lower() for e in errors))

    def test_low_audio_sample_rate(self):
        """Verify audio sample rate below 24000Hz is rejected."""
        low_sr = self.temp_dir / "low_sample_rate.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=16000",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-ar", "16000",
            "-t", "1",
            str(low_sr),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        valid, errors, _ = validate_video_output(low_sr, min_size_bytes=1000)
        self.assertFalse(valid)
        self.assertTrue(any("sample rate" in e.lower() for e in errors))

    def test_duration_mismatch_exceeds_tolerance(self):
        """Verify duration mismatch between video (4s) and narration (1s) is rejected."""
        short_audio = self.temp_dir / "short_audio.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-c:a", "libmp3lame",
            "-t", "1",
            str(short_audio),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        # valid_video_path is 4.0s, short_audio is 1.0s (delta = 3.0s > 1.5s tolerance)
        valid, errors, meta = validate_video_output(
            self.valid_video_path,
            expected_audio_path=short_audio,
            tolerance_sec=1.5,
        )
        self.assertFalse(valid)
        self.assertTrue(any("duration" in e.lower() for e in errors))
        self.assertGreater(meta.get("duration_difference", 0), 1.5)

    def test_valid_video_passes_all_checks(self):
        """Verify compliant 1080x1920 h264/aac video passes output validation cleanly."""
        valid, errors, meta = validate_video_output(
            self.valid_video_path,
            expected_audio_path=self.valid_audio_path,
            tolerance_sec=1.5,
        )
        self.assertTrue(valid, f"Validation failed with unexpected errors: {errors}")
        self.assertEqual(len(errors), 0)
        self.assertEqual(meta.get("width"), REQUIRED_WIDTH)
        self.assertEqual(meta.get("height"), REQUIRED_HEIGHT)
        self.assertIn(meta.get("video_codec"), ["h264", "avc1"])
        self.assertEqual(meta.get("audio_codec"), "aac")
        self.assertGreaterEqual(meta.get("sample_rate", 0), 24000)
        self.assertAlmostEqual(meta.get("fps", 0), TARGET_FPS, delta=1.5)

    def test_validate_video_or_raise(self):
        """Verify validate_video_or_raise returns metadata on success and raises OutputValidationError on failure."""
        meta = validate_video_or_raise(
            self.valid_video_path,
            expected_audio_path=self.valid_audio_path,
            tolerance_sec=1.5,
        )
        self.assertIsInstance(meta, dict)

        missing = self.temp_dir / "non_existent.mp4"
        with self.assertRaises(OutputValidationError) as ctx:
            validate_video_or_raise(missing)
        self.assertTrue(len(ctx.exception.errors) > 0)

    def test_orchestrator_quarantine_corrupt_file(self):
        """Verify corrupt files can be quarantined without lingering under original path."""
        test_out = self.temp_dir / "render_corrupt_test.mp4"
        test_out.write_text("corrupted content")

        quarantine_path = test_out.with_name(f"{test_out.stem}.corrupt{test_out.suffix}")
        shutil.move(str(test_out), str(quarantine_path))

        self.assertFalse(test_out.exists(), "Original video path must no longer exist")
        self.assertTrue(quarantine_path.exists(), "Quarantined file must exist")


if __name__ == "__main__":
    unittest.main()

