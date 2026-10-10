import os
import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_DIR))

from unittest.mock import MagicMock, patch
from validation import (
    validate_script_plan,
    validate_or_raise,
    ScriptValidationError,
    VALID_SCENE_TYPES,
    MIN_WORDS_PER_BEAT,
    MAX_WORDS_PER_BEAT,
    MAX_DIAGRAM_NODES,
)
from director.script import DEFAULT_MODEL_CHAIN, generate_script
import generate as gen_module


def create_valid_test_script():
    """Returns a fully conformant multi-beat script plan."""
    return {
        "title": "Python Dictionary Keys Trick",
        "schema_version": "2.1",
        "scenes": [
            {
                "scene_type": "fullscreen_text",
                "spoken_text": "Did you know dictionary keys can be tuples?",
                "display_text": "TUPLE DICTIONARY KEYS",
                "emphasis_word": "tuples",
            },
            {
                "scene_type": "code_reveal",
                "spoken_text": "Here is how you define multi-dimensional coordinates easily.",
                "code_snippet": "points = {(0, 0): 'origin', (1, 2): 'target'}\nprint(points[(0, 0)])",
                "focus_phrase": "points = {(0, 0): 'origin'",
            },
            {
                "scene_type": "diagram",
                "spoken_text": "Tuples are immutable so their hashes never change.",
                "nodes": ["Tuple Created", "Immutable Hash", "Fast Lookup"],
            },
            {
                "scene_type": "terminal",
                "spoken_text": "Running this script outputs origin right away.",
                "code_snippet": "$ python main.py\norigin",
            },
            {
                "scene_type": "comparison",
                "spoken_text": "Never use mutable lists as dictionary key lookups.",
                "problem_label": "Fails With TypeError",
                "problem_code": "bad = {[1, 2]: 'fails'}",
                "solution_label": "Works With Tuples",
                "solution_code": "good = {(1, 2): 'works'}",
            },
            {
                "scene_type": "code_transform",
                "spoken_text": "Always remember that dictionary keys must be hashable.",
                "code_snippet": "valid_key = (42, 'answer')\ndata = {valid_key: True}",
            },
        ],
    }


class TestMilestone2ValidationGate(unittest.TestCase):
    def test_valid_script_passes(self):
        """Verify that a well-formed script plan passes validation with zero errors."""
        script = create_valid_test_script()
        is_valid, errors = validate_script_plan(script)
        self.assertTrue(is_valid, f"Expected valid script to pass, got errors: {errors}")
        self.assertEqual(len(errors), 0)

        # validate_or_raise should not raise
        try:
            validate_or_raise(script)
        except ScriptValidationError:
            self.fail("validate_or_raise raised ScriptValidationError unexpectedly on valid script")

    def test_invalid_ast_in_code_reveal(self):
        """Verify that invalid Python syntax in code_reveal is caught before downstream stages."""
        script = create_valid_test_script()
        script["scenes"][1]["code_snippet"] = "def broken_syntax(:"  # missing closing paren

        is_valid, errors = validate_script_plan(script)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("AST syntax check failed" in err for err in errors),
            f"Expected AST syntax error in errors list. Got: {errors}",
        )

    def test_invalid_ast_in_code_transform(self):
        """Verify that invalid Python syntax in code_transform is caught."""
        script = create_valid_test_script()
        script["scenes"][5]["code_snippet"] = "for in range(10): pass"  # invalid target

        is_valid, errors = validate_script_plan(script)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("code_transform" in err and "AST syntax check failed" in err for err in errors),
            f"Expected code_transform AST error in errors. Got: {errors}",
        )

    def test_invalid_ast_in_comparison_problem_and_solution(self):
        """Verify that comparison scenes validate both problem_code and solution_code AST syntax."""
        # Problem code broken
        script1 = create_valid_test_script()
        script1["scenes"][4]["problem_code"] = "def bad(x: pass"
        is_valid, errors = validate_script_plan(script1)
        self.assertFalse(is_valid)
        self.assertTrue(any("problem_code AST syntax check failed" in err for err in errors))

        # Solution code broken
        script2 = create_valid_test_script()
        script2["scenes"][4]["solution_code"] = "class 123InvalidName: pass"
        is_valid, errors = validate_script_plan(script2)
        self.assertFalse(is_valid)
        self.assertTrue(any("solution_code AST syntax check failed" in err for err in errors))

    def test_word_count_limits_per_beat(self):
        """Verify beat bounds (5 to 11 words per spoken_text)."""
        # Under minimum (< 5 words)
        script_under = create_valid_test_script()
        script_under["scenes"][1]["spoken_text"] = "Too short beat."  # 3 words
        is_valid, errors = validate_script_plan(script_under)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("Minimum is 5 words per beat" in err for err in errors),
            f"Expected minimum word count error. Got: {errors}",
        )

        # Over maximum (> 11 words)
        script_over = create_valid_test_script()
        script_over["scenes"][1]["spoken_text"] = (
            "This beat contains way too many words because it exceeds the maximum allowed limit of eleven."
        )  # 16 words
        is_valid, errors = validate_script_plan(script_over)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("Maximum is 11 words per beat" in err for err in errors),
            f"Expected maximum word count error. Got: {errors}",
        )

    def test_unsupported_scene_type(self):
        """Verify that unsupported visual primitives are rejected."""
        script = create_valid_test_script()
        script["scenes"][2]["scene_type"] = "3d_voxel_mesh"  # unsupported
        is_valid, errors = validate_script_plan(script)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("invalid scene_type: '3d_voxel_mesh'" in err for err in errors),
            f"Expected invalid scene_type error. Got: {errors}",
        )

    def test_scene_1_must_be_fullscreen_text(self):
        """Verify Scene 1 must be fullscreen_text hook."""
        script = create_valid_test_script()
        script["scenes"][0]["scene_type"] = "code_reveal"
        script["scenes"][0]["code_snippet"] = "x = 42"
        is_valid, errors = validate_script_plan(script)
        self.assertFalse(is_valid)
        self.assertTrue(any("Scene 1 must be 'fullscreen_text'" in err for err in errors))

    def test_must_contain_comparison_scene(self):
        """Verify script plan must contain at least one comparison scene."""
        script = create_valid_test_script()
        # Remove comparison scene
        script["scenes"] = [s for s in script["scenes"] if s["scene_type"] != "comparison"]
        is_valid, errors = validate_script_plan(script)
        self.assertFalse(is_valid)
        self.assertTrue(any("must contain at least one 'comparison' scene" in err for err in errors))

    def test_diagram_node_bounds(self):
        """Verify diagram scenes require 1 to 3 nodes max."""
        # > 3 nodes
        script_over = create_valid_test_script()
        script_over["scenes"][2]["nodes"] = ["Node 1", "Node 2", "Node 3", "Node 4"]
        is_valid, errors = validate_script_plan(script_over)
        self.assertFalse(is_valid)
        self.assertTrue(any("Maximum is 3" in err for err in errors))

        # Empty nodes
        script_empty = create_valid_test_script()
        script_empty["scenes"][2]["nodes"] = []
        is_valid, errors = validate_script_plan(script_empty)
        self.assertFalse(is_valid)
        self.assertTrue(any("requires non-empty 'nodes' list" in err for err in errors))

    def test_director_fallback_chain_cleaned(self):
        """Verify fallback chain in engine/director/script.py contains only valid active models."""
        invalid_models = ["gemini-3.6-flash", "gemini-3.5-flash"]
        for bad_model in invalid_models:
            self.assertNotIn(
                bad_model,
                DEFAULT_MODEL_CHAIN,
                f"Unreleased model {bad_model} found in DEFAULT_MODEL_CHAIN: {DEFAULT_MODEL_CHAIN}",
            )
        self.assertTrue(len(DEFAULT_MODEL_CHAIN) >= 3, "Expected at least 3 fallback models in chain")
        self.assertEqual(DEFAULT_MODEL_CHAIN[0], "gemini-3.8-flash")
        self.assertIn("gemini-2.5-flash", DEFAULT_MODEL_CHAIN)
        self.assertIn("gemini-2.0-flash", DEFAULT_MODEL_CHAIN)

    def test_scene_count_bounds(self):
        """Verify scene count limits (minimum 2 scenes, maximum 35 scenes)."""
        # Zero scenes
        script_empty = create_valid_test_script()
        script_empty["scenes"] = []
        is_valid, errors = validate_script_plan(script_empty)
        self.assertFalse(is_valid)
        self.assertTrue(any("zero scenes" in err.lower() for err in errors))

        # Single scene (< 2)
        script_single = create_valid_test_script()
        script_single["scenes"] = [script_single["scenes"][0]]
        is_valid, errors = validate_script_plan(script_single)
        self.assertFalse(is_valid)
        self.assertTrue(any("at least 2 scenes" in err for err in errors))

        # Excessive scenes (> 35)
        script_excess = create_valid_test_script()
        extra_scene = script_excess["scenes"][1]  # code_reveal
        script_excess["scenes"] = [script_excess["scenes"][0]] + [extra_scene] * 35 + [script_excess["scenes"][4]]
        is_valid, errors = validate_script_plan(script_excess)
        self.assertFalse(is_valid)
        self.assertTrue(any("exceeding maximum of 35" in err for err in errors))

    def test_engine_generate_validate_script_halts_on_invalid_plan(self):
        """Verify generate.py:validate_script outputs [VALIDATION:ERROR] and halts on invalid plan."""
        bad_script = create_valid_test_script()
        bad_script["scenes"][1]["code_snippet"] = "def bad_ast(: pass"

        with self.assertRaises(SystemExit) as cm:
            gen_module.validate_script(bad_script)
        self.assertNotEqual(cm.exception.code, 0)

    @patch("director.script._get_client")
    def test_director_fallback_on_404_client_error(self, mock_get_client):
        """Verify that 404 client errors fall back to the next model in the chain without hard crashing."""
        import json
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        valid_script = create_valid_test_script()
        mock_success_response = MagicMock()
        mock_success_response.text = json.dumps(valid_script)

        calls = []

        def side_effect(model, contents, config):
            calls.append(model)
            if model == "gemini-3.8-flash":
                raise Exception("404 ClientError: models/gemini-3.8-flash is not found for API version v1beta")
            return mock_success_response

        mock_client.models.generate_content.side_effect = side_effect

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key_123"}):
            script = generate_script("Python Tuples", 60)

        self.assertEqual(script["title"], valid_script["title"])
        self.assertEqual(calls, ["gemini-3.8-flash", "gemini-2.5-flash"])

    @patch("director.script._get_client")
    def test_director_fails_when_all_models_404(self, mock_get_client):
        """Verify that when all models in the chain return 404, RuntimeError is raised after trying all models."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        calls = []

        def side_effect(model, contents, config):
            calls.append(model)
            raise Exception(f"404 NOT_FOUND: {model} not found")

        mock_client.models.generate_content.side_effect = side_effect

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key_123"}):
            with self.assertRaises(RuntimeError) as ctx:
                generate_script("Python Tuples", 60)

        self.assertIn("exhausted or failed", str(ctx.exception))
        self.assertEqual(calls, DEFAULT_MODEL_CHAIN)


if __name__ == "__main__":
    unittest.main()


