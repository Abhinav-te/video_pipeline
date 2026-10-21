"""
engine/audio/scene_audio.py

Per-Scene Audio Synthesis & Master Audio Recomposition.
- Isolated scene audio synthesis: scenes/<scene_id>/audio_v<N>.wav (uncompressed PCM WAV, 48000Hz)
- Native Edge-TTS WordBoundary events with spoken-to-display code mapping
- Deterministic atrim (end=last_word_end + 0.15) + apad (pad_dur=0.25)
- Lossless PCM concatenation into master audio.wav & audio.mp3
- Single master loudnorm pass (I=-16, TP=-1.5, LRA=11)
- Microsecond-exact cumulative scene offsets and global word timestamps
"""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import wave
from typing import Any, Dict, List, Optional, Tuple, Union

REPO_DIR = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from engine.audio.tts_whisper import (
    synthesize_voice_with_boundaries,
    get_audio_duration_seconds,
)


def get_audio_duration(audio_path: Union[str, Path]) -> float:
    """Returns exact duration of an audio file in seconds via wave header or ffprobe."""
    path = Path(audio_path)
    if not path.exists():
        return 0.0

    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as wf:
                return round(wf.getnframes() / float(wf.getframerate()), 4)
        except Exception:
            pass

    return get_audio_duration_seconds(path)


async def synthesize_scene_audio_async(
    narration_text: str,
    scene_dir: Path,
    revision: int = 1,
    voice_id: str = "en-US-AndrewNeural",
) -> Tuple[Path, float, List[Dict[str, Any]]]:
    """
    Synthesizes audio for a single scene using native Edge-TTS WordBoundary events.
    Trims silence deterministically using atrim/apad and converts to uncompressed PCM WAV:
      scenes/<scene_id>/audio_v<N>.wav
    NO per-scene loudnorm is applied to prevent duration drift.
    Returns (audio_wav_path, duration, words_relative_to_0).
    """
    scene_dir = Path(scene_dir)
    scene_dir.mkdir(parents=True, exist_ok=True)
    audio_wav_path = scene_dir / f"audio_v{revision}.wav"

    raw_text = (narration_text or "").strip()
    text = raw_text if raw_text else "Next concept."

    audio_bytes, words = await synthesize_voice_with_boundaries(text, voice=voice_id)

    temp_mp3 = scene_dir / f"raw_audio_v{revision}.tmp.mp3"
    with open(temp_mp3, "wb") as f:
        f.write(audio_bytes)

    try:
        last_word_end = words[-1]["end"] if words else 1.0
        trim_end = last_word_end + 0.15

        # Deterministic atrim + apad on Uncompressed PCM WAV (NO silenceremove)
        # Leaving leading ~40ms untouched so t=0 matches edge-tts word offsets
        cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_mp3),
            "-af", f"atrim=end={trim_end:.4f},asetpts=PTS-STARTPTS,apad=pad_dur=0.25",
            "-c:a", "pcm_s16le",
            "-ar", "48000",
            "-ac", "2",
            str(audio_wav_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
    finally:
        if temp_mp3.exists():
            temp_mp3.unlink(missing_ok=True)

    # Measure exact duration from WAV header
    with wave.open(str(audio_wav_path), "rb") as wf:
        dur = round(wf.getnframes() / float(wf.getframerate()), 4)

    return audio_wav_path, dur, words


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
    tolerance_sec: float = 0.05,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Concatenates per-scene PCM WAV files into master audio using FFmpeg concat.
    Applies single master loudnorm pass (loudnorm=I=-16:TP=-1.5:LRA=11).
    Asserts abs(sum(scene_wav_durations) - master_audio_duration) <= 0.05.
    Computes exact cumulative scene start/end offsets and global word timestamps.
    """
    output_master_audio = Path(output_master_audio).resolve()
    output_master_audio.parent.mkdir(parents=True, exist_ok=True)

    if not scene_items:
        raise ValueError("Cannot concatenate empty scene audio list.")

    # Concat demuxer list
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for item in scene_items:
            p = Path(item["audio_path"]).resolve()
            f.write(f"file '{p.as_posix()}'\n")
        concat_list_path = Path(f.name)

    temp_master_wav = output_master_audio.with_suffix(".concat_tmp.wav")
    try:
        # Step 1: Lossless concat of PCM WAVs
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-c:a", "pcm_s16le",
            "-ar", "48000",
            "-ac", "2",
            str(temp_master_wav),
        ]
        subprocess.run(cmd_concat, capture_output=True, check=True)

        # Step 2: Single master loudnorm pass on the whole video audio
        is_mp3 = output_master_audio.suffix.lower() == ".mp3"
        target_wav = output_master_audio if not is_mp3 else output_master_audio.with_suffix(".wav")

        cmd_master = [
            "ffmpeg", "-y",
            "-i", str(temp_master_wav),
            "-af", "highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "pcm_s16le",
            "-ar", "48000",
            "-ac", "2",
            str(target_wav),
        ]
        subprocess.run(cmd_master, capture_output=True, check=True)

        # Also write parallel .mp3 version if target is .wav or vice versa
        if is_mp3:
            cmd_mp3 = [
                "ffmpeg", "-y",
                "-i", str(target_wav),
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                "-ar", "48000",
                "-ac", "2",
                str(output_master_audio),
            ]
            subprocess.run(cmd_mp3, capture_output=True, check=True)
        else:
            mp3_path = output_master_audio.with_suffix(".mp3")
            cmd_mp3 = [
                "ffmpeg", "-y",
                "-i", str(target_wav),
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                "-ar", "48000",
                "-ac", "2",
                str(mp3_path),
            ]
            subprocess.run(cmd_mp3, capture_output=True, check=True)
    finally:
        if concat_list_path.exists():
            concat_list_path.unlink(missing_ok=True)
        if temp_master_wav.exists():
            temp_master_wav.unlink(missing_ok=True)

    # Duration assertion against lossless WAV
    sum_scene_durations = sum(float(item["duration"]) for item in scene_items)
    master_wav_for_check = output_master_audio if output_master_audio.suffix.lower() == ".wav" else output_master_audio.with_suffix(".wav")
    master_dur = get_audio_duration(master_wav_for_check)
    drift = abs(sum_scene_durations - master_dur)
    print(f"[AUDIO:CONCAT] 🎚️ Master audio rendered. Sum={sum_scene_durations:.4f}s, Master={master_dur:.4f}s, Drift={drift:.6f}s", flush=True)
    assert drift <= tolerance_sec, f"Audio drift exceeded {tolerance_sec}s: sum={sum_scene_durations:.4f}s vs master={master_dur:.4f}s"

    # Compute exact cumulative offsets (no clamping)
    current_time = 0.0
    master_words: List[Dict[str, Any]] = []
    updated_scenes: List[Dict[str, Any]] = []

    for idx, item in enumerate(scene_items):
        scene_id = item["scene_id"]
        a_path = Path(item["audio_path"])
        dur = float(item["duration"])

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

    return updated_scenes, master_words
