"""engine/events/event_model.py

Normalized Workflow Event Model & Deterministic Log/Output Parser.
- Matches TypeScript WorkflowEvent interface in video/src/components/WorkflowStateTransition.tsx:
    action: 'start' | 'succeed' | 'saved_state' | 'fail' | 'retry' | 'recover'
- Validates causality, timestamps, targets, and evidence bindings.
- Deterministically parses structured execution logs (JSON/NDJSON/Key-Value)
  without loose unstructured text hallucination.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

WorkflowAction = Literal[
    "start",
    "succeed",
    "saved_state",
    "fail",
    "retry",
    "recover",
]

VALID_ACTIONS: Set[WorkflowAction] = {
    "start",
    "succeed",
    "saved_state",
    "fail",
    "retry",
    "recover",
}


class WorkflowEntity(BaseModel):
    id: str = Field(description="Stable target identifier (e.g. 'step1_auth', 'step2_charge')")
    label: str = Field(description="Human-readable title displayed in the diagram/workflow node")
    sub_label: Optional[str] = Field(default=None, description="Optional secondary subtitle/metric")


class NormalizedEvent(BaseModel):
    target: str = Field(description="Target entity ID to which this state transition applies")
    action: WorkflowAction = Field(description="State transition action type")
    label: Optional[str] = Field(default=None, description="Optional text badge or message")
    at_word: Optional[str] = Field(default=None, description="Narration word trigger for audio synchronization")
    timestamp_sec: Optional[float] = Field(default=None, description="Exact timestamp offset in seconds from scene start")
    elapsed: Optional[Union[str, float]] = Field(default=None, description="Recorded elapsed execution time (e.g. '120ms' or 0.12)")
    evidence_id: Optional[str] = Field(default=None, description="Linked EvidenceRecord ID justifying this state transition")
    artifact_id: Optional[str] = Field(default=None, description="Linked ExecutionArtifact ID if derived from real execution")


def validate_event_sequence(
    events: List[NormalizedEvent],
    known_targets: Optional[Set[str]] = None,
    valid_evidence_ids: Optional[Set[str]] = None,
) -> Tuple[bool, List[str]]:
    """
    Validates state machine transitions and invariants:
    1. Target must be non-empty and in known_targets if provided.
    2. Action must be one of the 6 canonical states.
    3. Monotonic timestamp ordering (if timestamps are specified).
    4. Causal transition consistency:
       - 'retry' or 'recover' must be preceded by an initial state or failure.
       - 'succeed' after 'fail' without retry/recover is invalid.
    5. Evidence ID reference must exist in valid_evidence_ids if provided.
    """
    errors: List[str] = []
    if not events:
        errors.append("Event sequence is empty.")
        return False, errors

    last_timestamp = -1.0
    # Map target -> current state
    target_states: Dict[str, str] = {}

    for idx, ev in enumerate(events):
        prefix = f"Event[{idx}] (target='{ev.target}', action='{ev.action}')"

        if not ev.target or not ev.target.strip():
            errors.append(f"{prefix}: target identifier cannot be empty.")

        if known_targets is not None and ev.target not in known_targets:
            errors.append(f"{prefix}: unknown target '{ev.target}'. Expected one of {sorted(known_targets)}.")

        if ev.action not in VALID_ACTIONS:
            errors.append(f"{prefix}: invalid action '{ev.action}'. Expected one of {sorted(VALID_ACTIONS)}.")

        if ev.timestamp_sec is not None:
            if ev.timestamp_sec < 0:
                errors.append(f"{prefix}: timestamp_sec ({ev.timestamp_sec}s) must be non-negative.")
            elif ev.timestamp_sec < last_timestamp:
                errors.append(
                    f"{prefix}: out-of-order timestamp ({ev.timestamp_sec}s < previous {last_timestamp}s)."
                )
            last_timestamp = ev.timestamp_sec

        if valid_evidence_ids is not None and ev.evidence_id:
            if ev.evidence_id not in valid_evidence_ids:
                errors.append(f"{prefix}: references unknown evidence_id '{ev.evidence_id}'.")

        # Causal state machine validation
        prev_state = target_states.get(ev.target, "none")

        if ev.action == "succeed":
            if prev_state == "fail":
                errors.append(
                    f"{prefix}: cannot 'succeed' target directly from state 'fail' without an intervening retry or recovery."
                )
            elif prev_state == "none":
                errors.append(
                    f"{prefix}: cannot 'succeed' target from state 'none' without an initial operation (e.g. 'start')."
                )
        elif ev.action == "recover":
            if prev_state not in ("fail", "retry", "saved_state"):
                errors.append(
                    f"{prefix}: cannot 'recover' target from state '{prev_state}' without a preceding failure, retry, or saved_state."
                )
        elif ev.action == "retry":
            if prev_state not in ("fail", "start", "saved_state", "retry"):
                errors.append(
                    f"{prefix}: cannot 'retry' target from state '{prev_state}' without a preceding failure, start, or retry."
                )
        elif ev.action == "fail":
            if prev_state not in ("start", "retry", "saved_state"):
                errors.append(
                    f"{prefix}: cannot 'fail' target from state '{prev_state}' without an active operation."
                )
        elif ev.action == "saved_state":
            if prev_state not in ("start", "retry", "recover", "saved_state"):
                errors.append(
                    f"{prefix}: cannot 'saved_state' target from state '{prev_state}' without an active operation."
                )

        target_states[ev.target] = ev.action

    return len(errors) == 0, errors


def parse_structured_execution_events(
    raw_output: str,
    artifact_id: Optional[str] = None,
    default_evidence_id: Optional[str] = None,
) -> List[NormalizedEvent]:
    """
    Deterministically parses structured execution output into NormalizedEvent objects.
    Supports:
    1. Line-delimited JSON (NDJSON) or JSON array of event objects.
    2. Structured tag format: [EVENT:action] target=<id> [label=<lbl>] [elapsed=<t>] [evidence=<ev_id>]
    """
    if not raw_output or not raw_output.strip():
        return []

    events: List[NormalizedEvent] = []

    # Attempt 1: JSON array or NDJSON
    stripped = raw_output.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            items = json.loads(stripped)
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and "target" in it and "action" in it:
                        events.append(
                            NormalizedEvent(
                                target=str(it["target"]),
                                action=it["action"],
                                label=it.get("label"),
                                at_word=it.get("at_word"),
                                timestamp_sec=float(it["timestamp_sec"]) if "timestamp_sec" in it and it["timestamp_sec"] is not None else None,
                                elapsed=it.get("elapsed"),
                                evidence_id=it.get("evidence_id") or default_evidence_id,
                                artifact_id=artifact_id,
                            )
                        )
                if events:
                    return events
        except Exception:
            pass

    # NDJSON line parsing
    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    action_candidate = data.get("action") or data.get("event") or data.get("status")
                    target_candidate = data.get("target") or data.get("step") or data.get("node")
                    if action_candidate in VALID_ACTIONS and target_candidate:
                        events.append(
                            NormalizedEvent(
                                target=str(target_candidate),
                                action=action_candidate,
                                label=data.get("label") or data.get("message"),
                                at_word=data.get("at_word"),
                                timestamp_sec=float(data["timestamp_sec"]) if "timestamp_sec" in data and data["timestamp_sec"] is not None else None,
                                elapsed=data.get("elapsed") or data.get("duration"),
                                evidence_id=data.get("evidence_id") or default_evidence_id,
                                artifact_id=artifact_id,
                            )
                        )
                        continue
            except Exception:
                pass

        # Structured tag parsing: [EVENT:action] target=step1 label="foo"
        tag_match = re.search(r"\[EVENT:([a-z_]+)\]\s+target=([^\s]+)", line)
        if tag_match:
            action_tag = tag_match.group(1)
            target_tag = tag_match.group(2)
            if action_tag in VALID_ACTIONS:
                label_m = re.search(r'label="([^"]+)"', line)
                elapsed_m = re.search(r'elapsed=([^\s]+)', line)
                ev_m = re.search(r'evidence=([^\s]+)', line)
                ts_m = re.search(r'timestamp=([0-9.]+)', line)

                events.append(
                    NormalizedEvent(
                        target=target_tag,
                        action=action_tag,  # type: ignore[arg-type]
                        label=label_m.group(1) if label_m else None,
                        elapsed=elapsed_m.group(1) if elapsed_m else None,
                        timestamp_sec=float(ts_m.group(1)) if ts_m else None,
                        evidence_id=ev_m.group(1) if ev_m else default_evidence_id,
                        artifact_id=artifact_id,
                    )
                )

    return events
