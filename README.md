# AGENTS.md — Lean Documentation & Release-Driven DevTool Video Engine (`~/video_gen`)

## 1. Core Mission & Scope
We build accurate, deterministic product explainers and release-note videos for B2B Developer-Tool companies.
- **Single Pipeline Rule:** There is ONLY ONE pipeline: `Source/Release Ingestion -> EvidencePack -> Data-Driven ScenePlanner -> EvidenceValidator -> TimelineMapper -> Remotion Render`. Do NOT use free-form topic invention (`script.py`), STEM/Manim branches, or `choreographer.py`.
- **Core Visual Primitives Only (`video/src/components/`):**
  Keep ONLY: `HookScene`, `CodeSpotlightScene`, `CodeRevealScene`, `CodeTransformScene`, `TerminalScene`, `WorkflowStateTransition` (merged with progress-bar visuals; delete `WorkflowTraceScene.tsx`), `DiagramScene`, `EvidenceBentoScene`, `TakeawayCTAScene`, `SceneRenderer`, `CameraRig`, `KineticCallout`, `SceneBadge`.
- **Execution Guardrails:**
  - Always use `.venv/bin/python` (never bare `python3`).
  - NEVER scan, glob, or grep `video/public/runs/`, `video/out/`, `revisions/`, `node_modules/`, or `.venv/`.
  - Use `--frames=0-29` for intermediate Remotion checks before full renders.

## 2. Code, Audio, Timeline & Component Contracts
1. **Code Display Invariant:**
   - Run `sanitize_code()` on every ingestion path to strip markdown fences (````ts`, ````typescript`, ````) and normalize indentation.
   - Never truncate code at 12 lines (`[:12]`). Displayed code must be a complete, syntactically balanced, contiguous slice of the source excerpt in `evidence_pack.json`.
   - Derive `highlight_lines` dynamically from the focus token in the code (e.g., `step.run(`), never hardcoded line arrays.
   - Dynamically scale code font size (`>= 26px` target at 1080p) so the longest line never clips horizontally.
2. **Deterministic PCM WAV Audio & `edge-tts` Word Timing Invariant:**
   - Pin `edge-tts` in `requirements.txt` and capture native `WordBoundary` events (`assert len(word_events) > 0`).
   - Maintain a **Spoken-to-Display Token Map** when applying phonetic substitutions (e.g., `"step.run()"` -> spoken `"step dot run"`), merging the spoken word timestamps back onto the original display token (`"step.run()"`) for captions and `at_word` triggers.
   - **NEVER use `silenceremove=stop_periods=-1`** (which deletes mid-sentence pauses). Instead, leave leading audio untouched and trim trailing silence deterministically using `end = last_word_end + 0.15` via FFmpeg `atrim=end={end},asetpts=PTS-STARTPTS,apad=pad_dur=0.25`.
   - Save per-scene audio as uncompressed **PCM WAV** (`pcm_s16le`, `48000Hz`) to avoid MP3 LAME padding drift. Concatenate the scene WAVs, run `loudnorm=I=-16:TP=-1.5:LRA=11` **ONCE** on the joined master audio, and compute scene `start_time`/`duration` and word offsets as exact cumulative sums of the measured scene WAV lengths (NO `max(2.5, duration)` clamping).
   - Assert `abs(sum(scene_durations) - master_audio_duration) <= 0.05`.
   - Pre-chunk `caption_chunks` in Python: split at sentence boundaries (`.`, `!`, `?`, `;`, `,`), 3–6 words (`<= 28 chars`) per chunk, and NEVER join words across a period or scene boundary.
3. **`WorkflowStateTransition` Contract:**
   - Route `workflow_state_transition` in `CodingShort.jsx` and `SceneRenderer.tsx` strictly to `WorkflowStateTransition.tsx` (delete `WorkflowTraceScene.tsx`).
   - Delete all fallback `step_1`/`step_2` entities, `"FAILED: 503"`, `"RETRY #1"`, `"OpenTelemetry / Durable Execution Waterfall"`, and `"trace_id: 8f4e29b1 • span: process-order • duration: 420ms"`.
   - Render strictly from props: header from `scene.title`, `entities[{id, label, sub_label?}]`, and `events[{target, action, label, at_word?, elapsed?, evidence_id}]`. Only display an `elapsed` duration if `event.elapsed` and `event.evidence_id` are present. Drive event transitions from `at_word` timestamps, NEVER `idx / numEvents`.
4. **1080p Visual Scale & Word-Timed Motion:**
   - Main visual stage fills ~80% of the `1920x1080` frame (`maxWidth: 1560px`).
   - Minimum font sizes at 1080p: `captions >= 40px`, `body >= 28px`, `code >= 26px`, `card_subtitle >= 24px`, `tags >= 18px`.

## 3. The 4-Gate Validator Moat (`engine/validation/evidence_validator.py`)
Every build must pass all 4 gates before rendering:
1. **Contiguous Code Equality:** Displayed code is an exact contiguous substring of sanitized source `code_evidence` with balanced braces and zero markdown fences.
2. **Quote / Paraphrase Check:** Every on-screen title, subtitle, and metric has `>= 0.35` normalized content-word overlap with its cited `EvidenceRecord` claim/excerpt.
3. **Limitation Gate:** If `evidence_pack.json` has a `limitation` record, a scene/card must display it accurately (never overclaiming `"GUARDED"`).
4. **Component Literal Lint:** Zero hardcoded domain strings, fake trace IDs/durations (`8f4e29b1`, `420ms`), fallback `step_1`/`step_2` events, or fake trust defaults (`"Verified via official documentation"`) inside `video/src/components/`.