"""tests/test_evidence_validator_correctness.py

Exhaustive correctness test suite for evidence validation, provenance integrity,
numeric precision, semantic polarity, and limitation relevance:

1. Supported claims & metrics pass validation.
2. Unsupported number (e.g. 999 in narration) fails validation.
3. Number in unrelated evidence elsewhere in pack does NOT substantiate scene claim.
4. Exact number matching: '2' is rejected when evidence only contains '20'.
5. Semantic contradiction rejection:
   - 'always retry' vs 'never retry'
   - 'automatic retry' vs 'manual retry'
   - 'is idempotent' vs 'non-idempotent'
6. Relevant limitation omitted fails Gate 3/4.
7. Unrelated limitation in large pack does not fail validation.
8. Unresolved/uncertain limitation relevance sets needs_review=True and passed=False.
9. Missing or invalid evidence reference fails Gate 1.
10. Prerecorded fixture artifact claiming observed_capture is rejected by Gate 1 provenance check.
11. Genuine observed_execution artifact (is_fixture=False) with observed_capture passes Gate 1.
"""

import pytest
from engine.validation.evidence_validator import validate_evidence_and_plan
from engine.ingestion.evidence_extractor import (
    EvidencePack,
    EvidenceRecord,
    ExecutionArtifact,
    SourceDocument,
)


@pytest.fixture
def base_evidence_pack():
    return {
        "project": "Acme Gateway",
        "sources": [{"source_url": "https://docs.acme.com/api", "title": "Acme API Docs"}],
        "records": [
            {
                "id": "ev_01",
                "kind": "concept",
                "claim": "The checkout service processes credit card charges with 3 retries on network failure.",
                "source_url": "https://docs.acme.com/api",
                "source_section": "Retries",
                "excerpt": "The checkout service processes credit card charges with 3 retries on network failure.",
                "confidence": "source_supported",
            },
            {
                "id": "ev_code",
                "kind": "code_evidence",
                "claim": "Charge function implementation",
                "source_url": "https://docs.acme.com/api",
                "source_section": "Code",
                "excerpt": "export const charge = async (amount: number) => {\n  return await gateway.post('/charge', { amount });\n};",
                "code_evidence": "export const charge = async (amount: number) => {\n  return await gateway.post('/charge', { amount });\n};",
                "confidence": "source_supported",
            },
        ],
        "execution_artifacts": [],
    }


def test_supported_claims_and_metrics_pass(base_evidence_pack):
    """1. Verify that valid scenes with accurate numbers, code, and cited claims pass validation."""
    plan = {
        "title": "Acme Gateway Payment Retries",
        "topic": "Payment Retries",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Charge Function Implementation",
                "visual_type": "code_reveal",
                "evidence_ids": ["ev_code"],
                "code": "export const charge = async (amount: number) => {\n  return await gateway.post('/charge', { amount });\n};",
                "spoken_text": "Here is the charge function implementation.",
            },
            {
                "scene_id": 2,
                "title": "Credit Card Charges",
                "visual_type": "bento_grid",
                "evidence_ids": ["ev_01"],
                "spoken_text": "The checkout service allows 3 retries on network failure.",
                "items": [
                    {
                        "title": "Checkout Service",
                        "value": "3",
                        "subtitle": "retries on network failure",
                        "evidence_id": "ev_01",
                    }
                ],
            },
        ],
    }

    report = validate_evidence_and_plan(base_evidence_pack, plan)
    assert report.passed, f"Validation unexpectedly failed: {report.checks}"
    assert report.claim_coverage_pct == 100.0
    assert len(report.unsupported_numbers) == 0
    assert not report.needs_review


def test_unsupported_number_fails(base_evidence_pack):
    """2. Verify that an unsupported number (999) in narration fails validation."""
    plan = {
        "title": "Acme Gateway Payment Retries",
        "topic": "Payment Retries",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Credit Card Charges",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_01"],
                "spoken_text": "The checkout service performs 999 retries before giving up.",
            }
        ],
    }

    report = validate_evidence_and_plan(base_evidence_pack, plan)
    assert not report.passed
    assert any("999" in err for err in report.unsupported_numbers)


def test_number_in_unrelated_evidence_does_not_substantiate_scene(base_evidence_pack):
    """3. Verify that a number in an unrelated record in the pack cannot substantiate an uncited scene claim."""
    # Add unrelated record with number '42'
    base_evidence_pack["records"].append({
        "id": "ev_unrelated",
        "kind": "metric",
        "claim": "Maximum pool concurrency is 42 workers.",
        "source_url": "https://docs.acme.com/api",
        "source_section": "Concurrency",
        "excerpt": "Maximum pool concurrency is 42 workers.",
        "confidence": "source_supported",
    })

    # Scene 1 cites ONLY ev_01 (which mentions '3', but NOT '42')
    plan = {
        "title": "Acme Gateway Payment Retries",
        "topic": "Payment Retries",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Credit Card Charges",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_01"],  # Does NOT cite ev_unrelated
                "spoken_text": "The checkout service allocates 42 workers for retrying charges.",
            }
        ],
    }

    report = validate_evidence_and_plan(base_evidence_pack, plan)
    assert not report.passed
    assert any("42" in err for err in report.unsupported_numbers)


def test_exact_number_matching_rejects_partial_substring(base_evidence_pack):
    """4. Verify strict token matching: '2' is rejected when cited evidence only contains '20'."""
    pack = {
        "project": "Acme Gateway",
        "sources": [{"source_url": "https://docs.acme.com/api", "title": "Acme Docs"}],
        "records": [
            {
                "id": "ev_timeout",
                "kind": "concept",
                "claim": "The gateway limits operations to 20 seconds.",
                "source_url": "https://docs.acme.com/api",
                "source_section": "Limits",
                "excerpt": "The gateway limits operations to 20 seconds.",
                "confidence": "source_supported",
            }
        ],
        "execution_artifacts": [],
    }

    plan = {
        "title": "Acme Gateway Timeout",
        "topic": "Gateway Limits",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Gateway Limits",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_timeout"],
                # Narration claims '2' seconds, but evidence states '20' seconds
                "spoken_text": "The gateway limits operations to 2 seconds.",
            }
        ],
    }

    report = validate_evidence_and_plan(pack, plan)
    assert not report.passed
    assert any("unverified number '2'" in err for err in report.unsupported_numbers)


@pytest.mark.parametrize(
    "claim_narration,evidence_excerpt,contradiction_key",
    [
        ("The system will always retry failed webhooks.", "The system will never retry failed webhooks.", "always retry"),
        ("We configure automatic retry for all network calls.", "We enforce manual retry for all network calls.", "automatic retry"),
        ("The charge operation is idempotent and safe.", "The charge operation is non-idempotent and dangerous.", "is idempotent"),
    ],
)
def test_semantic_contradiction_rejection(claim_narration, evidence_excerpt, contradiction_key):
    """5. Verify rejection of polarity contradictions: 'always retry' vs 'never retry', etc."""
    pack = {
        "project": "Acme Gateway",
        "sources": [{"source_url": "https://docs.acme.com/api", "title": "Acme Docs"}],
        "records": [
            {
                "id": "ev_contra",
                "kind": "behavior",
                "claim": evidence_excerpt,
                "source_url": "https://docs.acme.com/api",
                "source_section": "Semantics",
                "excerpt": evidence_excerpt,
                "confidence": "source_supported",
            }
        ],
        "execution_artifacts": [],
    }

    plan = {
        "title": "Acme Semantics",
        "topic": "Semantics",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Webhook Handling",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_contra"],
                "spoken_text": claim_narration,
            }
        ],
    }

    report = validate_evidence_and_plan(pack, plan)
    assert not report.passed
    assert len(report.contradiction_errors) > 0
    assert any(contradiction_key in err for err in report.contradiction_errors)


def test_relevant_limitation_omitted_fails(base_evidence_pack):
    """6. Verify that omitting a relevant documented limitation fails Gate 3/4."""
    base_evidence_pack["records"].append({
        "id": "ev_lim_retry",
        "kind": "limitation",
        "claim": "Non-idempotent payment charges inside a retried callback execute more than once.",
        "source_url": "https://docs.acme.com/api",
        "source_section": "Retries",
        "excerpt": "Non-idempotent payment charges inside a retried callback execute more than once.",
        "confidence": "source_supported",
    })

    # The plan addresses "Payment Retries", which is directly relevant to ev_lim_retry,
    # but does NOT cite or display ev_lim_retry.
    plan = {
        "title": "Acme Gateway Payment Retries",
        "topic": "Payment Retries",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Credit Card Charges",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_01"],
                "spoken_text": "The checkout service retries failed credit card charges.",
            }
        ],
    }

    report = validate_evidence_and_plan(base_evidence_pack, plan)
    assert not report.passed
    assert any("Limitation record 'ev_lim_retry' is relevant" in err for err in report.gate3_errors)


def test_unrelated_limitation_in_large_pack_does_not_fail():
    """7. Generality check: an unrelated limitation in a large pack does not fail validation."""
    pack = {
        "project": "Stripe",
        "sources": [{"source_url": "https://stripe.com/docs", "title": "Stripe Docs"}],
        "records": [
            {
                "id": "ev_token",
                "kind": "concept",
                "claim": "Token creation generates a secure single-use payment credential.",
                "source_url": "https://stripe.com/docs",
                "source_section": "Tokens",
                "excerpt": "Token creation generates a secure single-use payment credential.",
                "confidence": "source_supported",
            },
            {
                "id": "ev_lim_unrelated",
                "kind": "limitation",
                "claim": "Webhooks require raw request payloads for HMAC SHA-256 signature verification.",
                "source_url": "https://stripe.com/docs",
                "source_section": "Webhooks",
                "excerpt": "Webhooks require raw request payloads for HMAC SHA-256 signature verification.",
                "confidence": "source_supported",
            },
        ],
        "execution_artifacts": [],
    }

    # The plan focuses strictly on Token Creation and does not touch Webhooks
    plan = {
        "title": "Stripe Token Creation",
        "topic": "Token Creation",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Single-Use Payment Credential",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_token"],
                "spoken_text": "Token creation generates a secure single-use payment credential.",
            }
        ],
    }

    report = validate_evidence_and_plan(pack, plan)
    assert report.passed
    assert len(report.gate3_errors) == 0
    assert not report.needs_review


def test_uncertain_limitation_relevance_sets_needs_review():
    """8. Verify that ambiguous/uncertain limitation relevance sets needs_review=True and passed=False."""
    pack = {
        "project": "Acme Auth",
        "sources": [{"source_url": "https://docs.acme.com", "title": "Acme Docs"}],
        "records": [
            {
                "id": "ev_session",
                "kind": "concept",
                "claim": "Session authentication verifies client bearer tokens.",
                "source_url": "https://docs.acme.com",
                "source_section": "Auth",
                "excerpt": "Session authentication verifies client bearer tokens.",
                "confidence": "source_supported",
            },
            {
                "id": "ev_lim_ambiguous",
                "kind": "limitation",
                # Contains exactly 1 overlapping topic term with the workflow context (e.g. 'tokens')
                "claim": "OAuth refresh tokens expire after ninety days of inactivity.",
                "source_url": "https://docs.acme.com",
                "source_section": "OAuth",
                "excerpt": "OAuth refresh tokens expire after ninety days of inactivity.",
                "confidence": "source_supported",
            },
        ],
        "execution_artifacts": [],
    }

    plan = {
        "title": "Client Session Verification",
        "topic": "Session Management",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Bearer Tokens",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_session"],
                "spoken_text": "Session authentication verifies client bearer tokens.",
            }
        ],
    }

    report = validate_evidence_and_plan(pack, plan)
    assert not report.passed
    assert report.needs_review is True
    assert len(report.review_reasons) > 0
    assert any("ev_lim_ambiguous" in r for r in report.review_reasons)


def test_missing_or_invalid_evidence_id_fails_gate1(base_evidence_pack):
    """9. Verify that citing a non-existent evidence ID fails Gate 1."""
    plan = {
        "title": "Acme Gateway Payment Retries",
        "topic": "Payment Retries",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Credit Card Charges",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_nonexistent_99"],
                "spoken_text": "We process payments with guaranteed durability.",
            }
        ],
    }

    report = validate_evidence_and_plan(base_evidence_pack, plan)
    assert not report.passed
    assert any("ev_nonexistent_99" in err for err in report.missing_evidence_ids)


def test_prerecorded_fixture_masquerading_as_observed_capture_rejected():
    """10. Verify that a prerecorded fixture artifact claiming observed_capture is rejected by Gate 1."""
    pack = {
        "project": "Acme CLI",
        "sources": [{"source_url": "https://docs.acme.com", "title": "Acme CLI"}],
        "records": [
            {
                "id": "ev_cli",
                "kind": "developer_action",
                "claim": "Deploy application using acme deploy.",
                "source_url": "https://docs.acme.com",
                "source_section": "CLI",
                "excerpt": "Deploy application using acme deploy.",
                "confidence": "source_supported",
            }
        ],
        "execution_artifacts": [
            {
                "artifact_id": "art_fixture_01",
                "command": "acme deploy",
                "provenance": "prerecorded_fixture",
                "is_fixture": True,
                "exit_code": 0,
                "stdout_preview": "Deployed successfully",
                "stderr_preview": "",
                "source_hash": "abc123hash",
                "artifact_hash": "def456hash",
            }
        ],
    }

    plan = {
        "title": "Acme CLI Deploy",
        "topic": "CLI Deployment",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Deploy Application",
                "visual_type": "terminal",
                "visual_representation": "observed_capture",
                "execution_artifact_id": "art_fixture_01",
                "evidence_ids": ["ev_cli"],
                "spoken_text": "Deploy application using acme deploy.",
            }
        ],
    }

    report = validate_evidence_and_plan(pack, plan)
    assert not report.passed
    assert len(report.provenance_errors) > 0
    assert any("Prerecorded fixtures cannot be accepted as live observed_execution" in err for err in report.provenance_errors)


def test_genuine_observed_execution_passes_gate1():
    """11. Verify that genuine observed_execution (is_fixture=False) passes Gate 1."""
    pack = {
        "project": "Acme CLI",
        "sources": [{"source_url": "https://docs.acme.com", "title": "Acme CLI"}],
        "records": [
            {
                "id": "ev_cli",
                "kind": "developer_action",
                "claim": "Deploy application using acme deploy.",
                "source_url": "https://docs.acme.com",
                "source_section": "CLI",
                "excerpt": "Deploy application using acme deploy.",
                "confidence": "source_supported",
                "provenance": "observed_execution",
                "execution_artifact_id": "art_live_01",
            }
        ],
        "execution_artifacts": [
            {
                "artifact_id": "art_live_01",
                "command": "acme deploy",
                "provenance": "observed_execution",
                "is_fixture": False,
                "exit_code": 0,
                "stdout_preview": "Deployed successfully in live sandbox",
                "stderr_preview": "",
                "source_hash": "abc123livehash",
                "artifact_hash": "def456livehash",
            }
        ],
    }

    plan = {
        "title": "Acme CLI Deploy",
        "topic": "CLI Deployment",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Deploy Application",
                "visual_type": "terminal",
                "visual_representation": "observed_capture",
                "execution_artifact_id": "art_live_01",
                "evidence_ids": ["ev_cli"],
                "spoken_text": "Deploy application using acme deploy.",
            }
        ],
    }

    report = validate_evidence_and_plan(pack, plan)
    assert report.passed, f"Validation failed: {report.checks}"
    assert len(report.provenance_errors) == 0


def test_unsupported_number_in_badge_fails(base_evidence_pack):
    """12. Verify that an unsupported number in a scene badge (string or dict) fails validation."""
    # String badge
    plan_str_badge = {
        "title": "Acme Gateway Payment Retries",
        "topic": "Payment Retries",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Credit Card Charges",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_01"],
                "badge": "99.9% RELIABILITY",  # 99.9% not in ev_01 (only mentions 3)
                "spoken_text": "The checkout service processes credit card charges.",
            }
        ],
    }
    report1 = validate_evidence_and_plan(base_evidence_pack, plan_str_badge)
    assert not report1.passed
    assert any("99.9%" in err for err in report1.unsupported_numbers)

    # Dict badge
    plan_dict_badge = {
        "title": "Acme Gateway Payment Retries",
        "topic": "Payment Retries",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Credit Card Charges",
                "visual_type": "fullscreen_text",
                "evidence_ids": ["ev_01"],
                "badge": {"text": "5 retries maximum", "type": "warning"},  # 5 not in ev_01
                "spoken_text": "The checkout service processes credit card charges.",
            }
        ],
    }
    report2 = validate_evidence_and_plan(base_evidence_pack, plan_dict_badge)
    assert not report2.passed
    assert any("5" in err for err in report2.unsupported_numbers)


def test_unsupported_number_in_labels_and_footer_fails(base_evidence_pack):
    """13. Verify that unsupported numbers in before/after labels or comparison_footer fail validation."""
    plan = {
        "title": "Charge Function Implementation",
        "topic": "Charge Function Implementation",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Charge Function Implementation",
                "visual_type": "code_transform",
                "evidence_ids": ["ev_code"],
                "before_label": "Legacy v1 (timeout: 500ms)",  # 500 not in ev_code
                "comparison_footer": "Target SLA: 99% uptime",  # 99% not in ev_code
                "spoken_text": "Here is the charge function implementation.",
            }
        ],
    }
    report = validate_evidence_and_plan(base_evidence_pack, plan)
    assert not report.passed
    assert any("500" in err for err in report.unsupported_numbers)
    assert any("99%" in err for err in report.unsupported_numbers)


def test_unsupported_number_in_card_tags_and_details_fails(base_evidence_pack):
    """14. Verify that unsupported numbers in card tags, subtitles, and details fail validation."""
    plan = {
        "title": "Acme Gateway Payment Retries",
        "topic": "Payment Retries",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Credit Card Charges",
                "visual_type": "bento_grid",
                "evidence_ids": ["ev_01"],
                "spoken_text": "The checkout service allows 3 retries on network failure.",
                "items": [
                    {
                        "title": "Checkout Service",
                        "value": "3",
                        "subtitle": "retries on network failure",
                        "tag": "10X RETRY POOL",  # 10 not in ev_01
                        "detail": "Allocates 50 threads",  # 50 not in ev_01
                        "evidence_id": "ev_01",
                    }
                ],
            }
        ],
    }
    report = validate_evidence_and_plan(base_evidence_pack, plan)
    assert not report.passed
    assert any("10" in err for err in report.unsupported_numbers)
    assert any("50" in err for err in report.unsupported_numbers)


def test_card_specific_evidence_id_isolation():
    """15. Verify that a card citing evidence_id A cannot use numbers from evidence_id B."""
    pack = {
        "project": "Acme Gateway",
        "sources": [{"source_url": "https://docs.acme.com", "title": "Acme Docs"}],
        "records": [
            {
                "id": "ev_retries",
                "kind": "concept",
                "claim": "The service performs 3 retries on transient errors.",
                "source_url": "https://docs.acme.com",
                "source_section": "Retries",
                "excerpt": "The service performs 3 retries on transient errors.",
                "confidence": "source_supported",
            },
            {
                "id": "ev_timeout",
                "kind": "concept",
                "claim": "Each attempt times out after 15 seconds.",
                "source_url": "https://docs.acme.com",
                "source_section": "Timeouts",
                "excerpt": "Each attempt times out after 15 seconds.",
                "confidence": "source_supported",
            },
        ],
        "execution_artifacts": [],
    }

    # Scene cites both ev_retries and ev_timeout
    # But Card 1 specifically cites ONLY ev_retries, yet claims '15 seconds'
    plan = {
        "title": "Acme Gateway Resilience",
        "topic": "Gateway Resilience",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Gateway Resilience",
                "visual_type": "bento_grid",
                "evidence_ids": ["ev_retries", "ev_timeout"],
                "spoken_text": "We configure retries and timeouts.",
                "items": [
                    {
                        "title": "Retry Policy",
                        "value": "15",  # 15 belongs to ev_timeout, NOT ev_retries!
                        "subtitle": "Max attempt duration",
                        "evidence_id": "ev_retries",
                    }
                ],
            }
        ],
    }

    report = validate_evidence_and_plan(pack, plan)
    assert not report.passed
    assert any("card_1_value" in err and "15" in err for err in report.unsupported_numbers)


def test_code_syntax_and_metadata_not_flagged_as_unsupported_numbers():
    """16. Verify that code syntax, scene IDs, durations, and timestamps are not flagged as factual metrics."""
    pack = {
        "project": "Acme Gateway",
        "sources": [{"source_url": "https://docs.acme.com/api", "title": "Acme API Docs"}],
        "records": [
            {
                "id": "ev_code",
                "kind": "code_evidence",
                "claim": "Charge function implementation",
                "source_url": "https://docs.acme.com/api",
                "source_section": "Code",
                "excerpt": "export const charge = async (amount: number) => {\n  const timeout = 5000;\n  return await gateway.post('/charge', { amount });\n};",
                "code_evidence": "export const charge = async (amount: number) => {\n  const timeout = 5000;\n  return await gateway.post('/charge', { amount });\n};",
                "confidence": "source_supported",
            }
        ],
        "execution_artifacts": [],
    }
    plan = {
        "title": "Charge Function Implementation",
        "topic": "Charge Function Implementation",
        "scenes": [
            {
                "scene_id": 2,  # '2' as scene_id
                "title": "Charge Function Implementation",
                "visual_type": "code_reveal",
                "evidence_ids": ["ev_code"],
                "code": "export const charge = async (amount: number) => {\n  const timeout = 5000;\n  return await gateway.post('/charge', { amount });\n};",
                "spoken_text": "Here is the charge function implementation.",
                "start_time": 0.0,
                "end_time": 30.0,
                "duration": 30.0,
            }
        ],
    }

    report = validate_evidence_and_plan(pack, plan)
    # The '5000' in code and '2' in scene_id must NOT be flagged as unsupported numbers
    assert report.passed, f"Validation failed: {report.checks}"
    assert len(report.unsupported_numbers) == 0

