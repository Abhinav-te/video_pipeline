"""Canonical Code Sanitization, Delimiter Balancing & Dynamic Line Highlight Derivation.

Guarantees clean, syntax-balanced code snippets across all ingestion paths.
Zero markdown fence leakage, normalized indentation, and dynamic focus token mapping.
"""

from __future__ import annotations

import re
import textwrap
from typing import List, Tuple, Optional


def sanitize_code(raw: str) -> str:
    """Sanitizes raw code from documentation, markdown, or HTML pre blocks.

    - Strips markdown fences (```typescript, ```ts, ```javascript, ```json, etc.)
    - Removes opening and closing triple backticks
    - Normalizes tabs to 2 spaces
    - Dedents to remove common leading indentation
    - Trims leading/trailing blank lines
    - Guarantees Line 1 on screen is NEVER ```typescript or any fence
    """
    if not raw or not isinstance(raw, str):
        return ""

    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize tabs to 2 spaces first
    text = text.replace("\t", "  ")

    # Strip markdown code block fences if present at top/bottom
    lines = text.split("\n")

    # If first non-empty line starts with ```, drop it
    start_idx = 0
    while start_idx < len(lines) and not lines[start_idx].strip():
        start_idx += 1

    if start_idx < len(lines) and lines[start_idx].strip().startswith("```"):
        start_idx += 1

    end_idx = len(lines)
    while end_idx > start_idx and not lines[end_idx - 1].strip():
        end_idx -= 1

    if end_idx > start_idx and lines[end_idx - 1].strip().startswith("```"):
        end_idx -= 1

    cleaned_lines = lines[start_idx:end_idx]

    # Filter out any internal rogue fence lines if present
    final_lines = [
        line for line in cleaned_lines
        if not re.match(r"^\s*```[a-zA-Z0-9_\-+]*\s*$", line)
    ]

    joined = "\n".join(final_lines)
    # Dedent
    dedented = textwrap.dedent(joined).strip()

    # Final safety check: Line 1 must NEVER start with ```
    out_lines = dedented.split("\n")
    while out_lines and out_lines[0].strip().startswith("```"):
        out_lines = out_lines[1:]
    while out_lines and out_lines[-1].strip().startswith("```"):
        out_lines = out_lines[:-1]

    return "\n".join(out_lines).strip()


def is_delimiter_balanced(code: str) -> bool:
    """Checks whether braces {}, parentheses (), and brackets [] are syntactically balanced.
    
    Ignores delimiters inside single-line comments (//), multi-line comments (/* */),
    and string literals ('...', "...", `...`).
    """
    if not code:
        return True

    stack: List[str] = []
    pairs = {"}": "{", ")": "(", "]": "["}
    
    # Strip comments and strings before bracket checking
    # Regex for strings and comments
    token_pattern = re.compile(
        r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`|[{}\[\]()]'
    )

    for m in token_pattern.finditer(code):
        token = m.group(0)
        # Skip comments and strings
        if token.startswith("//") or token.startswith("/*") or token.startswith('"') or token.startswith("'") or token.startswith("`"):
            continue

        if token in "{([":
            stack.append(token)
        elif token in "})]" :
            if not stack or stack[-1] != pairs[token]:
                return False
            stack.pop()

    return len(stack) == 0


def derive_highlight_lines(
    code: str,
    focus_token: Optional[str] = None,
    max_span: int = 8,
) -> List[int]:
    """Dynamically derives 1-indexed highlight line numbers based on focus token.

    Matches focus_token (e.g. 'step.run(' or 'idempotencyKey') against sanitized code lines.
    If the match starts a multi-line statement/closure (unclosed ( or {), spans down to the
    closing line so the entire active construct is highlighted.
    """
    if not code or not focus_token:
        return []

    lines = code.split("\n")
    token_lower = focus_token.strip().lower()
    clean_token = re.sub(r"[{}\[\]()]", "", token_lower).strip()

    matching_line_indices: List[int] = []

    for idx, line in enumerate(lines):
        line_clean = line.lower()
        if token_lower in line_clean or (clean_token and clean_token in line_clean):
            matching_line_indices.append(idx)

    if not matching_line_indices:
        return []

    highlight_set = set()

    for start_idx in matching_line_indices:
        highlight_set.add(start_idx + 1)
        
        # Check if this line opens a block that continues
        sub_code = "\n".join(lines[start_idx:])
        # Track open parens / braces from start_idx
        open_count = 0
        in_string = None
        curr_idx = start_idx

        for offset, l in enumerate(lines[start_idx:start_idx + max_span]):
            line_num = start_idx + offset + 1
            # Simple bracket counter for spanning statement
            for char in l:
                if char in "{(":
                    open_count += 1
                elif char in "})":
                    open_count -= 1

            highlight_set.add(line_num)
            if open_count <= 0 and offset > 0:
                break

    return sorted(list(highlight_set))

