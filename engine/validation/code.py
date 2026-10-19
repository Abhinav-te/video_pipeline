import ast
import subprocess
import re

def _normalize_snippet(code_string):
    """
    Strips markdown ticks, appends an indented 'pass' if a snippet ends
    on an open colon block, ignoring trailing empty lines or comments.
    """
    # Strip LLM Markdown formatting
    code_string = re.sub(r"^```(python)?\s*", "", code_string, flags=re.MULTILINE | re.IGNORECASE)
    code_string = re.sub(r"```\s*$", "", code_string).strip()

    lines = code_string.split("\n")

    # Scan backwards to find the last line that actually contains code
    last_code_line = ""
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            last_code_line = line
            break

    if last_code_line.strip().endswith(":"):
        indent = len(last_code_line) - len(last_code_line.lstrip()) + 4
        lines.append(" " * indent + "pass")
        return "\n".join(lines)

    return code_string

def check_syntax(code_string):
    """
    Parses the Python code to ensure it is syntactically valid without running it.
    Returns (True, None) if valid, (False, Error_Message) if invalid.

    Use this ONLY for scenes that claim to contain real, executable Python
    (code_reveal, code_transform, comparison). Do not use it for terminal
    scenes — see check_terminal_snippet below.
    """
    if not code_string or not code_string.strip():
        return True, None

    normalized_code = _normalize_snippet(code_string)

    try:
        ast.parse(normalized_code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax Error: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Parsing Error: {str(e)}"

def check_terminal_snippet(code_string):
    """
    Loose sanity check for 'terminal' scenes.

    Terminal scenes show command-line output — command invocations, print
    output, timings like '2.5s', tracebacks, etc. That text is NOT valid
    Python and should never be run through ast.parse() (a bare '2.5s' will
    always fail as 'invalid decimal literal', even though it's perfectly
    legitimate terminal output).

    We only check that it's non-empty and reasonably sized, so the director
    can't hand Remotion something empty or absurdly long.
    """
    if not code_string or not code_string.strip():
        return False, "Terminal scene has empty content."

    if len(code_string) > 2000:
        return False, "Terminal scene content is unreasonably long (>2000 chars)."

    return True, None

def run_in_sandbox(code_string, timeout=5):
    """
    Runs the code in an isolated subprocess to verify it executes without crashing.
    Returns (True, terminal_output) or (False, traceback).
    """
    if not code_string or not code_string.strip():
        return True, ""

    normalized_code = _normalize_snippet(code_string)

    try:
        result = subprocess.run(
            ["python3", "-c", normalized_code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            return False, result.stderr.strip()
        return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout} seconds."
    except Exception as e:
        return False, str(e)


def calculate_font_scale(code_string: str, base_font_size: int = 28, max_chars: int = 46, max_lines: int = 14) -> int:
    """
    Dynamically calculates font size (px) from maximum line length and line count
    to guarantee code fits within the 920px card width and 1360px subtitle safe zone.
    """
    if not code_string:
        return base_font_size

    lines = str(code_string).split("\n")
    max_len = max((len(l) for l in lines), default=0)
    line_count = len(lines)

    if max_len > 55 or line_count > 12:
        return 19
    elif max_len > 46 or line_count > 10:
        return 22
    elif max_len > 38 or line_count > 8:
        return 25
    return base_font_size


def format_and_wrap_code_snippet(code_string: str, max_chars: int = 46, max_lines: int = 14) -> str:
    """
    Wraps code lines exceeding max_chars at natural token boundaries (commas, dots, spaces, parens)
    with a clean 4-space hanging indent, and caps total lines at max_lines to prevent overflow.
    """
    if not code_string:
        return ""

    raw_lines = str(code_string).split("\n")
    out_lines = []

    for line in raw_lines:
        if len(line) <= max_chars:
            out_lines.append(line)
            continue

        indent = len(line) - len(line.lstrip())
        indent_str = " " * (indent + 4)
        rem = line
        while len(rem) > max_chars:
            split_idx = -1
            for sep in [", ", " && ", " || ", " = ", ". ", "(", " "]:
                idx = rem.rfind(sep, 0, max_chars)
                if idx > indent + 4:
                    split_idx = idx + len(sep)
                    break
            if split_idx == -1:
                split_idx = max_chars

            out_lines.append(rem[:split_idx].rstrip())
            rem = indent_str + rem[split_idx:].lstrip()

        if rem:
            out_lines.append(rem)

    if len(out_lines) > max_lines:
        out_lines = out_lines[:max_lines - 1] + ["..."]

    return "\n".join(out_lines)


def validate_code_layout(code_string: str, max_chars: int = 46, max_lines: int = 14):
    """
    Checks line width and line count against the 920px card constraint.
    Returns (fits_without_scaling, warning_message, layout_meta).
    """
    if not code_string:
        return True, None, {"max_line_length": 0, "line_count": 0, "font_size": 28, "needs_scaling": False}

    lines = str(code_string).split("\n")
    max_len = max((len(l) for l in lines), default=0)
    line_count = len(lines)
    font_size = calculate_font_scale(code_string, base_font_size=28, max_chars=max_chars, max_lines=max_lines)

    needs_scaling = max_len > max_chars or line_count > 10
    msg = None
    if max_len > max_chars:
        msg = f"Code line exceeds {max_chars} chars (max: {max_len}). Scaling font to {font_size}px or wrapping."
    elif line_count > max_lines:
        msg = f"Code lines exceed {max_lines} lines (count: {line_count})."

    meta = {
        "max_line_length": max_len,
        "line_count": line_count,
        "font_size": font_size,
        "needs_scaling": needs_scaling,
    }
    return not needs_scaling, msg, meta