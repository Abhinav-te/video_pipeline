"""
engine/audio/scene_audio.py

Per-Scene Audio Synthesis & Master Audio Recomposition (Checkpoint 02).
- Isolated scene audio synthesis: scenes/<scene_id>/audio_v<N>.mp3
- Whisper word timestamps per scene: (0.0s to scene_duration)
- Fast deterministic concatenation into master audio.mp3
- Accurate cumulative scene offset and global word timestamp calculation.
"""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union

REPO_DIR = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from engine.audio.tts_whisper import generate_voice, extract_word_timings, sanitize_spoken_narration, master_audio
from engine.timeline.beats import align_script_tokens_to_whisper


def get_audio_duration(audio_path: Union[str, Path]) -> float:
    """Returns duration of an audio file in seconds via ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration:stream=duration",
        "-of", "json",
        str(audio_path),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        meta = json.loads(res.stdout)
        dur = meta.get("format", {}).get("duration")
        if dur:
            return float(dur)
        streams = meta.get("streams", [])
        if streams and streams[0].get("duration"):
            return float(streams[0]["duration"])
        return 0.0
    except Exception:
        return 0.0


async def synthesize_scene_audio_async(
    narration_text: str,
    scene_dir: Path,
    revision: int = 1,
    voice_id: str = "en-US-AndrewNeural",
) -> Tuple[Path, float, List[Dict[str, Any]]]:
    """
    Synthesizes audio for a single scene and extracts Whisper word timestamps.
    Returns (audio_path, duration, words_relative_to_0).
    """
    scene_dir = Path(scene_dir)
    scene_dir.mkdir(parents=True, exist_ok=True)
    audio_path = scene_dir / f"audio_v{revision}.mp3"

    raw_text = (narration_text or "").strip()
    text = raw_text if raw_text else "Next concept."

    await generate_voice(text, str(audio_path), voice=voice_id)

    dur = get_audio_duration(audio_path)
    if dur <= 0.0:
        dur = max(2.5, len(text.split()) * 0.35)

    words: List[Dict[str, Any]] = []
    try:
        raw_words = extract_word_timings(str(audio_path))
        words = align_script_tokens_to_whisper(text, raw_words)
    except Exception as exc:
        print(f"[AUDIO:WARN] Scene Whisper extraction fallback: {exc}", file=sys.stderr)
        # Synthetic evenly distributed timestamps fallback
        tokens = text.split()
        if tokens:
            step = dur / len(tokens)
            for idx, tok in enumerate(tokens):
                words.append({
                    "word": tok,
                    "start": round(idx * step, 3),
                    "end": round((idx + 1) * step, 3),
                })

    return audio_path, dur, words


def synthesize_scene_audio(
    narration_text: str,
    scene_dir: Path,
    revision: int = 1,
    voice_id: str = "en-US-AndrewNeural",
) -> Tuple[Path, float, List[Dict[str, Any]]]:
    """Synchronous wrapper for synthesize_scene_audio_async."""
    return asyncio.run(
        synthesize_scene_audio_async(
            narration_text=narration_text,
            scene_dir=scene_dir,
            revision=revision,
            voice_id=voice_id,
        )
    )


def concatenate_scene_audios(
    scene_items: List[Dict[str, Any]],
    output_master_audio: Path,
    min_scene_duration: float = 2.5,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Concatenates per-scene audio files into master audio.mp3 using FFmpeg concat.
    Computes cumulative scene start/end offsets and global word timestamps.

    scene_items: list of dicts with:
      - scene_id: int
      - audio_path: Path
      - duration: float (optional, will probe if omitted)
      - words: list of word dicts (relative to 0.0)

    Returns (updated_scenes_meta, master_words).
    """
    output_master_audio = Path(output_master_audio).resolve()
    output_master_audio.parent.mkdir(parents=True, exist_ok=True)

    if not scene_items:
        raise ValueError("Cannot concatenate empty scene audio list.")

    # Write concat demuxer list
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for item in scene_items:
            p = Path(item["audio_path"]).resolve()
            f.write(f"file '{p.as_posix()}'\n")
        concat_list_path = Path(f.name)

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c:a", "libmp3lame",
        "-ar", "48000",
        "-ac", "2",
        "-b:a", "192k",
        str(output_master_audio),
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        master_audio(output_master_audio)
    finally:
        if concat_list_path.exists():
            concat_list_path.unlink(missing_ok=True)

    # Compute deterministic cumulative offsets
    current_time = 0.0
    master_words: List[Dict[str, Any]] = []
    updated_scenes: List[Dict[str, Any]] = []

    master_dur = get_audio_duration(output_master_audio)

    for idx, item in enumerate(scene_items):
        scene_id = item["scene_id"]
        a_path = Path(item["audio_path"])
        dur = float(item.get("duration", 0.0))
        if dur <= 0.0:
            dur = get_audio_duration(a_path)
        dur = max(min_scene_duration, dur)

        start_time = round(current_time, 3)
        end_time = round(start_time + dur, 3)

        scene_words = item.get("words", [])
        for w in scene_words:
            w_start = round(start_time + float(w.get("start", 0.0)), 3)
            w_end = round(start_time + float(w.get("end", 0.0)), 3)
            master_words.append({
                "word": w.get("word", ""),
                "start": w_start,
                "end": max(w_start + 0.05, w_end),
            })

        updated_scenes.append({
            "scene_id": scene_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": dur,
            "audio_file": str(a_path),
        })

        current_time = end_time

    # Mandatory Tail Padding: Ensure total video duration includes >= +0.4s past master audio
    if updated_scenes:
        total_vid = updated_scenes[-1]["end_time"]
        if total_vid < master_dur + 0.4:
            deficit = round((master_dur + 0.4) - total_vid, 3)
            updated_scenes[-1]["duration"] = round(updated_scenes[-1]["duration"] + deficit, 3)
            updated_scenes[-1]["end_time"] = round(updated_scenes[-1]["start_time"] + updated_scenes[-1]["duration"], 3)

    return updated_scenes, master_words

