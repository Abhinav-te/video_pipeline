"""tests/test_planner_generality.py

Behavioral Test Suite for Data-Driven Scene Planning:
- Zero company hardcoding across different products (Inngest, Stripe, Generic Tool).
- Deterministic 5-beat story arc generation from EvidencePack.
- 100% evidence citation backing and dynamic highlight lines.
- First-class Release / Diff Mode ('What Changed in vX') with CodeTransformScene.
- 4-Gate validator verification on generated scene plans.
"""

import json
from pathlib import Path
import pytest

from engine.ingestion.evidence_extractor import extract_evidence_pack, extract_evidence_offline, SourceDocument
from engine.director.workflow_selector import select_best_workflow, WorkflowCandidate, WorkflowScore
from engine.director.scene_planner import plan_scenes, build_scene_plan_deterministic
from engine.validation.evidence_validator import validate_evidence_and_plan

REPO_DIR = Path(__file__).resolve().parent.parent


def test_planner_generality_inngest_step_run():
    """Verify scene planning for Inngest step.run() is 100% data-driven and passes all 4 gates."""
    doc_path = REPO_DIR / "examples" / "docs" / "inngest_step_run.md"
    assert doc_path.exists(), f"Missing {doc_path}"

    sources = [{"url": "https://www.inngest.com/docs/step-run", "local_file": str(doc_path), "title": "Inngest step.run Docs"}]
    project_profile = {
        "product": "Inngest",
        "topic": "Inngest step.run() Durable Execution",
        "duration_target_seconds": 30,
    }

    pack = extract_evidence_pack(sources, project_profile=project_profile, mock=True)
    assert len(pack.records) >= 3

    wf_res = select_best_workflow(pack, project_profile=project_profile, mock=True)
    plan = plan_scenes(wf_res.selected_workflow, pack, duration_target=30)

    assert len(plan.scenes) == 5
    # Verify no 12-line cap: code snippet has all lines including closing } and );
    code_scene = plan.scenes[1]
    assert code_scene.code is not None
    assert "```" not in code_scene.code
    assert code_scene.code.endswith(");")
    assert code_scene.highlight_lines is not None and len(code_scene.highlight_lines) > 0

    # Verify Gate 1-4 pass on generated plan
    val_report = validate_evidence_and_plan(pack, plan)
    assert val_report.passed, f"Validation failed: {val_report.checks}"
    assert val_report.claim_coverage_pct == 100.0


def test_planner_generality_stripe_idempotency():
    """Verify scene planning for Stripe Idempotent Requests is 100% data-driven and passes all 4 gates."""
    doc_path = REPO_DIR / "examples" / "docs" / "stripe_idempotency.md"
    assert doc_path.exists(), f"Missing {doc_path}"

    sources = [{"url": "https://docs.stripe.com/api/idempotent_requests", "local_file": str(doc_path), "title": "Stripe Idempotency Docs"}]
    project_profile = {
        "product": "Stripe API",
        "topic": "Stripe API Idempotent Requests & Safe Retries",
        "duration_target_seconds": 30,
    }

    pack = extract_evidence_pack(sources, project_profile=project_profile, mock=True)
    assert len(pack.records) >= 3

    wf_res = select_best_workflow(pack, project_profile=project_profile, mock=True)
    plan = plan_scenes(wf_res.selected_workflow, pack, duration_target=30)

    assert len(plan.scenes) == 5
    code_scene = plan.scenes[1]
    assert code_scene.code is not None
    assert "idempotencyKey" in code_scene.code
    assert code_scene.highlight_lines is not None and len(code_scene.highlight_lines) > 0

    val_report = validate_evidence_and_plan(pack, plan)
    assert val_report.passed, f"Validation failed: {val_report.checks}"


def test_planner_generality_arbitrary_new_product():
    """Verify scene planning works on an arbitrary third product with zero hardcoding."""
    raw_markdown = """# Acme Lock Service

Acme Lock is a distributed consensus primitive for atomic operations.

## Developer Action
To acquire a distributed lease safely, pass a lease duration to `lock.acquire("resource-id", 30)`.

```typescript
export async function updateResource(resId: string) {
  const lease = await lock.acquire(resId, 30);
  await lease.execute(async () => {
    return await database.write(resId);
  });
}
```

## Runtime Behavior & Guarantees
Acme Lock guarantees mutual exclusion across all distributed workers and automatically renews leases until the callback completes.

## Important Limitations
> [!WARNING]
> Expired leases cannot be reacquired until the TTL expires. Side effects inside lost leases must be cancelled immediately.
"""

    doc = SourceDocument(
        source_url="https://docs.acme.dev/locks",
        title="Acme Lock Documentation",
        retrieved_at="2026-10-21T00:00:00Z",
        content_hash="hash_acme",
        raw_content=raw_markdown,
    )

    pack = extract_evidence_offline([doc], project_name="Acme Lock")
    assert len(pack.records) >= 4

    wf_res = select_best_workflow(pack, project_profile={"product": "Acme Lock", "goal": "Demonstrate distributed locks"}, mock=True)
    plan = plan_scenes(wf_res.selected_workflow, pack, duration_target=30)

    assert len(plan.scenes) == 5
    val_report = validate_evidence_and_plan(pack, plan)
    assert val_report.passed, f"Validation failed: {val_report.checks}"


def test_first_class_release_diff_mode():
    """Verify first-class Release / Diff Mode ('What Changed in vX') with CodeTransformScene."""
    release_info = {
        "version_tag": "v2.0",
        "release_notes": "Migrate from callbacks to promises with durable checkpointing.",
        "before_code": "export function legacyTask(cb) {\n  client.run(cb);\n}",
        "after_code": "export async function modernTask() {\n  return await client.runAsync();\n}",
        "focus_phrase": "runAsync",
    }

    raw_doc = """# Acme SDK v2.0 Release Notes

Release v2.0: Migrate from callbacks to promises with durable checkpointing.

```typescript
export function legacyTask(cb) {
  client.run(cb);
}
```

```typescript
export async function modernTask() {
  return await client.runAsync();
}
```

## Important Limitations
> [!WARNING]
> Callbacks are deprecated in v2.0 and will throw an unhandled rejection error.
"""

    doc = SourceDocument(
        source_url="https://docs.acme.dev/release-v2",
        title="Acme SDK v2 Release",
        retrieved_at="2026-10-21T00:00:00Z",
        content_hash="hash_v2",
        raw_content=raw_doc,
    )

    pack = extract_evidence_offline([doc], project_name="Acme SDK")

    wf = WorkflowCandidate(
        id="wf_v2_migration",
        title="Acme SDK v2.0 Migration",
        description="Migrate from callbacks to promises with durable checkpointing.",
        problem_statement="Legacy callbacks risk unhandled error rejections.",
        implementation_summary="Use modern async/await with runAsync.",
        demonstration_behavior="Runtime automatically checkpoints promise resolution.",
        payoff="Zero unhandled callback rejections and clean async flow.",
        takeaway="Upgrade to v2.0 for promise-based durable workflows.",
        evidence_ids=[r.id for r in pack.records],
        code_snippet=release_info["after_code"],
        release=release_info,
        scores=WorkflowScore(
            supported_by_evidence=10.0,
            understandable_in_30s=9.0,
            visible_before_and_after=10.0,
            code_and_behavior_demonstrable=10.0,
            single_clear_takeaway=9.5,
            visual_story_works_without_long_prose=9.5,
            total_score=58.0,
        ),
    )

    plan = plan_scenes(wf, pack, duration_target=30)
    assert len(plan.scenes) == 5

    # Scene 1: Hook ("What Changed in v2.0")
    assert "v2.0" in plan.scenes[0].title or "What Changed" in plan.scenes[0].title

    # Scene 2: CodeTransformScene
    diff_scene = plan.scenes[1]
    assert diff_scene.visual_type == "code_transform"
    assert diff_scene.before_code is not None
    assert diff_scene.after_code is not None
    assert "client.run(cb);" in diff_scene.before_code
    assert "client.runAsync();" in diff_scene.after_code

    # Verify Gate 1-4 validation passes
    val_report = validate_evidence_and_plan(pack, plan)
    assert val_report.passed, f"Release diff validation failed: {val_report.checks}"


def test_planner_generality_resend_webhooks():
    """Verify scene planning for Resend Webhook Signatures is 100% data-driven and passes all 4 gates."""
    doc_path = REPO_DIR / "examples" / "docs" / "resend_webhooks.md"
    assert doc_path.exists(), f"Missing {doc_path}"

    sources = [{"url": "https://resend.com/docs/dashboard/webhooks/verify-webhooks", "local_file": str(doc_path), "title": "Resend Webhook Docs"}]
    project_profile = {
        "product": "Resend",
        "topic": "Resend Webhook Signature Verification & Security",
        "duration_target_seconds": 30,
    }

    pack = extract_evidence_pack(sources, project_profile=project_profile, mock=True)
    assert len(pack.records) >= 3

    wf_res = select_best_workflow(pack, project_profile=project_profile, mock=True)
    plan = plan_scenes(wf_res.selected_workflow, pack, duration_target=30)

    assert len(plan.scenes) == 5
    code_scene = plan.scenes[1]
    assert code_scene.code is not None
    assert "Webhook" in code_scene.code
    assert code_scene.highlight_lines is not None and len(code_scene.highlight_lines) > 0

    val_report = validate_evidence_and_plan(pack, plan)
    assert val_report.passed, f"Validation failed: {val_report.checks}"


