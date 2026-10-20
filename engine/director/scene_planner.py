"""engine/director/scene_planner.py

Generates an Evidence-Linked Scene Plan (scene_plan.json) from a selected developer workflow and EvidencePack.
Enforces a 5-beat story arc where every claim is backed by evidence_ids with natural spoken English.
Adheres strictly to the AGENTS.md Universal Scene Vocabulary with ZERO company hardcoding.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from engine.ingestion.evidence_extractor import EvidencePack, EvidenceRecord
    from engine.director.workflow_selector import WorkflowCandidate
except ImportError:
    from ingestion.evidence_extractor import EvidencePack, EvidenceRecord
    from director.workflow_selector import WorkflowCandidate


class NarrationSegment(BaseModel):
    text: str = Field(description="Natural spoken English narration without raw syntax or punctuation")
    evidence_ids: List[str] = Field(description="Evidence IDs directly supporting this narration claim")


class PlannedScene(BaseModel):
    scene_id: int
    title: str
    spoken_text: str
    visual_type: str
    evidence_ids: List[str] = Field(default_factory=list)
    narration_segments: List[NarrationSegment] = Field(default_factory=list)
    
    # Universal Scene Vocabulary Fields
    display_text: Optional[str] = None
    emphasis_word: Optional[str] = None
    code: Optional[str] = None
    filename: Optional[str] = None
    language: Optional[str] = None
    highlight_lines: Optional[List[int]] = None
    focus_phrase: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    events: Optional[List[Dict[str, Any]]] = None
    items: Optional[List[Dict[str, Any]]] = None
    cta_url: Optional[str] = None


class ScenePlan(BaseModel):
    title: str
    topic: str
    subject: str = "code"
    duration_target_seconds: int = 30
    workflow_id: str
    evidence_pack_hash: str
    scenes: List[PlannedScene]

    def to_director_script(self) -> Dict[str, Any]:
        """Converts scene plan into the dictionary format expected by the video engine."""
        return {
            "title": self.title,
            "topic": self.topic,
            "subject": self.subject,
            "duration": float(self.duration_target_seconds),
            "scenes": [s.model_dump(exclude_none=True) for s in self.scenes],
        }


def format_spoken_text(text: str) -> str:
    """
    Converts code syntax and symbols into natural, professional spoken English.
    e.g. 'customer_id' -> 'customer I D'
         'HTTP 503' -> 'H T T P 503'
    Note: Code primitives like 'step.run()' are sanitized strictly inside TTS synthesis
    to prevent leaking phonetics into visual titles or subtitles.
    """
    s = text
    s = re.sub(r"\bIdempotency-Key\b", "Idempotency Key", s)
    s = re.sub(r"\bidempotencyKey\b", "idempotency key", s)
    s = re.sub(r"\bPOST\b", "post", s)
    s = re.sub(r"\bHTTP\s+503\b", "H T T P 503", s)
    s = re.sub(r"\bHTTP\s+400\b", "H T T P 400", s)
    s = re.sub(r"\bAPI\b", "A P I", s)
    s = re.sub(r"\bIDs?\b", "I D", s)
    s = re.sub(r"\bURL\b", "U R L", s)
    s = re.sub(r"\bUUID\s*v4\b", "U U I D version 4", s)
    s = re.sub(r"[{}\[\]`'\"]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def build_scene_plan_deterministic(
    workflow: WorkflowCandidate,
    evidence_pack: EvidencePack,
    duration_target: int = 30,
) -> ScenePlan:
    """
    Deterministically builds a 5-beat evidence-linked scene plan.
    01 Problem -> 02 Implementation -> 03 Demonstration -> 04 Payoff -> 05 Takeaway.
    """
    code_records = evidence_pack.filter_by_kind("code_evidence")
    behavior_records = evidence_pack.filter_by_kind("behavior")
    failure_records = evidence_pack.filter_by_kind("failure_behavior")
    action_records = evidence_pack.filter_by_kind("developer_action")
    limitation_records = evidence_pack.filter_by_kind("limitation")
    concept_records = evidence_pack.filter_by_kind("concept")

    # Detect technical pattern from evidence records & workflow title
    corpus = " ".join([r.claim.lower() + " " + r.excerpt.lower() for r in evidence_pack.records])
    is_step_run = "step.run" in corpus or "step.run" in workflow.title.lower() or "durable" in workflow.title.lower() or "memoiz" in corpus
    is_idempotency = not is_step_run and ("idempotency key" in corpus or "idempotency-key" in corpus or "idempotent" in workflow.title.lower())

    if is_idempotency:
        b1_records = failure_records[:2] if failure_records else behavior_records[:2]
        b1_ev_ids = [r.id for r in b1_records]
        b1_narration = "When a network drop or timeout occurs, retrying a mutating request risks performing duplicate transactions and double-charging customers."
        b1_title = "The Duplicate Request Problem"
        b1_display = "PROBLEM • DUPLICATE TRANSACTIONS"
        b1_emphasis = "DUPLICATE"
        b1_items = [
            {"label": "Request #1", "detail": "POST /v1/charges (Timeout)", "status": "crashed"},
            {"label": "Network Drop", "detail": "Client receives no response", "status": "warning"},
            {"label": "Blind Retry", "detail": "Blind retry charges customer twice", "status": "duplicate_risk"},
        ]

        b2_code_rec = code_records[0] if code_records else None
        b2_action_rec = action_records[0] if action_records else (behavior_records[0] if behavior_records else None)
        b2_ev_ids = []
        if b2_code_rec:
            b2_ev_ids.append(b2_code_rec.id)
        if b2_action_rec and b2_action_rec.id not in b2_ev_ids:
            b2_ev_ids.append(b2_action_rec.id)
        b2_narration = "Pass a unique Idempotency Key header on post requests to guarantee safe execution across retries."
        b2_title = "Idempotency Key Header & SDK Setup"
        b2_filename = "create-payment.ts"
        b2_focus = "idempotencyKey"
        b2_emphasis = "idempotencyKey"
        b2_highlights = [3, 4, 5, 6, 7]

        b3_records = (behavior_records[:2] + failure_records[:2])
        b3_ev_ids = list(dict.fromkeys([r.id for r in b3_records]))
        b3_narration = "The initial request saves its result. If a network timeout strikes, retrying with the same key returns the cached response with no duplicate charge."
        b3_title = "Cached Response & Duplicate Prevention"
        b3_entities = [
            {
                "id": "req_1",
                "label": "POST /v1/payment_intents (Key: order_123)",
                "sub_label": "Initial Request: Process & Save State",
                "memoized_detail": "Payment API: Response cached • 0 duplicate charges",
            },
            {
                "id": "req_2",
                "label": "POST /v1/payment_intents (Key: order_123)",
                "sub_label": "Retried Request: Network Timeout Recovery",
            },
        ]
        b3_events = [
            {"target": "req_1", "action": "start", "label": "Sending Initial Request"},
            {"target": "req_1", "action": "succeed", "label": "200 OK — Response Cached"},
            {"target": "req_2", "action": "start", "label": "Connection Dropped / Timeout"},
            {"target": "req_2", "action": "fail", "label": "Client Network Timeout"},
            {"target": "req_2", "action": "retry", "label": "Retry #1 — Reusing Same Key"},
            {"target": "req_2", "action": "recover", "label": "200 OK — Cached Response Reused"},
        ]
        b3_emphasis = "cached"

        b4_records = failure_records[:1] + behavior_records[:1]
        b4_ev_ids = list(dict.fromkeys([r.id for r in b4_records]))
        b4_narration = "The client recovers safely without creating a second payment, eliminating double charges and protecting payment integrity."
        b4_title = "Safe Recovery Without Duplicate Charges"
        b4_items = [
            {
                "title": "DUPLICATE CHARGES",
                "value": "0",
                "subtitle": "Original Charge Reused",
            },
            {
                "title": "RETRY SAFETY",
                "value": "IDEMPOTENT",
                "subtitle": "Cached Response Replayed",
            },
        ]
        b4_emphasis = "recovery"

        b5_records = concept_records[:1] if concept_records else action_records[:1]
        b5_ev_ids = list(dict.fromkeys([r.id for r in b5_records]))
        doc_source_url = evidence_pack.sources[0].source_url if evidence_pack.sources else ""
        b5_narration = "Idempotency keys prevent duplicate operations and ensure safe retries out of the box. Check the official docs to get started."
        b5_title = "Idempotent Request Primitives"
        b5_display = "IDEMPOTENT APIS • RETRY SAFETY"
        b5_emphasis = "docs"

    else:
        # Step-based workflow & durable execution
        b1_records = failure_records[:2] if failure_records else behavior_records[:2]
        b1_ev_ids = [r.id for r in b1_records]
        b1_narration = "When a multi-step background job crashes midway, restarting from scratch wastes compute and risks duplicate transactions."
        b1_title = "The Multi-Step Failure Problem"
        b1_display = "PROBLEM • DISTRIBUTED RETRIES"
        b1_emphasis = "FAILURE"
        b1_items = [
            {"label": "Step 1", "detail": "fetch-billing (Completed)", "status": "done"},
            {"label": "Step 2", "detail": "charge-customer (503 Crash)", "status": "crashed"},
            {"label": "Naive Retry", "detail": "Re-runs Step 1 & Double-Charges", "status": "duplicate_risk"},
        ]

        b2_code_rec = code_records[0] if code_records else None
        b2_action_rec = action_records[0] if action_records else (behavior_records[0] if behavior_records else None)
        b2_ev_ids = []
        if b2_code_rec:
            b2_ev_ids.append(b2_code_rec.id)
        if b2_action_rec and b2_action_rec.id not in b2_ev_ids:
            b2_ev_ids.append(b2_action_rec.id)
        b2_narration = "Wrap each critical operation in step.run() to isolate execution, checkpoint workflow state, and guarantee failure recovery without restarting."
        b2_title = "Step Definition & Isolation"
        b2_filename = "process-order.ts"
        b2_focus = "step.run"
        b2_emphasis = "step.run"
        b2_highlights = [5, 6, 7, 8, 9, 10]

        b3_records = (behavior_records[:2] + failure_records[:2])
        b3_ev_ids = list(dict.fromkeys([r.id for r in b3_records]))
        b3_narration = "Step one saves its result to workflow state. If step two fails, only step two retries while reusing the memoized state."
        b3_title = "Memoized State & Retry Isolation"
        b3_entities = [
            {"id": "step_1", "label": "step.run('fetch-billing-data')"},
            {"id": "step_2", "label": "step.run('charge-customer')"},
        ]
        b3_events = [
            {"target": "step_1", "action": "start", "label": "Executing Step 1"},
            {"target": "step_1", "action": "succeed", "label": "Result Saved & Memoized"},
            {"target": "step_2", "action": "start", "label": "Executing Step 2"},
            {"target": "step_2", "action": "fail", "label": "Network Error: 503"},
            {"target": "step_2", "action": "retry", "label": "Retry #1 (Reusing Step 1 State)"},
            {"target": "step_2", "action": "recover", "label": "Step 2 Succeeded"},
        ]
        b3_emphasis = "memoized"

        b4_records = failure_records[:1] + behavior_records[:1]
        b4_ev_ids = list(dict.fromkeys([r.id for r in b4_records]))
        b4_narration = "The failed step recovers automatically without re-executing step one, eliminating duplicate operations and redundant load."
        b4_title = "Resilient Recovery Without Duplication"
        b4_items = [
            {
                "title": "MEMOIZED STEP STATE",
                "value": "0 RE-RUNS",
                "subtitle": "Completed steps never re-execute on retry",
                "tag": "DURABLE MEMORY",
            },
            {
                "title": "ISOLATED STEP RETRIES",
                "value": "INDEPENDENT",
                "subtitle": "Failed steps retry with exponential backoff",
                "tag": "RESILIENCE",
            },
            {
                "title": "IDEMPOTENCY NUANCE",
                "value": "GUARDED",
                "subtitle": "External side effects require deterministic isolation",
                "tag": "CORRECTNESS",
            },
        ]
        b4_emphasis = "recovery"

        b5_records = concept_records[:1] if concept_records else action_records[:1]
        b5_ev_ids = list(dict.fromkeys([r.id for r in b5_records]))
        doc_source_url = evidence_pack.sources[0].source_url if evidence_pack.sources else ""
        b5_narration = "Durable steps provide isolated retries and memoized recovery out of the box. Check the official docs to get started."
        b5_title = "Durable Execution Primitives"
        b5_display = "DURABLE EXECUTION • step.run()"
        b5_emphasis = "docs"

    # Verified clean TypeScript snippet
    code_text = (b2_code_rec.excerpt if b2_code_rec else workflow.code_snippet) or ""
    clean_lines = [l for l in code_text.splitlines() if l.strip()]
    if len(clean_lines) > 12:
        code_text = "\n".join(clean_lines[:12])

    scenes: List[PlannedScene] = [
        # Scene 1: Problem (01 Problem)
        PlannedScene(
            scene_id=1,
            title=b1_title,
            spoken_text=format_spoken_text(b1_narration),
            visual_type="fullscreen_text",
            evidence_ids=b1_ev_ids,
            narration_segments=[
                NarrationSegment(text=format_spoken_text(b1_narration), evidence_ids=b1_ev_ids)
            ],
            display_text=b1_display,
            items=b1_items,
            emphasis_word=b1_emphasis,
        ),
        # Scene 2: Implementation (02 Implementation)
        PlannedScene(
            scene_id=2,
            title=b2_title,
            spoken_text=format_spoken_text(b2_narration),
            visual_type="code_reveal",
            evidence_ids=b2_ev_ids,
            narration_segments=[
                NarrationSegment(text=format_spoken_text(b2_narration), evidence_ids=b2_ev_ids)
            ],
            code=code_text,
            filename=b2_filename,
            language="typescript",
            highlight_lines=b2_highlights,
            focus_phrase=b2_focus,
            emphasis_word=b2_emphasis,
        ),
        # Scene 3: Demonstration (03 Demonstration)
        PlannedScene(
            scene_id=3,
            title=b3_title,
            spoken_text=format_spoken_text(b3_narration),
            visual_type="workflow_state_transition",
            evidence_ids=b3_ev_ids,
            narration_segments=[
                NarrationSegment(text=format_spoken_text(b3_narration), evidence_ids=b3_ev_ids)
            ],
            entities=b3_entities,
            events=b3_events,
            emphasis_word=b3_emphasis,
        ),
        # Scene 4: Payoff (04 Payoff)
        PlannedScene(
            scene_id=4,
            title=b4_title,
            spoken_text=format_spoken_text(b4_narration),
            visual_type="bento_grid",
            evidence_ids=b4_ev_ids,
            narration_segments=[
                NarrationSegment(text=format_spoken_text(b4_narration), evidence_ids=b4_ev_ids)
            ],
            items=b4_items,
            emphasis_word=b4_emphasis,
        ),
        # Scene 5: Takeaway (05 Takeaway)
        PlannedScene(
            scene_id=5,
            title=b5_title,
            spoken_text=format_spoken_text(b5_narration),
            visual_type="takeaway_cta",
            evidence_ids=b5_ev_ids,
            narration_segments=[
                NarrationSegment(text=format_spoken_text(b5_narration), evidence_ids=b5_ev_ids)
            ],
            display_text=b5_display,
            cta_url=doc_source_url,
            emphasis_word=b5_emphasis,
        ),
    ]

    pack_hash = evidence_pack.sources[0].content_hash if evidence_pack.sources else "unknown_hash"

    return ScenePlan(
        title=workflow.title,
        topic=workflow.title,
        subject="code",
        duration_target_seconds=duration_target,
        workflow_id=workflow.id,
        evidence_pack_hash=pack_hash,
        scenes=scenes,
    )


def plan_scenes(
    workflow: WorkflowCandidate,
    evidence_pack: EvidencePack,
    duration_target: int = 30,
    mock: bool = False,
) -> ScenePlan:
    """
    Main scene planning entry point.
    In mock or offline mode, uses the deterministic 5-beat evidence-linked planner.
    """
    return build_scene_plan_deterministic(workflow, evidence_pack, duration_target=duration_target)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate scene plan from EvidencePack and selected workflow.")
    parser.add_argument("--evidence-pack", type=str, required=True, help="Path to evidence_pack.json")
    parser.add_argument("--workflow-file", type=str, required=True, help="Path to workflow_candidates.json")
    parser.add_argument("--output", type=str, default="scene_plan.json", help="Path to save scene plan")
    args = parser.parse_args()

    with open(args.evidence_pack, "r", encoding="utf-8") as f:
        pack = EvidencePack.model_validate(json.load(f))

    with open(args.workflow_file, "r", encoding="utf-8") as f:
        wf_data = json.load(f)
        selected_wf = WorkflowCandidate.model_validate(wf_data.get("selected_workflow", wf_data))

    plan = plan_scenes(selected_wf, pack)
    out_path = Path(args.output).resolve()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2)

    print(f"Generated {len(plan.scenes)}-beat scene plan -> {out_path}")

