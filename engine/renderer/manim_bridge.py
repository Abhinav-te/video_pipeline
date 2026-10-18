"""
engine/renderer/manim_bridge.py

Stage 4.5 Sub-Renderer Bridge:
Pre-renders high-precision Manim Community animations for up to 2 key mathematical,
graph, or quantum scenes per video. Embeds the generated MP4 clips into Remotion
via scene["manim_video_src"] with a bulletproof 45-second timeout and graceful fallback
to native Remotion SVGs.
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
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))


def is_manim_available() -> bool:
    """Checks whether Manim Community is installed and importable in this Python environment."""
    try:
        import manim  # noqa: F401
        return True
    except ImportError:
        return False


def _run_manim_clip_subprocess(template_name: str, params: Dict[str, Any], output_path: Path, timeout: float = 45.0) -> bool:
    """Executes scene rendering inside an isolated subprocess with strict OS-level timeout."""
    python_exec = ENGINE_DIR / ".venv" / "bin" / "python"
    if not python_exec.exists():
        python_exec = Path(sys.executable)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as pf:
        json.dump(params, pf)
        params_file = Path(pf.name)

    cmd = [
        str(python_exec),
        "-m",
        "engine.renderer.manim_bridge",
        "--render-clip",
        "--template",
        template_name,
        "--params-file",
        str(params_file),
        "--output",
        str(output_path),
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_DIR}:{ENGINE_DIR}:{env.get('PYTHONPATH', '')}"

    try:
        res = subprocess.run(cmd, cwd=str(REPO_DIR), env=env, capture_output=True, text=True, timeout=timeout)
        if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
            return True
        else:
            err_msg = res.stderr[-500:] if res.stderr else f"Process exited with code {res.returncode}"
            print(f"[MANIM:WARN] Subprocess failed for template '{template_name}': {err_msg}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"[MANIM:WARN] Subprocess timed out after {timeout}s for template '{template_name}'", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[MANIM:WARN] Subprocess execution exception for template '{template_name}': {exc}", file=sys.stderr)
        return False
    finally:
        if params_file.exists():
            try:
                params_file.unlink()
            except Exception:
                pass


def resolve_manim_template(scene: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Resolves template name and extracts normalized parameters from scene payload."""
    sub_mode = (scene.get("sub_mode") or "").lower()
    visual_type = (scene.get("visual_type") or scene.get("scene_type") or "").lower()

    duration = 4.0
    start_time = scene.get("start_time")
    end_time = scene.get("end_time")
    if start_time is not None and end_time is not None:
        duration = max(2.5, float(end_time) - float(start_time))

    title = scene.get("title") or "MATHEMATICAL SIMULATION"

    # Template 1: Equation Morph
    if sub_mode == "equation_morph" or visual_type == "math_equation":
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

        return "equation_morph", {
            "steps": norm_steps,
            "duration": duration,
            "title": title,
        }

    # Template 2: Calculus Graph
    elif sub_mode == "calculus_graph" or visual_type == "function_graph":
        curves = scene.get("curves") or scene.get("functions") or scene.get("graph_data", {}).get("curves") or []
        first_curve = curves[0] if isinstance(curves, list) and curves else ""
        fn_str = first_curve if isinstance(first_curve, str) else (first_curve.get("fn") or "0.4 * x**2 + 0.2")

        return "calculus_graph", {
            "fn_str": fn_str,
            "duration": duration,
            "title": title,
        }

    # Template 3: Vector Field & Linear Transform
    elif sub_mode == "vector_field":
        matrix = scene.get("matrix") or [[1.5, 0.5], [0.5, 1.2]]
        return "vector_field", {
            "matrix": matrix,
            "duration": duration,
            "title": title,
        }

    # Template 4: Quantum Wavepacket Tunneling
    elif sub_mode == "quantum_wave" or visual_type in ("quantum_sim", "quantum_physics"):
        barrier_x = float(scene.get("barrier_x", 0.0))
        return "quantum_wave", {
            "barrier_x": barrier_x,
            "duration": duration,
            "title": title,
        }

    # Default fallback
    return "equation_morph", {
        "steps": [],
        "duration": duration,
        "title": title,
    }


def render_manim_clips_for_timeline(
    timeline_data: Any,
    run_dir: Path,
    enable_manim: bool = True,
    max_clips: int = 2,
) -> Any:
    """
    Stage 4.5 Sub-Renderer Bridge:
    Pre-renders up to max_clips (default 2) mathematical, graph, or quantum scenes using Manim Community.
    Injects scene["manim_video_src"] = f"runs/{run_dir.name}/manim_scene_{id}.mp4".
    Falls back gracefully without raising errors if Manim is unavailable, disabled, or fails.
    """
    run_dir = Path(run_dir)

    if not enable_manim:
        print("[MANIM:INFO] Manim sub-renderer disabled via --no-manim; using native Remotion SVG renderers.", flush=True)
        return timeline_data

    if not is_manim_available():
        print("[MANIM:INFO] Manim Community unavailable in environment; using native Remotion SVG renderers.", flush=True)
        return timeline_data

    # Extract scene list
    is_dict_payload = isinstance(timeline_data, dict) and "scenes" in timeline_data
    scenes = timeline_data["scenes"] if is_dict_payload else (timeline_data if isinstance(timeline_data, list) else [])

    if not scenes:
        return timeline_data

    # Eligible scene types for 3Blue1Brown-style Manim sub-rendering
    eligible_types = {"math_equation", "function_graph", "quantum_sim", "quantum_physics", "manim_scene"}
    eligible_sub_modes = {"equation_morph", "calculus_graph", "vector_field", "quantum_wave"}

    candidates: List[Tuple[int, Dict[str, Any]]] = []
    for idx, sc in enumerate(scenes):
        v_type = sc.get("visual_type") or sc.get("scene_type") or ""
        s_mode = sc.get("sub_mode") or ""
        if v_type in eligible_types or s_mode in eligible_sub_modes:
            candidates.append((idx, sc))

    if not candidates:
        print("[MANIM:INFO] No mathematical/graph scenes requiring Manim pre-render in this short.", flush=True)
        return timeline_data

    # Select at most max_clips scenes to keep total pre-render overhead under ~10-15s
    selected = candidates[:max_clips]
    print(f"[MANIM:START] Pre-rendering {len(selected)} Manim canvas clip(s) for run '{run_dir.name}'...", flush=True)

    rendered_count = 0
    for scene_idx, scene in selected:
        scene_id = scene.get("scene_id") or scene.get("scene_index") or scene_idx
        out_clip_name = f"manim_scene_{scene_id}.mp4"
        out_clip_path = run_dir / out_clip_name

        template_name, params = resolve_manim_template(scene)
        print(f"[MANIM:RENDER] Rendering Scene #{scene_id} with template '{template_name}' ({params['duration']:.1f}s)...", flush=True)

        success = _run_manim_clip_subprocess(
            template_name=template_name,
            params=params,
            output_path=out_clip_path,
            timeout=45.0,
        )

        if success:
            rel_src = f"runs/{run_dir.name}/{out_clip_name}"
            scene["manim_video_src"] = rel_src
            rendered_count += 1
            print(f"[MANIM:SUCCESS] Scene #{scene_id} ready -> {rel_src}", flush=True)
        else:
            print(f"[MANIM:WARN] Scene #{scene_id} render failed or timed out; falling back to native Remotion SVG.", flush=True)

    print(f"[MANIM:FINISH] Successfully integrated {rendered_count}/{len(selected)} Manim clip(s) into Remotion timeline.", flush=True)
    return timeline_data


# ---------------------------------------------------------------------------
# Standalone CLI Subprocess Runner
# ---------------------------------------------------------------------------

def _cli_render_clip():
    """CLI entrypoint invoked by the subprocess to render an individual clip."""
    parser = argparse.ArgumentParser(description="Manim Sub-Renderer Subprocess Worker")
    parser.add_argument("--render-clip", action="store_true", required=True)
    parser.add_argument("--template", type=str, required=True, choices=["equation_morph", "calculus_graph", "vector_field", "quantum_wave"])
    parser.add_argument("--params-file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    with open(args.params_file, "r", encoding="utf-8") as f:
        params = json.load(f)

    from engine.renderer.manim_templates import (
        ManimEquationMorphScene,
        ManimCalculusGraphScene,
        ManimLinearVectorScene,
        ManimQuantumWaveScene,
        configure_manim_environment,
    )
    import shutil
    from manim import config

    out_file = Path(args.output).resolve()
    temp_dir = Path(tempfile.mkdtemp(prefix="manim_worker_"))

    configure_manim_environment(
        media_dir=str(temp_dir),
        output_file=out_file.name,
    )

    template_map = {
        "equation_morph": ManimEquationMorphScene,
        "calculus_graph": ManimCalculusGraphScene,
        "vector_field": ManimLinearVectorScene,
        "quantum_wave": ManimQuantumWaveScene,
    }

    scene_cls = template_map[args.template]
    scene_instance = scene_cls(**params)
    scene_instance.render()

    # Move rendered mp4 to designated output path
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
        _cli_render_clip()
