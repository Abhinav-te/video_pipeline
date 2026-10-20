"""engine/ingestion/evidence_extractor.py

Universal Documentation Evidence Extractor.
Extracts verifiable atomic EvidenceRecords from ingested documentation into an EvidencePack.
Adheres strictly to the AGENTS.md Universal Evidence Record Schema with ZERO company hardcoding.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


EvidenceKind = Literal[
    "concept",
    "developer_action",
    "behavior",
    "failure_behavior",
    "limitation",
    "code_evidence",
    "metric",
]

ConfidenceLevel = Literal["source_supported", "inferred_needs_review"]


class EvidenceRecord(BaseModel):
    id: str = Field(description="Unique stable evidence identifier (e.g. 'ev_step_run_01')")
    kind: EvidenceKind = Field(description="Taxonomy kind of the evidence record")
    claim: str = Field(description="Concise factual statement directly supported by the source")
    source_url: str = Field(description="Exact URL or file path of the source document")
    source_section: str = Field(description="Heading or section title")
    excerpt: str = Field(description="Verbatim quote or code snippet from the source")
    retrieved_at: str = Field(description="ISO-8601 timestamp of source ingestion")
    content_hash: str = Field(description="SHA-256 of the normalized source section")
    confidence: ConfidenceLevel = Field(default="source_supported", description="Verification confidence")
    code_evidence: Optional[str] = Field(default=None, description="Optional attached code snippet")


class SourceDocument(BaseModel):
    source_url: str
    title: str
    retrieved_at: str
    content_hash: str
    raw_content: str


class EvidencePack(BaseModel):
    project: str = Field(default="Generic Technical Product", description="Product or project identifier")
    sources: List[SourceDocument] = Field(default_factory=list)
    records: List[EvidenceRecord] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def get_record(self, record_id: str) -> Optional[EvidenceRecord]:
        for r in self.records:
            if r.id == record_id:
                return r
        return None

    def filter_by_kind(self, kind: EvidenceKind) -> List[EvidenceRecord]:
        return [r for r in self.records if r.kind == kind]

    def to_json_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def compute_sha256(text: str) -> str:
    """Computes normalized SHA-256 hash of a string."""
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def split_markdown_into_sections(markdown_text: str) -> List[Dict[str, str]]:
    """Splits Markdown text into titled sections based on headers."""
    lines = markdown_text.strip().splitlines()
    sections: List[Dict[str, str]] = []
    current_title = "Overview"
    current_lines: List[str] = []

    for line in lines:
        header_match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if header_match:
            if current_lines:
                sec_text = "\n".join(current_lines).strip()
                if sec_text:
                    sections.append({
                        "title": current_title,
                        "content": sec_text,
                        "hash": compute_sha256(sec_text),
                    })
            current_title = header_match.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sec_text = "\n".join(current_lines).strip()
        if sec_text:
            sections.append({
                "title": current_title,
                "content": sec_text,
                "hash": compute_sha256(sec_text),
            })

    return sections


def extract_evidence_offline(
    source_docs: List[SourceDocument],
    project_name: str = "Developer Tool",
) -> EvidencePack:
    """
    Deterministic offline evidence extractor.
    Parses Markdown sections, code blocks, callouts, and developer workflows
    without hardcoding any company names or domains.
    """
    records: List[EvidenceRecord] = []
    record_counter = 1

    for doc in source_docs:
        sections = split_markdown_into_sections(doc.raw_content)

        for sec in sections:
            sec_title = sec["title"]
            sec_content = sec["content"]
            sec_hash = sec["hash"]

            # 1. Extract Code Blocks (kind: "code_evidence")
            code_blocks = re.findall(r"```([a-zA-Z0-9_\-+]*)\n([\s\S]*?)```", sec_content)
            for lang, code_body in code_blocks:
                clean_code = code_body.strip()
                if not clean_code:
                    continue

                rec_id = f"ev_{record_counter:02d}"
                record_counter += 1

                # Derive concise claim from section title and code language
                first_line = clean_code.splitlines()[0].strip() if clean_code.splitlines() else ""
                claim = f"Code snippet in {lang or 'source'} for {sec_title}: {first_line[:60]}"

                records.append(
                    EvidenceRecord(
                        id=rec_id,
                        kind="code_evidence",
                        claim=claim,
                        source_url=doc.source_url,
                        source_section=sec_title,
                        excerpt=clean_code,
                        retrieved_at=doc.retrieved_at,
                        content_hash=compute_sha256(clean_code),
                        confidence="source_supported",
                        code_evidence=clean_code,
                    )
                )

            # 2. Extract Callouts, Warnings, and Limitations (kind: "limitation" / "failure_behavior")
            callout_matches = re.finditer(
                r">\s*\[!(WARNING|CAUTION|NOTE|IMPORTANT)\]\s*\n((?:>.*(?:\n|$))+)",
                sec_content,
                re.IGNORECASE,
            )
            for cm in callout_matches:
                ctype = cm.group(1).upper()
                raw_body = cm.group(2)
                body = re.sub(r"^>\s?", "", raw_body, flags=re.MULTILINE).strip()
                if not body:
                    continue

                rec_id = f"ev_{record_counter:02d}"
                record_counter += 1

                kind: EvidenceKind = "limitation" if ctype in ("WARNING", "CAUTION") else "behavior"
                first_sent = re.split(r"\.\s+|\n", body)[0].strip()
                claim = first_sent if first_sent else f"Documentation {ctype.lower()} notice in {sec_title}"

                records.append(
                    EvidenceRecord(
                        id=rec_id,
                        kind=kind,
                        claim=claim,
                        source_url=doc.source_url,
                        source_section=sec_title,
                        excerpt=body,
                        retrieved_at=doc.retrieved_at,
                        content_hash=compute_sha256(body),
                        confidence="source_supported",
                    )
                )

            # 3. Analyze Paragraphs and Bullets
            # Remove already extracted code blocks to avoid duplicate text noise
            text_without_code = re.sub(r"```[\s\S]*?```", "", sec_content)
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text_without_code) if p.strip()]

            for para in paragraphs:
                if para.startswith(">"):
                    continue  # already handled in callouts

                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if len(s.strip()) > 15]

                for sentence in sentences:
                    # Clean markdown symbols for claim analysis
                    clean_sent = re.sub(r"[`*#]", "", sentence).strip()
                    lower_sent = clean_sent.lower()

                    # Check for limitations / constraints
                    if any(term in lower_sent for term in ["limitation", "must not", "caution", "warning", "must be idempotent", "parameter mismatch", "expires after", "retains idempotency keys for", "only needed on", "only on post"]):
                        rec_id = f"ev_{record_counter:02d}"
                        record_counter += 1
                        records.append(
                            EvidenceRecord(
                                id=rec_id,
                                kind="limitation",
                                claim=clean_sent,
                                source_url=doc.source_url,
                                source_section=sec_title,
                                excerpt=sentence,
                                retrieved_at=doc.retrieved_at,
                                content_hash=compute_sha256(sentence),
                                confidence="source_supported",
                            )
                        )
                    # Check for failure/error behavior
                    elif any(term in lower_sent for term in ["throws", "fails", "failure", "retry", "retries", "error", "timeout", "503", "400", "dropped", "connection drop", "double-charg", "duplicate"]):
                        rec_id = f"ev_{record_counter:02d}"
                        record_counter += 1
                        records.append(
                            EvidenceRecord(
                                id=rec_id,
                                kind="failure_behavior",
                                claim=clean_sent,
                                source_url=doc.source_url,
                                source_section=sec_title,
                                excerpt=sentence,
                                retrieved_at=doc.retrieved_at,
                                content_hash=compute_sha256(sentence),
                                confidence="source_supported",
                            )
                        )
                    # Check for developer actions
                    elif any(lower_sent.startswith(verb) for verb in ["to ", "wrap ", "call ", "import ", "create ", "define ", "use ", "pass ", "send "]) or any(term in lower_sent for term in ["pass a unique", "pass an idempotency", "specify an idempotency"]):
                        rec_id = f"ev_{record_counter:02d}"
                        record_counter += 1
                        records.append(
                            EvidenceRecord(
                                id=rec_id,
                                kind="developer_action",
                                claim=clean_sent,
                                source_url=doc.source_url,
                                source_section=sec_title,
                                excerpt=sentence,
                                retrieved_at=doc.retrieved_at,
                                content_hash=compute_sha256(sentence),
                                confidence="source_supported",
                            )
                        )
                    # Check for core runtime behavior / memoization / state
                    elif any(term in lower_sent for term in ["memoized", "saved", "persisted", "reused", "workflow state", "execution context", "resumes", "isolated", "cached", "returns the cached", "without creating", "safe to retry"]):
                        rec_id = f"ev_{record_counter:02d}"
                        record_counter += 1
                        records.append(
                            EvidenceRecord(
                                id=rec_id,
                                kind="behavior",
                                claim=clean_sent,
                                source_url=doc.source_url,
                                source_section=sec_title,
                                excerpt=sentence,
                                retrieved_at=doc.retrieved_at,
                                content_hash=compute_sha256(sentence),
                                confidence="source_supported",
                            )
                        )
                    # Check for metrics
                    elif re.search(r"\b(?:\d+(?:\.\d+)?(?:x|ms|s|%|req/s|rps|MB|GB|KB|hours?|days?))\b", sentence):
                        rec_id = f"ev_{record_counter:02d}"
                        record_counter += 1
                        records.append(
                            EvidenceRecord(
                                id=rec_id,
                                kind="metric",
                                claim=clean_sent,
                                source_url=doc.source_url,
                                source_section=sec_title,
                                excerpt=sentence,
                                retrieved_at=doc.retrieved_at,
                                content_hash=compute_sha256(sentence),
                                confidence="source_supported",
                            )
                        )
                    # Core concept definitions
                    elif any(term in lower_sent for term in ["is a core", "primitive", "enables developers", "provides built-in", "core durable", "idempotent requests", "idempotency", "prevent accidentally", "same mutating"]):
                        rec_id = f"ev_{record_counter:02d}"
                        record_counter += 1
                        records.append(
                            EvidenceRecord(
                                id=rec_id,
                                kind="concept",
                                claim=clean_sent,
                                source_url=doc.source_url,
                                source_section=sec_title,
                                excerpt=sentence,
                                retrieved_at=doc.retrieved_at,
                                content_hash=compute_sha256(sentence),
                                confidence="source_supported",
                            )
                        )

    return EvidencePack(
        project=project_name,
        sources=source_docs,
        records=records,
    )


def extract_evidence_pack(
    sources_info: List[Dict[str, str]],
    project_profile: Optional[Dict[str, Any]] = None,
    mock: bool = False,
) -> EvidencePack:
    """
    Main entry point: loads documentation sources and extracts structured EvidencePack.
    Falls back gracefully to offline extraction in mock mode or when LLM is unavailable.
    """
    from engine.ingestion.source_loader import load_source_content

    project_name = (
        (project_profile and project_profile.get("product"))
        or (project_profile and project_profile.get("title"))
        or "Developer Tool"
    )

    source_docs: List[SourceDocument] = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for s in sources_info:
        url = s.get("url") or s.get("source_url") or ""
        local_file = s.get("local_file") or s.get("source_file") or ""
        title = s.get("title") or url or local_file

        # If local_file is provided and exists, load it immediately
        raw_text = ""
        resolved_source = url or local_file

        if local_file:
            try:
                raw_text = load_source_content(source_file=local_file)
                resolved_source = url or local_file
            except Exception:
                pass

        if not raw_text and url and not mock:
            try:
                raw_text = load_source_content(source_url=url)
                resolved_source = url
            except Exception:
                pass

        if raw_text:
            source_docs.append(
                SourceDocument(
                    source_url=resolved_source,
                    title=title,
                    retrieved_at=now_iso,
                    content_hash=compute_sha256(raw_text),
                    raw_content=raw_text,
                )
            )

    # In mock or offline mode, extract using the deterministic offline parser
    if mock or not os.getenv("GEMINI_API_KEY"):
        return extract_evidence_offline(source_docs, project_name=project_name)

    # In live mode with GEMINI_API_KEY, use Gemini structured extraction with offline fallback
    try:
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY", "").split(",")[0].strip()
        client = genai.Client(api_key=api_key)

        combined_docs = "\n\n---\n\n".join(
            f"SOURCE: {doc.source_url} (Title: {doc.title})\n\n{doc.raw_content}"
            for doc in source_docs
        )

        prompt = (
            f"You are a strict technical documentation analyst for {project_name}.\n"
            f"Extract all verifiable facts from the provided documentation into typed EvidenceRecords.\n"
            f"Every claim must be directly supported by a verbatim excerpt.\n"
            f"Classify each record into one of: concept, developer_action, behavior, failure_behavior, limitation, code_evidence, metric.\n"
            f"Do not invent any facts, numbers, or assumptions.\n\n"
            f"DOCUMENTATION:\n{combined_docs}"
        )

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EvidencePack,
                temperature=0.1,
            ),
        )

        if response.parsed and isinstance(response.parsed, EvidencePack) and response.parsed.records:
            pack = response.parsed
            pack.sources = source_docs
            pack.project = project_name
            return pack

        if response.text:
            parsed_json = json.loads(response.text)
            parsed_json["sources"] = [d.model_dump() for d in source_docs]
            parsed_json["project"] = project_name
            return EvidencePack.model_validate(parsed_json)

    except Exception as exc:
        print(f"[EVIDENCE:WARN] Gemini extraction failed ({exc}). Falling back to deterministic offline extractor.", flush=True)

    return extract_evidence_offline(source_docs, project_name=project_name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract structured EvidencePack from documentation.")
    parser.add_argument("--source-file", type=str, help="Path to markdown documentation file")
    parser.add_argument("--source-url", type=str, help="URL of public documentation")
    parser.add_argument("--project-file", type=str, help="Path to project_profile.json")
    parser.add_argument("--output", type=str, default="evidence_pack.json", help="Output JSON path")
    parser.add_argument("--mock", action="store_true", help="Deterministic offline mode")
    args = parser.parse_args()

    sources = []
    project_profile = {}

    if args.project_file:
        with open(args.project_file, "r", encoding="utf-8") as f:
            pdata = json.load(f)
            project_profile = pdata.get("project_profile", pdata)
            sources = project_profile.get("sources", [])
    elif args.source_file:
        sources.append({"local_file": args.source_file, "title": Path(args.source_file).name})
    elif args.source_url:
        sources.append({"url": args.source_url, "title": args.source_url})

    pack = extract_evidence_pack(sources, project_profile=project_profile, mock=args.mock)
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pack.to_json_dict(), f, indent=2)

    print(f"Extracted {len(pack.records)} evidence records -> {out_path}")

