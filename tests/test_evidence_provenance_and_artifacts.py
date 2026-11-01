"""tests/test_evidence_provenance_and_artifacts.py

Tests explicit evidence provenance, execution artifacts, and visual representation contracts.
- Provenance: documented vs observed_execution.
- ExecutionArtifact: command, exit code, hashes, bounded stdout/stderr.
- PlannedScene: visual_representation (observed_capture, illustrative, composite).
- Backward compatibility: existing EvidencePack and project fixtures default cleanly.
"""

import json
from pathlib import Path
import pytest

from engine.ingestion.evidence_extractor import (
    EvidenceRecord,
    EvidencePack,
    ExecutionArtifact,
    compute_sha256,
)
from engine.director.scene_planner import PlannedScene, NarrationSegment

REPO_DIR = Path(__file__).resolve().parent.parent


def test_evidence_record_provenance_defaults():
    rec = EvidenceRecord(
        id="ev_01",
        kind="concept",
        claim="Idempotent requests prevent double charging.",
        source_url="https://docs.stripe.com/api/idempotent_requests",
        source_section="Overview",
        excerpt="The Stripe API supports idempotency...",
        retrieved_at="2026-10-23T12:00:00Z",
        content_hash=compute_sha256("test excerpt"),
    )
    assert rec.provenance == "documented"
    assert rec.execution_artifact_id is None
    assert rec.confidence == "source_supported"


def test_evidence_record_observed_execution():
    rec = EvidenceRecord(
        id="ev_exec_01",
        kind="behavior",
        claim="POST /v1/payment_intents returns 200 with cached response on retry.",
        source_url="tests/fixtures/exec_idempotency.json",
        source_section="Runtime Output",
        excerpt="HTTP/1.1 200 OK\nIdempotency-Replayed: true",
        retrieved_at="2026-10-23T12:00:00Z",
        content_hash=compute_sha256("HTTP/1.1 200 OK"),
        provenance="observed_execution",
        execution_artifact_id="exec_art_101",
    )
    assert rec.provenance == "observed_execution"
    assert rec.execution_artifact_id == "exec_art_101"


def test_execution_artifact_schema_and_hashing():
    cmd = ["node", "test_idempotency.js"]
    src = "console.log('Testing idempotency key retry');"
    stdout_text = '{"status": "succeeded", "idempotency_key": "order_123"}'
    
    art = ExecutionArtifact(
        artifact_id="exec_art_101",
        run_id="run_test_001",
        command=cmd,
        exit_code=0,
        stdout_preview=stdout_text,
        stderr_preview="",
        executed_at="2026-10-23T12:00:00Z",
        environment_meta={"node": "20.20.2", "sandbox": "fixture"},
        source_hash=compute_sha256(src),
        artifact_hash=compute_sha256(f"0\n{stdout_text}\n"),
        provenance="observed_execution",
    )
    assert art.artifact_id == "exec_art_101"
    assert art.exit_code == 0
    assert len(art.source_hash) == 64
    assert len(art.artifact_hash) == 64
    assert art.provenance == "observed_execution"


def test_planned_scene_visual_representation():
    scene_illustrative = PlannedScene(
        scene_id=1,
        title="Problem Overview",
        spoken_text="Network drops duplicate charges.",
        visual_type="hook_scene",
    )
    assert scene_illustrative.visual_representation == "illustrative"
    assert scene_illustrative.execution_artifact_id is None

    scene_observed = PlannedScene(
        scene_id=2,
        title="Observed Execution",
        spoken_text="Here is the live terminal trace.",
        visual_type="workflow_state_transition",
        visual_representation="observed_capture",
        execution_artifact_id="exec_art_101",
    )
    assert scene_observed.visual_representation == "observed_capture"
    assert scene_observed.execution_artifact_id == "exec_art_101"


def test_evidence_pack_with_execution_artifacts():
    pack = EvidencePack(
        project="Stripe Idempotency",
        records=[
            EvidenceRecord(
                id="ev_01",
                kind="code_evidence",
                claim="Pass idempotencyKey option in Node SDK.",
                source_url="examples/docs/stripe_idempotency.md",
                source_section="SDK",
                excerpt="stripe.paymentIntents.create(params, { idempotencyKey: order.id });",
                retrieved_at="2026-10-23T12:00:00Z",
                content_hash=compute_sha256("code"),
                provenance="documented",
            )
        ],
        execution_artifacts=[
            ExecutionArtifact(
                artifact_id="exec_art_stripe_01",
                run_id="run_stripe_001",
                command=["node", "verify_stripe.js"],
                exit_code=0,
                stdout_preview="200 OK",
                stderr_preview="",
                executed_at="2026-10-23T12:00:00Z",
                source_hash=compute_sha256("verify_stripe"),
                artifact_hash=compute_sha256("0\n200 OK\n"),
            )
        ]
    )
    d = pack.model_dump()
    assert len(d["records"]) == 1
    assert len(d["execution_artifacts"]) == 1
    assert d["records"][0]["provenance"] == "documented"
    assert d["execution_artifacts"][0]["artifact_id"] == "exec_art_stripe_01"

