"""
tests/test_run_data_loss_prevention.py
Regression tests for Phase 4.0 Task 1:
Guarantees non-destructive error handling, diagnostic preservation, and prevention of run data loss.
"""

import json
from pathlib import Path
import pytest
from engine.generate import cleanup_run_artifacts
from engine.validation.reflection import write_reflection_error


def test_cleanup_run_artifacts_preserves_durable_files(tmp_path: Path):
    """
    Verifies cleanup_run_artifacts removes only transient scratch files
    and preserves durable project state, diagnostics, audio, revisions, and outputs.
    """
    run_dir = tmp_path / "run_test_preserve"
    run_dir.mkdir(parents=True)

    # Durable artifacts
    manifest_file = run_dir / "manifest.json"
    manifest_file.write_text(json.dumps({"revision": 2, "scenes": {}}), encoding="utf-8")

    data_file = run_dir / "data.json"
    data_file.write_text(json.dumps({"run_id": "test", "scenes": []}), encoding="utf-8")

    audio_file = run_dir / "audio.wav"
    audio_file.write_bytes(b"RIFF_SENTINEL_AUDIO_DATA_12345")

    rev_dir = run_dir / "revisions" / "rev_001"
    rev_dir.mkdir(parents=True)
    rev_data = rev_dir / "data.json"
    rev_data.write_text("rev_1_data", encoding="utf-8")

    out_file = run_dir / "output.mp4"
    out_file.write_bytes(b"MP4_SENTINEL_VIDEO_DATA_67890")

    # Diagnostic files
    write_reflection_error(run_dir, stage="TEST_STAGE", message="Diagnostic error occurred.")
    refl_file = run_dir / "reflection.error.json"
    assert refl_file.exists(), "reflection.error.json should exist"

    val_err_file = run_dir / "validation.error.json"
    val_err_file.write_text(json.dumps({"stage": "zod", "error": "schema_error"}), encoding="utf-8")

    # Transient scratch files
    tmp_scratch1 = run_dir / "candidate.tmp"
    tmp_scratch1.write_text("scratch", encoding="utf-8")
    tmp_scratch2 = run_dir / ".staged_data.json"
    tmp_scratch2.write_text("staging", encoding="utf-8")
    partial_scratch = run_dir / "render.partial"
    partial_scratch.write_text("partial", encoding="utf-8")

    # Execute cleanup
    cleanup_run_artifacts(run_dir)

    # Assert run directory itself still exists
    assert run_dir.exists(), "run_dir itself must never be deleted"

    # Assert diagnostic files preserved
    assert refl_file.exists(), "reflection.error.json must not be deleted on failure cleanup"
    refl_content = json.loads(refl_file.read_text(encoding="utf-8"))
    assert refl_content.get("message") == "Diagnostic error occurred."
    assert val_err_file.exists(), "validation.error.json must not be deleted on failure cleanup"

    # Assert durable files intact
    assert manifest_file.exists() and "revision" in manifest_file.read_text(encoding="utf-8")
    assert data_file.exists() and "run_id" in data_file.read_text(encoding="utf-8")
    assert audio_file.exists() and audio_file.read_bytes() == b"RIFF_SENTINEL_AUDIO_DATA_12345"
    assert rev_data.exists() and rev_data.read_text(encoding="utf-8") == "rev_1_data"
    assert out_file.exists() and out_file.read_bytes() == b"MP4_SENTINEL_VIDEO_DATA_67890"

    # Assert transient files are removed
    assert not tmp_scratch1.exists(), "*.tmp files should be cleaned up"
    assert not tmp_scratch2.exists(), ".staged_* files should be cleaned up"
    assert not partial_scratch.exists(), "*.partial files should be cleaned up"


def test_generation_exception_handler_preserves_existing_run_dir(tmp_path: Path):
    """
    Simulates generation failure and ensures diagnostic is written without wiping run_dir.
    """
    run_dir = tmp_path / "run_existing"
    run_dir.mkdir(parents=True)

    sentinel_manifest = run_dir / "manifest.json"
    sentinel_manifest.write_text('{"status": "pre-existing"}', encoding="utf-8")

    sentinel_audio = run_dir / "audio.wav"
    sentinel_audio.write_bytes(b"DO_NOT_DELETE")

    # Simulate exception handling block from engine/generate.py:915-918
    exc = RuntimeError("Simulated stage error in timeline generation")
    write_reflection_error(run_dir, stage="GENERATION", message=str(exc))
    cleanup_run_artifacts(run_dir)

    assert run_dir.exists(), "Pre-existing run_dir must survive generation exception"
    assert sentinel_manifest.exists(), "Pre-existing manifest must survive"
    assert sentinel_audio.exists(), "Pre-existing audio must survive"
    assert (run_dir / "reflection.error.json").exists(), "reflection.error.json must be preserved for inspection"
