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
import subprocess
import sys
import uuid
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
REPO_DIR = ENGINE_DIR.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

# Evidence pipeline imports
from director.scene_planner import plan_scenes
from director.workflow_selector import select_best_workflow
from ingestion.evidence_extractor import extract_evidence_pack
from validation.evidence_validator import validate_evidence_and_plan
from validation import validate_script_plan, write_reflection_error, auto_heal_timeline_payload
from audio.tts_whisper import generate_voice, extract_word_timings
from timeline.beats import (
    align_timeline,
    align_script_tokens_to_whisper,
    enforce_minimum_scene_durations,
    calculate_target_scenes,
    merge_excess_scenes,
)
from timeline.enhancer import enhance_scenes
from timeline.timeline_mapper import choreograph_scenes, map_scene_timeline, chunk_caption_words
from config.brand_config import load_brand_config


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

def build_cache_key(topic, duration, subject="auto", source_text=None):
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
            "source_text": (source_text or "").strip(),
            "model": model,
            "schema_version": SCHEMA_VERSION,
            "engine_version": ENGINE_VERSION,
        },
        sort_keys=True,
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def get_script_cache_path(topic, duration, subject="auto", source_text=None):
    key = build_cache_key(topic, duration, subject=subject, source_text=source_text)
    return SCRIPT_CACHE_DIR / f"{key}.json"


def load_script_cache(topic, duration, subject="auto", source_text=None):
    cache_file = get_script_cache_path(topic, duration, subject=subject, source_text=source_text)

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


def save_script_cache(topic, duration, data, subject="auto", source_text=None):
    SCRIPT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = get_script_cache_path(topic, duration, subject=subject, source_text=source_text)

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

def generate_or_load_script(topic, duration, no_cache=False, subject="auto", mock=False, source_text=None, source_facts=None):
    if mock:
        stage_start("DIRECTOR", f"Loading pre-validated mock script for topic='{topic}', subject='{subject}', length={duration}s")
        from director.mock_library import get_mock_script
        script = get_mock_script(topic=topic, duration=duration, subject=subject, source_text=source_text, source_facts=source_facts)
        stage_success("DIRECTOR", f"Loaded mock script ({len(script.get('scenes', []))} scenes)")
        stage_start("VALIDATION", f"Validating mock script ({len(script.get('scenes', []))} scenes)")
        is_valid, errors = validate_script_plan(script)
        if not is_valid:
            stage_error("VALIDATION", f"Mock script failed validation: {errors}")
        stage_success("VALIDATION", f"Mock script validation passed ({len(script.get('scenes', []))} scenes)")
        return script

    if not no_cache:
        cached = load_script_cache(topic, duration, subject=subject, source_text=source_text)

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
            script = generate_script(topic, duration, subject=subject, source_text=source_text, source_facts=source_facts)
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
            save_script_cache(topic, duration, script, subject=subject, source_text=source_text)
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

    # ffprobe audio header and duration verification
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=codec_name",
            "-of", "json", str(audio_file)
        ]
        probe_res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_meta = json.loads(probe_res.stdout)
        dur = float(probe_meta.get("format", {}).get("duration", 0.0))
        if dur <= 0:
            stage_error("AUDIO", f"ffprobe verified duration is non-positive ({dur}s).")
    except Exception as exc:
        stage_error("AUDIO", f"ffprobe audio header verification failed: {exc}")

    stage_success(
        "AUDIO",
        f"Audio generated: {audio_file.name} ({dur:.2f}s, {audio_file.stat().st_size:,} bytes)"
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


def build_final_payload(
    script,
    timed_scenes,
    words,
    run_id: str,
    source_facts=None,
    evidence_pack=None,
    selected_workflow=None,
    validation_report=None,
    project_profile=None,
):
    """
    Build the exact top-level object expected by Remotion/CodingShort.jsx.
    """

    payload = {
        "title": script.get("title", ""),
        "topic": script.get("topic", script.get("title", "")),
        "subject": script.get("subject", "code"),
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
    if source_facts:
        payload["source_facts"] = source_facts
    if evidence_pack:
        payload["evidence_pack"] = evidence_pack.model_dump() if hasattr(evidence_pack, "model_dump") else evidence_pack
    if selected_workflow:
        payload["workflow"] = selected_workflow.model_dump() if hasattr(selected_workflow, "model_dump") else selected_workflow
    if validation_report:
        payload["validation_report"] = validation_report.model_dump() if hasattr(validation_report, "model_dump") else validation_report
    if project_profile:
        payload["project_profile"] = project_profile

    # Attach Brand and Render Profile tokens
    brand_cfg = load_brand_config(project_profile or {})
    payload["brand"] = brand_cfg.model_dump()
    if isinstance(project_profile, dict) and "render_profile" in project_profile:
        payload["render_profile"] = project_profile["render_profile"]

    return payload


def write_data_file(payload, data_file: Path):
    data_file.parent.mkdir(parents=True, exist_ok=True)

    # Apply deterministic auto-healing on timing & monotonicity bounds
    payload, was_healed = auto_heal_timeline_payload(payload)
    if was_healed:
        log("🩹 Applied deterministic auto-healing to timeline payload before write.")

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
        default=None,
        help="Topic for the educational short.",
    )

    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Path to project profile JSON file (e.g. projects/project_profile.json).",
    )

    parser.add_argument(
        "--length",
        type=int,
        choices=[15, 30, 35, 60],
        default=60,
        help="Video target length in seconds.",
    )

    parser.add_argument(
        "--subject",
        type=str,
        choices=["auto", "code", "devtools", "math", "physics", "systems", "ml", "chemistry", "quantum_physics", "mechanics", "electrical"],
        default="auto",
        help="Subject domain for video.",
    )

    parser.add_argument(
        "--source-file",
        type=str,
        default=None,
        help="Path to source documentation, README, changelog, or code snippet.",
    )

    parser.add_argument(
        "--source-url",
        type=str,
        default=None,
        help="Public documentation or GitHub README URL to ingest.",
    )

    parser.add_argument(
        "--source-text",
        type=str,
        default=None,
        help="Raw source markdown or code snippet text.",
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
        "--mock",
        action="store_true",
        help="Bypass Gemini API calls and load pre-validated mock script from mock library.",
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

    topic = (args.topic or "").strip()
    project_profile: Dict[str, Any] = {}
    sources: List[Dict[str, Any]] = []
    evidence_pack = None
    selected_workflow = None
    val_report = None

    if args.project:
        proj_path = Path(args.project).resolve()
        if not proj_path.exists():
            stage_error("PIPELINE", f"Project configuration file not found: {proj_path}")
        with open(proj_path, "r", encoding="utf-8") as f:
            proj_data = json.load(f)
        project_profile = dict(proj_data.get("project_profile", proj_data))
        if "render_profile" in proj_data and "render_profile" not in project_profile:
            project_profile["render_profile"] = proj_data["render_profile"]
        if "brand" in proj_data and "brand" not in project_profile:
            project_profile["brand"] = proj_data["brand"]
        topic = topic or project_profile.get("topic") or project_profile.get("product") or "Technical Feature"
        if args.subject == "auto" and project_profile.get("subject"):
            args.subject = project_profile.get("subject")
        if args.length == 60 and project_profile.get("duration_target_seconds"):
            args.length = int(project_profile.get("duration_target_seconds"))
        sources = project_profile.get("sources", [])

    if not topic:
        stage_error("DIRECTOR", "Either --topic or --project is required.")

    source_text = ""
    source_facts = {}
    if not args.project and (args.source_file or args.source_url or args.source_text):
        stage_start("INGESTION", "Loading and parsing customer documentation / code source...")
        try:
            try:
                from engine.ingestion.source_loader import load_source_content, extract_source_facts, format_source_summary
            except ImportError:
                from ingestion.source_loader import load_source_content, extract_source_facts, format_source_summary

            source_text = load_source_content(
                source_file=args.source_file,
                source_url=args.source_url,
                source_text=args.source_text,
            )
            source_facts = extract_source_facts(source_text) if source_text else {}
            summary_str = format_source_summary(source_facts)
            stage_success("INGESTION", f"Source ingested: {summary_str}")
        except Exception as exc:
            stage_error("INGESTION", f"Failed to ingest source material: {exc}")

    # ---------------------------------------------------------------
    # Environment check
    # ---------------------------------------------------------------

    if not args.mock and not os.getenv("GEMINI_API_KEY") and not os.getenv("GEMINI_API_KEYS"):
        stage_error(
            "DIRECTOR",
            "GEMINI_API_KEY environment variable is not set.\n\n"
            "Set it before running the engine, or pass --mock for offline mode.\n"
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
    print(f"Mode:     {'MOCK (OFFLINE)' if args.mock else 'LIVE API'}")
    print(f"Project:  {args.project or 'None'}")
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
        # Step 1 & 2 — Ingestion, Evidence Extraction & Planning
        # ---------------------------------------------------------------

        # Unified Evidence Pipeline Path for all CLI entry points
        if not project_profile:
            project_profile = {
                "product": topic.split()[0] if topic else "Developer Tool",
                "audience": "Developers & Engineers",
                "goal": f"Explain {topic} in {args.length} seconds",
                "duration_target_seconds": args.length,
                "topic": topic or "Developer Workflow",
                "subject": args.subject or "code",
                "sources": sources if sources else [
                    {
                        "url": args.source_url or "https://docs.example.com",
                        "local_file": args.source_file,
                        "title": topic,
                    }
                ],
            }

        stage_start("INGESTION", f"Extracting EvidencePack from official sources for {project_profile.get('product', 'project')}...")
        evidence_pack = extract_evidence_pack(sources, project_profile=project_profile, mock=args.mock)
        with open(run_dir / "evidence_pack.json", "w", encoding="utf-8") as f:
            json.dump(evidence_pack.model_dump(), f, indent=2)
        stage_success("INGESTION", f"Extracted {len(evidence_pack.records)} atomic evidence records -> {run_dir}/evidence_pack.json")

        stage_start("WORKFLOW", "Scoring candidate developer workflows across 6 criteria...")
        wf_res = select_best_workflow(evidence_pack, project_profile=project_profile, mock=args.mock)
        selected_workflow = wf_res.selected_workflow
        with open(run_dir / "workflow_candidates.json", "w", encoding="utf-8") as f:
            json.dump(wf_res.model_dump(), f, indent=2)
        stage_success("WORKFLOW", f"Selected workflow '{selected_workflow.title}' (Score: {selected_workflow.scores.total_score}/60)")

        stage_start("SCENE_PLAN", "Generating evidence-linked 5-beat scene plan...")
        scene_plan = plan_scenes(selected_workflow, evidence_pack, duration_target=args.length, mock=args.mock)
        with open(run_dir / "scene_plan.json", "w", encoding="utf-8") as f:
            json.dump(scene_plan.model_dump(), f, indent=2)
        stage_success("SCENE_PLAN", f"Generated {len(scene_plan.scenes)} evidence-linked scenes -> {run_dir}/scene_plan.json")

        stage_start("EVIDENCE_GATE", "Validating 100% claim coverage before timeline assembly...")
        val_report = validate_evidence_and_plan(evidence_pack, scene_plan)
        with open(run_dir / "validation_report.json", "w", encoding="utf-8") as f:
            json.dump(val_report.model_dump(), f, indent=2)
        if not val_report.passed:
            stage_error("EVIDENCE_GATE", f"Evidence validation failed: {val_report.checks}")
        stage_success("EVIDENCE_GATE", f"Verified 100% claim backing across all {val_report.total_claims} scenes.")

        script = scene_plan.to_director_script()

        # ---------------------------------------------------------------
        # Step 2 & 3 — Synthesize Per-Scene Audio & Master Concat
        # ---------------------------------------------------------------

        scenes_raw = script.get("scenes", [])
        stage_start("AUDIO", f"Synthesizing per-scene neural audio for {len(scenes_raw)} scenes...")
        from engine.audio.scene_audio import synthesize_scene_audio_async, concatenate_scene_audios
        from engine.timeline.timeline_mapper import map_scene_timeline, chunk_caption_words

        scene_audio_items = []
        for s_idx, sc in enumerate(scenes_raw):
            sid = sc.get("scene_id", s_idx + 1)
            s_text = sc.get("spoken_text") or sc.get("narration") or "Next concept."
            s_dir = run_dir / "scenes" / str(sid)
            s_wav, s_dur, s_words = asyncio.run(
                synthesize_scene_audio_async(
                    narration_text=s_text,
                    scene_dir=s_dir,
                    revision=1,
                )
            )
            scene_audio_items.append({
                "scene_id": sid,
                "audio_path": s_wav,
                "duration": s_dur,
                "words": s_words,
            })

        # Concatenate audio into master audio.wav and audio.mp3
        master_audio_wav = run_dir / "audio.wav"
        updated_scenes_meta, master_words = concatenate_scene_audios(
            scene_items=scene_audio_items,
            output_master_audio=master_audio_wav,
        )
        audio_file = run_dir / "audio.mp3"
        stage_success("AUDIO", f"Master audio generated: {audio_file.name} ({updated_scenes_meta[-1]['end_time']:.2f}s)")

        # ---------------------------------------------------------------
        # Step 4 — Deterministic Timeline Mapping & Subtitle Chunking
        # ---------------------------------------------------------------

        stage_start("TIMELINE", "Mapping scene timeline and chunking subtitles...")
        timed_scenes, words, caption_chunks = map_scene_timeline(
            scenes=scenes_raw,
            scene_audio_results=scene_audio_items,
            domain=script.get("subject") or script.get("domain") or "code",
            fps=30,
        )
        stage_success("TIMELINE", f"Timeline mapped ({len(timed_scenes)} scenes, {len(words)} words, {len(caption_chunks)} caption chunks)")

        # ---------------------------------------------------------------
        # Step 5 — Final JSON Payload & Atomic Write
        # ---------------------------------------------------------------

        payload = build_final_payload(
            script=script,
            timed_scenes=timed_scenes,
            words=words,
            run_id=run_id,
            source_facts=source_facts,
            evidence_pack=evidence_pack,
            selected_workflow=selected_workflow,
            validation_report=val_report,
            project_profile=project_profile,
        )
        payload["caption_chunks"] = caption_chunks

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
        expected_audio_rel_wav = f"runs/{run_id}/audio.wav"
        if verification_data.get("audio_file") not in {expected_audio_rel, expected_audio_rel_wav}:
            stage_error(
                "TIMELINE",
                f"Final JSON audio_file does not match expected path:\n"
                f"Expected: {expected_audio_rel!r}\n"
                f"Got:      {verification_data.get('audio_file')!r}"
            )
    except BaseException as exc:
        write_reflection_error(run_dir, stage="GENERATION", message=str(exc))
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