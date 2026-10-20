import argparse
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


# ---------------------------------------------------------------------------
# Path Resolution (Repository-Relative)
# ---------------------------------------------------------------------------

REPO_DIR = Path(__file__).resolve().parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"
PUBLIC_DIR = VIDEO_DIR / "public"
RUNS_DIR = PUBLIC_DIR / "runs"
OUT_DIR = VIDEO_DIR / "out"

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

# Auto re-exec into engine virtualenv if running under standard system Python
VENV_PYTHON = ENGINE_DIR / ".venv" / "bin" / "python"
if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from validation.output import validate_video_output
from validation.reflection import write_reflection_error
from renderer.lambda_dispatcher import dispatch_lambda_render
from pipeline.manifest import init_manifest, archive_revision_snapshot, load_manifest, create_baseline_artifacts
from revise import execute_revision


# ---------------------------------------------------------------------------
# Run Identification & Logging
# ---------------------------------------------------------------------------

def generate_run_id() -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    return f"run_{timestamp}_{short_id}"


def stage_start(stage: str, message: str):
    print(f"[{stage}:START] {message}", flush=True)


def stage_success(stage: str, message: str):
    print(f"[{stage}:SUCCESS] {message}", flush=True)


def stage_error(stage: str, message: str, exit_code: int = 1):
    print(f"\n[{stage}:ERROR] {message}", file=sys.stderr, flush=True)
    sys.exit(exit_code)


def get_next_video_index(public_dir):
    video_files = glob.glob(os.path.join(str(public_dir), "final_video_*.mp4"))
    indices = []
    for f in video_files:
        match = re.search(r'final_video_(\d+)\.mp4', f)
        if match:
            indices.append(int(match.group(1)))
    return max(indices) + 1 if indices else 1


def load_dotenv():
    """Loads environment variables from .env if present into os.environ."""
    env_file = REPO_DIR / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="V2 Video Engine: One-Click Pipeline")
    parser.add_argument("--topic", type=str, default=None, help="Topic for the video short")
    parser.add_argument("--length", type=int, choices=[15, 30, 35, 60], default=60, help="Target duration in seconds")
    parser.add_argument("--project", type=str, default=None, help="Path to project configuration JSON file (e.g. projects/project_profile.json)")
    parser.add_argument("--subject", type=str, choices=["auto", "code", "devtools", "math", "physics", "systems", "ml", "chemistry", "quantum_physics", "mechanics", "electrical"], default="auto", help="Subject domain for video")
    parser.add_argument("--source-file", type=str, default=None, help="Path to source documentation, README, changelog, or code snippet")
    parser.add_argument("--source-url", type=str, default=None, help="Public documentation or GitHub README URL to ingest")
    parser.add_argument("--source-text", type=str, default=None, help="Raw source markdown or code text")
    parser.add_argument("--no-cache", action="store_true", help="Force regenerate AI script")
    parser.add_argument("--run-id", type=str, default=None, help="Explicit run ID (auto-generated if omitted)")
    parser.add_argument("--output", type=str, default=None, help="Explicit output MP4 path")
    parser.add_argument("--frames", type=str, default=None, help="Frame range to render (e.g. '0-89') for benchmarks")
    parser.add_argument("--fast-test", action="store_true", help="Quick 90-frame (3s) benchmark render (equivalent to --frames 0-89)")
    parser.add_argument("--no-manim", action="store_true", help="Disable Stage 4.5 Manim Community pre-rendering")
    parser.add_argument("--mock", action="store_true", help="Bypass Gemini API calls and load pre-validated mock script")
    parser.add_argument("--render-backend", choices=["local", "lambda"], default="local", help="Rendering backend (local or AWS Remotion Lambda)")
    # Revision CLI Entrypoints (Checkpoint 02)
    parser.add_argument("--revise-scene", type=str, default=None, help="Target scene_id to surgically revise (Mode A or B)")
    parser.add_argument("--set-visual-type", type=str, default=None, help="Mode A: New visual_type for scene")
    parser.add_argument("--set-title", type=str, default=None, help="Mode A: New title for scene")
    parser.add_argument("--set-visual-json", type=str, default=None, help="Mode A: JSON dictionary of visual props")
    parser.add_argument("--set-narration", type=str, default=None, help="Mode B: New spoken narration for scene")
    parser.add_argument("--set-evidence-id", type=str, default=None, help="Mode B: Evidence ID backing new narration")
    parser.add_argument("--aspect-ratio", type=str, choices=["16:9", "9:16"], default=None, help="Aspect ratio: 16:9 widescreen or 9:16 vertical")
    args = parser.parse_args()

    # Dispatch to surgical scene revision engine if --revise-scene is present
    if args.revise_scene:
        if not args.run_id:
            stage_error("REVISE", "--run-id is required when using --revise-scene.", exit_code=1)
        out_file = execute_revision(
            run_id=args.run_id,
            target_scene_id=args.revise_scene,
            set_visual_type=args.set_visual_type,
            set_title=args.set_title,
            set_visual_json=args.set_visual_json,
            set_narration=args.set_narration,
            set_evidence_id=args.set_evidence_id,
            output_path=args.output,
        )
        stage_success("REVISE", f"Revision complete! Video saved to {out_file}")
        return

    if args.fast_test and not args.frames:
        args.frames = "0-89"

    topic = (args.topic or "").strip()
    aspect_ratio = args.aspect_ratio
    if args.project:
        proj_p = Path(args.project).resolve()
        if not proj_p.exists():
            stage_error("PIPELINE", f"Project file not found: {proj_p}", exit_code=1)
        import json
        with open(proj_p, "r", encoding="utf-8") as pf:
            p_data = json.load(pf)
        p_profile = p_data.get("project_profile", p_data)
        topic = topic or p_profile.get("topic") or p_profile.get("product") or "Technical Feature"
        if args.length == 60 and p_profile.get("duration_target_seconds"):
            args.length = int(p_profile.get("duration_target_seconds"))
        if args.subject == "auto" and p_profile.get("subject"):
            args.subject = p_profile.get("subject")
        if not aspect_ratio:
            aspect_ratio = p_data.get("render_profile", {}).get("aspect_ratio") or p_profile.get("aspect_ratio")

    if not aspect_ratio:
        aspect_ratio = "16:9"

    is_vertical = (aspect_ratio == "9:16")
    render_width = 1080 if is_vertical else 1920
    render_height = 1920 if is_vertical else 1080

    if not topic:
        stage_error("PIPELINE", "Either --topic or --project is required.", exit_code=1)

    run_id = args.run_id or generate_run_id()

    stage_start("PIPELINE", f"Run ID: {run_id} | Topic: '{topic}' | Subject: {args.subject} | Length: {args.length}s")

    python_exec = ENGINE_DIR / ".venv" / "bin" / "python"
    if not python_exec.exists():
        python_exec = Path(sys.executable)

    gen_script = ENGINE_DIR / "generate.py"

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    data_file_path = run_dir / "data.json"

    # Step 1: Execute Python Generation Subprocess
    cmd = [
        str(python_exec), str(gen_script),
        "--length", str(args.length),
        "--subject", args.subject,
        "--run-id", run_id,
    ]
    if topic:
        cmd.extend(["--topic", topic])
    if args.project:
        cmd.extend(["--project", str(Path(args.project).resolve())])
    if args.no_cache:
        cmd.append("--no-cache")
    if args.no_manim:
        cmd.append("--no-manim")
    if args.mock:
        cmd.append("--mock")
    if args.source_file:
        cmd.extend(["--source-file", str(Path(args.source_file).resolve())])
    if args.source_url:
        cmd.extend(["--source-url", args.source_url])
    if args.source_text:
        cmd.extend(["--source-text", args.source_text])

    gen_env = os.environ.copy()
    gen_env["PYTHONPATH"] = f"{REPO_DIR}:{ENGINE_DIR}:{gen_env.get('PYTHONPATH', '')}"

    try:
        res = subprocess.run(cmd, cwd=str(ENGINE_DIR), env=gen_env)
        if res.returncode != 0:
            if run_dir.exists():
                shutil.rmtree(run_dir, ignore_errors=True)
            stage_error("PIPELINE", f"AI generation stage failed with exit code {res.returncode}.", exit_code=res.returncode)
    except Exception as exc:
        if run_dir.exists():
            shutil.rmtree(run_dir, ignore_errors=True)
        stage_error("PIPELINE", f"Failed to execute generation script: {exc}", exit_code=1)

    # Pre-render verification: ensure data.json exists and is populated
    if not data_file_path.exists():
        stage_error("VALIDATION", f"Generation completed but {data_file_path.name} was not created at {data_file_path}")

    if data_file_path.stat().st_size == 0:
        stage_error("VALIDATION", f"Generated data file is empty: {data_file_path}")

    # Inject chosen aspect ratio & dimensions into data payload
    try:
        with open(data_file_path, "r", encoding="utf-8") as df:
            d_payload = json.load(df)
        d_payload["aspect_ratio"] = aspect_ratio
        if "render_profile" not in d_payload:
            d_payload["render_profile"] = {}
        d_payload["render_profile"]["aspect_ratio"] = aspect_ratio
        d_payload["render_profile"]["width"] = render_width
        d_payload["render_profile"]["height"] = render_height
        with open(data_file_path, "w", encoding="utf-8") as df:
            json.dump(d_payload, df, indent=2)
    except Exception as exc:
        print(f"[ENGINE:WARN] Failed to stamp aspect ratio into data payload: {exc}", file=sys.stderr)

    # Step 1.4: Evidence Validation Gate (Phase 4)
    stage_start("EVIDENCE_GATE", "Validating 100% claim backing and factual integrity...")
    ev_pack_path = run_dir / "evidence_pack.json"
    if ev_pack_path.exists():
        try:
            from validation.evidence_validator import validate_evidence_and_plan
            import json
            with open(ev_pack_path, "r", encoding="utf-8") as f:
                ev_pack_data = json.load(f)
            with open(data_file_path, "r", encoding="utf-8") as f:
                data_json_payload = json.load(f)
            val_report = validate_evidence_and_plan(ev_pack_data, data_json_payload)
            with open(run_dir / "validation_report.json", "w", encoding="utf-8") as f:
                json.dump(val_report.model_dump(), f, indent=2)
            if not val_report.passed:
                write_reflection_error(
                    run_dir=run_dir,
                    stage="evidence_gate",
                    message=f"Evidence validation gate failed: {val_report.checks}",
                )
                stage_error("EVIDENCE_GATE", "Evidence validation gate failed. Review validation_report.json", exit_code=1)
            stage_success("EVIDENCE_GATE", f"Evidence validation passed with {val_report.claim_coverage_pct}% claim coverage.")
        except Exception as exc:
            stage_error("EVIDENCE_GATE", f"Evidence validation execution failed: {exc}", exit_code=1)

    # Step 1.5: Stage 4.8 - Node.js TypeScript Zod Validation Gate
    stage_start("ZOD_GATE", f"Validating {data_file_path.name} against TypeScript Zod schema...")
    zod_script = VIDEO_DIR / "scripts" / "validate_timeline.mjs"
    try:
        zod_res = subprocess.run(["node", str(zod_script), str(data_file_path)], cwd=str(VIDEO_DIR))
        if zod_res.returncode != 0:
            write_reflection_error(
                run_dir=run_dir,
                stage="zod_gate",
                message=f"Node.js Zod validation gate failed on {data_file_path.name}",
            )
            stage_error("ZOD_GATE", f"Node.js Zod validation gate failed. Review {run_dir}/validation.error.json", exit_code=zod_res.returncode)
    except Exception as exc:
        write_reflection_error(
            run_dir=run_dir,
            stage="zod_gate",
            message=f"Failed to execute Zod validation subprocess: {exc}",
        )
        stage_error("ZOD_GATE", f"Failed to execute Zod validation subprocess: {exc}", exit_code=1)

    stage_success("ZOD_GATE", "Timeline schema successfully verified by Zod gate.")

    # Step 2: Clear Remotion build cache
    cache_dir = VIDEO_DIR / "node_modules" / ".cache"
    if cache_dir.is_dir():
        shutil.rmtree(cache_dir, ignore_errors=True)

    # Step 3: Determine output path
    if args.output:
        out_file_path = Path(args.output).resolve()
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_file_path = (OUT_DIR / f"{run_id}.mp4").resolve()

    out_file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        remotion_out = str(out_file_path.relative_to(VIDEO_DIR))
    except ValueError:
        remotion_out = str(out_file_path)

    # Step 4: Render Video with Remotion (Lambda or Local Engine)
    remotion_cmd = [
        "npx", "remotion", "render", "CodingShort", remotion_out,
        "--codec", "h264",
        "--props", str(data_file_path),
    ]
    if args.frames:
        remotion_cmd.extend(["--frames", str(args.frames)])

    if args.render_backend == "lambda":
        stage_start("RENDER_LAMBDA", f"Dispatching render to AWS Remotion Lambda: {out_file_path.name}")
        lambda_ok = dispatch_lambda_render(
            data_file_path=data_file_path,
            output_file_path=out_file_path,
            frames=args.frames,
        )
        if not lambda_ok:
            stage_start("RENDER_LOCAL", f"Rendering locally {out_file_path.name} with props: {data_file_path}")
            try:
                res = subprocess.run(remotion_cmd, cwd=str(VIDEO_DIR))
                if res.returncode != 0:
                    stage_error("RENDER", f"Remotion render failed with exit code {res.returncode}.", exit_code=res.returncode)
            except Exception as exc:
                stage_error("RENDER", f"Failed to execute Remotion subprocess: {exc}", exit_code=1)
    else:
        stage_start("RENDER", f"Rendering {out_file_path.name} with props: {data_file_path}")
        try:
            res = subprocess.run(remotion_cmd, cwd=str(VIDEO_DIR))
            if res.returncode != 0:
                stage_error("RENDER", f"Remotion render failed with exit code {res.returncode}.", exit_code=res.returncode)
        except Exception as exc:
            stage_error("RENDER", f"Failed to execute Remotion subprocess: {exc}", exit_code=1)

    stage_success("RENDER", f"Video rendered successfully: {out_file_path}")

    # Step 5: Stage 6 - Post-Render Output Validation
    stage_start("OUTPUT_VALIDATION", f"Inspecting rendered video: {out_file_path.name}")

    audio_file_path = run_dir / "audio.mp3"

    try:
        is_valid, errors, meta = validate_video_output(
            video_path=out_file_path,
            expected_audio_path=audio_file_path if (audio_file_path.exists() and not args.frames) else None,
            tolerance_sec=1.5,
            aspect_ratio=aspect_ratio,
            expected_width=render_width,
            expected_height=render_height,
        )
    except Exception as exc:
        is_valid = False
        errors = [f"Unexpected exception during output validation: {exc}"]
        meta = {}

    if not is_valid:
        write_reflection_error(
            run_dir=run_dir,
            stage="output_validation",
            message="Rendered video failed output validation",
            errors=errors,
        )
        # Quarantine or clean up corrupt video
        if out_file_path.exists():
            quarantine_path = out_file_path.with_name(f"{out_file_path.stem}.corrupt{out_file_path.suffix}")
            try:
                shutil.move(str(out_file_path), str(quarantine_path))
                print(f"[OUTPUT_VALIDATION:WARN] Corrupt output quarantined to {quarantine_path}", file=sys.stderr)
            except Exception:
                out_file_path.unlink(missing_ok=True)

        err_details = "\n".join(f"  • {e}" for e in errors)
        stage_error(
            "OUTPUT_VALIDATION",
            f"Rendered video failed output validation:\n{err_details}",
            exit_code=1,
        )

    vid_dur = meta.get("video_duration", 0.0)
    width = meta.get("width", 0)
    height = meta.get("height", 0)
    stage_success(
        "OUTPUT_VALIDATION",
        f"Video verified: {width}x{height}, h264/aac, duration {vid_dur:.2f}s ({out_file_path.stat().st_size:,} bytes)"
    )

    # Step 6: Initialize manifest & baseline segments for surgical revisions (Checkpoint 02)
    try:
        import json
        with open(data_file_path, "r", encoding="utf-8") as f:
            data_payload = json.load(f)
        scenes = data_payload.get("scenes", [])
        manifest = load_manifest(run_dir)
        if not manifest:
            manifest = init_manifest(run_id, run_dir, scenes)

        create_baseline_artifacts(
            run_dir=run_dir,
            data_payload=data_payload,
            master_video_path=out_file_path,
            master_audio_path=audio_file_path,
        )

        archive_revision_snapshot(
            run_dir=run_dir,
            revision=1,
            data_payload=data_payload,
            manifest_data=manifest,
            output_mp4=out_file_path,
        )
        stage_success("MANIFEST", f"Artifact manifest initialized and revision 1 archived at revisions/rev_001/")
    except Exception as exc:
        print(f"[MANIFEST:WARN] Non-critical error archiving baseline revision: {exc}", file=sys.stderr)

    stage_success("PIPELINE", f"Upload-ready video available at: {out_file_path}")


if __name__ == "__main__":
    main()