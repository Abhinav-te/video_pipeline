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