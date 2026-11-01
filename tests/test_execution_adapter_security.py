"""tests/test_execution_adapter_security.py

Tests ControlledExecutionAdapter and security isolation guarantees.
- Asserts that live execution is disabled without verified OS-level container isolation.
- Negative tests: calling execute_command raises SecurityIsolationError.
- Verifies deterministic fixture artifact recording, hash binding, and preview capping.
"""

from pathlib import Path
import pytest

from engine.ingestion.execution_adapter import (
    ControlledExecutionAdapter,
    SecurityIsolationError,
    check_environment_isolation,
)

REPO_DIR = Path(__file__).resolve().parent.parent


def test_environment_isolation_check():
    is_isolated, reason = check_environment_isolation()
    # On standard host environment, isolation must be detected as False
    assert is_isolated is False
    assert "Live execution is disabled by security policy" in reason


def test_live_execution_blocked_by_default():
    adapter = ControlledExecutionAdapter(run_id="run_sec_test_001")
    is_safe, reason = adapter.is_live_execution_available()
    assert is_safe is False

    with pytest.raises(SecurityIsolationError) as exc_info:
        adapter.execute_command(
            command=["node", "-e", "console.log('pwned')"],
            source_code="console.log('pwned')",
        )
    assert "Execution Blocked" in str(exc_info.value)


def test_live_execution_blocked_even_if_flag_passed_without_os_sandbox():
    adapter = ControlledExecutionAdapter(run_id="run_sec_test_002", live_execution_enabled=True)
    # Even if caller attempts live_execution_enabled=True, check_environment_isolation blocks it
    is_safe, reason = adapter.is_live_execution_available()
    assert is_safe is False
    assert "lacks verified rootless sandbox isolation" in reason

    with pytest.raises(SecurityIsolationError) as exc_info:
        adapter.execute_command(
            command=["sh", "-c", "env"],
            source_code="env",
        )
    assert "Execution Blocked" in str(exc_info.value)


def test_deterministic_fixture_recording_and_hashing(tmp_path):
    adapter = ControlledExecutionAdapter(run_id="run_fixture_001")
    cmd = ["node", "test_idempotency.js"]
    source = "const stripe = require('stripe'); stripe.paymentIntents.create({...});"
    stdout = "HTTP/1.1 200 OK\nIdempotency-Key: test_key\nStatus: succeeded"
    stderr = ""

    artifact = adapter.record_fixture_artifact(
        artifact_id="exec_art_fixture_01",
        command=cmd,
        exit_code=0,
        stdout=stdout,
        stderr=stderr,
        source_text=source,
        tool_versions={"node": "20.20.2", "npm": "10.8.2"},
        output_dir=tmp_path,
    )

    assert artifact.artifact_id == "exec_art_fixture_01"
    assert artifact.exit_code == 0
    assert artifact.provenance == "prerecorded_fixture"
    assert artifact.is_fixture is True
    assert artifact.environment_meta["execution_type"] == "prerecorded_fixture"
    assert artifact.environment_meta["isolation_verified"] is False
    assert len(artifact.source_hash) == 64
    assert len(artifact.artifact_hash) == 64
    assert artifact.stdout_ref is not None
    assert Path(artifact.stdout_ref).exists()
    assert Path(artifact.stdout_ref).read_text(encoding="utf-8") == stdout


def test_stdout_preview_bounding():
    adapter = ControlledExecutionAdapter(run_id="run_fixture_002")
    huge_stdout = "x" * 10000  # 10KB
    artifact = adapter.record_fixture_artifact(
        artifact_id="exec_art_huge",
        command=["cat", "huge.txt"],
        exit_code=0,
        stdout=huge_stdout,
        stderr="",
        source_text="huge data",
    )
    # Preview must be capped at 4096 bytes
    assert len(artifact.stdout_preview) == 4096

