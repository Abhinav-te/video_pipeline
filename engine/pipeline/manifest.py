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
import fcntl
import hashlib
import json
import os
import re
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

    import math
    total_duration_sec = float(initial_scenes[-1].get("end_time", 0.0)) if initial_scenes else 0.0
    total_timeline_frames = max(fps, math.ceil(total_duration_sec * fps))

    for idx, sc in enumerate(initial_scenes):
        scene_id = sc.get("scene_id", idx + 1)
        dur = float(sc.get("duration", (sc.get("end_time", 0.0) - sc.get("start_time", 0.0))))
        start_t = float(sc.get("start_time", 0.0))
        end_t = float(sc.get("end_time", start_t + dur))

        start_frame = int(round(start_t * fps))
        if idx < len(initial_scenes) - 1:
            next_start_t = float(initial_scenes[idx + 1].get("start_time", end_t))
            next_start_frame = int(round(next_start_t * fps))
            duration_frames = max(1, next_start_frame - start_frame)
        else:
            duration_frames = max(1, total_timeline_frames - start_frame)

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
    storing data.json, manifest.json, output.mp4, master audio, validation report,
    and all referenced scene segment and audio artifacts.
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

    # Copy master audio if present
    audio_wav = run_dir / "audio.wav"
    if audio_wav.exists():
        shutil.copyfile(audio_wav, rev_dir / "audio.wav")
    audio_mp3 = run_dir / "audio.mp3"
    if audio_mp3.exists():
        shutil.copyfile(audio_mp3, rev_dir / "audio.mp3")

    # Copy validation report if present
    val_rep = run_dir / "validation_report.json"
    if val_rep.exists():
        shutil.copyfile(val_rep, rev_dir / "validation_report.json")

    # Copy referenced scene segments and scene audios
    for s_key, sc_info in manifest_data.get("scenes", {}).items():
        rel_seg = sc_info.get("segment_video")
        if rel_seg:
            src_seg = run_dir / rel_seg
            if src_seg.exists():
                dest_seg = rev_dir / rel_seg
                dest_seg.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src_seg, dest_seg)

        rel_audio = sc_info.get("audio_file")
        if rel_audio:
            src_audio = run_dir / rel_audio
            if src_audio.exists():
                dest_audio = rev_dir / rel_audio
                dest_audio.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src_audio, dest_audio)

    return rev_dir


def restore_revision_snapshot(
    run_dir: Union[str, Path],
    target_revision: int,
) -> Dict[str, Any]:
    """
    Non-destructively restores snapshot revisions/rev_<target_revision>/
    as a new active revision.
    Restores consistent data.json, manifest.json, master audio, output video,
    validation report, and all referenced scene segments and audio artifacts,
    archiving the current active state before overwriting.
    """
    run_dir = Path(run_dir)
    with RevisionLock(run_dir):
        rev_dir = run_dir / "revisions" / f"rev_{target_revision:03d}"
        if not rev_dir.exists():
            raise FileNotFoundError(f"Snapshot 'rev_{target_revision:03d}' not found in {run_dir / 'revisions'}")

        snap_data_file = rev_dir / "data.json"
        snap_manifest_file = rev_dir / "manifest.json"
        if not snap_data_file.exists() or not snap_manifest_file.exists():
            raise ValueError(f"Snapshot 'rev_{target_revision:03d}' is missing data.json or manifest.json")

        with open(snap_data_file, "r", encoding="utf-8") as f:
            snap_data = json.load(f)
        with open(snap_manifest_file, "r", encoding="utf-8") as f:
            snap_manifest = json.load(f)

        # 1. Archive current active state first before overwriting
        curr_manifest = load_manifest(run_dir) or {}
        curr_rev = curr_manifest.get("revision", 1)
        current_data_file = run_dir / "data.json"
        if current_data_file.exists() and curr_manifest:
            with open(current_data_file, "r", encoding="utf-8") as f:
                curr_data = json.load(f)
            curr_out = run_dir / "output.mp4"
            archive_revision_snapshot(
                run_dir=run_dir,
                revision=curr_rev,
                data_payload=curr_data,
                manifest_data=curr_manifest,
                output_mp4=curr_out if curr_out.exists() else None,
            )

        # 2. Determine new revision number (strictly monotonic)
        existing_rev_nums = [curr_rev, target_revision]
        revs_dir = run_dir / "revisions"
        if revs_dir.exists():
            for d in revs_dir.iterdir():
                if d.is_dir():
                    m = re.search(r"rev_(\d+)", d.name)
                    if m:
                        existing_rev_nums.append(int(m.group(1)))
        new_rev = max(existing_rev_nums) + 1

        # 3. Update snapshot manifest to become the new revision
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        restored_manifest = copy.deepcopy(snap_manifest)
        restored_manifest["revision"] = new_rev
        restored_manifest["updated_at"] = now_iso
        if "history" not in restored_manifest:
            restored_manifest["history"] = []
        restored_manifest["history"].append({
            "revision": new_rev,
            "timestamp": now_iso,
            "action": f"Restored snapshot rev_{target_revision:03d}",
        })

        restored_data = copy.deepcopy(snap_data)
        if "revision" in restored_data:
            restored_data["revision"] = new_rev

        # 4. Save restored data.json and manifest.json to run_dir
        with open(run_dir / "data.json", "w", encoding="utf-8") as f:
            json.dump(restored_data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        save_manifest(restored_manifest, run_dir)

        # 5. Restore audio
        snap_wav = rev_dir / "audio.wav"
        if snap_wav.exists():
            shutil.copyfile(snap_wav, run_dir / "audio.wav")
        snap_mp3 = rev_dir / "audio.mp3"
        if snap_mp3.exists():
            shutil.copyfile(snap_mp3, run_dir / "audio.mp3")

        # 6. Restore output video if present
        snap_vid = rev_dir / "output.mp4"
        if snap_vid.exists():
            run_out = run_dir / "output.mp4"
            shutil.copyfile(snap_vid, run_out)
            out_dir = Path("video/out")
            out_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(snap_vid, out_dir / f"{run_dir.name}_v{new_rev}.mp4")

        # 7. Restore validation report if present
        snap_val_rep = rev_dir / "validation_report.json"
        if snap_val_rep.exists():
            shutil.copyfile(snap_val_rep, run_dir / "validation_report.json")

        # 8. Restore referenced segments and scene audio from snapshot
        for s_key, sc_info in snap_manifest.get("scenes", {}).items():
            rel_seg = sc_info.get("segment_video")
            if rel_seg:
                snap_seg = rev_dir / rel_seg
                if snap_seg.exists():
                    dest_seg = run_dir / rel_seg
                    dest_seg.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(snap_seg, dest_seg)
            rel_audio = sc_info.get("audio_file")
            if rel_audio:
                snap_audio = rev_dir / rel_audio
                if snap_audio.exists():
                    dest_audio = run_dir / rel_audio
                    dest_audio.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(snap_audio, dest_audio)

        # 9. Archive this newly restored state as rev_<new_rev>
        archive_revision_snapshot(
            run_dir=run_dir,
            revision=new_rev,
            data_payload=restored_data,
            manifest_data=restored_manifest,
            output_mp4=snap_vid if snap_vid.exists() else None,
        )

        return {
            "revision": new_rev,
            "restored_from": target_revision,
            "manifest": restored_manifest,
            "data": restored_data,
        }


class RevisionLock:
    """
    Non-blocking advisory file lock using fcntl.flock to serialize revisions.
    Prevents concurrent revision processes from corrupting run state.
    """
    def __init__(self, run_dir: Union[str, Path]):
        self.run_dir = Path(run_dir)
        self.lock_file_path = self.run_dir / ".revision.lock"
        self._fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self):
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._fd = open(self.lock_file_path, "w")
        try:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._fd.write(f"pid={os.getpid()}\ntimestamp={datetime.datetime.now(datetime.timezone.utc).isoformat()}\n")
            self._fd.flush()
        except (BlockingIOError, OSError) as exc:
            try:
                self._fd.close()
            except Exception:
                pass
            self._fd = None
            raise RuntimeError(
                f"Concurrent revision rejected: Run '{self.run_dir.name}' is currently locked by another active process."
            ) from exc

    def release(self):
        if self._fd is not None:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                self._fd.close()
            except Exception:
                pass
            self._fd = None


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
        manifest_data = load_manifest(run_dir) or {}
        manifest_scenes = manifest_data.get("scenes", {})
        for idx, sc in enumerate(scenes):
            sid = sc.get("scene_id", idx + 1)
            sc_info = manifest_scenes.get(str(sid), {})
            start_frame = int(sc_info.get("start_frame", round(float(sc.get("start_time", 0.0)) * 30)))
            dur_frames = int(sc_info.get("duration_frames", max(1, round(float(sc.get("duration", 2.5)) * 30))))
            sc_seg_path = segments_dir / f"scene_{sid}_v1.mp4"
            if not sc_seg_path.exists() or sc_seg_path.stat().st_size < 1024:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_frame / 30.0:.4f}",
                    "-i", str(master_video_path),
                    "-frames:v", str(dur_frames),
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
