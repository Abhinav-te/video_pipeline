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

from validation.output import validate_video_output


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


def main():
    parser = argparse.ArgumentParser(description="V2 Video Engine: One-Click Pipeline")
    parser.add_argument("--topic", type=str, required=True, help="Topic for the video short")
    parser.add_argument("--length", type=int, choices=[15, 30, 60], default=60, help="Target duration in seconds")
    parser.add_argument("--subject", type=str, choices=["auto", "code", "math", "physics", "systems", "ml", "chemistry", "quantum_physics", "mechanics", "electrical"], default="auto", help="Subject domain for video")
    parser.add_argument("--no-cache", action="store_true", help="Force regenerate AI script")
    parser.add_argument("--run-id", type=str, default=None, help="Explicit run ID (auto-generated if omitted)")
    parser.add_argument("--output", type=str, default=None, help="Explicit output MP4 path")
    parser.add_argument("--frames", type=str, default=None, help="Frame range to render (e.g. '0-89') for benchmarks")
    parser.add_argument("--fast-test", action="store_true", help="Quick 90-frame (3s) benchmark render (equivalent to --frames 0-89)")
    parser.add_argument("--no-manim", action="store_true", help="Disable Stage 4.5 Manim Community pre-rendering")
    args = parser.parse_args()

    if args.fast_test and not args.frames:
        args.frames = "0-89"

    topic = args.topic.strip()
    if not topic:
        stage_error("PIPELINE", "--topic cannot be empty.", exit_code=1)

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
        "--topic", args.topic,
        "--subject", args.subject,
        "--run-id", run_id,
    ]
    if args.no_cache:
        cmd.append("--no-cache")
    if args.no_manim:
        cmd.append("--no-manim")

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

    # Step 4: Render Video with Remotion
    stage_start("RENDER", f"Rendering {out_file_path.name} with props: {data_file_path}")

    remotion_cmd = [
        "npx", "remotion", "render", "CodingShort", remotion_out,
        "--codec", "h264",
        "--props", str(data_file_path),
    ]
    if args.frames:
        remotion_cmd.extend(["--frames", str(args.frames)])

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
        )
    except Exception as exc:
        is_valid = False
        errors = [f"Unexpected exception during output validation: {exc}"]
        meta = {}

    if not is_valid:
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

    stage_success("PIPELINE", f"Upload-ready video available at: {out_file_path}")


if __name__ == "__main__":
    main()