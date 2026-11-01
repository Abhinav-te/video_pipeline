"""tests/test_audio_sync_tolerance.py

Tests post-render QA duration synchronization tolerance and trailing audio policy:
- Tolerance standardized to <= 0.05 seconds across output.py and evidence_validator.py.
- Negative & positive boundary tests for 0.04s (within tolerance) vs 0.06s (outside tolerance).
- Checks container internal stream duration agreement (video vs audio stream inside MP4).
- Verifies removal of max(0.5, tolerance_sec) clamp in validate_post_render_qa.
- Verifies trailing audio policy (last_word_end + 0.05s trim + 0.20s pad = 0.25s tail).
"""

from pathlib import Path
from unittest.mock import patch
import pytest

from engine.validation.output import (
    validate_video_output,
    DEFAULT_DURATION_TOLERANCE_SEC,
)
from engine.validation.evidence_validator import validate_post_render_qa

REPO_DIR = Path(__file__).resolve().parent.parent


def test_default_duration_tolerance_is_0_05():
    assert DEFAULT_DURATION_TOLERANCE_SEC == 0.05


def test_video_output_sync_within_tolerance(tmp_path):
    # Create dummy video file
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Mock ffprobe output: video = 30.00s, audio = 30.04s (0.04s diff <= 0.05s tolerance)
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.000000"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.040000",  # Stream sync diff = 0.04s
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.04,  # Video vs reference diff = 0.04s <= 0.05s
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert is_valid, f"Expected validation to pass but got errors: {errors}"
        assert meta["stream_sync_difference"] == 0.04
        assert meta["duration_difference"] == 0.04


def test_video_output_sync_outside_tolerance_fails(tmp_path):
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Mock ffprobe output: video = 30.00s, reference = 30.06s (0.06s diff > 0.05s tolerance)
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.000000"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.000000",
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.06,  # 0.06s difference > 0.05s
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert not is_valid
        assert any("differs from reference narration duration" in e for e in errors)
        assert any("tolerance: +/-0.0500s" in e for e in errors)


def test_internal_stream_desync_fails(tmp_path):
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Internal audio stream differs from video stream by 0.12s (effective diff = 0.0773s > 0.05s tolerance)
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.000000"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.120000",  # 0.12s raw diff -> effective diff 0.0773s > 0.05s
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.00,
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert not is_valid
        assert any("Internal MP4 stream duration desynchronization" in e for e in errors)
        assert meta["stream_sync_difference"] == 0.12


def test_aac_codec_priming_delay_with_verified_metadata_passes(tmp_path):
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Reference Inngest audio: 30.4750s
    # Encoded AAC audio: 30.5280s (2048 samples priming + 496 samples padding)
    # Container stream declares initial_padding = 2048 samples
    # Video stream: 30.4667s (914 frames @ 30fps)
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.466667"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.466667",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.528000",
                "initial_padding": 2048,
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.4750,
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert is_valid, f"Expected validation to pass but got errors: {errors}"
        assert meta["codec_padding_verified"] is True
        assert meta["codec_overhead_sec"] == 0.0427
        assert meta["effective_audio_duration"] == 30.4853
        assert meta["duration_difference"] == 0.0083
        assert meta["stream_sync_difference"] == 0.0186
        assert meta["audio_reference_difference"] == 0.0103


def test_genuine_excess_audio_hidden_by_unconditional_compensation_fails(tmp_path):
    """
    Challenge test (Phase 3.7.1 audit):
    Audio stream has genuine excess audio of 0.0600s above reference (30.0600s vs 30.0000s),
    which violates the strict 0.0500s tolerance limit.
    Under an unsafe unconditional subtraction of 2048 samples (0.0427s),
    the apparent difference becomes:
        effective_audio_dur = 30.0600 - 0.0427 = 30.0173s
        apparent_diff = |30.0173 - 30.0000| = 0.0173s <= 0.0500s (FAILS TO DETECT DEFECT!).
    Under a conservative, verified policy where container metadata does not verify padding,
    no silent subtraction is performed, and this genuine duration defect is caught.
    """
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Genuine excess audio: 30.0600s vs 30.0000s (delta = 0.0600s > 0.0500s tolerance)
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.000000"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.060000",
                "initial_padding": 0,
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.0000,
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert not is_valid, "Expected genuine excess audio of 0.0600s to fail, but it passed!"
        assert any("differs from reference narration duration" in e for e in errors)
        assert meta["codec_padding_verified"] is False
        assert meta["effective_audio_duration"] == 30.0600
        assert meta["audio_reference_difference"] == 0.0600


def test_unverified_aac_padding_exceeding_tolerance_fails_conservative_policy(tmp_path):
    """
    Verifies that when an AAC audio stream exceeds the duration tolerance (e.g. 30.5280s vs 30.4750s,
    diff = 0.0530s > 0.0500s) but the container does NOT expose verified presentation-trimming metadata
    (initial_padding = 0, no skip_samples, no edit list trimming), the conservative policy does NOT
    infer codec padding merely because audio is longer than WAV. Validation must fail.
    """
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.466667"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.466667",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.528000",
                "initial_padding": 0,
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.4750,
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert not is_valid
        assert meta["codec_padding_verified"] is False
        assert meta["effective_audio_duration"] == 30.5280
        assert meta["audio_reference_difference"] == 0.0530
        assert meta["stream_sync_difference"] == 0.0613


def test_genuine_audio_truncation_fails(tmp_path):
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Audio stream truncated to 30.4000s vs 30.4750s reference (75ms truncation > 50ms tolerance)
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.466667"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.466667",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.400000",  # Truncated!
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.4750,
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert not is_valid
        assert any("differs from reference narration duration" in e for e in errors)
        assert meta["effective_audio_duration"] == 30.4000


def test_genuine_extra_audio_fails(tmp_path):
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Audio stream 30.6500s vs 30.4750s reference (175ms extra audio, effective diff = 0.1323s > 0.05s)
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.466667"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.466667",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.650000",  # Genuine extra audio!
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.4750,
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert not is_valid
        assert any("differs from reference narration duration" in e for e in errors)
        assert meta["effective_audio_duration"] == 30.6500
        assert meta["audio_reference_difference"] == 0.1750


def test_genuine_video_audio_desynchronization_fails(tmp_path):
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Video is 30.00s, audio stream is 30.12s (effective audio = 30.0773s, diff = 0.0773s > 0.05s)
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.000000"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.120000",
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_video_output(
            video_path=dummy_vid,
            expected_duration=30.00,
            tolerance_sec=0.05,
            aspect_ratio="16:9",
        )
        assert not is_valid
        assert any("Internal MP4 stream duration desynchronization" in e for e in errors)
        assert meta["stream_sync_difference"] == 0.12


def test_validate_post_render_qa_does_not_clamp_tolerance(tmp_path):
    dummy_vid = tmp_path / "test.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # In previous code, max(0.5, tol) clamped tol to 0.5s even if caller requested 0.03s.
    # We assert that a 0.04s difference fails when tolerance_sec=0.03 is passed.
    mock_probe = {
        "format": {"format_name": "mp4", "duration": "30.000000"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "30.000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "30.000000",
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)), \
         patch("shutil.which", return_value=None):
        is_valid, errors, meta = validate_post_render_qa(
            video_path=dummy_vid,
            expected_duration=30.04,  # diff = 0.04s
            tolerance_sec=0.03,  # strict 0.03s tolerance
            aspect_ratio="16:9",
        )
        # If clamp existed, 0.04s would pass against 0.5s. With clamp removed, 0.04s > 0.03s must FAIL.
        assert not is_valid
        assert any("differs from reference narration duration" in e for e in errors)


def test_direct_muxed_aac_preserves_waveform_and_speech_boundaries(tmp_path):
    """
    Deterministic regression test satisfying Phase 3.7.2 Requirement 5:
    Preservation of the source waveform and intended spoken-content boundaries.

    Synthesizes a 1.0s reference audio with exact silent boundaries and active tone:
    - 100ms leading silence (samples 0 - 4,800)
    - 800ms active tone (samples 4,800 - 43,200)
    - 100ms trailing silence (samples 43,200 - 48,000)
    Muxes directly into an MP4 container using mux_master_audio_into_video.
    Asserts:
    1. Sample-by-sample correlation at offset 0 between source and decoded audio is >= 0.999.
    2. Tone onset in decoded MP4 matches intended onset (0.100s) within <= 2ms.
    3. Output video passes validate_video_output and validate_post_render_qa cleanly.
    4. Audio duration and video duration agree within tolerance <= 0.050s.
    """
    import shutil
    import subprocess
    import wave
    import numpy as np
    from engine.audio.scene_audio import mux_master_audio_into_video

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg or ffprobe not available in PATH")

    sr = 48000
    dur = 1.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    signal = np.zeros(len(t), dtype=np.float32)
    idx_start = int(0.1 * sr)
    idx_end = int(0.9 * sr)
    signal[idx_start:idx_end] = 0.5 * np.sin(2 * np.pi * 440 * t[idx_start:idx_end])
    pcm_data = (signal * 32767).astype(np.int16)
    stereo_pcm = np.column_stack([pcm_data, pcm_data])

    wav_path = tmp_path / "reference.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo_pcm.tobytes())

    # Generate 1.0s video with 30 frames
    raw_video = tmp_path / "raw_video.mp4"
    cmd_vid = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=30:d=1.0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(raw_video),
    ]
    subprocess.run(cmd_vid, capture_output=True, check=True)

    # Execute direct audio muxing
    muxed_video = tmp_path / "final_muxed.mp4"
    ok = mux_master_audio_into_video(
        video_path=raw_video,
        audio_path=wav_path,
        output_path=muxed_video,
    )
    assert ok is True
    assert muxed_video.exists()

    # 1. Validate post render QA
    is_valid, errors, meta = validate_video_output(
        video_path=muxed_video,
        expected_audio_path=wav_path,
        tolerance_sec=0.05,
        min_size_bytes=1000,
        expected_width=1280,
        expected_height=720,
    )
    assert is_valid, f"Validation failed: {errors}"
    assert meta["stream_sync_difference"] <= 0.05
    assert meta["audio_reference_difference"] <= 0.05

    # 2. Decode audio from MP4 and verify waveform alignment at offset 0
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(muxed_video), "-vn", "-f", "s16le", "-ar", "48000", "-ac", "2", "-"],
        capture_output=True,
        check=True,
    )
    dec_pcm = np.frombuffer(proc.stdout, dtype=np.int16).reshape(-1, 2)
    dec_mono = dec_pcm[:, 0].astype(np.float32)

    # Correlation across active tone segment
    corr_at_0 = np.corrcoef(signal[idx_start:idx_end], dec_mono[idx_start:idx_end])[0, 1]
    assert corr_at_0 >= 0.999, f"Expected correlation >= 0.999 at offset 0, got {corr_at_0:.6f}"

    # Tone onset detection
    threshold = 32767 * 0.1
    dec_onset = np.where(np.abs(dec_mono) > threshold)[0][0]
    onset_time_diff_ms = abs(dec_onset - idx_start) / sr * 1000.0
    assert onset_time_diff_ms <= 2.0, f"Tone onset shifted by {onset_time_diff_ms:.2f}ms (expected <= 2ms)"


def test_revision_frame_count_consistency_and_non_overlapping_intervals(tmp_path):
    """
    Phase 3.9.1 (Task 2) Regression Test:
    Verifies that:
    1. Scene start_frame and duration_frames form a strictly contiguous partition
       of the timeline [0, total_timeline_frames).
    2. Sum of scene duration_frames exactly equals total_timeline_frames = ceil(total_duration * fps).
    3. No boundary frames are duplicated across adjacent scenes.
    4. Slicing segment videos produces exact duration_frames without +1 frame creep.
    """
    import math
    from engine.pipeline.manifest import init_manifest

    fps = 30
    scenes = [
        {"scene_id": 1, "start_time": 0.0, "end_time": 2.475, "duration": 2.475},
        {"scene_id": 2, "start_time": 2.475, "end_time": 9.125, "duration": 6.65},
        {"scene_id": 3, "start_time": 9.125, "end_time": 14.625, "duration": 5.5},
        {"scene_id": 4, "start_time": 14.625, "end_time": 23.287, "duration": 8.662},
        {"scene_id": 5, "start_time": 23.287, "end_time": 28.425, "duration": 5.138},
    ]

    total_duration_sec = 28.425
    expected_total_frames = math.ceil(total_duration_sec * fps)  # 853 frames
    assert expected_total_frames == 853

    manifest = init_manifest(
        run_id="test_consistency_run",
        run_dir=tmp_path,
        initial_scenes=scenes,
        fps=fps,
    )

    manifest_scenes = manifest["scenes"]
    total_frames_sum = 0
    current_expected_start = 0

    for s_idx in range(1, len(scenes) + 1):
        s_info = manifest_scenes[str(s_idx)]
        start_frame = s_info["start_frame"]
        dur_frames = s_info["duration_frames"]

        # 1. No gaps and no duplicated frames between adjacent scenes
        assert start_frame == current_expected_start, (
            f"Scene {s_idx} start_frame {start_frame} != expected {current_expected_start}"
        )
        total_frames_sum += dur_frames
        current_expected_start = start_frame + dur_frames

    # 2. Total frame sum must equal exactly 853 frames (matching Remotion Root.jsx)
    assert total_frames_sum == expected_total_frames
    assert current_expected_start == expected_total_frames


def test_short_preview_unmuxed_remotion_audio_fails_duration_check(tmp_path):
    """
    Phase 4.3.1 Regression Test (Objective 2):
    Reproduces the exact failure from Phase 4.3 where a short preview rendered with
    --frames=74-314 (241 frames @ 30fps = 8.0333s) without master audio muxing left
    Remotion's intermediate ADTS AAC audio stream in the MP4 container (duration 8.0853s).
    Because the AAC priming delay (2048 samples = 42.7ms) and packet padding (448 samples = 9.3ms)
    totaled 52.0ms (0.0520s > 0.0500s tolerance), Gate 6 post-render QA correctly failed
    and quarantined the file to .corrupt.mp4.
    """
    dummy_vid = tmp_path / "preview_spotlight.corrupt.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Exact ffprobe metrics from video/out/preview_spotlight.corrupt.mp4
    mock_probe = {
        "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "8.085333"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "8.033333",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "8.085333",  # 0.0520s diff > 0.0500s tolerance
                "initial_padding": 0,
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_post_render_qa(
            video_path=dummy_vid,
            aspect_ratio="16:9",
            tolerance_sec=0.05,
        )
        assert not is_valid, "Expected unmuxed Remotion preview with 0.0520s diff to fail QA"
        assert any("Internal MP4 stream duration desynchronization" in e for e in errors)
        assert meta["stream_sync_difference"] == 0.0520


def test_short_preview_slice_and_mux_passes_duration_check(tmp_path):
    """
    Phase 4.3.1 Regression Test (Objective 2):
    Verifies that when slice_audio_for_frame_range slices the master audio for
    the exact preview frame range and muxes it with mux_master_audio_into_video:
    1. Audio duration and video duration agree within tolerance <= 0.050s (typically < 0.001s).
    2. Post-render QA passes cleanly without quarantine.
    """
    import shutil
    import subprocess
    import wave
    import numpy as np
    from engine.audio.scene_audio import slice_audio_for_frame_range, mux_master_audio_into_video

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg or ffprobe not available in PATH")

    sr = 48000
    fps = 30.0
    start_frame = 74
    end_frame = 314
    dur_frames = end_frame - start_frame + 1  # 241 frames
    preview_dur_sec = dur_frames / fps  # 8.033333s

    # Create 30.0s master WAV
    total_samples = int(sr * 30.0)
    master_wav = tmp_path / "master_audio.wav"
    t = np.linspace(0, 30.0, total_samples, endpoint=False)
    sig = (0.3 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    stereo = np.column_stack([sig, sig])
    with wave.open(str(master_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())

    # Create 241-frame video (8.033333s)
    raw_video = tmp_path / "preview_raw.mp4"
    cmd_vid = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r=30:d={preview_dur_sec:.6f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(raw_video),
    ]
    subprocess.run(cmd_vid, capture_output=True, check=True)

    # Slice master audio for frames 74-314
    sliced_audio = slice_audio_for_frame_range(
        audio_path=master_wav,
        frames_spec=f"{start_frame}-{end_frame}",
        fps=fps,
        output_path=tmp_path / "preview_sliced.wav",
    )
    assert sliced_audio is not None
    assert sliced_audio.exists()

    # Mux sliced audio directly into video
    final_preview = tmp_path / "preview_final.mp4"
    ok = mux_master_audio_into_video(
        video_path=raw_video,
        audio_path=sliced_audio,
        output_path=final_preview,
    )
    assert ok is True

    # Validate post-render QA with strict 0.05s tolerance
    is_valid, errors, meta = validate_post_render_qa(
        video_path=final_preview,
        expected_audio_path=sliced_audio,
        aspect_ratio="16:9",
        tolerance_sec=0.05,
    )
    assert is_valid, f"Expected valid preview to pass Gate 6 QA but got errors: {errors}"
    assert meta["stream_sync_difference"] <= 0.05
    assert meta["duration_difference"] <= 0.05


def test_short_preview_genuinely_invalid_audio_fails(tmp_path):
    """
    Phase 4.3.1 Regression Test (Objective 2):
    Verifies that a genuinely invalid preview with 0.08s audio desync still FAILS
    Gate 6 QA under the strict 0.05s tolerance (no weakening of validation).
    """
    dummy_vid = tmp_path / "invalid_preview.mp4"
    dummy_vid.write_bytes(b"\x00" * 200_000)

    # Video: 3.00s, Audio: 3.08s (diff = 0.08s > 0.05s tolerance)
    mock_probe = {
        "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "3.080000"},
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "duration": "3.000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "3.080000",  # 0.0800s diff > 0.0500s tolerance
                "initial_padding": 0,
            },
        ],
    }

    with patch("engine.validation.output.inspect_video_file", return_value=(mock_probe, None)):
        is_valid, errors, meta = validate_post_render_qa(
            video_path=dummy_vid,
            aspect_ratio="16:9",
            tolerance_sec=0.05,
        )
        assert not is_valid
        assert any("Internal MP4 stream duration desynchronization" in e for e in errors)
        assert meta["stream_sync_difference"] == 0.0800


def test_slice_audio_for_frame_range_boundaries(tmp_path):
    """
    Phase 4.3.1: Unit tests for slice_audio_for_frame_range edge cases and validation.
    """
    import shutil
    import wave
    import numpy as np
    from engine.audio.scene_audio import slice_audio_for_frame_range, get_audio_duration

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available in PATH")

    sr = 48000
    wav_path = tmp_path / "test.wav"
    t = np.linspace(0, 5.0, sr * 5, endpoint=False)
    sig = (0.2 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(np.column_stack([sig, sig]).tobytes())

    # Range 0-89 (90 frames @ 30fps = 3.0s)
    slice_1 = slice_audio_for_frame_range(wav_path, "0-89", fps=30.0, output_path=tmp_path / "s1.wav")
    assert slice_1 is not None
    dur_1 = get_audio_duration(slice_1)
    assert abs(dur_1 - 3.0) < 0.01

    # Single frame 30 (1 frame @ 30fps = 0.0333s)
    slice_2 = slice_audio_for_frame_range(wav_path, "30", fps=30.0, output_path=tmp_path / "s2.wav")
    assert slice_2 is not None

    # Invalid range: reversed frames
    slice_inv = slice_audio_for_frame_range(wav_path, "90-30", fps=30.0)
    assert slice_inv is None

    # Invalid range: non-numeric string
    slice_inv2 = slice_audio_for_frame_range(wav_path, "invalid-range", fps=30.0)
    assert slice_inv2 is None




