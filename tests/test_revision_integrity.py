"""
tests/test_revision_integrity.py
Comprehensive regression tests for Phase 4.0:
- Task 2: Revision validation fail-closed behavior (evidence gate and timeline schema Zod gate).
- Task 3: Revision consistency, manifest audio tracking across multiple revisions, staging, snapshot restoration.
- Task 4: Advisory concurrency locking (RevisionLock) preventing simultaneous revision corruption.
"""

import copy
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from engine.pipeline.manifest import (
    RevisionLock,
    init_manifest,
    load_manifest,
    save_manifest,
    archive_revision_snapshot,
    restore_revision_snapshot,
)
from engine.revise import execute_revision


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_project(tmp_path: Path):
    """Sets up a disposable project run directory with initial valid state."""
    run_id = "test_disposable_proj"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)

    data_payload = {
        "version": 1,
        "run_id": run_id,
        "aspect_ratio": "16:9",
        "audio_file": f"runs/{run_id}/audio.wav",
        "words": [
            {"word": "Welcome", "start": 0.0, "end": 0.5},
            {"word": "to", "start": 0.5, "end": 0.8},
            {"word": "testing", "start": 0.8, "end": 1.5},
        ],
        "scenes": [
            {
                "scene_id": 1,
                "title": "Scene 1 Hook",
                "visual_type": "hook",
                "start_time": 0.0,
                "end_time": 1.5,
                "duration": 1.5,
                "spoken_text": "Welcome to testing",
                "evidence_ids": ["ev_1"],
            },
            {
                "scene_id": 2,
                "title": "Scene 2 Code",
                "visual_type": "code_spotlight",
                "start_time": 1.5,
                "end_time": 3.0,
                "duration": 1.5,
                "spoken_text": "Here is the code",
                "evidence_ids": ["ev_2"],
            },
        ],
    }

    evidence_pack = {
        "records": [
            {"id": "ev_1", "kind": "concept", "claim": "Welcome to testing", "excerpt": "Welcome to testing excerpt"},
            {"id": "ev_2", "kind": "code_evidence", "claim": "Here is the code", "excerpt": "def test(): pass"},
        ]
    }

    with open(run_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2)

    with open(run_dir / "evidence_pack.json", "w", encoding="utf-8") as f:
        json.dump(evidence_pack, f, indent=2)

    master_audio = run_dir / "audio.wav"
    master_audio.write_bytes(b"INITIAL_MASTER_AUDIO_V1")

    # Per scene initial audio
    (run_dir / "scenes" / "1").mkdir(parents=True)
    (run_dir / "scenes" / "2").mkdir(parents=True)
    (run_dir / "scenes" / "1" / "audio_v1.wav").write_bytes(b"SC1_AUDIO_V1")
    (run_dir / "scenes" / "2" / "audio_v1.wav").write_bytes(b"SC2_AUDIO_V1")

    # Initial manifest
    manifest = init_manifest(run_id, run_dir, data_payload["scenes"], fps=30)
    manifest["scenes"]["1"]["audio_file"] = "scenes/1/audio_v1.wav"
    manifest["scenes"]["2"]["audio_file"] = "scenes/2/audio_v1.wav"
    save_manifest(manifest, run_dir)

    # Initial output
    (run_dir / "output.mp4").write_bytes(b"INITIAL_OUTPUT_MP4_V1")

    # Snapshot rev_001
    archive_revision_snapshot(
        run_dir=run_dir,
        revision=1,
        data_payload=data_payload,
        manifest_data=manifest,
        output_mp4=run_dir / "output.mp4",
    )

    return run_id, run_dir, data_payload, manifest


# ---------------------------------------------------------------------------
# TASK 4: CONCURRENCY LOCK TESTS
# ---------------------------------------------------------------------------

def test_revision_lock_acquisition_and_release(tmp_path: Path):
    """Verifies that RevisionLock acquires lock and releases properly."""
    run_dir = tmp_path / "lock_test"
    run_dir.mkdir(parents=True)

    with RevisionLock(run_dir):
        # Inside lock
        assert (run_dir / ".revision.lock").exists()

    # After exit, acquiring again must succeed
    with RevisionLock(run_dir):
        assert (run_dir / ".revision.lock").exists()


def test_concurrent_revision_lock_rejects_second_operation(tmp_path: Path):
    """Verifies that an attempt to acquire an already-held lock raises RuntimeError."""
    run_dir = tmp_path / "lock_conflict_test"
    run_dir.mkdir(parents=True)

    lock1 = RevisionLock(run_dir)
    lock1.acquire()

    try:
        lock2 = RevisionLock(run_dir)
        with pytest.raises(RuntimeError) as exc_info:
            lock2.acquire()
        assert "is currently locked by another active process" in str(exc_info.value)
    finally:
        lock1.release()

    # Once lock1 is released, lock2 can acquire without error
    lock2.acquire()
    lock2.release()


# ---------------------------------------------------------------------------
# TASK 2: FAIL-CLOSED REVISION VALIDATION TESTS
# ---------------------------------------------------------------------------

def test_revision_fails_closed_on_evidence_validation_failure(sample_project, monkeypatch):
    """
    When validate_evidence_and_plan returns passed=False,
    execute_revision must abort with RuntimeError and leave data.json intact.
    """
    run_id, run_dir, initial_data, _ = sample_project

    # Patch RUNS_DIR in revise module
    monkeypatch.setattr("engine.revise.RUNS_DIR", run_dir.parent)

    mock_report = MagicMock()
    mock_report.passed = False
    mock_report.needs_review = False
    mock_report.checks = {"gate1_contiguous_code_equality": False}
    mock_report.model_dump.return_value = {"passed": False}

    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_report):
        with pytest.raises(RuntimeError) as exc_info:
            execute_revision(
                run_id=run_id,
                target_scene_id=1,
                set_title="Unbacked Title",
            )
        assert "Evidence validation gate failed for revision 2" in str(exc_info.value)

    # Verify data.json on disk was NOT modified
    with open(run_dir / "data.json", "r", encoding="utf-8") as f:
        current_data = json.load(f)
    assert current_data["scenes"][0]["title"] == "Scene 1 Hook"

    # Verify manifest was NOT updated to rev 2
    current_manifest = load_manifest(run_dir)
    assert current_manifest["revision"] == 1


def test_revision_fails_closed_on_evidence_needs_review(sample_project, monkeypatch):
    """
    When validate_evidence_and_plan returns needs_review=True,
    execute_revision must abort with RuntimeError without publishing.
    """
    run_id, run_dir, initial_data, _ = sample_project
    monkeypatch.setattr("engine.revise.RUNS_DIR", run_dir.parent)

    mock_report = MagicMock()
    mock_report.passed = True
    mock_report.needs_review = True
    mock_report.review_reasons = ["Ambiguous metric citation requires human review"]
    mock_report.model_dump.return_value = {"needs_review": True}

    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_report):
        with pytest.raises(RuntimeError) as exc_info:
            execute_revision(
                run_id=run_id,
                target_scene_id=1,
                set_title="Ambiguous Claim",
            )
        assert "requires human review for revision 2" in str(exc_info.value)

    # Verify data.json intact
    with open(run_dir / "data.json", "r", encoding="utf-8") as f:
        current_data = json.load(f)
    assert current_data["scenes"][0]["title"] == "Scene 1 Hook"


def test_revision_fails_closed_on_zod_timeline_validation_failure(sample_project, monkeypatch):
    """
    When Zod timeline validation fails (non-zero exit code),
    execute_revision must abort with RuntimeError and not render or commit.
    """
    run_id, run_dir, initial_data, _ = sample_project
    monkeypatch.setattr("engine.revise.RUNS_DIR", run_dir.parent)

    mock_evidence_report = MagicMock()
    mock_evidence_report.passed = True
    mock_evidence_report.needs_review = False
    mock_evidence_report.claim_coverage_pct = 100
    mock_evidence_report.model_dump.return_value = {"passed": True}

    mock_zod_proc = MagicMock()
    mock_zod_proc.returncode = 1
    mock_zod_proc.stderr = "ZodSchemaError: Invalid visual_type 'corrupt_type'"
    mock_zod_proc.stdout = ""

    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_evidence_report), \
         patch("subprocess.run", return_value=mock_zod_proc), \
         patch("engine.revise.render_dirty_segments") as mock_render:

        with pytest.raises(RuntimeError) as exc_info:
            execute_revision(
                run_id=run_id,
                target_scene_id=1,
                set_visual_type="corrupt_type",
            )
        assert "Timeline schema validation (Zod) failed" in str(exc_info.value)
        # Remotion rendering must never have been called!
        mock_render.assert_not_called()

    # Verify data.json intact
    with open(run_dir / "data.json", "r", encoding="utf-8") as f:
        current_data = json.load(f)
    assert current_data["scenes"][0]["visual_type"] == "hook"


def test_revision_fails_closed_on_render_failure(sample_project, monkeypatch):
    """
    When render_dirty_segments fails, execute_revision must abort
    without overwriting data.json or manifest.json.
    """
    run_id, run_dir, initial_data, _ = sample_project
    monkeypatch.setattr("engine.revise.RUNS_DIR", run_dir.parent)

    mock_evidence_report = MagicMock()
    mock_evidence_report.passed = True
    mock_evidence_report.needs_review = False
    mock_evidence_report.claim_coverage_pct = 100
    mock_evidence_report.model_dump.return_value = {"passed": True}

    mock_zod_proc = MagicMock()
    mock_zod_proc.returncode = 0
    mock_zod_proc.stderr = ""
    mock_zod_proc.stdout = "OK"

    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_evidence_report), \
         patch("subprocess.run", return_value=mock_zod_proc), \
         patch("engine.revise.render_dirty_segments", return_value=False):

        with pytest.raises(RuntimeError) as exc_info:
            execute_revision(
                run_id=run_id,
                target_scene_id=1,
                set_title="New Valid Title",
            )
        assert "Failed to render segments" in str(exc_info.value)

    # Verify data.json intact
    with open(run_dir / "data.json", "r", encoding="utf-8") as f:
        current_data = json.load(f)
    assert current_data["scenes"][0]["title"] == "Scene 1 Hook"

    # Verify manifest intact
    current_manifest = load_manifest(run_dir)
    assert current_manifest["revision"] == 1


# ---------------------------------------------------------------------------
# TASK 3: REVISION CONSISTENCY & ARTIFACT PRESERVATION
# ---------------------------------------------------------------------------

def test_repeated_narration_revisions_preserve_earlier_scene_audio(sample_project, monkeypatch):
    """
    Tests that:
    1. Narration revision of Scene 2 updates manifest audio_file to audio_v2.wav.
    2. Subsequent visual or narration revision of Scene 1 does NOT revert Scene 2 audio_file.
    """
    run_id, run_dir, initial_data, _ = sample_project
    monkeypatch.setattr("engine.revise.RUNS_DIR", run_dir.parent)

    mock_evidence_report = MagicMock()
    mock_evidence_report.passed = True
    mock_evidence_report.needs_review = False
    mock_evidence_report.claim_coverage_pct = 100
    mock_evidence_report.model_dump.return_value = {"passed": True}

    mock_zod_proc = MagicMock()
    mock_zod_proc.returncode = 0
    mock_zod_proc.stderr = ""
    mock_zod_proc.stdout = "OK"

    def mock_synth(narration_text, scene_dir, revision, voice_id="en-US-ChristopherNeural"):
        p = scene_dir / f"audio_v{revision}.wav"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(f"SYNTH_AUDIO_V{revision}".encode())
        return p, 2.0, [{"word": "Test", "start": 0.0, "end": 0.5}]

    def mock_concat(scene_items, output_master_audio):
        output_master_audio.parent.mkdir(parents=True, exist_ok=True)
        output_master_audio.write_bytes(b"CONCAT_MASTER_AUDIO")
        scenes_meta = []
        cur_t = 0.0
        for item in scene_items:
            dur = item["duration"]
            scenes_meta.append({"start_time": cur_t, "end_time": cur_t + dur, "duration": dur})
            cur_t += dur
        return scenes_meta, [{"word": "word", "start": 0.0, "end": 1.0}]

    def mock_stitch(segment_paths, output_video_path, master_audio_path=None, scenes_meta=None):
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        output_video_path.write_bytes(b"STITCHED_VIDEO_MP4")
        return True

    # Revision 1 -> 2: Revise Narration on Scene 2
    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_evidence_report), \
         patch("subprocess.run", return_value=mock_zod_proc), \
         patch("engine.revise.synthesize_scene_audio", side_effect=mock_synth), \
         patch("engine.revise.concatenate_scene_audios", side_effect=mock_concat), \
         patch("engine.revise.render_dirty_segments", return_value=True), \
         patch("engine.revise.stitch_segments", side_effect=mock_stitch), \
         patch("engine.revise.validate_post_render_qa", return_value=(True, [], {})):

        execute_revision(
            run_id=run_id,
            target_scene_id=2,
            set_narration="Updated Scene 2 Narration Text",
        )

    # Inspect manifest after revision 2
    m2 = load_manifest(run_dir)
    assert m2["revision"] == 2
    sc2_audio = m2["scenes"]["2"]["audio_file"]
    assert sc2_audio == "scenes/2/audio_v2.wav", f"Scene 2 audio_file should be audio_v2.wav, got: {sc2_audio}"

    # Revision 2 -> 3: Revise Visual on Scene 1
    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_evidence_report), \
         patch("subprocess.run", return_value=mock_zod_proc), \
         patch("engine.revise.synthesize_scene_audio", side_effect=mock_synth), \
         patch("engine.revise.concatenate_scene_audios", side_effect=mock_concat), \
         patch("engine.revise.render_dirty_segments", return_value=True), \
         patch("engine.revise.stitch_segments", side_effect=mock_stitch), \
         patch("engine.revise.validate_post_render_qa", return_value=(True, [], {})):

        execute_revision(
            run_id=run_id,
            target_scene_id=1,
            set_title="Revised Scene 1 Title",
        )

    # Inspect manifest after revision 3
    m3 = load_manifest(run_dir)
    assert m3["revision"] == 3
    # Scene 2 audio_file must NOT have reverted to audio_v1!
    sc2_audio_rev3 = m3["scenes"]["2"]["audio_file"]
    assert sc2_audio_rev3 == "scenes/2/audio_v2.wav", f"Scene 2 audio_file reverted to: {sc2_audio_rev3}"


def test_snapshot_restoration_restores_consistent_state(sample_project):
    """
    Tests that restore_revision_snapshot restores timeline data, manifest,
    master audio, and video consistently, archiving previous active state.
    """
    run_id, run_dir, initial_data, _ = sample_project

    # Step 1: Simulate that active state was mutated in revision 2
    active_data = copy.deepcopy(initial_data)
    active_data["scenes"][0]["title"] = "Modified in Rev 2"
    with open(run_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(active_data, f, indent=2)

    # Active audio in rev 2
    (run_dir / "audio.wav").write_bytes(b"REV_2_ACTIVE_AUDIO")
    (run_dir / "output.mp4").write_bytes(b"REV_2_ACTIVE_OUTPUT")

    m = load_manifest(run_dir)
    m["revision"] = 2
    save_manifest(m, run_dir)

    # Step 2: Restore snapshot rev_001
    res = restore_revision_snapshot(run_dir, target_revision=1)

    assert res["revision"] == 3
    assert res["restored_from"] == 1

    # Verify rev_002 was preserved before rollback
    rev2_dir = run_dir / "revisions" / "rev_002"
    assert rev2_dir.exists(), "Previous active state must be non-destructively snapshotted!"
    assert (rev2_dir / "audio.wav").read_bytes() == b"REV_2_ACTIVE_AUDIO"

    # Verify active state reverted to rev_001 content
    with open(run_dir / "data.json", "r", encoding="utf-8") as f:
        restored_data = json.load(f)
    assert restored_data["scenes"][0]["title"] == "Scene 1 Hook"

    # Verify active master audio restored to rev_001 audio
    assert (run_dir / "audio.wav").read_bytes() == b"INITIAL_MASTER_AUDIO_V1"
    assert (run_dir / "output.mp4").read_bytes() == b"INITIAL_OUTPUT_MP4_V1"

    # Verify rev_003 snapshot was created for restored state
    rev3_dir = run_dir / "revisions" / "rev_003"
    assert rev3_dir.exists()
    assert (rev3_dir / "audio.wav").read_bytes() == b"INITIAL_MASTER_AUDIO_V1"

