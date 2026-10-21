"""Customer Content & Internet Documentation Ingestion Package."""

from .source_loader import (
    load_source_content,
    extract_source_facts,
    format_source_summary,
)
from .code_sanitizer import (
    sanitize_code,
    is_delimiter_balanced,
    derive_highlight_lines,
)

__all__ = [
    "load_source_content",
    "extract_source_facts",
    "format_source_summary",
    "sanitize_code",
    "is_delimiter_balanced",
    "derive_highlight_lines",
]

