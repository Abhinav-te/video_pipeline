# AGENTS.md — Documentation-Driven B2B Technical Video Engine (`~/video_gen`)

## 1. Core Architectural Philosophy
We are building a **Documentation-Driven Technical Video Production Engine**.
- **The Golden Rule:** Never ask the AI to invent a tutorial about a topic. The engine must ingest official documentation, extract a source-linked `EvidencePack`, select a verifiable developer workflow, and compile it into a synchronized Remotion + Manim video where every claim, code snippet, and animation event is backed by an `evidence_id`.
- **Zero Company Hardcoding:** Inngest (and any future product) is strictly a data input passed via `projects/<slug>.json`. NEVER write `if company == "Inngest"` or hardcode product-specific strings, fallbacks, or fake metrics in `engine/` or `video/src/`.
- **Three-Artifact Separation:** Every run strictly separates:
  1. `project_profile.json` (company, audience, goal, duration, official source URLs/files).
  2. `evidence_pack.json` & `scene_plan.json` (retrieved sources, atomic evidence records, scored workflow candidates, and evidence-linked scene graph).
  3. `render_profile.json` (typography, dark theme color tokens, `9:16` or `16:9` aspect ratio, caption layout).

## 2. Strict Execution & Directory Guardrails (MUST FOLLOW)
1. **Python Interpreter:** ALWAYS use `.venv/bin/python` (never bare `python3`).
2. **Forbidden Scan Directories:** NEVER glob, grep, index, or scan `video/public/runs/`, `video/out/`, `revisions/`, `node_modules/`, or `.venv/`.
3. **Fast Render Gate:** When testing Remotion components or timeline changes, ALWAYS test with `--frames=0-29` or `npx remotion still` first. Never run full multi-scene renders until schema and frame checks pass.
4. **Never Trust Exit Code 0 Alone:** Always verify `validate_timeline.mjs`, `evidence_validator.py`, `ffprobe` duration/timescale (`1/90000`), and extracted midpoint keyframes.

## 3. Universal Evidence & Scene Plan Contracts
### 3.1 Evidence Record Schema (`evidence_pack.json`)
Every extracted fact must follow this structure:
- `id`: Unique string (e.g., `"ev_step_run_01"`)
- `kind`: `"concept" | "developer_action" | "behavior" | "failure_behavior" | "limitation" | "code_evidence" | "metric"`
- `claim`: Concise factual statement directly supported by the source
- `source_url`: Exact URL or file path of the source document
- `source_section`: Heading or section title
- `excerpt`: Verbatim quote or code snippet from the source
- `retrieved_at`: ISO-8601 timestamp
- `content_hash`: SHA-256 of the normalized source section
- `confidence`: `"source_supported" | "inferred_needs_review"`

### 3.2 Universal Scene Vocabulary (`video/src/`)
The scene planner may ONLY emit supported generic visual primitives:
- `show_code` / `highlight_code` (`CodeReveal` / `CodeTransform`): Real documented code only; active lines highlighted, context lines readable (`opacity: 0.55`), content-fitted container height.
- `workflow_state_transition` (`WorkflowStateTransition` / `Diagram`): Generic state-machine node graph (`entities: string[]`, `events: {target, action: "start" | "succeed" | "fail" | "retry" | "reuse_cached", label}[]`).
- `show_terminal` (`Terminal`): Content-fitted CLI execution + stdout reveal.
- `show_request_response` (`ApiFlow`): Client -> Gateway/Endpoint -> Response payload inspection.
- `show_metric` / `takeaway_cta` (`BentoGrid` / `FullscreenText`): Only renders metrics that cite a valid `evidence_id` + official docs URL/CTA.

## 4. Validation & Studio Rules
1. **Evidence Citation Gate:** Every scene narration segment and every visual metric/claim must include `evidence_ids: string[]` referencing valid IDs in `evidence_pack.json`. Unbacked numerical claims are rejected before rendering.
2. **Nuance & Limitation Gate:** If `evidence_pack.json` contains a `limitation` record for the chosen workflow (e.g., external side effects requiring idempotency on retry), the script/visuals must not contradict it.
3. **Spoken Narration vs. Visual Syntax:** `narration[].text` must be natural spoken English (e.g., "Wrap the operation in step dot run")—never raw CLI/URL punctuation. Remove duplicate narration prose footers inside visual cards so they do not collide with Remotion captions.
4. **Studio Traceability:** `studio_api.py` and `studio_ui/index.html` must expose each scene's linked `evidence_ids`, source excerpts, and validation warnings alongside Mode A (Visual) and Mode B (Narration) surgical revision controls.

## 5. Premium B2B Design System, Multi-Aspect Ratio & Audio Rules
1. **ZERO Hardcoded Text in React JSX (`video/src/components/`):**
   - React components (`FullscreenText.tsx`, `BentoGrid.tsx`, `CodeReveal.tsx`, `WorkflowStateTransition.tsx`, `Terminal.tsx`) must NEVER contain fallback strings like `"Single-step package install"`, `"Declarative Async Pipeline"`, `"Sub-Millisecond Edge Scale"`, `"90% Less Boilerplate"`, `"1.4ms"`, `"Invariant state transitions"`, or hardcoded `"⚠️ ANTI-PATTERN"` badges.
   - 100% of titles, subtitles, badges, metrics, and cards MUST come from the `scene` props generated from `evidence_pack.json`.
2. **Never Leak TTS Phonetics Into Visual Titles:**
   - Visual titles and code must always render real technical syntax (`step.run()`, `@acme/sdk`, `POST /v1/charges`).
   - Phonetic normalizations (`"step dot run"`) apply ONLY to the string passed to TTS audio synthesis—NEVER mutate visual titles or captions!
3. **Neural-Only Audio Policy (Ban `espeak`):**
   - NEVER use `espeak`, `espeak-ng`, `pyttsx3`, or sine-wave audio fallbacks.
   - Always synthesize voiceovers using Neural TTS (`edge-tts` with `en-US-AndrewNeural` / `en-US-BrianNeural` or local `kokoro` ONNX/PyTorch) and apply FFmpeg broadcast loudness normalization (`af="loudnorm=I=-16:TP=-1.5:LRA=11"`).
4. **Multi-Aspect Ratio Architecture (`16:9` Widescreen & `9:16` Vertical):**
   - Support `--aspect-ratio 16:9` (`1920x1080`, default for B2B docs/YouTube/landing pages) and `--aspect-ratio 9:16` (`1080x1920`, for vertical social feeds).
   - In `16:9`, use full widescreen layouts (split-screen code + state trace, wide IDE viewport, horizontal span waterfall) with bottom cinema captions.
5. **Client Brand Configuration (`brand_config.json`) & GitHub Webhook Automation:**
   - Every project loads a `brand_config.json` (or `brand` block in `project_profile.json`) mapping client hex colors (`primary_color`, `secondary_color`, `bg_dark`, `surface_card`), typography (`font_sans`, `font_mono`), company name, and logo badge directly into Remotion via `BrandContext`.
   - `studio_api.py` exposes `POST /api/webhooks/github` to ingest GitHub `release` webhook payloads and trigger automated video generation.