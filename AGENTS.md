# Agent Instructions: Video Pipeline Engine — Phase A.2 (Zero-Crash React Reliability, Customer Source/URL Ingestion & Final Git Commit)

## SPEED & EXECUTION RULES (CRITICAL)
1. **DO NOT scan `video/public/runs/`, `video/out/`, `node_modules/`, or `.venv/`.**
2. **NEVER run `npx tsc` (which downloads the wrong `tsc@2.0.4` npm package).** Use Node scripts or `npx remotion render ... --frames=0-1` to verify React components.
3. **Keep test suite execution fast (< 30 seconds).**

---

## Objective 1: Eliminate React Error #130 & Enforce Component Export Contracts

During `devtool_sdk_v2_demo.mp4`, Remotion crashed at frame 137 (Scene 2) with `Minified React error #130 (... got: undefined)`.
1. **Audit All Imports/Exports in `video/src/CodingShort.jsx` and `video/src/components/`**:
   - Inspect every `import` in `CodingShort.jsx` and every component in `video/src/components/` (`CodeRevealScene`, `CodeTransformScene`, `TerminalScene`, `DiagramScene`, `ComparisonScene`, `ManimScene`, `MathScene`, `GraphScene`, `BentoGridScene`, etc.).
   - Ensure every component file exports BOTH a named export AND `export default` (e.g., `export { TerminalScene }; export default TerminalScene;`) so neither default nor named imports can ever resolve to `undefined`!
   - Check every child tag or icon inside `video/src/components/*.jsx` to ensure no `undefined` sub-component is ever rendered as `<UndefinedComponent />`.
2. **Add `<SceneErrorBoundary>` & Safe Component Router in `CodingShort.jsx`**:
   - Wrap the scene switcher in a React class `SceneErrorBoundary` and verify `typeof TargetComponent === "function"` before rendering so an invalid element type is structurally impossible.
3. **Multi-Scene Frame Verification Gate**:
   - Render 1 frame from the middle of EVERY scene (`--frames=<midFrame>-<midFrame>`) of the 6-scene DevTool run (`fullscreen_text`, `terminal`, `code_transform`, `code_reveal`, `diagram`, `comparison`) to prove all 6 scene types render in Chromium with zero React errors!

---

## Objective 2: Customer Content & Internet Documentation Ingestion (`engine/ingestion/source_loader.py`)

Build `engine/ingestion/source_loader.py` so the pipeline can ingest real developer-tool material provided by customers or fetched from documentation URLs:

1. **Supported Input Modes (`generate_and_render.py`, `engine/generate.py`, `studio_api.py`)**:
   - `--source-file <path>`: Reads local `.md`, `.txt`, `.py`, `.ts`, `.js`, `.json`, or `.html` files.
   - `--source-url <url>`: Fetches any public documentation URL or GitHub README/release page (`urllib.request` with clean User-Agent + timeout), strips HTML tags (`<script>`, `<style>`, `<nav>`, `<header>`, `<footer>`), and preserves headings, paragraphs, and `<pre><code>` blocks as clean Markdown.
   - `--source-text "<string>"`: Direct raw text/markdown input (used by the Local Studio UI).
2. **Ground-Truth Fact & Code Extractor (`extract_source_facts(raw_text: str) -> dict`)**:
   - Automatically parses the customer's document to extract:
     - `product_name` / `title` (from H1/H2 or package name)
     - `cli_commands`: Extracted `$ ...`, `npm ...`, `npx ...`, `pip ...`, `uv ...`, `curl ...`, `docker ...` commands.
     - `code_snippets`: Extracted fenced code blocks (```` ```ts ... ``` ````) with language tags, split cleanly into short displayable lines (`<= 46 chars` per line, `<= 12 lines` per block).
     - `key_points`: Extracted bullet points, API endpoints (`GET /v1/...`, `POST /v1/...`), and benchmark numbers.
3. **End-to-End Propagation (Both Live Gemini Director AND `--mock` Mode)**:
   - Pass the extracted `source_facts` into `engine/director/script.py` AND `engine/director/mock_library.py` + `choreographer.py`!
   - **Crucial Reliability Rule**: Even when running in `--mock` mode (or if the LLM omits a code block), if the user passed `--source-file`, `--source-url`, or `--source-text`, populate the `terminal`, `code_reveal`, `code_transform`, and `diagram` scenes directly with the **actual CLI commands, code blocks, and product facts extracted from the customer's source document**!
4. **Update Local Production Studio UI (`studio_ui/index.html` & `studio_api.py`)**:
   - In the `+ NEW VIDEO PROJECT` panel in `studio_ui/index.html`, provide:
     - **Source URL input** (`https://...` docs or GitHub README link)
     - **Source Material / Docs / Code textarea** (paste customer README, changelog, or SDK code directly)
   - Display the ingested `source_facts` summary inside the Studio project inspector so the operator can see which customer facts were used.

---

## Objective 3: Verify End-to-End, Clean Up & Commit Everything to Git

1. Create a sample customer DevTool brief at `examples/sample_devtool_release.md` (e.g., an SDK release document with a CLI install command, a v1-vs-v2 code migration snippet, and an API architecture flow).
2. Run a full end-to-end verification render using that customer document:
   ```bash
   python3 generate_and_render.py \
     --topic "Acme EdgeCache SDK v2 Release" \
     --subject code \
     --source-file examples/sample_devtool_release.md \
     --length 35 \
     --mock \
     --output video/out/devtool_sdk_v2_demo.mp4
   ```
3. Confirm `devtool_sdk_v2_demo.mp4` renders all frames (`0` through `end`) with **zero React #130 errors**, passes `ffprobe` and post-render validation, and displays the customer's actual CLI commands and code from `examples/sample_devtool_release.md`.
4. Run all Python unit tests (`PYTHONPATH=. pytest`) and Node validation tests.
5. Stage and commit all source changes cleanly to Git (`git status` clean, ignoring temporary run/out artifacts).