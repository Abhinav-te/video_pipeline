"""tests/test_normalized_events.py

Tests NormalizedEvent model and deterministic parser for developer execution events.
- Model agrees with TypeScript WorkflowEvent contract.
- Validates sequence ordering, monotonic timestamps, and causality.
- Tests deterministic parsing of NDJSON and tagged log streams.
- Rejects malformed and out-of-order events.
"""

import json
import pytest

from engine.events.event_model import (
    NormalizedEvent,
    validate_event_sequence,
    parse_structured_execution_events,
)


def test_normalized_event_schema_contract():
    ev = NormalizedEvent(
        target="charge_step",
        action="start",
        label="POST /v1/payment_intents",
        at_word="charging",
        timestamp_sec=1.25,
        elapsed="140ms",
        evidence_id="ev_01",
        artifact_id="exec_art_01",
    )
    assert ev.target == "charge_step"
    assert ev.action == "start"
    assert ev.timestamp_sec == 1.25
    assert ev.elapsed == "140ms"


def test_validate_event_sequence_valid_causality():
    events = [
        NormalizedEvent(target="step_charge", action="start", timestamp_sec=0.0),
        NormalizedEvent(target="step_charge", action="fail", timestamp_sec=0.5, label="503 Timeout"),
        NormalizedEvent(target="step_charge", action="retry", timestamp_sec=1.0, label="Retry with Idempotency Key"),
        NormalizedEvent(target="step_charge", action="recover", timestamp_sec=1.5, label="200 OK (Replayed)"),
        NormalizedEvent(target="step_charge", action="succeed", timestamp_sec=2.0),
    ]
    is_valid, errors = validate_event_sequence(events, known_targets={"step_charge"})
    assert is_valid
    assert errors == []


def test_validate_event_sequence_out_of_order_timestamps():
    events = [
        NormalizedEvent(target="step_charge", action="start", timestamp_sec=1.5),
        NormalizedEvent(target="step_charge", action="succeed", timestamp_sec=1.0),  # Earlier timestamp!
    ]
    is_valid, errors = validate_event_sequence(events)
    assert not is_valid
    assert any("out-of-order timestamp" in e for e in errors)


def test_validate_event_sequence_invalid_causality():
    # Attempting to recover without prior failure or start
    events = [
        NormalizedEvent(target="step_charge", action="recover", timestamp_sec=0.0),
    ]
    is_valid, errors = validate_event_sequence(events)
    assert not is_valid
    assert any("cannot 'recover'" in e for e in errors)


def test_parse_structured_execution_events_ndjson():
    ndjson_log = """
    {"action": "start", "target": "step1_init", "timestamp_sec": 0.1, "elapsed": "10ms"}
    {"action": "saved_state", "target": "step1_init", "timestamp_sec": 0.4, "elapsed": "300ms"}
    {"action": "start", "target": "step2_network", "timestamp_sec": 0.5}
    {"action": "fail", "target": "step2_network", "timestamp_sec": 0.9, "label": "ECONNRESET"}
    {"action": "retry", "target": "step2_network", "timestamp_sec": 1.2}
    {"action": "recover", "target": "step2_network", "timestamp_sec": 1.6, "label": "Recovered from checkpoint"}
    """
    events = parse_structured_execution_events(ndjson_log, artifact_id="exec_art_ndjson")
    assert len(events) == 6
    assert events[0].action == "start"
    assert events[0].target == "step1_init"
    assert events[3].action == "fail"
    assert events[3].label == "ECONNRESET"
    assert events[5].action == "recover"

    # Verify parsed events pass sequence validation
    is_valid, errors = validate_event_sequence(events)
    assert is_valid, f"Parsed events failed validation: {errors}"


def test_parse_structured_execution_events_tagged():
    tagged_log = """
    [INFO] Starting workflow execution...
    [EVENT:start] target=step_auth label="Verify Token" timestamp=0.2
    [EVENT:succeed] target=step_auth timestamp=0.6 elapsed=400ms
    [EVENT:start] target=step_pay label="Charge Card" timestamp=0.8
    [EVENT:fail] target=step_pay label="503 Service Unavailable" timestamp=1.2
    [EVENT:retry] target=step_pay label="Auto Retry" timestamp=1.8
    [EVENT:succeed] target=step_pay timestamp=2.2 elapsed=400ms
    [INFO] Execution finished.
    """
    events = parse_structured_execution_events(tagged_log, default_evidence_id="ev_step_run_01")
    assert len(events) == 6
    assert events[0].target == "step_auth"
    assert events[0].action == "start"
    assert events[1].elapsed == "400ms"
    assert events[3].label == "503 Service Unavailable"
    assert events[0].evidence_id == "ev_step_run_01"


def test_validate_event_sequence_fail_to_succeed_rejected():
    """Verify that start -> fail -> succeed without retry or recovery is rejected."""
    events = [
        NormalizedEvent(target="step_charge", action="start", timestamp_sec=0.0),
        NormalizedEvent(target="step_charge", action="fail", timestamp_sec=0.5),
        NormalizedEvent(target="step_charge", action="succeed", timestamp_sec=1.0),
    ]
    is_valid, errors = validate_event_sequence(events)
    assert not is_valid
    assert any("cannot 'succeed' target directly from state 'fail'" in e for e in errors)


def test_validate_event_sequence_fail_retry_succeed_accepted():
    """Verify that start -> fail -> retry -> succeed is accepted."""
    events = [
        NormalizedEvent(target="step_charge", action="start", timestamp_sec=0.0),
        NormalizedEvent(target="step_charge", action="fail", timestamp_sec=0.5),
        NormalizedEvent(target="step_charge", action="retry", timestamp_sec=1.0),
        NormalizedEvent(target="step_charge", action="succeed", timestamp_sec=1.5),
    ]
    is_valid, errors = validate_event_sequence(events)
    assert is_valid
    assert errors == []


def test_validate_event_sequence_unknown_target_and_evidence():
    """Verify that unknown targets and evidence IDs are rejected when allowed sets provided."""
    events = [
        NormalizedEvent(target="unknown_step", action="start", evidence_id="unknown_ev_01"),
    ]
    is_valid, errors = validate_event_sequence(
        events,
        known_targets={"step_charge", "step_auth"},
        valid_evidence_ids={"ev_01", "ev_02"},
    )
    assert not is_valid
    assert any("unknown target 'unknown_step'" in e for e in errors)
    assert any("unknown evidence_id 'unknown_ev_01'" in e for e in errors)


