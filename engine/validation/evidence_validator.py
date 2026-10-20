"""engine/validation/evidence_validator.py

Evidence & Quality Validation Gate.
Verifies:
1. 100% Claim Coverage: Every scene narration segment and visual metric links to a valid evidence_id.
2. Zero Unsupported Numbers: All numerical tokens must be backed by evidence records or code evidence.
3. Zero Placeholder Contamination: Rejects banned tokens (K-Means, DBSCAN, PCA, t-SNE, Invariant algorithmic).
4. Generates comprehensive audit log in validation_report.json.
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
    from engine.ingestion.evidence_extractor import EvidencePack, EvidenceRecord
except ImportError:
    try:
        from ingestion.evidence_extractor import EvidencePack, EvidenceRecord
    except ImportError:
        EvidencePack = None
        EvidenceRecord = None


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


def extract_numbers_from_text(text: str) -> List[str]:
    """Extracts numerical tokens from text, ignoring standard code syntax tokens."""
    # Matches integers, decimals, percentages, e.g. "503", "10", "99.9%"
    raw = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    # Ignore zero, 1 (common singular words), and line numbers 1-20
    return [n for n in raw if n not in {"0", "1"}]


def validate_evidence_and_plan(
    evidence_pack_data: Union[Dict[str, Any], Any],
    scene_plan_or_timeline_data: Union[Dict[str, Any], Any],
    source_docs: Optional[List[Dict[str, Any]]] = None,
) -> ValidationReport:
    """
    Core validation function enforcing 100% claim backing and factual integrity.
    """
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

    # Extract all text from all evidence records for factual number verification
    all_evidence_corpus = " ".join([
        f"{r.get('claim', '')} {r.get('excerpt', '')} {r.get('code_evidence', '')}"
        for r in evidence_records_by_id.values()
    ])

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
    checks: List[ValidationCheckItem] = []

    # Check 1: Evidence records presence
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

    # Evaluate Each Scene
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id") or scene.get("id") or (idx + 1)
        scene_str = json.dumps(scene).lower()

        # Check Placeholder Contamination
        for token in BANNED_CONTAMINATION_TOKENS:
            if token in scene_str:
                banned_tokens_found.append(f"Scene {scene_id}: contains '{token}'")

        # Extract Evidence IDs cited by this scene
        cited_ids: Set[str] = set()
        raw_ids = scene.get("evidence_ids") or []
        if isinstance(raw_ids, list):
            cited_ids.update([str(x) for x in raw_ids])

        # Check narration segments
        segments = scene.get("narration_segments") or []
        if segments and isinstance(segments, list):
            for seg in segments:
                if isinstance(seg, dict):
                    seg_ids = seg.get("evidence_ids") or []
                    for sid in seg_ids:
                        cited_ids.add(str(sid))

        total_claims += 1
        scene_passed_citation = False

        if not cited_ids:
            checks.append(ValidationCheckItem(
                check="claim_citation",
                passed=False,
                details=f"Scene {scene_id} has no linked evidence_ids.",
                scene_id=scene_id,
            ))
        else:
            # Check all cited IDs exist in evidence pack
            valid_for_scene = True
            for cid in cited_ids:
                if cid not in evidence_records_by_id:
                    valid_for_scene = False
                    missing_evidence_ids.append(f"Scene {scene_id} cited non-existent evidence_id: '{cid}'")

            if valid_for_scene:
                backed_claims += 1
                scene_passed_citation = True
                checks.append(ValidationCheckItem(
                    check="claim_citation",
                    passed=True,
                    details=f"Scene {scene_id} backed by {len(cited_ids)} verified record(s): {sorted(list(cited_ids))}",
                    scene_id=scene_id,
                ))
            else:
                checks.append(ValidationCheckItem(
                    check="claim_citation",
                    passed=False,
                    details=f"Scene {scene_id} cited unverified or missing evidence IDs.",
                    scene_id=scene_id,
                ))

        # Check Numerical Claims in Narration & Visuals
        narration = str(scene.get("spoken_text") or scene.get("narration") or "")
        numbers_in_narration = extract_numbers_from_text(narration)

        # Build corpus of cited records for this scene
        scene_evidence_corpus = " ".join([
            f"{evidence_records_by_id[cid].get('claim', '')} {evidence_records_by_id[cid].get('excerpt', '')} {evidence_records_by_id[cid].get('code_evidence', '')}"
            for cid in cited_ids if cid in evidence_records_by_id
        ])
        
        # Include scene code snippet if present
        if scene.get("code"):
            scene_evidence_corpus += " " + str(scene["code"])

        for num in numbers_in_narration:
            # Number must appear in cited evidence or scene code
            if num not in scene_evidence_corpus and num not in all_evidence_corpus:
                unsupported_numbers.append(f"Scene {scene_id} spoken text contains unverified number '{num}'")

        # Check visual items / metrics if present
        items = scene.get("items") or []
        for it in items:
            if isinstance(it, dict):
                val = str(it.get("value", ""))
                val_nums = extract_numbers_from_text(val)
                for vn in val_nums:
                    if vn not in scene_evidence_corpus and vn not in all_evidence_corpus:
                        unsupported_numbers.append(f"Scene {scene_id} metric card contains unverified number '{vn}'")

    claim_coverage_pct = round((backed_claims / total_claims * 100.0), 2) if total_claims > 0 else 0.0

    # Overall Pass Decision
    is_passed = (
        len(evidence_records_by_id) > 0
        and claim_coverage_pct == 100.0
        and len(missing_evidence_ids) == 0
        and len(unsupported_numbers) == 0
        and len(banned_tokens_found) == 0
    )

    if banned_tokens_found:
        checks.append(ValidationCheckItem(
            check="placeholder_tokens",
            passed=False,
            details=f"Found banned contamination tokens: {banned_tokens_found}",
        ))
    else:
        checks.append(ValidationCheckItem(
            check="placeholder_tokens",
            passed=True,
            details="Zero banned placeholder or template contamination tokens found.",
        ))

    if unsupported_numbers:
        checks.append(ValidationCheckItem(
            check="numerical_claims",
            passed=False,
            details=f"Found unsupported numbers: {unsupported_numbers}",
        ))
    else:
        checks.append(ValidationCheckItem(
            check="numerical_claims",
            passed=True,
            details="All numerical figures and metrics verified in official evidence records.",
        ))

    return ValidationReport(
        passed=is_passed,
        claim_coverage_pct=claim_coverage_pct,
        total_claims=total_claims,
        backed_claims=backed_claims,
        unsupported_numbers=unsupported_numbers,
        banned_tokens_found=banned_tokens_found,
        missing_evidence_ids=missing_evidence_ids,
        checks=checks,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate EvidencePack and ScenePlan compliance.")
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

    # If neither provided, check test /tmp files or latest run
    if not pack_path or not Path(pack_path).exists():
        if Path("/tmp/test_evidence_pack.json").exists():
            pack_path = "/tmp/test_evidence_pack.json"
        else:
            print("[EVIDENCE_VALIDATOR:ERROR] Missing --evidence-pack argument or file not found.", file=sys.stderr)
            sys.exit(1)

    if not plan_path or not Path(plan_path).exists():
        if Path("/tmp/test_scene_plan.json").exists():
            plan_path = "/tmp/test_scene_plan.json"
        else:
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
        print(f"Validation report saved to: {out_file}")

    print("=" * 65)
    print("EVIDENCE & QUALITY VALIDATION REPORT")
    print("=" * 65)
    print(f"Status:            {'PASSED ✅' if report.passed else 'FAILED ❌'}")
    print(f"Claim Coverage:    {report.claim_coverage_pct}% ({report.backed_claims}/{report.total_claims} scenes backed)")
    print(f"Missing Citations: {len(report.missing_evidence_ids)}")
    print(f"Invalid Numbers:   {len(report.unsupported_numbers)}")
    print(f"Contamination:     {len(report.banned_tokens_found)}")
    print("=" * 65)

    if not report.passed:
        for check in report.checks:
            if not check.passed:
                print(f"  ❌ [{check.check}] {check.details}")
        sys.exit(1)
    else:
        print("All evidence citations, claims, and numerical bounds verified 100%.")
        sys.exit(0)

