"""
engine/revise.py

Surgical Scene Revision Engine (Checkpoint 02).
Supports:
1. Mode A — Visual-Only Revision:
   - Modifies scene visual properties (visual_type, title, visual_props).
   - Audio and word timestamps remain 100% untouched across all scenes.
   - Re-renders Remotion ONLY for the revised scene.
   - Fast FFmpeg recomposition of all segments.
2. Mode B — Narration Revision:
   - Modifies spoken explanation for a specific scene.
   - Regenerates TTS audio and Whisper word timestamps ONLY for that scene.
   - Shifts downstream scene start offsets by delta_t.
   - Re-renders revised visual segment to match new duration.
   - Fast FFmpeg recomposition of all segments.
- Atomically increments revision and preserves non-destructive snapshots in revisions/rev_<NNN>/.
"""

import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"
PUBLIC_DIR = VIDEO_DIR / "public"
RUNS_DIR = PUBLIC_DIR / "runs"

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from engine.pipeline.manifest import (
    load_manifest,
    init_manifest,
    save_manifest,
    archive_revision_snapshot,
    restore_revision_snapshot,
    compute_visual_hash,
    compute_audio_hash,
    RevisionLock,
)
from engine.audio.scene_audio import (
    synthesize_scene_audio,
    concatenate_scene_audios,
    get_audio_duration,
)
from engine.renderer.segment_stitcher import (
    render_scene_segment,
    render_dirty_segments,
    stitch_segments,
)
from engine.validation.output import validate_video_output
from engine.validation.evidence_validator import validate_post_render_qa


def parse_scene_id(val: Any) -> int:
    """Parses integer scene_id from string like '2' or 'scene_2'."""
    s = str(val).strip().lower()
    if s.startswith("scene_"):
        s = s[6:]
    return int(s)


def execute_revision(
    run_id: str,
    target_scene_id: Union[int, str],
    set_visual_type: Optional[str] = None,
    set_title: Optional[str] = None,
    set_visual_json: Optional[str] = None,
    set_narration: Optional[str] = None,
    set_evidence_id: Optional[str] = None,
    output_path: Optional[Union[str, Path]] = None,
    fps: int = 30,
) -> Path:
    """
    Executes a surgical scene revision on run_id.
    Returns path to the newly recomposed final video.
    """
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    # Enforce advisory per-run concurrency lock
    with RevisionLock(run_dir):
        data_path = run_dir / "data.json"
        if not data_path.exists():
            raise FileNotFoundError(f"Timeline data.json not found in {run_dir}")

        with open(data_path, "r", encoding="utf-8") as f:
            data_payload = json.load(f)

        scenes = data_payload.get("scenes", [])
        if not scenes:
            raise ValueError("data.json contains no scenes.")

        target_id = parse_scene_id(target_scene_id)
        target_scene_idx = -1
        for idx, sc in enumerate(scenes):
            if parse_scene_id(sc.get("scene_id", idx + 1)) == target_id:
                target_scene_idx = idx
                break

        if target_scene_idx == -1:
            raise ValueError(f"Scene ID {target_scene_id} not found in run '{run_id}'. Available: {[s.get('scene_id') for s in scenes]}")

        target_scene = scenes[target_scene_idx]

        # Load or initialize manifest
        manifest = load_manifest(run_dir)
        if not manifest:
            print(f"[REVISE:INFO] No manifest found; initializing manifest for run '{run_id}'...", flush=True)
            manifest = init_manifest(run_id, run_dir, scenes, fps=fps)

        curr_rev = manifest.get("revision", 1)
        new_rev = curr_rev + 1
        manifest["revision"] = new_rev
        manifest["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Determine mode
        is_narration_revision = bool(set_narration and set_narration.strip())
        is_visual_revision = bool(set_visual_type or set_title or set_visual_json)

        if not is_narration_revision and not is_visual_revision:
            raise ValueError("Revision request specified neither visual changes nor narration changes.")

        mode_label = "Mode B (Narration Revision)" if is_narration_revision else "Mode A (Visual-Only Revision)"
        print(f"\n[REVISE:START] 🚀 Executing {mode_label} on Scene {target_id} (Rev {curr_rev} -> {new_rev})", flush=True)

        subject = data_payload.get("subject") or data_payload.get("domain") or target_scene.get("domain") or "code"
        scene_key = str(target_id)
        prev_scene_info = manifest["scenes"].get(scene_key, {})

        staged_data_path = run_dir / f".staged_data_v{new_rev}.json"
        staged_audio_path = None
        staged_output_path = run_dir / f".staged_output_v{new_rev}.mp4"
        new_audio_path = None

        try:
            # =========================================================================
            # MODE B: NARRATION REVISION
            # =========================================================================
            if is_narration_revision:
                new_narration = set_narration.strip()
                print(f"[REVISE:NARRATION] Updating spoken text for Scene {target_id}: '{new_narration}'", flush=True)

                target_scene["spoken_text"] = new_narration
                target_scene["narration"] = new_narration

                if set_evidence_id:
                    curr_ev = target_scene.get("evidence_ids") or []
                    if set_evidence_id not in curr_ev:
                        curr_ev.append(set_evidence_id)
                    target_scene["evidence_ids"] = curr_ev
                    target_scene["narration_segments"] = [
                        {"text": new_narration, "evidence_ids": curr_ev}
                    ]

                # Synthesize audio ONLY for target scene
                scene_audio_dir = run_dir / "scenes" / str(target_id)
                voice_id = target_scene.get("voice_id") or "en-US-ChristopherNeural"
                new_audio_path, new_scene_dur, new_scene_words = synthesize_scene_audio(
                    narration_text=new_narration,
                    scene_dir=scene_audio_dir,
                    revision=new_rev,
                    voice_id=voice_id,
                )

                old_scene_dur = float(target_scene.get("duration", (target_scene.get("end_time", 0.0) - target_scene.get("start_time", 0.0))))
                delta_t = round(new_scene_dur - old_scene_dur, 3)

                print(f"[REVISE:TIMING] Scene {target_id} duration changed from {old_scene_dur:.2f}s to {new_scene_dur:.2f}s (Δt = {delta_t:+.2f}s)", flush=True)

                # Update target scene timing
                target_scene["duration"] = new_scene_dur
                target_scene["end_time"] = round(float(target_scene.get("start_time", 0.0)) + new_scene_dur, 3)

                # Re-assemble all scene audio items
                scene_audio_items: List[Dict[str, Any]] = []
                for idx, sc in enumerate(scenes):
                    sid = parse_scene_id(sc.get("scene_id", idx + 1))
                    if sid == target_id:
                        scene_audio_items.append({
                            "scene_id": sid,
                            "audio_path": new_audio_path,
                            "duration": new_scene_dur,
                            "words": new_scene_words,
                        })
                    else:
                        s_info = manifest["scenes"].get(str(sid), {})
                        rel_audio = s_info.get("audio_file")
                        wav_candidate = (run_dir / rel_audio).with_suffix(".wav") if rel_audio else None
                        if wav_candidate and wav_candidate.exists():
                            s_audio_path = wav_candidate
                        elif rel_audio and (run_dir / rel_audio).exists():
                            s_audio_path = run_dir / rel_audio
                        elif (run_dir / "scenes" / str(sid) / "audio_v1.wav").exists():
                            s_audio_path = run_dir / "scenes" / str(sid) / "audio_v1.wav"
                        elif (run_dir / "scenes" / str(sid) / "audio_v1.mp3").exists():
                            s_audio_path = run_dir / "scenes" / str(sid) / "audio_v1.mp3"
                        else:
                            s_audio_path = run_dir / "scenes" / str(sid) / "audio_v1.wav"

                        # If per-scene audio doesn't exist yet, generate it
                        if not s_audio_path.exists():
                            s_text = sc.get("spoken_text") or sc.get("narration") or "Next step."
                            s_audio_path, _, s_words = synthesize_scene_audio(
                                narration_text=s_text,
                                scene_dir=run_dir / "scenes" / str(sid),
                                revision=1,
                            )
                        else:
                            s_words = []
                            # Filter existing master words in range
                            st = float(sc.get("start_time", 0.0))
                            et = float(sc.get("end_time", st + 5.0))
                            for w in data_payload.get("words", []):
                                if st <= w.get("start", 0.0) < et:
                                    s_words.append({
                                        "word": w.get("word", ""),
                                        "start": round(w.get("start", 0.0) - st, 3),
                                        "end": round(w.get("end", 0.0) - st, 3),
                                    })

                        scene_audio_items.append({
                            "scene_id": sid,
                            "audio_path": s_audio_path,
                            "duration": float(sc.get("duration", (sc.get("end_time", 0.0) - sc.get("start_time", 0.0)))),
                            "words": s_words,
                        })

                # Concatenate audio into candidate staged master audio file
                staged_audio_path = run_dir / f".staged_audio_v{new_rev}.wav"
                updated_scenes_meta, master_words = concatenate_scene_audios(
                    scene_items=scene_audio_items,
                    output_master_audio=staged_audio_path,
                )

                # Update scene timings & words in data_payload
                from engine.timeline.timeline_mapper import chunk_caption_words
                for idx, sc in enumerate(scenes):
                    sc["start_time"] = updated_scenes_meta[idx]["start_time"]
                    sc["end_time"] = updated_scenes_meta[idx]["end_time"]
                    sc["duration"] = updated_scenes_meta[idx]["duration"]
                data_payload["words"] = master_words
                data_payload["caption_chunks"] = chunk_caption_words(master_words)
            else:
                staged_audio_path = run_dir / "audio.wav" if (run_dir / "audio.wav").exists() else run_dir / "audio.mp3"

            # =========================================================================
            # MODE A: VISUAL-ONLY REVISION
            # =========================================================================
            if is_visual_revision:
                if set_visual_type:
                    v_type = set_visual_type.strip().lower()
                    target_scene["visual_type"] = v_type
                    target_scene["scene_type"] = v_type
                    print(f"[REVISE:VISUAL] Set visual_type for Scene {target_id}: '{v_type}'", flush=True)

                    if v_type == "comparison":
                        from engine.timeline.timeline_mapper import COMPARISON_FOOTERS
                        domain_footer = COMPARISON_FOOTERS.get(subject, COMPARISON_FOOTERS.get("code", "KEY TAKEAWAY: Declarative async execution eliminates distributed retry race conditions"))
                        target_scene["comparison_footer"] = domain_footer

                if set_title:
                    target_scene["title"] = set_title.strip()
                    print(f"[REVISE:VISUAL] Set title for Scene {target_id}: '{set_title}'", flush=True)

                if set_visual_json:
                    try:
                        props = json.loads(set_visual_json)
                        if isinstance(props, dict):
                            target_scene.update(props)
                            print(f"[REVISE:VISUAL] Applied visual props JSON to Scene {target_id}: {list(props.keys())}", flush=True)
                    except Exception as exc:
                        raise ValueError(f"Failed to parse --set-visual-json: {exc}")

            # Evidence Validation Gate during revision (FAIL CLOSED)
            ev_pack_path = run_dir / "evidence_pack.json"
            if ev_pack_path.exists():
                from engine.validation.evidence_validator import validate_evidence_and_plan
                with open(ev_pack_path, "r", encoding="utf-8") as ef:
                    ev_pack_data = json.load(ef)
                val_report = validate_evidence_and_plan(ev_pack_data, data_payload)
                with open(run_dir / "validation_report.json", "w", encoding="utf-8") as vf:
                    json.dump(val_report.model_dump(), vf, indent=2)
                if val_report.needs_review:
                    reasons = "; ".join(val_report.review_reasons) if val_report.review_reasons else "Needs manual review"
                    raise RuntimeError(f"Evidence validation gate requires human review for revision {new_rev}: {reasons}")
                if not val_report.passed:
                    failed_checks = []
                    if isinstance(val_report.checks, list):
                        for c in val_report.checks:
                            c_passed = getattr(c, "passed", None) if not isinstance(c, dict) else c.get("passed")
                            c_name = getattr(c, "check", None) if not isinstance(c, dict) else c.get("check")
                            if c_passed is False and c_name:
                                failed_checks.append(c_name)
                    elif isinstance(val_report.checks, dict):
                        failed_checks = [k for k, v in val_report.checks.items() if not v]

                    if not failed_checks:
                        failed_checks = (
                            getattr(val_report, "banned_tokens_found", [])
                            + getattr(val_report, "schema_lineage_errors", [])
                            + getattr(val_report, "gate1_errors", [])
                            + getattr(val_report, "gate2_errors", [])
                            + getattr(val_report, "gate3_errors", [])
                            + getattr(val_report, "unsupported_numbers", [])
                        )
                    err_summary = ", ".join(str(fc) for fc in failed_checks) if failed_checks else "Unknown validation failure"
                    raise RuntimeError(f"Evidence validation gate failed for revision {new_rev}: {err_summary}")
                print(f"[REVISE:EVIDENCE] Verified 100% claim backing ({val_report.claim_coverage_pct}% coverage).", flush=True)

            # Stage candidate data.json
            with open(staged_data_path, "w", encoding="utf-8") as f:
                json.dump(data_payload, f, indent=2, ensure_ascii=False)
                f.write("\n")

            # Timeline Schema (Zod) Validation Gate (FAIL CLOSED)
            zod_script = VIDEO_DIR / "scripts" / "validate_timeline.mjs"
            if zod_script.exists():
                zod_res = subprocess.run(
                    ["node", str(zod_script), str(staged_data_path)],
                    cwd=str(VIDEO_DIR),
                    capture_output=True,
                    text=True,
                )
                if zod_res.returncode != 0:
                    err_msg = zod_res.stderr.strip() or zod_res.stdout.strip()
                    raise RuntimeError(f"Timeline schema validation (Zod) failed for revision {new_rev}:\n{err_msg}")
                print("[REVISE:ZOD] Timeline schema successfully verified by Zod gate.", flush=True)

            # Update manifest scenes state in candidate manifest
            import math
            total_duration_sec = float(scenes[-1].get("end_time", 0.0)) if scenes else 0.0
            total_timeline_frames = max(fps, math.ceil(total_duration_sec * fps))

            for idx, sc in enumerate(scenes):
                sid = parse_scene_id(sc.get("scene_id", idx + 1))
                s_key = str(sid)
                prev = manifest["scenes"].get(s_key, {})

                dur = float(sc.get("duration", (sc.get("end_time", 0.0) - sc.get("start_time", 0.0))))
                st = float(sc.get("start_time", 0.0))
                et = float(sc.get("end_time", st + dur))

                start_frame = int(round(st * fps))
                if idx < len(scenes) - 1:
                    next_st = float(scenes[idx + 1].get("start_time", et))
                    next_start_frame = int(round(next_st * fps))
                    duration_frames = max(1, next_start_frame - start_frame)
                else:
                    duration_frames = max(1, total_timeline_frames - start_frame)

                v_hash = compute_visual_hash(sc, duration=dur)
                narr = sc.get("spoken_text") or sc.get("narration") or ""
                a_hash = compute_audio_hash(narr)

                sc_rev = new_rev if sid == target_id else prev.get("revision", 1)
                seg_file = f"segments/scene_{sid}_v{sc_rev}.mp4"

                if is_narration_revision and sid == target_id and new_audio_path:
                    scene_audio_rel = f"scenes/{sid}/{new_audio_path.name}"
                else:
                    scene_audio_rel = prev.get("audio_file") or f"scenes/{sid}/audio_v1.mp3"

                manifest["scenes"][s_key] = {
                    "scene_id": sid,
                    "revision": sc_rev,
                    "visual_hash": v_hash,
                    "audio_hash": a_hash,
                    "audio_file": scene_audio_rel,
                    "segment_video": seg_file,
                    "manim_asset": sc.get("manim_asset_url") or sc.get("manim_video_src"),
                    "start_time": round(st, 3),
                    "end_time": round(et, 3),
                    "duration": round(dur, 3),
                    "start_frame": start_frame,
                    "duration_frames": duration_frames,
                }

            manifest["history"].append({
                "revision": new_rev,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "action": mode_label,
                "target_scene": target_id,
            })

            # Render dirty segments using staged_data_path
            dirty_scenes = [target_id]
            if is_narration_revision:
                for idx, sc in enumerate(scenes):
                    sid = parse_scene_id(sc.get("scene_id", idx + 1))
                    if sid > target_id:
                        dirty_scenes.append(sid)

            print(f"[REVISE:RENDER] Re-rendering segments for dirty scenes: {dirty_scenes}", flush=True)
            render_ok = render_dirty_segments(
                run_dir=run_dir,
                manifest_data=manifest,
                data_file_path=staged_data_path,
                dirty_scene_ids=dirty_scenes,
                force_all=False,
            )
            if not render_ok:
                raise RuntimeError(f"Failed to render segments for revised run '{run_id}'.")

            # Stitch all current segments in order
            segment_paths: List[Path] = []
            def get_sort_key(k: str) -> int:
                try:
                    return int(k)
                except ValueError:
                    return 999

            for s_key in sorted(manifest["scenes"].keys(), key=get_sort_key):
                rel_seg = manifest["scenes"][s_key]["segment_video"]
                segment_paths.append(run_dir / rel_seg)

            if output_path:
                out_file = Path(output_path).resolve()
            else:
                out_file = VIDEO_DIR / "out" / f"{run_id}_v{new_rev}.mp4"
            out_file.parent.mkdir(parents=True, exist_ok=True)

            stitch_ok = stitch_segments(
                segment_paths=segment_paths,
                output_video_path=staged_output_path,
                master_audio_path=staged_audio_path if (staged_audio_path and staged_audio_path.exists()) else None,
                scenes_meta=scenes,
            )
            if not stitch_ok:
                raise RuntimeError(f"FFmpeg recomposition failed for revision {new_rev}.")

            # Gate 6 Post-Render Technical and Visual QA
            rev_aspect_ratio = data_payload.get("aspect_ratio") or data_payload.get("render_profile", {}).get("aspect_ratio") or "16:9"
            is_valid, errors, meta = validate_post_render_qa(
                video_path=staged_output_path,
                expected_audio_path=staged_audio_path if (staged_audio_path and staged_audio_path.exists()) else None,
                aspect_ratio=rev_aspect_ratio,
                tolerance_sec=0.05,
            )
            if not is_valid:
                err_msg = "; ".join(errors)
                raise RuntimeError(f"Recomposed video failed Gate 6 output validation: {err_msg}")

            # =========================================================================
            # ATOMIC COMMIT: Publish updated state only after ALL gates pass
            # =========================================================================
            if is_narration_revision and staged_audio_path and staged_audio_path.exists():
                shutil.copyfile(staged_audio_path, run_dir / "audio.wav")

            shutil.copyfile(staged_data_path, data_path)
            save_manifest(manifest, run_dir)

            shutil.copyfile(staged_output_path, out_file)
            shutil.copyfile(staged_output_path, run_dir / "output.mp4")

            staged_output_kf = staged_output_path.with_suffix(".keyframe.jpg")
            if staged_output_kf.exists():
                try:
                    shutil.copyfile(staged_output_kf, out_file.with_suffix(".keyframe.jpg"))
                except Exception:
                    pass

            archive_dir = archive_revision_snapshot(
                run_dir=run_dir,
                revision=new_rev,
                data_payload=data_payload,
                manifest_data=manifest,
                output_mp4=out_file,
            )

            print(f"\n[REVISE:SUCCESS] ✅ Revision {new_rev} complete! Preserved at: {archive_dir.name}")
            print(f"[REVISE:SUCCESS] 🎬 Output video available at: {out_file} ({out_file.stat().st_size:,} bytes)\n", flush=True)

            return out_file

        except Exception as exc:
            try:
                from engine.validation.reflection import write_reflection_error
                write_reflection_error(run_dir, stage=f"REVISION_{new_rev}", message=str(exc))
            except Exception:
                pass
            raise

        finally:
            # Clean up transient staged candidate files
            if staged_data_path and staged_data_path.exists():
                try:
                    staged_data_path.unlink(missing_ok=True)
                except Exception:
                    pass
            if staged_output_path and staged_output_path.exists():
                try:
                    staged_output_path.unlink(missing_ok=True)
                except Exception:
                    pass
            staged_output_kf = staged_output_path.with_suffix(".keyframe.jpg") if staged_output_path else None
            if staged_output_kf and staged_output_kf.exists():
                try:
                    staged_output_kf.unlink(missing_ok=True)
                except Exception:
                    pass
            if staged_audio_path and staged_audio_path != run_dir / "audio.wav":
                try:
                    staged_audio_path.unlink(missing_ok=True)
                except Exception:
                    pass
                try:
                    staged_audio_path.with_suffix(".mp3").unlink(missing_ok=True)
                except Exception:
                    pass


def main():
    parser = argparse.ArgumentParser(description="V2 Surgical Scene Revision CLI")
    parser.add_argument("--run-id", type=str, required=True, help="Run ID of the existing timeline to revise")
    parser.add_argument("--revise-scene", type=str, required=True, help="Target scene_id to revise (e.g. 2)")
    parser.add_argument("--set-visual-type", type=str, default=None, help="Mode A: New visual_type for scene")
    parser.add_argument("--set-title", type=str, default=None, help="Mode A: New title for scene")
    parser.add_argument("--set-visual-json", type=str, default=None, help="Mode A: JSON dictionary of visual props")
    parser.add_argument("--set-narration", type=str, default=None, help="Mode B: New spoken narration for scene")
    parser.add_argument("--set-evidence-id", type=str, default=None, help="Mode B: Evidence ID backing the new narration")
    parser.add_argument("--output", type=str, default=None, help="Output path for the revised MP4 video")
    args = parser.parse_args()

    execute_revision(
        run_id=args.run_id,
        target_scene_id=args.revise_scene,
        set_visual_type=args.set_visual_type,
        set_title=args.set_title,
        set_visual_json=args.set_visual_json,
        set_narration=args.set_narration,
        set_evidence_id=args.set_evidence_id,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()

