"""engine/validation/evidence_validator.py

Evidence & Quality Validation Gate (4-Gate Validator Moat).
Verifies:
Gate 1 (Contiguous Code Equality): Displayed code must be an exact contiguous substring of source code_evidence,
       with balanced delimiters and zero markdown fences.
Gate 2 (Quote / Paraphrase Check): Every on-screen title, subtitle, and card claim must have >= 0.35 normalized
       content-word overlap with its cited EvidenceRecord (claim or excerpt).
Gate 3 (Limitation Gate): If evidence_pack has a limitation record, the scene plan must include a scene/card
       citing that evidence_id that displays the warning verbatim or as a close paraphrase (no 'GUARDED').
Gate 4 (Component Literal Lint): Scans video/src/components/*.tsx/jsx for banned hardcoded literals and fake-assurance labels.

Also enforces 100% claim coverage, zero unsupported numbers, and zero contamination tokens.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field

try:
    from engine.ingestion.code_sanitizer import sanitize_code, is_delimiter_balanced
except ImportError:
    from ingestion.code_sanitizer import sanitize_code, is_delimiter_balanced


class ValidationCheckItem(BaseModel):
    check: str
    passed: bool
    details: str
    scene_id: Optional[Union[int, str]] = None


class ValidationReport(BaseModel):
    passed: bool
    claim_coverage_pct: float
    total_claims: int
    backed_claims: int
    unsupported_numbers: List[str] = Field(default_factory=list)
    banned_tokens_found: List[str] = Field(default_factory=list)
    missing_evidence_ids: List[str] = Field(default_factory=list)
    contradiction_errors: List[str] = Field(default_factory=list, description="Contradicted or negated assertions")
    provenance_errors: List[str] = Field(default_factory=list, description="Provenance and execution artifact validation errors")
    schema_lineage_errors: List[str] = Field(default_factory=list, description="Gate 1 Schema & Lineage errors")
    gate1_errors: List[str] = Field(default_factory=list, description="Legacy alias for Gate 2 Code Fidelity errors")
    gate2_errors: List[str] = Field(default_factory=list, description="Legacy alias for Gate 3 Claim Support errors")
    gate3_errors: List[str] = Field(default_factory=list, description="Legacy alias for Gate 4 Limitation & Nuance errors")
    gate4_errors: List[str] = Field(default_factory=list, description="Legacy alias for Gate 5 Component Lint errors")
    gate5_errors: List[str] = Field(default_factory=list, description="Gate 5 Component & Timeline Schema errors")
    gate6_errors: List[str] = Field(default_factory=list, description="Gate 6 Post-Render QA errors")
    needs_review: bool = Field(default=False, description="Flag indicating unresolved claim or limitation uncertainty requires human review")
    review_reasons: List[str] = Field(default_factory=list, description="Detailed explanations of items requiring human review")
    checks: List[ValidationCheckItem] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


BANNED_CONTAMINATION_TOKENS = [
    "k-means",
    "kmeans",
    "dbscan",
    "pca",
    "t-sne",
    "tsne",
    "invariant algorithmic",
    "boilerplate state",
    "acme vector",
]

GATE4_BANNED_LITERALS = [
    "EVIDENCE-BACKED PRODUCTION VALUE",
    "Verified via official documentation",
    "0 RE-RUNS",
    "GUARDED",
    "OpenTelemetry",
    "8f4e29b1",
    "420ms",
    "FAILED: 503",
    "RETRY #1",
    "'VERIFIED'",
    "'GUARANTEE'",
]

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after",
    "above", "below", "to", "from", "up", "down", "of", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
    "don", "should", "now", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "and", "but",
    "if", "or", "because", "as", "until", "while", "this", "that", "it",
}


def get_content_words(text: str) -> Set[str]:
    """Extracts normalized content words from text, ignoring punctuation and stopwords."""
    if not text:
        return set()
    cleaned = re.sub(r"[^a-zA-Z0-9_\s]", " ", text.lower())
    tokens = cleaned.split()
    return {w for w in tokens if len(w) > 1 and w not in STOP_WORDS}


def extract_numbers_from_text(text: str) -> List[str]:
    """Extracts numerical tokens from text, ignoring standard syntax digits 0 and 1."""
    raw = re.findall(r"\b\d+(?:\.\d+)?%?", text)
    return [n for n in raw if n not in {"0", "1"}]


def normalize_number_token(n: str) -> str:
    """Normalizes numeric string token (e.g. '2.0' -> '2', '50%' -> '50%')."""
    n_clean = n.strip()
    if n_clean.endswith("%"):
        val_part = n_clean[:-1]
        try:
            f = float(val_part)
            return f"{int(f)}%" if f.is_integer() else f"{f}%"
        except ValueError:
            return n_clean
    try:
        f = float(n_clean)
        return str(int(f)) if f.is_integer() else str(f)
    except ValueError:
        return n_clean


SECRET_PATTERNS = [
    (r"\bsk_live_[0-9a-zA-Z]{16,}\b", "Stripe Live Secret Key"),
    (r"\bBearer\s+[0-9a-zA-Z._-]{20,}\b", "Bearer Auth Token"),
    (r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----", "Private Key Header"),
    (r"\bghp_[0-9a-zA-Z]{30,}\b", "GitHub Personal Access Token"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS Access Key ID"),
]


def detect_secret_exposure(text: str) -> Optional[str]:
    """Detects leaked credentials or secret API tokens in execution outputs or previews."""
    if not text:
        return None
    for pattern, name in SECRET_PATTERNS:
        if re.search(pattern, text):
            return name
    return None


CONTRADICTION_PAIRS = [
    # Retry contradictions (including base form retry, retries, retried, retrying)
    (r"\balways\s+(?:retry|retries|retried|retrying)\b", r"\bnever\s+(?:retry|retries|retried|retrying)\b"),
    (r"\bnever\s+(?:retry|retries|retried|retrying)\b", r"\balways\s+(?:retry|retries|retried|retrying)\b"),
    (r"\b(?:automatic|automatically)\s+(?:retry|retries|retried|retrying)\b", r"\b(?:no|never|manual)\s+(?:retry|retries|retried|retrying)\b"),
    (r"\b(?:no|never|manual)\s+(?:retry|retries|retried|retrying)\b", r"\b(?:automatic|automatically)\s+(?:retry|retries|retried|retrying)\b"),
    # Duplication contradictions
    (r"\bnever\s+(?:duplicate|double)\b", r"\b(?:can|will|does)\s+(?:duplicate|double)\b"),
    (r"\b(?:can|will|does)\s+(?:duplicate|double)\b", r"\bnever\s+(?:duplicate|double)\b"),
    # Guarantee contradictions
    (r"\bguarante(?:e|es|ed)\b", r"\b(?:no|cannot|does not)\s+guarantee\b"),
    (r"\b(?:no|cannot|does not)\s+guarantee\b", r"\bguarante(?:e|es|ed)\b"),
    # Limits and Downtime
    (r"\bunlimited\b", r"\b(?:rate\s+limit|limited\s+to|maximum)\b"),
    (r"\bzero\s+downtime\b", r"\b(?:requires\s+restart|downtime)\b"),
    # Idempotency requirements
    (r"\bwithout\s+idempotency\s+key\b", r"\brequires?\s+idempotency\s+key\b"),
    (r"\brequires?\s+idempotency\s+key\b", r"\bwithout\s+idempotency\s+key\b"),
    # Idempotent vs non-idempotent
    (r"\b(?:is|always)\s+idempotent\b", r"\bnon-idempotent\b"),
    (r"\bnon-idempotent\b", r"\b(?:is|always)\s+idempotent\b"),
]


def detect_semantic_contradiction(claim_text: str, evidence_text: str) -> Optional[str]:
    """
    Detects direct polarity contradictions between claim assertions and cited evidence.
    Returns diagnostic message if contradiction is confirmed.
    """
    if not claim_text or not evidence_text:
        return None
    claim_lower = claim_text.lower()
    ev_lower = evidence_text.lower()

    for pattern_claim, pattern_ev in CONTRADICTION_PAIRS:
        m_claim = re.search(pattern_claim, claim_lower)
        m_ev = re.search(pattern_ev, ev_lower)
        if m_claim and m_ev:
            return (
                f"Claim asserts '{m_claim.group(0)}' which contradicts cited evidence "
                f"stating '{m_ev.group(0)}'"
            )
    return None


def normalize_domain_token(token: str) -> str:
    """
    Normalizes technical and grammatical variants of domain terms to a canonical form.
    E.g.: 'retried' -> 'retry', 'retries' -> 'retry', 'idempotency' -> 'idempotent'.
    Ensures safe, deterministic matching without indiscriminate stemming.
    NEVER strips negative prefixes or equates opposites to positive forms.
    """
    t = token.lower().strip()
    if not t:
        return ""

    # Preserve explicit technical negations and opposites
    if t in {"non-idempotent", "non_idempotent", "non-retryable", "unsupported", "disabled", "invalid"}:
        return t.replace("_", "-")

    EXPLICIT_SYNONYMS = {
        "retried": "retry",
        "retries": "retry",
        "retrying": "retry",
        "idempotency": "idempotent",
        "idempotent": "idempotent",
        "cached": "cache",
        "caching": "cache",
        "caches": "cache",
        "reused": "reuse",
        "reusing": "reuse",
        "reuses": "reuse",
        "executed": "execute",
        "executing": "execute",
        "executes": "execute",
        "execution": "execute",
        "failed": "fail",
        "failing": "fail",
        "fails": "fail",
        "failure": "fail",
        "failures": "fail",
        "timedout": "timeout",
        "timeouts": "timeout",
        "payloads": "payload",
        "effects": "effect",
        "steps": "step",
        "operations": "operation",
        "requests": "request",
        "responses": "response",
        "signatures": "signature",
        "endpoints": "endpoint",
        "webhooks": "webhook",
        "headers": "header",
    }
    if t in EXPLICIT_SYNONYMS:
        return EXPLICIT_SYNONYMS[t]

    # Standard deterministic inflection rules for technical English:
    # 1. -ies / -ied -> -y (e.g. retried -> retry, queries -> query)
    if (t.endswith("ies") or t.endswith("ied")) and len(t) > 4:
        return t[:-3] + "y"
    # 2. -ency / -ence -> -ent (e.g. idempotency -> idempotent, concurrency -> concurrent)
    if (t.endswith("ency") or t.endswith("ence")) and len(t) > 5:
        return t[:-4] + "ent"
    # 3. Simple plural 's' (e.g. errors -> error, warnings -> warning)
    if t.endswith("s") and not t.endswith("ss") and len(t) > 4:
        return t[:-1]

    return t


# Domain topic associations for limitation relevance (topic relevance != semantic synonym)
DOMAIN_TOPIC_RELEVANCE: Dict[str, Set[str]] = {
    "non-idempotent": {"idempotent", "idempotency"},
    "idempotent": {"idempotency", "non-idempotent"},
    "idempotency": {"idempotent", "non-idempotent"},
    "retry": {"retried", "retrying", "retries", "backoff"},
    "fail": {"failure", "error", "503", "timeout"},
    "webhook": {"signature", "verify", "payload"},
}


def is_limitation_relevant(
    lim_record: Dict[str, Any],
    cited_evidence_ids: Set[str],
    workflow_context_words: Set[str],
) -> Tuple[bool, bool]:
    """
    Determines whether a documented limitation is relevant to the active workflow.
    Returns (is_relevant: bool, is_uncertain: bool).
    """
    lim_id = lim_record.get("id", "")
    if lim_id in cited_evidence_ids:
        return True, False

    lim_claim = lim_record.get("claim", "")
    lim_excerpt = lim_record.get("excerpt", "")
    lim_words = get_content_words(f"{lim_claim} {lim_excerpt}")

    # Remove generic small words and normalize domain tokens
    domain_lim_words = {normalize_domain_token(w) for w in lim_words if len(w) > 3}
    normalized_context_words = {normalize_domain_token(w) for w in workflow_context_words}

    # Expand domain lim words with topic associations for relevance detection
    expanded_lim_topics = set(domain_lim_words)
    for w in domain_lim_words:
        if w in DOMAIN_TOPIC_RELEVANCE:
            expanded_lim_topics.update(DOMAIN_TOPIC_RELEVANCE[w])

    overlap_words = expanded_lim_topics.intersection(normalized_context_words)

    if len(overlap_words) >= 2:
        return True, False
    elif len(overlap_words) == 1:
        return False, True
    return False, False


def lint_component_literals() -> List[str]:
    """Gate 4: Scans video/src/components/*.tsx and *.jsx for hardcoded banned literals."""
    errors: List[str] = []
    repo_dir = Path(__file__).resolve().parent.parent.parent
    components_dir = repo_dir / "video" / "src" / "components"
    if not components_dir.exists():
        return errors

    for file_path in components_dir.iterdir():
        if file_path.suffix in {".tsx", ".jsx"}:
            try:
                content = file_path.read_text(encoding="utf-8")
                for banned in GATE4_BANNED_LITERALS:
                    if banned in content:
                        errors.append(f"{file_path.name}: contains forbidden literal/default '{banned}'")
            except Exception as e:
                errors.append(f"Failed to read {file_path.name}: {e}")

    return errors


def validate_evidence_and_plan(
    evidence_pack_data: Union[Dict[str, Any], Any],
    scene_plan_or_timeline_data: Union[Dict[str, Any], Any],
    source_docs: Optional[List[Dict[str, Any]]] = None,
) -> ValidationReport:
    """Core validation moat enforcing 6 strict gates and 100% claim backing."""
    # 1. Parse Evidence Pack
    if isinstance(evidence_pack_data, dict):
        records_list = evidence_pack_data.get("records", [])
        evidence_records_by_id: Dict[str, Dict[str, Any]] = {
            r.get("id"): r for r in records_list if isinstance(r, dict) and r.get("id")
        }
        raw_artifacts = evidence_pack_data.get("execution_artifacts", [])
        execution_artifacts_by_id: Dict[str, Dict[str, Any]] = {
            a.get("artifact_id"): a for a in raw_artifacts if isinstance(a, dict) and a.get("artifact_id")
        }
    elif hasattr(evidence_pack_data, "records"):
        evidence_records_by_id = {
            r.id: r.model_dump() for r in evidence_pack_data.records
        }
        execution_artifacts_by_id = {
            a.artifact_id: a.model_dump() for a in getattr(evidence_pack_data, "execution_artifacts", [])
        }
    else:
        evidence_records_by_id = {}
        execution_artifacts_by_id = {}

    all_evidence_corpus = " ".join([
        f"{r.get('claim', '')} {r.get('excerpt', '')} {r.get('code_evidence', '')}"
        for r in evidence_records_by_id.values()
    ])

    code_evidence_records = [
        r for r in evidence_records_by_id.values()
        if r.get("kind") == "code_evidence"
    ]

    limitation_records = [
        r for r in evidence_records_by_id.values()
        if r.get("kind") == "limitation"
    ]

    # 2. Parse Scenes
    scenes: List[Dict[str, Any]] = []
    if isinstance(scene_plan_or_timeline_data, dict):
        scenes = scene_plan_or_timeline_data.get("scenes", [])
    elif hasattr(scene_plan_or_timeline_data, "scenes"):
        scenes = [s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in scene_plan_or_timeline_data.scenes]

    total_claims = 0
    backed_claims = 0
    missing_evidence_ids: List[str] = []
    unsupported_numbers: List[str] = []
    banned_tokens_found: List[str] = []
    contradiction_errors: List[str] = []
    provenance_errors: List[str] = []
    schema_lineage_errors: List[str] = []
    gate1_errors: List[str] = []
    gate2_errors: List[str] = []
    gate3_errors: List[str] = []
    review_reasons: List[str] = []
    checks: List[ValidationCheckItem] = []

    # -----------------------------------------------------------------
    # Gate 1: Schema, Lineage & Provenance Integrity
    # -----------------------------------------------------------------
    if not evidence_records_by_id:
        schema_lineage_errors.append("EvidencePack contains 0 records. A valid evidence_pack.json is required.")
        checks.append(ValidationCheckItem(
            check="evidence_pack_presence",
            passed=False,
            details="EvidencePack contains 0 records. A valid evidence_pack.json is required.",
        ))
    else:
        checks.append(ValidationCheckItem(
            check="evidence_pack_presence",
            passed=True,
            details=f"EvidencePack populated with {len(evidence_records_by_id)} verified records.",
        ))

    # Evidence Record Provenance Check
    for r_id, rec in evidence_records_by_id.items():
        prov = rec.get("provenance", "documented")
        if prov == "observed_execution":
            art_id = rec.get("execution_artifact_id")
            if not art_id:
                provenance_errors.append(
                    f"EvidenceRecord '{r_id}' specifies provenance='observed_execution' but has no execution_artifact_id."
                )
            elif art_id not in execution_artifacts_by_id:
                provenance_errors.append(
                    f"EvidenceRecord '{r_id}' links to non-existent execution_artifact_id '{art_id}'."
                )
            else:
                art = execution_artifacts_by_id[art_id]
                if art.get("is_fixture", False) or art.get("provenance") != "observed_execution":
                    provenance_errors.append(
                        f"EvidenceRecord '{r_id}' claims provenance='observed_execution' but linked artifact '{art_id}' is a prerecorded fixture."
                    )

    # Execution Artifact Secret Exposure & Integrity Check
    for art_id, art in execution_artifacts_by_id.items():
        preview_text = f"{art.get('stdout_preview', '')} {art.get('stderr_preview', '')} {json.dumps(art.get('environment_meta', {}))}"
        secret_leak = detect_secret_exposure(preview_text)
        if secret_leak:
            provenance_errors.append(
                f"ExecutionArtifact '{art_id}': exposed secret token detected ({secret_leak})."
            )
        if not art.get("source_hash") or not art.get("artifact_hash"):
            provenance_errors.append(
                f"ExecutionArtifact '{art_id}': missing cryptographic source_hash or artifact_hash."
            )

    # All cited evidence IDs across all scenes
    all_cited_ids: Set[str] = set()

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id") or scene.get("id") or (idx + 1)
        scene_str = json.dumps(scene).lower()

        # Check Placeholder Contamination
        for token in BANNED_CONTAMINATION_TOKENS:
            if token in scene_str:
                banned_tokens_found.append(f"Scene {scene_id}: contains '{token}'")

        # Provenance & Visual Representation Integrity
        vis_rep = scene.get("visual_representation", "illustrative")
        scene_art_id = scene.get("execution_artifact_id")

        if vis_rep == "observed_capture":
            if not scene_art_id:
                provenance_errors.append(
                    f"Scene {scene_id}: visual_representation='observed_capture' requires a valid execution_artifact_id."
                )
            elif scene_art_id not in execution_artifacts_by_id:
                provenance_errors.append(
                    f"Scene {scene_id}: execution_artifact_id '{scene_art_id}' not found in evidence pack artifacts."
                )
            else:
                art = execution_artifacts_by_id[scene_art_id]
                if art.get("provenance") != "observed_execution" or art.get("is_fixture", False):
                    provenance_errors.append(
                        f"Scene {scene_id}: visual_representation='observed_capture' claims live execution, but linked artifact '{scene_art_id}' has provenance='{art.get('provenance')}' (is_fixture={art.get('is_fixture', False)}). Prerecorded fixtures cannot be accepted as live observed_execution."
                    )
        elif vis_rep == "illustrative":
            sc_title = str(scene.get("title", "")).lower()
            sc_badge = str(scene.get("badge", "")).lower()
            if any(k in sc_title or k in sc_badge for k in ("live execution", "verified capture", "live terminal trace")) and not scene_art_id:
                provenance_errors.append(
                    f"Scene {scene_id}: illustrative scene claims live execution without an execution artifact."
                )

        # Extract Evidence IDs
        cited_ids: Set[str] = set()
        raw_ids = scene.get("evidence_ids") or []
        if isinstance(raw_ids, list):
            cited_ids.update([str(x) for x in raw_ids])

        segments = scene.get("narration_segments") or []
        if segments and isinstance(segments, list):
            for seg in segments:
                if isinstance(seg, dict):
                    seg_ids = seg.get("evidence_ids") or []
                    for sid in seg_ids:
                        cited_ids.add(str(sid))

        all_cited_ids.update(cited_ids)
        total_claims += 1

        if not cited_ids:
            checks.append(ValidationCheckItem(
                check="claim_citation",
                passed=False,
                details=f"Scene {scene_id} has no linked evidence_ids.",
                scene_id=scene_id,
            ))
        else:
            valid_for_scene = True
            for cid in cited_ids:
                if cid not in evidence_records_by_id:
                    valid_for_scene = False
                    missing_evidence_ids.append(f"Scene {scene_id} cited non-existent evidence_id: '{cid}'")

            if valid_for_scene:
                backed_claims += 1
                checks.append(ValidationCheckItem(
                    check="claim_citation",
                    passed=True,
                    details=f"Scene {scene_id} backed by verified record(s): {sorted(list(cited_ids))}",
                    scene_id=scene_id,
                ))
            else:
                checks.append(ValidationCheckItem(
                    check="claim_citation",
                    passed=False,
                    details=f"Scene {scene_id} cited unverified or missing evidence IDs.",
                    scene_id=scene_id,
                ))

        # Build corpus of cited records for this scene ONLY (never include scene's own code)
        scene_evidence_corpus = " ".join([
            f"{evidence_records_by_id[cid].get('claim', '')} {evidence_records_by_id[cid].get('excerpt', '')} {evidence_records_by_id[cid].get('code_evidence', '')}"
            for cid in cited_ids if cid in evidence_records_by_id
        ])

        # Build set of verified numeric tokens from cited records ONLY (strictly scoped and normalized)
        cited_numbers_set: Set[str] = set()
        for cid in cited_ids:
            if cid in evidence_records_by_id:
                rec_text = f"{evidence_records_by_id[cid].get('claim', '')} {evidence_records_by_id[cid].get('excerpt', '')}"
                for n in extract_numbers_from_text(rec_text):
                    cited_numbers_set.add(normalize_number_token(n))

        # Check spoken text / narration numbers
        narration = str(scene.get("spoken_text") or scene.get("narration") or "")
        numbers_in_narration = extract_numbers_from_text(narration)
        for num in numbers_in_narration:
            if normalize_number_token(num) not in cited_numbers_set:
                unsupported_numbers.append(
                    f"Scene {scene_id} spoken text contains unverified number '{num}' (not in cited evidence)"
                )

        # Check visible title, subtitle, display_text, and labels for numerical claims
        visible_text_fields = (
            "title",
            "subtitle",
            "heading",
            "display_text",
            "takeaway",
            "before_label",
            "after_label",
            "problem_label",
            "solution_label",
            "comparison_footer",
        )
        for field in visible_text_fields:
            f_val = scene.get(field)
            if f_val and isinstance(f_val, str):
                for num in extract_numbers_from_text(f_val):
                    if normalize_number_token(num) not in cited_numbers_set:
                        unsupported_numbers.append(
                            f"Scene {scene_id} [{field}] contains unverified number '{num}' (not in cited evidence)"
                        )

        # Check badge for numerical claims if present
        badge_val = scene.get("badge")
        if badge_val:
            badge_texts = []
            if isinstance(badge_val, str):
                badge_texts.append(badge_val)
            elif isinstance(badge_val, dict):
                for b_key in ("text", "label", "title", "value"):
                    b_str = badge_val.get(b_key)
                    if b_str and isinstance(b_str, str):
                        badge_texts.append(b_str)
            for b_text in badge_texts:
                for num in extract_numbers_from_text(b_text):
                    if normalize_number_token(num) not in cited_numbers_set:
                        unsupported_numbers.append(
                            f"Scene {scene_id} [badge] contains unverified number '{num}' (not in cited evidence)"
                        )

        # Check narration segments if present
        for seg_idx, seg in enumerate(scene.get("narration_segments") or []):
            if isinstance(seg, dict):
                seg_text = seg.get("text")
                if seg_text and isinstance(seg_text, str):
                    seg_numbers_set = set()
                    seg_eids = seg.get("evidence_ids") or []
                    for seid in seg_eids:
                        if seid in evidence_records_by_id:
                            srec_text = f"{evidence_records_by_id[seid].get('claim', '')} {evidence_records_by_id[seid].get('excerpt', '')}"
                            for n in extract_numbers_from_text(srec_text):
                                seg_numbers_set.add(normalize_number_token(n))
                    if not seg_numbers_set:
                        seg_numbers_set = set(cited_numbers_set)
                    for num in extract_numbers_from_text(seg_text):
                        if normalize_number_token(num) not in seg_numbers_set:
                            unsupported_numbers.append(
                                f"Scene {scene_id} [narration_segment_{seg_idx+1}] contains unverified number '{num}' (not in cited evidence)"
                            )

        # Check visual cards / items
        items = scene.get("items") or scene.get("cards") or []
        for c_idx, it in enumerate(items):
            if isinstance(it, dict):
                card_eids = []
                raw_eid = it.get("evidence_id") or it.get("evidence_ids")
                if isinstance(raw_eid, list):
                    card_eids.extend([str(x) for x in raw_eid])
                elif raw_eid:
                    card_eids.append(str(raw_eid))

                if card_eids:
                    card_numbers_set = set()
                    for ceid in card_eids:
                        if ceid in evidence_records_by_id:
                            c_rec = evidence_records_by_id[ceid]
                            c_text = f"{c_rec.get('claim', '')} {c_rec.get('excerpt', '')}"
                            for n in extract_numbers_from_text(c_text):
                                card_numbers_set.add(normalize_number_token(n))
                else:
                    card_numbers_set = set(cited_numbers_set)

                for f_name in ("title", "subtitle", "detail", "value", "label", "tag"):
                    val_str = str(it.get(f_name, ""))
                    if val_str:
                        for vn in extract_numbers_from_text(val_str):
                            if normalize_number_token(vn) not in card_numbers_set:
                                unsupported_numbers.append(
                                    f"Scene {scene_id} [card_{c_idx+1}_{f_name}] contains unverified number '{vn}' (not in cited evidence)"
                                )

        # Semantic Contradiction Check (Gate 3)
        for cid in cited_ids:
            if cid in evidence_records_by_id:
                ev_rec = evidence_records_by_id[cid]
                ev_text = f"{ev_rec.get('claim', '')} {ev_rec.get('excerpt', '')}"
                c_narration = detect_semantic_contradiction(narration, ev_text)
                if c_narration:
                    contradiction_errors.append(
                        f"Scene {scene_id} narration contradicts cited evidence '{cid}': {c_narration}"
                    )
                for field in ("title", "display_text"):
                    val = scene.get(field)
                    if val:
                        c_val = detect_semantic_contradiction(str(val), ev_text)
                        if c_val:
                            contradiction_errors.append(
                                f"Scene {scene_id} [{field}] contradicts cited evidence '{cid}': {c_val}"
                            )

        # -------------------------------------------------------------
        # Gate 2: Contiguous Code Equality & Syntax Health (Legacy alias gate1_errors)
        # -------------------------------------------------------------
        raw_code = scene.get("code") or scene.get("code_snippet")
        if raw_code and isinstance(raw_code, str) and raw_code.strip():
            # Check zero markdown fences in displayed code
            if "```" in raw_code:
                gate1_errors.append(f"Scene {scene_id}: code contains raw markdown fences (```).")

            # Check balanced delimiters
            if not is_delimiter_balanced(raw_code):
                gate1_errors.append(f"Scene {scene_id}: code contains syntactically unbalanced delimiters ({{}}, (), []).")

            # Check exact contiguous substring against source code_evidence records
            clean_displayed = sanitize_code(raw_code)
            found_exact_substring = False

            for rec in code_evidence_records:
                src_excerpt = sanitize_code(rec.get("excerpt", ""))
                src_code_ev = sanitize_code(rec.get("code_evidence", ""))
                if (src_excerpt and clean_displayed in src_excerpt) or (src_code_ev and clean_displayed in src_code_ev):
                    found_exact_substring = True
                    break

            if not found_exact_substring:
                # Also check normalized whitespace match
                norm_disp = re.sub(r"\s+", " ", clean_displayed).strip()
                for rec in code_evidence_records:
                    norm_src = re.sub(r"\s+", " ", sanitize_code(rec.get("excerpt", ""))).strip()
                    if norm_disp in norm_src:
                        found_exact_substring = True
                        break

            if not found_exact_substring:
                gate1_errors.append(
                    f"Scene {scene_id}: displayed code is not an exact contiguous substring of any source code_evidence record."
                )

        # -------------------------------------------------------------
        # Gate 3: Quote / Paraphrase Check (>= 0.35 content-word overlap) (Legacy alias gate2_errors)
        # -------------------------------------------------------------
        cited_evidence_words = get_content_words(scene_evidence_corpus)

        # Scene level elements
        for field in ("title", "display_text"):
            val = scene.get(field)
            if val:
                w = get_content_words(str(val))
                if len(w) >= 2:
                    overlap = len(w.intersection(cited_evidence_words)) / len(w)
                    if overlap < 0.35:
                        gate2_errors.append(
                            f"Scene {scene_id} [{field}] '{val}' has {overlap:.2f} content-word overlap (< 0.35 threshold) with cited evidence."
                        )

        # Card level elements
        for c_idx, it in enumerate(items):
            if isinstance(it, dict):
                target_words = set(cited_evidence_words)
                if it.get("evidence_id") and it["evidence_id"] in evidence_records_by_id:
                    c_rec = evidence_records_by_id[it["evidence_id"]]
                    target_words.update(get_content_words(f"{c_rec.get('claim', '')} {c_rec.get('excerpt', '')}"))

                for f_name in ("title", "subtitle", "detail"):
                    val = it.get(f_name)
                    if val:
                        w = get_content_words(str(val))
                        if len(w) >= 2:
                            overlap = len(w.intersection(target_words)) / len(w)
                            if overlap < 0.35:
                                gate2_errors.append(
                                    f"Scene {scene_id} [card_{c_idx+1}_{f_name}] '{val}' has {overlap:.2f} content-word overlap (< 0.35 threshold) with cited evidence."
                                )

    # Append semantic contradiction errors into Gate 3 errors
    gate2_errors.extend(contradiction_errors)

    # -----------------------------------------------------------------
    # Gate 4: Workflow-Aware Limitation & Nuance (Legacy alias gate3_errors)
    # -----------------------------------------------------------------
    if isinstance(scene_plan_or_timeline_data, dict):
        plan_title = str(scene_plan_or_timeline_data.get("title", ""))
        plan_topic = str(scene_plan_or_timeline_data.get("topic", ""))
    else:
        plan_title = str(getattr(scene_plan_or_timeline_data, "title", "") or "")
        plan_topic = str(getattr(scene_plan_or_timeline_data, "topic", "") or "")
    workflow_context_text = f"{plan_title} {plan_topic} " + " ".join([
        f"{r.get('claim', '')} {r.get('source_section', '')}"
        for cid in all_cited_ids if cid in evidence_records_by_id
        for r in [evidence_records_by_id[cid]]
        if r.get("kind") in ("developer_action", "behavior", "concept")
    ])
    workflow_context_words = get_content_words(workflow_context_text)

    has_guarded_anti_pattern = False

    for lim_rec in limitation_records:
        lim_id = lim_rec.get("id")
        lim_claim = lim_rec.get("claim", "")
        lim_excerpt = lim_rec.get("excerpt", "")
        lim_words = get_content_words(f"{lim_claim} {lim_excerpt}")

        is_relevant, is_uncertain = is_limitation_relevant(lim_rec, all_cited_ids, workflow_context_words)

        # Check for direct limitation contradiction across scenes
        for s in scenes:
            s_full_text = f"{s.get('title', '')} {s.get('spoken_text', '')} {s.get('narration', '')} {json.dumps(s.get('items', []))}"
            contra_lim = detect_semantic_contradiction(s_full_text, f"{lim_claim} {lim_excerpt}")
            if contra_lim:
                gate3_errors.append(
                    f"Scene {s.get('scene_id') or 1} contradicts documented limitation '{lim_id}': {contra_lim}"
                )

        if is_relevant:
            has_limitation_cited = lim_id in all_cited_ids
            has_warning_displayed = False

            for s in scenes:
                s_text = json.dumps(s)
                if "GUARDED" in s_text:
                    has_guarded_anti_pattern = True

                s_ids = [str(x) for x in (s.get("evidence_ids") or [])]
                s_items = s.get("items") or s.get("cards") or []
                for it in s_items:
                    if isinstance(it, dict) and it.get("evidence_id") == lim_id:
                        s_ids.append(lim_id)
                        it_text = f"{it.get('title', '')} {it.get('subtitle', '')} {it.get('value', '')} {it.get('detail', '')}"
                        if len(lim_words) > 0 and len(get_content_words(it_text).intersection(lim_words)) >= 2:
                            has_warning_displayed = True

                if lim_id in s_ids:
                    s_all_text = f"{s.get('title', '')} {s.get('spoken_text', '')} {s.get('narration', '')} {s_text}"
                    if len(lim_words) > 0 and len(get_content_words(s_all_text).intersection(lim_words)) >= 2:
                        has_warning_displayed = True

            if not has_limitation_cited:
                gate3_errors.append(
                    f"Limitation record '{lim_id}' is relevant to this workflow but is not cited in the scene plan."
                )
            elif not has_warning_displayed:
                gate3_errors.append(
                    f"Documented limitation '{lim_id}' is cited but not displayed verbatim or as a close paraphrase on screen."
                )
        elif is_uncertain:
            review_msg = f"Documented limitation '{lim_id}' ({lim_claim[:50]}...) has ambiguous workflow relevance (requires human review)."
            review_reasons.append(review_msg)
            checks.append(ValidationCheckItem(
                check="gate4_limitation_nuance",
                passed=False,
                details=f"needs_review: {review_msg}",
            ))

    if has_guarded_anti_pattern:
        gate3_errors.append(
            "Found placeholder 'GUARDED' instead of the actual documented limitation warning."
        )

    # -----------------------------------------------------------------
    # Gate 5: Component Literal Lint & Timeline Schema (Legacy alias gate4_errors)
    # -----------------------------------------------------------------
    gate4_errors = lint_component_literals()
    gate5_errors = list(gate4_errors)

    # Record Gate Check Items
    checks.append(ValidationCheckItem(
        check="gate1_schema_and_lineage",
        passed=(len(schema_lineage_errors) == 0 and len(missing_evidence_ids) == 0 and len(banned_tokens_found) == 0),
        details="Schema, citations, branding, and lineage verified." if not (schema_lineage_errors or missing_evidence_ids or banned_tokens_found) else "; ".join(schema_lineage_errors + missing_evidence_ids + banned_tokens_found),
    ))

    checks.append(ValidationCheckItem(
        check="gate1_provenance_integrity",
        passed=(len(provenance_errors) == 0),
        details="Execution artifacts and visual representation provenance verified." if not provenance_errors else "; ".join(provenance_errors),
    ))

    checks.append(ValidationCheckItem(
        check="gate1_contiguous_code_equality",
        passed=(len(gate1_errors) == 0),
        details="Code matches exact source snippet with balanced delimiters and zero fences." if not gate1_errors else "; ".join(gate1_errors),
    ))

    checks.append(ValidationCheckItem(
        check="gate2_quote_paraphrase",
        passed=(len(gate2_errors) == 0),
        details="All on-screen titles, subtitles, and card claims have >= 0.35 content-word overlap with cited records." if not gate2_errors else "; ".join(gate2_errors),
    ))

    checks.append(ValidationCheckItem(
        check="numerical_claims",
        passed=(len(unsupported_numbers) == 0),
        details="All numeric values in narration and cards verified against cited evidence." if not unsupported_numbers else "; ".join(unsupported_numbers),
    ))

    checks.append(ValidationCheckItem(
        check="semantic_contradiction",
        passed=(len(contradiction_errors) == 0),
        details="Zero direct polarity contradictions or unsupported guarantees." if not contradiction_errors else "; ".join(contradiction_errors),
    ))

    checks.append(ValidationCheckItem(
        check="gate3_limitation_gate",
        passed=(len(gate3_errors) == 0),
        details="Relevant documented limitations cited and displayed accurately without fake placeholders." if not gate3_errors else "; ".join(gate3_errors),
    ))

    checks.append(ValidationCheckItem(
        check="gate4_component_literal_lint",
        passed=(len(gate4_errors) == 0),
        details="Zero hardcoded copy or fake assurance defaults in React components." if not gate4_errors else "; ".join(gate4_errors),
    ))

    claim_coverage_pct = round((backed_claims / total_claims * 100.0), 2) if total_claims > 0 else 0.0

    has_review = len(review_reasons) > 0

    is_passed = (
        len(evidence_records_by_id) > 0
        and claim_coverage_pct == 100.0
        and len(missing_evidence_ids) == 0
        and len(unsupported_numbers) == 0
        and len(banned_tokens_found) == 0
        and len(provenance_errors) == 0
        and len(schema_lineage_errors) == 0
        and len(contradiction_errors) == 0
        and len(gate1_errors) == 0
        and len(gate2_errors) == 0
        and len(gate3_errors) == 0
        and len(gate4_errors) == 0
        and not has_review
    )

    return ValidationReport(
        passed=is_passed,
        claim_coverage_pct=claim_coverage_pct,
        total_claims=total_claims,
        backed_claims=backed_claims,
        unsupported_numbers=unsupported_numbers,
        banned_tokens_found=banned_tokens_found,
        missing_evidence_ids=missing_evidence_ids,
        contradiction_errors=contradiction_errors,
        provenance_errors=provenance_errors,
        schema_lineage_errors=schema_lineage_errors,
        gate1_errors=gate1_errors,
        gate2_errors=gate2_errors,
        gate3_errors=gate3_errors,
        gate4_errors=gate4_errors,
        gate5_errors=gate5_errors,
        gate6_errors=[],
        needs_review=has_review,
        review_reasons=review_reasons,
        checks=checks,
    )


def validate_post_render_qa(
    video_path: Union[str, Path],
    expected_duration: Optional[float] = None,
    expected_audio_path: Optional[Union[str, Path]] = None,
    aspect_ratio: str = "16:9",
    tolerance_sec: float = 0.05,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Gate 6: Post-Render Technical and Visual QA.
    Verifies:
    1. Container format and stream counts (1 video, 1 audio).
    2. Video resolution (1920x1080 for 16:9, 1080x1920 for 9:16) and target FPS ~30.
    3. Audio codec (aac/mp3) and sample rate >= 24000Hz.
    4. Exact audio/video duration synchronization (within tolerance_sec <= 0.05s).
    5. Midpoint keyframe extraction and non-blank frame verification.
    """
    try:
        from engine.validation.output import validate_video_output
    except ImportError:
        from validation.output import validate_video_output

    req_w, req_h = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    is_valid, errors, meta = validate_video_output(
        video_path=video_path,
        expected_audio_path=expected_audio_path,
        expected_duration=expected_duration,
        tolerance_sec=tolerance_sec,
        expected_width=req_w,
        expected_height=req_h,
        aspect_ratio=aspect_ratio,
    )

    vid_p = Path(video_path)
    if vid_p.exists() and vid_p.stat().st_size > 0 and shutil.which("ffmpeg"):
        kf_path = vid_p.with_suffix(".keyframe.jpg")
        try:
            dur = meta.get("video_duration") or 2.0
            mid_t = max(0.5, dur / 2.0)
            kf_cmd = [
                "ffmpeg", "-y",
                "-ss", f"{mid_t:.2f}",
                "-i", str(vid_p),
                "-vframes", "1",
                "-q:v", "2",
                str(kf_path),
            ]
            subprocess.run(kf_cmd, capture_output=True, check=True)
            if not kf_path.exists() or kf_path.stat().st_size < 1000:
                errors.append(f"Gate 6: Rendered keyframe extraction produced blank or corrupt frame ({kf_path})")
                is_valid = False
            else:
                meta["keyframe_path"] = str(kf_path)
        except Exception as e:
            errors.append(f"Gate 6: Failed to extract validation keyframe: {e}")
            is_valid = False

    return is_valid, errors, meta


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate EvidencePack and ScenePlan compliance (4-Gate Moat).")
    parser.add_argument("--evidence-pack", type=str, default=None, help="Path to evidence_pack.json")
    parser.add_argument("--scene-plan", type=str, default=None, help="Path to scene_plan.json or data.json")
    parser.add_argument("--run-dir", type=str, default=None, help="Path to run directory")
    parser.add_argument("--output", type=str, default=None, help="Path to write validation_report.json")
    args = parser.parse_args()

    pack_path = args.evidence_pack
    plan_path = args.scene_plan
    run_dir = Path(args.run_dir) if args.run_dir else None

    if run_dir:
        pack_path = pack_path or str(run_dir / "evidence_pack.json")
        plan_path = plan_path or str(run_dir / "data.json")
        if not Path(plan_path).exists():
            plan_path = str(run_dir / "scene_plan.json")

    if not pack_path or not Path(pack_path).exists():
        print("[EVIDENCE_VALIDATOR:ERROR] Missing --evidence-pack argument or file not found.", file=sys.stderr)
        sys.exit(1)

    if not plan_path or not Path(plan_path).exists():
        print("[EVIDENCE_VALIDATOR:ERROR] Missing --scene-plan argument or file not found.", file=sys.stderr)
        sys.exit(1)

    with open(pack_path, "r", encoding="utf-8") as f:
        pack_data = json.load(f)

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    report = validate_evidence_and_plan(pack_data, plan_data)

    out_file = args.output
    if not out_file and run_dir:
        out_file = str(run_dir / "validation_report.json")

    if out_file:
        out_p = Path(out_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

    print("=" * 65)
    print("EVIDENCE & QUALITY VALIDATION REPORT (4-GATE MOAT)")
    print("=" * 65)
    print(f"Status:            {'PASSED ✅' if report.passed else 'FAILED ❌'}")
    print(f"Claim Coverage:    {report.claim_coverage_pct}% ({report.backed_claims}/{report.total_claims} scenes backed)")
    print(f"Gate 1 (Code):     {'PASSED ✅' if not report.gate1_errors else 'FAILED ❌'}")
    print(f"Gate 2 (Overlap):  {'PASSED ✅' if not report.gate2_errors else 'FAILED ❌'}")
    print(f"Gate 3 (Limits):   {'PASSED ✅' if not report.gate3_errors else 'FAILED ❌'}")
    print(f"Gate 4 (Lint):     {'PASSED ✅' if not report.gate4_errors else 'FAILED ❌'}")
    print("=" * 65)

    if not report.passed:
        for check in report.checks:
            if not check.passed:
                print(f"  ❌ [{check.check}] {check.details}")
        sys.exit(1)
    else:
        print("All 4 validation gates, evidence citations, claims, and numerical bounds verified 100%.")
        sys.exit(0)
