# Agent Instructions: Video Pipeline Engine — Phase 1 Stabilization

You are an expert systems and audio/video pipeline software engineer.
Your objective is to execute **Phase 1: Reliable Video Generation Engine** on this existing repository without breaking Remotion rendering or rewriting established modules.

---

## 1. Prime Directives & Constraints

1. **Incremental Execution Only**: Work on ONLY ONE milestone at a time. Never jump ahead.
2. **Do Not Rewrite**: Refactor and strengthen existing modules (`engine/director`, `engine/audio`, `engine/timeline`, `engine/validation`, `generate_and_render.py`). Do not discard functioning code.
3. **Fail-Fast & Explicit**: No stage may swallow errors or continue on failures. Every failure must identify:
   - Failing stage name
   - Specific reason/exception
   - Exit code (non-zero)
4. **No Stale Artifacts**: Every run MUST use isolated run IDs or cleaned target paths. A failed run must never leave half-baked JSON or audio that gets picked up by a subsequent render.
5. **Strict Scope Exclusions**: Do NOT implement image generation (DALL-E/Midjourney), external B-roll, complex 3D renderers, or automatic YouTube uploads.

---

## 2. Core Target Architecture

```text
generate_and_render.py (CLI / Orchestrator)
       │
       ▼
[Stage 1: AI Director]  --> engine/director/
       │ (JSON Scene Plan)
       ▼
[Stage 2: Validation Gate] --> engine/validation/ (AST, schema, bounds)
       │ (Validated JSON)
       ▼
[Stage 3: Audio Generation] --> engine/audio/ (Edge-TTS + Whisper alignment)
       │ (Playable Audio + Word Timestamps)
       ▼
[Stage 4: Timeline Assembly] --> engine/timeline/ (Frame beats & mapping)
       │ (Remotion-Ready Data)
       ▼
[Stage 5: Video Renderer] --> Remotion / React (Subprocess render)
       │ (Raw Video File)
       ▼
[Stage 6: Output Validation] --> ffprobe / checks (Format, duration, audio streams)
       │
       ▼
Final MP4 Output


3. Implementation Milestones
Milestone 0: Pipeline Audit (Read-Only)
Inspect generate_and_render.py, engine/generate.py, engine/director/, engine/audio/, engine/timeline/, and video/src/.

Produce PHASE1_AUDIT.md detailing for each stage:

Input data/artifacts

Output data/artifacts

Failure behavior and exit handling

Stop and await user approval before writing application code.

Milestone 1: Observability & Run Isolation
Introduce clean run identifiers (e.g., timestamped or UUID run IDs).

Standardize log format across stages: [STAGE_NAME:START], [STAGE_NAME:SUCCESS], [STAGE_NAME:ERROR].

Propagate exit codes cleanly from all subprocesses (Edge-TTS, Whisper, Remotion).

Milestone 2: Artifact Contracts & Validation Gate
Formalize Director output contract (JSON schema, beat length constraints 5–11 words, supported visual primitives).

Ensure Pre-flight AST validation rejects invalid code snippets before hitting the audio or render stages.

Milestone 3: Subprocess Safety & Audio Guarantees
Verify audio files are playable and non-empty.

Verify Whisper timestamps map correctly to beats without timestamp gaps.

Milestone 4: Remotion Output Validation
Post-render check using ffprobe or file inspection: verify video exists, resolution is 1080x1920, audio stream exists, duration matches audio within tolerance.

Milestone 5: Automated Testing
Add unit tests for AST validation (engine/validation/) and timeline beat mapping (engine/timeline/).

4. Phase 1 Acceptance Criteria
Before declaring Phase 1 complete, verify all items:

[ ] Single CLI command runs entire flow reliably.

[ ] Director output is validated before audio/render triggers.

[ ] Word timestamps and audio are verified for the specific run ID.

[ ] Any stage failure halts the pipeline with a descriptive error code.

[ ] No stale cached files can contaminate fresh runs.

[ ] Output validator confirms final MP4 integrity (video + audio streams).

[ ] Unit tests pass for validation and timeline components.