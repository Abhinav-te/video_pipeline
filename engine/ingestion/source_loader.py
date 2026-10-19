"""Customer Content & Internet Documentation Ingestion Engine.

Provides unified ingestion for customer-provided developer-tool materials:
- Local documentation/code files (--source-file)
- Public documentation / GitHub URLs (--source-url)
- Raw text/markdown strings (--source-text)

Extracts ground-truth facts (CLI commands, code snippets, endpoints, key metrics)
and formats them for injection into both live LLM prompts and deterministic --mock scenes.
"""

from __future__ import annotations

import html
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import urllib.parse
import urllib.request


class HTMLToMarkdownParser(HTMLParser):
    """Clean HTML to Markdown parser preserving headings, code blocks, lists, and paragraphs."""

    def __init__(self) -> None:
        super().__init__()
        self.output: List[str] = []
        self.ignore_tags = {"script", "style", "nav", "header", "footer", "svg", "noscript", "head", "aside"}
        self.current_ignore_depth = 0
        self.in_pre = False
        self.in_code = False
        self.code_lang = ""

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.ignore_tags:
            self.current_ignore_depth += 1
            return
        if self.current_ignore_depth > 0:
            return

        attr_dict = dict(attrs)

        if tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag_lower[1])
            self.output.append(f"\n\n{'#' * level} ")
        elif tag_lower == "p":
            self.output.append("\n\n")
        elif tag_lower == "br":
            self.output.append("\n")
        elif tag_lower == "li":
            self.output.append("\n- ")
        elif tag_lower == "pre":
            self.in_pre = True
            # Attempt to discover language from class
            cls = attr_dict.get("class", "") or ""
            m = re.search(r"language-([\w-]+)", cls)
            self.code_lang = m.group(1) if m else ""
            self.output.append(f"\n\n```{self.code_lang}\n")
        elif tag_lower == "code":
            if not self.in_pre:
                self.in_code = True
                self.output.append("`")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.ignore_tags:
            if self.current_ignore_depth > 0:
                self.current_ignore_depth -= 1
            return
        if self.current_ignore_depth > 0:
            return

        if tag_lower == "pre":
            self.in_pre = False
            self.output.append("\n```\n")
        elif tag_lower == "code":
            if not self.in_pre and self.in_code:
                self.in_code = False
                self.output.append("`")
        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6", "p"}:
            self.output.append("\n")

    def handle_data(self, data: str) -> None:
        if self.current_ignore_depth > 0:
            return
        if self.in_pre:
            self.output.append(data)
        else:
            # Collapse irregular whitespace while keeping words spaced
            cleaned = re.sub(r"[ \t]+", " ", data)
            self.output.append(cleaned)

    def get_text(self) -> str:
        raw = "".join(self.output)
        # Normalize excessive blank lines
        normalized = re.sub(r"\n{3,}", "\n\n", raw).strip()
        return html.unescape(normalized)


def html_to_markdown(raw_html: str) -> str:
    """Convert HTML documentation string to clean Markdown."""
    parser = HTMLToMarkdownParser()
    parser.feed(raw_html)
    return parser.get_text()


def fetch_url_content(url: str, timeout_sec: int = 15) -> str:
    """Fetch documentation or README from a public URL."""
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    # Smart GitHub README resolver
    github_match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)(?:/(?:tree|blob)/([^/]+)(?:/(.*))?)?$", url)
    if github_match:
        owner, repo, branch, path = github_match.groups()
        if not path or path.lower().endswith("readme.md"):
            branch = branch or "main"
            raw_candidate = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
            try:
                req = urllib.request.Request(
                    raw_candidate,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; VideoGenPipeline/1.0)"},
                )
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                    if resp.status == 200:
                        return resp.read().decode("utf-8", errors="replace")
            except Exception:
                # If 'main' failed, try 'master'
                if branch == "main":
                    try:
                        raw_master = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                        req = urllib.request.Request(
                            raw_master,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; VideoGenPipeline/1.0)"},
                        )
                        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                            if resp.status == 200:
                                return resp.read().decode("utf-8", errors="replace")
                    except Exception:
                        pass

    # Standard URL fetch
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,text/plain,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        content_type = resp.headers.get("Content-Type", "").lower()
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()
        body = resp.read().decode(charset, errors="replace")

    # If the response looks like HTML, convert it to clean markdown
    if "<html" in body.lower() or "<body" in body.lower() or "<!doctype" in body.lower():
        return html_to_markdown(body)

    return body


def load_source_content(
    source_file: Optional[str] = None,
    source_url: Optional[str] = None,
    source_text: Optional[str] = None,
) -> str:
    """Load content from source_text, source_file, or source_url.

    Priority:
    1. source_text (if provided and non-empty)
    2. source_file (read local file path)
    3. source_url (fetch via HTTP)
    """
    if source_text and source_text.strip():
        return source_text.strip()

    if source_file and source_file.strip():
        file_path = Path(source_file.strip()).resolve()
        if not file_path.exists():
            # Check relative to repository root if cwd is a subdirectory (e.g. engine/)
            repo_candidate = (Path(__file__).resolve().parent.parent.parent / source_file.strip()).resolve()
            if repo_candidate.exists():
                file_path = repo_candidate
            else:
                raise FileNotFoundError(f"Source file not found at: {file_path}")
        raw = file_path.read_text(encoding="utf-8", errors="replace")
        if file_path.suffix.lower() == ".html" or "<html" in raw.lower() or "<!doctype" in raw.lower():
            return html_to_markdown(raw)
        return raw.strip()

    if source_url and source_url.strip():
        return fetch_url_content(source_url.strip())

    return ""


def wrap_code_line(line: str, max_width: int = 46) -> List[str]:
    """Wrap or split a long code line to fit within max_width without breaking syntax abruptly."""
    if len(line) <= max_width:
        return [line]

    # Detect leading indentation
    indent_match = re.match(r"^(\s*)", line)
    indent = indent_match.group(1) if indent_match else ""
    extra_indent = indent + "  "

    sublines = []
    remaining = line

    while len(remaining) > max_width:
        # Look for natural split points within the first max_width characters
        split_idx = -1
        for sep in [", ", " => ", " && ", " || ", " + ", " (", " ", "("]:
            idx = remaining.rfind(sep, 0, max_width)
            if idx > len(indent) + 4:
                split_idx = idx + len(sep)
                break

        if split_idx == -1:
            # Force split at max_width
            split_idx = max_width

        chunk = remaining[:split_idx].rstrip()
        sublines.append(chunk)
        remaining = extra_indent + remaining[split_idx:].lstrip()

    if remaining.strip():
        sublines.append(remaining)

    return sublines


def format_code_snippet(code: str, max_lines: int = 12, max_width: int = 46) -> str:
    """Format and constraint a code block to <= max_width chars and <= max_lines."""
    raw_lines = code.strip().splitlines()
    formatted_lines: List[str] = []

    for line in raw_lines:
        wrapped = wrap_code_line(line, max_width=max_width)
        formatted_lines.extend(wrapped)
        if len(formatted_lines) >= max_lines:
            break

    total_untruncated = sum(len(wrap_code_line(l, max_width=max_width)) for l in raw_lines)
    if total_untruncated > max_lines:
        formatted_lines = formatted_lines[: max_lines - 1]
        formatted_lines.append("// ...")

    return "\n".join(formatted_lines)


def extract_source_facts(raw_text: str) -> Dict[str, Any]:
    """Extract ground-truth developer facts from raw customer documentation/code.

    Returns:
    {
        "product_name": str,
        "cli_commands": List[str],
        "code_snippets": List[Dict[str, str]],
        "api_endpoints": List[str],
        "key_points": List[str],
        "raw_text": str,
    }
    """
    if not raw_text or not raw_text.strip():
        return {
            "product_name": "",
            "cli_commands": [],
            "code_snippets": [],
            "api_endpoints": [],
            "key_points": [],
            "raw_text": "",
        }

    text = raw_text.strip()

    # 1. Product Name / Title Extraction
    product_name = ""
    # Check H1 header
    h1_match = re.search(r"^#\s+([^\n]+)", text, re.MULTILINE)
    if h1_match:
        # Strip badges or markdown links: e.g. "# Acme SDK [![npm]...](...)" -> "Acme SDK"
        cleaned_title = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)|\[.*?\]\(.*?\)", "", h1_match.group(1)).strip()
        cleaned_title = re.sub(r"[#*`_]", "", cleaned_title).strip()
        if cleaned_title:
            product_name = cleaned_title

    if not product_name:
        # Check npm package name e.g. "@acme/edgecache" or "name: package-name"
        pkg_match = re.search(r"(@[\w\-]+/[\w\-]+|npm\s+i(?:nstall)?\s+([@\w\-\/]+))", text)
        if pkg_match:
            product_name = pkg_match.group(2) or pkg_match.group(1)

    if not product_name:
        # Check H2
        h2_match = re.search(r"^##\s+([^\n]+)", text, re.MULTILINE)
        if h2_match:
            product_name = re.sub(r"[#*`_]", "", h2_match.group(1)).strip()

    # 2. CLI Commands Extraction
    cli_commands: List[str] = []
    # Match commands with explicit prefix $ or >
    shell_matches = re.findall(r"(?:^|\n)\s*[\$>]\s+([^\n]+)", text)
    for cmd in shell_matches:
        c = cmd.strip()
        if c and not c.startswith("#") and len(c) < 120:
            cli_commands.append(c)

    # Match common CLI tool lines
    cli_tool_pattern = re.compile(
        r"(?:^|\n)\s*(npm\s+(?:install|i|add|run|exec)\s+[^\n]+|"
        r"npx\s+[^\n]+|"
        r"pnpm\s+(?:add|install|i)\s+[^\n]+|"
        r"yarn\s+(?:add|install)\s+[^\n]+|"
        r"pip(?:3)?\s+install\s+[^\n]+|"
        r"uv\s+(?:pip|add|run)\s+[^\n]+|"
        r"brew\s+install\s+[^\n]+|"
        r"docker\s+(?:run|build|compose)\s+[^\n]+|"
        r"curl\s+[^\n]+|"
        r"git\s+clone\s+[^\n]+)",
        re.IGNORECASE,
    )
    for match in cli_tool_pattern.findall(text):
        c = match.strip()
        if c and len(c) < 120:
            cli_commands.append(c)

    # Deduplicate while preserving order
    seen_cmds = set()
    deduped_cmds = []
    for c in cli_commands:
        cleaned_c = c.strip()
        if cleaned_c and cleaned_c not in seen_cmds:
            seen_cmds.add(cleaned_c)
            deduped_cmds.append(cleaned_c)

    # 3. Code Snippets Extraction (Fenced blocks)
    code_snippets: List[Dict[str, str]] = []
    code_block_pattern = re.compile(r"```([a-zA-Z0-9_\-+]*)\n([\s\S]*?)```")
    for m in code_block_pattern.finditer(text):
        lang = m.group(1).strip().lower() or "typescript"
        code_body = m.group(2)
        # Skip pure shell commands if already caught
        if lang in {"bash", "sh", "shell", "console"} and any(cmd in code_body for cmd in ["npm ", "npx ", "pip ", "curl "]):
            continue
        formatted_code = format_code_snippet(code_body, max_lines=12, max_width=46)
        if formatted_code.strip():
            code_snippets.append({
                "language": lang,
                "code": formatted_code,
                "raw_lines": len(code_body.strip().splitlines()),
            })

    # 4. API Endpoints Extraction
    api_endpoints: List[str] = []
    endpoint_pattern = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[a-zA-Z0-9_\-\.\/\{\}]+)")
    for verb, path in endpoint_pattern.findall(text):
        endpoint = f"{verb.upper()} {path}"
        if endpoint not in api_endpoints:
            api_endpoints.append(endpoint)

    # 5. Key Points & Benchmark Metrics Extraction
    key_points: List[str] = []
    # Markdown bullets
    bullet_pattern = re.compile(r"(?:^|\n)\s*[-*•]\s+([^\n]+)")
    for b in bullet_pattern.findall(text):
        cleaned_b = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", b).strip()
        cleaned_b = re.sub(r"[`*]", "", cleaned_b).strip()
        if len(cleaned_b) > 10 and len(cleaned_b) < 160:
            if cleaned_b not in key_points:
                key_points.append(cleaned_b)

    # Benchmark metrics: e.g. "10x faster", "99.9% cache hit", "2.4ms latency"
    metric_pattern = re.compile(r"([^.\n]*\b(?:\d+(?:\.\d+)?(?:x|ms|%|req/s|rps|MB|GB|KB))\b[^.\n]*)", re.IGNORECASE)
    for m in metric_pattern.findall(text):
        cleaned_m = re.sub(r"[`*]", "", m).strip()
        if len(cleaned_m) > 10 and len(cleaned_m) < 140:
            if cleaned_m not in key_points:
                key_points.append(cleaned_m)

    return {
        "product_name": product_name or "Developer Tool",
        "cli_commands": deduped_cmds,
        "code_snippets": code_snippets,
        "api_endpoints": api_endpoints,
        "key_points": key_points[:8],
        "raw_text": text,
    }


def format_source_summary(facts: Dict[str, Any]) -> str:
    """Generate a concise textual summary of ingested source facts."""
    if not facts:
        return "No source content ingested."

    parts = []
    if facts.get("product_name"):
        parts.append(f"Product: {facts['product_name']}")
    if facts.get("cli_commands"):
        parts.append(f"{len(facts['cli_commands'])} CLI command(s)")
    if facts.get("code_snippets"):
        parts.append(f"{len(facts['code_snippets'])} code snippet(s)")
    if facts.get("api_endpoints"):
        parts.append(f"{len(facts['api_endpoints'])} API endpoint(s)")
    if facts.get("key_points"):
        parts.append(f"{len(facts['key_points'])} key point(s)")

    return " | ".join(parts) if parts else "Source content parsed (0 facts identified)"
