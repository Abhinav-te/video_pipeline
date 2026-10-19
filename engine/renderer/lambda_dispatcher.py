"""
engine/renderer/lambda_dispatcher.py

Remotion Serverless Lambda Architecture Dispatcher (Step 5):
Dispatches video rendering jobs to AWS Remotion Lambda or falls back cleanly
to local rendering when AWS credentials (AWS_ACCESS_KEY_ID / REMOTION_AWS_ACCESS_KEY_ID)
are not present in environment variables.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

REPO_DIR = Path(__file__).resolve().parent.parent.parent
VIDEO_DIR = REPO_DIR / "video"


def check_aws_lambda_credentials() -> Tuple[bool, str]:
    """
    Checks if valid AWS Lambda credentials are configured for Remotion.
    Returns (is_ready, message).
    """
    access_key = os.getenv("REMOTION_AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("REMOTION_AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")

    if not access_key or not secret_key:
        return (
            False,
            "AWS credentials (REMOTION_AWS_ACCESS_KEY_ID / REMOTION_AWS_SECRET_ACCESS_KEY) not set in environment."
        )

    region = os.getenv("REMOTION_AWS_REGION") or os.getenv("AWS_REGION") or "us-east-1"
    bucket = os.getenv("REMOTION_AWS_BUCKET") or "remotion-lambda-renders"
    function_name = os.getenv("REMOTION_AWS_FUNCTION") or "remotion-render-4-0-522"

    return True, f"Credentials present for region: {region}, bucket: {bucket}, function: {function_name}"


def dispatch_lambda_render(
    data_file_path: Path,
    output_file_path: Path,
    frames: Optional[str] = None,
) -> bool:
    """
    Dispatches video render to Remotion Lambda cluster.
    If AWS credentials are missing, returns False so caller can fall back to local rendering.
    """
    is_ready, status_msg = check_aws_lambda_credentials()
    if not is_ready:
        print(f"[LAMBDA:FALLBACK] ⚠️ {status_msg}", flush=True)
        print("[LAMBDA:FALLBACK] Falling back cleanly to local multi-threaded Remotion rendering.", flush=True)
        return False

    region = os.getenv("REMOTION_AWS_REGION") or os.getenv("AWS_REGION") or "us-east-1"
    bucket = os.getenv("REMOTION_AWS_BUCKET") or "remotion-lambda-renders"
    function_name = os.getenv("REMOTION_AWS_FUNCTION") or "remotion-render-4-0-522"

    print(f"[LAMBDA:DISPATCH] ☁️ Dispatching render to AWS Remotion Lambda ({region})...", flush=True)

    cmd = [
        "npx", "remotion", "lambda", "render",
        "CodingShort",
        str(output_file_path),
        "--region", region,
        "--function-name", function_name,
        "--bucket-name", bucket,
        "--props", str(data_file_path),
    ]
    if frames:
        cmd.extend(["--frames", str(frames)])

    try:
        res = subprocess.run(cmd, cwd=str(VIDEO_DIR))
        if res.returncode == 0 and output_file_path.exists():
            print(f"[LAMBDA:SUCCESS] Render completed on Remotion Lambda: {output_file_path}", flush=True)
            return True
        else:
            print(f"[LAMBDA:WARN] Lambda render failed with exit code {res.returncode}. Falling back to local.", flush=True)
            return False
    except Exception as exc:
        print(f"[LAMBDA:WARN] Lambda invocation exception: {exc}. Falling back to local.", flush=True)
        return False

