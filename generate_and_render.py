import subprocess
import argparse
import os
import sys
import glob
import re

def get_next_video_index(public_dir):
    video_files = glob.glob(os.path.join(public_dir, "final_video_*.mp4"))
    indices = []
    for f in video_files:
        match = re.search(r'final_video_(\d+)\.mp4', f)
        if match:
            indices.append(int(match.group(1)))
    return max(indices) + 1 if indices else 1

def main():
    parser = argparse.ArgumentParser(description="V2 Video Engine: One-Click Pipeline")
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--length", type=int, choices=[15, 30, 60], default=60)
    parser.add_argument("--no-cache", action="store_true", help="Force regenerate AI script")
    args = parser.parse_args()

    print(f"\n🚀 STARTING V2 PIPELINE: {args.topic.upper()}\n")

    engine_dir = os.path.expanduser("~/video_gen/engine")
    video_dir = os.path.expanduser("~/video_gen/video")
    public_dir = os.path.join(video_dir, "public")
    python_exec = os.path.join(engine_dir, ".venv/bin/python")
    gen_script = os.path.join(engine_dir, "generate.py")

    # data_file_path is needed by Phase 1's own success check, so define it up front.
    data_file_path = os.path.abspath(os.path.join(public_dir, "data_current.json"))

    # Compute the shared index ONCE, before generation, so audio_N.mp3,
    # data_N.json, and final_video_N.mp4 all end up as the same N.
    next_idx = get_next_video_index(public_dir)

    print("▶️ PHASE 1: AI Scripting & Edge-TTS...")

    cmd = [
        python_exec, gen_script,
        "--length", str(args.length),
        "--topic", args.topic,
        "--index", str(next_idx),
    ]
    if args.no_cache:
        cmd.append("--no-cache")

    try:
        subprocess.run(cmd, cwd=engine_dir, check=True)
    except subprocess.CalledProcessError:
        print("\n❌ FATAL: AI Generation failed.")
        sys.exit(1)

    # Only bail here if Phase 1 claimed success but somehow didn't write the file.
    if not os.path.exists(data_file_path):
        print("❌ FATAL: Phase 1 did not create data_current.json")
        sys.exit(1)

    out_file = f"public/final_video_{next_idx}.mp4"

    print("\n🧹 Clearing Remotion webpack/rspack cache...")
    cache_dir = os.path.join(video_dir, "node_modules", ".cache")
    if os.path.isdir(cache_dir):
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)

    print(f"\n▶️ PHASE 2: Rendering {out_file}...")
    try:
        subprocess.run(
            [
                "npx", "remotion", "render", "CodingShort", out_file,
                "--codec", "h264",
                "--props", data_file_path  # Force Remotion to physically read the file
            ],
            cwd=video_dir,
            check=True
        )
        print(f"\n✅ SUCCESS! Your upload-ready video is at: ~/video_gen/video/{out_file}")
    except subprocess.CalledProcessError:
        print("\n❌ FATAL: Remotion render failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()