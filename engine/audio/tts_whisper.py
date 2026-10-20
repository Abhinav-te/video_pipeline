import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import edge_tts
import torch
import whisper

REPO_DIR = Path(__file__).resolve().parent.parent.parent
AUDIO_CACHE_DIR = REPO_DIR / "engine" / ".cache" / "audio"

_whisper_model = None
_whisper_device = None


def sanitize_spoken_narration(text: str) -> str:
    """
    Sanitizes spoken narration text so raw CLI commands, package scopes, and symbols
    are converted into natural spoken developer English before Edge-TTS / Whisper run.

    Examples:
      - 'step.run()' -> 'step dot run'
      - 'npm install @acme/edgecache@latest' -> 'npm install the latest acme edgecache package'
      - 'npm install at acme slash sdk at latest' -> 'install the latest acme sdk package'
      - '@scope/pkg' -> 'the scope pkg package'
      - '--cluster edge-us-east' -> 'cluster edge us east'
      - 'v1' -> 'version one', 'v2' -> 'version two'
      - 'O(1)' -> 'O of one', 'O(n)' -> 'O of n', 'O(n log n)' -> 'O of n log n'
    """
    if not text:
        return ""

    s = text.strip()

    # 0. Strict Phonetic Spoken Code Normalization (Applies ONLY to TTS synthesis audio)
    s = re.sub(r"\bstep\.run\(\)", "step dot run", s)
    s = re.sub(r"\bstep\.run\b", "step dot run", s)
    s = re.sub(r"\binngest\.createFunction\(\)", "inngest create function", s)
    s = re.sub(r"\binngest\.createFunction\b", "inngest create function", s)

    # 1. Clean legacy phonetic mispronunciations: "at <pkg> slash <name> at latest" -> "the latest <pkg> <name> package"
    s = re.sub(
        r"\bat\s+([a-zA-Z0-9_-]+)\s+slash\s+([a-zA-Z0-9_-]+)\s+at\s+latest\b",
        r"the latest \1 \2 package",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"\bat\s+([a-zA-Z0-9_-]+)\s+slash\s+([a-zA-Z0-9_-]+)\b",
        r"the \1 \2 package",
        s,
        flags=re.IGNORECASE,
    )

    # 2. Package scoped syntax: @scope/pkg@latest or @scope/pkg@version
    s = re.sub(
        r"@([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)@(?:latest|[0-9a-zA-Z_.-]+)",
        r"the latest \1 \2 package",
        s,
    )
    s = re.sub(
        r"@([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)",
        r"the \1 \2 package",
        s,
    )

    # 3. CLI flags: --flag-name or --flag -> clean spoken flag name
    s = re.sub(r"--([a-zA-Z0-9]+)-([a-zA-Z0-9]+)", r"\1 \2", s)
    s = re.sub(r"--([a-zA-Z0-9]+)", r"\1", s)

    # 4. HTTP Endpoints: GET /v2/cache/keys -> GET cache keys
    s = re.sub(r"\b(GET|POST|PUT|DELETE|PATCH)\s+/v[0-9]/", r"\1 ", s)
    s = re.sub(r"/([a-zA-Z0-9_-]+)", r" \1", s)

    # 5. Algorithmic Complexity notation
    s = re.sub(r"\bO\(1\)\b", "O of one", s)
    s = re.sub(r"\bO\(n\s*log\s*n\)\b", "O of n log n", s, flags=re.IGNORECASE)
    s = re.sub(r"\bO\(n\^2\)\b|\bO\(n²\)\b", "O of n squared", s)
    s = re.sub(r"\bO\(n\)\b", "O of n", s)
    s = re.sub(r"\bO\(N\)\b", "O of N", s)

    # 6. Version notation
    s = re.sub(r"\bv1\.0\b|\bv1\b", "version one", s, flags=re.IGNORECASE)
    s = re.sub(r"\bv2\.0\b|\bv2\b", "version two", s, flags=re.IGNORECASE)

    # 7. Common technical abbreviations
    s = re.sub(r"\s+", " ", s).strip()
    return s


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


def get_audio_duration_seconds(audio_path: Union[str, Path]) -> float:
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


def master_audio(audio_path: Union[str, Path]) -> Path:
    """
    Post-processes audio with broadcast mastering:
    - Highpass filter at 80Hz (removes low-end rumble/thumps)
    - EBU R128 loudness normalization (I=-16, TP=-1.5, LRA=11)
    - Fade-in 0.03s and Fade-out 0.04s for seamless scene transitions
    - 48000Hz stereo output
    """
    path = Path(audio_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found for mastering: {path}")

    dur = get_audio_duration_seconds(path)
    if dur <= 0.08:
        return path

    fade_out_start = max(0.0, dur - 0.04)
    af_filter = f"highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.03,afade=t=out:st={fade_out_start:.3f}:d=0.04"

    temp_out = path.with_suffix(".mastered.mp3")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(path),
        "-af", af_filter,
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(temp_out),
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        valid, err = verify_audio_file(str(temp_out))
        if not valid:
            raise RuntimeError(f"Mastered audio integrity check failed: {err}")
        temp_out.replace(path)
        print(f"[AUDIO:MASTER] 🎚️ Mastered broadcast audio (48kHz stereo, loudnorm=-16LUFS) -> {path.name}", flush=True)
        return path
    except Exception as exc:
        if temp_out.exists():
            temp_out.unlink(missing_ok=True)
        print(f"[AUDIO:WARN] Audio mastering skipped due to error: {exc}", file=sys.stderr)
        return path


async def generate_voice(
    text: str,
    output_file: str,
    max_retries: int = 3,
    voice: Optional[str] = None,
    allow_offline_fallback: bool = False,
) -> None:
    """
    Generates narration MP3 using Edge-TTS with warm, natural senior-engineer voices
    (en-US-AndrewNeural / en-US-BrianNeural), 3 automatic backoff retries,
    local audio caching, and broadcast mastering.

    STRICT POLICY: Robotic espeak/espeak-ng/pyttsx3 fallbacks are completely banned.
    """
    clean_text = sanitize_spoken_narration(text)
    active_voice = voice or os.getenv("EDGE_TTS_VOICE", "en-US-AndrewNeural")
    out_path = Path(output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Local Audio Cache Check
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(f"{clean_text}:{active_voice}".encode("utf-8")).hexdigest()
    cached_file = AUDIO_CACHE_DIR / f"{cache_key}.mp3"

    if cached_file.exists():
        valid, _ = verify_audio_file(str(cached_file))
        if valid:
            shutil.copyfile(cached_file, out_path)
            master_audio(out_path)
            print(f"[AUDIO:CACHE] ⚡ Reused cached neural audio -> {out_path.name}", flush=True)
            return

    last_err = None
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(clean_text, active_voice)
            await communicate.save(str(out_path))

            valid, err = verify_audio_file(str(out_path))
            if not valid:
                raise RuntimeError(f"Audio integrity verification failed: {err}")

            # Apply broadcast audio mastering
            master_audio(out_path)

            # Store in cache
            shutil.copyfile(out_path, cached_file)
            print(f"[AUDIO:NEURAL] 🎙️ Synthesized neural voice ({active_voice}) -> {out_path.name}", flush=True)
            return
        except Exception as e:
            last_err = e
            if out_path.exists():
                try:
                    out_path.unlink()
                except OSError:
                    pass

            if attempt + 1 < max_retries:
                wait_time = 2 ** attempt
                print(
                    f"[AUDIO:RETRY] Edge-TTS attempt {attempt + 1}/{max_retries} failed ({e}). "
                    f"Retrying in {wait_time}s...",
                    flush=True,
                )
                await asyncio.sleep(wait_time)

    # NEVER fallback to espeak/espeak-ng. Raise clear runtime error.
    raise RuntimeError(
        f"Neural TTS synthesis failed after {max_retries} attempts ({last_err}). "
        f"Robotic espeak/espeak-ng fallbacks are strictly prohibited per AGENTS.md rules."
    )


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