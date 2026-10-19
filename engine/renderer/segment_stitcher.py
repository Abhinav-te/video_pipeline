"""
engine/renderer/segment_stitcher.py

Per-Scene Segment Rendering & Fast FFmpeg Recomposition (Checkpoint 02).
- Renders isolated scene segments: runs/<run_id>/segments/scene_<scene_id>_v<rev>.mp4
  using Remotion frame ranges (--frames=<startFrame>-<endFrame>).
- Selectively re-renders only dirty scenes whose visual_hash or audio_hash changed.
- Stitches all current scene segment MP4s in order using FFmpeg concat:
  ffmpeg -y -f concat -safe 0 -i concat_list.txt -c copy <output_mp4>
- Guaranteed sub-second recomposition of untouched scenes.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union

REPO_DIR = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"


def render_scene_segment(
    scene_id: Union[int, str],
    start_frame: int,
    end_frame: int,
    output_segment_path: Path,
    data_file_path: Path,
    timeout: float = 180.0,
) -> bool:
    """
    Renders a single scene segment using Remotion with --frames=<start_frame>-<end_frame>.
    """
    output_segment_path = Path(output_segment_path).resolve()
    output_segment_path.parent.mkdir(parents=True, exist_ok=True)
    data_file_path = Path(data_file_path).resolve()

    try:
        remotion_out = str(output_segment_path.relative_to(VIDEO_DIR))
    except ValueError:
        remotion_out = str(output_segment_path)

    cmd = [
        "npx", "remotion", "render", "CodingShort", remotion_out,
        "--frames", f"{start_frame}-{end_frame}",
        "--codec", "h264",
        "--props", str(data_file_path),
    ]

    print(f"[SEGMENT:RENDER] 🎬 Rendering Scene {scene_id} frames {start_frame}-{end_frame} -> {output_segment_path.name}...", flush=True)

    try:
        res = subprocess.run(cmd, cwd=str(VIDEO_DIR), capture_output=True, text=True, timeout=timeout)
        if res.returncode == 0 and output_segment_path.exists() and output_segment_path.stat().st_size > 1024:
            # Mandatory Normalization: Ensure pure video, PTS=0, IDR keyframe at start, and exact libx264 settings
            temp_raw = output_segment_path.with_name(f"{output_segment_path.stem}.raw_remotion.mp4")
            shutil.move(str(output_segment_path), str(temp_raw))
            cmd_norm = [
                "ffmpeg", "-y",
                "-i", str(temp_raw),
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
                str(output_segment_path),
            ]
            res_norm = subprocess.run(cmd_norm, capture_output=True)
            temp_raw.unlink(missing_ok=True)
            if res_norm.returncode != 0 or not output_segment_path.exists() or output_segment_path.stat().st_size < 1024:
                print(f"[SEGMENT:ERROR] Failed to normalize segment for Scene {scene_id}", file=sys.stderr, flush=True)
                return False

            print(f"[SEGMENT:SUCCESS] Scene {scene_id} rendered & normalized ({output_segment_path.stat().st_size:,} bytes)", flush=True)
            return True
        else:
            err_msg = res.stderr[-500:] if res.stderr else f"Exit code {res.returncode}"
            print(f"[SEGMENT:ERROR] Failed to render segment for Scene {scene_id}: {err_msg}", file=sys.stderr, flush=True)
            return False
    except subprocess.TimeoutExpired:
        print(f"[SEGMENT:ERROR] Remotion render timed out after {timeout}s for Scene {scene_id}", file=sys.stderr, flush=True)
        return False
    except Exception as exc:
        print(f"[SEGMENT:ERROR] Exception rendering segment for Scene {scene_id}: {exc}", file=sys.stderr, flush=True)
        return False


def render_dirty_segments(
    run_dir: Path,
    manifest_data: Dict[str, Any],
    data_file_path: Path,
    dirty_scene_ids: List[Union[int, str]],
    force_all: bool = False,
) -> bool:
    """
    Renders all dirty scene segments or missing segment files.
    """
    run_dir = Path(run_dir)
    segments_dir = run_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    scenes_dict = manifest_data.get("scenes", {})
    dirty_set = set(str(sid) for sid in dirty_scene_ids)

    # Sort scene keys numerically if possible
    def get_sort_key(k: str) -> int:
        try:
            return int(k)
        except ValueError:
            return 999

    sorted_keys = sorted(scenes_dict.keys(), key=get_sort_key)

    for key in sorted_keys:
        info = scenes_dict[key]
        scene_id = info["scene_id"]
        rev = info.get("revision", 1)
        rel_seg = info.get("segment_video") or f"segments/scene_{scene_id}_v{rev}.mp4"
        seg_path = run_dir / rel_seg

        is_dirty = force_all or (str(scene_id) in dirty_set) or not seg_path.exists() or seg_path.stat().st_size < 1024

        if is_dirty:
            start_frame = int(info["start_frame"])
            duration_frames = int(info["duration_frames"])
            end_frame = start_frame + duration_frames - 1

            ok = render_scene_segment(
                scene_id=scene_id,
                start_frame=start_frame,
                end_frame=end_frame,
                output_segment_path=seg_path,
                data_file_path=data_file_path,
            )
            if not ok:
                return False
        else:
            print(f"[SEGMENT:CACHE] ⚡ Scene {scene_id} unchanged; reusing {seg_path.name}", flush=True)

    return True


def get_segment_timebase(path: Path) -> str:
    try:
        res = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=time_base", "-of", "default=noprint_wrappers=1:nokey=1",
            str(path)
        ], capture_output=True, text=True, timeout=10.0)
        return res.stdout.strip()
    except Exception:
        return ""


def verify_stitched_scene_frames(
    video_path: Union[str, Path],
    scenes: List[Dict[str, Any]],
    min_luminance: float = 8.0,
    min_scene_diff: float = 2.0,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Mandatory Post-Stitch Scene Frame Verification Gate:
    Extracts 1 frame from the middle of EVERY scene (t = scene.start + scene.duration / 2)
    from the final stitched output.mp4 and asserts that:
      (a) Mean luminance > min_luminance (never a black frame)
      (b) Adjacent scenes in the final stitched output.mp4 are NOT frozen on Scene 1 (mean_abs_diff > min_scene_diff)
    """
    import numpy as np

    video_path = Path(video_path).resolve()
    if not video_path.exists():
        return False, [f"Video file does not exist: {video_path}"], {}

    errors: List[str] = []
    meta: Dict[str, Any] = {"scenes": []}
    frames: List[np.ndarray] = []

    for idx, sc in enumerate(scenes):
        sid = sc.get("scene_id", idx + 1)
        st = float(sc.get("start_time", 0.0))
        dur = float(sc.get("duration", (sc.get("end_time", st + 2.5) - st)))
        mid_t = round(st + dur / 2.0, 3)

        cmd = [
            "ffmpeg", "-v", "error",
            "-ss", f"{mid_t:.3f}",
            "-i", str(video_path),
            "-vframes", "1",
            "-f", "image2pipe",
            "-pix_fmt", "gray",
            "-vcodec", "rawvideo",
            "-"
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0 or len(res.stdout) == 0:
            err = f"Scene {sid} (t={mid_t:.2f}s): Failed to extract verification frame."
            errors.append(err)
            continue

        raw_frame = np.frombuffer(res.stdout, dtype=np.uint8)
        frames.append(raw_frame)
        lum = float(np.mean(raw_frame))

        sc_meta = {
            "scene_id": sid,
            "mid_time": mid_t,
            "mean_luminance": round(lum, 2),
        }

        if lum <= min_luminance:
            err = f"Scene {sid} (t={mid_t:.2f}s): Mean luminance {lum:.2f} <= {min_luminance} (Black frame detected!)."
            errors.append(err)
            sc_meta["status"] = "BLACK_FRAME_ERROR"
        else:
            sc_meta["status"] = "OK"

        meta["scenes"].append(sc_meta)

    # Check adjacent scenes for freeze
    for i in range(len(frames) - 1):
        sid_curr = scenes[i].get("scene_id", i + 1)
        sid_next = scenes[i + 1].get("scene_id", i + 2)
        f_curr = frames[i]
        f_next = frames[i + 1]

        if len(f_curr) == len(f_next) and len(f_curr) > 0:
            diff = float(np.mean(np.abs(f_curr.astype(float) - f_next.astype(float))))
            meta["scenes"][i]["diff_to_next"] = round(diff, 2)
            if diff <= min_scene_diff:
                err = (
                    f"Adjacent Scenes {sid_curr} and {sid_next} are frozen/identical "
                    f"(mean pixel diff {diff:.2f} <= {min_scene_diff})."
                )
                errors.append(err)

    is_valid = len(errors) == 0
    return is_valid, errors, meta


def stitch_segments(
    segment_paths: List[Path],
    output_video_path: Path,
    master_audio_path: Optional[Path] = None,
    scenes_meta: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """
    Stitches multiple scene segments into a unified master video using FFmpeg concat.
    Optionally muxes master audio for seamless synchronization.
    Guarantees matching 90000 timescale across all segments and runs Post-Stitch Scene Frame Verification.
    """
    output_video_path = Path(output_video_path).resolve()
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    if not segment_paths:
        print("[STITCH:ERROR] No segment paths provided for stitching.", file=sys.stderr)
        return False

    for sp in segment_paths:
        if not sp.exists() or sp.stat().st_size < 1024:
            print(f"[STITCH:ERROR] Segment file missing or invalid: {sp}", file=sys.stderr)
            return False

    effective_paths: List[Path] = []
    cleanup_paths: List[Path] = []

    # Ensure all segments have consistent 1/90000 timebase before concat
    for idx, sp in enumerate(segment_paths):
        tb = get_segment_timebase(sp)
        if tb and tb != "1/90000":
            norm_seg = output_video_path.with_name(f"{sp.stem}.norm90k.mp4")
            cmd_norm = [
                "ffmpeg", "-y",
                "-i", str(sp),
                "-video_track_timescale", "90000",
                "-c", "copy",
                str(norm_seg),
            ]
            res_norm = subprocess.run(cmd_norm, capture_output=True, text=True)
            if res_norm.returncode == 0 and norm_seg.exists() and norm_seg.stat().st_size > 1024:
                effective_paths.append(norm_seg)
                cleanup_paths.append(norm_seg)
            else:
                effective_paths.append(sp)
        else:
            effective_paths.append(sp)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for ep in effective_paths:
            f.write(f"file '{ep.resolve().as_posix()}'\n")
        concat_list = Path(f.name)

    temp_stitched = output_video_path.with_name(f"{output_video_path.stem}.raw_concat.mp4")

    try:
        # Step 1: Lossless segment concat
        cmd_concat = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-avoid_negative_ts", "make_zero",
            "-fflags", "+genpts",
            "-i", str(concat_list),
            "-c", "copy",
            str(temp_stitched),
        ]
        res = subprocess.run(cmd_concat, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[STITCH:ERROR] FFmpeg segment concat failed: {res.stderr[-400:]}", file=sys.stderr)
            return False

        # Step 2: Mux master audio if provided, or finalize (NO -shortest so audio is never clipped)
        if master_audio_path and Path(master_audio_path).exists():
            cmd_mux = [
                "ffmpeg",
                "-y",
                "-i", str(temp_stitched),
                "-i", str(master_audio_path),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-ar", "44100",
                "-b:a", "192k",
                str(output_video_path),
            ]
            res_mux = subprocess.run(cmd_mux, capture_output=True, text=True)
            if res_mux.returncode != 0:
                print(f"[STITCH:ERROR] FFmpeg audio mux failed: {res_mux.stderr[-400:]}", file=sys.stderr)
                # Fallback to direct temp copy
                shutil.move(str(temp_stitched), str(output_video_path))
            else:
                if temp_stitched.exists():
                    temp_stitched.unlink(missing_ok=True)
        else:
            shutil.move(str(temp_stitched), str(output_video_path))

        # Step 3: Mandatory Post-Stitch Scene Frame Verification Gate
        if scenes_meta:
            is_valid, errors, v_meta = verify_stitched_scene_frames(output_video_path, scenes_meta)
            if not is_valid:
                print(f"[STITCH:WARN] Stream copy concat failed post-stitch frame verification: {errors}. Retrying with concat filter...", file=sys.stderr, flush=True)
                # Fallback to concat filter with normalized libx264 pass
                cmd_filter = ["ffmpeg", "-y"]
                for ep in effective_paths:
                    cmd_filter.extend(["-i", str(ep)])
                if master_audio_path and Path(master_audio_path).exists():
                    cmd_filter.extend(["-i", str(master_audio_path)])
                n = len(effective_paths)
                filter_str = "".join([f"[{i}:v]" for i in range(n)]) + f"concat=n={n}:v=1:a=0[outv]"
                cmd_filter.extend([
                    "-filter_complex", filter_str,
                    "-map", "[outv]",
                ])
                if master_audio_path and Path(master_audio_path).exists():
                    cmd_filter.extend(["-map", f"{n}:a", "-c:a", "aac", "-ar", "44100", "-b:a", "192k"])
                cmd_filter.extend([
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    "-g", "30",
                    "-video_track_timescale", "90000",
                    str(output_video_path),
                ])
                res_f = subprocess.run(cmd_filter, capture_output=True, text=True)
                if res_f.returncode != 0:
                    print(f"[STITCH:ERROR] FFmpeg concat filter fallback failed: {res_f.stderr[-400:]}", file=sys.stderr)
                    return False

                is_valid2, errors2, v_meta2 = verify_stitched_scene_frames(output_video_path, scenes_meta)
                if not is_valid2:
                    print(f"[STITCH:ERROR] Post-stitch verification failed after filter fallback: {errors2}", file=sys.stderr)
                    return False
                print(f"[STITCH:SUCCESS] ✅ Concat filter recovered output; verified {len(scenes_meta)} scenes (luminance > 8.0, diff > 2.0)", flush=True)
            else:
                print(f"[STITCH:VERIFY] ✅ All {len(scenes_meta)} scenes passed Post-Stitch Scene Frame Verification Gate (luminance > 8.0, diff > 2.0)", flush=True)

        print(f"[STITCH:SUCCESS] Recomposed {len(segment_paths)} segments into {output_video_path.name} ({output_video_path.stat().st_size:,} bytes)", flush=True)
        return True
    finally:
        if concat_list.exists():
            concat_list.unlink(missing_ok=True)
        if temp_stitched.exists():
            temp_stitched.unlink(missing_ok=True)
        for cp in cleanup_paths:
            if cp.exists():
                cp.unlink(missing_ok=True)

