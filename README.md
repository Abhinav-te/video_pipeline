# Automated Technical Video Generation Engine

An end-to-end programmatic video pipeline that transforms technical coding topics into 9:16 vertical shorts (TikTok/Reels/Shorts) using an automated multi-stage architecture.

---

## System Architecture

```text
generate_and_render.py (CLI / Orchestrator)
       │
       ▼
[Stage 1: AI Director]       --> engine/director/ (Gemini API)
       │ (JSON Scene Plan)
       ▼
[Stage 2: Validation Gate]   --> engine/validation/ (AST & Schema Gate)
       │ (Validated JSON)
       ▼
[Stage 3: Audio Generation]  --> engine/audio/ (Edge-TTS + Integrity Check)
       │ (Playable Audio + Word Timestamps)
       ▼
[Stage 4: Timeline Assembly] --> engine/timeline/ (Whisper Beats & Mapping)
       │ (Remotion-Ready Data: video/public/runs/<run_id>/)
       ▼
[Stage 5: Video Renderer]    --> Remotion / React (Subprocess Render)
       │ (Raw Video File: video/out/<run_id>.mp4)
       ▼
[Stage 6: Output Validation] --> engine/validation/output.py (ffprobe Verification)
       │
       ▼
Final MP4 Output (1080x1920, h264/aac, 30fps)
```

---

## Pipeline Stages

### 1. `[DIRECTOR]` — AI Director (`engine/director/`)
- Generates structured multi-scene JSON plans using Google Gemini models (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`).
- Enforces 5–11 words per spoken beat to ensure optimal mobile pacing.
- Selects from 6 visual primitives: `fullscreen_text`, `code_reveal`, `code_transform`, `diagram`, `terminal`, `comparison`.
- Enforces an initial curiosity hook in Scene 1 and at least one bug-vs-fix `comparison` scene.

### 2. `[VALIDATION]` — Pre-Flight Validation Gate (`engine/validation/`)
- Centralized validation before speech or video rendering triggers.
- **Python AST Syntax Checking**: Verifies all code snippets in `code_reveal`, `code_transform`, and `comparison` scenes via `ast.parse`.
- **Schema & Bounds Enforcement**: Verifies scene count (2–35), 5–11 words per beat, 1–3 diagram nodes, and schema version contracts.

### 3. `[AUDIO]` — Voice Synthesis (`engine/audio/`)
- Generates natural narration via Microsoft Edge-TTS with exponential backoff (up to 3 retries).
- Inspects audio integrity via `ffprobe` to verify valid headers, supported codecs (`mp3`, `aac`), and duration $> 0$s before downstream stages.
- Removes partial files on error to prevent corrupted assets from lingering.

### 4. `[TIMELINE]` — Whisper Alignment & Timeline Assembly (`engine/timeline/`)
- Dynamic hardware acceleration detection (`cuda` if available, falling back to `cpu`).
- In-process Whisper model caching to avoid reloading weights across repeated operations.
- Word timestamp sanitization: strictly non-negative, `end > start`, and monotonic progression.
- Timeline beat mapping protected against zero-duration stalls or collapsed scenes (`MIN_SCENE_DURATION = 0.3s`).

### 5. `[RENDER]` — Remotion React Compositing (`video/`)
- Renders 1080x1920 (9:16) vertical video shorts using React components and Remotion CLI.
- Reads dynamic run properties per run via `--props video/public/runs/<run_id>/data.json`.
- Dynamic rolling subtitle window with word-level highlight punch.

### 6. `[OUTPUT_VALIDATION]` — Post-Render Output Validation (`engine/validation/output.py`)
- Automated `ffprobe` inspection of final rendered video:
  - File exists and size $\ge$ 100KB.
  - Container is a valid MP4 (`mov,mp4,m4a,3gp,3g2,mj2`).
  - Exactly 1 video stream: codec `h264`, dimensions `1080x1920` (9:16 vertical), ~30 fps.
  - Exactly 1 audio stream: codec `aac` or `mp3`, sample rate $\ge 24,000$Hz.
  - Video duration matches audio narration duration within $\pm 1.5$s tolerance.
- Automatically quarantines corrupt or non-compliant videos (`<name>.corrupt.mp4`) and exits non-zero.

---

## Run Isolation & Artifacts

Every run generates a unique timestamped identifier:
```text
run_YYYYMMDD_HHMMSS_<shortid>
```

- Intermediate assets are isolated in dedicated directories:
  ```text
  video/public/runs/<run_id>/
  ├── audio.mp3   # Narrated voiceover
  └── data.json   # Validated scene plan and Whisper timings
  ```
- Rendered video outputs are stored at:
  ```text
  video/out/<run_id>.mp4
  ```
- **Fail-Fast & Zero Stale Artifacts**: If any stage fails mid-flight, partial files in `video/public/runs/<run_id>/` are immediately wiped so no half-baked assets contaminate future runs.

---

## Visual Primitives Supported

- `fullscreen_text`: High-impact curiosity hooks and concept resets.
- `code_reveal`: Progressive syntax-highlighted code block mounting with optional focus phrase highlight.
- `code_transform`: In-place modification of existing functions and logic.
- `terminal`: Interactive command runs and traceback demonstrations.
- `diagram`: Dynamic node graphs for algorithmic flow (1–3 nodes).
- `comparison`: Side-by-side / top-bottom bug-vs-fix comparisons (`problem_code` vs `solution_code`).

---

## Prerequisites

- **Python**: 3.10+ (tested on Python 3.11 / Linux)
- **Node.js**: v20+ LTS
- **FFmpeg / FFprobe**: System-level binaries installed
- **Gemini API Key**: From Google AI Studio

---

## Quickstart

### 1. Environment Setup

```bash
git clone https://github.com/Abhinav-te/video_pipeline.git
cd video_pipeline

python3 -m venv engine/.venv
source engine/.venv/bin/activate
pip install -r engine/requirements.txt

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
python3 generate_and_render.py --topic "Python Dictionary Keys Trick" --length 60
```

#### CLI Options:
| Flag | Type | Description |
|---|---|---|
| `--topic` | `str` | **Required**. Topic for the educational coding short. |
| `--length` | `int` | Target duration in seconds: `15`, `30`, or `60` (default: `60`). |
| `--no-cache` | `flag` | Force fresh AI Director generation (bypasses script cache). |
| `--run-id` | `str` | Explicit run ID (auto-generated if omitted). |
| `--output` | `str` | Custom path for the rendered MP4 output. |

---

## Running the Automated Test Suite

The test suite contains 51 unit and integration tests across all pipeline milestones:

```bash
# Run all tests with discovery:
engine/.venv/bin/python -m unittest discover -s tests -p "test_*.py" -v

# Or run individual milestone test suites:
engine/.venv/bin/python -m unittest tests/test_milestone1.py -v   # Run Isolation & Observability
engine/.venv/bin/python -m unittest tests/test_milestone2.py -v   # Validation Gate & AST Syntax
engine/.venv/bin/python -m unittest tests/test_milestone3.py -v   # Audio Guarantees & Whisper Alignment
engine/.venv/bin/python -m unittest tests/test_milestone4.py -v   # Post-Render Output Validation
engine/.venv/bin/python -m unittest tests/test_milestone5.py -v   # Integration & Reliability
```
