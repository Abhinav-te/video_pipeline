# Video Pipeline Engine — Phase 1 Stabilization Audit (Milestone 0)

**Date**: 2026-10-10  
**Status**: Milestone 0 Complete — Awaiting Approval  
**Scope**: Codebase audit and gap analysis against Phase 1 stabilization requirements defined in `AGENTS.md`.  
**Modules Inspected**:
- Orchestrator: `generate_and_render.py`
- Monolithic Pipeline Runner: `engine/generate.py`
- Stage 1 (AI Director): `engine/director/script.py`
- Stage 2 (Validation Gate): `engine/validation/code.py`, `engine/generate.py`
- Stage 3 (Audio Generation): `engine/audio/tts_whisper.py`
- Stage 4 (Timeline Assembly): `engine/timeline/beats.py`
- Stage 5 (Video Renderer): `video/src/Root.jsx`, `video/src/CodingShort.jsx`, `video/remotion.config.js`
- Stage 6 (Output Validation): Currently absent in codebase

---

## 1. Executive Summary

The repository provides an end-to-end automated video generation system translating technical topics into 1080x1920 (9:16) educational shorts. The existing implementation functions as a prototype but exhibits several structural vulnerabilities that violate the Prime Directives outlined in `AGENTS.md`:

1. **Shared Artifact Contamination**: Generation currently relies on fixed filenames (`data_current.json`, `audio_current.mp3`). If a run fails mid-flight, stale files or partial outputs risk being picked up by Remotion or subsequent renders.
2. **Missing Stage 6**: There is zero post-render validation. `generate_and_render.py` prints success as soon as Remotion exits without verifying that the MP4 file exists, has a non-zero size, contains valid H.264 video and AAC/MP3 audio streams, or matches audio duration.
3. **Inconsistent Stage Boundaries & Error Propagation**: `engine/generate.py` acts as a monolithic script rather than cleanly decoupled stages. Subprocess errors in `generate_and_render.py` are caught generically with `sys.exit(1)` without structured stage identifiers (`[STAGE:ERROR]`).
4. **Validation Logic Fragmentation**: Script structure validation, word counts, and scene schema rules are hardcoded in `engine/generate.py` rather than encapsulated cleanly in `engine/validation/`.
5. **Hardware & Resource Inefficiencies**: Whisper is instantiated with `device="cpu"` on every run despite CUDA availability, and models are reloaded without caching.

---

## 2. Architecture Comparison: Current vs. Target

```text
TARGET ARCHITECTURE (AGENTS.md):
generate_and_render.py (CLI / Orchestrator)
       │
       ▼
[Stage 1: AI Director]  --> engine/director/ (JSON Scene Plan)
       │
       ▼
[Stage 2: Validation Gate] --> engine/validation/ (AST, schema, bounds)
       │
       ▼
[Stage 3: Audio Generation] --> engine/audio/ (Edge-TTS + Whisper alignment)
       │
       ▼
[Stage 4: Timeline Assembly] --> engine/timeline/ (Frame beats & mapping)
       │
       ▼
[Stage 5: Video Renderer] --> Remotion / React (Subprocess render)
       │
       ▼
[Stage 6: Output Validation] --> ffprobe / checks (Format, duration, audio streams)
       │
       ▼
Final MP4 Output
```

### Current Workflow Architecture:
```text
generate_and_render.py
  ├── 1. Compute global counter index from public/final_video_*.mp4
  ├── 2. Subprocess call: engine/.venv/bin/python engine/generate.py
  │       ├── Cleans data_current.json & audio_current.mp3
  │       ├── Stage 1: AI Director (Gemini API)
  │       ├── Stage 2: Inline Script Validation (AST + rules in generate.py)
  │       ├── Stage 3: Edge-TTS synthesis -> audio_current.mp3
  │       ├── Stage 4: Whisper transcription + timeline alignment
  │       ├── Writes data_current.json atomically (.tmp -> replace)
  │       └── Archives copies: audio_N.mp3, data_N.json
  ├── 3. Clears Remotion node_modules/.cache
  ├── 4. Subprocess call: npx remotion render CodingShort public/final_video_N.mp4
  └── 5. Exits (No Stage 6 validation!)
```

---

## 3. Stage-by-Stage Detailed Audit

### Stage 0: Orchestrator (`generate_and_render.py`)

* **Purpose**: CLI entry point coordinating script generation and Remotion video rendering.
* **Input Data / Artifacts**:
  - CLI flags: `--topic` (string, required), `--length` (15, 30, 60; default 60), `--no-cache` (bool flag).
  - Environment: `GEMINI_API_KEY`, Node.js environment, Python virtualenv at `engine/.venv/bin/python`.
* **Output Data / Artifacts**:
  - `video/public/final_video_{index}.mp4`
* **Current Failure Behavior & Exit Handling**:
  - Invokes `engine/generate.py` via `subprocess.run(check=True)`. On `CalledProcessError`, prints `❌ FATAL: AI Generation failed.` and exits with code 1.
  - Checks if `data_current.json` exists. If missing, prints `❌ FATAL: Phase 1 did not create data_current.json` and exits with code 1.
  - Invokes Remotion via `subprocess.run(check=True)`. On `CalledProcessError`, prints `❌ FATAL: Remotion render failed.` and exits with code 1.
* **Gaps & Vulnerabilities**:
  1. **Hardcoded User Paths**: Uses `os.path.expanduser("~/video_gen/engine")` and `os.path.expanduser("~/video_gen/video")` instead of repository-relative paths (`Path(__file__).resolve().parent`).
  2. **Index Race Condition & Stale Artifacts**: Uses sequential numbering `final_video_{next_idx}.mp4` based on counting existing files in `video/public/`. If files are deleted or runs occur concurrently, index collisions occur.
  3. **No Isolated Run ID**: Both the engine script and Remotion pass `data_current.json`.
  4. **No Stage 6**: After Remotion rendering completes, there is no validation step to ensure the video is valid and complete.
  5. **No Stage Log Standardization**: Does not output `[STAGE_NAME:START]`, `[STAGE_NAME:SUCCESS]`, `[STAGE_NAME:ERROR]`.

---

### Stage 1: AI Director (`engine/director/script.py`)

* **Purpose**: Generates high-retention structured JSON scene plans from topic and target duration.
* **Input Data / Artifacts**:
  - Function arguments: `topic` (str), `duration` (int: 15, 30, or 60).
  - Environment variables: `GEMINI_API_KEY` (comma-separated key list supported), `GEMINI_MODEL` (fallback list supported).
* **Output Data / Artifacts**:
  - Python `dict` representing raw scene plan:
    ```json
    {
      "title": "Topic",
      "schema_version": "2.1",
      "scenes": [
        {
          "scene_type": "fullscreen_text",
          "spoken_text": "...",
          "display_text": "...",
          "emphasis_word": "..."
        }
      ]
    }
    ```
  - Disk Cache: `engine/.cache/scripts/{hash}.json` (derived from topic, duration, model, schema version).
* **Current Failure Behavior & Exit Handling**:
  - Implements multi-model fallback (`DEFAULT_MODEL_CHAIN`) and multi-key fallback.
  - Retries transient 503/UNAVAILABLE errors with exponential backoff (1s, 2s, 4s, 8s).
  - Advances to next model on 429/RESOURCE_EXHAUSTED immediately.
  - If all keys and models fail, raises `RuntimeError("All key(s) x model(s) exhausted or failed...")`.
* **Gaps & Vulnerabilities**:
  1. **Non-existent Default Models in Fallback Chain**: Default chain includes `"gemini-3.6-flash"` and `"gemini-3.5-flash"` which are invalid/unreleased model names. These fail with client errors, adding unnecessary latency until hitting valid models like `gemini-2.5-flash`.
  2. **Regex Parsing Fragility**: `_call_model` strips fences and uses `re.search(r"(\{.*\})", raw_text, flags=re.DOTALL)`. Greedy regex can match leading or trailing braces if non-JSON output precedes or follows.
  3. **Loose Schema Contract**: Output dictionary is not validated by a Pydantic model or JSON Schema within `engine/director/`.

---

### Stage 2: Validation Gate (`engine/validation/code.py` + `engine/generate.py`)

* **Purpose**: Verifies Python syntax of generated code snippets, checks terminal outputs, and enforces scene constraints before triggering expensive audio generation or video rendering.
* **Input Data / Artifacts**:
  - Script plan `dict` from Director.
* **Output Data / Artifacts**:
  - Validated script object or explicit rejection.
* **Current Failure Behavior & Exit Handling**:
  - Syntax check (`check_syntax` in `engine/validation/code.py`) uses `ast.parse` on normalized code.
  - Terminal check (`check_terminal_snippet`) checks non-empty and length <= 2000 chars.
  - Scene checks in `engine/generate.py:validate_script`:
    - Checks `scene_type` in `VALID_SCENE_TYPES` (`fullscreen_text`, `code_reveal`, `code_transform`, `terminal`, `diagram`, `comparison`).
    - Enforces `spoken_text` non-empty and `<= 11` words.
    - Enforces code snippet existence and runs `check_syntax` for `code_reveal`, `code_transform`, and `comparison` (`problem_code` and `solution_code`).
    - Enforces diagram `nodes` list length `<= 3`.
    - Enforces Scene 1 is `fullscreen_text`.
    - Enforces at least one `comparison` scene.
  - On violation: calls `fatal(msg, exit_code=1)`, halting execution immediately.
* **Gaps & Vulnerabilities**:
  1. **Architectural Leak**: `validate_script` currently lives in `engine/generate.py` instead of `engine/validation/`. `engine/validation/code.py` only contains snippet syntax validation.
  2. **Missing Formal Schema Model**: Schema rules (word limits, scene fields, diagram rules) are evaluated via imperative if-conditions rather than a declarative schema or centralized validator.
  3. **No AST Sandbox Verification during Pipeline**: `run_in_sandbox` is implemented in `code.py` but never called by the pipeline.

---

### Stage 3: Audio Generation (`engine/audio/tts_whisper.py`)

* **Purpose**: Generates voiceover narration using Microsoft Edge-TTS and extracts precise word-level timestamps using Whisper.
* **Input Data / Artifacts**:
  - Input: Concatenated narration string `narration = build_spoken_text(script)`.
  - Output Audio Path: `video/public/audio_current.mp3`.
* **Output Data / Artifacts**:
  - Audio file: `video/public/audio_current.mp3` (MPEG-1 Audio Layer 3, 44.1kHz or 24kHz).
  - Word Timestamps List:
    ```python
    [
      {"word": "This", "start": 0.0, "end": 0.24},
      {"word": "Python", "start": 0.24, "end": 0.62},
      ...
    ]
    ```
* **Current Failure Behavior & Exit Handling**:
  - `generate_audio` in `generate.py`: Checks if `audio_current.mp3` exists and has non-zero size (`stat().st_size == 0`). If failed, calls `fatal()`.
  - `extract_word_timings`: Checks if Whisper returned words. If empty, calls `fatal()`.
* **Gaps & Vulnerabilities**:
  1. **Fixed Audio Destination**: Writes directly to shared `audio_current.mp3`.
  2. **Lack of Playability & Audio Stream Validation**: Only checks `file.exists()` and `st_size > 0`. Does not verify that the generated audio file is a valid, playable MP3 stream without truncated frames or corrupted headers.
  3. **No Whisper Caching / Hardcoded CPU**: `whisper.load_model("base", device="cpu")` reloads the base model into CPU memory on every execution, despite the host environment having CUDA (`torch.cuda.is_available() == True`).
  4. **No Network Retry for Edge-TTS**: Network hiccups on Edge-TTS WebSocket cause immediate pipeline failure.

---

### Stage 4: Timeline Assembly (`engine/timeline/beats.py`)

* **Purpose**: Maps scene boundaries and emphasis trigger words to Whisper word timestamps, producing Remotion-ready data.
* **Input Data / Artifacts**:
  - `scenes`: List of scene dictionaries from Stage 1 & 2.
  - `words`: List of word timestamp dictionaries from Stage 3.
* **Output Data / Artifacts**:
  - `timed_scenes`: List of timed scene objects containing `start_time` and `emphasis_time`.
  - Combined data payload written to `video/public/data_current.json`:
    ```json
    {
      "title": "...",
      "schema_version": "2.1",
      "engine_version": "2.0",
      "scenes": [...],
      "words": [...],
      "audio_file": "audio_current.mp3"
    }
    ```
* **Current Failure Behavior & Exit Handling**:
  - Validates `start_time >= 0` and strictly non-decreasing chronological order (`start_time >= previous_start`).
  - Calls `fatal()` on negative or out-of-order timestamps.
  - Atomic write of `data_current.json` using `.tmp` and `os.replace`.
* **Gaps & Vulnerabilities**:
  1. **Single-Word Heuristic Alignment**: `seg_first_word = spoken_text.split()[0]`. If two consecutive scenes start with the same common word (e.g. "The", "If", "This"), or if Whisper misheard or punctuated the first word, alignment can stall or advance inaccurately.
  2. **Timestamp Collisions / Stalls**: When unmatched, `scene_start_time` falls back to `last_start_time`, resulting in zero-duration scenes where multiple scenes share the exact same start timestamp.
  3. **Fixed File Overwrites**: Writes to `data_current.json`, contaminating shared state.
  4. **Unchecked Audio/Timeline Bounds**: Does not verify that `lastWordTime` is within reasonable tolerance of the target duration.

---

### Stage 5: Video Renderer (`video/src/Root.jsx`, `video/src/CodingShort.jsx`, Remotion)

* **Purpose**: High-density 1080x1920 (9:16) Remotion/React compositing engine rendering the final MP4.
* **Input Data / Artifacts**:
  - Props file: `video/public/data_current.json` passed via `--props` CLI parameter.
  - Audio assets: `data.audio_file` (located in `video/public/`), `video/public/pop.mp3`.
  - Config: `video/remotion.config.js` (`Config.setRspack(true)`, `Config.setVideoImageFormat("jpeg")`).
* **Output Data / Artifacts**:
  - Rendered video: `video/public/final_video_{index}.mp4`.
* **Current Failure Behavior & Exit Handling**:
  - Executed via `npx remotion render CodingShort <out_file> --codec h264 --props <data_file_path>`.
  - Subprocess exit code checked via `check=True`. If non-zero, `generate_and_render.py` prints generic error and exits with code 1.
* **Gaps & Vulnerabilities**:
  1. **Static Fallback Data Coupling**: `Root.jsx` imports `import fallbackData from '../public/data_current.json';`. If `--props` fails to parse or pass cleanly, Remotion falls back to stale `data_current.json` on disk.
  2. **Public Directory Pollution**: All intermediate audio and video files (`audio_1.mp3`, `data_1.json`, `final_video_1.mp4`, etc.) are written directly into `video/public/`.
  3. **No Dynamic Composition Parameter Passing**: `CodingShort` relies on reading audio from `staticFile(data.audio_file)`.

---

### Stage 6: Output Validation (MISSING IN CODEBASE)

* **Purpose**: Post-render verification using `ffprobe` to validate format, stream integrity, duration, and audio synchronization.
* **Input Data / Artifacts**:
  - Rendered MP4 file path.
  - Target run metadata (expected duration, audio duration, run ID).
* **Output Data / Artifacts**:
  - Validation report or boolean confirmation.
* **Current Failure Behavior & Exit Handling**:
  - **NONEXISTENT**. `generate_and_render.py` currently assumes that if Remotion returns exit code 0, the output video is valid and complete.
* **Required Checks (Target Architecture)**:
  1. File existence and non-zero byte size (`size > 100KB`).
  2. Container format: ISO Media / MP4 (`mov,mp4,m4a,3gp,3g2,mj2`).
  3. Video stream: Exactly 1 video stream, codec `h264`, resolution `1080x1920` (9:16 aspect ratio), valid frame rate (`30 fps`).
  4. Audio stream: Exactly 1 audio stream, codec `aac` or `mp3`, sample rate >= 24000Hz.
  5. Duration matching: Video duration must match audio narration duration within acceptable tolerance (e.g., ±1.5 seconds / 45 frames).
  6. Explicit failure exit: Must exit non-zero with `[OUTPUT_VALIDATION:ERROR]` identifying the failure reason.

---

## 4. Cross-Cutting Analysis against Prime Directives

| Prime Directive | Current Codebase Status | Gap / Risk | Proposed Remediation in Phase 1 |
| :--- | :--- | :--- | :--- |
| **1. Incremental Execution Only** | Compliant (Milestone 0 Audit underway) | N/A | Strictly complete Milestones 1 through 5 sequentially with user approval gates. |
| **2. Do Not Rewrite** | Compliant | Existing modules in `engine/` are functional; refactor in place rather than replacing. | Strengthen modules (`director`, `validation`, `audio`, `timeline`, `render_orchestrator`) by adding clear interfaces without discarding functioning logic. |
| **3. Fail-Fast & Explicit** | **NON-COMPLIANT** | Generic `fatal()` calls; subprocess errors caught with generic `sys.exit(1)`; no structured log tokens. | Standardize logging with `[STAGE_NAME:START]`, `[STAGE_NAME:SUCCESS]`, `[STAGE_NAME:ERROR]`. Propagate exit codes cleanly. |
| **4. No Stale Artifacts** | **NON-COMPLIANT** | Global files `data_current.json` and `audio_current.mp3` shared across runs; index determined by counting existing files. | Implement isolated run identifiers (`run_{timestamp}_{uuid}`) and separate runtime directories per run (`runs/<run_id>/`). |
| **5. Strict Scope Exclusions** | Compliant | No image generation, external B-roll, or 3D renderers present. | Maintain strict focus on 2D programmatic primitives and audio pipeline stabilization. |

---

## 5. Milestone Implementation Roadmap

Following the requirements of `AGENTS.md`, the stabilization roadmap is structured into 5 sequential milestones:

```text
Milestone 0: Pipeline Audit (COMPLETED)
       │
       ▼
Milestone 1: Observability & Run Isolation
       ├── Run ID generation (e.g. run_YYYYMMDD_HHMMSS_<shortid>)
       ├── Isolated artifact directories per run (artifacts/<run_id>/)
       ├── Standardized stage log tokens: [STAGE:START], [STAGE:SUCCESS], [STAGE:ERROR]
       └── Subprocess exit code propagation
       │
       ▼
Milestone 2: Artifact Contracts & Validation Gate
       ├── Director schema formalization (Pydantic / strict dataclass contract)
       ├── Centralized validation gate in engine/validation/ (scene rules, word counts, bounds)
       └── Pre-flight Python AST syntax & terminal checks prior to audio trigger
       │
       ▼
Milestone 3: Subprocess Safety & Audio Guarantees
       ├── Audio verification (ffprobe/soundfile verification of MP3 playability & non-empty stream)
       ├── Whisper alignment hardening (gap detection, fallback sanity, GPU/CUDA acceleration if present)
       └── Clean temp artifact cleanup on failure
       │
       ▼
Milestone 4: Remotion Output Validation
       ├── Post-render inspection module using ffprobe
       ├── Verification of 1080x1920 resolution, H.264 video stream, audio stream presence
       └── Duration alignment check (video duration vs. audio duration tolerance)
       │
       ▼
Milestone 5: Automated Testing
       ├── Unit tests for engine/validation/ (valid/invalid AST, schema bounds, edge cases)
       ├── Unit tests for engine/timeline/ (beat alignment, timestamp monotonicity, gap handling)
       └── Integration test verifying exit codes and failure propagation
```

---

## 6. Phase 1 Acceptance Criteria Checklist

- [ ] Single CLI command runs entire flow reliably (`python3 generate_and_render.py --topic "..." --length 60`).
- [ ] Director output is validated before audio/render triggers.
- [ ] Word timestamps and audio are verified for the specific run ID.
- [ ] Any stage failure halts the pipeline with a descriptive error code and failing stage name.
- [ ] No stale cached files can contaminate fresh runs.
- [ ] Output validator confirms final MP4 integrity (video + audio streams, resolution, duration).
- [ ] Unit tests pass for validation and timeline components.

---

## 7. Next Action

Milestone 0 is complete. In accordance with the instruction:
> **"Stop and await user approval before writing application code."**

No application code has been modified. Awaiting user approval to proceed to **Milestone 1: Observability & Run Isolation**.

