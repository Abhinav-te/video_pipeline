# AGENTS.md — Evidence-Driven B2B Developer-Tool Video Engine

## 1. Product North Star

Build a reliable video production engine for B2B developer-tool companies. It turns official documentation, code examples, API references, and release notes into polished, source-traceable technical videos.

The product is not a free-form topic-to-video generator. It must not invent tutorials first and attach evidence afterward. Source evidence determines what the video may claim, show, and animate.

### Initial customer and video intents

Prioritize these intents, in this order:
1. Documentation-grounded developer workflow explainers.
2. Release notes and before/after change explainers.
3. API/SDK walkthroughs.
4. Failure, retry, and recovery explainers.
5. Migration and upgrade guides.
6. Product-feature explainers.

The architecture should support these intents through configuration and evidence-driven workflow selection, not new product-specific Python or React branches. An intent may only be generated when available evidence supports it. Never force every intent into the same storyboard.

### Product promises

- **Grounded:** every material factual claim is traceable to source evidence.
- **Technically faithful:** displayed code and technical behavior match the selected sources and versions.
- **Polished:** content is readable, paced, synchronized, and visually appropriate to the concept.
- **Repairable:** users can edit a scene and rebuild only artifacts invalidated by that edit.
- **Inspectable:** each run records inputs, artifact hashes, validation results, and unresolved issues.

## 2. One Authoritative Pipeline

All video generation must use one shared pipeline:

`ProjectProfile -> Source/Release Ingestion -> EvidencePack -> WorkflowSelector -> ScenePlanner -> Pre-render Validation -> Narration/TTS -> Word-Timing & Token Mapping -> TimelineMapper -> Remotion Render -> Post-render QA -> Run Report/Studio`

The implementation may split these responsibilities across existing modules, but there must not be parallel, competing orchestration paths for the same product purpose.

- Use Remotion as the video renderer.
- Do not reintroduce Manim/STEM rendering branches, free-form topic invention, or a legacy choreographer merely because old files exist.
- Do not delete a legacy module until its callers, responsibilities, tests, and replacement are understood and the migration is shown to preserve required behavior.
- Keep the workflow selector separate in responsibility from scene compilation. The selector chooses a supported explanatory approach; the planner converts that choice and evidence into scenes.
- Pre-render gates must run before rendering. Final artifact QA is a post-render gate; do not claim all gates run before rendering.

## 3. Execution Safety and Repository Discipline

1. Work only in the repository root confirmed at the start of the task. Do not assume a path such as `~/video_gen` without checking it.
2. Before changes, report the current branch, HEAD commit, and working-tree status. Preserve all pre-existing uncommitted work.
3. Never overwrite or force-move a Git tag. Use a unique safety tag only after checking the working tree and confirming an appropriate committed baseline. A tag does not back up uncommitted changes.
4. Do not commit, push, reset, clean, or discard user changes unless explicitly authorized.
5. Do not scan, glob, grep, index, or recursively enumerate generated/dependency directories such as `video/public/runs/`, `video/out/`, `revisions/`, `node_modules/`, or `.venv/`. Inspect a specifically named artifact only when required; do not perform broad scans there.
6. Use the project virtual environment interpreter, normally `.venv/bin/python`, after verifying that it exists. If it does not exist, report the environment issue rather than silently switching interpreters or installing dependencies.
7. Before a full Remotion render, run the available schema/timeline checks, TypeScript checks, and a short render/frame check such as `--frames=0-29` or the repository's equivalent. Confirm the exact supported command from the project scripts before using it.
8. Do not install packages, change dependency versions, or add services unless required by an approved task. Explain the need first.
9. Never state that a test or render passed unless it was actually executed. Distinguish passed, failed, skipped, and not run.
10. Do not replace a failing test with a weaker test just to obtain a green run. Preserve meaningful assertions and add regression tests for fixed defects.

## 4. Run Artifacts and Responsibility Boundaries

Each run should have explicit, versioned artifacts. Reuse existing names if the repository already has equivalent schemas; do not create duplicate formats without a migration reason.

### `project_profile.json`

Defines the input and intent, including:
- Project/run identity.
- `product_subject`: product, API, SDK, or capability being explained.
- `product_company`: vendor/publisher of the product being explained, where applicable.
- `client_brand` or `publisher_brand`: organization commissioning or publishing the video.
- Audience, goal, target duration, desired video intent, allowed source URLs/files, optional release metadata, and aspect ratio (`16:9` or `9:16`).

These identity fields have distinct meanings and must not be forced to equal one another. Validate them against an explicit project profile and allowed branding configuration.

### `evidence_pack.json`

Evidence records should contain, as appropriate:
- `id` (unique within the pack)
- `kind` from the documented enum
- `claim` (a concise factual statement)
- `source_url` or source file path
- `source_section`
- `excerpt` (verbatim quote or source code)
- `retrieved_at` (ISO-8601 timestamp where retrieval applies)
- `content_hash` (hash of the normalized source section or artifact)
- `confidence`/review status
- Optional source version or commit/release identifier

Use a single schema enum across ingestion, planning, validation, fixtures, and tests. The initial kinds may include `concept`, `developer_action`, `behavior`, `failure_behavior`, `limitation`, `code_evidence`, `metric`, and `release_change`. Do not use an undeclared kind such as `problem`; map it to an existing kind or deliberately update and test the schema everywhere.

Every fact must remain connected to the evidence that supports it. Evidence excerpts must not be fabricated by copying generated scene text back into the evidence corpus.

### `scene_plan.json`

Each scene should have a stable `scene_id`, purpose, supported visual primitive, props, narration segments, applicable evidence IDs, optional code references, and word/time triggers where needed.

- Every material narration claim and on-screen factual label, metric, code block, or behavior must link to valid evidence IDs.
- A scene may omit a claim when evidence is insufficient; it must not fill a gap with invented details.
- Scene order and structure are selected for the requested video intent rather than hardcoded product names or topic keywords.

### `render_profile.json`

Contains presentation-only settings: brand tokens, fonts, aspect ratio, output resolution, safe areas, caption style, and documented source/CTA display rules. Do not use presentation settings as hidden factual inputs.

### `run_manifest.json` and `dependency_graph.json`

Track input and artifact hashes, versions, selected workflow, per-gate status, source lineage, generated assets, timings, render output, and unresolved warnings. Represent dependencies such as:

`source -> evidence record -> claim/scene -> narration -> word timings -> timeline -> render`

Dependency edges must reflect real data dependencies. On edits, invalidate only affected downstream artifacts, but always rerun required validation gates over changed artifacts and their dependents. Never reuse an artifact solely because a filename is unchanged; compare content/configuration hashes.

## 5. Evidence, Claims, and Technical Correctness

1. Prefer primary, official documentation and version-matched source material. Record source URLs, sections, retrieval metadata, and source/version identifiers where available.
2. Every material claim must cite applicable evidence. Unbacked numbers, fabricated metrics, invented product capabilities, and fake verification badges must be rejected.
3. Text-overlap scores may be used as heuristics, not proof of truth. A high overlap score does not establish semantic support and can miss contradictions. Combine deterministic checks with contradiction/limitation checks and human review for uncertain claims.
4. If automated checks cannot establish correctness, mark the claim as `needs_review` or equivalent. Do not silently turn uncertainty into a passing result.
5. Apply limitations that are relevant to the selected workflow/claim. Do not require an unrelated limitation from elsewhere in a large evidence pack to appear in every video, but never omit a relevant caveat or contradict it.
6. Check source/API versions for code and behavior claims when version differences matter.
7. Parse or execute code in a safe, appropriately isolated environment when useful and feasible. Parsing success is not proof of conceptual correctness. Do not execute untrusted source code outside a sandbox.
8. Explain what remains unverified in each run report.

## 6. Code Display Contract

- Run a consistent `sanitize_code()` step on every applicable ingestion path (local Markdown, fetched documentation, and HTML code blocks). Strip Markdown fences and normalize presentation whitespace without silently altering code semantics.
- Display code as a complete, syntactically balanced, contiguous slice of source `code_evidence`. Never append generated code to the evidence corpus to make a false equality check pass.
- Do not truncate code at a fixed line count. If the code is too long, choose a smaller complete source-backed excerpt, split it across scenes at valid boundaries, or use a code-transform/reveal sequence. Do not clip closing braces, parentheses, or important parameters.
- Derive focus/highlight lines from actual tokens or source spans, not hardcoded line-number arrays.
- Preserve language-aware syntax highlighting. Prefer an existing robust tokenizer (for example, Shiki in the renderer if already available) over brittle token regexes; do not add a dependency without reviewing the current stack.
- Fit and wrap/reflow code to the available composition. A 26px code font at 1080p is a target, not permission to clip long lines. If readable rendering cannot be achieved, emit a QA failure instead of silently hiding text.
- Render technical syntax faithfully. TTS pronunciation substitutions must never mutate code, headings, or visible captions.

## 7. Branding and Content Isolation

- Never hardcode product-specific names, metrics, trace IDs, company slogans, API behavior, or fake events in generic renderer components.
- Never use a fake fallback such as `"Verified via official documentation"` unless that exact statement is backed by an actual verification record and the product design intentionally displays it.
- Missing required project/company identity must fail validation or require explicit user input. Do not silently substitute a different company.
- Keep `product_subject`, `product_company`, and `client_brand`/`publisher_brand` separate. A consulting company can publish a video about another vendor's product.
- Branding, source attribution, end cards, code, and evidence must all belong to the active run. Add regression tests for cross-project leakage (for example, an Inngest name appearing in a Stripe run).

## 8. Audio, Word Timing, and Captions

- Use supported neural TTS (for example, the repository's existing Edge-TTS integration) and pin/test the relevant dependency version. Do not silently fall back to `espeak`, `pyttsx3`, or generated tones.
- When relying on Edge-TTS word boundaries, explicitly request `WordBoundary` events and verify the library version/API, timestamp units, non-empty output, ordering, and text alignment. Do not assume defaults.
- Maintain a spoken-to-display mapping for phonetic substitutions (for example, spoken `step dot run` mapped to visible `step.run()`). Map the combined spoken token's start/end times back to the visible technical token without altering its display text.
- Preserve leading audio and natural pauses unless an intentional, tested policy says otherwise. Do not use broad silence-removal filters that can remove pauses inside sentences.
- Use measured per-scene PCM WAV durations for timeline calculations where that is the chosen architecture. If using 48 kHz PCM (`pcm_s16le`), verify the actual output format with media inspection tools.
- Define one explicit trailing-audio policy. Do not accidentally add a trim allowance and a padding duration that together create a different tail than intended. Measure the actual result and test sentence endings and inter-scene transitions.
- If master loudness normalization is used, normalize at the documented stage and measure the final output again. Verify that processing has not introduced timing discrepancies.
- Scene start times and word offsets must be based on measured audio/timeline data, not arbitrary minimum-duration clamping. Assert that scene durations, master audio duration, and rendered video duration agree within a documented tolerance.
- Precompute captions where possible. Respect sentence and scene boundaries, preserve technical identifiers, and optimize for rendered width/readability. Word/character counts are targets, not reasons to split identifiers or create unnatural captions.
- Visual transitions, code highlights, and workflow events must follow resolved word/time triggers; do not distribute events evenly by array index when their meaning depends on narration timing.

## 9. Visual Product and Quality Contracts

The target output is a premium, clear technical explanation—not a set of generic text cards. Keep brand consistency while choosing visuals that teach the concept.

- Use supported generic primitives only, as verified against the actual renderer: hook/problem, code spotlight/reveal/transform, terminal, workflow/state transition, diagram, evidence/summary cards, and takeaway/CTA. Do not assume a component exists because it appears in this list; verify it before wiring it into a plan.
- Release videos should show source-backed before/after changes. API walkthroughs should expose request/input, operation and response/output where sources support them. Failure/recovery videos should distinguish failure, timeout, retry and recovered/saved-result states accurately. Migration videos should show concrete old/new differences. Do not force all intents into one fixed five-beat storyboard.
- Use a deliberate output profile: 16:9 landscape for documentation, YouTube, websites and B2B release explainers; 9:16 vertical where explicitly requested. Layouts must reflow for each aspect ratio rather than merely crop/rescale one design.
- At 1080p, aim for readable captions (about 40px), body text (about 28px), code (about 26px), card subtitles (about 24px), and tags (about 18px), subject to actual layout constraints. The layout must reflow, split or fail QA rather than clip text to preserve these numbers.
- Keep the main visual stage spacious and compositionally balanced. Use roughly 80% of the usable frame when appropriate, not as an unconditional rule for every primitive or aspect ratio.
- Every scene change should have an explanatory purpose. Motion should clarify causal relationships, code changes, request flow, state transitions, or evidence—not merely decorate the frame.
- Post-render QA should check dimensions, FPS, audio/video duration/synchronization, blank or corrupt frames, text/code clipping where measurable, caption visibility, expected audio, and keyframes. Automated visual QA is not a substitute for human review of factual clarity and aesthetics.

## 10. Six Validation Gates

Use explicit pass/fail/needs-review results. Gate names and implementation may be mapped onto existing validators, but the contracts must remain testable.

1. **Schema and lineage:** all artifacts validate; evidence IDs exist; source/artifact hashes are coherent; project and branding identities are valid.
2. **Source-code fidelity:** displayed code is a source-backed contiguous excerpt after documented sanitization, with balanced syntax and no Markdown fences.
3. **Claim support:** every material claim/title/metric has applicable evidence; unbacked numbers and contradictions are rejected. Text overlap is heuristic only.
4. **Limitation and nuance:** relevant caveats are represented accurately; unsupported guarantees are blocked.
5. **Component/data integrity:** generic UI components contain no fake product-specific content, metrics, default company names or silent fallback claims; visual props are schema-valid.
6. **Final artifact QA:** after rendering, verify container/streams, intended resolution/FPS, audio and timing tolerances, keyframes, non-blank output, and visual defects detectable by tests.

Gates 1–5 are pre-render gates where applicable. Gate 6 is post-render. Some checks may need to run again after a repair; report the actual sequence.

## 11. Testing and Completion Reports

For every change:
- Add or update tests for the behavior changed, including a regression test for the original failure.
- Test both positive and negative cases (e.g. correct source snippet vs modified snippet, valid brand vs cross-brand leak, valid caveat vs contradictory claim, non-empty word events vs missing events).
- Run the relevant Python tests using the verified project interpreter, TypeScript checks, timeline/schema validation, a short Remotion frame check, and full renders only after earlier gates pass.
- Keep Stripe and Inngest as regression fixtures if they are present and still relevant; add at least one third product/source fixture to test generality without product-specific branches.
- A passing MP4/container check is not evidence that the educational content is correct.

Every task completion report must state:
1. Exact files created, changed, deleted, and why.
2. Important architectural decisions and trade-offs.
3. Commands/tests actually run and their results.
4. Render paths and inspected properties, if rendered.
5. What passed, failed, was skipped, or remains unverified.
6. Any migration risks or manual review still required.

Do not claim the system is production-ready solely because the listed tests pass. Production readiness requires evidence of repeatable end-to-end behavior, successful repair/invalidation, and human-reviewed representative videos.
