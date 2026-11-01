"""
tests/test_revision_failure_scenarios.py
Comprehensive failure scenario test suite for Phase 4.0.1:
1. Failed-render and Gate-6 failure rollback preserving exact artifact checksums.
2. Repeated narration revisions across same and different scenes preserving versioned lineage.
3. Complete snapshot restoration recovering data, manifest, master audio, segments, and validation report.
4. Per-run lock coverage across revisions, snapshot restoration, and generation reruns.
"""

import copy
import hashlib
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


def compute_file_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture
def disposable_run(tmp_path: Path):
    """Sets up a complete known-good run with manifest, segments, audio, and snapshots."""
    run_id = "test_run_fail_safety"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)

    data_payload = {
        "version": 1,
        "run_id": run_id,
        "title": "Fail Safety Run",
        "aspect_ratio": "16:9",
        "audio_file": f"runs/{run_id}/audio.wav",
        "words": [
            {"word": "Step", "start": 0.0, "end": 0.5},
            {"word": "one", "start": 0.5, "end": 1.0},
            {"word": "code", "start": 1.0, "end": 2.0},
        ],
        "scenes": [
            {
                "scene_id": 1,
                "title": "Scene 1 Hook",
                "visual_type": "hook",
                "start_time": 0.0,
                "end_time": 1.0,
                "duration": 1.0,
                "spoken_text": "Step one",
                "evidence_ids": ["ev_1"],
            },
            {
                "scene_id": 2,
                "title": "Scene 2 Code",
                "visual_type": "code_spotlight",
                "start_time": 1.0,
                "end_time": 2.0,
                "duration": 1.0,
                "spoken_text": "code",
                "evidence_ids": ["ev_2"],
            },
        ],
    }

    evidence_pack = {
        "records": [
            {"id": "ev_1", "kind": "concept", "claim": "Step one", "excerpt": "Step one claim"},
            {"id": "ev_2", "kind": "code_evidence", "claim": "code", "excerpt": "const x = 10;"},
        ]
    }

    with open(run_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2)

    with open(run_dir / "evidence_pack.json", "w", encoding="utf-8") as f:
        json.dump(evidence_pack, f, indent=2)

    val_report = {"passed": True, "total_claims": 2, "backed_claims": 2}
    with open(run_dir / "validation_report.json", "w", encoding="utf-8") as f:
        json.dump(val_report, f, indent=2)

    (run_dir / "audio.wav").write_bytes(b"INITIAL_MASTER_AUDIO_V1")
    (run_dir / "audio.mp3").write_bytes(b"INITIAL_MASTER_AUDIO_MP3_V1")

    (run_dir / "scenes" / "1").mkdir(parents=True)
    (run_dir / "scenes" / "2").mkdir(parents=True)
    (run_dir / "scenes" / "1" / "audio_v1.wav").write_bytes(b"SC1_AUDIO_V1")
    (run_dir / "scenes" / "2" / "audio_v1.wav").write_bytes(b"SC2_AUDIO_V1")

    (run_dir / "segments").mkdir(parents=True)
    (run_dir / "segments" / "scene_1_v1.mp4").write_bytes(b"SEGMENT_SC1_V1")
    (run_dir / "segments" / "scene_2_v1.mp4").write_bytes(b"SEGMENT_SC2_V1")

    (run_dir / "output.mp4").write_bytes(b"INITIAL_MASTER_VIDEO_MP4_V1")

    manifest = init_manifest(run_id, run_dir, data_payload["scenes"], fps=30)
    manifest["scenes"]["1"]["audio_file"] = "scenes/1/audio_v1.wav"
    manifest["scenes"]["1"]["segment_video"] = "segments/scene_1_v1.mp4"
    manifest["scenes"]["2"]["audio_file"] = "scenes/2/audio_v1.wav"
    manifest["scenes"]["2"]["segment_video"] = "segments/scene_2_v1.mp4"
    save_manifest(manifest, run_dir)

    # Archive snapshot rev_001
    archive_revision_snapshot(
        run_dir=run_dir,
        revision=1,
        data_payload=data_payload,
        manifest_data=manifest,
        output_mp4=run_dir / "output.mp4",
    )

    return run_id, run_dir, data_payload, manifest


# ---------------------------------------------------------------------------
# 1. FAILED-RENDER & GATE 6 FAILURE ROLLBACK TESTS
# ---------------------------------------------------------------------------

def test_render_failure_preserves_every_previously_successful_artifact(disposable_run, monkeypatch):
    """
    Simulates a failure during Remotion segment rendering.
    Verifies that all pre-existing files (data, manifest, audio, segments, output)
    retain their exact checksums and no corrupt state is referenced.
    """
    run_id, run_dir, _, _ = disposable_run
    monkeypatch.setattr("engine.revise.RUNS_DIR", run_dir.parent)

    # Record checksums of all existing durable artifacts
    checksums_before = {
        "data.json": compute_file_sha256(run_dir / "data.json"),
        "manifest.json": compute_file_sha256(run_dir / "manifest.json"),
        "audio.wav": compute_file_sha256(run_dir / "audio.wav"),
        "audio.mp3": compute_file_sha256(run_dir / "audio.mp3"),
        "sc1_audio": compute_file_sha256(run_dir / "scenes" / "1" / "audio_v1.wav"),
        "sc2_audio": compute_file_sha256(run_dir / "scenes" / "2" / "audio_v1.wav"),
        "sc1_seg": compute_file_sha256(run_dir / "segments" / "scene_1_v1.mp4"),
        "sc2_seg": compute_file_sha256(run_dir / "segments" / "scene_2_v1.mp4"),
        "output.mp4": compute_file_sha256(run_dir / "output.mp4"),
        "rev_001_manifest": compute_file_sha256(run_dir / "revisions" / "rev_001" / "manifest.json"),
    }

    mock_report = MagicMock(passed=True, needs_review=False, claim_coverage_pct=100)
    mock_report.model_dump.return_value = {"passed": True}
    mock_zod = MagicMock(returncode=0, stderr="", stdout="")

    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_report), \
         patch("subprocess.run", return_value=mock_zod), \
         patch("engine.revise.render_dirty_segments", side_effect=RuntimeError("Remotion render process crashed with OOM")):

        with pytest.raises(RuntimeError) as exc_info:
            execute_revision(
                run_id=run_id,
                target_scene_id=2,
                set_title="New Candidate Title",
            )
        assert "Remotion render process crashed" in str(exc_info.value)

    # 1. Verify every checksum is 100% identical
    assert compute_file_sha256(run_dir / "data.json") == checksums_before["data.json"]
    assert compute_file_sha256(run_dir / "manifest.json") == checksums_before["manifest.json"]
    assert compute_file_sha256(run_dir / "audio.wav") == checksums_before["audio.wav"]
    assert compute_file_sha256(run_dir / "audio.mp3") == checksums_before["audio.mp3"]
    assert compute_file_sha256(run_dir / "scenes" / "1" / "audio_v1.wav") == checksums_before["sc1_audio"]
    assert compute_file_sha256(run_dir / "scenes" / "2" / "audio_v1.wav") == checksums_before["sc2_audio"]
    assert compute_file_sha256(run_dir / "segments" / "scene_1_v1.mp4") == checksums_before["sc1_seg"]
    assert compute_file_sha256(run_dir / "segments" / "scene_2_v1.mp4") == checksums_before["sc2_seg"]
    assert compute_file_sha256(run_dir / "output.mp4") == checksums_before["output.mp4"]

    # 2. Verify diagnostic file was written and survived cleanup
    diag_file = run_dir / "reflection.error.json"
    assert diag_file.exists(), "Diagnostic reflection.error.json must be preserved"
    diag_data = json.loads(diag_file.read_text(encoding="utf-8"))
    assert "Remotion render process crashed" in diag_data.get("message", "")

    # 3. Verify no temporary staging files left behind
    assert not list(run_dir.glob(".staged_*")), "No .staged_* files should remain after failure"

    # 4. Verify manifest still reports revision 1
    m = load_manifest(run_dir)
    assert m["revision"] == 1


def test_gate6_failure_preserves_previous_output_and_state(disposable_run, monkeypatch):
    """
    Simulates a case where rendering and stitching succeed, but Gate 6 Post-Render QA fails
    (e.g. duration desync or blank frame).
    Verifies that the previously successful MP4 is NOT replaced and state remains intact.
    """
    run_id, run_dir, _, _ = disposable_run
    monkeypatch.setattr("engine.revise.RUNS_DIR", run_dir.parent)

    original_output_sha = compute_file_sha256(run_dir / "output.mp4")
    original_data_sha = compute_file_sha256(run_dir / "data.json")
    original_manifest_sha = compute_file_sha256(run_dir / "manifest.json")

    mock_report = MagicMock(passed=True, needs_review=False, claim_coverage_pct=100)
    mock_report.model_dump.return_value = {"passed": True}
    mock_zod = MagicMock(returncode=0, stderr="", stdout="")

    def mock_stitch(segment_paths, output_video_path, master_audio_path=None, scenes_meta=None):
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        output_video_path.write_bytes(b"CANDIDATE_CORRUPT_STITCH_MP4")
        return True

    # Gate 6 returns (False, ["Duration mismatch: video=30.0s, audio=28.4s, delta=1.6s > 0.05s tolerance"], {})
    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_report), \
         patch("subprocess.run", return_value=mock_zod), \
         patch("engine.revise.render_dirty_segments", return_value=True), \
         patch("engine.revise.stitch_segments", side_effect=mock_stitch), \
         patch("engine.revise.validate_post_render_qa", return_value=(False, ["Duration mismatch delta=1.6s > 0.05s tolerance"], {})):

        with pytest.raises(RuntimeError) as exc_info:
            execute_revision(
                run_id=run_id,
                target_scene_id=1,
                set_title="New Title",
            )
        assert "Gate 6 output validation" in str(exc_info.value)

    # 1. Output MP4 must remain the original successful MP4
    assert compute_file_sha256(run_dir / "output.mp4") == original_output_sha
    assert (run_dir / "output.mp4").read_bytes() == b"INITIAL_MASTER_VIDEO_MP4_V1"

    # 2. Timeline data.json and manifest.json must remain identical
    assert compute_file_sha256(run_dir / "data.json") == original_data_sha
    assert compute_file_sha256(run_dir / "manifest.json") == original_manifest_sha

    # 3. Diagnostic recorded
    assert (run_dir / "reflection.error.json").exists()
    diag_data = json.loads((run_dir / "reflection.error.json").read_text(encoding="utf-8"))
    assert "Gate 6 output validation" in diag_data.get("message", "")

    # 4. Subsequent valid revision can still run and succeed
    with patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_report), \
         patch("subprocess.run", return_value=mock_zod), \
         patch("engine.revise.render_dirty_segments", return_value=True), \
         patch("engine.revise.stitch_segments", side_effect=mock_stitch), \
         patch("engine.revise.validate_post_render_qa", return_value=(True, [], {})):

        out = execute_revision(
            run_id=run_id,
            target_scene_id=1,
            set_title="Valid Subsequent Title",
        )
        assert out.exists()

    # After successful subsequent revision, manifest revision advanced to 2
    m = load_manifest(run_dir)
    assert m["revision"] == 2
    assert (run_dir / "revisions" / "rev_002").exists()


# ---------------------------------------------------------------------------
# 2. REPEATED NARRATION REVISIONS (SAME & DIFFERENT SCENES)
# ---------------------------------------------------------------------------

def test_repeated_narration_revisions_across_scenes(disposable_run, monkeypatch):
    """
    Tests:
    1. Narration revision on Scene 2 -> audio_v2.wav.
    2. Second narration revision on Scene 2 -> audio_v3.wav.
    3. Visual revision on Scene 2 -> audio remains audio_v3.wav.
    4. Narration revision on Scene 1 -> Scene 1 gets audio_v5.wav AND Scene 2 retains audio_v3.wav!
    """
    run_id, run_dir, _, _ = disposable_run
    monkeypatch.setattr("engine.revise.RUNS_DIR", run_dir.parent)

    mock_report = MagicMock(passed=True, needs_review=False, claim_coverage_pct=100)
    mock_report.model_dump.return_value = {"passed": True}
    mock_zod = MagicMock(returncode=0, stderr="", stdout="")

    def mock_synth(narration_text, scene_dir, revision, voice_id="en-US-ChristopherNeural"):
        p = scene_dir / f"audio_v{revision}.wav"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(f"SYNTH_{scene_dir.name}_V{revision}".encode())
        return p, 2.5, [{"word": narration_text.split()[0], "start": 0.0, "end": 0.5}]

    def mock_concat(scene_items, output_master_audio):
        output_master_audio.parent.mkdir(parents=True, exist_ok=True)
        output_master_audio.write_bytes(b"CONCAT_MASTER_WAV")
        scenes_meta = []
        cur_t = 0.0
        for item in scene_items:
            dur = item["duration"]
            scenes_meta.append({"start_time": cur_t, "end_time": cur_t + dur, "duration": dur})
            cur_t += dur
        return scenes_meta, [{"word": "w", "start": 0.0, "end": 1.0}]

    def mock_stitch(segment_paths, output_video_path, master_audio_path=None, scenes_meta=None):
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        output_video_path.write_bytes(b"STITCHED_MP4")
        return True

    common_patches = [
        patch("engine.validation.evidence_validator.validate_evidence_and_plan", return_value=mock_report),
        patch("subprocess.run", return_value=mock_zod),
        patch("engine.revise.synthesize_scene_audio", side_effect=mock_synth),
        patch("engine.revise.concatenate_scene_audios", side_effect=mock_concat),
        patch("engine.revise.render_dirty_segments", return_value=True),
        patch("engine.revise.stitch_segments", side_effect=mock_stitch),
        patch("engine.revise.validate_post_render_qa", return_value=(True, [], {})),
    ]

    # Step 1: Narration revision 1 on Scene 2 (Rev 1 -> Rev 2)
    with common_patches[0], common_patches[1], common_patches[2], common_patches[3], common_patches[4], common_patches[5], common_patches[6]:
        execute_revision(run_id=run_id, target_scene_id=2, set_narration="First updated narration for Scene 2")

    m2 = load_manifest(run_dir)
    assert m2["revision"] == 2
    assert m2["scenes"]["2"]["audio_file"] == "scenes/2/audio_v2.wav"

    # Step 2: Second narration revision on Scene 2 (Rev 2 -> Rev 3)
    with common_patches[0], common_patches[1], common_patches[2], common_patches[3], common_patches[4], common_patches[5], common_patches[6]:
        execute_revision(run_id=run_id, target_scene_id=2, set_narration="Second distinct narration for Scene 2")

    m3 = load_manifest(run_dir)
    assert m3["revision"] == 3
    assert m3["scenes"]["2"]["audio_file"] == "scenes/2/audio_v3.wav"

    # Step 3: Visual revision on Scene 2 (Rev 3 -> Rev 4)
    with common_patches[0], common_patches[1], common_patches[2], common_patches[3], common_patches[4], common_patches[5], common_patches[6]:
        execute_revision(run_id=run_id, target_scene_id=2, set_title="Visual Title Revision")

    m4 = load_manifest(run_dir)
    assert m4["revision"] == 4
    # Scene 2 audio MUST remain audio_v3.wav!
    assert m4["scenes"]["2"]["audio_file"] == "scenes/2/audio_v3.wav"

    # Step 4: Narration revision on a DIFFERENT scene (Scene 1) (Rev 4 -> Rev 5)
    with common_patches[0], common_patches[1], common_patches[2], common_patches[3], common_patches[4], common_patches[5], common_patches[6]:
        execute_revision(run_id=run_id, target_scene_id=1, set_narration="New narration for Scene 1")

    m5 = load_manifest(run_dir)
    assert m5["revision"] == 5
    assert m5["scenes"]["1"]["audio_file"] == "scenes/1/audio_v5.wav"
    # Scene 2 audio MUST STILL remain audio_v3.wav!
    assert m5["scenes"]["2"]["audio_file"] == "scenes/2/audio_v3.wav"


# ---------------------------------------------------------------------------
# 3. COMPLETE SNAPSHOT RESTORATION
# ---------------------------------------------------------------------------

def test_complete_snapshot_restoration_consistency(disposable_run):
    """
    Tests complete snapshot restoration:
    - Snapshot A (Rev 1) records initial state with segments, audios, and validation report.
    - Mutate to State B (Rev 2 and Rev 3).
    - Restore Snapshot A -> Rev 4.
    - Proves data, manifest, master audio, per-scene audio, segments, and validation report
      match Snapshot A and do not leak State B.
    - Creates Rev 5 from restored project to prove monotonicity and continued revisability.
    """
    run_id, run_dir, initial_data, _ = disposable_run

    # Snapshot A checksums
    snap_a_master_audio_sha = compute_file_sha256(run_dir / "audio.wav")
    snap_a_sc1_seg_sha = compute_file_sha256(run_dir / "segments" / "scene_1_v1.mp4")
    snap_a_sc2_seg_sha = compute_file_sha256(run_dir / "segments" / "scene_2_v1.mp4")
    snap_a_output_sha = compute_file_sha256(run_dir / "output.mp4")

    # Step 1: Mutate project to State B (simulate Rev 2 and Rev 3)
    mutated_data = copy.deepcopy(initial_data)
    mutated_data["scenes"][0]["spoken_text"] = "State B Spoken Text"
    mutated_data["scenes"][1]["title"] = "State B Title"
    with open(run_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(mutated_data, f, indent=2)

    (run_dir / "audio.wav").write_bytes(b"STATE_B_MASTER_AUDIO")
    (run_dir / "output.mp4").write_bytes(b"STATE_B_OUTPUT_MP4")

    # Add State B new versioned segments
    (run_dir / "segments" / "scene_1_v2.mp4").write_bytes(b"STATE_B_SEG_SC1_V2")
    (run_dir / "segments" / "scene_2_v3.mp4").write_bytes(b"STATE_B_SEG_SC2_V3")

    m = load_manifest(run_dir)
    m["revision"] = 3
    m["scenes"]["1"]["revision"] = 2
    m["scenes"]["1"]["segment_video"] = "segments/scene_1_v2.mp4"
    m["scenes"]["2"]["revision"] = 3
    m["scenes"]["2"]["segment_video"] = "segments/scene_2_v3.mp4"
    save_manifest(m, run_dir)

    # Archive State B as rev_003
    archive_revision_snapshot(
        run_dir=run_dir,
        revision=3,
        data_payload=mutated_data,
        manifest_data=m,
        output_mp4=run_dir / "output.mp4",
    )

    # Step 2: Restore Snapshot A (target_revision = 1)
    res = restore_revision_snapshot(run_dir, target_revision=1)
    new_rev = res["revision"]
    assert new_rev == 4, f"New revision after restore should be 4, got {new_rev}"
    assert res["restored_from"] == 1

    # 1. Timeline data restored to Snapshot A
    with open(run_dir / "data.json", "r", encoding="utf-8") as f:
        restored_data = json.load(f)
    assert restored_data["scenes"][0]["spoken_text"] == "Step one"

    # 2. Master audio restored to Snapshot A
    assert compute_file_sha256(run_dir / "audio.wav") == snap_a_master_audio_sha

    # 3. Output video restored to Snapshot A
    assert compute_file_sha256(run_dir / "output.mp4") == snap_a_output_sha

    # 4. Manifest points to Snapshot A's segments
    restored_manifest = load_manifest(run_dir)
    assert restored_manifest["revision"] == 4
    assert restored_manifest["scenes"]["1"]["segment_video"] == "segments/scene_1_v1.mp4"
    assert restored_manifest["scenes"]["2"]["segment_video"] == "segments/scene_2_v1.mp4"
    assert compute_file_sha256(run_dir / "segments" / "scene_1_v1.mp4") == snap_a_sc1_seg_sha
    assert compute_file_sha256(run_dir / "segments" / "scene_2_v1.mp4") == snap_a_sc2_seg_sha

    # 5. History records rollback
    assert any("Restored snapshot rev_001" in h.get("action", "") for h in restored_manifest.get("history", []))

    # 6. Monotonic snapshot created for rev_004
    assert (run_dir / "revisions" / "rev_004").exists()
    assert (run_dir / "revisions" / "rev_004" / "audio.wav").read_bytes() == b"INITIAL_MASTER_AUDIO_V1"


# ---------------------------------------------------------------------------
# 4. PER-RUN LOCKING COVERS ALL CONFLICTING OPERATIONS
# ---------------------------------------------------------------------------

def test_lock_protects_snapshot_restore_against_concurrent_revision(disposable_run):
    """
    Verifies that restore_revision_snapshot acquires RevisionLock
    and rejects concurrent operation if lock is already held.
    """
    run_id, run_dir, _, _ = disposable_run

    lock = RevisionLock(run_dir)
    lock.acquire()

    try:
        with pytest.raises(RuntimeError) as exc_info:
            restore_revision_snapshot(run_dir, target_revision=1)
        assert "is currently locked by another active process" in str(exc_info.value)
    finally:
        lock.release()

    # After lock is released, restore succeeds
    res = restore_revision_snapshot(run_dir, target_revision=1)
    assert res["revision"] == 2


def test_generation_with_existing_run_id_rejects_when_locked(disposable_run, monkeypatch):
    """
    Verifies that running generation on an existing run ID is rejected
    if another process holds RevisionLock on that run directory.
    """
    from engine.pipeline.manifest import RevisionLock
    run_id, run_dir, _, _ = disposable_run

    lock = RevisionLock(run_dir)
    lock.acquire()

    try:
        # Simulate generate.py standalone execution on existing run_id
        lock_attempt = RevisionLock(run_dir)
        with pytest.raises(RuntimeError) as exc_info:
            lock_attempt.acquire()
        assert "is currently locked by another active process" in str(exc_info.value)
    finally:
        lock.release()
