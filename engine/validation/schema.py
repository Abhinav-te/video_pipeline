"""
Validation Gate & Contract Enforcement for AI Director Script Plans.

Formalizes the scene plan contract, enforces beat lengths (5–11 words),
diagram node bounds, and runs pre-flight Python AST syntax checks.
"""

from typing import Any, Dict, List, Tuple
from validation.code import check_syntax, check_terminal_snippet

VALID_SCENE_TYPES = {
    "fullscreen_text",
    "code_reveal",
    "code_transform",
    "terminal",
    "diagram",
    "comparison",
}

MIN_WORDS_PER_BEAT = 5
MAX_WORDS_PER_BEAT = 11
MAX_DIAGRAM_NODES = 3
MIN_SCENES = 2
MAX_SCENES = 35


class ScriptValidationError(ValueError):
    """Raised when a script plan fails validation gate checks."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def validate_script_plan(script_data: Any) -> Tuple[bool, List[str]]:
    """
    Validates a complete script plan against schema contracts and AST syntax.

    Returns:
        (True, []) if completely valid.
        (False, [list of error messages]) if any violations are found.
    """
    errors: List[str] = []

    if not isinstance(script_data, dict):
        return False, ["Script plan must be a JSON object / dict."]

    # Title check
    title = script_data.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        errors.append("Script plan must contain a non-empty 'title' string.")

    # Scenes list check
    scenes = script_data.get("scenes")
    if not isinstance(scenes, list):
        return False, ["Script plan does not contain a valid 'scenes' list."]

    if not scenes:
        return False, ["Script plan contains zero scenes."]

    # Scene count bounds
    if len(scenes) < MIN_SCENES:
        errors.append(
            f"Script plan must contain at least {MIN_SCENES} scenes (got {len(scenes)}). "
            "A short requires an initial curiosity hook and at least one comparison."
        )
    elif len(scenes) > MAX_SCENES:
        errors.append(
            f"Script plan contains {len(scenes)} scenes, exceeding maximum of {MAX_SCENES}."
        )

    # Scene 1 hook constraint
    first_scene = scenes[0]
    if isinstance(first_scene, dict) and first_scene.get("scene_type") != "fullscreen_text":
        errors.append(
            f"Scene 1 must be 'fullscreen_text' (hook), got {first_scene.get('scene_type')!r}."
        )

    # Comparison scene constraint
    has_comparison = any(
        isinstance(s, dict) and s.get("scene_type") == "comparison"
        for s in scenes
    )
    if not has_comparison:
        errors.append("Script plan must contain at least one 'comparison' scene.")

    # Per-scene validation
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            errors.append(f"Scene {index} is not an object / dict.")
            continue

        scene_type = scene.get("scene_type")
        if scene_type not in VALID_SCENE_TYPES:
            errors.append(
                f"Scene {index} has invalid scene_type: {scene_type!r}. "
                f"Allowed: {sorted(VALID_SCENE_TYPES)}"
            )

        # Spoken text constraint: 5–11 words per semantic beat
        spoken_text = scene.get("spoken_text", "")
        if not isinstance(spoken_text, str) or not spoken_text.strip():
            errors.append(f"Scene {index} has empty or non-string 'spoken_text'.")
        else:
            word_count = len(spoken_text.split())
            if word_count < MIN_WORDS_PER_BEAT:
                errors.append(
                    f"Scene {index} contains {word_count} spoken words ({spoken_text!r}). "
                    f"Minimum is {MIN_WORDS_PER_BEAT} words per beat."
                )
            elif word_count > MAX_WORDS_PER_BEAT:
                errors.append(
                    f"Scene {index} contains {word_count} spoken words ({spoken_text!r}). "
                    f"Maximum is {MAX_WORDS_PER_BEAT} words per beat."
                )

        # Scene-type specific checks & AST pre-flight validation
        if scene_type == "fullscreen_text":
            display_text = scene.get("display_text", "")
            if not isinstance(display_text, str) or not display_text.strip():
                errors.append(f"Scene {index} (fullscreen_text) requires non-empty 'display_text'.")

        elif scene_type in {"code_reveal", "code_transform"}:
            code = scene.get("code_snippet", "")
            if not isinstance(code, str) or not code.strip():
                errors.append(f"Scene {index} ({scene_type}) requires non-empty 'code_snippet'.")
            else:
                # Pre-flight AST syntax check
                valid, err = check_syntax(code)
                if not valid:
                    errors.append(
                        f"Scene {index} ({scene_type}) AST syntax check failed: {err}\nCode snippet:\n{code}"
                    )

        elif scene_type == "terminal":
            code = scene.get("code_snippet", "")
            if not isinstance(code, str) or not code.strip():
                errors.append(f"Scene {index} (terminal) requires non-empty 'code_snippet'.")
            else:
                valid, err = check_terminal_snippet(code)
                if not valid:
                    errors.append(f"Scene {index} (terminal) check failed: {err}")

        elif scene_type == "comparison":
            problem_code = scene.get("problem_code", "")
            solution_code = scene.get("solution_code", "")

            if not isinstance(problem_code, str) or not problem_code.strip():
                errors.append(f"Scene {index} (comparison) requires non-empty 'problem_code'.")
            else:
                valid, err = check_syntax(problem_code)
                if not valid:
                    errors.append(
                        f"Scene {index} (comparison) problem_code AST syntax check failed: {err}\nCode:\n{problem_code}"
                    )

            if not isinstance(solution_code, str) or not solution_code.strip():
                errors.append(f"Scene {index} (comparison) requires non-empty 'solution_code'.")
            else:
                valid, err = check_syntax(solution_code)
                if not valid:
                    errors.append(
                        f"Scene {index} (comparison) solution_code AST syntax check failed: {err}\nCode:\n{solution_code}"
                    )

        elif scene_type == "diagram":
            nodes = scene.get("nodes")
            if not isinstance(nodes, list) or not nodes:
                errors.append(f"Scene {index} (diagram) requires non-empty 'nodes' list.")
            elif len(nodes) > MAX_DIAGRAM_NODES:
                errors.append(
                    f"Scene {index} (diagram) has {len(nodes)} nodes. "
                    f"Maximum is {MAX_DIAGRAM_NODES}."
                )

    return (len(errors) == 0, errors)


def validate_or_raise(script_data: Any) -> None:
    """
    Validates script_data and raises ScriptValidationError if invalid.
    """
    is_valid, errors = validate_script_plan(script_data)
    if not is_valid:
        raise ScriptValidationError(errors)

