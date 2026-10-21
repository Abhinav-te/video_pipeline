"""tests/test_validator_moat.py

Behavioral Test Suite for the 4-Gate Validator Moat:
Gate 1: Contiguous Code Equality, balanced delimiters, zero markdown fences.
Gate 2: Quote / Paraphrase Check (>= 0.35 normalized content-word overlap).
Gate 3: Limitation Gate (actual warning verbatim/paraphrase, reject 'GUARDED').
Gate 4: Component Literal Lint (no hardcoded banned strings in video components).
"""

import pytest
from engine.validation.evidence_validator import (
    validate_evidence_and_plan,
    lint_component_literals,
    GATE4_BANNED_LITERALS,
)


@pytest.fixture
def sample_evidence_pack():
    return {
        "project": "Test Product",
        "sources": [{"source_url": "https://docs.example.com", "title": "Example Docs"}],
        "records": [
            {
                "id": "ev_code_01",
                "kind": "code_evidence",
                "claim": "Sample API function definition",
                "source_url": "https://docs.example.com",
                "source_section": "API Reference",
                "excerpt": "export const processPayment = async (orderId: string) => {\n  return await gateway.charge(orderId);\n};",
                "retrieved_at": "2026-10-21T00:00:00Z",
                "content_hash": "hash_01",
                "confidence": "source_supported",
                "code_evidence": "export const processPayment = async (orderId: string) => {\n  return await gateway.charge(orderId);\n};",
            },
            {
                "id": "ev_beh_01",
                "kind": "behavior",
                "claim": "The payment gateway reuses cached response payloads on network retry.",
                "source_url": "https://docs.example.com",
                "source_section": "Idempotency",
                "excerpt": "The payment gateway reuses cached response payloads on network retry.",
                "retrieved_at": "2026-10-21T00:00:00Z",
                "content_hash": "hash_02",
                "confidence": "source_supported",
            },
            {
                "id": "ev_lim_01",
                "kind": "limitation",
                "claim": "Non-idempotent side effects inside a retried step can execute more than once.",
                "source_url": "https://docs.example.com",
                "source_section": "Important Limitations",
                "excerpt": "Non-idempotent side effects inside a retried step can execute more than once.",
                "retrieved_at": "2026-10-21T00:00:00Z",
                "content_hash": "hash_03",
                "confidence": "source_supported",
            },
        ],
    }


def test_gate1_valid_contiguous_substring_passes(sample_evidence_pack):
    """Verify that displayed code matching a source code_evidence substring passes Gate 1."""
    plan = {
        "title": "Payment Processing",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Sample API Function",
                "visual_type": "code_reveal",
                "evidence_ids": ["ev_code_01"],
                "code": "export const processPayment = async (orderId: string) => {\n  return await gateway.charge(orderId);\n};",
            },
            {
                "scene_id": 2,
                "title": "Payment Gateway Reuses Cached Response",
                "visual_type": "bento_grid",
                "evidence_ids": ["ev_beh_01", "ev_lim_01"],
                "items": [
                    {
                        "title": "CACHED RESPONSE",
                        "value": "REUSED",
                        "subtitle": "Payment gateway reuses cached response payloads on network retry",
                        "evidence_id": "ev_beh_01",
                    },
                    {
                        "title": "NON-IDEMPOTENT SIDE EFFECTS",
                        "value": "CONSTRAINT",
                        "subtitle": "Non-idempotent side effects inside a retried step can execute more than once",
                        "evidence_id": "ev_lim_01",
                    },
                ],
            },
        ],
    }

    report = validate_evidence_and_plan(sample_evidence_pack, plan)
    assert report.passed, f"Validation failed: {report.checks}"
    assert len(report.gate1_errors) == 0


def test_gate1_unbalanced_delimiters_fails(sample_evidence_pack):
    """Verify that displayed code with unbalanced delimiters fails Gate 1."""
    plan = {
        "title": "Payment Processing",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Sample API Function",
                "visual_type": "code_reveal",
                "evidence_ids": ["ev_code_01"],
                "code": "export const processPayment = async (orderId: string) => {\n  return await gateway.charge(orderId);\n", # Missing };
            },
        ],
    }

    report = validate_evidence_and_plan(sample_evidence_pack, plan)
    assert not report.passed
    assert any("unbalanced delimiters" in err for err in report.gate1_errors)


def test_gate1_fences_in_code_fails(sample_evidence_pack):
    """Verify that displayed code with raw markdown fences fails Gate 1."""
    plan = {
        "title": "Payment Processing",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Sample API Function",
                "visual_type": "code_reveal",
                "evidence_ids": ["ev_code_01"],
                "code": "```typescript\nexport const processPayment = async (orderId: string) => {};\n```",
            },
        ],
    }

    report = validate_evidence_and_plan(sample_evidence_pack, plan)
    assert not report.passed
    assert any("raw markdown fences" in err for err in report.gate1_errors)


def test_gate2_quote_paraphrase_overlap_threshold(sample_evidence_pack):
    """Verify that on-screen copy with low content-word overlap (< 0.35) fails Gate 2."""
    plan = {
        "title": "Unrelated Topic",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Completely Hallucinated Title About Weather Systems",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_beh_01"],
            },
        ],
    }

    report = validate_evidence_and_plan(sample_evidence_pack, plan)
    assert not report.passed
    assert any("content-word overlap" in err for err in report.gate2_errors)


def test_gate3_limitation_rejects_guarded_placeholder(sample_evidence_pack):
    """Verify that using 'GUARDED' placeholder fails Gate 3."""
    plan = {
        "title": "Payment Processing",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Payment Gateway Reuses Cached Response",
                "visual_type": "bento_grid",
                "evidence_ids": ["ev_beh_01", "ev_lim_01"],
                "items": [
                    {
                        "title": "IDEMPOTENCY NUANCE",
                        "value": "GUARDED",  # Banned placeholder
                        "subtitle": "External side effects are guarded",
                        "evidence_id": "ev_lim_01",
                    },
                ],
            },
        ],
    }

    report = validate_evidence_and_plan(sample_evidence_pack, plan)
    assert not report.passed
    assert any("GUARDED" in err for err in report.gate3_errors)


def test_gate3_limitation_missing_fails(sample_evidence_pack):
    """Verify that omitting a documented limitation fails Gate 3."""
    plan = {
        "title": "Payment Processing",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Payment Gateway Reuses Cached Response",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_beh_01"], # ev_lim_01 not cited
            },
        ],
    }

    report = validate_evidence_and_plan(sample_evidence_pack, plan)
    assert not report.passed
    assert any("Limitation record" in err for err in report.gate3_errors)


def test_gate4_component_literal_lint():
    """Verify that all video/src/components/*.tsx files pass the component literal lint."""
    errors = lint_component_literals()
    assert len(errors) == 0, f"Component literal lint found forbidden strings: {errors}"


def test_evidence_corpus_does_not_contain_scene_code(sample_evidence_pack):
    """Verify the bug fix: scene code is never added to the evidence corpus to prevent hallucination bypass."""
    # Narration has number '9999' which only exists in scene's code, not in evidence pack
    plan = {
        "title": "Sample API Function",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Sample API Function",
                "visual_type": "code_reveal",
                "evidence_ids": ["ev_code_01"],
                "code": "const timeout = 9999;",
                "spoken_text": "We configure the timeout to 9999 milliseconds.",
            },
        ],
    }

    report = validate_evidence_and_plan(sample_evidence_pack, plan)
    # Must catch unsupported number '9999'
    assert any("9999" in num_err for num_err in report.unsupported_numbers)

