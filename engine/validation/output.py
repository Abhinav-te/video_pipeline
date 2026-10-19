import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

VALID_CONTAINER_TOKENS = {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"}
REQUIRED_WIDTH = 1080
REQUIRED_HEIGHT = 1920
TARGET_FPS = 30.0
FPS_TOLERANCE = 1.5  # Allowed framerate variance [28.5, 31.5]
DEFAULT_DURATION_TOLERANCE_SEC = 1.5  # +/- 1.5s (approx 45 frames at 30fps)
DEFAULT_MIN_SIZE_BYTES = 100 * 1024  # 100 KB
VALID_VIDEO_CODECS = {"h264", "avc1"}
VALID_AUDIO_CODECS = {"aac", "mp3"}
MIN_AUDIO_SAMPLE_RATE = 24000


class OutputValidationError(Exception):
    """Raised when rendered video fails post-render output validation."""

    def __init__(self, errors: List[str], metadata: Optional[Dict[str, Any]] = None):
        self.errors = errors
        self.metadata = metadata or {}
        super().__init__("; ".join(errors))


def _parse_fps(rate_str: Optional[str]) -> Optional[float]:
    """Parses ffprobe framerate string (e.g. '30/1', '29.97', '30000/1001') to float."""
    if not rate_str:
        return None
    try:
        if "/" in rate_str:
            num, den = rate_str.split("/", 1)
            den_f = float(den)
            if den_f == 0.0:
                return None
            return float(num) / den_f
        return float(rate_str)
    except (ValueError, TypeError):
        return None


def get_media_duration(media_path: Union[str, Path]) -> Optional[float]:
    """Inspects a media file using ffprobe and returns duration in seconds, or None."""
    path = Path(media_path)
    if not path.exists() or path.stat().st_size == 0:
        return None

    if not shutil.which("ffprobe"):
        return None

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        dur_val = data.get("format", {}).get("duration")
        if dur_val:
            return float(dur_val)
    except Exception:
        pass
    return None


def inspect_video_file(video_path: Union[str, Path]) -> Tuple[Dict[str, Any], Optional[str]]:
    """Runs ffprobe on the video file and returns raw parsed dictionary and error string if any."""
    path = Path(video_path)
    if not shutil.which("ffprobe"):
        return {}, "ffprobe executable not found in PATH."

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,duration",
        "-show_entries", "format=format_name,duration,size",
        "-of", "json",
        str(path),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        return data, None
    except subprocess.CalledProcessError as exc:
        err_msg = exc.stderr.strip() if exc.stderr else f"ffprobe exited with code {exc.returncode}"
        return {}, f"ffprobe error inspecting video: {err_msg}"
    except Exception as exc:
        return {}, f"Failed to execute ffprobe: {exc}"


def validate_video_output(
    video_path: Union[str, Path],
    expected_audio_path: Optional[Union[str, Path]] = None,
    expected_duration: Optional[float] = None,
    tolerance_sec: float = DEFAULT_DURATION_TOLERANCE_SEC,
    min_size_bytes: int = DEFAULT_MIN_SIZE_BYTES,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates a post-render video file against Remotion specifications.

    Checks:
    - File exists and is >= min_size_bytes.
    - Container format is a valid MP4 (mov,mp4,m4a,3gp,3g2,mj2).
    - Exactly 1 video stream with codec h264, 1080x1920 (9:16 vertical), and ~30 fps.
    - Exactly 1 audio stream with codec aac or mp3 and sample rate >= 24000Hz.
    - Video duration matches expected audio/narration duration within tolerance_sec.

    Returns:
    (is_valid: bool, errors: List[str], metadata: Dict[str, Any])
    """
    errors: List[str] = []
    metadata: Dict[str, Any] = {}

    path = Path(video_path)

    # 1. File existence & basic size check
    if not path.exists():
        errors.append(f"Output video file does not exist: {video_path}")
        return False, errors, metadata

    if not path.is_file():
        errors.append(f"Output video path is not a regular file: {video_path}")
        return False, errors, metadata

    file_size = path.stat().st_size
    metadata["file_size"] = file_size

    if file_size == 0:
        errors.append(f"Output video file is 0 bytes: {video_path}")
        return False, errors, metadata

    if file_size < min_size_bytes:
        errors.append(
            f"Output video file is too small ({file_size:,} bytes). "
            f"Expected at least {min_size_bytes:,} bytes ({min_size_bytes // 1024} KB)."
        )

    # 2. Run ffprobe inspection
    data, probe_err = inspect_video_file(path)
    if probe_err:
        errors.append(probe_err)
        return False, errors, metadata

    # 3. Container format check
    format_data = data.get("format", {})
    format_name = format_data.get("format_name", "").lower()
    metadata["format_name"] = format_name

    format_tokens = set(format_name.split(","))
    if not (format_tokens & VALID_CONTAINER_TOKENS or "mp4" in format_name):
        errors.append(
            f"Invalid container format: '{format_name}'. "
            f"Expected an MP4 container (matching {sorted(VALID_CONTAINER_TOKENS)})."
        )

    # 4. Stream separation
    streams = data.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    metadata["video_stream_count"] = len(video_streams)
    metadata["audio_stream_count"] = len(audio_streams)

    # 5. Video stream verification
    if len(video_streams) == 0:
        errors.append("No video stream found in rendered output.")
    elif len(video_streams) > 1:
        errors.append(f"Expected exactly 1 video stream, but found {len(video_streams)}.")
    else:
        v_stream = video_streams[0]
        v_codec = v_stream.get("codec_name", "").lower()
        metadata["video_codec"] = v_codec
        if v_codec not in VALID_VIDEO_CODECS:
            errors.append(
                f"Invalid video codec: '{v_codec}'. Expected one of {sorted(VALID_VIDEO_CODECS)}."
            )

        width = v_stream.get("width")
        height = v_stream.get("height")
        metadata["width"] = width
        metadata["height"] = height
        if width != REQUIRED_WIDTH or height != REQUIRED_HEIGHT:
            errors.append(
                f"Invalid video dimensions: {width}x{height}. "
                f"Expected {REQUIRED_WIDTH}x{REQUIRED_HEIGHT} (9:16 vertical short)."
            )

        r_fps = _parse_fps(v_stream.get("r_frame_rate"))
        avg_fps = _parse_fps(v_stream.get("avg_frame_rate"))
        if r_fps is not None and (TARGET_FPS - FPS_TOLERANCE) <= r_fps <= (TARGET_FPS + FPS_TOLERANCE):
            fps = r_fps
        else:
            fps = avg_fps or r_fps
        metadata["fps"] = fps
        if fps is None or not ((TARGET_FPS - FPS_TOLERANCE) <= fps <= (TARGET_FPS + FPS_TOLERANCE)):
            fps_display = f"{fps:.2f}" if fps is not None else "None"
            errors.append(
                f"Invalid framerate: {fps_display} fps. "
                f"Expected ~{int(TARGET_FPS)} fps (tolerance: {TARGET_FPS - FPS_TOLERANCE}-{TARGET_FPS + FPS_TOLERANCE} fps)."
            )

    # 6. Audio stream verification
    if len(audio_streams) == 0:
        errors.append("No audio stream found in rendered output.")
    elif len(audio_streams) > 1:
        errors.append(f"Expected exactly 1 audio stream, but found {len(audio_streams)}.")
    else:
        a_stream = audio_streams[0]
        a_codec = a_stream.get("codec_name", "").lower()
        metadata["audio_codec"] = a_codec
        if a_codec not in VALID_AUDIO_CODECS:
            errors.append(
                f"Invalid audio codec: '{a_codec}'. Expected one of {sorted(VALID_AUDIO_CODECS)}."
            )

        try:
            sample_rate = int(a_stream.get("sample_rate", 0))
        except (ValueError, TypeError):
            sample_rate = 0
        metadata["sample_rate"] = sample_rate

        if sample_rate < MIN_AUDIO_SAMPLE_RATE:
            errors.append(
                f"Audio sample rate {sample_rate}Hz is below minimum requirement of {MIN_AUDIO_SAMPLE_RATE}Hz."
            )

    # 7. Duration verification
    v_dur_raw = format_data.get("duration") or (video_streams[0].get("duration") if video_streams else None)
    video_dur: Optional[float] = None
    if v_dur_raw:
        try:
            video_dur = float(v_dur_raw)
        except (ValueError, TypeError):
            pass

    metadata["video_duration"] = video_dur

    if video_dur is None or video_dur <= 0.0:
        errors.append("Video duration is 0 or unreadable.")

    # Determine reference audio narration duration
    target_audio_duration = expected_duration
    if target_audio_duration is None and expected_audio_path is not None:
        audio_ref_path = Path(expected_audio_path)
        if not audio_ref_path.exists():
            errors.append(f"Expected audio reference file does not exist: {expected_audio_path}")
        else:
            target_audio_duration = get_media_duration(audio_ref_path)
            if target_audio_duration is None:
                errors.append(f"Could not read duration from reference audio: {expected_audio_path}")

    metadata["expected_duration"] = target_audio_duration

    if video_dur is not None and target_audio_duration is not None and target_audio_duration > 0.0:
        diff = abs(video_dur - target_audio_duration)
        metadata["duration_difference"] = round(diff, 3)
        if diff > tolerance_sec:
            errors.append(
                f"Video duration ({video_dur:.2f}s) differs from reference narration duration "
                f"({target_audio_duration:.2f}s) by {diff:.2f}s (tolerance: +/-{tolerance_sec:.2f}s / ~45 frames)."
            )

    is_valid = len(errors) == 0
    return is_valid, errors, metadata


def validate_video_or_raise(
    video_path: Union[str, Path],
    expected_audio_path: Optional[Union[str, Path]] = None,
    expected_duration: Optional[float] = None,
    tolerance_sec: float = DEFAULT_DURATION_TOLERANCE_SEC,
    min_size_bytes: int = DEFAULT_MIN_SIZE_BYTES,
) -> Dict[str, Any]:
    """Validates video output and raises OutputValidationError on any failure."""
    is_valid, errors, metadata = validate_video_output(
        video_path=video_path,
        expected_audio_path=expected_audio_path,
        expected_duration=expected_duration,
        tolerance_sec=tolerance_sec,
        min_size_bytes=min_size_bytes,
    )
    if not is_valid:
        raise OutputValidationError(errors, metadata)
    return metadata

