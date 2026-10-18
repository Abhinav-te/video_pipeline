#!/usr/bin/env python3

import argparse
import asyncio
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
REPO_DIR = ENGINE_DIR.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from director.script import generate_script
from validation import validate_script_plan
from audio.tts_whisper import generate_voice, extract_word_timings
from timeline.beats import (
    align_timeline,
    align_script_tokens_to_whisper,
    enforce_minimum_scene_durations,
    calculate_target_scenes,
    merge_excess_scenes,
)
from timeline.enhancer import enhance_scenes
from timeline.choreographer import choreograph_scenes


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

VIDEO_DIR = ENGINE_DIR.parent / "video"
PUBLIC_DIR = VIDEO_DIR / "public"
RUNS_DIR = PUBLIC_DIR / "runs"

CACHE_DIR = ENGINE_DIR / ".cache"
SCRIPT_CACHE_DIR = CACHE_DIR / "scripts"


# ---------------------------------------------------------------------------
# Run Identification & Isolation
# ---------------------------------------------------------------------------

def generate_run_id() -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    return f"run_{timestamp}_{short_id}"


def cleanup_run_artifacts(run_dir: Path) -> None:
    """
    Cleans up partial or corrupted files in public/runs/<run_id>/ on failure.
    Guarantees zero stale or half-baked artifacts remain.
    """
    if run_dir and run_dir.exists():
        try:
            shutil.rmtree(run_dir, ignore_errors=True)
            log(f"🧹 Cleaned up failed run directory: {run_dir}")
        except Exception as exc:
            print(f"[ENGINE:WARN] Failed to clean up run directory {run_dir}: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Standardized Logging
# ---------------------------------------------------------------------------

def stage_start(stage: str, message: str):
    print(f"[{stage}:START] {message}", flush=True)


def stage_success(stage: str, message: str):
    print(f"[{stage}:SUCCESS] {message}", flush=True)


def stage_error(stage: str, message: str, exit_code: int = 1):
    print(f"\n[{stage}:ERROR] {message}", file=sys.stderr, flush=True)
    raise SystemExit(exit_code)


def log(message):
    print(f"[ENGINE] {message}", flush=True)


def fatal(message, stage="PIPELINE", exit_code=1):
    stage_error(stage, message, exit_code=exit_code)


# ---------------------------------------------------------------------------
# Numbered output archiving (audio_N.mp3 / data_N.json for legacy --index)
# ---------------------------------------------------------------------------

def get_next_output_index(public_dir):
    """
    Finds the next free N for audio_N.mp3 / data_N.json / final_video_N.mp4,
    looking across all three so they always stay in sync even if one type
    is missing for some past run.
    """
    indices = [0]
    for pattern in ("audio_*.mp3", "data_*.json", "final_video_*.mp4"):
        for f in glob.glob(os.path.join(str(public_dir), pattern)):
            match = re.search(r'_(\d+)\.', os.path.basename(f))
            if match:
                indices.append(int(match.group(1)))
    return max(indices) + 1


def archive_numbered_outputs(index, audio_file: Path, data_file: Path):
    """
    Copies run files into permanent numbered files (audio_N.mp3 / data_N.json)
    if legacy --index was requested.
    """
    numbered_audio = PUBLIC_DIR / f"audio_{index}.mp3"
    numbered_data = PUBLIC_DIR / f"data_{index}.json"

    shutil.copyfile(audio_file, numbered_audio)

    with open(data_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    payload["audio_file"] = numbered_audio.name

    with open(numbered_data, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    log(
        f"🗄️ Archived outputs as {numbered_audio.name} / {numbered_data.name}"
    )


SCHEMA_VERSION = "2.1"
ENGINE_VERSION = "2.0"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def build_cache_key(topic, duration, subject="auto"):
    """
    Create a stable cache key from the actual generation inputs.

    This prevents unrelated topics from sharing one stale JSON file.
    """
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    raw = json.dumps(
        {
            "topic": topic.strip(),
            "duration": duration,
            "subject": subject,
            "model": model,
            "schema_version": SCHEMA_VERSION,
            "engine_version": ENGINE_VERSION,
        },
        sort_keys=True,
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def get_script_cache_path(topic, duration, subject="auto"):
    key = build_cache_key(topic, duration, subject=subject)
    return SCRIPT_CACHE_DIR / f"{key}.json"


def load_script_cache(topic, duration, subject="auto"):
    cache_file = get_script_cache_path(topic, duration, subject=subject)

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            log(f"⚠️ Cache invalid: {cache_file}")
            return None

        if not isinstance(data.get("scenes"), list):
            log(f"⚠️ Cache missing scenes: {cache_file}")
            return None

        log(f"💾 CACHE HIT: {cache_file.name}")
        return data

    except Exception as exc:
        log(f"⚠️ Could not read cache: {exc}")
        return None


def save_script_cache(topic, duration, data, subject="auto"):
    SCRIPT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = get_script_cache_path(topic, duration, subject=subject)

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    log(f"💾 CACHE SAVED: {cache_file.name}")



# ---------------------------------------------------------------------------
# Script validation (delegated to centralized engine/validation module)
# ---------------------------------------------------------------------------

def validate_script(script):
    """
    Validate the structure returned by Gemini before touching TTS/timeline.
    Delegates to the centralized engine/validation module.
    """
    scenes = script.get("scenes", []) if isinstance(script, dict) else []
    log(f"🔍 Validating {len(scenes)} scenes via Validation Gate...")

    is_valid, errors = validate_script_plan(script)
    if not is_valid:
        error_msg = "Script validation failed:\n" + "\n".join(f"  • {e}" for e in errors)
        stage_error("VALIDATION", error_msg)

    stage_success("VALIDATION", f"Script validation passed ({len(scenes)} scenes)")


# ---------------------------------------------------------------------------
# Text preparation
# ---------------------------------------------------------------------------

def build_spoken_text(script):
    """
    Join scene narration into the exact text sent to TTS.
    """

    scenes = script.get("scenes", [])
    parts = []

    for scene in scenes:
        text = (scene.get("spoken_text") or scene.get("narration") or "").strip()
        if text:
            parts.append(text)

    text = " ".join(parts).strip()

    if not text:
        stage_error("DIRECTOR", "Generated script produced empty narration.")

    return text


# ---------------------------------------------------------------------------
# Stage Execution
# ---------------------------------------------------------------------------

def generate_or_load_script(topic, duration, no_cache=False, subject="auto"):
    if not no_cache:
        cached = load_script_cache(topic, duration, subject=subject)

        if cached is not None:
            stage_start("DIRECTOR", f"Loading cached script for '{topic}' ({duration}s)")
            target_scenes = calculate_target_scenes(duration)
            cached.setdefault("duration", duration)
            if "scenes" in cached and len(cached.get("scenes", [])) > target_scenes + 1:
                cached["scenes"] = merge_excess_scenes(cached["scenes"], target_scenes=target_scenes)
            stage_success("DIRECTOR", f"Cache hit: loaded script ({len(cached.get('scenes', []))} scenes)")
            stage_start("VALIDATION", f"Validating cached script ({len(cached.get('scenes', []))} scenes)")
            is_valid, errors = validate_script_plan(cached)
            if is_valid:
                stage_success("VALIDATION", f"Script validation passed ({len(cached.get('scenes', []))} scenes)")
                return cached
            log(f"⚠️ Cached script failed validation: {errors}. Bypassing cache for fresh generation.")

    MAX_ATTEMPTS = 3
    last_errors = []
    last_exception = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        attempt_str = f" (attempt {attempt}/{MAX_ATTEMPTS})" if attempt > 1 else ""
        stage_start("DIRECTOR", f"Generating script with Gemini for '{topic}' ({duration}s){attempt_str}")

        try:
            script = generate_script(topic, duration, subject=subject)
        except KeyError as exc:
            stage_error("DIRECTOR", f"Gemini generation failed: Environment variable {exc} is not set.")
        except Exception as exc:
            last_exception = exc
            if attempt < MAX_ATTEMPTS:
                print(
                    f"[DIRECTOR:RETRY] Gemini generation attempt {attempt}/{MAX_ATTEMPTS} failed:\n{exc}\nRetrying fresh generation...",
                    file=sys.stderr,
                    flush=True,
                )
                continue
            stage_error("DIRECTOR", f"Gemini generation failed after {MAX_ATTEMPTS} attempts:\n{exc}")

        target_scenes = calculate_target_scenes(duration)
        if isinstance(script, dict):
            script.setdefault("duration", duration)
            if "scenes" in script and len(script.get("scenes", [])) > target_scenes + 1:
                script["scenes"] = merge_excess_scenes(script["scenes"], target_scenes=target_scenes)

        stage_success("DIRECTOR", f"Generated script successfully ({len(script.get('scenes', []))} scenes)")

        stage_start("VALIDATION", f"Validating generated script ({len(script.get('scenes', []))} scenes)")
        is_valid, errors = validate_script_plan(script)

        if is_valid:
            stage_success("VALIDATION", f"Script validation passed ({len(script.get('scenes', []))} scenes)")
            save_script_cache(topic, duration, script, subject=subject)
            return script

        last_errors = errors
        violation_details = "\n".join(f"  • {e}" for e in errors)

        if attempt < MAX_ATTEMPTS:
            print(
                f"[VALIDATION:RETRY] Script validation failed on attempt {attempt}/{MAX_ATTEMPTS}:\n{violation_details}\nRequesting fresh generation from Gemini...",
                flush=True,
            )
        else:
            error_msg = f"Script validation failed after {MAX_ATTEMPTS} attempts:\n{violation_details}"
            stage_error("VALIDATION", error_msg)

    if last_errors:
        stage_error("VALIDATION", f"Script validation failed:\n" + "\n".join(f"  • {e}" for e in last_errors))
    elif last_exception:
        stage_error("DIRECTOR", f"Gemini generation failed:\n{last_exception}")


async def generate_audio(text, audio_file: Path):
    audio_file.parent.mkdir(parents=True, exist_ok=True)

    stage_start("AUDIO", f"Generating Edge-TTS narration ({len(text.split())} words)")

    try:
        await generate_voice(text, str(audio_file))
    except Exception as exc:
        stage_error("AUDIO", f"Edge-TTS generation failed:\n{exc}")

    if not audio_file.exists():
        stage_error(
            "AUDIO",
            f"TTS completed without creating audio file:\n{audio_file}"
        )

    if audio_file.stat().st_size == 0:
        stage_error("AUDIO", "Generated audio file is empty.")

    stage_success(
        "AUDIO",
        f"Audio generated: {audio_file.name} ({audio_file.stat().st_size:,} bytes)"
    )


def generate_timeline(script, audio_file: Path):
    stage_start("TIMELINE", "Extracting Whisper word timestamps and aligning timeline")

    try:
        words = extract_word_timings(str(audio_file))
    except Exception as exc:
        stage_error("TIMELINE", f"Whisper timestamp extraction failed:\n{exc}")

    if not words:
        stage_error("TIMELINE", "Whisper returned zero word timestamps.")

    log(f"Whisper extracted {len(words)} words.")

    # Phase 7: Align Whisper timestamps back to original script tokens
    # (Preserves script spelling over Whisper phonetic mishears: DBSCAN vs DISCAN, partitions vs PETITIONS)
    narration_text = build_spoken_text(script)
    words = align_script_tokens_to_whisper(narration_text, words)

    log("Aligning scenes to narration...")

    scenes = script.get("scenes", [])
    if len(scenes) > 8:
        scenes = merge_excess_scenes(scenes, target_scenes=8)

    try:
        timed_scenes = align_timeline(scenes, words)
    except Exception as exc:
        stage_error("TIMELINE", f"Timeline alignment failed:\n{exc}")

    if not timed_scenes:
        stage_error("TIMELINE", "Timeline alignment produced zero scenes.")

    # Phase 2 Milestone 3: Semantic Visual Enhancer Pass
    try:
        timed_scenes = enhance_scenes(timed_scenes)
    except Exception as exc:
        stage_error("TIMELINE", f"Semantic enhancement pass failed:\n{exc}")

    badged_count = sum(1 for s in timed_scenes if s.get("badge"))
    log(f"🏷️ Attached semantic badges to {badged_count}/{len(timed_scenes)} scenes.")

    # Phase 3 & 7: Context-Aware AI Scene Choreographer Pass
    try:
        domain = script.get("subject") or script.get("domain") or "auto"
        timed_scenes = choreograph_scenes(timed_scenes, words, domain=domain, fps=30)
    except Exception as exc:
        stage_error("TIMELINE", f"Context-aware choreography pass failed:\n{exc}")

    # Phase 7: Final post-processing pass guaranteeing duration >= 2.5s across every scene in data.json
    timed_scenes = enforce_minimum_scene_durations(timed_scenes, min_duration=2.5)

    domain_tag = timed_scenes[0].get("choreography", {}).get("domain", "code") if timed_scenes else "code"
    log(f"🎬 Choreographed {len(timed_scenes)} scenes for domain '{domain_tag}'.")

    # Basic sanity check
    previous_start = -1.0

    for index, scene in enumerate(timed_scenes, start=1):
        start_time = scene.get("start_time")

        if not isinstance(start_time, (int, float)):
            stage_error(
                "TIMELINE",
                f"Timed scene {index} has invalid start_time: {start_time!r}"
            )

        if start_time < 0:
            stage_error("TIMELINE", f"Timed scene {index} has negative start_time.")

        if start_time < previous_start:
            stage_error(
                "TIMELINE",
                f"Timeline is not chronological at scene {index}: {start_time} < {previous_start}"
            )

        previous_start = start_time

    return timed_scenes, words


def build_final_payload(script, timed_scenes, words, run_id: str):
    """
    Build the exact top-level object expected by Remotion/CodingShort.jsx.
    """

    payload = {
        "title": script.get("title", ""),
        "schema_version": script.get(
            "schema_version",
            SCHEMA_VERSION,
        ),
        "engine_version": ENGINE_VERSION,
        "run_id": run_id,
        "scenes": timed_scenes,
        "words": words,
        "audio_file": f"runs/{run_id}/audio.mp3",
    }

    return payload


def write_data_file(payload, data_file: Path):
    data_file.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically so Remotion never sees half-written JSON.
    temp_file = data_file.with_suffix(".tmp")

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(
                payload,
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.write("\n")

        os.replace(temp_file, data_file)

    except Exception as exc:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)

        stage_error("TIMELINE", f"Could not write {data_file}:\n{exc}")

    if not data_file.exists():
        stage_error("TIMELINE", f"Expected output was not created: {data_file}")

    if data_file.stat().st_size == 0:
        stage_error("TIMELINE", f"Generated JSON is empty: {data_file}")

    stage_success(
        "TIMELINE",
        f"Timeline assembled and saved: {data_file.name} ({data_file.stat().st_size:,} bytes)"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="V2 Phase 1: AI Script → TTS → Whisper → Timeline"
    )

    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="Topic for the educational short.",
    )

    parser.add_argument(
        "--length",
        type=int,
        choices=[15, 30, 60],
        default=60,
        help="Video target length in seconds.",
    )

    parser.add_argument(
        "--subject",
        type=str,
        choices=["auto", "code", "math", "physics", "systems", "ml", "chemistry", "quantum_physics", "mechanics", "electrical"],
        default="auto",
        help="Subject domain for video.",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force fresh Gemini generation.",
    )

    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Unique identifier for run isolation.",
    )

    parser.add_argument(
        "--no-manim",
        action="store_true",
        help="Disable Stage 4.5 Manim Community pre-rendering.",
    )

    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help=(
            "Numbered output index for legacy archive copies "
            "(audio_N.mp3 / data_N.json)."
        ),
    )

    args = parser.parse_args()

    topic = args.topic.strip()

    if not topic:
        stage_error("DIRECTOR", "--topic cannot be empty.")

    # ---------------------------------------------------------------
    # Environment check
    # ---------------------------------------------------------------

    if not os.getenv("GEMINI_API_KEY"):
        stage_error(
            "DIRECTOR",
            "GEMINI_API_KEY environment variable is not set.\n\n"
            "Set it before running the engine, for example:\n"
            "export GEMINI_API_KEY='YOUR_KEY'"
        )

    # ---------------------------------------------------------------
    # Run Isolation Setup
    # ---------------------------------------------------------------

    run_id = args.run_id or generate_run_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    data_file = run_dir / "data.json"
    audio_file = run_dir / "audio.mp3"

    print()
    print("=" * 70)
    print(f"🚀 V2 PHASE 1 — AI SCRIPTING PIPELINE [Run: {run_id}]")
    print("=" * 70)
    print(f"Topic:    {topic}")
    print(f"Subject:  {args.subject}")
    print(f"Length:   {args.length}s")
    print(f"Cache:    {'DISABLED' if args.no_cache else 'ENABLED'}")
    print(f"Run Dir:  {run_dir}")
    print("=" * 70)
    print()

    try:
        # Clean existing artifacts in this run_dir if re-running same run_id
        if data_file.exists():
            data_file.unlink()
        if audio_file.exists():
            audio_file.unlink()

        # ---------------------------------------------------------------
        # Step 1 & 2 — Gemini & Validation
        # ---------------------------------------------------------------

        script = generate_or_load_script(
            topic=topic,
            duration=args.length,
            no_cache=args.no_cache,
            subject=args.subject,
        )

        # ---------------------------------------------------------------
        # Step 2 — Build narration
        # ---------------------------------------------------------------

        narration = build_spoken_text(script)
        word_count = len(narration.split())
        log(f"🗣️ Narration: {word_count} words")

        # ---------------------------------------------------------------
        # Step 3 — Edge-TTS
        # ---------------------------------------------------------------

        asyncio.run(generate_audio(narration, audio_file))

        # ---------------------------------------------------------------
        # Step 4 — Whisper & Timeline
        # ---------------------------------------------------------------

        timed_scenes, words = generate_timeline(script, audio_file)

        # ---------------------------------------------------------------
        # Step 4.5 — Stage 4.5 Manim Sub-Renderer Bridge
        # ---------------------------------------------------------------

        enable_manim = not getattr(args, "no_manim", False)
        try:
            try:
                from engine.renderer.manim_bridge import render_manim_clips_for_timeline
            except ModuleNotFoundError:
                from renderer.manim_bridge import render_manim_clips_for_timeline
            timed_scenes = render_manim_clips_for_timeline(
                timed_scenes,
                run_dir=run_dir,
                enable_manim=enable_manim,
                max_clips=2,
            )
        except Exception as exc:
            log(f"[MANIM:WARN] Manim sub-renderer encountered an unexpected error: {exc}. Continuing with Remotion SVG fallbacks.")

        # ---------------------------------------------------------------
        # Step 5 — Final JSON Payload & Atomic Write
        # ---------------------------------------------------------------

        payload = build_final_payload(
            script=script,
            timed_scenes=timed_scenes,
            words=words,
            run_id=run_id,
        )

        write_data_file(payload, data_file)

        # ---------------------------------------------------------------
        # Step 6 — Archive numbered copies (if requested)
        # ---------------------------------------------------------------

        if args.index is not None:
            archive_numbered_outputs(args.index, audio_file, data_file)

        # ---------------------------------------------------------------
        # Final verification
        # ---------------------------------------------------------------

        log("🔎 Running run artifact verification...")

        if not data_file.exists():
            stage_error("TIMELINE", f"Run finished but {data_file.name} is missing.")

        if not audio_file.exists():
            stage_error("AUDIO", f"Run finished but {audio_file.name} is missing.")

        try:
            with open(data_file, "r", encoding="utf-8") as f:
                verification_data = json.load(f)
        except Exception as exc:
            stage_error("TIMELINE", f"Final data.json is invalid JSON:\n{exc}")

        if not verification_data.get("scenes"):
            stage_error("TIMELINE", "Final data.json contains no scenes.")

        if not verification_data.get("words"):
            stage_error("TIMELINE", "Final data.json contains no Whisper words.")

        expected_audio_rel = f"runs/{run_id}/audio.mp3"
        if verification_data.get("audio_file") != expected_audio_rel:
            stage_error(
                "TIMELINE",
                f"Final JSON audio_file does not match expected path:\n"
                f"Expected: {expected_audio_rel!r}\n"
                f"Got:      {verification_data.get('audio_file')!r}"
            )
    except BaseException:
        cleanup_run_artifacts(run_dir)
        raise

    print()
    print("=" * 70)
    print("✅ ENGINE GENERATION COMPLETE")
    print("=" * 70)
    print(f"🆔 Run ID:  {run_id}")
    print(f"📄 JSON:    {data_file}")
    print(f"🎙️ Audio:   {audio_file}")
    print(f"🎬 Scenes:  {len(verification_data['scenes'])}")
    print(f"🗣️ Words:   {len(verification_data['words'])}")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()