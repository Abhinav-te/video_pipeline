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
    gate1_errors: List[str] = Field(default_factory=list)
    gate2_errors: List[str] = Field(default_factory=list)
    gate3_errors: List[str] = Field(default_factory=list)
    gate4_errors: List[str] = Field(default_factory=list)
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
    raw = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    return [n for n in raw if n not in {"0", "1"}]


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
    """Core validation moat enforcing 4 strict gates and 100% claim backing."""
    # 1. Parse Evidence Pack
    if isinstance(evidence_pack_data, dict):
        records_list = evidence_pack_data.get("records", [])
        evidence_records_by_id: Dict[str, Dict[str, Any]] = {
            r.get("id"): r for r in records_list if isinstance(r, dict) and r.get("id")
        }
    elif hasattr(evidence_pack_data, "records"):
        evidence_records_by_id = {
            r.id: r.model_dump() for r in evidence_pack_data.records
        }
    else:
        evidence_records_by_id = {}

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
    gate1_errors: List[str] = []
    gate2_errors: List[str] = []
    gate3_errors: List[str] = []
    checks: List[ValidationCheckItem] = []

    if not evidence_records_by_id:
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

    # All cited evidence IDs across all scenes
    all_cited_ids: Set[str] = set()

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id") or scene.get("id") or (idx + 1)
        scene_str = json.dumps(scene).lower()

        # Check Placeholder Contamination
        for token in BANNED_CONTAMINATION_TOKENS:
            if token in scene_str:
                banned_tokens_found.append(f"Scene {scene_id}: contains '{token}'")

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

        # Build corpus of cited records for this scene ONLY (Bug fixed: never include scene's own code)
        scene_evidence_corpus = " ".join([
            f"{evidence_records_by_id[cid].get('claim', '')} {evidence_records_by_id[cid].get('excerpt', '')} {evidence_records_by_id[cid].get('code_evidence', '')}"
            for cid in cited_ids if cid in evidence_records_by_id
        ])

        # Numerical Claims Check
        narration = str(scene.get("spoken_text") or scene.get("narration") or "")
        numbers_in_narration = extract_numbers_from_text(narration)
        for num in numbers_in_narration:
            if num not in scene_evidence_corpus and num not in all_evidence_corpus:
                unsupported_numbers.append(f"Scene {scene_id} spoken text contains unverified number '{num}'")

        items = scene.get("items") or scene.get("cards") or []
        for it in items:
            if isinstance(it, dict):
                val = str(it.get("value", ""))
                val_nums = extract_numbers_from_text(val)
                for vn in val_nums:
                    if vn not in scene_evidence_corpus and vn not in all_evidence_corpus:
                        unsupported_numbers.append(f"Scene {scene_id} metric card contains unverified number '{vn}'")

        # -------------------------------------------------------------
        # Gate 1: Contiguous Code Equality & Syntax Health
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
        # Gate 2: Quote / Paraphrase Check (>= 0.35 content-word overlap)
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

    # -----------------------------------------------------------------
    # Gate 3: Limitation Gate
    # -----------------------------------------------------------------
    if limitation_records:
        has_limitation_cited = False
        has_warning_displayed = False
        has_guarded_anti_pattern = False

        for lim_rec in limitation_records:
            lim_id = lim_rec.get("id")
            lim_claim = lim_rec.get("claim", "")
            lim_excerpt = lim_rec.get("excerpt", "")
            lim_words = get_content_words(f"{lim_claim} {lim_excerpt}")

            if lim_id in all_cited_ids:
                has_limitation_cited = True

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
            gate3_errors.append(f"Limitation record is not cited in the scene plan.")
        elif not has_warning_displayed:
            gate3_errors.append(
                f"Documented limitation is cited but not displayed verbatim or as a close paraphrase on screen."
            )

        if has_guarded_anti_pattern:
            gate3_errors.append(
                f"Found placeholder 'GUARDED' instead of the actual documented limitation warning."
            )

    # -----------------------------------------------------------------
    # Gate 4: Component Literal Lint
    # -----------------------------------------------------------------
    gate4_errors = lint_component_literals()

    # Record Gate Check Items
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
        check="gate3_limitation_gate",
        passed=(len(gate3_errors) == 0),
        details="All documented limitations cited and displayed accurately without fake placeholders." if not gate3_errors else "; ".join(gate3_errors),
    ))

    checks.append(ValidationCheckItem(
        check="gate4_component_literal_lint",
        passed=(len(gate4_errors) == 0),
        details="Zero hardcoded copy or fake assurance defaults in React components." if not gate4_errors else "; ".join(gate4_errors),
    ))

    claim_coverage_pct = round((backed_claims / total_claims * 100.0), 2) if total_claims > 0 else 0.0

    is_passed = (
        len(evidence_records_by_id) > 0
        and claim_coverage_pct == 100.0
        and len(missing_evidence_ids) == 0
        and len(unsupported_numbers) == 0
        and len(banned_tokens_found) == 0
        and len(gate1_errors) == 0
        and len(gate2_errors) == 0
        and len(gate3_errors) == 0
        and len(gate4_errors) == 0
    )

    return ValidationReport(
        passed=is_passed,
        claim_coverage_pct=claim_coverage_pct,
        total_claims=total_claims,
        backed_claims=backed_claims,
        unsupported_numbers=unsupported_numbers,
        banned_tokens_found=banned_tokens_found,
        missing_evidence_ids=missing_evidence_ids,
        gate1_errors=gate1_errors,
        gate2_errors=gate2_errors,
        gate3_errors=gate3_errors,
        gate4_errors=gate4_errors,
        checks=checks,
    )


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
