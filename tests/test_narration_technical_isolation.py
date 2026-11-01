"""Regression tests for Phase 3.9:
- Technical identifier isolation in narration (spoken_text vs displayed tokens)
- Markdown prose sanitization
- Dangling conjunction stripping in titles
- Deduplication between Scene 1 Hook and Scene 5 Takeaway
"""
import pytest
from engine.director.scene_planner import (
    strip_markdown_prose,
    derive_clean_title_from_claim,
    build_scene_plan_deterministic,
    DANGLING_CONJUNCTIONS,
)
from engine.director.workflow_selector import WorkflowCandidate, WorkflowScore
from engine.ingestion.evidence_extractor import EvidencePack, EvidenceRecord, SourceDocument


def test_strip_markdown_prose():
    assert strip_markdown_prose("## Failure Modes In Distributed Execution") == "Failure Modes In Distributed Execution"
    assert strip_markdown_prose("### Subheading with **bold text**") == "Subheading with bold text"
    assert strip_markdown_prose("- Bullet point item") == "Bullet point item"
    assert strip_markdown_prose("* Another bullet point") == "Another bullet point"
    assert strip_markdown_prose("Normal text with `code_identifier` inside") == "Normal text with code_identifier inside"


def test_derive_clean_title_from_claim_strips_dangling_conjunctions():
    # If title ends in a dangling conjunction with no following word, it must be stripped
    claim_ending_in_conj = "Durable Execution and"
    title1 = derive_clean_title_from_claim(claim_ending_in_conj, max_words=3)
    assert not any(title1.lower().endswith(f" {conj}") for conj in DANGLING_CONJUNCTIONS)
    assert not title1.endswith("&")
    assert title1 == "Durable Execution"

    # If title would be cut off at '&', it completes the phrase rather than leaving '&' hanging
    claim_with_ampersand = "Durable Execution & Memoization For Serverless Workflows"
    title2 = derive_clean_title_from_claim(claim_with_ampersand, max_words=3)
    assert not any(title2.lower().endswith(f" {conj}") for conj in DANGLING_CONJUNCTIONS)
    assert not title2.endswith("&")
    assert title2 == "Durable Execution & Memoization"


def test_scene_planner_preserves_technical_identifiers():
    """Verify that build_scene_plan_deterministic keeps technical identifiers intact
    in spoken_text and narration (e.g. step.run()) instead of prematurely phonetically
    corrupting them to 'step dot run'.
    """
    evidence_pack = EvidencePack(
        sources=[
            SourceDocument(
                source_url="https://example.com/docs/step-run",
                title="Step Run Documentation",
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="abc12345",
                raw_content="Step Run documentation text.",
            )
        ],
        records=[
            EvidenceRecord(
                id="ev_01",
                kind="behavior",
                claim="step.run() executes each step with automatic retries and memoization.",
                source_url="https://example.com/docs/step-run",
                source_section="Overview",
                excerpt="await step.run('my-step', async () => { return true; });",
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="hash1",
            ),
            EvidenceRecord(
                id="ev_02",
                kind="failure_behavior",
                claim="Without durable execution, network drops cause duplicate operations.",
                source_url="https://example.com/docs/step-run",
                source_section="Failures",
                excerpt="Network drops result in duplicate charges.",
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="hash2",
            ),
            EvidenceRecord(
                id="ev_03",
                kind="code_evidence",
                claim="A complete step.run() example.",
                source_url="https://example.com/docs/step-run",
                source_section="Example",
                excerpt="""export const myFn = inngest.createFunction(
  { id: "charge-user" },
  { event: "order.created" },
  async ({ event, step }) => {
    return await step.run("charge", async () => {
      return await paymentGateway.charge({ amount: 100 });
    });
  }
);""",
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="hash3",
            ),
            EvidenceRecord(
                id="ev_04",
                kind="limitation",
                claim="Return values must be JSON serializable.",
                source_url="https://example.com/docs/step-run",
                source_section="Limitations",
                excerpt="Return values must be JSON serializable.",
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="hash4",
            ),
        ],
    )

    workflow = WorkflowCandidate(
        id="developer_workflow_explainer",
        title="Durable Execution with step.run()",
        description="Explain durable step execution",
        problem_statement="Network drops cause duplicate execution",
        implementation_summary="Wrap execution in step.run()",
        demonstration_behavior="Retries with memoization",
        payoff="Guaranteed once-only execution",
        takeaway="Durable execution with memoized steps.",
        evidence_ids=["ev_01", "ev_02", "ev_03", "ev_04"],
        scores=WorkflowScore(
            supported_by_evidence=10,
            understandable_in_30s=10,
            visible_before_and_after=10,
            code_and_behavior_demonstrable=10,
            single_clear_takeaway=10,
            visual_story_works_without_long_prose=10,
            total_score=60,
        ),
    )

    plan = build_scene_plan_deterministic(
        workflow=workflow,
        evidence_pack=evidence_pack,
        duration_target=30,
    )

    assert len(plan.scenes) == 5

    # Scene 2 (Code Reveal) should retain step.run() in spoken_text and narration
    scene_2 = plan.scenes[1]
    assert "step.run" in scene_2.spoken_text or "step.run()" in scene_2.spoken_text
    assert "step dot run" not in scene_2.spoken_text
    assert "step dot run" not in scene_2.narration_segments[0].text

    # Scene 1 (Hook) should NOT have raw markdown '##'
    scene_1 = plan.scenes[0]
    for item in scene_1.items:
        assert not item.get("detail", "").startswith("##")
        assert not item.get("title", "").startswith("##")

    # Scene 5 (Takeaway) should NOT duplicate Scene 1's claim
    scene_5 = plan.scenes[4]
    assert scene_5.title != scene_1.title
    assert scene_5.spoken_text != scene_1.spoken_text
    assert scene_5.spoken_text.endswith("Check the official docs to get started.")


def test_scene_planner_and_captions_for_step_run_narration():
    """Regression test for Phase 3.9.1 (Task 1):
    Ensure that 'wrap your operation in await step.run(...)' is cleaned so:
    - Narration reads naturally: 'wrap your operation in step.run().'
    - Technical focus identifier is 'step.run' (not generic keyword 'await').
    - Caption chunks cleanly split at clause boundary and do NOT concatenate
      incompatible fragments such as 'OPERATION IN AWAIT step.run().'.
    """
    from engine.audio.tts_whisper import prepare_tts_text_with_token_map, collapse_spoken_word_boundaries
    from engine.timeline.timeline_mapper import chunk_caption_words

    evidence_pack = EvidencePack(
        sources=[
            SourceDocument(
                source_url="https://example.com/docs/step-run",
                title="Step Run Documentation",
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="abc12345",
                raw_content="Step Run documentation text.",
            )
        ],
        records=[
            EvidenceRecord(
                id="ev_01",
                kind="behavior",
                claim="step.run() executes each step with automatic retries and memoization.",
                source_url="https://example.com/docs/step-run",
                source_section="Overview",
                excerpt="await step.run('my-step', async () => { return true; });",
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="hash1",
            ),
            EvidenceRecord(
                id="ev_02",
                kind="developer_action",
                claim='To execute synchronous or asynchronous operations durably, wrap your operation in await step.run("step-id", async () => { ... })',
                source_url="https://example.com/docs/step-run",
                source_section="Definition and Syntax",
                excerpt='To execute synchronous or asynchronous operations durably, wrap your operation in `await step.run("step-id", async () => { ... })`.',
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="hash2",
            ),
            EvidenceRecord(
                id="ev_03",
                kind="code_evidence",
                claim="A complete step.run() example.",
                source_url="https://example.com/docs/step-run",
                source_section="Example",
                excerpt="""export const processOrder = inngest.createFunction(
  { id: "process-order" },
  { event: "order.created" },
  async ({ event, step }) => {
    const billing = await step.run("fetch-billing-data", async () => {
      return await getBillingAccount(event.data.customerId);
    });
    return { status: "completed" };
  }
);""",
                retrieved_at="2026-10-25T00:00:00Z",
                content_hash="hash3",
            ),
        ],
    )

    workflow = WorkflowCandidate(
        id="developer_workflow_explainer",
        title="Durable Execution with step.run()",
        description="Explain durable step execution",
        problem_statement="Network drops cause duplicate execution",
        implementation_summary="Wrap execution in step.run()",
        demonstration_behavior="Retries with memoization",
        payoff="Guaranteed once-only execution",
        takeaway="Durable execution with memoized steps.",
        evidence_ids=["ev_01", "ev_02", "ev_03"],
        scores=WorkflowScore(
            supported_by_evidence=10,
            understandable_in_30s=10,
            visible_before_and_after=10,
            code_and_behavior_demonstrable=10,
            single_clear_takeaway=10,
            visual_story_works_without_long_prose=10,
            total_score=60,
        ),
    )

    plan = build_scene_plan_deterministic(
        workflow=workflow,
        evidence_pack=evidence_pack,
        duration_target=30,
    )

    scene_2 = plan.scenes[1]
    # 1. Narration should say 'wrap your operation in step.run().' without awkward 'in await'
    assert "wrap your operation in step.run()." in scene_2.spoken_text
    assert "in await" not in scene_2.spoken_text

    # 2. Focus token should be 'step.run', not generic 'await'
    assert scene_2.focus_phrase == "step.run"
    assert scene_2.emphasis_word == "step.run"

    # 3. Spoken text preparation
    spoken_text, mappings = prepare_tts_text_with_token_map(scene_2.spoken_text)
    assert "step dot run" in spoken_text
    assert "step.run()." in [m["display_word"] for m in mappings]

    # 4. Collapse word events
    raw_events = [
        {"word": "To", "start": 0.0, "end": 0.2},
        {"word": "execute", "start": 0.21, "end": 0.5},
        {"word": "synchronous", "start": 0.51, "end": 0.9},
        {"word": "or", "start": 0.91, "end": 1.0},
        {"word": "asynchronous", "start": 1.01, "end": 1.5},
        {"word": "operations", "start": 1.51, "end": 1.9},
        {"word": "durably", "start": 1.91, "end": 2.3},
        {"word": "wrap", "start": 2.4, "end": 2.6},
        {"word": "your", "start": 2.61, "end": 2.8},
        {"word": "operation", "start": 2.81, "end": 3.2},
        {"word": "in", "start": 3.21, "end": 3.4},
        {"word": "step", "start": 3.41, "end": 3.7},
        {"word": "dot", "start": 3.71, "end": 3.9},
        {"word": "run", "start": 3.91, "end": 4.2},
    ]
    collapsed = collapse_spoken_word_boundaries(raw_events, mappings)
    assert any(c["word"] == "step.run()." for c in collapsed)

    # 5. Caption chunking must NOT produce 'operation in await step.run().'
    chunks = chunk_caption_words(collapsed)
    chunk_texts = [c["text"] for c in chunks]
    assert not any("in await" in t.lower() for t in chunk_texts)
    assert not any("operation in await" in t.lower() for t in chunk_texts)
    # The last chunk should be the clean main clause
    assert chunk_texts[-1] == "wrap your operation in step.run()."

