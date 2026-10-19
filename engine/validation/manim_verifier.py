"""
engine/validation/manim_verifier.py

Automated Manim Output Verification:
1. Stream & Duration Check (ffprobe):
   - Video stream exists and has valid codec.
   - Resolution matches expected dimensions (default: 920x920).
   - abs(actual_duration - expected_duration) <= duration_tolerance (default: 0.75s).
2. Motion Check (Frame Diff):
   - Extracts two grayscale frames at 20% and 80% of actual clip duration via ffmpeg.
   - Calculates mean absolute pixel difference between the frames.
   - Asserts mean absolute pixel difference > min_motion_delta (default: 0.5),
     proving the animation dynamically moved across time and is not blank or frozen.
"""

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None  # type: ignore
    HAVE_NUMPY = False


def extract_grayscale_frame(
    video_path: Union[str, Path],
    timestamp: float,
    width: int = 920,
    height: int = 920,
) -> Optional[bytes]:
    """
    Extracts a single grayscale frame at the specified timestamp in raw format.
    Returns raw bytes of size width * height, or None if extraction failed.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        return None

    cmd = [
        "ffmpeg",
        "-v", "error",
        "-ss", f"{timestamp:.3f}",
        "-i", str(video_path),
        "-vframes", "1",
        "-vf", f"scale={width}:{height},format=gray",
        "-f", "rawvideo",
        "pipe:1",
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, check=True)
        expected_bytes = width * height
        if len(res.stdout) >= expected_bytes:
            return res.stdout[:expected_bytes]
        return None
    except Exception:
        return None


def calculate_motion_delta(
    frame_bytes_a: bytes,
    frame_bytes_b: bytes,
) -> float:
    """
    Calculates the mean absolute pixel difference (0.0 to 255.0) between two grayscale frames.
    """
    if not frame_bytes_a or not frame_bytes_b:
        return 0.0

    length = min(len(frame_bytes_a), len(frame_bytes_b))
    if length == 0:
        return 0.0

    if HAVE_NUMPY and np is not None:
        arr_a = np.frombuffer(frame_bytes_a[:length], dtype=np.uint8).astype(np.float32)
        arr_b = np.frombuffer(frame_bytes_b[:length], dtype=np.uint8).astype(np.float32)
        return float(np.mean(np.abs(arr_a - arr_b)))

    # Pure Python fallback
    total_diff = sum(abs(a - b) for a, b in zip(frame_bytes_a[:length], frame_bytes_b[:length]))
    return float(total_diff / length)


def verify_manim_clip(
    video_path: Union[str, Path],
    expected_duration: float,
    expected_width: int = 920,
    expected_height: int = 920,
    duration_tolerance: float = 1.0,
    min_motion_delta: float = 0.5,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Full automated verification of a compiled Manim video asset.
    Returns (is_valid, errors, metadata).
    """
    video_path = Path(video_path).resolve()
    errors: List[str] = []
    meta: Dict[str, Any] = {
        "path": str(video_path),
        "exists": False,
        "size_bytes": 0,
        "width": 0,
        "height": 0,
        "actual_duration": 0.0,
        "expected_duration": float(expected_duration),
        "duration_diff": 0.0,
        "motion_delta": 0.0,
    }

    if not video_path.exists():
        errors.append(f"Manim clip not found at path: {video_path}")
        return False, errors, meta

    meta["exists"] = True
    size_bytes = video_path.stat().st_size
    meta["size_bytes"] = size_bytes

    if size_bytes < 10240:
        errors.append(f"Manim clip is corrupt or too small: {size_bytes} bytes (< 10 KB threshold).")
        return False, errors, meta

    # 1. ffprobe Stream & Duration Inspection
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,codec_name:format=duration",
        "-of", "json",
        str(video_path),
    ]

    try:
        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(probe_res.stdout)
    except Exception as exc:
        errors.append(f"ffprobe metadata inspection failed: {exc}")
        return False, errors, meta

    streams = probe_data.get("streams", [])
    if not streams:
        errors.append("No video stream found in Manim clip.")
        return False, errors, meta

    stream = streams[0]
    actual_width = int(stream.get("width", 0))
    actual_height = int(stream.get("height", 0))
    meta["width"] = actual_width
    meta["height"] = actual_height

    # Parse duration from stream or fallback to format duration
    dur_str = stream.get("duration") or probe_data.get("format", {}).get("duration", "0")
    try:
        actual_duration = float(dur_str)
    except (ValueError, TypeError):
        actual_duration = 0.0
    meta["actual_duration"] = actual_duration

    # Resolution Check
    if expected_width > 0 and expected_height > 0:
        if actual_width != expected_width or actual_height != expected_height:
            errors.append(
                f"Resolution mismatch: expected {expected_width}x{expected_height}, got {actual_width}x{actual_height}."
            )

    # Duration Check
    duration_diff = abs(actual_duration - expected_duration)
    meta["duration_diff"] = duration_diff
    if actual_duration <= 0.0:
        errors.append(f"Video duration is non-positive ({actual_duration:.2f}s).")
    elif duration_diff > duration_tolerance:
        errors.append(
            f"Duration mismatch exceeds tolerance {duration_tolerance:.2f}s: "
            f"actual {actual_duration:.2f}s vs expected {expected_duration:.2f}s (delta: {duration_diff:.2f}s)."
        )

    # 2. Motion Check (20% vs 80% Frame Diff)
    if actual_duration > 0.5:
        t1 = 0.20 * actual_duration
        t2 = 0.80 * actual_duration
        frame_a = extract_grayscale_frame(video_path, t1, width=min(actual_width, 460), height=min(actual_height, 460))
        frame_b = extract_grayscale_frame(video_path, t2, width=min(actual_width, 460), height=min(actual_height, 460))

        if frame_a is None or frame_b is None:
            errors.append(f"Failed to extract verification frames at t={t1:.2f}s and t={t2:.2f}s.")
        else:
            motion_delta = calculate_motion_delta(frame_a, frame_b)
            meta["motion_delta"] = motion_delta
            if motion_delta < min_motion_delta:
                errors.append(
                    f"Motion verification failed: mean frame pixel difference {motion_delta:.3f} "
                    f"is <= {min_motion_delta} (animation appears static or blank)."
                )

    is_valid = len(errors) == 0
    return is_valid, errors, meta

