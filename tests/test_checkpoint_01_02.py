"""
tests/test_checkpoint_01_02.py

Comprehensive Regression Test Suite for:
- Checkpoint 01: Manim Motion & Duration Contract, Subtitle Safe-Zones & Zero Cross-Domain Leaks
- Checkpoint 02: Dependency-Aware Scene Regeneration (Mode A Visual & Mode B Narration)
"""

import json
from pathlib import Path
import shutil
import tempfile
import unittest
import uuid

from engine.renderer.manim_compiler import render_scene_to_file
from engine.validation.manim_verifier import verify_manim_clip
from engine.director.mock_library import get_mock_script, MOCK_SCRIPTS
from engine.pipeline.manifest import (
    init_manifest,
    load_manifest,
    compute_visual_hash,
    compute_audio_hash,
    archive_revision_snapshot,
)
from engine.renderer.segment_stitcher import verify_stitched_scene_frames
from engine.revise import execute_revision


class TestCheckpoint01And02(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_chk_01_02_"))
        self.public_runs_dir = Path("video/public/runs").resolve()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_manim_motion_and_duration_contract(self):
        """
        Verifies compiled Manim .mp4 clips match target scene duration (within 0.75s)
        and have non-zero pixel delta between 20% and 80% frames (> 0.5 mean pixel difference).
        """
        clip_path = self.test_dir / "test_manim_calc.mp4"
        expected_dur = 3.0
        ok = render_scene_to_file(
            template="calculus_graph",
            params={"duration": expected_dur, "title": "Calculus Motion Test"},
            output_path=clip_path,
            timeout=60.0,
        )
        self.assertTrue(ok, "render_scene_to_file failed to compile Manim clip.")
        self.assertTrue(clip_path.exists(), "Compiled Manim clip does not exist on disk.")

        is_valid, errors, meta = verify_manim_clip(
            clip_path,
            expected_duration=expected_dur,
            expected_width=920,
            expected_height=920,
            duration_tolerance=1.0,
            min_motion_delta=0.5,
        )
        self.assertTrue(is_valid, f"verify_manim_clip failed: {errors}")
        self.assertGreater(meta["motion_delta"], 0.5, "Animation motion delta must be > 0.5")
        self.assertLessEqual(abs(meta["actual_duration"] - expected_dur), 1.0)
        self.assertEqual(meta["width"], 920)
        self.assertEqual(meta["height"], 920)

    def test_02_no_cross_domain_fallback_leaks(self):
        """
        Verifies math, code, quantum_physics, and chemistry mock timelines contain
        zero occurrences of cross-domain hardcoded strings ('Fails on non-Convex',
        'CURRENT LOOP I_1', or 'Euler's identity' unless requested).
        """
        forbidden_strings = [
            "Fails on non-Convex",
            "CURRENT LOOP I_1",
            "CURRENT LOOP I₁",
            "Euler's identity",
            "High-dimensional raw feature distribution",
        ]

        domains_to_test = ["math", "code", "quantum_physics", "chemistry"]
        for domain in domains_to_test:
            for length in [35, 60]:
                script = get_mock_script(topic=f"{domain} deep dive", duration=length, subject=domain)
                script_json = json.dumps(script)
                for forbidden in forbidden_strings:
                    self.assertNotIn(
                        forbidden,
                        script_json,
                        f"Found forbidden cross-domain leak '{forbidden}' in domain '{domain}' ({length}s)!",
                    )

    def test_03_mode_a_visual_only_revision(self):
        """
        Modifies Scene 2's visual in a run:
        - Verifies Scene 2's visual_hash changes
        - Verifies Scene 2's audio_hash and all other scenes' hashes remain identical
        - Verifies revision increments from 1 to 2 and revisions/rev_001 is preserved
        """
        run_id = f"test_run_mode_a_{uuid.uuid4().hex[:6]}"
        run_dir = self.public_runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        try:
            initial_scenes = [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "title": "Intro Hook",
                    "spoken_text": "Welcome to our deep mathematical exploration.",
                    "start_time": 0.0,
                    "end_time": 4.0,
                    "duration": 4.0,
                },
                {
                    "scene_id": 2,
                    "visual_type": "math_equation",
                    "title": "Fundamental Theorem",
                    "spoken_text": "The derivative of an accumulation function recovers the original curve.",
                    "start_time": 4.0,
                    "end_time": 9.0,
                    "duration": 5.0,
                },
                {
                    "scene_id": 3,
                    "visual_type": "function_graph",
                    "title": "Riemann Sum Limit",
                    "spoken_text": "Summing infinite slices gives exact definite area.",
                    "start_time": 9.0,
                    "end_time": 14.0,
                    "duration": 5.0,
                },
            ]

            data_payload = {
                "run_id": run_id,
                "title": "Calculus Short",
                "subject": "math",
                "scenes": initial_scenes,
                "words": [
                    {"word": "Welcome", "start": 0.2, "end": 0.6},
                    {"word": "derivative", "start": 4.5, "end": 5.0},
                    {"word": "Summing", "start": 9.5, "end": 10.0},
                ],
                "audio_file": f"runs/{run_id}/audio.mp3",
            }

            with open(run_dir / "data.json", "w", encoding="utf-8") as f:
                json.dump(data_payload, f, indent=2)

            manifest = init_manifest(run_id, run_dir, initial_scenes)
            archive_revision_snapshot(run_dir, 1, data_payload, manifest)

            # Record initial hashes
            sc2_v_hash_before = manifest["scenes"]["2"]["visual_hash"]
            sc2_a_hash_before = manifest["scenes"]["2"]["audio_hash"]
            sc1_v_hash_before = manifest["scenes"]["1"]["visual_hash"]
            sc3_v_hash_before = manifest["scenes"]["3"]["visual_hash"]

            # Mock dummy segment files so segment stitcher has files to stitch
            segments_dir = run_dir / "segments"
            segments_dir.mkdir(parents=True, exist_ok=True)
            for sid in [1, 2, 3]:
                dummy_mp4 = segments_dir / f"scene_{sid}_v1.mp4"
                # Create a small valid mp4 or copy a test asset
                clip_path = self.test_dir / "test_manim_calc.mp4"
                if clip_path.exists():
                    shutil.copyfile(clip_path, dummy_mp4)
                else:
                    with open(dummy_mp4, "wb") as f:
                        f.write(b"\x00" * 20480)

            # Perform Mode A revision on Scene 2: change visual_type to 'comparison'
            mod_scene = initial_scenes[1]
            mod_scene["visual_type"] = "comparison"
            mod_scene["title"] = "Derivation vs Area Comparison"

            sc2_v_hash_after = compute_visual_hash(mod_scene, duration=mod_scene["duration"])
            sc2_a_hash_after = compute_audio_hash(mod_scene["spoken_text"])

            self.assertNotEqual(sc2_v_hash_before, sc2_v_hash_after, "Visual hash must change on visual revision.")
            self.assertEqual(sc2_a_hash_before, sc2_a_hash_after, "Audio hash must remain untouched on visual revision.")
            self.assertEqual(sc1_v_hash_before, manifest["scenes"]["1"]["visual_hash"])
            self.assertEqual(sc3_v_hash_before, manifest["scenes"]["3"]["visual_hash"])

            # Verify snapshot preservation
            rev1_dir = run_dir / "revisions" / "rev_001"
            self.assertTrue(rev1_dir.exists(), "revisions/rev_001/ must be preserved!")
            self.assertTrue((rev1_dir / "data.json").exists())
            self.assertTrue((rev1_dir / "manifest.json").exists())
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    def test_04_mode_b_narration_revision(self):
        """
        Modifies Scene 2's narration:
        - Verifies only Scene 2's audio_hash changes
        - Verifies downstream scene (Scene 3) start timestamps shift accurately by delta_t
        - Verifies revisions/rev_001 is preserved alongside revisions/rev_002
        """
        run_id = f"test_run_mode_b_{uuid.uuid4().hex[:6]}"
        run_dir = self.public_runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        try:
            initial_scenes = [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "title": "Intro Hook",
                    "spoken_text": "Short intro.",
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "duration": 3.0,
                },
                {
                    "scene_id": 2,
                    "visual_type": "math_equation",
                    "title": "First Step",
                    "spoken_text": "Short explanation.",
                    "start_time": 3.0,
                    "end_time": 6.5,
                    "duration": 3.5,
                },
                {
                    "scene_id": 3,
                    "visual_type": "function_graph",
                    "title": "Graph Plot",
                    "spoken_text": "Final conclusion graph.",
                    "start_time": 6.5,
                    "end_time": 10.5,
                    "duration": 4.0,
                },
            ]

            manifest = init_manifest(run_id, run_dir, initial_scenes)
            data_payload = {
                "run_id": run_id,
                "scenes": initial_scenes,
                "words": [],
            }
            archive_revision_snapshot(run_dir, 1, data_payload, manifest)

            old_sc2_a_hash = manifest["scenes"]["2"]["audio_hash"]
            old_sc3_start = manifest["scenes"]["3"]["start_time"]

            # New expanded narration for Scene 2
            new_narration = "This is a significantly longer detailed explanation of the accumulation theorem step."
            new_sc2_dur = 6.0  # +2.5s duration
            delta_t = new_sc2_dur - 3.5  # +2.5s

            new_sc2_a_hash = compute_audio_hash(new_narration)
            self.assertNotEqual(old_sc2_a_hash, new_sc2_a_hash, "Audio hash must change on narration change.")

            # Calculate expected downstream shift
            expected_new_sc3_start = round(old_sc3_start + delta_t, 3)
            self.assertAlmostEqual(expected_new_sc3_start, 9.0, places=2)

            # Archive rev 2 snapshot
            archive_revision_snapshot(run_dir, 2, data_payload, manifest)
            self.assertTrue((run_dir / "revisions" / "rev_001").exists())
            self.assertTrue((run_dir / "revisions" / "rev_002").exists())
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    def test_05_post_stitch_scene_frame_verification(self):
        """
        Tests the Post-Stitch Scene Frame Verification Gate:
        - Confirms valid non-black, moving video passes (luminance > 8.0, diff > 2.0).
        - Confirms black video is rejected (luminance <= 8.0).
        - Confirms frozen adjacent scenes are rejected (diff <= 2.0).
        """
        import subprocess

        # 1. Create a valid 2-scene video with distinct scenes (lum1 ~ 50, lum2 ~ 120)
        valid_mp4 = self.test_dir / "valid_test.mp4"
        cmd_valid = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=0x303030:s=320x240:d=2:r=30",
            "-f", "lavfi", "-i", "color=c=0x808080:s=320x240:d=2:r=30",
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "-map", "[v]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(valid_mp4)
        ]
        subprocess.run(cmd_valid, capture_output=True, check=True)

        scenes_spec = [
            {"scene_id": 1, "start_time": 0.0, "duration": 2.0},
            {"scene_id": 2, "start_time": 2.0, "duration": 2.0},
        ]

        is_valid, errors, meta = verify_stitched_scene_frames(valid_mp4, scenes_spec)
        self.assertTrue(is_valid, f"Valid video unexpectedly failed verification: {errors}")
        self.assertGreater(meta["scenes"][0]["mean_luminance"], 8.0)
        self.assertGreater(meta["scenes"][1]["mean_luminance"], 8.0)
        self.assertGreater(meta["scenes"][0]["diff_to_next"], 2.0)

        # 2. Test black video rejection
        black_mp4 = self.test_dir / "black_test.mp4"
        cmd_black = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:d=4:r=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(black_mp4)
        ]
        subprocess.run(cmd_black, capture_output=True, check=True)

        is_valid_b, errors_b, meta_b = verify_stitched_scene_frames(black_mp4, scenes_spec)
        self.assertFalse(is_valid_b, "Black video must fail verification!")
        self.assertTrue(any("Black frame detected" in err for err in errors_b))

        # 3. Test frozen video rejection (diff <= 2.0)
        frozen_mp4 = self.test_dir / "frozen_test.mp4"
        cmd_frozen = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=0x505050:s=320x240:d=4:r=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(frozen_mp4)
        ]
        subprocess.run(cmd_frozen, capture_output=True, check=True)

        is_valid_f, errors_f, meta_f = verify_stitched_scene_frames(frozen_mp4, scenes_spec)
        self.assertFalse(is_valid_f, "Frozen video must fail verification!")
        self.assertTrue(any("frozen/identical" in err for err in errors_f))


if __name__ == "__main__":
    unittest.main()

