"""Customer Content & Internet Documentation Ingestion Package."""

from .source_loader import (
    load_source_content,
    extract_source_facts,
    format_source_summary,
)

__all__ = [
    "load_source_content",
    "extract_source_facts",
    "format_source_summary",
]

