#!/usr/bin/env python3

import argparse
import asyncio
import glob
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

from director.script import generate_script
from validation.code import check_syntax, check_terminal_snippet
from audio.tts_whisper import generate_voice, extract_word_timings
from timeline.beats import align_timeline


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ENGINE_DIR = Path(__file__).resolve().parent
VIDEO_DIR = ENGINE_DIR.parent / "video"
PUBLIC_DIR = VIDEO_DIR / "public"

DATA_FILE = PUBLIC_DIR / "data_current.json"
AUDIO_FILE = PUBLIC_DIR / "audio_current.mp3"

CACHE_DIR = ENGINE_DIR / ".cache"
SCRIPT_CACHE_DIR = CACHE_DIR / "scripts"


# ---------------------------------------------------------------------------
# Numbered output archiving (audio_N.mp3 / data_N.json, matching final_video_N.mp4)
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


def archive_numbered_outputs(index):
    """
    Copies the just-generated _current files into permanent numbered
    files (audio_N.mp3 / data_N.json), so past runs aren't overwritten
    the next time generate.py runs. The archived JSON's audio_file field
    is rewritten to point at the archived audio file, so the pair is
    self-contained even after audio_current.mp3 gets replaced later.
    """
    numbered_audio = PUBLIC_DIR / f"audio_{index}.mp3"
    numbered_data = PUBLIC_DIR / f"data_{index}.json"

    shutil.copyfile(AUDIO_FILE, numbered_audio)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
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
# Logging
# ---------------------------------------------------------------------------

def log(message):
    print(f"[ENGINE] {message}", flush=True)


def fatal(message, exit_code=1):
    print(f"\n❌ FATAL: {message}", file=sys.stderr, flush=True)
    raise SystemExit(exit_code)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def build_cache_key(topic, duration):
    """
    Create a stable cache key from the actual generation inputs.

    This prevents unrelated topics from sharing one stale JSON file.
    """
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    raw = json.dumps(
        {
            "topic": topic.strip(),
            "duration": duration,
            "model": model,
            "schema_version": SCHEMA_VERSION,
            "engine_version": ENGINE_VERSION,
        },
        sort_keys=True,
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def get_script_cache_path(topic, duration):
    key = build_cache_key(topic, duration)
    return SCRIPT_CACHE_DIR / f"{key}.json"


def load_script_cache(topic, duration):
    cache_file = get_script_cache_path(topic, duration)

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


def save_script_cache(topic, duration, data):
    SCRIPT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = get_script_cache_path(topic, duration)

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    log(f"💾 CACHE SAVED: {cache_file.name}")


# ---------------------------------------------------------------------------
# Script validation
# ---------------------------------------------------------------------------

VALID_SCENE_TYPES = {
    "fullscreen_text",
    "code_reveal",
    "code_transform",
    "terminal",
    "diagram",
    "comparison",
}


def validate_script(script):
    """
    Validate the structure returned by Gemini before touching TTS/timeline.
    """

    if not isinstance(script, dict):
        fatal("Gemini returned something other than a JSON object.")

    scenes = script.get("scenes")

    if not isinstance(scenes, list):
        fatal("Generated script does not contain a valid 'scenes' list.")

    if not scenes:
        fatal("Generated script contains zero scenes.")

    log(f"🔍 Validating {len(scenes)} scenes...")

    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            fatal(f"Scene {index} is not an object.")

        scene_type = scene.get("scene_type")

        if scene_type not in VALID_SCENE_TYPES:
            fatal(
                f"Scene {index} has invalid scene_type: "
                f"{scene_type!r}. "
                f"Allowed: {sorted(VALID_SCENE_TYPES)}"
            )

        spoken_text = scene.get("spoken_text", "")

        if not isinstance(spoken_text, str):
            fatal(f"Scene {index} spoken_text is not a string.")

        if not spoken_text.strip():
            fatal(f"Scene {index} has empty spoken_text.")

        word_count = len(spoken_text.split())

        if word_count > 11:
            fatal(
                f"Scene {index} contains {word_count} spoken words. "
                f"Maximum is 11."
            )

        # Validate code-bearing scenes.
        if scene_type in {
            "code_reveal",
            "code_transform",
            "terminal",
        }:
            code = scene.get("code_snippet", "")

            if not isinstance(code, str) or not code.strip():
                fatal(
                    f"Scene {index} ({scene_type}) has no code_snippet."
                )

            # "terminal" scenes show command-line OUTPUT (e.g. "Done in 2.5s",
            # tracebacks, prompts) — that text is not valid Python and must
            # not be run through ast.parse(). Only code_reveal/code_transform
            # claim to hold real, executable Python.
            if scene_type == "terminal":
                valid, error = check_terminal_snippet(code)
            else:
                valid, error = check_syntax(code)

            if not valid:
                fatal(
                    f"Scene {index} ({scene_type}) contains invalid content:\n"
                    f"{error}\n\n"
                    f"{code}"
                )

        # Comparison has two code blocks.
        if scene_type == "comparison":
            problem_code = scene.get("problem_code", "")
            solution_code = scene.get("solution_code", "")

            if not problem_code.strip():
                fatal(f"Scene {index} comparison has empty problem_code.")

            if not solution_code.strip():
                fatal(f"Scene {index} comparison has empty solution_code.")

            valid, error = check_syntax(problem_code)

            if not valid:
                fatal(
                    f"Scene {index} problem_code is invalid:\n{error}"
                )

            valid, error = check_syntax(solution_code)

            if not valid:
                fatal(
                    f"Scene {index} solution_code is invalid:\n{error}"
                )

        # Diagram requires nodes.
        if scene_type == "diagram":
            nodes = scene.get("nodes")

            if not isinstance(nodes, list) or not nodes:
                fatal(f"Scene {index} diagram has no nodes.")

            if len(nodes) > 3:
                fatal(
                    f"Scene {index} diagram has {len(nodes)} nodes. "
                    f"Maximum is 3."
                )

    # The director requires the first scene to be fullscreen text.
    if scenes[0].get("scene_type") != "fullscreen_text":
        fatal(
            "Scene 1 must be 'fullscreen_text', "
            f"got {scenes[0].get('scene_type')!r}."
        )

    if not any(
        scene.get("scene_type") == "comparison"
        for scene in scenes
    ):
        fatal("Generated script contains no comparison scene.")

    log("✅ Script validation passed.")


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
        text = scene.get("spoken_text", "").strip()

        if text:
            parts.append(text)

    text = " ".join(parts).strip()

    if not text:
        fatal("Generated script produced empty narration.")

    return text


# ---------------------------------------------------------------------------
# Phase 1
# ---------------------------------------------------------------------------

def generate_or_load_script(topic, duration, no_cache=False):
    if not no_cache:
        cached = load_script_cache(topic, duration)

        if cached is not None:
            validate_script(cached)
            return cached

    log("🤖 CACHE MISS: Generating script with Gemini...")

    try:
        script = generate_script(topic, duration)
    except Exception as exc:
        fatal(f"Gemini generation failed:\n{exc}")

    validate_script(script)

    save_script_cache(topic, duration, script)

    return script


async def generate_audio(text):
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    log("🎙️ Generating Edge-TTS narration...")

    try:
        await generate_voice(text, str(AUDIO_FILE))
    except Exception as exc:
        fatal(f"Edge-TTS generation failed:\n{exc}")

    if not AUDIO_FILE.exists():
        fatal(
            f"TTS completed without creating audio file:\n"
            f"{AUDIO_FILE}"
        )

    if AUDIO_FILE.stat().st_size == 0:
        fatal("Generated audio file is empty.")

    log(
        f"✅ Audio generated: "
        f"{AUDIO_FILE.name} "
        f"({AUDIO_FILE.stat().st_size:,} bytes)"
    )


def generate_timeline(script):
    log("📝 Extracting Whisper word timestamps...")

    try:
        words = extract_word_timings(str(AUDIO_FILE))
    except Exception as exc:
        fatal(f"Whisper timestamp extraction failed:\n{exc}")

    if not words:
        fatal("Whisper returned zero word timestamps.")

    log(f"✅ Whisper extracted {len(words)} words.")

    log("⏱️ Aligning scenes to narration...")

    scenes = script.get("scenes", [])

    try:
        timed_scenes = align_timeline(scenes, words)
    except Exception as exc:
        fatal(f"Timeline alignment failed:\n{exc}")

    if not timed_scenes:
        fatal("Timeline alignment produced zero scenes.")

    # Basic sanity check.
    previous_start = -1.0

    for index, scene in enumerate(timed_scenes, start=1):
        start_time = scene.get("start_time")

        if not isinstance(start_time, (int, float)):
            fatal(
                f"Timed scene {index} has invalid start_time: "
                f"{start_time!r}"
            )

        if start_time < 0:
            fatal(f"Timed scene {index} has negative start_time.")

        if start_time < previous_start:
            fatal(
                f"Timeline is not chronological at scene {index}: "
                f"{start_time} < {previous_start}"
            )

        previous_start = start_time

    log(f"✅ Timeline contains {len(timed_scenes)} scenes.")

    return timed_scenes, words


def build_final_payload(script, timed_scenes, words):
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
        "scenes": timed_scenes,
        "words": words,
        "audio_file": AUDIO_FILE.name,
    }

    return payload


def write_data_file(payload):
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    # Write atomically so Remotion never sees half-written JSON.
    temp_file = DATA_FILE.with_suffix(".tmp")

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(
                payload,
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.write("\n")

        os.replace(temp_file, DATA_FILE)

    except Exception as exc:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)

        fatal(f"Could not write {DATA_FILE}:\n{exc}")

    if not DATA_FILE.exists():
        fatal(f"Expected output was not created: {DATA_FILE}")

    if DATA_FILE.stat().st_size == 0:
        fatal(f"Generated JSON is empty: {DATA_FILE}")

    log(
        f"💾 Wrote {DATA_FILE.name} "
        f"({DATA_FILE.stat().st_size:,} bytes)"
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
        "--no-cache",
        action="store_true",
        help="Force fresh Gemini generation.",
    )

    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help=(
            "Numbered output index for this run's archive copies "
            "(audio_N.mp3 / data_N.json). If omitted, auto-detects the "
            "next free index from existing public/ files, keeping it in "
            "sync with final_video_N.mp4 numbering."
        ),
    )

    args = parser.parse_args()

    topic = args.topic.strip()

    if not topic:
        fatal("--topic cannot be empty.")

    # ---------------------------------------------------------------
    # Environment check
    # ---------------------------------------------------------------

    if not os.getenv("GEMINI_API_KEY"):
        fatal(
            "GEMINI_API_KEY environment variable is not set.\n\n"
            "Set it before running the engine, for example:\n"
            "export GEMINI_API_KEY='YOUR_KEY'"
        )

    # ---------------------------------------------------------------
    # Startup
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("🚀 V2 PHASE 1 — AI SCRIPTING PIPELINE")
    print("=" * 70)
    print(f"Topic:    {topic}")
    print(f"Length:   {args.length}s")
    print(f"Cache:    {'DISABLED' if args.no_cache else 'ENABLED'}")
    print("=" * 70)
    print()

    # ---------------------------------------------------------------
    # Clean previous runtime artifacts
    # ---------------------------------------------------------------
    #
    # IMPORTANT:
    # We remove the previous data/audio BEFORE generation.
    #
    # That way, if Phase 1 fails, generate_and_render.py cannot
    # accidentally render yesterday's video.
    # ---------------------------------------------------------------

    if DATA_FILE.exists():
        log("🗑️ Removing previous data_current.json")
        DATA_FILE.unlink()

    if AUDIO_FILE.exists():
        log("🗑️ Removing previous audio_current.mp3")
        AUDIO_FILE.unlink()

    # ---------------------------------------------------------------
    # Step 1 — Gemini
    # ---------------------------------------------------------------

    script = generate_or_load_script(
        topic=topic,
        duration=args.length,
        no_cache=args.no_cache,
    )

    # ---------------------------------------------------------------
    # Step 2 — Build narration
    # ---------------------------------------------------------------

    narration = build_spoken_text(script)

    word_count = len(narration.split())

    log(
        f"🗣️ Narration: {word_count} words"
    )

    # ---------------------------------------------------------------
    # Step 3 — Edge-TTS
    # ---------------------------------------------------------------

    asyncio.run(generate_audio(narration))

    # ---------------------------------------------------------------
    # Step 4 — Whisper
    # ---------------------------------------------------------------

    timed_scenes, words = generate_timeline(script)

    # ---------------------------------------------------------------
    # Step 5 — Final JSON
    # ---------------------------------------------------------------

    payload = build_final_payload(
        script=script,
        timed_scenes=timed_scenes,
        words=words,
    )

    write_data_file(payload)

    # ---------------------------------------------------------------
    # Step 6 — Archive numbered copies (audio_N.mp3 / data_N.json)
    # ---------------------------------------------------------------

    output_index = args.index if args.index is not None else get_next_output_index(PUBLIC_DIR)
    archive_numbered_outputs(output_index)

    # ---------------------------------------------------------------
    # Final verification
    # ---------------------------------------------------------------

    log("🔎 Running final Phase 1 verification...")

    if not DATA_FILE.exists():
        fatal("Phase 1 finished but data_current.json is missing.")

    if not AUDIO_FILE.exists():
        fatal("Phase 1 finished but audio_current.mp3 is missing.")

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            verification_data = json.load(f)
    except Exception as exc:
        fatal(f"Final data_current.json is invalid JSON:\n{exc}")

    if not verification_data.get("scenes"):
        fatal("Final data_current.json contains no scenes.")

    if not verification_data.get("words"):
        fatal("Final data_current.json contains no Whisper words.")

    if verification_data.get("audio_file") != AUDIO_FILE.name:
        fatal(
            "Final JSON audio_file does not match generated audio: "
            f"{verification_data.get('audio_file')!r}"
        )

    print()
    print("=" * 70)
    print("✅ PHASE 1 COMPLETE")
    print("=" * 70)
    print(f"📄 JSON:  {DATA_FILE}")
    print(f"🎙️ Audio: {AUDIO_FILE}")
    print(f"🎬 Scenes: {len(verification_data['scenes'])}")
    print(f"🗣️ Words:  {len(verification_data['words'])}")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()