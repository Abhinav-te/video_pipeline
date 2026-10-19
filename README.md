# Automated Technical & Developer-Tool Video Generation Engine

An end-to-end programmatic video generation engine that transforms technical concepts, B2B developer tool releases, and STEM topics into broadcast-quality 9:16 vertical shorts (TikTok, YouTube Shorts, Instagram Reels, LinkedIn Video) using an automated, decoupled multi-stage architecture.

---

## Key Capabilities

- **Code-First Developer Tool Visuals**: Native Remotion visual primitives for developer documentation, SDK releases, and API architectures (`terminal`, `code_reveal`, `code_transform`, `diagram`, `comparison`).
- **Ground-Truth Customer Ingestion**: Ingests real customer codebases, documentation files, and live web/GitHub documentation URLs, extracting CLI commands, code snippets, and API endpoints directly into scenes.
- **Local Production Studio Control Room**: Fast web-based 3-column UI (`studio_ui/index.html`) and FastAPI backend (`studio_api.py`) for scene-by-scene storyboard inspection, surgical visual/audio revisions (Mode A & Mode B), and instant revision rollbacks.
- **Dependency-Tracked Scene Regeneration**: Non-destructive revisions with isolated per-scene audio and frame-targeted Remotion rendering, recomposed in seconds via normalized FFmpeg segment stitching.
- **Zero-Crash React Reliability**: Protected with `<SceneErrorBoundary>`, strict named and default component export contracts, and runtime element type verification.
- **Hybrid Manim Community Sub-Renderer**: Pre-renders high-precision 3Blue1Brown-style mathematical and physics animations (`ManimEquationMorphScene`, `ManimCalculusGraphScene`, `ManimLinearVectorScene`, `ManimQuantumWaveScene`).
- **Comprehensive STEM & Algorithmic Domain Support**: Computer Science, Developer Tools, Machine Learning, Organic Chemistry, Quantum Physics, Advanced Mechanics, Electrical Engineering, and Applied Mathematics.

---

## Supported Domains

The engine natively generates visual simulations, LaTeX derivations, kinetic badges, and domain-tuned color palettes for:

- **B2B Developer Tools & Systems** (`code`, `systems`) — Animated terminal sessions (`$ ...`), syntax typewriter reveals with progressive line highlighting, before/after code diff morphing, and API request/response flowchart diagrams.
- **Computer Science & Algorithms** (`code`) — AST validation, algorithm complexity badges ($O(1)$, $O(n \log n)$), memory layout cards, and data structure operations.
- **Machine Learning & Systems** (`ml`, `systems`) — 3-tier algorithm exploration (K-Means, DBSCAN, PCA, t-SNE) and dual-pane neural network simulations.
- **Organic & Physical Chemistry** (`chemistry`) — Curved arrow electron pushing, $S_N2$ backside inversion, steric hindrance shields, and $S_N1$ planar carbocation ionization.
- **Quantum Physics** (`quantum_physics`) — Dirac relativistic atomic orbitals ($1s, 2p, 3d$), Schrödinger potential barrier tunneling, and Heisenberg position-momentum squeezing.
- **Advanced Mechanics & Statics** (`mechanics`) — Multi-support beam reaction forces, live $V(x)/M(x)$ shear-moment diagrams, inclined plane vector decomposition, and chassis dynamic load transfer.
- **Electrical Engineering & Smart Grids** (`electrical`) — KVL/KCL multi-loop mesh analysis, Thévenin/Norton linear reduction, and multi-bus optimal power flow (OPF) grids.
- **Applied Mathematics & Physics** (`math`, `physics`) — Multi-step LaTeX derivation studio, 2D coordinate calculus plots, and vector field transformations.

---

## System Architecture

```text
               generate_and_render.py / studio_api.py
                                 │
                                 ▼
   [Stage 0: Ingestion]      --> engine/ingestion/source_loader.py
                                 │ (Extracts customer CLI, code, endpoints)
                                 ▼
   [Stage 1: AI Director]    --> engine/director/ (Gemini API / Mock Library)
                                 │ (Structured JSON Scene Plan)
                                 ▼
   [Stage 2: Validation]     --> engine/validation/ (Polymorphic AST & Line Wrap Gate)
                                 │ (Bounds-checked JSON Plan)
                                 ▼
   [Stage 3: Audio & TTS]    --> engine/audio/ (Edge-TTS + GPU/CPU Whisper Alignment)
                                 │ (Playable Audio + Word-Level Timestamps)
                                 ▼
   [Stage 4: Timeline]       --> engine/timeline/ (Choreographer & Pacing Engine)
                                 │ (Run-isolated data.json)
                                 ▼
   [Stage 4.5: Manim Bridge] --> engine/renderer/ (Manim Community 920x920 Sub-Renderer)
                                 │ (Optional pre-rendered MP4 clips)
                                 ▼
   [Stage 5: Remotion Comp]  --> Remotion / React 18 (<SceneErrorBoundary> Compositor)
                                 │ (1080x1920 9:16 Vertical Video)
                                 ▼
   [Stage 6: Post-Validation]--> engine/validation/output.py (ffprobe Verification)
                                 │
                                 ▼
                   Final Production Video (MP4, 30fps)
```

---

## Visual Primitives

| Visual Primitive | Subject / Mode | Key Capabilities |
|---|---|---|
| `terminal` | `code`, `systems` | Terminal window chrome, typing CLI command (`$ ...`, `npm ...`, `pip ...`), animated status pill, progressive stdout reveal. |
| `code_reveal` | `code`, `systems` | Syntax typewriter mounting, progressive line highlighting, focus phrase badge, auto-wrapped lines ($\le 46$ chars). |
| `code_transform` | `code` | Side-by-side Before/After diff cards with `⚠️ Before` and `✨ After` badges and token mutation effects. |
| `diagram` / `flowchart` | All Domains | Client-to-edge API request/response cards, status codes (`200 OK`, `204`), JSON payloads, latency metrics. |
| `comparison` | All Domains | Dual-card split layout with clean domain-specific `KEY TAKEAWAY` footers. |
| `fullscreen_text` / `concept` | All Domains | High-impact hook cards, hero concept resets, kinetic title typography. |
| `function_graph` | `math`, `physics`, STEM | 2D coordinate calculus, shear-moment diagrams, quantum wavepackets, reaction energy profiles. |
| `math_equation` | `math`, STEM | Multi-step LaTeX derivation studio with domain-specific mathematical equations. |
| `physics_sim` | `physics` | 2D Newtonian projectile kinematics, vector decomposition, and force balance. |
| `bento_grid` | All Domains | 4-card overview matrices with distinct animated mini-diagrams (guaranteed at most once per video). |
| `algorithm_explorer` | `ml`, `code` | 3-tier deep dive (K-Means, DBSCAN, PCA, t-SNE) with parameter HUDs. |
| `neural_code_split` | `ml`, `code` | Side-by-side live neural network layer simulation and PyTorch tensor code. |
| `chemistry_reaction` | `chemistry` | $S_N2$ backside attack, steric shields, $S_N1$ carbocation ionization, and racemic products. |
| `quantum_sim` | `quantum_physics` | Dirac atomic orbitals ($1s, 2p, 3d$), Schrödinger tunneling, Heisenberg phase space. |
| `mechanics_fbd` | `mechanics` | Multi-support beam reaction forces, inclined plane decomposition, chassis load transfer. |
| `electrical_grid` | `electrical` | KVL/KCL mesh loops, Thévenin equivalent reduction, multi-bus OPF dispatch. |
| `manim_scene` | `math`, `physics`, STEM | 3Blue1Brown-style animations: equation morphs, calculus curves, vector fields, and wavepackets. |

---

## Customer Content & Internet Documentation Ingestion

The engine supports feeding real customer developer tools, changelogs, SDK documentation, and release notes directly into video generation:

1. **Input Channels**:
   - `--source-file <path>`: Local `.md`, `.txt`, `.py`, `.ts`, `.js`, `.json`, or `.html` file.
   - `--source-url <url>`: Public documentation URL or GitHub README/release page. Strips noise tags (`<nav>`, `<script>`, `<style>`) and parses clean Markdown headings and code blocks.
   - `--source-text "<string>"`: Raw text/markdown strings (used in the Studio UI).
2. **Ground-Truth Fact Extraction (`extract_source_facts`)**:
   - Automatically parses `product_name`, `cli_commands` (`npm`, `npx`, `pip`, `uv`, `docker`, `curl`, `$` commands), fenced `code_snippets` (auto-formatted and line-wrapped to $\le 46$ chars, $\le 12$ lines), `api_endpoints`, and `key_points`.
3. **End-to-End Propagation**:
   - Extracted facts are injected into both Gemini Director prompts and `--mock` mode generation so real customer identifiers, commands, and code appear accurately on screen.

---

## Local Production Studio Control Room

The Local Production Studio provides an interactive web workspace for inspecting projects and performing surgical revisions without full pipeline re-runs:

```bash
# Start the studio backend (runs on http://localhost:8000)
python3 studio_api.py
```

Open `http://localhost:8000/` (or open `studio_ui/index.html` directly) in any modern browser.

### Key Features:
- **Project Explorer & Generator**:
  - Create new video projects with subject selection, duration, prompt, and optional customer Source URL or pasted Source Material.
- **Storyboard Inspector**:
  - Per-scene timeline cards with visual type, audio durations, narration scripts, and diagnostic customer fact badges.
- **Per-Scene Segment Video Previews**:
  - Watch isolated rendered MP4 clips per scene or listen to scene voiceover audio.
- **Surgical Revision Modes**:
  - **Mode A (Visual Revision)**: Change visual type or parameters for a single scene and re-render only that scene's frame range (~3-5s). Audio and other scenes are untouched.
  - **Mode B (Narration Revision)**: Edit spoken script for a single scene. Only that scene's audio and word timestamps are regenerated, downstream scene start times shift cleanly by $\Delta t$, and the visual segment is re-rendered to match.
- **One-Click Rollback**:
  - Revert to any previous revision snapshot (`rev_001`, `rev_002`, ...) instantly.
- **Export Verified MP4**:
  - Stitches all current scene segment MP4s using FFmpeg with normalized timescales (`libx264 -preset veryfast -crf 18 -r 30 -g 30 -video_track_timescale 90000`), completely eliminating splice freeze frames.

---

## Prerequisites

- **Python**: 3.10+ (tested on Python 3.11 / Linux & WSL2)
- **Node.js**: v20+ LTS
- **FFmpeg & FFprobe**: System-level binaries installed
- **Gemini API Key**: From [Google AI Studio](https://aistudio.google.com/) (optional if using `--mock`)
- **Manim Community & LaTeX** (optional): `manim`, `latex`, and `dvisvgm` for mathematical animation sub-rendering

---

## Quickstart

### 1. Environment Setup

```bash
git clone https://github.com/Abhinav-te/video_pipeline.git
cd video_pipeline

python3 -m venv engine/.venv
source engine/.venv/bin/activate
pip install -r requirements.txt

cd video
npm install
cd ..
```

### 2. Configure Environment Variables

```bash
export GEMINI_API_KEY="your_gemini_api_key"

# Optional overrides:
export WHISPER_DEVICE="cuda"   # or "cpu" (auto-detected)
export EDGE_TTS_VOICE="en-US-ChristopherNeural"
```

### 3. Generate a Video Short

#### A. Generate from Customer Documentation (DevTool Release)
```bash
python3 generate_and_render.py \
  --topic "Acme EdgeCache SDK v2 Release" \
  --subject code \
  --source-file examples/sample_devtool_release.md \
  --length 35 \
  --mock \
  --output video/out/devtool_sdk_v2_demo.mp4
```

#### B. Generate from Remote Documentation URL
```bash
python3 generate_and_render.py \
  --topic "FastAPI Asynchronous Endpoints" \
  --subject code \
  --source-url "https://fastapi.tiangolo.com/tutorial/first-steps/" \
  --length 35
```

#### C. Generate STEM Shorts
```bash
# Electrical Power Grid Short (60 seconds)
python3 generate_and_render.py --topic "Smart Grid Optimal Power Flow and Thevenin Equivalence" --subject electrical --length 60

# Quantum Physics Short (60 seconds)
python3 generate_and_render.py --topic "Quantum Tunneling and Dirac Atomic Orbitals" --subject quantum_physics --length 60

# Chemistry Short (30 seconds)
python3 generate_and_render.py --topic "SN1 vs SN2 Reaction Mechanisms" --subject chemistry --length 30

# Math Short with Manim Sub-Renderer (15 seconds fast test)
python3 generate_and_render.py --topic "Euler Identity and Complex Exponential Morph" --subject math --length 15 --fast-test
```

---

## CLI Options

| Flag | Type | Description |
|---|---|---|
| `--topic` | `str` | **Required**. Topic for the short. |
| `--subject` | `str` | Target domain (`code`, `math`, `physics`, `quantum_physics`, `mechanics`, `electrical`, `chemistry`, `ml`, `systems`). |
| `--length` | `int` | Target duration in seconds: `15`, `30`, `35`, or `60` (default: `60`). |
| `--source-file` | `str` | Local documentation or code file to extract facts from. |
| `--source-url` | `str` | Public documentation or GitHub README URL to ingest. |
| `--source-text` | `str` | Raw documentation text or code snippet to ingest. |
| `--mock` | `flag` | Use deterministic mock generator instead of live Gemini API. |
| `--frames` | `str` | Remotion frame range for fast benchmarks (e.g. `--frames 0-89`). |
| `--fast-test` | `flag` | Fast 3-second render mode for quick visual checks. |
| `--no-manim` | `flag` | Disable Stage 4.5 Manim Community pre-rendering. |
| `--no-cache` | `flag` | Force fresh AI Director generation (bypasses script cache). |
| `--run-id` | `str` | Explicit run ID (auto-generated if omitted). |
| `--output` | `str` | Custom path for the rendered MP4 output. |
| `--revise-scene` | `str` | Scene ID to revise in an existing run. |
| `--revise-visual` | `flag` | Perform Mode A visual-only revision on `--revise-scene`. |
| `--revise-narration` | `flag` | Perform Mode B narration revision on `--revise-scene`. |
| `--set-visual-type` | `str` | New visual type for visual revision. |
| `--set-narration` | `str` | New narration text for narration revision. |

---

## Automated Test Suites

The repository contains 230+ automated tests across pipeline stages, ingestion, API, and frontend rendering.

### Running Python Tests with Pytest
```bash
# Run all tests:
PYTHONPATH=. engine/.venv/bin/pytest -v

# Run targeted test suites:
PYTHONPATH=. engine/.venv/bin/pytest tests/test_source_loader.py -v       # Ingestion & Fact Extraction
PYTHONPATH=. engine/.venv/bin/pytest tests/test_phase_a_devtools.py -v    # DevTool Visual Primitives
PYTHONPATH=. engine/.venv/bin/pytest tests/test_studio_api.py -v         # Studio API & Revisions
PYTHONPATH=. engine/.venv/bin/pytest tests/test_checkpoint_01_02.py -v   # Segments & Mode A/B
PYTHONPATH=. engine/.venv/bin/pytest tests/test_validation.py -v          # AST & Code Length Gates
PYTHONPATH=. engine/.venv/bin/pytest tests/test_manim_bridge.py -v        # Manim Sub-Renderer
```

### Running Remotion Frame Smoke Tests
```bash
# Verify component frame renders in Chromium:
npx remotion render video/src/index.js CodingShort /tmp/test_frame.mp4 --frames=0-1 --props=video/public/runs/<run_id>/data.json
```
