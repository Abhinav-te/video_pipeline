"""
tests/test_studio_api.py

Fast Unit & Integration Test Suite for Local Production Studio Control Room API (Checkpoint 04).
Uses FastAPI TestClient to verify:
1. GET / and GET /api/projects and GET /api/projects/test_rev_workflow.
2. Mode A visual revision & Mode B narration revision (parameter validation and state updates).
3. Non-destructive snapshot restore endpoint (POST /api/projects/{run_id}/restore/{rev_id}).
4. Master video export (POST /api/projects/{run_id}/export).
5. Generation job launch & validation (POST /api/projects/generate, GET /api/jobs/{job_id}).

Total execution time MUST stay under 15 seconds.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import studio_api
# ... rest of your tests
import copy
import datetime
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

import studio_api
from studio_api import app, RUNS_DIR, OUT_DIR, PUBLIC_DIR
from engine.pipeline.manifest import init_manifest, archive_revision_snapshot, save_manifest


class TestStudioAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.test_run_id = f"test_studio_run_{datetime.datetime.now().strftime('%H%M%S')}"
        self.test_run_dir = RUNS_DIR / self.test_run_id
        self.test_run_dir.mkdir(parents=True, exist_ok=True)

        # Baseline scenes
        self.scenes = [
            {
                "scene_id": 1,
                "title": "Introduction to Limits",
                "visual_type": "fullscreen_text",
                "spoken_text": "Welcome to calculus where we analyze rates of change.",
                "start_time": 0.0,
                "end_time": 4.0,
                "duration": 4.0,
            },
            {
                "scene_id": 2,
                "title": "Partition Slices",
                "visual_type": "function_graph",
                "spoken_text": "We slice the curve into small rectangular partitions.",
                "start_time": 4.0,
                "end_time": 9.0,
                "duration": 5.0,
            },
            {
                "scene_id": 3,
                "title": "Definite Integral",
                "visual_type": "math_equation",
                "spoken_text": "Taking the continuous limit yields the exact definite integral.",
                "start_time": 9.0,
                "end_time": 14.5,
                "duration": 5.5,
            },
        ]

        self.data_payload = {
            "run_id": self.test_run_id,
            "topic": "Calculus Fundamentals",
            "subject": "math",
            "duration": 14.5,
            "scenes": self.scenes,
            "words": [
                {"word": "Welcome", "start": 0.2, "end": 0.6},
                {"word": "calculus", "start": 0.7, "end": 1.2},
                {"word": "slice", "start": 4.2, "end": 4.6},
                {"word": "Taking", "start": 9.1, "end": 9.5},
            ],
        }

        # Write initial data.json & manifest
        with open(self.test_run_dir / "data.json", "w", encoding="utf-8") as f:
            json.dump(self.data_payload, f, indent=2)

        self.manifest = init_manifest(self.test_run_id, self.test_run_dir, self.scenes, fps=30)

        # Create dummy segment files and dummy output MP4
        segments_dir = self.test_run_dir / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        for sc in self.scenes:
            sid = sc["scene_id"]
            with open(segments_dir / f"scene_{sid}_v1.mp4", "wb") as f:
                f.write(b"\x00" * 2048)

        # Dummy master output video
        self.dummy_master_mp4 = self.test_run_dir / "output.mp4"
        with open(self.dummy_master_mp4, "wb") as f:
            f.write(b"\x00" * 4096)

        # Archive rev_001 snapshot
        archive_revision_snapshot(
            run_dir=self.test_run_dir,
            revision=1,
            data_payload=self.data_payload,
            manifest_data=self.manifest,
            output_mp4=self.dummy_master_mp4,
        )

    def tearDown(self):
        # Clean up temporary test run directory
        if self.test_run_dir.exists():
            shutil.rmtree(self.test_run_dir, ignore_errors=True)

    # =========================================================================
    # 1. ROOT & PROJECTS LIST TESTS
    # =========================================================================
    def test_01_get_root_and_health(self):
        """Tests that GET / serves studio UI and /api/health returns 200."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("LOCAL PRODUCTION STUDIO", resp.text)

        resp_health = self.client.get("/api/health")
        self.assertEqual(resp_health.status_code, 200)
        data = resp_health.json()
        self.assertEqual(data.get("status"), "ok")

    def test_02_get_visual_types(self):
        """Tests that GET /api/visual-types returns supported scene types."""
        resp = self.client.get("/api/visual-types")
        self.assertEqual(resp.status_code, 200)
        types = resp.json().get("visual_types", [])
        type_ids = [t["id"] for t in types]
        for expected in ["code_reveal", "comparison", "manim_scene", "math_equation", "quantum_sim"]:
            self.assertIn(expected, type_ids)

    def test_03_get_projects_and_test_rev_workflow(self):
        """Tests GET /api/projects and GET /api/projects/test_rev_workflow."""
        resp = self.client.get("/api/projects")
        self.assertEqual(resp.status_code, 200)
        projects = resp.json()
        self.assertIsInstance(projects, list)
        self.assertGreaterEqual(len(projects), 1)

        # Verify our newly set up test run is in the list
        run_ids = [p["run_id"] for p in projects]
        self.assertIn(self.test_run_id, run_ids)

        # Verify fields on our project summary
        target = next(p for p in projects if p["run_id"] == self.test_run_id)
        self.assertEqual(target["topic"], "Calculus Fundamentals")
        self.assertEqual(target["subject"], "math")
        self.assertEqual(target["scene_count"], 3)
        self.assertEqual(target["current_revision"], 1)
        self.assertTrue(target["has_output"])

        # Test pre-existing project test_rev_workflow if present
        if "test_rev_workflow" in run_ids:
            resp_rev = self.client.get("/api/projects/test_rev_workflow")
            self.assertEqual(resp_rev.status_code, 200)
            data_rev = resp_rev.json()
            self.assertEqual(data_rev["run_id"], "test_rev_workflow")
            self.assertGreaterEqual(data_rev["current_revision"], 1)
            self.assertIn("scenes_resolved", data_rev)
            self.assertIn("snapshots", data_rev)
            self.assertGreaterEqual(len(data_rev["snapshots"]), 1)

    def test_04_get_project_detail_and_resolved_assets(self):
        """Tests GET /api/projects/{run_id} returns full state with resolved URLs."""
        resp = self.client.get(f"/api/projects/{self.test_run_id}")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()

        self.assertEqual(payload["run_id"], self.test_run_id)
        self.assertEqual(payload["current_revision"], 1)
        self.assertEqual(len(payload["scenes_resolved"]), 3)

        sc1 = payload["scenes_resolved"][0]
        self.assertEqual(sc1["scene_id"], 1)
        self.assertEqual(sc1["visual_type"], "fullscreen_text")
        self.assertTrue(sc1["has_segment_video"])
        self.assertTrue(sc1["segment_video_url"].startswith(f"/public/runs/{self.test_run_id}/"))

        # Verify snapshots
        self.assertEqual(len(payload["snapshots"]), 1)
        self.assertEqual(payload["snapshots"][0]["rev_id"], "rev_001")
        self.assertTrue(payload["snapshots"][0]["has_video"])

    def test_05_get_project_not_found(self):
        """Tests GET /api/projects/non_existent_run returns 404."""
        resp = self.client.get("/api/projects/non_existent_run_999999")
        self.assertEqual(resp.status_code, 404)

    # =========================================================================
    # 2. PARAMETER VALIDATION TESTS (Mode A & Mode B)
    # =========================================================================
    def test_06_parameter_validation_mode_a(self):
        """Mode A requires at least one of visual_type, title, sub_mode, visual_props."""
        resp = self.client.post(
            f"/api/projects/{self.test_run_id}/scenes/1/revise-visual",
            json={},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("requires at least one of", resp.json()["detail"])

    def test_07_parameter_validation_mode_b(self):
        """Mode B requires non-empty narration."""
        resp = self.client.post(
            f"/api/projects/{self.test_run_id}/scenes/1/revise-narration",
            json={"narration": "    "},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cannot be empty", resp.json()["detail"])

    def test_08_generate_validation(self):
        """POST /api/projects/generate requires topic."""
        resp = self.client.post("/api/projects/generate", json={"topic": ""})
        self.assertEqual(resp.status_code, 400)

    # =========================================================================
    # 3. REVISION EXECUTION TESTS (Mode A & Mode B)
    # =========================================================================
    def test_09_mode_a_visual_revision_state_update(self):
        """
        Tests Mode A visual revision:
        - Mocks execute_revision to update data.json & manifest cleanly
        - Verifies API endpoint updates scene visual_type, title, and returns updated project state
        """
        def mock_execute_revision(run_id, target_scene_id, set_visual_type=None, set_title=None, set_visual_json=None, set_narration=None, output_path=None, fps=30):
            # Simulate execute_revision behavior on disk
            r_dir = RUNS_DIR / run_id
            with open(r_dir / "data.json", "r", encoding="utf-8") as f:
                d = json.load(f)
            for sc in d["scenes"]:
                if sc["scene_id"] == int(target_scene_id):
                    if set_visual_type:
                        sc["visual_type"] = set_visual_type
                    if set_title:
                        sc["title"] = set_title
            with open(r_dir / "data.json", "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)

            m = studio_api.load_manifest(r_dir)
            m["revision"] = m.get("revision", 1) + 1
            save_manifest(m, r_dir)
            return r_dir / "output.mp4"

        with patch("studio_api.execute_revision", side_effect=mock_execute_revision):
            resp = self.client.post(
                f"/api/projects/{self.test_run_id}/scenes/2/revise-visual",
                json={
                    "visual_type": "comparison",
                    "title": "Partition vs Riemann Integral",
                    "visual_props": {"comparison_sides": {"left": "Discrete", "right": "Continuous"}},
                },
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["current_revision"], 2)

            # Scene 2 should now have visual_type 'comparison' and updated title
            sc2 = next(s for s in data["scenes_resolved"] if s["scene_id"] == 2)
            self.assertEqual(sc2["visual_type"], "comparison")
            self.assertEqual(sc2["title"], "Partition vs Riemann Integral")

    def test_10_mode_b_narration_revision_state_update(self):
        """
        Tests Mode B narration revision:
        - Mocks execute_revision to update narration on disk
        - Verifies API endpoint returns updated project state with new spoken text
        """
        def mock_execute_narration(run_id, target_scene_id, set_visual_type=None, set_title=None, set_visual_json=None, set_narration=None, output_path=None, fps=30):
            r_dir = RUNS_DIR / run_id
            with open(r_dir / "data.json", "r", encoding="utf-8") as f:
                d = json.load(f)
            for sc in d["scenes"]:
                if sc["scene_id"] == int(target_scene_id):
                    sc["spoken_text"] = set_narration
                    sc["narration"] = set_narration
            with open(r_dir / "data.json", "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)

            m = studio_api.load_manifest(r_dir)
            m["revision"] = m.get("revision", 1) + 1
            save_manifest(m, r_dir)
            return r_dir / "output.mp4"

        with patch("studio_api.execute_revision", side_effect=mock_execute_narration):
            new_text = "Here we rigorously examine the infinite limit of Riemann sums."
            resp = self.client.post(
                f"/api/projects/{self.test_run_id}/scenes/3/revise-narration",
                json={"narration": new_text},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            sc3 = next(s for s in data["scenes_resolved"] if s["scene_id"] == 3)
            self.assertEqual(sc3["spoken_text"], new_text)

    # =========================================================================
    # 4. SNAPSHOT RESTORE TESTS (POST /api/projects/{run_id}/restore/{rev_id})
    # =========================================================================
    def test_11_restore_snapshot_non_destructive(self):
        """
        Tests non-destructive rollback:
        1. Current state is revision 1 (archived as rev_001).
        2. Mutate active state to simulate revision 2 changes.
        3. Restore rev_001.
        4. Verifies:
           - Revision 2 was safely snapshotted before rollback.
           - New active revision becomes 3 (strictly monotonic).
           - Active scene state reverts to rev_001 content.
           - History records restoration action.
        """
        # Step 1: Simulate that active state moved to revision 2
        rev2_data = copy.deepcopy(self.data_payload)
        rev2_data["scenes"][0]["title"] = "Modified Scene 1 Title in Rev 2"
        with open(self.test_run_dir / "data.json", "w", encoding="utf-8") as f:
            json.dump(rev2_data, f, indent=2)

        self.manifest["revision"] = 2
        save_manifest(self.manifest, self.test_run_dir)

        # Step 2: Trigger rollback to rev_001
        resp = self.client.post(f"/api/projects/{self.test_run_id}/restore/rev_001")
        self.assertEqual(resp.status_code, 200)
        restored = resp.json()

        # Step 3: Check revision number incremented to 3
        self.assertEqual(restored["current_revision"], 3)

        # Step 4: Scene 1 title must have reverted to rev_001's original title
        sc1 = next(s for s in restored["scenes_resolved"] if s["scene_id"] == 1)
        self.assertEqual(sc1["title"], "Introduction to Limits")

        # Step 5: Verify rev_002 snapshot was archived during restore
        rev2_snapshot_dir = self.test_run_dir / "revisions" / "rev_002"
        self.assertTrue(rev2_snapshot_dir.exists(), "Previous active state must be non-destructively preserved!")

        # Step 6: Verify rev_003 snapshot was created for the restored state
        rev3_snapshot_dir = self.test_run_dir / "revisions" / "rev_003"
        self.assertTrue(rev3_snapshot_dir.exists())

    def test_12_restore_nonexistent_snapshot_returns_404(self):
        """Tests that attempting to restore a nonexistent snapshot returns 404."""
        resp = self.client.post(f"/api/projects/{self.test_run_id}/restore/rev_999")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

    # =========================================================================
    # 5. PRODUCTION EXPORT TESTS (POST /api/projects/{run_id}/export)
    # =========================================================================
    def test_13_export_production_mp4(self):
        """Tests exporting master video with custom filename."""
        custom_name = "test_calculus_export_final.mp4"
        export_file = OUT_DIR / custom_name
        if export_file.exists():
            export_file.unlink()

        try:
            resp = self.client.post(
                f"/api/projects/{self.test_run_id}/export",
                json={"custom_filename": custom_name},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["filename"], custom_name)
            self.assertEqual(data["download_url"], f"/out/{custom_name}")
            self.assertTrue(export_file.exists())
            self.assertEqual(export_file.stat().st_size, self.dummy_master_mp4.stat().st_size)
        finally:
            if export_file.exists():
                export_file.unlink()

    # =========================================================================
    # 6. GENERATION JOB TRACKER TESTS
    # =========================================================================
    def test_14_generate_job_launch_and_status(self):
        """Tests POST /api/projects/generate registers a job and returns job_id."""
        with patch("threading.Thread") as mock_thread:
            # Prevent actual subprocess from spawning
            mock_inst = MagicMock()
            mock_thread.return_value = mock_inst

            resp = self.client.post(
                "/api/projects/generate",
                json={
                    "topic": "Quantum Harmonic Oscillator",
                    "subject": "quantum_physics",
                    "length": 35,
                    "mock": True,
                },
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("run_id", data)
            self.assertIn("job_id", data)
            self.assertEqual(data["status"], "running")

            # Check job query
            job_resp = self.client.get(f"/api/jobs/{data['job_id']}")
            self.assertEqual(job_resp.status_code, 200)
            job_data = job_resp.json()
            self.assertEqual(job_data["topic"], "Quantum Harmonic Oscillator")
            self.assertEqual(job_data["subject"], "quantum_physics")


if __name__ == "__main__":
    unittest.main()

