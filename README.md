# Automated Technical & Developer-Tool Video Generation Engine

An end-to-end programmatic video generation engine that transforms technical concepts, B2B developer tool documentation, SDK releases, and STEM topics into commercial-grade **16:9 Widescreen (1920x1080)** and **9:16 Vertical Shorts (1080x1920)** using an automated, decoupled multi-stage architecture.

---

## Key Capabilities

- **Evidence-Based Documentation Ingestion**: Ingests official documentation, extracts source-linked `EvidencePack` records, selects verifiable developer workflows, and compiles synchronized videos where every claim, code snippet, and animation event is backed by an `evidence_id`.
- **Zero Product Hardcoding**: Any product is strictly a data input passed via `projects/<slug>.json` or `--project`. Visual components and engine stages contain zero hardcoded strings, brand assumptions, or fake metrics.
- **Multi-Aspect Ratio Architecture (`16:9` & `9:16`)**: Native support for `--aspect-ratio 16:9` (1920x1080 widescreen cinema canvas for docs, YouTube, and product landing pages) and `--aspect-ratio 9:16` (1080x1920 vertical format for mobile feeds).
- **Client Brand Design System (`brand_config.json`)**: Dynamic Remotion theming via `BrandContext` supporting client hex palettes (`primary_color`, `secondary_color`, `bg_canvas`, `bg_surface`), typography (`font_sans`, `font_mono`), logo badges, and docs CTA links.
- **Broadcast-Grade Neural Audio**: Edge-TTS senior-engineer voices (`en-US-AndrewNeural`, `en-US-BrianNeural`) with automatic retries and local disk caching, mastered with FFmpeg broadcast filters (`highpass=80Hz`, `loudnorm=-16LUFS`, anti-click fades) at 48000Hz stereo.
- **Strict Spoken/Visual Separation**: Phonetic replacements (e.g. `step.run()` $\rightarrow$ `"step dot run"`) are applied strictly within the TTS synthesis function right before audio generation, ensuring visual titles, IDE code, and captions always render clean technical syntax.
- **Modern B2B Motion Primitives**: Linear/Vercel/Stripe-styled motion components (`HookScene`, `CodeSpotlightScene`, `WorkflowTraceScene`, `EvidenceBentoScene`, `TakeawayCTAScene`).
- **Local Production Studio & GitHub Webhooks**: Interactive 3-column UI (`studio_ui/index.html`) with Mode A/B surgical revisions, aspect ratio toggling, and `POST /api/webhooks/github` release automation.
- **Hybrid Manim Community Sub-Renderer**: Pre-renders high-precision mathematical and physics animations (`ManimEquationMorphScene`, `ManimCalculusGraphScene`, `ManimLinearVectorScene`, `ManimQuantumWaveScene`).

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
   [Stage 0: Ingestion]      --> engine/ingestion/evidence_extractor.py
                                 │ (Extracts source-backed atomic EvidencePack)
                                 ▼
   [Stage 1: Workflow]       --> engine/director/workflow_selector.py
                                 │ (Scores verifiable developer workflows 0-60)
                                 ▼
   [Stage 1.5: Scene Plan]   --> engine/director/scene_planner.py
                                 │ (Evidence-linked 5-beat scene plan)
                                 ▼
   [Stage 2: Validation]     --> engine/validation/evidence_validator.py
                                 │ (100% claim backing & citation verification gate)
                                 ▼
   [Stage 3: Audio & TTS]    --> engine/audio/ (Edge-TTS Neural + FFmpeg Broadcast Mastering)
                                 │ (48kHz Stereo, -16 LUFS, Whisper Timestamps)
                                 ▼
   [Stage 4: Timeline & Zod] --> video/scripts/validate_timeline.mjs
                                 │ (Zod schema validation of data.json)
                                 ▼
   [Stage 5: Remotion Comp]  --> Remotion / React 18 (<BrandProvider> + Multi-Aspect Canvas)
                                 │ (16:9 1920x1080 Widescreen OR 9:16 1080x1920 Vertical)
                                 ▼
   [Stage 6: Post-Validation]--> engine/validation/output.py (ffprobe Dimensions & Streams)
                                 │
                                 ▼
                   Final Broadcast-Ready Video (MP4, 30fps)
```

---

## Visual Primitives

| Visual Primitive | Component | Key Capabilities |
|---|---|---|
| `HookScene` | `HookScene.tsx` | Status pill from props (`PROBLEM • DISTRIBUTED RETRIES`), headline, multi-node flow diagram showing failure vs naive retry. |
| `CodeSpotlightScene` | `CodeSpotlightScene.tsx` | Sleek modern IDE (Cursor/Raycast dark glass), real token syntax coloring, animated highlight bar, floating callout badge. |
| `WorkflowTraceScene` | `WorkflowTraceScene.tsx` | OpenTelemetry/Inngest execution waterfall with live duration bars, state badges (`COMPLETED & MEMOIZED`), and memoization locks. |
| `EvidenceBentoScene` | `EvidenceBentoScene.tsx` | 2–4 data cards populated strictly from `scene.items` citing verified `evidence_ids`. Zero fake placeholder metrics. |
| `TakeawayCTAScene` | `TakeawayCTAScene.tsx` | Dedicated brand outro card with client logo, proposition takeaway, quickstart code bar, and official docs URL. |
| `terminal` | `TerminalScene.jsx` | Content-fitted CLI terminal chrome, typing command (`$ ...`), stdout reveal. |
| `code_reveal` / `code_transform` | `CodeRevealScene.jsx` | Syntax typewriter mounting, progressive line highlighting, and before/after diff morphing. |
| `diagram` / `flowchart` | `DiagramScene.jsx` | Client-to-edge API request/response cards, HTTP status codes (`200 OK`, `503`), payload inspection. |
| `comparison` | `ComparisonScene.jsx` | Dual-card split layout with clean domain-specific takeaway footers. |
| `manim_scene` | `ManimScene.jsx` | 3Blue1Brown-style animations: equation morphs, calculus curves, vector fields, and wavepackets. |

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
export EDGE_TTS_VOICE="en-US-AndrewNeural" # Senior engineer neural voice
```

### 3. Generate a Video Short

#### A. Generate from Project Profile (e.g. Inngest Widescreen)
```bash
.venv/bin/python generate_and_render.py \
  --project projects/inngest_step_run.json \
  --aspect-ratio 16:9 \
  --output video/out/inngest_step_run_16_9.mp4
```

#### B. Generate Vertical Short (`9:16`) with Fast Frame Check
```bash
.venv/bin/python generate_and_render.py \
  --project projects/inngest_step_run.json \
  --aspect-ratio 9:16 \
  --frames 0-29
```

#### C. Generate from Customer Documentation URL
```bash
.venv/bin/python generate_and_render.py \
  --topic "FastAPI Asynchronous Endpoints" \
  --subject code \
  --source-url "https://fastapi.tiangolo.com/tutorial/first-steps/" \
  --aspect-ratio 16:9 \
  --length 35
```

#### D. Generate STEM Shorts
```bash
# Electrical Power Grid Short (60 seconds)
.venv/bin/python generate_and_render.py --topic "Smart Grid Optimal Power Flow and Thevenin Equivalence" --subject electrical --length 60

# Quantum Physics Short (60 seconds)
.venv/bin/python generate_and_render.py --topic "Quantum Tunneling and Dirac Atomic Orbitals" --subject quantum_physics --length 60

# Chemistry Short (30 seconds)
.venv/bin/python generate_and_render.py --topic "SN1 vs SN2 Reaction Mechanisms" --subject chemistry --length 30

# Math Short with Manim Sub-Renderer (15 seconds fast test)
.venv/bin/python generate_and_render.py --topic "Euler Identity and Complex Exponential Morph" --subject math --length 15 --fast-test
```

---

## CLI Options

| Flag | Type | Description |
|---|---|---|
| `--project` | `str` | Path to `projects/<slug>.json` defining product, sources, brand, and profiles. |
| `--aspect-ratio` | `str` | Aspect ratio: `16:9` (1920x1080 Widescreen) or `9:16` (1080x1920 Vertical). |
| `--topic` | `str` | Topic for the video (if not using `--project`). |
| `--subject` | `str` | Target domain (`code`, `math`, `physics`, `quantum_physics`, `mechanics`, `electrical`, `chemistry`, `ml`, `systems`). |
| `--length` | `int` | Target duration in seconds: `15`, `30`, `35`, or `60` (default: `30` or from project). |
| `--source-file` | `str` | Local documentation or code file to extract facts from. |
| `--source-url` | `str` | Public documentation or GitHub README URL to ingest. |
| `--source-text` | `str` | Raw documentation text or code snippet to ingest. |
| `--mock` | `flag` | Use deterministic mock generator instead of live Gemini API. |
| `--frames` | `str` | Remotion frame range for fast benchmarks (e.g. `--frames 0-29`). |
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

## GitHub Webhook Automation

The Studio API backend (`studio_api.py`) exposes an automated endpoint for GitHub release webhooks:

```bash
# Ingest release webhook payload and automatically trigger video generation
curl -X POST http://localhost:8000/api/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: release" \
  -d '{
    "action": "published",
    "release": {
      "tag_name": "v2.4.0",
      "name": "Durable Step Execution",
      "body": "Introduced step.run() with memoized state and isolated retries."
    },
    "repository": {
      "name": "inngest-js",
      "html_url": "https://github.com/inngest/inngest-js"
    }
  }'
```

---

## Automated Test Suites

The repository contains automated tests across pipeline stages, ingestion, API, and frontend rendering.

### Running Python Tests with Pytest
```bash
# Run all tests:
.venv/bin/python -m pytest -v

# Run targeted test suites:
.venv/bin/python -m pytest tests/test_validation.py -v         # Schema & Evidence Gates
.venv/bin/python -m pytest tests/test_studio_api.py -v         # Studio API & Webhooks
.venv/bin/python -m pytest tests/test_source_loader.py -v      # Ingestion & Fact Extraction
.venv/bin/python -m pytest tests/test_milestone4.py -v         # Video Output ffprobe Validation
```

### Running Remotion Frame Smoke Tests
```bash
# Verify component frame renders in Chromium:
npx remotion render video/src/index.js CodingShort /tmp/test_frame.mp4 --frames=0-1 --props=video/public/runs/<run_id>/data.json
```
