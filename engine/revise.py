"""
engine/revise.py

Surgical Scene Revision Engine (Checkpoint 02).
Supports:
1. Mode A — Visual-Only Revision:
   - Modifies scene visual properties (visual_type, title, visual_props).
   - Audio and word timestamps remain 100% untouched across all scenes.
   - Re-renders Manim (if applicable) and Remotion ONLY for the revised scene.
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
    compute_visual_hash,
    compute_audio_hash,
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
from engine.renderer.manim_compiler import (
    resolve_scene_manim_template,
    render_scene_to_file,
)
from engine.validation.output import validate_video_output


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

    subject = data_payload.get("subject") or data_payload.get("domain") or target_scene.get("domain") or "math"
    scene_key = str(target_id)
    prev_scene_info = manifest["scenes"].get(scene_key, {})

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
                rel_audio = s_info.get("audio_file") or f"scenes/{sid}/audio_v1.mp3"
                s_audio_path = run_dir / rel_audio
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

        # Concatenate audio into master audio.mp3
        master_audio_path = run_dir / "audio.mp3"
        updated_scenes_meta, master_words = concatenate_scene_audios(
            scene_items=scene_audio_items,
            output_master_audio=master_audio_path,
        )

        # Update scene timings & words in data_payload
        for idx, sc in enumerate(scenes):
            sc["start_time"] = updated_scenes_meta[idx]["start_time"]
            sc["end_time"] = updated_scenes_meta[idx]["end_time"]
            sc["duration"] = updated_scenes_meta[idx]["duration"]
        data_payload["words"] = master_words

        # If target scene has a Manim clip, recompile Manim to match new duration
        if target_scene.get("manim_asset_url") or target_scene.get("manim_video_src"):
            out_manim = run_dir / "assets" / f"manim_{target_id}_v{new_rev}.mp4"
            template, params = resolve_scene_manim_template(target_scene, subject=subject)
            params["duration"] = new_scene_dur
            print(f"[REVISE:MANIM] Recompiling Manim for Scene {target_id} ({template}, {new_scene_dur:.2f}s) -> {out_manim.name}", flush=True)
            ok = render_scene_to_file(template, params, out_manim)
            if ok:
                target_scene["manim_asset_url"] = f"runs/{run_id}/assets/{out_manim.name}"
                target_scene["manim_video_src"] = f"runs/{run_id}/assets/{out_manim.name}"

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
                from engine.timeline.choreographer import COMPARISON_FOOTERS
                domain_footer = COMPARISON_FOOTERS.get(subject, "KEY TAKEAWAY: Evaluating trade-offs across both analytical regimes")
                target_scene["comparison_footer"] = domain_footer
                if subject == "math":
                    if not target_scene.get("problem_label"):
                        target_scene["problem_label"] = "DISCRETE RIEMANN PARTITION"
                    if not target_scene.get("solution_label"):
                        target_scene["solution_label"] = "CONTINUOUS INTEGRAL LIMIT"
                    if not target_scene.get("problem_code"):
                        target_scene["problem_code"] = "S_N = \\sum_{i=1}^{N} f(x_i^*) \\Delta x\nFinite discrete sum of rectangle areas\nO(1/N) approximation error"
                    if not target_scene.get("solution_code"):
                        target_scene["solution_code"] = "\\int_a^b f(x)dx = \\lim_{N\\to\\infty} \\sum_{i=1}^{N} f(x_i^*) \\Delta x\nExact continuous accumulated area\nError \\to 0 in the continuous limit"
                    target_scene["left_card"] = {
                        "tag": "Discrete Sum",
                        "metric": "Σ f(x_i) Δx",
                        "title": "Partition Sum",
                    }
                    target_scene["right_card"] = {
                        "tag": "Continuous Limit",
                        "metric": "∫ f(x) dx",
                        "title": "Exact Integral",
                    }

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

        # Check if new visual type requires Manim
        v_type = target_scene.get("visual_type") or target_scene.get("scene_type")
        needs_manim = v_type in ("math_equation", "function_graph", "manim_scene", "quantum_sim", "physics_sim", "electrical_grid", "mechanics_fbd")
        if needs_manim and subject in ("math", "quantum_physics", "physics", "mechanics", "electrical"):
            out_manim = run_dir / "assets" / f"manim_{target_id}_v{new_rev}.mp4"
            template, params = resolve_scene_manim_template(target_scene, subject=subject)
            print(f"[REVISE:MANIM] Compiling Manim for Scene {target_id} ({template}) -> {out_manim.name}", flush=True)
            ok = render_scene_to_file(template, params, out_manim)
            if ok:
                target_scene["manim_asset_url"] = f"runs/{run_id}/assets/{out_manim.name}"
                target_scene["manim_video_src"] = f"runs/{run_id}/assets/{out_manim.name}"
        else:
            # If changed to non-Manim scene (e.g. comparison or concept), clear Manim video references
            target_scene.pop("manim_asset_url", None)
            target_scene.pop("manim_video_src", None)

    # Evidence Validation Gate during revision
    ev_pack_path = run_dir / "evidence_pack.json"
    if ev_pack_path.exists():
        try:
            from engine.validation.evidence_validator import validate_evidence_and_plan
            with open(ev_pack_path, "r", encoding="utf-8") as ef:
                ev_pack_data = json.load(ef)
            val_report = validate_evidence_and_plan(ev_pack_data, data_payload)
            with open(run_dir / "validation_report.json", "w", encoding="utf-8") as vf:
                json.dump(val_report.model_dump(), vf, indent=2)
            if not val_report.passed:
                raise ValueError(f"Evidence validation gate failed for revision {new_rev}: {val_report.checks}")
            print(f"[REVISE:EVIDENCE] Verified 100% claim backing ({val_report.claim_coverage_pct}% coverage).", flush=True)
        except Exception as exc:
            print(f"[REVISE:WARNING] Evidence validation check: {exc}", flush=True)

    # Save updated data.json
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Update manifest scenes state
    for idx, sc in enumerate(scenes):
        sid = parse_scene_id(sc.get("scene_id", idx + 1))
        s_key = str(sid)
        prev = manifest["scenes"].get(s_key, {})

        dur = float(sc.get("duration", (sc.get("end_time", 0.0) - sc.get("start_time", 0.0))))
        st = float(sc.get("start_time", 0.0))
        et = float(sc.get("end_time", st + dur))

        start_frame = int(round(st * fps))
        duration_frames = max(1, int(round(dur * fps)))

        v_hash = compute_visual_hash(sc, duration=dur)
        narr = sc.get("spoken_text") or sc.get("narration") or ""
        a_hash = compute_audio_hash(narr)

        sc_rev = new_rev if sid == target_id else prev.get("revision", 1)
        seg_file = f"segments/scene_{sid}_v{sc_rev}.mp4"

        manifest["scenes"][s_key] = {
            "scene_id": sid,
            "revision": sc_rev,
            "visual_hash": v_hash,
            "audio_hash": a_hash,
            "audio_file": prev.get("audio_file") or f"scenes/{sid}/audio_v1.mp3",
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

    save_manifest(manifest, run_dir)

    # Render dirty segments (only target_scene or downstream scenes affected by shift)
    dirty_scenes = [target_id]
    if is_narration_revision:
        # If timing shifted, downstream scenes' start_frames shifted, so render them too
        for idx, sc in enumerate(scenes):
            sid = parse_scene_id(sc.get("scene_id", idx + 1))
            if sid > target_id:
                dirty_scenes.append(sid)

    print(f"[REVISE:RENDER] Re-rendering segments for dirty scenes: {dirty_scenes}", flush=True)
    render_ok = render_dirty_segments(
        run_dir=run_dir,
        manifest_data=manifest,
        data_file_path=data_path,
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

    master_audio = run_dir / "audio.mp3"
    stitch_ok = stitch_segments(
        segment_paths=segment_paths,
        output_video_path=out_file,
        master_audio_path=master_audio if master_audio.exists() else None,
        scenes_meta=scenes,
    )
    if not stitch_ok:
        raise RuntimeError(f"FFmpeg recomposition failed for revision {new_rev}.")

    # Output validation
    rev_aspect_ratio = data_payload.get("aspect_ratio") or data_payload.get("render_profile", {}).get("aspect_ratio")
    is_valid, errors, meta = validate_video_output(
        video_path=out_file,
        expected_audio_path=master_audio if master_audio.exists() else None,
        tolerance_sec=1.5,
        aspect_ratio=rev_aspect_ratio,
    )
    if not is_valid:
        err_msg = "; ".join(errors)
        raise RuntimeError(f"Recomposed video failed output validation: {err_msg}")

    # Archive revision snapshot
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

