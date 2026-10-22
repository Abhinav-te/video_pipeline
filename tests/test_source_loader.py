"""tests/test_source_loader.py

Fast unit tests for customer source & internet documentation ingestion (Phase A.2).
Tests execute in < 2 seconds without external network dependencies.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from engine.ingestion.source_loader import (
    html_to_markdown,
    load_source_content,
    wrap_code_line,
    format_code_snippet,
    extract_source_facts,
    format_source_summary,
)
from engine.director.mock_library import get_mock_script, inject_source_facts_into_mock


def test_html_to_markdown_clean_conversion():
    raw_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Sample Docs</title>
      <script>console.log("malicious")</script>
      <style>body { background: red; }</style>
    </head>
    <body>
      <nav><a href="/docs">Docs</a></nav>
      <h1>EdgeStore Engine v2.0</h1>
      <p>Low-latency key-value storage designed for serverless runtimes.</p>
      <pre><code class="language-bash">$ npm install @edgestore/client@latest</code></pre>
      <ul>
        <li>99.99% Availability SLA</li>
        <li>1.2ms Edge Read Latency</li>
      </ul>
      <footer>Copyright 2026</footer>
    </body>
    </html>
    """
    md = html_to_markdown(raw_html)
    assert "# EdgeStore Engine v2.0" in md
    assert "console.log" not in md
    assert "background: red" not in md
    assert "Copyright 2026" not in md
    assert "npm install @edgestore/client@latest" in md
    assert "99.99% Availability SLA" in md


def test_wrap_code_line_constraints():
    short_line = 'const client = new CacheClient();'
    assert wrap_code_line(short_line, max_width=46) == [short_line]

    long_line = 'const response = await client.veryLongMethodCallWithLotsOfArguments("user:123", { timeout: 5000, retryCount: 3 });'
    wrapped = wrap_code_line(long_line, max_width=46)
    assert len(wrapped) > 1
    for w in wrapped:
        assert len(w) <= 50  # Allows slight boundary buffer


def test_format_code_snippet_preserves_syntax():
    code_block = "```ts\n" + "\n".join([f"const line_{i} = doSomething({i});" for i in range(25)]) + "\n```"
    formatted = format_code_snippet(code_block)
    lines = formatted.splitlines()
    # Code display invariant: never truncate code with fixed line limits or // ...
    assert len(lines) == 25
    assert not formatted.startswith("```")
    assert "// ..." not in lines


def test_extract_source_facts_full_parse():
    sample_doc = """# FastKV Edge Storage
FastKV is a zero-config key-value store for global edge compute.

## Installation
```bash
$ npm install @fastkv/edge@latest
$ npx fastkv init --cluster us-east
```

## Migration from v1
```ts
import { FastKV } from "@fastkv/edge";

const kv = new FastKV({ region: "auto" });
const user = await kv.getOrSet("user:101", async () => {
  return await fetchUser("101");
});
```

## REST Endpoints
- GET /v1/kv/keys - List all keys
- POST /v1/kv/batch - Batch put

## Benchmarks
- 99.95% cache hit rate
- 0.8ms edge lookup latency
"""
    facts = extract_source_facts(sample_doc)
    assert "FastKV" in facts["product_name"]
    assert "npm install @fastkv/edge@latest" in facts["cli_commands"]
    assert "npx fastkv init --cluster us-east" in facts["cli_commands"]
    assert len(facts["code_snippets"]) >= 1
    assert "GET /v1/kv/keys" in facts["api_endpoints"]
    assert "POST /v1/kv/batch" in facts["api_endpoints"]
    assert any("hit rate" in p for p in facts["key_points"])

    summary = format_source_summary(facts)
    assert "Product:" in summary
    assert "CLI command(s)" in summary
    assert "code snippet(s)" in summary


def test_load_source_content_file_and_text(tmp_path):
    text_content = "# Direct Text Content\nSome details here."
    assert load_source_content(source_text=text_content) == text_content

    test_file = tmp_path / "sample.md"
    test_file.write_text("# From File\nFile details here.", encoding="utf-8")
    loaded = load_source_content(source_file=str(test_file))
    assert loaded == "# From File\nFile details here."


def test_mock_script_facts_injection():
    facts = {
        "product_name": "Turbopack Edge",
        "cli_commands": ["npm install turbopack-edge@next"],
        "code_snippets": [
            {"language": "ts", "code": "const client = legacy();"},
            {"language": "ts", "code": "import { Turbo } from 'turbopack-edge';\nconst t = new Turbo();"},
        ],
        "api_endpoints": ["GET /v2/turbo/stream"],
        "key_points": ["10x faster bundling", "0.5ms cold starts"],
    }

    script = get_mock_script("Turbopack Edge Launch", 35, "devtools", source_facts=facts)
    scenes_by_type = {s.get("visual_type"): s for s in script["scenes"]}

    # Scene 1: fullscreen_text
    assert "fullscreen_text" in scenes_by_type
    assert "TURBOPACK EDGE" in scenes_by_type["fullscreen_text"]["display_text"]

    # Scene 2: terminal
    assert "terminal" in scenes_by_type
    assert scenes_by_type["terminal"]["commands"][0]["cmd"] == "npm install turbopack-edge@next"

    # Scene 3: code_transform
    assert "code_transform" in scenes_by_type
    assert "legacy()" in scenes_by_type["code_transform"]["before_code"]
    assert "turbopack-edge" in scenes_by_type["code_transform"]["after_code"]

    # Scene 4: code_reveal
    assert "code_reveal" in scenes_by_type
    assert "turbopack-edge" in scenes_by_type["code_reveal"]["code"]

    # Scene 5: diagram
    assert "diagram" in scenes_by_type
    assert scenes_by_type["diagram"]["request_method"] == "GET /v2/turbo/stream"

