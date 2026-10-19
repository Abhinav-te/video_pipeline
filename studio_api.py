"""
studio_api.py

Local Production Studio Control Room Backend API (Checkpoint 04).
FastAPI control server wrapping:
- Project exploration & asset streaming (GET /api/projects, GET /api/projects/{run_id})
- Pipeline generation with job tracking (POST /api/projects/generate)
- Surgical Scene Revision Mode A (POST /api/projects/{run_id}/scenes/{scene_id}/revise-visual)
- Surgical Scene Revision Mode B (POST /api/projects/{run_id}/scenes/{scene_id}/revise-narration)
- Non-destructive snapshot rollback (POST /api/projects/{run_id}/restore/{rev_id})
- Production export to video/out (POST /api/projects/{run_id}/export)
- Static streaming for run audio, Manim assets, scene segments, and master MP4s.
"""

import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path Resolution (Repository-Relative)
# ---------------------------------------------------------------------------
REPO_DIR = Path(__file__).resolve().parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"
PUBLIC_DIR = VIDEO_DIR / "public"
RUNS_DIR = PUBLIC_DIR / "runs"
OUT_DIR = VIDEO_DIR / "out"
STUDIO_UI_DIR = REPO_DIR / "studio_ui"

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from engine.pipeline.manifest import (
    load_manifest,
    save_manifest,
    archive_revision_snapshot,
    init_manifest,
    compute_visual_hash,
    compute_audio_hash,
)
from engine.revise import execute_revision, parse_scene_id

# ---------------------------------------------------------------------------
# FastAPI App Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Video Pipeline Engine — Local Production Studio",
    description="Control Room API for automated generation, surgical scene revision, and snapshot rollback.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)
STUDIO_UI_DIR.mkdir(parents=True, exist_ok=True)

# Mount static asset directories so browser can directly stream audio/video
app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
app.mount("/out", StaticFiles(directory=str(OUT_DIR)), name="out")
if STUDIO_UI_DIR.exists():
    app.mount("/studio_ui", StaticFiles(directory=str(STUDIO_UI_DIR)), name="studio_ui")

# In-memory background jobs registry
JOBS: Dict[str, Dict[str, Any]] = {}
TERMINAL_LOGS: List[str] = []
MAX_TERMINAL_LOGS = 200


def log_terminal(msg: str):
    """Appends to the in-memory terminal log ring buffer."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    TERMINAL_LOGS.append(formatted)
    if len(TERMINAL_LOGS) > MAX_TERMINAL_LOGS:
        del TERMINAL_LOGS[: len(TERMINAL_LOGS) - MAX_TERMINAL_LOGS]


# ---------------------------------------------------------------------------
# Pydantic Request / Response Models
# ---------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    topic: str = Field(..., description="Topic of the video short")
    subject: str = Field("auto", description="Domain: math, code, physics, chemistry, quantum_physics, mechanics, electrical, systems, ml, devtools, auto")
    length: int = Field(60, description="Target duration in seconds (15, 30, 35, 60)")
    mock: bool = Field(False, description="Use pre-validated mock script")
    fast_test: bool = Field(False, description="Quick 90-frame test render")
    frames: Optional[str] = Field(None, description="Remotion frame range (e.g. 0-29)")
    source_text: Optional[str] = Field(None, description="Raw markdown, code, documentation, or changelog text")
    source_file: Optional[str] = Field(None, description="Path to source documentation file")
    source_url: Optional[str] = Field(None, description="Public documentation or GitHub README URL to ingest")
    sync: bool = Field(False, description="Run synchronously instead of background thread")


class ReviseVisualRequest(BaseModel):
    visual_type: Optional[str] = Field(None, description="Mode A: New visual type for scene")
    title: Optional[str] = Field(None, description="Mode A: New scene title")
    sub_mode: Optional[str] = Field(None, description="Mode A: Sub-mode identifier")
    visual_props: Optional[Dict[str, Any]] = Field(None, description="Mode A: Visual property dictionary")


class ReviseNarrationRequest(BaseModel):
    narration: str = Field(..., description="Mode B: New spoken narration for scene")


class RestoreRequest(BaseModel):
    pass


class ExportRequest(BaseModel):
    custom_filename: Optional[str] = Field(None, description="Custom filename for exported video")


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def resolve_master_video(run_id: str, current_rev: int = 1) -> Tuple[Optional[str], Optional[Path], int]:
    """
    Finds the active master video for a run.
    Returns (url_path, absolute_file_path, size_bytes).
    """
    run_dir = RUNS_DIR / run_id

    # 1. Check video/out for versioned or unversioned MP4
    candidates = [
        (OUT_DIR / f"{run_id}_v{current_rev}.mp4", f"/out/{run_id}_v{current_rev}.mp4"),
        (OUT_DIR / f"{run_id}.mp4", f"/out/{run_id}.mp4"),
        (run_dir / "output.mp4", f"/public/runs/{run_id}/output.mp4"),
        (run_dir / "revisions" / f"rev_{current_rev:03d}" / "output.mp4", f"/public/runs/{run_id}/revisions/rev_{current_rev:03d}/output.mp4"),
    ]

    for p, url in candidates:
        if p.exists() and p.stat().st_size > 1024:
            return url, p, p.stat().st_size

    # 2. Check any revisions snapshot with output.mp4 (latest first)
    rev_dir = run_dir / "revisions"
    if rev_dir.exists():
        rev_subdirs = sorted([d for d in rev_dir.iterdir() if d.is_dir() and d.name.startswith("rev_")], reverse=True)
        for d in rev_subdirs:
            snap_vid = d / "output.mp4"
            if snap_vid.exists() and snap_vid.stat().st_size > 1024:
                return f"/public/runs/{run_id}/revisions/{d.name}/output.mp4", snap_vid, snap_vid.stat().st_size

    return None, None, 0


def get_project_state(run_id: str) -> Dict[str, Any]:
    """
    Constructs the complete project state dictionary for run_id.
    """
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project '{run_id}' not found.")

    data_file = run_dir / "data.json"
    manifest_file = run_dir / "manifest.json"

    data_payload: Dict[str, Any] = {}
    if data_file.exists():
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data_payload = json.load(f)
        except Exception:
            pass

    manifest: Dict[str, Any] = {}
    if manifest_file.exists():
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            pass

    curr_rev = int(manifest.get("revision", 1))
    topic = data_payload.get("topic") or data_payload.get("title") or run_id
    subject = data_payload.get("subject") or data_payload.get("domain") or "auto"
    total_duration = round(float(data_payload.get("duration", 0.0)), 2)

    scenes = data_payload.get("scenes", [])
    if not total_duration and scenes:
        try:
            total_duration = round(sum(float(s.get("duration", 0.0)) for s in scenes), 2)
        except Exception:
            pass

    # Master Video URL
    master_video_url, master_video_path, master_video_size = resolve_master_video(run_id, curr_rev)

    # Master Audio URL
    master_audio_path = run_dir / "audio.mp3"
    master_audio_url = f"/public/runs/{run_id}/audio.mp3" if master_audio_path.exists() else None

    # Available Snapshots in revisions/
    snapshots: List[Dict[str, Any]] = []
    rev_parent = run_dir / "revisions"
    if rev_parent.exists():
        for d in sorted([p for p in rev_parent.iterdir() if p.is_dir() and p.name.startswith("rev_")]):
            rev_num_match = re.search(r"rev_(\d+)", d.name)
            rev_num = int(rev_num_match.group(1)) if rev_num_match else 0
            has_vid = (d / "output.mp4").exists()
            has_data = (d / "data.json").exists()
            has_man = (d / "manifest.json").exists()
            snap_time = datetime.datetime.fromtimestamp(d.stat().st_mtime, tz=datetime.timezone.utc).isoformat()
            action_desc = f"Revision {rev_num}"
            if has_man:
                try:
                    with open(d / "manifest.json", "r", encoding="utf-8") as mf:
                        m_data = json.load(mf)
                        for h in m_data.get("history", []):
                            if h.get("revision") == rev_num:
                                action_desc = h.get("action", action_desc)
                except Exception:
                    pass

            snapshots.append({
                "rev_id": d.name,
                "revision": rev_num,
                "action": action_desc,
                "has_video": has_vid,
                "has_data": has_data,
                "has_manifest": has_man,
                "video_url": f"/public/runs/{run_id}/revisions/{d.name}/output.mp4" if has_vid else None,
                "created_at": snap_time,
            })

    # Resolved Scene Assets
    resolved_scenes: List[Dict[str, Any]] = []
    manifest_scenes = manifest.get("scenes", {})
    master_words = data_payload.get("words", [])

    for idx, sc in enumerate(scenes):
        sid = parse_scene_id(sc.get("scene_id", idx + 1))
        sid_str = str(sid)
        m_sc = manifest_scenes.get(sid_str, {})

        st = float(sc.get("start_time", 0.0))
        dur = float(sc.get("duration", (sc.get("end_time", st + 4.0) - st)))
        et = float(sc.get("end_time", round(st + dur, 3)))

        # Segment video URL
        rel_seg = m_sc.get("segment_video") or f"segments/scene_{sid}_v{m_sc.get('revision', 1)}.mp4"
        seg_file = run_dir / rel_seg
        has_seg = seg_file.exists() and seg_file.stat().st_size > 1024
        seg_url = f"/public/runs/{run_id}/{rel_seg}" if has_seg else None

        # Manim Asset URL
        rel_manim = m_sc.get("manim_asset") or sc.get("manim_asset_url") or sc.get("manim_video_src")
        has_manim = False
        manim_url = None
        if rel_manim:
            if rel_manim.startswith("runs/"):
                cand = PUBLIC_DIR / rel_manim
            elif rel_manim.startswith("/"):
                cand = Path(rel_manim)
            else:
                cand = run_dir / rel_manim
            if cand.exists() and cand.stat().st_size > 1024:
                has_manim = True
                try:
                    rel_to_pub = cand.relative_to(PUBLIC_DIR)
                    manim_url = f"/public/{rel_to_pub.as_posix()}"
                except ValueError:
                    manim_url = str(cand)

        # Audio URL
        rel_audio = m_sc.get("audio_file") or f"scenes/{sid}/audio_v1.mp3"
        audio_file = run_dir / rel_audio
        has_aud = audio_file.exists() and audio_file.stat().st_size > 512
        audio_url = f"/public/runs/{run_id}/{rel_audio}" if has_aud else None

        # Scene Words Alignment
        sc_words = []
        for w in master_words:
            w_st = float(w.get("start", 0.0))
            if st - 0.05 <= w_st < et + 0.05:
                sc_words.append({
                    "word": w.get("word", ""),
                    "start": round(w_st, 2),
                    "end": round(float(w.get("end", w_st + 0.3)), 2),
                })

        resolved_scenes.append({
            "scene_id": sid,
            "title": sc.get("title", f"Scene {sid}"),
            "visual_type": sc.get("visual_type") or sc.get("scene_type") or "code_reveal",
            "start_time": round(st, 2),
            "end_time": round(et, 2),
            "duration": round(dur, 2),
            "spoken_text": sc.get("spoken_text") or sc.get("narration") or "",
            "visual_hash": m_sc.get("visual_hash") or compute_visual_hash(sc, duration=dur),
            "audio_hash": m_sc.get("audio_hash") or compute_audio_hash(sc.get("spoken_text") or sc.get("narration") or ""),
            "segment_video_url": seg_url,
            "has_segment_video": has_seg,
            "manim_asset_url": manim_url,
            "has_manim_asset": has_manim,
            "audio_url": audio_url,
            "has_audio": has_aud,
            "words": sc_words,
            "raw_scene": sc,
        })

    diagnostics = {
        "has_master_video": bool(master_video_url),
        "master_video_size": master_video_size,
        "scenes_count": len(scenes),
        "snapshots_count": len(snapshots),
        "manim_verified": any(s["has_manim_asset"] for s in resolved_scenes),
        "validation_status": "OK" if master_video_url else "NEEDS_RENDER",
    }

    return {
        "run_id": run_id,
        "topic": topic,
        "subject": subject,
        "duration": total_duration,
        "current_revision": curr_rev,
        "updated_at": manifest.get("updated_at") or datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "master_video_url": master_video_url,
        "master_audio_url": master_audio_url,
        "data": data_payload,
        "manifest": manifest,
        "snapshots": snapshots,
        "scenes_resolved": resolved_scenes,
        "diagnostics": diagnostics,
        "source_facts": data_payload.get("source_facts", {}),
    }


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.get("/", summary="Serve Production Studio UI")
def serve_ui():
    """Serves the local Production Studio Single Page Control Room."""
    index_file = STUDIO_UI_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "studio_ui/index.html not found. Run generation to initialize UI."},
        )
    return FileResponse(index_file)


@app.get("/api/health", summary="Studio Health Check")
def health_check():
    return {
        "status": "ok",
        "engine": "Video Pipeline Engine (Checkpoint 04)",
        "server_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "runs_count": len([d for d in RUNS_DIR.iterdir() if d.is_dir()]),
    }


@app.get("/api/terminal-logs", summary="Get Live Studio Terminal Logs")
def get_terminal_logs():
    return {"logs": TERMINAL_LOGS}


@app.get("/api/visual-types", summary="Get Supported Scene Visual Types")
def get_visual_types():
    return {
        "visual_types": [
            {"id": "code_reveal", "label": "Code Reveal (Spotlight)", "category": "code"},
            {"id": "code_transform", "label": "Code Transform / Diff", "category": "code"},
            {"id": "terminal", "label": "Terminal CLI Simulator", "category": "code"},
            {"id": "diagram", "label": "Architecture Flow & API Payloads", "category": "systems"},
            {"id": "comparison", "label": "Editorial Comparison", "category": "dual"},
            {"id": "manim_scene", "label": "Manim Math/Vector Engine", "category": "math"},
            {"id": "math_equation", "label": "LaTeX Math Derivation", "category": "math"},
            {"id": "function_graph", "label": "Function Graph Plotter", "category": "math"},
            {"id": "quantum_sim", "label": "Quantum Wavepacket Simulator", "category": "physics"},
            {"id": "mechanics_fbd", "label": "Mechanics Free Body Diagram", "category": "physics"},
            {"id": "electrical_grid", "label": "Electrical Grid & Phasor", "category": "systems"},
            {"id": "chemistry_reaction", "label": "Chemistry Reaction Pathway", "category": "chemistry"},
            {"id": "bento_grid", "label": "Bento Metric Grid", "category": "general"},
            {"id": "concept_hero", "label": "Concept Hero Showcase", "category": "general"},
        ]
    }


@app.get("/api/projects", summary="List All Video Projects")
def list_projects():
    """
    Lists all run directories in video/public/runs/ sorted newest-first.
    Returns: [{ run_id, topic, subject, duration, scene_count, current_revision, updated_at, has_output }]
    """
    if not RUNS_DIR.exists():
        return []

    projects: List[Dict[str, Any]] = []

    for d in RUNS_DIR.iterdir():
        if not d.is_dir():
            continue

        run_id = d.name
        data_file = d / "data.json"
        manifest_file = d / "manifest.json"

        # Require data.json or manifest.json to consider it a valid run project
        if not data_file.exists() and not manifest_file.exists():
            continue

        data_payload: Dict[str, Any] = {}
        if data_file.exists():
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data_payload = json.load(f)
            except Exception:
                pass

        manifest: Dict[str, Any] = {}
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                pass

        topic = data_payload.get("topic") or data_payload.get("title") or run_id
        subject = data_payload.get("subject") or data_payload.get("domain") or "auto"
        scenes = data_payload.get("scenes", [])
        scene_count = len(scenes)

        duration = round(float(data_payload.get("duration", 0.0)), 2)
        if not duration and scenes:
            try:
                duration = round(sum(float(s.get("duration", 0.0)) for s in scenes), 2)
            except Exception:
                pass

        current_rev = int(manifest.get("revision", 1))

        # Check output video existence
        has_output = False
        _, master_vid_path, _ = resolve_master_video(run_id, current_rev)
        if master_vid_path is not None:
            has_output = True

        # Updated timestamp
        updated_at = manifest.get("updated_at")
        if not updated_at:
            mtime = d.stat().st_mtime
            updated_at = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).isoformat()

        projects.append({
            "run_id": run_id,
            "topic": topic,
            "subject": subject,
            "duration": duration,
            "scene_count": scene_count,
            "current_revision": current_rev,
            "updated_at": updated_at,
            "has_output": has_output,
        })

    # Sort newest-first by updated_at or directory mtime
    projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return projects


@app.get("/api/projects/{run_id}", summary="Get Full Project State")
def get_project(run_id: str):
    """
    Returns full project state (data.json, manifest.json, snapshots, and resolved URLs).
    """
    return get_project_state(run_id)


def _run_generator_job(job_id: str, run_id: str, req: GenerateRequest):
    """Worker function for async generation."""
    python_exec = ENGINE_DIR / ".venv" / "bin" / "python"
    if not python_exec.exists():
        python_exec = Path(sys.executable)

    gen_and_render_script = REPO_DIR / "generate_and_render.py"

    cmd = [
        str(python_exec),
        str(gen_and_render_script),
        "--topic", req.topic,
        "--subject", req.subject,
        "--length", str(req.length),
        "--run-id", run_id,
    ]
    if req.mock:
        cmd.append("--mock")
    if req.fast_test:
        cmd.append("--fast-test")
    if req.frames:
        cmd.extend(["--frames", req.frames])
    if req.source_text:
        cmd.extend(["--source-text", req.source_text])
    if req.source_file:
        cmd.extend(["--source-file", req.source_file])
    if req.source_url:
        cmd.extend(["--source-url", req.source_url])

    log_terminal(f"🚀 Starting generation job {job_id} for '{req.topic}' -> {run_id}")
    JOBS[job_id]["status"] = "running"

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in proc.stdout:
            cleaned = line.strip()
            if cleaned:
                log_terminal(f"[{run_id}] {cleaned}")
                JOBS[job_id]["logs"].append(cleaned)

        proc.wait()
        if proc.returncode == 0:
            JOBS[job_id]["status"] = "completed"
            log_terminal(f"✅ Generation job {job_id} completed successfully for {run_id}")
        else:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = f"Process exited with code {proc.returncode}"
            log_terminal(f"❌ Generation job {job_id} failed with exit code {proc.returncode}")
    except Exception as exc:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(exc)
        log_terminal(f"❌ Generation job {job_id} exception: {exc}")


@app.post("/api/projects/generate", summary="Generate New Video Project")
def generate_project(req: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Accepts { topic, subject, length, mock }, invokes generate_and_render.py,
    and returns { run_id, job_id, status }.
    """
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    run_id = f"run_{timestamp}_{short_id}"
    job_id = f"job_{run_id}"

    JOBS[job_id] = {
        "job_id": job_id,
        "run_id": run_id,
        "status": "queued",
        "topic": req.topic,
        "subject": req.subject,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "logs": [],
        "error": None,
    }

    if req.sync:
        _run_generator_job(job_id, run_id, req)
        return {
            "run_id": run_id,
            "job_id": job_id,
            "status": JOBS[job_id]["status"],
            "logs": JOBS[job_id]["logs"],
            "error": JOBS[job_id]["error"],
        }
    else:
        thread = threading.Thread(target=_run_generator_job, args=(job_id, run_id, req), daemon=True)
        thread.start()
        return {
            "run_id": run_id,
            "job_id": job_id,
            "status": "running",
            "message": "Generation started in background.",
        }


@app.get("/api/jobs/{job_id}", summary="Check Generation Job Status")
def get_job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return JOBS[job_id]


@app.post("/api/projects/{run_id}/scenes/{scene_id}/revise-visual", summary="Mode A: Visual-Only Scene Revision")
def revise_scene_visual(run_id: str, scene_id: Union[int, str], req: ReviseVisualRequest):
    """
    Mode A: Accepts { visual_type, title, sub_mode, visual_props },
    calls engine/revise.py (Mode A) to re-render ONLY scene_id and stitch master MP4,
    returning updated project state.
    """
    has_changes = bool(req.visual_type or req.title or req.sub_mode or req.visual_props)
    if not has_changes:
        raise HTTPException(status_code=400, detail="Mode A requires at least one of: visual_type, title, sub_mode, visual_props.")

    v_props = req.visual_props.copy() if req.visual_props else {}
    if req.sub_mode:
        v_props["sub_mode"] = req.sub_mode

    v_json_str = json.dumps(v_props) if v_props else None

    log_terminal(f"⚡ [Mode A] Revising visual for {run_id} Scene {scene_id} (type='{req.visual_type}', title='{req.title}')")

    try:
        execute_revision(
            run_id=run_id,
            target_scene_id=scene_id,
            set_visual_type=req.visual_type,
            set_title=req.title,
            set_visual_json=v_json_str,
            set_narration=None,
        )
        log_terminal(f"✅ [Mode A] Scene {scene_id} revision complete.")
    except Exception as exc:
        log_terminal(f"❌ [Mode A] Scene {scene_id} revision failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Revision failed: {exc}")

    return get_project_state(run_id)


@app.post("/api/projects/{run_id}/scenes/{scene_id}/revise-narration", summary="Mode B: Narration & Timing Revision")
def revise_scene_narration(run_id: str, scene_id: Union[int, str], req: ReviseNarrationRequest):
    """
    Mode B: Accepts { narration },
    calls engine/revise.py (Mode B) to regenerate TTS + Whisper alignment ONLY for scene_id,
    shift downstream timings, re-render scene_id, stitch master MP4, and return updated project state.
    """
    if not req.narration or not req.narration.strip():
        raise HTTPException(status_code=400, detail="Narration cannot be empty for Mode B revision.")

    log_terminal(f"🎙️ [Mode B] Revising narration for {run_id} Scene {scene_id} ('{req.narration[:40]}...')")

    try:
        execute_revision(
            run_id=run_id,
            target_scene_id=scene_id,
            set_visual_type=None,
            set_title=None,
            set_visual_json=None,
            set_narration=req.narration.strip(),
        )
        log_terminal(f"✅ [Mode B] Scene {scene_id} narration revision complete.")
    except Exception as exc:
        log_terminal(f"❌ [Mode B] Scene {scene_id} narration revision failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Revision failed: {exc}")

    return get_project_state(run_id)


@app.post("/api/projects/{run_id}/restore/{rev_id}", summary="Non-Destructive Snapshot Rollback")
def restore_project_snapshot(run_id: str, rev_id: str):
    """
    Non-destructively restores snapshot revisions/{rev_id} as the new active state
    (archiving current state first) so no good work is ever lost.
    """
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project '{run_id}' not found.")

    snap_dir = run_dir / "revisions" / rev_id
    if not snap_dir.exists():
        raise HTTPException(status_code=404, detail=f"Snapshot '{rev_id}' not found in revisions/ for project '{run_id}'.")

    snap_data_file = snap_dir / "data.json"
    snap_manifest_file = snap_dir / "manifest.json"

    if not snap_data_file.exists() or not snap_manifest_file.exists():
        raise HTTPException(status_code=400, detail=f"Snapshot '{rev_id}' is missing data.json or manifest.json.")

    with open(snap_data_file, "r", encoding="utf-8") as f:
        snap_data = json.load(f)
    with open(snap_manifest_file, "r", encoding="utf-8") as f:
        snap_manifest = json.load(f)

    # 1. Archive current active state first before overwriting
    current_data_file = run_dir / "data.json"
    current_manifest_file = run_dir / "manifest.json"
    current_manifest = load_manifest(run_dir) or {}
    curr_rev = current_manifest.get("revision", 1)

    if current_data_file.exists():
        with open(current_data_file, "r", encoding="utf-8") as f:
            current_data = json.load(f)
        _, current_master_mp4, _ = resolve_master_video(run_id, curr_rev)
        archive_revision_snapshot(
            run_dir=run_dir,
            revision=curr_rev,
            data_payload=current_data,
            manifest_data=current_manifest,
            output_mp4=current_master_mp4,
        )

    # 2. Compute new revision number (strictly higher than current and all existing snapshots)
    existing_rev_nums = [curr_rev]
    for d in (run_dir / "revisions").iterdir():
        if d.is_dir():
            m = re.search(r"rev_(\d+)", d.name)
            if m:
                existing_rev_nums.append(int(m.group(1)))
    new_rev = max(existing_rev_nums) + 1
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    log_terminal(f"⏮️ Restoring snapshot {rev_id} -> New Revision {new_rev} for project '{run_id}'")

    # 3. Update snapshot manifest to become the new revision
    snap_manifest["revision"] = new_rev
    snap_manifest["updated_at"] = now_iso
    if "history" not in snap_manifest:
        snap_manifest["history"] = []
    snap_manifest["history"].append({
        "revision": new_rev,
        "timestamp": now_iso,
        "action": f"Restored snapshot {rev_id}",
    })

    # 4. Save restored data.json and manifest.json to run_dir
    with open(run_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(snap_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    save_manifest(snap_manifest, run_dir)

    # 5. Restore snapshot output video if present
    snap_vid = snap_dir / "output.mp4"
    if snap_vid.exists():
        dest_out = OUT_DIR / f"{run_id}_v{new_rev}.mp4"
        shutil.copyfile(snap_vid, dest_out)
        shutil.copyfile(snap_vid, run_dir / "output.mp4")
        log_terminal(f"🎬 Restored master video to {dest_out.name}")

    # 6. Archive this newly restored state as rev_<new_rev>
    archive_revision_snapshot(
        run_dir=run_dir,
        revision=new_rev,
        data_payload=snap_data,
        manifest_data=snap_manifest,
        output_mp4=snap_vid if snap_vid.exists() else None,
    )

    log_terminal(f"✅ Successfully restored {rev_id} as Revision {new_rev} for {run_id}.")
    return get_project_state(run_id)


@app.post("/api/projects/{run_id}/export", summary="Export Verified Final MP4")
def export_project(run_id: str, req: ExportRequest):
    """
    Copies current verified master MP4 to video/out/{custom_filename}.mp4
    and returns { download_url, filename, size_bytes }.
    """
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project '{run_id}' not found.")

    manifest = load_manifest(run_dir) or {}
    curr_rev = manifest.get("revision", 1)

    url, master_path, size = resolve_master_video(run_id, curr_rev)
    if not master_path or not master_path.exists():
        raise HTTPException(status_code=400, detail=f"No rendered master video found for project '{run_id}'.")

    if req.custom_filename and req.custom_filename.strip():
        clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", req.custom_filename.strip())
        if not clean_name.lower().endswith(".mp4"):
            clean_name += ".mp4"
    else:
        clean_name = f"{run_id}_final_v{curr_rev}.mp4"

    export_path = OUT_DIR / clean_name
    if master_path.resolve() != export_path.resolve():
        shutil.copyfile(master_path, export_path)

    log_terminal(f"📦 Exported {run_id} -> {export_path.name} ({export_path.stat().st_size:,} bytes)")

    return {
        "download_url": f"/out/{clean_name}",
        "filename": clean_name,
        "size_bytes": export_path.stat().st_size,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🎬 Starting Local Production Studio Control Room on http://localhost:{port}")
    uvicorn.run("studio_api:app", host="0.0.0.0", port=port, reload=True)
