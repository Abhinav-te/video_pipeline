# Agent Instructions: Video Pipeline Engine — Checkpoint 01 (Manim Reliability & Layout Safe-Zones) & Checkpoint 02 (Dependency-Aware Scene Regeneration)

You are a Principal Systems & Video Pipeline Architect.
Your objective is to execute **Checkpoint 01** and **Checkpoint 02** of our Production Engineering Roadmap:
1. **Checkpoint 01 (Manim & Layout Reliability)**: Fix frozen Manim playback inside Remotion, enforce motion/duration verification on compiled Manim clips, enforce strict subtitle layout safe-zones, and eliminate hardcoded cross-subject text leaks via generalizable schema/renderer rules.
2. **Checkpoint 02 (Surgical Scene Regeneration & Versioning)**: Build a dependency-aware artifact manifest (`manifest.json`), isolated per-scene audio & render segments (`segments/scene_<id>_v<N>.mp4`), and a non-destructive revision engine supporting **Mode A (Visual-Only Revision)** and **Mode B (Narration Revision)** with instant FFmpeg segment recomposition.

---

## 1. Checkpoint 01: Manim Contract, Motion Verification & Layout Generalization

### A. Fix Frozen Manim Playback in Remotion (`video/src/CodingShort.jsx` & Scene Components)
- **Root Cause**: When `<OffthreadVideo>` renders inside a scene without a scene-local `<Sequence from={sceneStartFrame} durationInFrames={sceneDurationFrames}>`, Remotion seeks `<OffthreadVideo>` using the **global timeline frame** instead of frame `0` of the current scene. By Scene 3 (`t = 10s`), a 4.5-second Manim video is already past its end and frozen on its final frame.
- **Mandatory Fix**:
  1. In `CodingShort.jsx` (or inside `ManimScene.jsx` / `MathScene.jsx` / `GraphScene.jsx` / `QuantumScene.jsx`), wrap every active scene body (and every `<OffthreadVideo>`) inside `<Sequence from={sceneStartFrame} durationInFrames={sceneDurationFrames}>` so `<OffthreadVideo>` ALWAYS begins at `0.0s` when the scene starts.
  2. In `engine/renderer/manim_compiler.py` (and `manim_templates.py`), ensure every Manim scene distributes `run_time` across its full target `duration`:
     - **`equation_morph`**: `Write(step1)` (`30%` duration) $\rightarrow$ `ReplacementTransform(step1, step2)` (`40%` duration) $\rightarrow$ animated `SurroundingRectangle` focus pulse (`30%` duration).
     - **`calculus_graph`**: `Create(axes)` + `Create(curve)` (`25%` duration) $\rightarrow$ `ValueTracker` sweeping `x` continuously from `x_min` to `x_max` (`75%` duration) with `always_redraw` updating both the moving tangent line and expanding Riemann rectangles on every frame.
     - **`riemann_refinement` / `antiderivative_bounds` / `vector_field` / `quantum_wave`**: Ensure distinct scene indices in the same video never receive identical curve parameters or static `self.add()` calls.

### B. Automated Manim Output Verification (`engine/validation/manim_verifier.py`)
- A subprocess returning exit code `0` does not prove the Manim video is valid.
- After compiling `assets/manim_scene_<id>.mp4`, verify:
  1. **Stream & Duration Check (`ffprobe`)**: Video stream exists, resolution matches `920x920` (or configured dimensions), and `abs(actual_duration - expected_duration) <= 0.75s`.
  2. **Motion Check (Frame Diff)**: Extract two grayscale frames at `20%` and `80%` of the clip duration using `ffmpeg` and verify mean absolute pixel difference `> 0.5` (proving the animation actually moved and is not blank or frozen).

### C. Generalize Layout Safe-Zones & Eliminate Hardcoded Cross-Domain Strings
- **Subtitle Safe-Zone Rule (`video/src/`)**:
  - Reserve the bottom `320px` (`y = 1600px..1920px`) exclusively for captions and progress HUD.
  - Constrain all scene card containers (`ConceptScene`, `BentoGridScene`, `ComparisonScene`, `ManimScene`, etc.) to `maxHeight: 1360px` (`top: 90px`, `bottom: 340px`) with automatic text truncation/scaling so scene cards never collide with bottom captions regardless of text length.
- **Zero Cross-Subject Hardcoded Fallbacks**:
  - Remove hardcoded ML strings (`"Fails on non-Convex: 54% Acc"`, `"High-dimensional raw feature distribution"`, `"Cluster separation"`) from `ConceptScene` / `CodingShort.jsx` and replace generic `"Scene 1"` / `"Scene 2"` titles in `mock_library.py` with descriptive titles.
  - Remove hardcoded Electrical Engineering mini-SVG labels (`"CURRENT LOOP I_1"`, `"NODE CONSERVATION"`, `"MATCHED IMPEDANCE"`, `"4-NODE MESH TOPOLOGY"`) from `BentoGridScene.jsx` when `subject != "electrical"`; derive mini-SVG labels dynamically from each card's `title` / `badge` or domain schema.
  - Ensure `zod` in `video/package.json` is pinned to the exact version required by Remotion (`4.5.4` or `npx remotion add zod`) so `npx remotion versions` reports zero warnings.

---

## 2. Checkpoint 02: Dependency-Tracked Scene Regeneration & Non-Destructive Revisions

### A. Stable Scene IDs, Isolated Scene Audio & Artifact Manifest (`engine/pipeline/manifest.py`)
1. **Per-Scene Audio Synthesis & Alignment (`engine/audio/` & `engine/timeline/`)**:
   - Store per-scene audio files in `runs/<run_id>/scenes/<scene_id>/audio_v<rev>.mp3` and per-scene word timestamps (`0.0s` to `scene_duration`).
   - Concatenate per-scene audio into the master `audio.mp3` and compute cumulative scene start/end offsets deterministically.
2. **Dependency Hashes (`runs/<run_id>/manifest.json`)**:
   - Track project `revision` (`1, 2, ...`) and per-scene state:
     - `visual_hash = sha256(visual_type + sub_mode + canonical_json(visual_props) + round(duration, 2))`
     - `audio_hash = sha256(narration.strip() + voice_id)`
     - `segment_video`: `segments/scene_<scene_id>_v<rev>.mp4`
     - `manim_asset`: `assets/manim_<scene_id>_v<rev>.mp4` (if applicable)
   - Save every revision snapshot to `runs/<run_id>/revisions/rev_<NNN>/data.json` before mutating so the last valid render is always preserved and recoverable.

### B. Per-Scene Segment Rendering & Fast FFmpeg Recomposition (`engine/renderer/segment_stitcher.py`)
- Render each scene (or only dirty scenes whose `visual_hash` or `audio_hash` changed) into `runs/<run_id>/segments/scene_<scene_id>_v<rev>.mp4` using Remotion frame ranges (`--frames=<startFrame>-<endFrame>`).
- Stitch all current scene segment MP4s in order using `ffmpeg -f concat -safe 0 -i concat_list.txt -c copy` into `runs/<run_id>/revisions/rev_<NNN>/output.mp4` (and copy to the target `--output` path).

### C. Revision CLI Entrypoints (`generate_and_render.py` & `engine/revise.py`)
Add first-class CLI support for surgical scene revisions on any existing `--run-id`:

1. **Mode A — Visual-Only Revision (`--revise-visual`)**:
   ```bash
   python3 generate_and_render.py \
     --run-id <run_id> \
     --revise-scene <scene_id> \
     --set-visual-type <visual_type> \
     [--set-title "..."] \
     [--set-Visual-json '{...}'] \
     --output video/out/revised_visual.mp4
   ```
   - **Contract**: Keeps `audio_v<N>.mp3` and word timestamps for `<scene_id>` and all other scenes 100% untouched. Re-runs Manim (if `<visual_type>` uses Manim) and Remotion **ONLY for `<scene_id>`'s frame range**, recomposes all segments via FFmpeg, validates the output, and increments the revision in `manifest.json`.

2. **Mode B — Narration Revision (`--revise-narration`)**:
   ```bash
   python3 generate_and_render.py \
     --run-id <run_id> \
     --revise-scene <scene_id> \
     --set-narration "New spoken explanation for this specific scene." \
     --output video/out/revised_narration.mp4
   ```
   - **Contract**: Regenerates TTS audio and Whisper word timestamps **ONLY for `<scene_id>`** (leaving all other scenes' audio files untouched), updates `<scene_id>`'s duration and shifts downstream scene start offsets by $\Delta t$, re-renders `<scene_id>`'s visual segment to match its new duration, stitches the full video, and increments the revision in `manifest.json`.

---

## 3. Regression Test Suite (`tests/test_checkpoint_01_02.py`)
Create automated regression tests covering:
1. **Manim Motion & Duration Contract**: Verifies compiled Manim `.mp4` clips match target scene duration and have non-zero pixel delta between `20%` and `80%` frames.
2. **No Cross-Domain Fallback Leaks**: Verifies `math`, `code`, `quantum_physics`, and `chemistry` timelines contain zero occurrences of `"Fails on non-Convex"`, `"CURRENT LOOP I_1"`, or `"Euler's identity"` (unless requested).
3. **Mode A (Visual-Only Revision)**: Modifies Scene 2's visual in a mock run, verifies Scene 2's `visual_hash` changes while `audio_hash` and all other scenes' hashes remain identical, and verifies only Scene 2 is re-rendered.
4. **Mode B (Narration Revision)**: Modifies Scene 2's narration, verifies only Scene 2's audio is regenerated, downstream scene start timestamps shift accurately by $\Delta t$, and `revisions/rev_001` is preserved alongside `revisions/rev_002`.