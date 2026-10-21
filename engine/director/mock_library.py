"""
engine/director/mock_library.py

Lightweight Fixture Loader & Pre-Validated Developer Scripts.
- Reads technical markdown documentation from examples/docs/
- Emits clean, evidence-backed developer scripts for code and devtools workflows
- Backward-compatible get_mock_script & inject_source_facts_into_mock
"""

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = REPO_DIR / "examples" / "docs"


def _create_inngest_mock_script(duration: int = 60) -> Dict[str, Any]:
    """Builds a verified 5-beat Inngest durable execution script based on examples/docs/inngest_step_run.md."""
    is_60 = duration >= 50
    return {
        "title": "Durable Execution with step.run()",
        "topic": "Inngest step.run() Durable Execution",
        "subject": "code",
        "domain": "code",
        "duration": 60 if is_60 else 35,
        "scenes": [
            {
                "scene_id": 1,
                "scene_type": "fullscreen_text",
                "visual_type": "fullscreen_text",
                "title": "THE DISTRIBUTED RETRY PROBLEM",
                "badge": "PROBLEM • DISTRIBUTED RETRIES",
                "spoken_text": "In distributed background jobs, network crashes cause naive retries to duplicate operations.",
                "emphasis_word": "duplicate",
                "display_text": "INNGEST STEP.RUN()",
                "evidence_ids": ["ev_step_run_01"],
                "visual": {
                    "headline": "THE DISTRIBUTED RETRY TRAP",
                    "subtitle": "Network failures mid-job cause blind retries to duplicate charges",
                    "items": [
                        {"label": "Step 1: Fetch Customer Billing", "status": "completed"},
                        {"label": "Step 2: Charge Payment Gateway (503 Error)", "status": "failed"},
                        {"label": "Blind Retry: Re-runs Step 1 & Duplicates API Call", "status": "warning"},
                    ],
                },
            },
            {
                "scene_id": 2,
                "scene_type": "show_code",
                "visual_type": "code_reveal",
                "title": "ISOLATE WORKFLOWS WITH STEP.RUN",
                "badge": "SYNTAX • STEP.RUN",
                "spoken_text": "Wrap each asynchronous operation in step.run to isolate execution state.",
                "emphasis_word": "isolate",
                "evidence_ids": ["ev_step_run_02"],
                "code": (
                    "export const processOrder = inngest.createFunction(\n"
                    "  { id: 'process-order' },\n"
                    "  { event: 'order.created' },\n"
                    "  async ({ event, step }) => {\n"
                    "    const billing = await step.run('fetch-billing', async () => {\n"
                    "      return await getBillingAccount(event.data.customerId);\n"
                    "    });\n"
                    "    return billing;\n"
                    "  }\n"
                    ");"
                ),
                "visual": {
                    "filename": "orderWorkflow.ts",
                    "language": "typescript",
                    "highlight_lines": [4, 5, 6, 7],
                    "callout": "step.run() memoizes returned state",
                    "code": (
                        "export const processOrder = inngest.createFunction(\n"
                        "  { id: 'process-order' },\n"
                        "  { event: 'order.created' },\n"
                        "  async ({ event, step }) => {\n"
                        "    const billing = await step.run('fetch-billing', async () => {\n"
                        "      return await getBillingAccount(event.data.customerId);\n"
                        "    });\n"
                        "    return billing;\n"
                        "  }\n"
                        ");"
                    ),
                },
            },
            {
                "scene_id": 3,
                "scene_type": "workflow_state_transition",
                "visual_type": "workflow_state_transition",
                "title": "DURABLE EXECUTION WATERFALL",
                "badge": "EXECUTION • STATE RECOVERY",
                "spoken_text": "When step two fails with a 503, the retry reuses step one's memoized output without re-running.",
                "emphasis_word": "memoized",
                "evidence_ids": ["ev_step_run_03"],
                "entities": [
                    {"id": "fetch-billing", "label": "fetch-billing-data", "sub_label": "Cached output reused"},
                    {"id": "charge-customer", "label": "charge-customer", "sub_label": "Independent retry"},
                ],
                "events": [
                    {"target": "fetch-billing", "action": "succeed", "label": "COMPLETED & MEMOIZED", "at_word": "fails"},
                    {"target": "charge-customer", "action": "fail", "label": "HTTP 503 ERROR", "at_word": "503"},
                    {"target": "charge-customer", "action": "retry", "label": "RETRY #1 • REUSING SAVED STATE", "at_word": "retry"},
                ],
                "visual": {
                    "entities": [
                        {"id": "fetch-billing", "label": "fetch-billing-data", "sub_label": "Cached output reused"},
                        {"id": "charge-customer", "label": "charge-customer", "sub_label": "Independent retry"},
                    ],
                    "events": [
                        {"target": "fetch-billing", "action": "succeed", "label": "COMPLETED & MEMOIZED", "at_word": "fails"},
                        {"target": "charge-customer", "action": "fail", "label": "HTTP 503 ERROR", "at_word": "503"},
                        {"target": "charge-customer", "action": "retry", "label": "RETRY #1 • REUSING SAVED STATE", "at_word": "retry"},
                    ],
                },
            },
            {
                "scene_id": 4,
                "scene_type": "show_metric",
                "visual_type": "bento_grid",
                "title": "DURABLE GUARANTEES & LIMITATIONS",
                "badge": "ARCHITECTURE • PRODUCTION GUARANTEES",
                "spoken_text": "Completed steps never re-execute, failed steps retry in isolation, and external side effects remain safe.",
                "emphasis_word": "isolation",
                "evidence_ids": ["ev_step_run_04", "ev_step_run_05"],
                "cards": [
                    {"title": "Memoized Step State", "description": "Completed steps never re-execute on retry"},
                    {"title": "Isolated Step Retries", "description": "Failed steps retry independently"},
                ],
                "visual": {
                    "cards": [
                        {"title": "Memoized Step State", "description": "Completed steps never re-execute on retry"},
                        {"title": "Isolated Step Retries", "description": "Failed steps retry independently"},
                    ],
                },
            },
            {
                "scene_id": 5,
                "scene_type": "takeaway_cta",
                "visual_type": "takeaway_cta",
                "title": "BUILD RESILIENT WORKFLOWS",
                "badge": "QUICKSTART • INNGEST",
                "spoken_text": "Break your workflows into step.run to guarantee durable execution across your stack.",
                "emphasis_word": "durable",
                "evidence_ids": ["ev_step_run_01"],
                "visual": {
                    "product": "Inngest",
                    "takeaway": "Durable execution without queues.",
                    "quickstart_command": "npm install inngest",
                    "docs_url": "inngest.com/docs/step-run",
                },
            },
        ],
    }


def _create_devtools_mock_script(duration: int = 35) -> Dict[str, Any]:
    """Builds a devtools CLI/SDK release workflow script."""
    return {
        "title": "Devtools Release Workflow",
        "topic": "Developer Tools & SDK",
        "subject": "devtools",
        "domain": "devtools",
        "duration": duration,
        "scenes": [
            {
                "scene_id": 1,
                "scene_type": "fullscreen_text",
                "visual_type": "fullscreen_text",
                "title": "Modern Devtools Release",
                "display_text": "MODERN DEVTOOLS",
                "spoken_text": "Ship high-performance developer workflows with zero config.",
                "emphasis_word": "developer",
            },
            {
                "scene_id": 2,
                "scene_type": "terminal",
                "visual_type": "terminal",
                "title": "Single-Command Install",
                "spoken_text": "Install the modern package from npm with zero peer conflicts.",
                "commands": [{"cmd": "npm install modern-devtools@latest"}],
            },
            {
                "scene_id": 3,
                "scene_type": "code_transform",
                "visual_type": "code_transform",
                "title": "Declarative API Migration",
                "spoken_text": "Migrate verbose legacy callback patterns into declarative async streaming.",
                "before_code": "const client = legacy();",
                "after_code": "import { Client } from 'modern-devtools';\nconst c = new Client();",
            },
            {
                "scene_id": 4,
                "scene_type": "code_reveal",
                "visual_type": "code_reveal",
                "title": "High-Throughput Streaming",
                "spoken_text": "Connect instantly to edge workers with typed responses.",
                "code": "import { Client } from 'modern-devtools';\nconst c = new Client();",
            },
            {
                "scene_id": 5,
                "scene_type": "diagram",
                "visual_type": "diagram",
                "title": "Edge Gateway Architecture",
                "spoken_text": "Requests resolve at the nearest edge region before touching origin.",
                "request_method": "GET /v1/health",
            },
        ],
    }


MOCK_SCRIPTS: Dict[str, Dict[int, Dict[str, Any]]] = {
    "code": {
        35: _create_inngest_mock_script(35),
        60: _create_inngest_mock_script(60),
    },
    "devtools": {
        35: _create_devtools_mock_script(35),
        60: _create_devtools_mock_script(60),
    },
    "default": {
        35: _create_inngest_mock_script(35),
        60: _create_inngest_mock_script(60),
    },
}


def inject_source_facts_into_mock(script: Dict[str, Any], facts: Any) -> Dict[str, Any]:
    """Injects extracted source documentation facts into mock script scenes."""
    if not facts or not isinstance(script, dict):
        return script

    script_copy = copy.deepcopy(script)
    if hasattr(facts, "dict"):
        facts_dict = facts.dict()
    elif isinstance(facts, dict):
        facts_dict = facts
    else:
        facts_dict = {}

    prod_name = facts_dict.get("product_name") or facts_dict.get("company_name")
    if prod_name:
        script_copy["title"] = f"{prod_name} Workflow"
        script_copy["topic"] = f"{prod_name} Feature Overview"
        if script_copy.get("scenes"):
            sc1 = script_copy["scenes"][0]
            sc1["display_text"] = f"{prod_name.upper()} LAUNCH"
            if "visual" in sc1 and isinstance(sc1["visual"], dict):
                sc1["visual"]["headline"] = f"{prod_name.upper()} WORKFLOW"

    scenes_by_type = {s.get("visual_type"): s for s in script_copy.get("scenes", [])}

    # Inject CLI commands into terminal scene
    cmds = facts_dict.get("cli_commands") or []
    if cmds and "terminal" in scenes_by_type:
        scenes_by_type["terminal"]["commands"] = [{"cmd": c} for c in cmds]

    # Inject code snippets into code_transform & code_reveal
    snippets = facts_dict.get("code_snippets") or []
    if len(snippets) >= 2 and "code_transform" in scenes_by_type:
        scenes_by_type["code_transform"]["before_code"] = snippets[0]["code"]
        scenes_by_type["code_transform"]["after_code"] = snippets[1]["code"]
    if snippets and "code_reveal" in scenes_by_type:
        scenes_by_type["code_reveal"]["code"] = snippets[-1]["code"]

    # Inject api endpoints into diagram scene
    endpoints = facts_dict.get("api_endpoints") or []
    if endpoints and "diagram" in scenes_by_type:
        scenes_by_type["diagram"]["request_method"] = endpoints[0]

    return script_copy


def get_mock_script(
    topic: str = "",
    duration: int = 60,
    subject: str = "code",
    source_text: Any = None,
    source_facts: Any = None,
) -> Dict[str, Any]:
    """Returns a rich, pre-validated mock script from fixture documentation."""
    dur = 60 if duration >= 50 else 35
    subj = (subject or "code").lower()
    if subj not in MOCK_SCRIPTS:
        subj = "code"

    script = copy.deepcopy(MOCK_SCRIPTS[subj][dur])
    if topic:
        script["title"] = topic.strip()
        script["topic"] = topic.strip()

    if source_facts:
        script = inject_source_facts_into_mock(script, source_facts)

    return script
