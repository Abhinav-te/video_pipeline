"""
engine/pipeline/manifest.py

Dependency-Aware Artifact Manifest & Non-Destructive Revision Tracking (Checkpoint 02).
Tracks:
- Project revision (1, 2, ...)
- Per-scene visual_hash = sha256(visual_type + sub_mode + canonical_json(visual_props) + round(duration, 2))
- Per-scene audio_hash = sha256(narration.strip() + voice_id)
- Per-scene audio files: scenes/<scene_id>/audio_v<N>.mp3
- Per-scene video segments: segments/scene_<scene_id>_v<N>.mp4
- Per-scene Manim assets: assets/manim_<scene_id>_v<N>.mp4
- Non-destructive revision snapshots: revisions/rev_<NNN>/data.json & output.mp4
"""

import copy
import datetime
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

VISUAL_PROPS_KEYS = [
    "title",
    "display_text",
    "visual_type",
    "scene_type",
    "sub_mode",
    "steps",
    "equations",
    "functions",
    "curves",
    "matrix",
    "barrier_x",
    "comparison_sides",
    "problem_code",
    "solution_code",
    "problem_label",
    "solution_label",
    "code",
    "code_snippet",
    "focus_phrase",
    "emphasis_word",
    "concept_mode",
    "diagram_mode",
    "nodes",
    "edges",
    "cards",
    "manim_spec",
    "badge",
]


def canonical_json(obj: Any) -> str:
    """Serializes an object into deterministic JSON with sorted keys."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_visual_hash(scene: Dict[str, Any], duration: Optional[float] = None) -> str:
    """
    Computes visual_hash = sha256(visual_type + sub_mode + canonical_json(visual_props) + round(duration, 2))
    """
    v_type = str(scene.get("visual_type") or scene.get("scene_type") or "").strip().lower()
    sub_mode = str(scene.get("sub_mode") or "").strip().lower()

    if duration is None:
        dur = scene.get("duration")
        if dur is None:
            start = scene.get("start_time", 0.0)
            end = scene.get("end_time", 0.0)
            dur = max(0.0, float(end) - float(start))
        duration = float(dur)

    dur_rounded = round(float(duration), 2)

    props: Dict[str, Any] = {}
    for k in VISUAL_PROPS_KEYS:
        val = scene.get(k)
        if val is not None:
            props[k] = val

    payload = f"{v_type}:{sub_mode}:{canonical_json(props)}:{dur_rounded:.2f}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_audio_hash(narration: str, voice_id: str = "en-US-ChristopherNeural") -> str:
    """
    Computes audio_hash = sha256(narration.strip() + voice_id)
    """
    clean_text = (narration or "").strip()
    payload = f"{clean_text}:{voice_id.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_manifest_path(run_dir: Union[str, Path]) -> Path:
    return Path(run_dir) / "manifest.json"


def load_manifest(run_dir: Union[str, Path]) -> Optional[Dict[str, Any]]:
    m_path = get_manifest_path(run_dir)
    if not m_path.exists():
        return None
    try:
        with open(m_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def init_manifest(run_id: str, run_dir: Union[str, Path], initial_scenes: List[Dict[str, Any]], fps: int = 30) -> Dict[str, Any]:
    """
    Initializes a new manifest dictionary for revision 1.
    """
    run_dir = Path(run_dir)
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest: Dict[str, Any] = {
        "run_id": run_id,
        "revision": 1,
        "created_at": now_str,
        "updated_at": now_str,
        "fps": fps,
        "scenes": {},
        "history": [
            {
                "revision": 1,
                "timestamp": now_str,
                "action": "initial_render",
                "affected_scenes": [s.get("scene_id") for s in initial_scenes],
            }
        ],
    }

    for idx, sc in enumerate(initial_scenes):
        scene_id = sc.get("scene_id", idx + 1)
        dur = float(sc.get("duration", (sc.get("end_time", 0.0) - sc.get("start_time", 0.0))))
        start_t = float(sc.get("start_time", 0.0))
        end_t = float(sc.get("end_time", start_t + dur))

        start_frame = int(round(start_t * fps))
        duration_frames = max(1, int(round(dur * fps)))

        narration = sc.get("spoken_text") or sc.get("narration") or ""
        voice_id = sc.get("voice_id") or "en-US-ChristopherNeural"

        v_hash = compute_visual_hash(sc, duration=dur)
        a_hash = compute_audio_hash(narration, voice_id=voice_id)

        manim_asset = sc.get("manim_asset_url") or sc.get("manim_video_src")

        manifest["scenes"][str(scene_id)] = {
            "scene_id": scene_id,
            "revision": 1,
            "visual_hash": v_hash,
            "audio_hash": a_hash,
            "audio_file": f"scenes/{scene_id}/audio_v1.mp3",
            "segment_video": f"segments/scene_{scene_id}_v1.mp4",
            "manim_asset": manim_asset,
            "start_time": round(start_t, 3),
            "end_time": round(end_t, 3),
            "duration": round(dur, 3),
            "start_frame": start_frame,
            "duration_frames": duration_frames,
        }

    save_manifest(manifest, run_dir)
    return manifest


def save_manifest(manifest_data: Dict[str, Any], run_dir: Union[str, Path]) -> None:
    """Writes manifest atomically to run_dir/manifest.json."""
    m_path = get_manifest_path(run_dir)
    m_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = m_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temp_path, m_path)


def archive_revision_snapshot(
    run_dir: Union[str, Path],
    revision: int,
    data_payload: Dict[str, Any],
    manifest_data: Dict[str, Any],
    output_mp4: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Saves a non-destructive snapshot of the project in revisions/rev_<NNN>/
    storing data.json, manifest.json, and output.mp4.
    """
    run_dir = Path(run_dir)
    rev_dir = run_dir / "revisions" / f"rev_{revision:03d}"
    rev_dir.mkdir(parents=True, exist_ok=True)

    # Save data.json
    with open(rev_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Save manifest.json snapshot
    with open(rev_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Copy output video if present
    if output_mp4:
        output_path = Path(output_mp4)
        if output_path.exists():
            shutil.copyfile(output_path, rev_dir / "output.mp4")

    return rev_dir


def detect_dirty_scenes(
    manifest_data: Dict[str, Any],
    current_scenes: List[Dict[str, Any]],
) -> Dict[str, List[int]]:
    """
    Compares the current scenes with the manifest to detect:
    - visual_dirty: scenes whose visual_hash changed
    - audio_dirty: scenes whose audio_hash changed
    """
    visual_dirty: List[int] = []
    audio_dirty: List[int] = []

    stored_scenes = manifest_data.get("scenes", {})

    for idx, sc in enumerate(current_scenes):
        scene_id = sc.get("scene_id", idx + 1)
        key = str(scene_id)
        if key not in stored_scenes:
            visual_dirty.append(scene_id)
            audio_dirty.append(scene_id)
            continue

        prev = stored_scenes[key]
        dur = float(sc.get("duration", (sc.get("end_time", 0.0) - sc.get("start_time", 0.0))))
        curr_v_hash = compute_visual_hash(sc, duration=dur)
        narration = sc.get("spoken_text") or sc.get("narration") or ""
        voice_id = sc.get("voice_id") or "en-US-ChristopherNeural"
        curr_a_hash = compute_audio_hash(narration, voice_id=voice_id)

        if curr_v_hash != prev.get("visual_hash"):
            visual_dirty.append(scene_id)
        if curr_a_hash != prev.get("audio_hash"):
            audio_dirty.append(scene_id)

    return {
        "visual_dirty": visual_dirty,
        "audio_dirty": audio_dirty,
    }


def create_baseline_artifacts(
    run_dir: Union[str, Path],
    data_payload: Dict[str, Any],
    master_video_path: Optional[Union[str, Path]] = None,
    master_audio_path: Optional[Union[str, Path]] = None,
) -> None:
    """
    Creates isolated scene audio (scenes/<id>/audio_v1.mp3) and segment video (segments/scene_<id>_v1.mp4)
    from the master audio and master video files via fast FFmpeg lossless cutting.
    """
    run_dir = Path(run_dir)
    scenes = data_payload.get("scenes", [])
    if not scenes:
        return

    # 1. Slice per-scene audio files
    if master_audio_path and Path(master_audio_path).exists():
        for idx, sc in enumerate(scenes):
            sid = sc.get("scene_id", idx + 1)
            st = float(sc.get("start_time", 0.0))
            dur = float(sc.get("duration", (sc.get("end_time", 0.0) - st)))
            sc_audio_dir = run_dir / "scenes" / str(sid)
            sc_audio_dir.mkdir(parents=True, exist_ok=True)
            sc_audio_path = sc_audio_dir / "audio_v1.mp3"
            if not sc_audio_path.exists() or sc_audio_path.stat().st_size < 1024:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{st:.3f}",
                    "-t", f"{dur:.3f}",
                    "-i", str(master_audio_path),
                    "-c:a", "libmp3lame", "-q:a", "2",
                    str(sc_audio_path),
                ]
                subprocess.run(cmd, capture_output=True)

    # 2. Slice per-scene video segments
    if master_video_path and Path(master_video_path).exists():
        segments_dir = run_dir / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        for idx, sc in enumerate(scenes):
            sid = sc.get("scene_id", idx + 1)
            st = float(sc.get("start_time", 0.0))
            dur = float(sc.get("duration", (sc.get("end_time", 0.0) - st)))
            sc_seg_path = segments_dir / f"scene_{sid}_v1.mp4"
            if not sc_seg_path.exists() or sc_seg_path.stat().st_size < 1024:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{st:.3f}",
                    "-t", f"{dur:.3f}",
                    "-i", str(master_video_path),
                    "-vf", "setpts=PTS-STARTPTS",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    "-g", "30",
                    "-sc_threshold", "0",
                    "-video_track_timescale", "90000",
                    "-an",
                    str(sc_seg_path),
                ]
                subprocess.run(cmd, capture_output=True)
