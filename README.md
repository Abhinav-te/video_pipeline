# Automated Technical & STEM Video Generation Engine

An end-to-end programmatic video generation engine that transforms technical topics across Computer Science and STEM domains into professional 9:16 vertical shorts (TikTok, YouTube Shorts, Instagram Reels) using an automated, decoupled multi-stage architecture.

---

## Supported Domains

The engine natively generates visual simulations, LaTeX derivations, kinetic badges, and domain-tuned color palettes for:

- **Computer Science & Algorithms** (`code`) — Syntax typewriter, AST validation, before/after morphing, terminal output.
- **Machine Learning & Systems** (`ml`, `systems`) — 3-tier algorithm exploration (K-Means, DBSCAN, PCA, t-SNE) and dual-pane neural network simulations.
- **Organic & Physical Chemistry** (`chemistry`) — Curved arrow electron pushing, $S_N2$ backside inversion, steric hindrance shields, and $S_N1$ planar carbocation ionization.
- **Quantum Physics** (`quantum_physics`) — Dirac relativistic atomic orbitals ($1s, 2p, 3d$), Schrödinger potential barrier tunneling, and Heisenberg position-momentum squeezing.
- **Advanced Mechanics & Statics** (`mechanics`) — Multi-support beam reaction forces, live $V(x)/M(x)$ shear-moment diagrams, inclined plane vector decomposition, and chassis dynamic load transfer.
- **Electrical Engineering & Smart Grids** (`electrical`) — KVL/KCL multi-loop mesh analysis, Thévenin/Norton linear reduction, and multi-bus optimal power flow (OPF) grids.
- **Applied Mathematics & Physics** (`math`, `physics`) — Multi-step LaTeX derivation studio and 2D coordinate calculus plots.

---

## System Architecture

```text
generate_and_render.py (CLI / Orchestrator)
       │
       ▼
[Stage 1: AI Director]       --> engine/director/ (Gemini API Fallback Chain)
       │ (JSON Scene Plan)
       ▼
[Stage 2: Validation Gate]   --> engine/validation/ (Polymorphic AST & Schema Gate)
       │ (Validated JSON)
       ▼
[Stage 3: Audio Generation]  --> engine/audio/ (Edge-TTS + Integrity Check)
       │ (Playable Audio + Word Timestamps)
       ▼
[Stage 4: Timeline Assembly] --> engine/timeline/ (Whisper Beats & Domain Choreographer)
       │
       ▼
[Stage 4.5: Manim Bridge]   --> engine/renderer/ (Manim Community 920x920 Sub-Renderer)
       │ (Pre-rendered MP4 clips: video/public/runs/<run_id>/manim_scene_<id>.mp4)
       ▼
[Stage 5: Video Renderer]    --> Remotion / React 18 (<OffthreadVideo> Compositing)
       │ (Raw Video File: video/out/<run_id>.mp4)
       ▼
[Stage 6: Output Validation] --> engine/validation/output.py (ffprobe Verification)
       │
       ▼
Final Production Video (1080x1920, H.264/AAC, 30fps)
```

---

## Pipeline Stages

### 1. `[DIRECTOR]` — AI Director (`engine/director/`)
- Generates structured multi-scene JSON plans using Google Gemini models with automatic fallback across the verified active v1beta model chain: `gemini-3.8-flash` -> `gemini-3.7-flash` -> `gemini-3.5-flash` -> `gemini-3.5-flash-lite` -> `gemini-3.1-flash-lite`.
- Automatically detects topic domain (`code`, `math`, `physics`, `chemistry`, `quantum_physics`, `mechanics`, `electrical`, `ml`, `systems`).
- Dynamically scales spoken narration and scene counts with duration:
  - **15s**: ~35 words across 3–4 scenes.
  - **30s / 35s**: ~70 words across 5–7 scenes.
  - **60s**: ~135 words across 10–11 scenes (~13–15 words per scene).
- Includes strict 30-second request timeouts, instant skipping of 404/invalid keys without retry sleeps, and fast backoff to eliminate indefinite API hangs.

### 2. `[VALIDATION]` — Polymorphic Validation Gate (`engine/validation/`)
- Pre-flight validation gate before audio synthesis or Remotion rendering runs.
- **Polymorphic Code & Formula Validation**:
  - Python AST syntax checking (`ast.parse`) is strictly restricted to `code` subjects and explicit Python scene types.
  - STEM formula strings (`problem_code`, `solution_code`, math derivations) are validated as formatted equation blocks rather than Python source.
- **Resilient Fallback Synthesis**: Missing optional graph curves, derivation steps, or simulation parameters are auto-synthesized during timeline choreography rather than halting pipeline execution.
- Validates pacing (minimum 4 words per beat), schema version contracts, and scene count bounds (2–35).

### 3. `[AUDIO]` — Voice Synthesis & GPU Whisper Alignment (`engine/audio/`)
- Generates natural, clear voiceover narration via Microsoft Edge-TTS with exponential backoff retry handling.
- Verifies audio container integrity via `ffprobe` (valid headers, codec `mp3`/`aac`, duration $> 0$s).
- Whisper forced word-level timestamp alignment with automatic CUDA GPU acceleration (`torch.cuda.is_available()`) and graceful CPU fallback.
- Sanitizes timestamps: strictly non-negative, monotonically increasing, and bounded by scene durations.

### 4. `[TIMELINE]` — Domain Choreographer & Beat Enhancer (`engine/timeline/`)
- Injects domain-specific color palettes (`electrical_neon`, `mechanics_amber`, `quantum_violet`, `chemistry_emerald`, `ml_amber`, `cyber_matrix`).
- **Anti-Repetition & Pacing Engine**:
  - Rotates simulation sub-modes across middle scenes so no two consecutive beats render identical visual layouts.
  - Enforces the **Single Bento Guarantee**: `bento_grid` overview matrices appear at most once per video, strictly at the final scene for multi-beat shorts.
  - Enforces clean 1-sentence comparison takeaways (`KEY TAKEAWAY: ...`) without duplicate pipe suffixes.
- Assembles run-isolated `data.json` for Remotion compositing.

### 4.5. `[MANIM]` — Hybrid Manim Community Sub-Renderer (`engine/renderer/`)
- Pre-renders high-precision 3Blue1Brown-style mathematical animations as deterministic 920x920 @ 30fps MP4 clips (`video/public/runs/<run_id>/manim_scene_<id>.mp4`).
- **4 Parameterized Scene Templates**:
  - `ManimEquationMorphScene` (`equation_morph`): Step-by-step LaTeX formula morphing (`MathTex`/`TransformMatchingShapes`) with color-highlighted variables and glowing bounding boxes.
  - `ManimCalculusGraphScene` (`calculus_graph`): Dynamic Cartesian axes plotting continuous functions, secant-to-tangent slope convergence, and shaded Riemann integral approximations.
  - `ManimLinearVectorScene` (`vector_field`): Matrix linear transformations (`apply_matrix`), eigenvector transformations, and electromagnetic/fluid vector fields (`ArrowVectorField`).
  - `ManimQuantumWaveScene` (`quantum_wave`): Time-dependent complex Gaussian wavepacket ($\text{Re}[\Psi]$, $\text{Im}[\Psi]$, $\vert\Psi\vert^2$) colliding with and tunneling through a finite potential barrier $V(x)$.
- **Strict Performance & Bulletproof Fallback**:
  - Pre-renders at most 2 key scenes per video (~8–10s pre-render overhead).
  - Isolated subprocess execution with a 45-second timeout and LaTeX error fallback (`safe_math_tex`).
  - Graceful fallback: If Manim is disabled or errors, the pipeline falls back seamlessly to native Remotion SVG components with zero pipeline crashes.

### 5. `[RENDER]` — Remotion React Compositing (`video/`)
- Master 1080x1920 (9:16) vertical compositor controlling headers, progress tabs, word-synced subtitles, and layout framing.
- Seamlessly integrates pre-rendered Manim clips via `<OffthreadVideo>` inside `ManimScene.jsx`, `MathScene.jsx`, `GraphScene.jsx`, and `QuantumScene.jsx`.
- **Optimized Rendering Engine**:
  - Clean Remotion configuration (`video/remotion.config.ts`) with high-speed JPEG sequence rendering and overwrite protection.
  - Zero heavy CSS `backdrop-filter: blur(...)` or per-frame SVG filter bottlenecks to ensure rapid rendering on headless Linux / WSL2 environments.
  - Dynamic `CameraRig` for smooth, non-jittering framing, kinetic callouts, dynamic badges, and word-level rolling captions.

### 6. `[OUTPUT_VALIDATION]` — Post-Render Verification (`engine/validation/output.py`)
- Automated `ffprobe` stream and container verification:
  - File exists and size $\ge 100$ KB.
  - Valid MP4 container (`mov,mp4,m4a,3gp,3g2,mj2`).
  - Exactly 1 video stream: codec `h264`, dimensions `1080x1920` (9:16 vertical), ~30 fps.
  - Exactly 1 audio stream: codec `aac` or `mp3`, sample rate $\ge 24,000$ Hz.
  - Video duration matches audio narration duration within $\pm 1.5$s tolerance.
- Automatically quarantines corrupt or non-compliant videos (`<name>.corrupt.mp4`) and exits non-zero.

---

## Visual Primitives

| Visual Primitive | Domain / Mode | Key Capabilities |
|---|---|---|
| `fullscreen_text` / `concept` | All Domains | Impactful hook cards, hero concept resets, takeaway highlights. |
| `code_reveal` | `code`, `systems` | Typewriter syntax mounting, line highlights, focus phrase tracking. |
| `code_transform` | `code` | In-place code mutation with before/after diff markers. |
| `terminal` | `code`, `systems` | Command line execution and formatted traceback output. |
| `diagram` / `flowchart` | All Domains | Animated node-link flows and state-machine transitions. |
| `comparison` | All Domains | Dual-card split with clean, domain-specific `KEY TAKEAWAY` footers. |
| `function_graph` | `math`, `physics`, STEM | 2D coordinate calculus, shear-moment diagrams, quantum wavepackets, reaction energy profiles. |
| `math_equation` | `math`, STEM | Multi-step LaTeX derivation studio with domain-specific formulas. |
| `physics_sim` | `physics` | 2D Newtonian projectile kinematics, vector decomposition, and force balance. |
| `bento_grid` | All Domains | 4-card overview matrices with 4 distinct animated mini-SVG diagrams. |
| `algorithm_explorer` | `ml`, `code` | 3-tier deep dive (K-Means, DBSCAN, PCA, t-SNE) with parameter HUDs. |
| `neural_code_split` | `ml`, `code` | Side-by-side live neural network simulation and PyTorch tensor code. |
| `chemistry_reaction` | `chemistry` | $S_N2$ backside attack, steric shields, $S_N1$ carbocation ionization, and racemic products. |
| `quantum_sim` | `quantum_physics` | Dirac atomic orbitals ($1s, 2p, 3d$), Schrödinger tunneling, Heisenberg phase space. |
| `mechanics_fbd` | `mechanics` | Beam reaction forces, inclined plane decomposition, chassis load transfer. |
| `electrical_grid` | `electrical` | KVL/KCL mesh loops, Thévenin equivalent reduction, multi-bus OPF dispatch. |
| `manim_scene` | `math`, `physics`, STEM | 3Blue1Brown-style animations: equation morphs, calculus curves, vector fields, and wavepackets. |

---

## Run Isolation & Artifacts

Each pipeline run generates a unique timestamped identifier:
```text
run_YYYYMMDD_HHMMSS_<shortid>
```

- Intermediate assets are isolated in dedicated directories:
  ```text
  video/public/runs/<run_id>/
  ├── audio.mp3               # Narrated voiceover
  ├── data.json               # Validated scene plan and Whisper timings
  ├── manim_scene_1.mp4       # Pre-rendered Manim 920x920 animation (optional)
  └── manim_scene_2.mp4       # Pre-rendered Manim 920x920 animation (optional)
  ```
- Rendered video outputs are stored at:
  ```text
  video/out/<run_id>.mp4
  ```
- **Zero Stale Artifacts**: If any stage fails mid-flight, temporary files in `video/public/runs/<run_id>/` are immediately wiped so no half-baked assets contaminate future runs.

---

## Prerequisites

- **Python**: 3.10+ (tested on Python 3.11 / Linux & WSL2)
- **Node.js**: v20+ LTS
- **FFmpeg / FFprobe**: System-level binaries installed
- **Manim Community & LaTeX** (optional): `manim`, `latex`, and `dvisvgm` for mathematical animation sub-rendering
- **Gemini API Key**: From [Google AI Studio](https://aistudio.google.com/)

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
export WHISPER_DEVICE="cuda"   # or "cpu" (auto-detected by default)
export EDGE_TTS_VOICE="en-US-ChristopherNeural"
```

### 3. Generate a Video Short

Run the full end-to-end pipeline with a single CLI command:

```bash
# Electrical Power Grid Short (60 seconds)
python3 generate_and_render.py --topic "Smart Grid Optimal Power Flow and Thevenin Equivalence" --subject electrical --length 60

# Quantum Physics Short (60 seconds)
python3 generate_and_render.py --topic "Quantum Tunneling and Dirac Atomic Orbitals" --subject quantum_physics --length 60

# Chemistry Short (30 seconds)
python3 generate_and_render.py --topic "SN1 vs SN2 Reaction Mechanisms" --subject chemistry --length 30

# Python Coding Short (60 seconds)
python3 generate_and_render.py --topic "Python Dictionary Keys Trick" --subject code --length 60

# Math Short with Manim Sub-Renderer (15 seconds test)
python3 generate_and_render.py --topic "Euler Identity and Complex Exponential Morph" --subject math --length 15 --fast-test
```

#### CLI Options:
| Flag | Type | Description |
|---|---|---|
| `--topic` | `str` | **Required**. Topic for the educational short. |
| `--subject` | `str` | Target domain (`code`, `math`, `physics`, `quantum_physics`, `mechanics`, `electrical`, `chemistry`, `ml`, `systems`). Auto-detected if omitted. |
| `--length` | `int` | Target duration in seconds: `15`, `30`, or `60` (default: `60`). |
| `--frames` | `str` | Optional Remotion frame range for fast benchmarks (e.g. `--frames 0-89`). |
| `--fast-test` | `flag` | Fast 3-second render mode for quick visual checks. |
| `--no-manim` | `flag` | Disable Stage 4.5 Manim Community pre-rendering (forces native Remotion SVGs). |
| `--no-cache` | `flag` | Force fresh AI Director generation (bypasses script cache). |
| `--run-id` | `str` | Explicit run ID (auto-generated if omitted). |
| `--output` | `str` | Custom path for the rendered MP4 output. |

---

## Automated Test Suites

The codebase includes comprehensive unit and integration tests across all pipeline stages and frontend components:

### Python Engine & Pipeline Tests
```bash
# Run all Python tests:
engine/.venv/bin/python -m unittest discover -s tests -p "test_*.py" -v

# Run targeted milestone & phase suites:
engine/.venv/bin/python -m unittest tests/test_manim_bridge.py -v               # Phase 14: Manim Community Sub-Renderer Bridge
engine/.venv/bin/python -m unittest tests/test_phase13_production_lock.py -v   # Phase 13: Production Lock
engine/.venv/bin/python -m unittest tests/test_phase12_duration_and_bento.py -v # Phase 12: Duration Scaling & Bento
engine/.venv/bin/python -m unittest tests/test_phase10_stem_and_gpu.py -v      # Phase 10: STEM Engines & GPU
engine/.venv/bin/python -m unittest tests/test_validation.py -v                # Polymorphic AST & Formula Gate
engine/.venv/bin/python -m unittest tests/test_stem_pipeline.py -v             # Full Multi-Subject Pipeline
```

### Node Remotion Component Tests
```bash
# Run frontend JSX & render tests:
node video/test_phase14_manim.mjs
node video/test_phase13_production_lock.mjs
node video/test_phase12_duration_and_fallbacks.mjs
node video/test_phase10_stem_and_gpu.mjs
node video/test_phase9_breathing.mjs
node video/test_phase7_chemistry.mjs
```
