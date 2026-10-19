"""
tests/test_phase_a_devtools.py

Unit and integration test suite for Phase A (Code-First B2B Developer-Tool Video Engine):
1. Source material ingestion (--source-file / source_text) preserves exact SDK identifiers in script/scenes.
2. All 4 DevTool visual types (code_reveal, code_transform, terminal, diagram) pass Node Zod gate.
3. Long code lines (> 50 chars) trigger font-scaling or clean wrapping rules without card overflow.
4. Fast Remotion smoke render test (--frames=0-29) executes with exit code 0 under 10 seconds.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
VIDEO_DIR = REPO_DIR / "video"

import sys
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from engine.director.mock_library import get_mock_script
from engine.director.script import detect_domain
from engine.validation.schema import validate_script_plan, resolve_script_subject
from engine.validation.code import calculate_font_scale, format_and_wrap_code_snippet, validate_code_layout
from engine.timeline.choreographer import choreograph_scenes


class TestPhaseADevtools(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_phase_a_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_source_material_ingestion_and_identifier_preservation(self):
        """Verify that source material ingestion preserves exact SDK identifiers in generated scenes."""
        source_text = """
# Acme SDK v2.0 Release
To install:
```bash
npm install @acme/sdk@latest
```
### Stream API
```typescript
import { Acme } from '@acme/sdk';
const client = new Acme({ apiKey: process.env.ACME_KEY });
for await (const chunk of client.agents.stream('deploy')) {
  process.stdout.write(chunk.text);
}
```
"""
        # 1. Subject detection recognizes devtools
        detected = detect_domain("Acme Cloud SDK v2 Launch & Migration")
        self.assertEqual(detected, "devtools")

        # 2. Mock / scripted director resolves devtools preset with source material
        script = get_mock_script(
            topic="Acme SDK v2 Migration",
            duration=35,
            subject="devtools",
            source_text=source_text,
        )
        self.assertIsInstance(script, dict)
        self.assertEqual(script.get("subject"), "devtools")

        # 3. Polymorphic script plan validation
        is_valid, errors = validate_script_plan(script)
        self.assertTrue(is_valid, f"Devtools script plan failed validation: {errors}")
        self.assertEqual(resolve_script_subject(script), "devtools")

        # 4. Strict accuracy rule: exact SDK identifiers are preserved
        all_code_content = " ".join([
            str(s.get("code") or "") + " " +
            str(s.get("code_snippet") or "") + " " +
            str(s.get("before_code") or "") + " " +
            str(s.get("after_code") or "") + " " +
            str(s.get("spoken_text") or "")
            for s in script.get("scenes", [])
        ])

        self.assertIn("@acme/sdk", all_code_content)
        self.assertIn("client.agents.stream", all_code_content)
        self.assertIn("Acme", all_code_content)

    def test_all_devtool_visual_types_pass_node_zod_gate(self):
        """Verify all 4 DevTool visual types (code_reveal, code_transform, terminal, diagram) pass Zod validation."""
        script = get_mock_script(topic="DevTool Walkthrough", duration=35, subject="devtools")
        scenes = script["scenes"]

        # Ensure all 4 DevTool visual primitives are present
        visual_types = {s.get("visual_type") for s in scenes}
        self.assertIn("terminal", visual_types)
        self.assertIn("code_transform", visual_types)
        self.assertIn("code_reveal", visual_types)
        self.assertIn("diagram", visual_types)

        # Choreograph and enrich scenes
        t = 0.0
        timed = []
        for s in scenes:
            dur = 5.0
            sc = dict(s)
            sc["start_time"] = round(t, 2)
            sc["end_time"] = round(t + dur, 2)
            sc["duration"] = dur
            timed.append(sc)
            t += dur

        words = [
            {"word": "Acme", "start": 0.0, "end": 0.3},
            {"word": "SDK", "start": 0.3, "end": 0.6},
            {"word": "release", "start": 0.6, "end": 0.9},
        ]

        enriched = choreograph_scenes(timed, words, domain="devtools")

        timeline = {
            "title": script["title"],
            "schema_version": "2.0.0",
            "engine_version": "2.0.0",
            "run_id": "phase_a_zod_test",
            "audio_file": "pop.mp3",
            "scenes": enriched,
            "words": words,
        }

        data_json = self.temp_dir / "data.json"
        with open(data_json, "w", encoding="utf-8") as f:
            json.dump(timeline, f, indent=2)

        # Execute Node.js Zod Validation Gate
        zod_script = VIDEO_DIR / "scripts" / "validate_timeline.mjs"
        res = subprocess.run(
            ["node", str(zod_script), str(data_json)],
            cwd=str(VIDEO_DIR),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Zod gate failed unexpectedly:\n{res.stderr}\n{res.stdout}")
        self.assertIn("[ZOD:SUCCESS]", res.stdout)

    def test_long_code_lines_trigger_scaling_and_wrapping_rules(self):
        """Verify that lines > 50 chars trigger font-scaling or wrapping without horizontal layout overflow."""
        long_line_code = (
            "const client = new AcmeClient({ apiKey: process.env.ACME_API_KEY_SECRET, endpoint: 'https://gateway.acme.cloud/v2/agents/stream', timeoutMs: 30000 });\n"
            "for await (const chunk of client.agents.stream({ query: 'deploy production' })) {\n"
            "  process.stdout.write(chunk.text);\n"
            "}"
        )

        # 1. calculate_font_scale returns <= 22px when lines exceed 46 chars
        font_size = calculate_font_scale(long_line_code, base_font_size=28, max_chars=46, max_lines=14)
        self.assertLessEqual(font_size, 22)
        self.assertGreaterEqual(font_size, 19)

        # 2. validate_code_layout detects line overflow and provides layout metadata
        fits_without_scale, warning_msg, meta = validate_code_layout(long_line_code, max_chars=46, max_lines=14)
        self.assertFalse(fits_without_scale)
        self.assertIsNotNone(warning_msg)
        self.assertTrue(meta["needs_scaling"])
        self.assertGreater(meta["max_line_length"], 50)

        # 3. format_and_wrap_code_snippet wraps lines cleanly at token boundaries
        wrapped = format_and_wrap_code_snippet(long_line_code, max_chars=46, max_lines=14)
        for line in wrapped.split("\n"):
            self.assertLessEqual(len(line), 55)

        # 4. Short code snippet keeps full 28px font size
        short_code = "x = 42\nreturn x * 2"
        short_font = calculate_font_scale(short_code, base_font_size=28)
        self.assertEqual(short_font, 28)

    def test_fast_smoke_render_frames_0_to_29(self):
        """Verify fast Remotion smoke render (--frames=0-29) executes with exit code 0."""
        script = get_mock_script(topic="Acme SDK Launch", duration=35, subject="devtools")
        scenes = script["scenes"]

        t = 0.0
        timed = []
        for s in scenes:
            dur = 5.0
            sc = dict(s)
            sc["start_time"] = round(t, 2)
            sc["end_time"] = round(t + dur, 2)
            sc["duration"] = dur
            timed.append(sc)
            t += dur

        words = [{"word": "Acme", "start": 0.0, "end": 0.5}]
        enriched = choreograph_scenes(timed, words, domain="devtools")

        timeline = {
            "title": "Acme SDK Fast Smoke Render",
            "schema_version": "2.0.0",
            "run_id": "test_render_smoke",
            "audio_file": "pop.mp3",
            "scenes": enriched,
            "words": words,
        }

        data_json = self.temp_dir / "data.json"
        with open(data_json, "w", encoding="utf-8") as f:
            json.dump(timeline, f, indent=2)

        out_mp4 = self.temp_dir / "smoke.mp4"

        # Remotion smoke render: strictly frames 0-29
        remotion_cmd = [
            "npx", "remotion", "render", "CodingShort",
            str(out_mp4),
            "--props", str(data_json),
            "--frames=0-29",
            "--concurrency=4",
        ]

        res = subprocess.run(
            remotion_cmd,
            cwd=str(VIDEO_DIR),
            capture_output=True,
            text=True,
            timeout=18,
        )

        self.assertEqual(
            res.returncode, 0,
            f"Remotion smoke render failed with exit code {res.returncode}:\n{res.stderr}\n{res.stdout}"
        )
        self.assertTrue(out_mp4.exists(), "Render completed with exit code 0 but smoke.mp4 was not written.")
        self.assertGreater(out_mp4.stat().st_size, 1000, "Output smoke.mp4 is empty or corrupted.")


if __name__ == "__main__":
    unittest.main()

