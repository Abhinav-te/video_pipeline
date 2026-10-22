"""
tests/test_validation.py

Unit tests for Technical B2B Video Validation Gate & Schema Enforcement.
Verifies that:
1. Universal B2B scene types (show_code, workflow_state_transition, show_metric, takeaway_cta, hook_scene, etc.) pass validation.
2. Obsolete STEM scene types (math_equation, quantum_sim, physics_sim, etc.) are strictly rejected.
3. Python / TypeScript syntax validation behaves correctly on code scenes.
4. Workflow state transitions require valid entities and events.
5. BentoGrid cards and metric scenes require evidence-backed cards.
6. Script plans require required narrative beats (hook, workflow / comparison, takeaway).
"""

import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from validation.schema import (
    validate_script_plan,
    validate_or_raise,
    resolve_script_subject,
    ScriptValidationError,
    VALID_SCENE_TYPES,
    ALL_SUBJECTS,
)


class TestB2BValidation(unittest.TestCase):

    def test_universal_b2b_scene_types_pass_validation(self):
        """
        Verify that all standard B2B technical scene types pass validation
        when provided with required narrative structure.
        """
        plan = {
            "title": "Inngest Durable Execution Guide",
            "subject": "code",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Problem Hook",
                    "narration": "In distributed background jobs, network crashes cause naive retries to duplicate operations.",
                    "visual_type": "hook_scene",
                    "visual": {
                        "headline": "DISTRIBUTED RETRY TRAP",
                        "items": [{"label": "Step 1", "status": "completed"}],
                    },
                },
                {
                    "scene_id": 2,
                    "title": "Step Run Syntax",
                    "narration": "Wrap asynchronous operations in step.run to isolate execution state.",
                    "visual_type": "show_code",
                    "code": "const billing = await step.run('billing', async () => getBilling(id));",
                },
                {
                    "scene_id": 3,
                    "title": "State Transition Graph",
                    "narration": "When step two fails with a 503, the retry reuses step one memoized output.",
                    "visual_type": "workflow_state_transition",
                    "visual": {
                        "entities": [{"id": "s1", "label": "step-1"}],
                        "events": [{"target": "s1", "action": "succeed", "label": "DONE"}],
                    },
                },
                {
                    "scene_id": 4,
                    "title": "Production Guarantees",
                    "narration": "Completed steps never re-execute while failed steps retry independently.",
                    "visual_type": "show_metric",
                    "visual": {
                        "cards": [{"title": "Memoized State", "description": "Output is cached"}],
                    },
                },
                {
                    "scene_id": 5,
                    "title": "Next Steps",
                    "narration": "Install the SDK and wrap critical tasks in step.run today.",
                    "visual_type": "takeaway_cta",
                    "visual": {
                        "takeaway": "Durable execution without queues.",
                        "docs_url": "inngest.com/docs/step-run",
                    },
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected valid B2B plan to pass, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_obsolete_stem_scene_types_rejected(self):
        """
        Verify that obsolete STEM scene types (math_equation, quantum_sim, physics_sim,
        chemistry_reaction, mechanics_fbd, electrical_grid) are strictly rejected.
        """
        obsolete_types = [
            "math_equation",
            "quantum_sim",
            "physics_sim",
            "chemistry_reaction",
            "mechanics_fbd",
            "electrical_grid",
            "function_graph",
        ]

        for obs in obsolete_types:
            plan = {
                "title": f"Test {obs}",
                "subject": "code",
                "duration": 60,
                "scenes": [
                    {
                        "scene_id": 1,
                        "title": "Intro Hook",
                        "narration": "Exploring modern cloud architecture patterns.",
                        "visual_type": "fullscreen_text",
                    },
                    {
                        "scene_id": 2,
                        "title": f"Scene with {obs}",
                        "narration": "This scene uses an obsolete visual primitive.",
                        "visual_type": obs,
                    },
                    {
                        "scene_id": 3,
                        "title": "Outro",
                        "narration": "Wrap up and conclusion.",
                        "visual_type": "takeaway_cta",
                    },
                ],
            }
            is_valid, errors = validate_script_plan(plan)
            self.assertFalse(is_valid, f"Expected obsolete scene_type '{obs}' to be rejected.")
            self.assertTrue(
                any("invalid scene_type" in e for e in errors),
                f"Expected invalid scene_type error for '{obs}', got: {errors}",
            )

    def test_missing_required_narrative_beats_fails(self):
        """
        Verify that scripts missing a comparison or workflow_state_transition fail validation.
        """
        plan = {
            "title": "Incomplete Script",
            "subject": "code",
            "duration": 30,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Intro Hook",
                    "narration": "Discover modern workflow primitives.",
                    "visual_type": "fullscreen_text",
                },
                {
                    "scene_id": 2,
                    "title": "Terminal",
                    "narration": "Install the package from npm.",
                    "visual_type": "terminal",
                    "command": "npm install inngest",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("Script plan must contain at least one 'comparison'" in e and "workflow_state_transition" in e for e in errors),
            f"Expected missing workflow error, got: {errors}",
        )

    def test_python_syntax_validation_on_code_scenes(self):
        """
        Verify that invalid Python code in a Python code scene is rejected with AST error.
        """
        plan = {
            "title": "Python SDK Guide",
            "subject": "code",
            "duration": 35,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Intro Hook",
                    "narration": "Learn how Python functions execute durably in the cloud.",
                    "visual_type": "hook_scene",
                },
                {
                    "scene_id": 2,
                    "title": "Workflow",
                    "narration": "Trace the step transitions as tasks succeed or retry.",
                    "visual_type": "workflow_state_transition",
                    "visual": {
                        "entities": [{"id": "s1", "label": "step"}],
                        "events": [{"target": "s1", "action": "succeed"}],
                    },
                },
                {
                    "scene_id": 3,
                    "title": "Broken Code",
                    "narration": "Here is our broken Python function definition.",
                    "visual_type": "code_reveal",
                    "language": "python",
                    "code_snippet": "def broken_syntax(x\n    return x + 1",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("AST syntax check failed" in e or "Syntax Error" in e for e in errors),
            f"Expected AST syntax failure, got: {errors}",
        )

    def test_resolve_script_subject(self):
        """
        Verify resolve_script_subject accurately detects code, systems, and devtools.
        """
        self.assertEqual(resolve_script_subject({"subject": "code"}), "code")
        self.assertEqual(resolve_script_subject({"subject": "devtools"}), "devtools")
        self.assertEqual(resolve_script_subject({"subject": "systems"}), "systems")
        # Inferred from code primitives
        self.assertEqual(
            resolve_script_subject({"scenes": [{"scene_type": "code_reveal"}]}),
            "code",
        )
        self.assertEqual(
            resolve_script_subject({"scenes": [{"scene_type": "terminal"}]}),
            "devtools",
        )

    def test_validate_or_raise_throws_exception(self):
        """
        Verify validate_or_raise raises ScriptValidationError on invalid plan.
        """
        bad_plan = {"title": "Bad", "scenes": []}
        with self.assertRaises(ScriptValidationError):
            validate_or_raise(bad_plan)


if __name__ == "__main__":
    unittest.main()
