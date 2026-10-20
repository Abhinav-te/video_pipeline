"""
engine/renderer/manim_compiler.py

Headless Manim Pre-Compiler Bridge (Stage 4.5):
Compiles parameterized 3Blue1Brown-style vector animations directly into
video/public/runs/<run_id>/assets/manim_scene_<scene_id>.mp4 at 920x920, 30fps.
Guarantees execution via sys.executable and verifies output with ffprobe (>10KB).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_DIR = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from engine.renderer.manim_templates import (
    ManimEquationMorphScene,
    ManimCalculusGraphScene,
    ManimRiemannRefinementScene,
    ManimAntiderivativeBoundsScene,
    ManimLinearVectorScene,
    ManimQuantumWaveScene,
    configure_manim_environment,
    MANIM_AVAILABLE,
)
from engine.validation.manim_verifier import verify_manim_clip


def get_python_executable() -> Path:
    """Returns the .venv Python binary if present, falling back to sys.executable."""
    venv_python = ENGINE_DIR / ".venv" / "bin" / "python"
    if venv_python.exists():
        return venv_python
    return Path(sys.executable)


def verify_manim_asset(video_path: Path, expected_duration: Optional[float] = None) -> Tuple[bool, float, int]:
    """
    Verifies that the compiled Manim video exists, is > 10KB, and has valid headers.
    Returns (is_valid, duration, file_size).
    """
    if not video_path.exists():
        return False, 0.0, 0
    size = video_path.stat().st_size
    if size < 10240:  # Must be > 10KB
        return False, 0.0, size

    if expected_duration is not None:
        is_valid, _, meta = verify_manim_clip(video_path, expected_duration=expected_duration)
        return is_valid, meta.get("actual_duration", 0.0), size

    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,codec_name",
        "-of", "json",
        str(video_path),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        meta = json.loads(res.stdout)
        stream = meta.get("streams", [{}])[0]
        dur = float(stream.get("duration", 0.0))
        return True, dur, size
    except Exception:
        # If ffprobe metadata parse fails, fallback to size check
        return size > 10240, 0.0, size


def render_scene_to_file(template: str, params: Dict[str, Any], output_path: Path, timeout: float = 60.0) -> bool:
    """
    Renders a single Manim template directly into output_path using sys.executable.
    """
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as pf:
        json.dump(params, pf)
        params_file = Path(pf.name)

    python_bin = get_python_executable()
    cmd = [
        str(python_bin),
        "-m",
        "engine.renderer.manim_compiler",
        "--render-clip",
        "--template",
        template,
        "--params-file",
        str(params_file),
        "--output",
        str(output_path),
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_DIR}:{ENGINE_DIR}:{env.get('PYTHONPATH', '')}"

    try:
        res = subprocess.run(cmd, cwd=str(REPO_DIR), env=env, capture_output=True, text=True, timeout=timeout)
        if params_file.exists():
            params_file.unlink(missing_ok=True)

        if res.returncode == 0 and output_path.exists():
            expected_dur = float(params.get("duration", 4.0))
            is_valid, errors, meta = verify_manim_clip(output_path, expected_duration=expected_dur)
            if is_valid:
                return True
            else:
                err_msg = "; ".join(errors)
                sz = meta.get("size_bytes", 0)
                print(f"[MANIM:WARN] Rendered file {output_path.name} failed verification: {err_msg} (size: {sz} bytes)", file=sys.stderr)
                return False
        else:
            err_msg = res.stderr[-500:] if res.stderr else f"Exit code {res.returncode}"
            print(f"[MANIM:WARN] Subprocess failed for {template}: {err_msg}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"[MANIM:WARN] Rendering timed out after {timeout}s for template '{template}'", file=sys.stderr)
        if params_file.exists():
            params_file.unlink(missing_ok=True)
        return False
    except Exception as exc:
        print(f"[MANIM:WARN] Exception during rendering: {exc}", file=sys.stderr)
        if params_file.exists():
            params_file.unlink(missing_ok=True)
        return False


def resolve_scene_manim_template(
    scene: Dict[str, Any],
    subject: str = "math",
    graph_scene_count: int = 0,
) -> Tuple[str, Dict[str, Any]]:
    """
    Resolves the most appropriate Manim template and parameters for a scene.
    Ensures that multiple graph scenes in the same video run distinct templates
    (e.g., Scene 3 runs calculus_graph, Scene 5 runs riemann_refinement or antiderivative_bounds).
    """
    visual_type = (scene.get("visual_type") or scene.get("scene_type") or "").lower()
    sub_mode = (scene.get("sub_mode") or "").lower()
    title = scene.get("title") or "MATHEMATICAL SIMULATION"

    duration = 4.0
    start_time = scene.get("start_time")
    end_time = scene.get("end_time")
    if start_time is not None and end_time is not None:
        duration = max(2.5, float(end_time) - float(start_time))

    # 1. Explicit manim_spec template override
    manim_spec = scene.get("manim_spec") or {}
    spec_template = (manim_spec.get("template") or "").lower()
    if spec_template == "riemann_refinement":
        return "riemann_refinement", {"duration": duration, "title": title}
    elif spec_template == "antiderivative_bounds":
        return "antiderivative_bounds", {"duration": duration, "title": title}
    elif spec_template == "calculus_graph":
        fn_expr = manim_spec.get("function_expr") or "0.4 * x**2 + 0.2"
        return "calculus_graph", {"fn_str": fn_expr, "duration": duration, "title": title}
    elif spec_template == "vector_field":
        matrix = manim_spec.get("matrix") or [[1.4, 0.4], [0.4, 1.2]]
        return "vector_field", {"matrix": matrix, "duration": duration, "title": title}
    elif spec_template == "quantum_wave":
        return "quantum_wave", {"barrier_x": float(manim_spec.get("barrier_x", 0.0)), "duration": duration, "title": title}

    # 2. Explicit sub_mode matches
    if sub_mode == "riemann_refinement":
        return "riemann_refinement", {"duration": duration, "title": title}
    if sub_mode == "antiderivative_bounds":
        return "antiderivative_bounds", {"duration": duration, "title": title}

    # Quantum Physics
    if subject == "quantum_physics" or visual_type in ("quantum_sim", "quantum_physics") or "quantum" in sub_mode:
        barrier_x = float(scene.get("barrier_x", 0.0))
        return "quantum_wave", {
            "barrier_x": barrier_x,
            "duration": duration,
            "title": title,
        }

    # Vector Field / Electrical Grid Phasor / Mechanics Flow
    if sub_mode == "vector_field" or visual_type in ("physics_sim", "electrical_grid", "mechanics_fbd"):
        matrix = scene.get("matrix") or [[1.4, 0.4], [0.4, 1.2]]
        return "vector_field", {
            "matrix": matrix,
            "duration": duration,
            "title": title,
        }

    # Calculus Graph / Function Graph
    if visual_type == "function_graph" or sub_mode == "calculus_graph" or "graph" in sub_mode:
        # If this is the second or subsequent graph scene in the video, render a distinct template!
        if graph_scene_count >= 1:
            return "riemann_refinement", {
                "duration": duration,
                "title": title or "RIEMANN INTEGRAL REFINEMENT",
            }

        curves = scene.get("curves") or scene.get("functions") or scene.get("graph_data", {}).get("curves") or []
        first_curve = curves[0] if isinstance(curves, list) and curves else ""
        fn_str = first_curve if isinstance(first_curve, str) else (first_curve.get("fn") or "0.4 * x**2 + 0.2")
        return "calculus_graph", {
            "fn_str": fn_str,
            "duration": duration,
            "title": title,
        }

    # Equation Morph (Default)
    raw_steps = (
        scene.get("steps")
        or scene.get("equations")
        or scene.get("choreography", {}).get("steps")
        or []
    )
    norm_steps = []
    for idx, s in enumerate(raw_steps):
        if isinstance(s, dict):
            norm_steps.append({
                "latex": s.get("latex") or s.get("formula") or "",
                "label": s.get("label") or s.get("explanation") or f"Step {idx + 1}",
            })
        elif isinstance(s, str):
            norm_steps.append({"latex": s, "label": f"Step {idx + 1}"})

    if not norm_steps:
        # Default equations based on domain
        if subject in ("quantum_physics", "quantum"):
            norm_steps = [
                {"latex": r"i\hbar \frac{\partial}{\partial t}\Psi = \hat{H}\Psi", "label": "Time-Dependent Schrödinger Eq."},
                {"latex": r"\hat{H} = -\frac{\hbar^2}{2m}\nabla^2 + V(x)", "label": "Hamiltonian Operator"},
            ]
        elif subject in ("electrical", "physics"):
            norm_steps = [
                {"latex": r"V_{th} = V_{oc},\quad R_{th} = \frac{V_{oc}}{I_{sc}}", "label": "Thévenin Equivalence"},
                {"latex": r"P_{max} = \frac{V_{th}^2}{4 R_{th}}\quad (\text{at } R_L = R_{th})", "label": "Max Power Transfer Theorem"},
            ]
        else:
            norm_steps = [
                {"latex": r"\int_{a}^{b} f(x)\,dx = F(b) - F(a)", "label": "Fundamental Theorem of Calculus"},
                {"latex": r"\frac{d}{dx}\left[ \int_{a}^{x} f(t)\,dt \right] = f(x)", "label": "First Fundamental Theorem"},
            ]

    return "equation_morph", {
        "steps": norm_steps,
        "duration": duration,
        "title": title,
    }


def compile_manim_scenes(
    timeline_data: Any,
    run_dir: Path,
    enable_manim: bool = True,
    max_clips: int = 5,
) -> Any:
    """
    Pre-compiles Manim animations for eligible scenes and stores .mp4 video layers directly
    in video/public/runs/<run_id>/assets/manim_scene_<scene_id>.mp4.
    Updates scene['manim_asset_url'] and scene['manim_video_src'].
    """
    run_dir = Path(run_dir)
    assets_dir = run_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    if not enable_manim:
        print("[MANIM:INFO] Manim compilation disabled via --no-manim flag.", flush=True)
        return timeline_data

    is_dict = isinstance(timeline_data, dict) and "scenes" in timeline_data
    scenes = timeline_data["scenes"] if is_dict else (timeline_data if isinstance(timeline_data, list) else [])
    if not scenes:
        return timeline_data

    subject = "auto"
    if is_dict:
        subject = timeline_data.get("subject") or timeline_data.get("domain") or "auto"
    elif scenes and isinstance(scenes[0], dict):
        subject = scenes[0].get("subject") or scenes[0].get("domain") or "auto"

    # Eligible scenes: scenes flagged with needs_manim or STEM body scenes
    # STEM subjects: math, quantum_physics, physics, mechanics, electrical
    is_stem = subject in ("math", "quantum_physics", "physics", "mechanics", "electrical")

    candidate_indices: List[int] = []
    for idx, sc in enumerate(scenes):
        if idx == 0:  # Skip hook scene
            continue
        if sc.get("needs_manim") or sc.get("visual_type") == "manim_scene":
            candidate_indices.append(idx)
        elif is_stem and sc.get("visual_type") in ("math_equation", "function_graph", "quantum_sim", "physics_sim", "electrical_grid", "mechanics_fbd", "comparison"):
            candidate_indices.append(idx)

    # Ensure at least 3 scenes (or 50% of body scenes) are selected for STEM subjects
    body_scene_count = max(1, len(scenes) - 2)
    min_manim_count = min(len(candidate_indices), max(3, int(round(body_scene_count * 0.5))))
    selected_indices = candidate_indices[:max(min_manim_count, min(len(candidate_indices), max_clips))]

    if not selected_indices:
        print("[MANIM:INFO] No candidate scenes identified for Manim pre-compilation.", flush=True)
        return timeline_data

    print(f"[MANIM:START] Compiling {len(selected_indices)} Manim vector scenes for run '{run_dir.name}'...", flush=True)

    compiled_count = 0
    graph_scene_count = 0
    for idx in selected_indices:
        scene = scenes[idx]
        scene_id = scene.get("scene_id", idx)
        out_filename = f"manim_scene_{scene_id}.mp4"
        out_path = assets_dir / out_filename

        template, params = resolve_scene_manim_template(scene, subject=subject, graph_scene_count=graph_scene_count)
        if template in ("calculus_graph", "riemann_refinement", "antiderivative_bounds"):
            graph_scene_count += 1

        print(f"[MANIM:COMPILE] 🎥 Rendering Scene {scene_id} ({template}) -> assets/{out_filename}", flush=True)

        success = render_scene_to_file(template=template, params=params, output_path=out_path, timeout=60.0)
        if success:
            rel_asset_url = f"runs/{run_dir.name}/assets/{out_filename}"
            scene["manim_asset_url"] = rel_asset_url
            scene["manim_video_src"] = rel_asset_url
            scene["visual_type"] = "manim_scene"
            scene["scene_type"] = "manim_scene"
            compiled_count += 1
            print(f"[MANIM:SUCCESS] Scene {scene_id} ready -> assets/{out_filename} ({out_path.stat().st_size:,} bytes)", flush=True)
        else:
            print(f"[MANIM:WARN] Scene {scene_id} failed Manim compilation; fallback to native Remotion SVG.", flush=True)

    print(f"[MANIM:FINISH] Successfully compiled {compiled_count}/{len(selected_indices)} Manim video layers.", flush=True)
    return timeline_data


# ---------------------------------------------------------------------------
# CLI Subprocess Worker for Single Clip
# ---------------------------------------------------------------------------

def _cli_worker():
    parser = argparse.ArgumentParser(description="Headless Manim Subprocess Worker")
    parser.add_argument("--render-clip", action="store_true", required=True)
    parser.add_argument(
        "--template",
        type=str,
        required=True,
        choices=[
            "equation_morph",
            "calculus_graph",
            "riemann_refinement",
            "antiderivative_bounds",
            "vector_field",
            "quantum_wave",
        ],
    )
    parser.add_argument("--params-file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    with open(args.params_file, "r", encoding="utf-8") as f:
        params = json.load(f)

    out_file = Path(args.output).resolve()
    temp_dir = Path(tempfile.mkdtemp(prefix="manim_worker_"))

    configure_manim_environment(
        media_dir=str(temp_dir),
        output_file=out_file.name,
    )

    template_map = {
        "equation_morph": ManimEquationMorphScene,
        "calculus_graph": ManimCalculusGraphScene,
        "riemann_refinement": ManimRiemannRefinementScene,
        "antiderivative_bounds": ManimAntiderivativeBoundsScene,
        "vector_field": ManimLinearVectorScene,
        "quantum_wave": ManimQuantumWaveScene,
    }

    scene_cls = template_map[args.template]
    scene_instance = scene_cls(**params)
    scene_instance.render()

    produced_file = scene_instance.renderer.file_writer.movie_file_path
    if produced_file and Path(produced_file).exists():
        out_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(produced_file, str(out_file))
        shutil.rmtree(temp_dir, ignore_errors=True)
        sys.exit(0)
    else:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Error: produced movie file not found at {produced_file}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if "--render-clip" in sys.argv:
        _cli_worker()
