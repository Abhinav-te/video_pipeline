# Agent Instructions: Video Pipeline Engine — Phase 14 Hybrid Manim Community (`manimce`) Sub-Renderer Integration

You are an expert systems and audio/video pipeline software engineer.
Your objective is to integrate **Manim Community (`manim`)** as a deterministic pre-render stage (`Stage 4.5`) that generates 3Blue1Brown-style mathematical animations (`TransformMatchingTex`, animated calculus curves, Riemann areas, vector fields, and quantum wavepackets) and embeds them seamlessly inside Remotion via `<OffthreadVideo>`.

---

## 1. System Architecture: Stage 4.5 Manim Bridge (`engine/renderer/manim_bridge.py`)

Do NOT replace Remotion as the master 1080x1920 compositor. Remotion remains the master frame controller (headers, kinetic subtitles, progress tabs, audio sync, and layout breathing). Manim renders high-precision animated canvases that slot directly into the center container.

### 1. Parameterized Manim Templates (`engine/renderer/manim_templates.py`)
Never ask the LLM to write raw arbitrary Python Manim code (which risks syntax/LaTeX crashes). Instead, build 4 rock-solid, parameterized Manim `Scene` classes configured with:
- `config.pixel_width = 920`
- `config.pixel_height = 920`
- `config.frame_rate = 30`
- `config.background_color = "#0b0f19"` (matching the Remotion card interior)

Implement these 4 Manim template classes:
1. **`ManimEquationMorphScene` (`sub_mode: "equation_morph"`)**:
   - Takes `steps: list[dict]` (`[{"latex": "...", "label": "..."}]`) and `duration: float`.
   - Renders clean `MathTex` equations (with a safe `Text` fallback if LaTeX compilation fails on unusual symbols), smoothly morphing step-by-step using `ReplacementTransform` / `TransformMatchingShapes`, highlighting key variables in cyan (`#00f2fe`), emerald (`#10b981`), and amber (`#f59e0b`), with a glowing bounding box around the final result.
2. **`ManimCalculusGraphScene` (`sub_mode: "calculus_graph"`)**:
   - Uses Manim `Axes` to plot smooth continuous curves (`f(x)`), animated secant-to-tangent derivative slopes (`ValueTracker`), and glowing Riemann sum rectangles (`get_riemann_rectangles`) smoothly converging into the exact integral area under the curve.
3. **`ManimLinearVectorScene` (`sub_mode: "vector_field"`)**:
   - Uses `NumberPlane` / `ComplexPlane` to animate 2D linear matrix transformations (`apply_matrix`), eigenvectors, or electromagnetic/fluid phase-space vector fields (`ArrowVectorField` / `StreamLines`).
4. **`ManimQuantumWaveScene` (`sub_mode: "quantum_wave"`)**:
   - Uses `Axes` + `ValueTracker(t)` with `always_redraw` to animate a real-time oscillating complex Gaussian wavepacket ($\text{Re}[\Psi]$, $\text{Im}[\Psi]$, and probability envelope $\vert{}\Psi(x,t)\vert{}^2$) colliding with and tunneling through a potential barrier $V(x)$.

### 2. Manim Execution & Fallback Logic (`engine/renderer/manim_bridge.py`)
- Create `render_manim_clips_for_timeline(timeline_data: dict, run_dir: Path, enable_manim: bool = True) -> dict`:
  - Check if `manim` is available (`shutil.which("manim")` or `import manim`). If Manim is not installed or `--no-manim` is passed, log `[MANIM:INFO] Manim unavailable or disabled; using native Remotion SVG renderers` and return `timeline_data` unchanged.
  - For scenes where `visual_type in ("math_equation", "function_graph", "quantum_sim")` (or `visual_type == "manim_scene"`), select at most **2 key scenes per video** to pre-render with Manim (so total pre-render overhead stays under ~10–15 seconds).
  - Render each selected scene into `run_dir / f"manim_scene_{scene_id}.mp4"` at `920x920 @ 30fps`.
  - Set `scene["manim_video_src"] = f"runs/{run_dir.name}/manim_scene_{scene_id}.mp4"` in `data.json`.
  - **Bulletproof Fallback**: Wrap every Manim subprocess call in a `try/except` with a `45s` timeout. If Manim or `latex` fails on any scene, log a warning and leave `manim_video_src` unset so Remotion automatically renders its native SVG component without failing the pipeline!

---

## 2. Remotion Integration (`video/src/components/ManimScene.jsx` & Scene Wrappers)

1. **Create `video/src/components/ManimScene.jsx`**:
   - Renders the standard top domain header badge, title, and subtitle.
   - Inside the center `920px x 920px` (`canvas_spotlight`) or `920px x 760px` (`full_dashboard`) container, if `scene.manim_video_src` is present, render:
     ```jsx
     <OffthreadVideo '100%', 'contain', 16 borderRadius: height: muted objectFit: src="{staticFile(scene.manim_video_src)}" style="{{" width: }}/>
     ```
   - Overlay subtle corner HUD telemetry badges (e.g., `MANIM OPENGL/CAIRO ENGINE • 30 FPS`, active equation/phase badge) so the Manim canvas blends seamlessly with the rest of the Remotion UI.
2. **Automatic Upgrade in `MathScene.jsx`, `GraphScene.jsx`, and `QuantumScene.jsx`**:
   - Inside `MathScene.jsx`, `GraphScene.jsx`, and `QuantumScene.jsx`, check `if (scene.manim_video_src)` — when present, render the `<OffthreadVideo src={staticFile(scene.manim_video_src)} />` inside the simulation canvas box while preserving the surrounding header and telemetry cards!

---

## 3. CLI Flags & Verification (`generate_and_render.py` & `engine/generate.py`)
1. Add `--no-manim` flag to `generate_and_render.py` and `engine/generate.py` (Manim enabled by default when installed).
2. Add unit tests in `tests/test_manim_bridge.py` and Node verifying:
   - Parameterized payload generation for all 4 Manim templates (`equation_morph`, `calculus_graph`, `vector_field`, `quantum_wave`).
   - Graceful fallback when Manim subprocess errors or is disabled (`--no-manim`).
   - `ManimScene.jsx` / `MathScene.jsx` / `GraphScene.jsx` rendering `<OffthreadVideo>` when `manim_video_src` is populated and falling back to SVG when absent.
3. Run all Python and Node unit tests and confirm 100% pass rate.