# Evidence-Driven B2B Developer-Tool Video Engine

An automated, evidence-grounded video production engine for B2B developer-tool companies. It converts official technical documentation, code snippets, release notes, and API references into synchronized, technically faithful technical explainer videos rendered with Remotion.

Every material statement, metric, on-screen label, and animated behavior links directly to an authoritative `evidence_id` extracted from primary documentation.

---

## 1. Core Architectural Pipeline

All video generation uses a single authoritative pipeline:

```
ProjectProfile -> Source/Release Ingestion -> EvidencePack -> WorkflowSelector -> ScenePlanner -> Pre-render Validation -> Narration/TTS -> Word-Timing & Token Mapping -> TimelineMapper -> Remotion Render -> Post-render QA -> Run Report/Studio
```

1. **ProjectProfile:** Defines project identity, `product_subject`, `product_company`, `publisher_brand`, target audience, aspect ratio (`16:9` widescreen or `9:16` vertical), and official source links.
2. **Source Ingestion:** Loads local Markdown, fetches remote documentation, or parses release changelogs.
3. **EvidencePack:** Extracts atomic, source-linked `EvidenceRecord`s (`concept`, `developer_action`, `behavior`, `failure_behavior`, `limitation`, `code_evidence`, `metric`, `release_change`) with SHA-256 section hashes.
4. **WorkflowSelector:** Evaluates candidate developer workflows across 6 criteria to pick the clearest narrative without hardcoded company branches.
5. **ScenePlanner:** Translates selected workflows and evidence into an evidence-linked scene plan (`scene_plan.json`).
6. **Pre-render Validation:** Enforces Gates 1–5 (Schema & Lineage, Code Fidelity, Claim Support, Limitation Propagation, Component Lint).
7. **Narration / Neural TTS:** Synthesizes natural spoken developer English using Edge-TTS with phonetic pronunciation rules.
8. **Word-Timing & Token Mapping:** Captures native `WordBoundary` timestamps and collapses phonetic replacements back to visible code tokens (e.g. spoken `step dot run` mapped to visible `step.run()`).
9. **TimelineMapper:** Uses measured per-scene PCM WAV durations (48kHz) to compute exact cumulative timeline offsets and precompute subtitle chunks.
10. **Remotion Render:** Renders frame-accurate video using Remotion and React visual primitives.
11. **Post-render QA:** Gate 6 validates container streams, duration sync, keyframes, non-blank frames, and readability.

---

## 2. Supported Video Intents

1. **Documentation-grounded developer workflow explainers:** Focuses on atomic developer primitives and distributed workflows.
2. **Release notes and before/after change explainers:** Contrasts legacy API patterns with new syntax, backed by release changelogs.
3. **API/SDK walkthroughs:** Step-by-step request payload, endpoint execution, and response payload handling.
4. **Failure, retry, and recovery explainers:** Explains network dropouts, HTTP 503 errors, and state recovery guarantees.
5. **Migration and upgrade guides:** Highlights deprecated configurations and side-by-side replacements.
6. **Product-feature explainers:** Verifiable feature walkthroughs backed by official documentation.

---

## 3. Quickstart & Usage

### Prerequisites
- Python 3.11+ in a virtual environment (`.venv/bin/python`)
- Node.js 20+ and npm
- FFmpeg and FFprobe installed in system `PATH`

### Installation
```bash
# Verify Python virtualenv
.venv/bin/python -m pip install -r requirements.txt

# Install Remotion dependencies
cd video && npm install && cd ..
```

### Running Generation (CLI)
```bash
# Offline verification mode using Inngest fixture (16:9 widescreen)
.venv/bin/python generate_and_render.py --project projects/inngest_step_run.json --mock --aspect-ratio 16:9

# Offline verification mode using Stripe fixture (9:16 vertical)
.venv/bin/python generate_and_render.py --project projects/stripe_idempotency.json --mock --aspect-ratio 9:16

# Quick 3-second (90-frame) benchmark render
.venv/bin/python generate_and_render.py --project projects/inngest_step_run.json --mock --fast-test
```

### Running Local Studio Control Room
```bash
.venv/bin/python -m uvicorn studio_api:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000/studio_ui/index.html in your browser
```

### Running Test Suites
```bash
# Run all active Python unit and validation gate tests
.venv/bin/python -m pytest

# Run Node.js timeline schema validation gate
node video/scripts/validate_timeline.mjs video/public/data.json
```

---

## 4. Authoritative Six Validation Gates

The engine enforces six testable validation gates across pre-render and post-render stages:

| Gate | Name | Pipeline Stage | Primary Implementation | Contract & Verification Rules |
| :--- | :--- | :--- | :--- | :--- |
| **Gate 1** | **Lineage & Citation Integrity** | Pre-render | `validate_evidence_and_plan` (`claim_citation`, `banned_contamination_tokens`) | Every scene must cite valid evidence IDs from `evidence_pack.json`. Rejects unbacked claims, missing records, and placeholder contamination (`lorem`, `todo`, `mock_metric`). |
| **Gate 2** | **Source-Code Fidelity** | Pre-render | `validate_evidence_and_plan` (internal: `gate1_contiguous_code_equality`) | Displayed code must be an exact contiguous slice (or normalized whitespace match) of source `code_evidence`. Fails if delimiters are unbalanced or markdown fences (` ``` `) leak into output. |
| **Gate 3** | **Claim & Metric Support** | Pre-render | `validate_evidence_and_plan` (internal: `gate2_quote_paraphrase`, `numerical_claims`) | Rejects unbacked numbers in spoken text and metric cards. Enforces $\ge 0.35$ content-word overlap between on-screen text and cited evidence excerpts. |
| **Gate 4** | **Limitation Propagation** | Pre-render | `validate_evidence_and_plan` (internal: `gate3_limitation_propagation`) | When limitation records exist, enforces that documented caveats are cited and displayed on-screen ($\ge 2$ content words). Rejects `"GUARDED"` placeholder anti-pattern. |
| **Gate 5** | **Component Integrity & Timeline Schema** | Pre-render | `validate_evidence_and_plan` (internal: `gate4_component_literal_lint`) & `video/scripts/validate_timeline.mjs` | Lints React components to prevent hardcoded brand tokens (`inngest`, `stripe`, `resend`, `#00e599`, `step.run`). Validates assembled `data.json` against Node.js TypeScript Zod schema. |
| **Gate 6** | **Post-Render Technical QA** | Post-render | `validate_post_render_qa` (`output.py` + keyframe check) | Inspects MP4 container streams (h264/aac), resolution (1920x1080 or 1080x1920), FPS (30), audio/video duration sync ($\le 0.5\text{s}$ tolerance), and extracts midpoint keyframe to verify non-blank video. Quarantines corrupt video to `.corrupt.mp4`. |

---

## 5. Current Capabilities vs. Roadmap

### Current Production Capabilities (Implemented & Verified)
- **Remotion-Only Video Generation:** Frame-accurate React rendering for both 16:9 widescreen and 9:16 vertical developer videos.
- **Unified 11-Step Pipeline:** Single data-driven execution flow from documentation ingestion to final MP4 QA.
- **Evidence-Linked Scene Planning:** Dynamic 5-beat story arcs derived from atomic evidence records without hardcoded company branches.
- **Cross-Brand Isolation:** Strict separation of `product_subject`, `product_company`, and `publisher_brand` with zero asset/token leakage across Inngest, Stripe, and Resend runs.
- **Zero-Drift Neural Audio:** Measured 48kHz PCM WAV headers drive Remotion frame counts and spoken-word subtitle chunking.
- **Surgical Scene Revisions:** Mode A (visual-only) and Mode B (narration) scene re-rendering and FFmpeg segment stitching via Studio API.

### Future Roadmap (Under Specification)
- **Isolated CLI Execution Adapter:** Safe sandbox execution of documented terminal commands and curl snippets with captured exit codes and environment metadata.
- **Explicit Evidence Provenance Badges:** On-screen visual tags distinguishing `[OBSERVED EXECUTION]` from `[ILLUSTRATIVE MODEL]`.
- **Fine-Grained Dependency Graph:** Full `dependency_graph.json` tracking `source -> evidence record -> scene -> audio -> video segment` for automatic invalidation upon upstream documentation edits.
- **Browser Automation Capture:** Automated headless browser recording of interactive developer consoles.
