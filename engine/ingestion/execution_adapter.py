"""engine/ingestion/execution_adapter.py

Controlled Execution Adapter & Security Isolation Guard.
- Defines the ExecutionAdapter interface for developer tool examples.
- Enforces strict security policy: Live execution remains DISABLED unless
  a verified OS/container sandbox (cgroups, network namespace, read-only root)
  is confirmed.
- Rejects pseudo-sandboxes (cleared env or tempdir alone are NOT sandboxes).
- Provides deterministic fixture execution and recorded artifact verification.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    from engine.ingestion.evidence_extractor import ExecutionArtifact, compute_sha256
except ImportError:
    from ingestion.evidence_extractor import ExecutionArtifact, compute_sha256


class SecurityIsolationError(RuntimeError):
    """Raised when live execution is attempted without a verified OS-level isolation sandbox."""
    pass


def check_environment_isolation() -> Tuple[bool, str]:
    """
    Inspects whether the host environment provides genuine container/namespace isolation:
    - Dedicated unshared mount namespace with read-only host root
    - Network namespace blocking unauthorized egress
    - Process and PID isolation
    Returns (is_isolated, explanation).
    """
    # Check if running inside an isolated OCI container or rootless namespace sandbox
    in_docker = Path("/.dockerenv").exists()
    in_container = os.environ.get("container") == "podman" or in_docker
    has_bwrap = shutil.which("bwrap") is not None

    # Even within a development container or VM, running arbitrary customer code via host subprocess
    # without unshared user/network namespaces can leak environment variables, local ports, or credentials.
    # Therefore, live host execution is strictly disabled by default.
    return (
        False,
        "Host environment lacks verified rootless sandbox isolation (unshared mount/network namespaces). "
        "Running arbitrary subprocess commands exposes host filesystem and environment. "
        "Live execution is disabled by security policy.",
    )


class ControlledExecutionAdapter:
    """
    Adapter for running pre-vetted developer tool examples and producing
    traceable ExecutionArtifacts.
    """

    def __init__(self, run_id: str, live_execution_enabled: bool = False):
        self.run_id = run_id
        self._is_live_enabled = live_execution_enabled

    def is_live_execution_available(self) -> Tuple[bool, str]:
        """Returns whether live execution can be safely performed in the current environment."""
        if not self._is_live_enabled:
            return False, "Live execution is explicitly disabled by security policy."
        return check_environment_isolation()

    def execute_command(
        self,
        command: List[str],
        source_code: str,
        timeout_seconds: float = 10.0,
        cwd: Optional[Path] = None,
    ) -> ExecutionArtifact:
        """
        Executes an approved technical command inside a secure sandbox.
        STRICT POLICY: If real OS-level isolation is not confirmed, this halts with SecurityIsolationError.
        """
        is_safe, reason = self.is_live_execution_available()
        if not is_safe:
            raise SecurityIsolationError(
                f"Execution Blocked: Cannot run live command {command!r}. Reason: {reason}"
            )

        # Intentionally unreachable unless is_safe is True
        raise NotImplementedError("Live sandbox execution runner is not enabled.")

    def record_fixture_artifact(
        self,
        artifact_id: str,
        command: List[str],
        exit_code: int,
        stdout: str,
        stderr: str,
        source_text: str,
        tool_versions: Optional[Dict[str, str]] = None,
        env_description: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
        recorded_at: Optional[str] = None,
    ) -> ExecutionArtifact:
        """
        Deterministically produces an ExecutionArtifact from vetted fixture execution data.
        Binds source hashes and execution output hashes without unsafe host execution.
        Explicitly distinguishes prerecorded fixture data (provenance="prerecorded_fixture",
        is_fixture=True) from genuine live observed execution.
        """
        src_hash = compute_sha256(source_text)
        art_payload = f"{exit_code}\n{stdout}\n{stderr}"
        art_hash = compute_sha256(art_payload)

        # Cap preview at 4096 bytes (4KB) to prevent giant manifest bloat
        stdout_preview = stdout[:4096] if stdout else ""
        stderr_preview = stderr[:4096] if stderr else ""

        stdout_ref = None
        stderr_ref = None

        if output_dir is not None:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            out_file = output_dir / f"{artifact_id}.stdout.log"
            err_file = output_dir / f"{artifact_id}.stderr.log"
            out_file.write_text(stdout, encoding="utf-8")
            err_file.write_text(stderr, encoding="utf-8")
            stdout_ref = str(out_file)
            stderr_ref = str(err_file)

        # Do NOT claim detected runtime facts or secure sandbox isolation for a fixture.
        # Explicitly mark metadata as fixture provenance without false sandbox guarantees.
        env_meta: Dict[str, Any] = {
            "execution_type": "prerecorded_fixture",
            "isolation_verified": False,
        }
        if tool_versions:
            env_meta["fixture_tool_versions"] = tool_versions
        if env_description:
            env_meta["fixture_env_description"] = env_description

        return ExecutionArtifact(
            artifact_id=artifact_id,
            run_id=self.run_id,
            command=command,
            exit_code=exit_code,
            stdout_preview=stdout_preview,
            stderr_preview=stderr_preview,
            stdout_ref=stdout_ref,
            stderr_ref=stderr_ref,
            executed_at=recorded_at,
            is_fixture=True,
            environment_meta=env_meta,
            source_hash=src_hash,
            artifact_hash=art_hash,
            provenance="prerecorded_fixture",
        )

    def load_fixture_artifact(self, artifact_json_path: Path) -> ExecutionArtifact:
        """Safely loads an ExecutionArtifact from a pre-recorded JSON fixture."""
        path = Path(artifact_json_path)
        if not path.exists():
            raise FileNotFoundError(f"Execution artifact fixture not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "is_fixture" not in data:
            data["is_fixture"] = True
        # Fixtures loaded from file cannot masquerade as live observed execution
        if data.get("is_fixture", True) and data.get("provenance") == "observed_execution":
            data["provenance"] = "prerecorded_fixture"

        return ExecutionArtifact(**data)

