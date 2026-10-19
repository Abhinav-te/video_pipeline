import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import edge_tts
import torch
import whisper

_whisper_model = None
_whisper_device = None


def get_whisper_device() -> str:
    """
    Detects acceleration device for Whisper:
    1. Checks WHISPER_DEVICE environment variable override first.
    2. If not set and torch.cuda.is_available() is True, performs a runtime
       kernel sanity check (torch.zeros(1, device='cuda') + 1) to confirm
       GPU compute capability is supported by the installed PyTorch build.
    3. Falls back to 'cpu' with [AUDIO:WARN] if kernel execution fails.
    """
    override = os.getenv("WHISPER_DEVICE")
    if override:
        return override.strip().lower()

    if torch.cuda.is_available():
        try:
            # Runtime kernel sanity check to detect unsupported compute capability (e.g. sm_120)
            _ = torch.zeros(1, device="cuda") + 1
            gpu_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "NVIDIA GPU"
            print(f"[AUDIO:INFO] 🚀 Whisper device: cuda ({gpu_name})", flush=True)
            return "cuda"
        except Exception as exc:
            print(
                f"[AUDIO:WARN] ⚠️ CUDA device is available but kernel execution failed ({exc}). "
                f"GPU compute capability is incompatible with the installed PyTorch build. "
                f"Falling back to 'cpu'.",
                flush=True,
            )
            return "cpu"

    return "cpu"


def reset_whisper_cache() -> None:
    """Reset cached Whisper model (used in tests or device switching)."""
    global _whisper_model, _whisper_device
    _whisper_model = None
    _whisper_device = None


def get_whisper_model(model_name: str = "base"):
    """
    Returns the in-process cached Whisper model for the active device.
    Avoids reloading weights from disk on repeated calls.
    """
    global _whisper_model, _whisper_device
    device = get_whisper_device()
    if _whisper_model is None or _whisper_device != device:
        print(f"[AUDIO:INFO] Loading Whisper '{model_name}' on device '{device}'...", flush=True)
        _whisper_model = whisper.load_model(model_name, device=device)
        _whisper_device = device
    return _whisper_model


def verify_audio_file(audio_path: str) -> Tuple[bool, Optional[str]]:
    """
    Verifies that audio_path exists, is non-empty, and contains a playable,
    un-corrupted audio stream with duration > 0 via ffprobe.
    """
    path = Path(audio_path)
    if not path.exists():
        return False, f"Audio file does not exist: {audio_path}"

    if path.stat().st_size == 0:
        return False, f"Audio file is zero bytes: {audio_path}"

    if not shutil.which("ffprobe"):
        # Fallback if ffprobe binary is not present in PATH
        if path.stat().st_size < 1024:
            return False, f"Audio file is too small ({path.stat().st_size} bytes)"
        return True, None

    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,duration,channels,sample_rate",
        "-show_entries", "format=duration,size,bit_rate",
        "-of", "json",
        str(path),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        if not streams:
            err = proc.stderr.strip() if proc.stderr else "No audio stream found"
            return False, f"Audio verification failed: {err}"

        audio_stream = streams[0]
        codec = audio_stream.get("codec_name", "")
        if codec not in {"mp3", "aac", "wav", "flac"}:
            return False, f"Unexpected audio codec: {codec!r}"

        duration_val = data.get("format", {}).get("duration") or audio_stream.get("duration")
        if not duration_val:
            return False, "Audio stream has no readable duration."

        try:
            duration = float(duration_val)
        except (ValueError, TypeError):
            return False, f"Audio stream duration cannot be parsed: {duration_val!r}"

        if duration <= 0:
            return False, f"Audio duration must be > 0s, got {duration}s."

        return True, None

    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() if e.stderr else str(e)
        return False, f"ffprobe error inspecting audio: {err}"
    except Exception as e:
        return False, f"Audio verification error: {e}"


os.environ.setdefault("TRITON_CACHE_DIR", "/tmp/.triton")


def generate_voice_offline_fallback(text: str, output_file: str) -> None:
    """Offline fallback voice synthesis using espeak-ng and ffmpeg when network is unavailable."""
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_wav = out_path.with_suffix(".temp.wav")
    try:
        # Run espeak-ng to generate wav
        subprocess.run(["espeak-ng", "-s", "155", text, "-w", str(temp_wav)], check=True, capture_output=True)
        # Convert wav to mp3 with ffmpeg (guarantee >= 24000Hz standard broadcast sample rate)
        subprocess.run(["ffmpeg", "-y", "-i", str(temp_wav), "-ar", "44100", str(out_path)], check=True, capture_output=True)
        valid, err = verify_audio_file(str(out_path))
        if not valid:
            raise RuntimeError(f"Offline audio verification failed: {err}")
        print(f"[AUDIO:OFFLINE] 🎙️ Synthesized offline narration audio via espeak-ng -> {out_path.name}", flush=True)
    finally:
        if temp_wav.exists():
            temp_wav.unlink(missing_ok=True)


async def generate_voice(text: str, output_file: str, max_retries: int = 3, allow_offline_fallback: bool = False) -> None:
    """
    Generates the TTS MP3 using Microsoft Edge TTS with backoff retries and
    immediate playability verification, with seamless offline espeak-ng failover.
    """
    voice = os.getenv("EDGE_TTS_VOICE", "en-US-ChristopherNeural")
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    last_err = None

    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(out_path))

            valid, err = verify_audio_file(str(out_path))
            if not valid:
                raise RuntimeError(f"Audio integrity verification failed: {err}")

            return
        except Exception as e:
            last_err = e
            # Remove incomplete or corrupt file on retry
            if out_path.exists():
                try:
                    out_path.unlink()
                except OSError:
                    pass

            # If name resolution or network unreachable, immediately fallback to offline
            msg = str(e).lower()
            if allow_offline_fallback and any(k in msg for k in ("name resolution", "cannot connect", "network is unreachable", "connection refused")):
                print(f"[AUDIO:OFFLINE] ⚠️ Network unavailable ({e}). Falling back to offline voice engine...", flush=True)
                generate_voice_offline_fallback(text, output_file)
                return

            if attempt + 1 < max_retries:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(
                    f"[AUDIO:RETRY] Edge-TTS attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait_time}s...",
                    flush=True,
                )
                await asyncio.sleep(wait_time)

    # If all retries exhausted, attempt offline fallback before giving up
    if allow_offline_fallback:
        try:
            print("[AUDIO:OFFLINE] ⚠️ Edge-TTS exhausted all retries. Falling back to offline voice engine...", flush=True)
            generate_voice_offline_fallback(text, output_file)
            return
        except Exception as off_exc:
            raise RuntimeError(
                f"Edge-TTS synthesis failed after {max_retries} attempts ({last_err}), "
                f"and offline fallback failed ({off_exc})."
            )

    raise RuntimeError(f"Edge-TTS synthesis failed after {max_retries} attempts ({last_err}).")


def merge_hyphenated_tokens(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merges split hyphenated tokens (e.g. 'K', '-means' or 'Non-', 'convex') into
    single intact word tokens so subtitles and visual callouts never split them.
    """
    if not words:
        return []

    merged: List[Dict[str, Any]] = []
    i = 0
    n = len(words)

    KNOWN_PAIRS = {
        ("k", "means"): "K-MEANS",
        ("t", "sne"): "T-SNE",
        ("auto", "encoders"): "AUTO-ENCODERS",
        ("auto", "encoder"): "AUTO-ENCODER",
        ("non", "convex"): "NON-CONVEX",
        ("high", "dimensional"): "HIGH-DIMENSIONAL",
        ("low", "dimensional"): "LOW-DIMENSIONAL",
    }

    while i < n:
        curr = words[i]
        curr_text = str(curr.get("word", "")).strip()

        # Check for isolated hyphen between previous and next
        if curr_text in {"-", "—", "--"} and merged and (i + 1 < n):
            nxt = words[i + 1]
            prev = merged[-1]
            merged[-1] = {
                "word": f"{prev['word'].rstrip('-')}-{str(nxt.get('word', '')).strip().lstrip('-')}",
                "start": prev["start"],
                "end": max(nxt["end"], prev["end"]),
            }
            i += 2
            continue

        # Check known compound pairs
        if i + 1 < n:
            nxt = words[i + 1]
            nxt_text = str(nxt.get("word", "")).strip()
            pair_key = (curr_text.lower().rstrip("-"), nxt_text.lower().lstrip("-"))
            if pair_key in KNOWN_PAIRS:
                merged.append({
                    "word": KNOWN_PAIRS[pair_key],
                    "start": curr["start"],
                    "end": nxt["end"],
                })
                i += 2
                continue

        # Check trailing hyphen on curr or leading hyphen on nxt
        if curr_text.endswith("-") and i + 1 < n:
            nxt = words[i + 1]
            nxt_text = str(nxt.get("word", "")).strip()
            merged.append({
                "word": f"{curr_text.rstrip('-')}-{nxt_text.lstrip('-')}",
                "start": curr["start"],
                "end": nxt["end"],
            })
            i += 2
            continue

        if i + 1 < n and str(words[i + 1].get("word", "")).strip().startswith("-"):
            nxt = words[i + 1]
            nxt_text = str(nxt.get("word", "")).strip()
            if nxt_text in {"-", "—", "--"} and i + 2 < n:
                nxt2 = words[i + 2]
                nxt2_text = str(nxt2.get("word", "")).strip().lstrip("-")
                merged.append({
                    "word": f"{curr_text.rstrip('-')}-{nxt2_text}",
                    "start": curr["start"],
                    "end": nxt2["end"],
                })
                i += 3
                continue
            elif nxt_text not in {"-", "—", "--"}:
                merged.append({
                    "word": f"{curr_text.rstrip('-')}-{nxt_text.lstrip('-')}",
                    "start": curr["start"],
                    "end": nxt["end"],
                })
                i += 2
                continue

        merged.append(curr)
        i += 1

    return merged


def validate_and_sanitize_word_timestamps(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitizes word timestamps:
    - Merges split hyphenated tokens into single intact tokens (Phase 6).
    - Guarantees strictly non-negative timestamps (>= 0.0).
    - Guarantees start < end (min duration 0.05s).
    - Guarantees monotonic progression (start >= previous end).
    """
    if not words:
        raise ValueError("Whisper produced zero word timestamps.")

    words = merge_hyphenated_tokens(words)

    sanitized: List[Dict[str, Any]] = []
    last_end = 0.0

    for w in words:
        raw_word = str(w.get("word", "")).strip()
        if not raw_word:
            continue

        raw_start = float(w.get("start", 0.0))
        raw_end = float(w.get("end", 0.0))

        start = max(0.0, raw_start)
        if start < last_end:
            start = last_end

        end = max(start + 0.05, raw_end)

        sanitized.append({
            "word": raw_word,
            "start": round(start, 3),
            "end": round(end, 3),
        })
        last_end = end

    if not sanitized:
        raise ValueError("All word timestamps were empty or invalid.")

    return sanitized


def extract_word_timings(audio_path: str) -> List[Dict[str, Any]]:
    """
    Extracts, validates, and sanitizes word timestamps using cached Whisper model.
    """
    valid, err = verify_audio_file(audio_path)
    if not valid:
        raise RuntimeError(f"Cannot extract timestamps from invalid audio: {err}")

    model = get_whisper_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)

    raw_words = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            raw_words.append({
                "word": word.get("word", ""),
                "start": word.get("start", 0.0),
                "end": word.get("end", 0.0),
            })

    return validate_and_sanitize_word_timestamps(raw_words)