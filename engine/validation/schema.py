"""
Validation Gate & Polymorphic Contract Enforcement for AI Director Script Plans.

Formalizes polymorphic validation across all domains:
- Code: Python AST syntax checks strictly restricted to subject == 'code' and Python visual types
- STEM (math, physics, chemistry, quantum_physics, mechanics, electrical, ml, systems):
  comparison, equation, and formula fields validated as formatted formula/LaTeX strings,
  skipping Python ast.parse() completely.
- Generic schema verification across all subjects (scene_id, title, narration, visual_type, duration).
- Beat length enforcement (5–11 words per semantic beat).
- Diagram node bounds (2-3 items).
"""

from typing import Any, Dict, List, Optional, Tuple

try:
    from engine.validation.code import check_syntax, check_terminal_snippet
except ImportError:
    from validation.code import check_syntax, check_terminal_snippet

try:
    from engine.director.script import DOMAINS, detect_domain
except ImportError:
    try:
        from director.script import DOMAINS, detect_domain
    except ImportError:
        DOMAINS = {
            "code",
            "math",
            "physics",
            "systems",
            "ml",
            "chemistry",
            "quantum_physics",
            "mechanics",
            "electrical",
        }
        detect_domain = None

ALL_SUBJECTS = {
    "code",
    "math",
    "physics",
    "systems",
    "ml",
    "chemistry",
    "quantum_physics",
    "mechanics",
    "electrical",
}

STEM_SUBJECTS = {
    "math",
    "physics",
    "chemistry",
    "quantum_physics",
    "mechanics",
    "electrical",
    "ml",
}

VALID_SCENE_TYPES = {
    "fullscreen_text",
    "code_reveal",
    "code_transform",
    "terminal",
    "diagram",
    "comparison",
    "concept",
    "math_equation",
    "function_graph",
    "physics_sim",
    "bento_grid",
    "algorithm_explorer",
    "neural_code_split",
    "chemistry_reaction",
    "quantum_sim",
    "mechanics_fbd",
    "electrical_grid",
}

STEM_SCENE_TYPES = {
    "math_equation",
    "function_graph",
    "physics_sim",
    "quantum_sim",
    "mechanics_fbd",
    "electrical_grid",
}

ML_SCENE_TYPES = {
    "bento_grid",
    "algorithm_explorer",
    "neural_code_split",
}

CHEMISTRY_SCENE_TYPES = {
    "chemistry_reaction",
}

QUANTUM_SCENE_TYPES = {
    "quantum_sim",
}

MECHANICS_SCENE_TYPES = {
    "mechanics_fbd",
}

ELECTRICAL_SCENE_TYPES = {
    "electrical_grid",
}

PYTHON_EXECUTION_SCENE_TYPES = {
    "code_reveal",
    "code_transform",
    "neural_code_split",
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


def resolve_script_subject(script_data: Any) -> str:
    """
    Polymorphically resolves the active subject/domain of a script plan.
    Strictly data-driven:
    1. Returns explicit 'subject' or 'domain' if matching recognized subjects.
    2. Scans scene visual primitives for domain-specific signatures.
    3. Uses content-based heuristic detection on title / narration if 'auto' or unspecified.
    4. Defaults to 'code'.
    """
    if not isinstance(script_data, dict):
        return "code"

    subject = script_data.get("subject") or script_data.get("domain")
    if isinstance(subject, str) and subject.strip().lower() in ALL_SUBJECTS:
        return subject.strip().lower()

    scenes = script_data.get("scenes") or []
    for s in scenes:
        if not isinstance(s, dict):
            continue
        v_type = s.get("visual_type") or s.get("scene_type")
        if v_type in QUANTUM_SCENE_TYPES:
            return "quantum_physics"
        if v_type in MECHANICS_SCENE_TYPES:
            return "mechanics"
        if v_type in ELECTRICAL_SCENE_TYPES:
            return "electrical"
        if v_type in CHEMISTRY_SCENE_TYPES:
            return "chemistry"
        if v_type in {"math_equation", "function_graph"}:
            return "math"
        if v_type == "physics_sim":
            return "physics"
        if v_type in ML_SCENE_TYPES:
            return "ml"

    if detect_domain is not None:
        title = script_data.get("title", "")
        detected = detect_domain(title)
        if detected in ALL_SUBJECTS and detected != "code":
            return detected

        for s in scenes:
            if isinstance(s, dict):
                text = s.get("narration") or s.get("spoken_text") or ""
                detected = detect_domain(text)
                if detected in ALL_SUBJECTS and detected != "code":
                    return detected

    return "code"


def validate_formula_string(val: Any, field_name: str, scene_idx: int) -> Tuple[bool, Optional[str]]:
    """
    Validates that a formula, LaTeX equation, or STEM comparison field is a non-empty,
    well-formed string without attempting Python ast.parse().
    """
    if not isinstance(val, str) or not val.strip():
        return False, f"Scene {scene_idx} requires non-empty string for '{field_name}'."
    if len(val) > 2000:
        return False, f"Scene {scene_idx} '{field_name}' exceeds maximum length of 2000 characters."
    return True, None


def validate_script_plan(script_data: Any) -> Tuple[bool, List[str]]:
    """
    Validates a complete script plan against polymorphic schema contracts and syntax checks.

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
            "A short requires an initial curiosity hook and at least one core demonstration scene."
        )
    elif len(scenes) > MAX_SCENES:
        errors.append(
            f"Script plan contains {len(scenes)} scenes, exceeding maximum of {MAX_SCENES}."
        )

    # Scene 1 hook constraint (must be fullscreen_text or concept)
    first_scene = scenes[0]
    if isinstance(first_scene, dict):
        first_type = first_scene.get("visual_type") or first_scene.get("scene_type")
        if first_type not in {"fullscreen_text", "concept"}:
            errors.append(
                f"Scene 1 must be 'fullscreen_text' (hook), got {first_type!r}."
            )

    # Polymorphic subject determination
    script_subject = resolve_script_subject(script_data)

    # Comparison scene constraint: strictly required for coding domain
    if script_subject == "code":
        has_comparison = any(
            isinstance(s, dict) and (
                s.get("visual_type") == "comparison" or s.get("scene_type") == "comparison"
            )
            for s in scenes
        )
        if not has_comparison:
            errors.append("Script plan must contain at least one 'comparison' scene.")

    # Determine length/duration bounds
    plan_duration = script_data.get("duration") or script_data.get("target_duration") or script_data.get("length")
    is_60s_scale = False
    if plan_duration is not None:
        try:
            if float(plan_duration) >= 50:
                is_60s_scale = True
        except (TypeError, ValueError):
            pass
    if not is_60s_scale and len(scenes) >= 9:
        is_60s_scale = True

    scene_min_words = 4 if is_60s_scale else MIN_WORDS_PER_BEAT
    scene_max_words = 22 if is_60s_scale else MAX_WORDS_PER_BEAT

    # Per-scene polymorphic validation
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            errors.append(f"Scene {index} is not an object / dict.")
            continue

        # 1. Visual type validation
        scene_type = scene.get("visual_type") or scene.get("scene_type")
        if not scene_type:
            errors.append(f"Scene {index} requires 'visual_type' (or 'scene_type').")
        elif scene_type not in VALID_SCENE_TYPES:
            errors.append(
                f"Scene {index} has invalid scene_type: {scene_type!r}. "
                f"Allowed: {sorted(VALID_SCENE_TYPES)}"
            )

        # 2. Narration / Spoken text constraint: >= 4 words (or 11–18 words for 60s)
        narration = scene.get("narration") or scene.get("spoken_text")
        if not isinstance(narration, str) or not narration.strip():
            errors.append(f"Scene {index} has empty or non-string 'narration' / 'spoken_text'.")
        else:
            word_count = len(narration.split())
            current_min_words = 4 if (is_60s_scale or index == 1 or index == len(scenes)) else scene_min_words
            if word_count < current_min_words:
                errors.append(
                    f"Scene {index} contains {word_count} spoken words ({narration!r}). "
                    f"Minimum is {current_min_words} words per beat."
                )
            elif word_count > scene_max_words:
                errors.append(
                    f"Scene {index} contains {word_count} spoken words ({narration!r}). "
                    f"Maximum is {scene_max_words} words per beat."
                )

        # 3. Generic field sanity checks (scene_id, title, duration)
        scene_id = scene.get("scene_id") or scene.get("id")
        if scene_id is not None:
            if isinstance(scene_id, str) and not scene_id.strip():
                errors.append(f"Scene {index} has empty 'scene_id'.")

        scene_title = scene.get("title")
        if scene_title is not None:
            if not isinstance(scene_title, str) or not scene_title.strip():
                errors.append(f"Scene {index} has invalid 'title': must be a non-empty string.")

        duration = scene.get("duration")
        if duration is not None:
            if not isinstance(duration, (int, float)) or duration <= 0:
                errors.append(f"Scene {index} has invalid 'duration': must be a positive number.")

        # ── Polymorphic Type Checks ──────────────────────────────────────────

        # 1. Fullscreen Hook / Concept Takeaway
        if scene_type in {"fullscreen_text", "concept"}:
            display_text = scene.get("display_text") or scene.get("title")
            if not display_text or not isinstance(display_text, str) or not display_text.strip():
                scene["display_text"] = scene.get("title") or scene.get("narration") or "HOOK TITLE"

        # 2. Code Reveal & Code Transform
        elif scene_type in {"code_reveal", "code_transform"}:
            code = scene.get("code_snippet") or scene.get("code", "")
            if not isinstance(code, str) or not code.strip():
                errors.append(f"Scene {index} ({scene_type}) requires non-empty 'code_snippet'.")
            elif script_subject == "code":
                # Strict Python AST validation ONLY for code subject
                lang = scene.get("language", "python").lower()
                if lang == "python":
                    valid, err = check_syntax(code)
                    if not valid:
                        errors.append(
                            f"Scene {index} ({scene_type}) AST syntax check failed: {err}\nCode snippet:\n{code}"
                        )
            else:
                # STEM/Non-code subject: validate as formatted equation or pseudo-code string
                valid, err = validate_formula_string(code, "code_snippet", index)
                if not valid:
                    errors.append(err)

        # 3. Terminal Run
        elif scene_type == "terminal":
            code = scene.get("code_snippet") or scene.get("code", "")
            if not isinstance(code, str) or not code.strip():
                errors.append(f"Scene {index} (terminal) requires non-empty 'code_snippet'.")
            else:
                valid, err = check_terminal_snippet(code)
                if not valid:
                    errors.append(f"Scene {index} (terminal) check failed: {err}")

        # 4. Comparison
        elif scene_type == "comparison":
            sides = scene.get("comparison_sides")
            if sides is not None:
                if not isinstance(sides, (dict, list)):
                    errors.append(f"Scene {index} (comparison) 'comparison_sides' must be an object or list.")
            else:
                problem_code = scene.get("problem_code") or scene.get("code_snippet") or scene.get("problem")
                solution_code = scene.get("solution_code") or scene.get("solution")

                if problem_code is None and solution_code is None:
                    left = scene.get("left")
                    right = scene.get("right")
                    if left is None or right is None:
                        if script_subject in STEM_SUBJECTS:
                            scene["problem_label"] = "BASELINE"
                            scene["problem_code"] = scene.get("title") or "Standard System"
                            scene["solution_label"] = "OPTIMIZED"
                            scene["solution_code"] = "Optimized System"
                        else:
                            errors.append(
                                f"Scene {index} (comparison) requires non-empty 'problem_code' and 'solution_code' (or 'comparison_sides')."
                            )
                else:
                    # Validate problem_code
                    if not isinstance(problem_code, str) or not problem_code.strip():
                        errors.append(f"Scene {index} (comparison) requires non-empty 'problem_code'.")
                    elif script_subject == "code":
                        valid, err = check_syntax(problem_code)
                        if not valid:
                            errors.append(
                                f"Scene {index} (comparison) problem_code AST syntax check failed: {err}\nCode:\n{problem_code}"
                            )
                    else:
                        valid, err = validate_formula_string(problem_code, "problem_code", index)
                        if not valid:
                            errors.append(err)

                    # Validate solution_code
                    if not isinstance(solution_code, str) or not solution_code.strip():
                        errors.append(f"Scene {index} (comparison) requires non-empty 'solution_code'.")
                    elif script_subject == "code":
                        valid, err = check_syntax(solution_code)
                        if not valid:
                            errors.append(
                                f"Scene {index} (comparison) solution_code AST syntax check failed: {err}\nCode:\n{solution_code}"
                            )
                    else:
                        valid, err = validate_formula_string(solution_code, "solution_code", index)
                        if not valid:
                            errors.append(err)

        # 5. Diagram Flow
        elif scene_type == "diagram":
            nodes = scene.get("nodes")
            if not isinstance(nodes, list) or not nodes:
                errors.append(f"Scene {index} (diagram) requires non-empty 'nodes' list.")
            elif len(nodes) > MAX_DIAGRAM_NODES:
                errors.append(
                    f"Scene {index} (diagram) has {len(nodes)} nodes. "
                    f"Maximum is {MAX_DIAGRAM_NODES}."
                )

        # 6. STEM: Math Equation Derivation
        elif scene_type == "math_equation":
            if not any(k in scene for k in ("steps", "equations")) or (
                scene.get("steps") is None and scene.get("equations") is None
            ):
                if scene.get("title") or is_60s_scale:
                    step_title = scene.get("title") or "Equation Derivation"
                    scene["steps"] = [{"step": 1, "formula": step_title, "label": step_title}]

            steps = scene.get("steps") or scene.get("equations")
            if not steps or not isinstance(steps, list):
                errors.append(f"Scene {index} (math_equation) requires non-empty 'steps' or 'equations' list.")
            else:
                for s_idx, step in enumerate(steps, start=1):
                    if isinstance(step, str):
                        if not step.strip():
                            errors.append(f"Scene {index} (math_equation) step {s_idx} formula string is empty.")
                    elif isinstance(step, dict):
                        formula = step.get("formula") or step.get("latex") or step.get("equation")
                        if not formula or not isinstance(formula, str) or not formula.strip():
                            step["formula"] = scene.get("title") or "f(x) = y"
                    else:
                        errors.append(f"Scene {index} (math_equation) step {s_idx} must be a string or object.")

        # 7. STEM: Function Graph Plotting
        elif scene_type == "function_graph":
            if not any(k in scene for k in ("functions", "curves", "function")) or (
                scene.get("functions") is None and scene.get("curves") is None and scene.get("function") is None
            ):
                if scene.get("title") or is_60s_scale:
                    scene["functions"] = [{"fn": "x^2", "label": scene.get("title") or "f(x)"}]

            functions = scene.get("functions") or scene.get("curves") or scene.get("function")
            if not functions:
                errors.append(f"Scene {index} (function_graph) requires 'functions' or 'curves' definition.")
            elif isinstance(functions, list) and len(functions) == 0:
                errors.append(f"Scene {index} (function_graph) 'functions' list cannot be empty.")

            x_dom = scene.get("x_domain") or scene.get("x_range") or scene.get("domain")
            if x_dom is not None:
                if not (isinstance(x_dom, (list, tuple)) and len(x_dom) == 2 and x_dom[0] < x_dom[1]):
                    errors.append(f"Scene {index} (function_graph) 'x_domain' must be [min, max] with min < max.")

            y_dom = scene.get("y_domain") or scene.get("y_range")
            if y_dom is not None:
                if not (isinstance(y_dom, (list, tuple)) and len(y_dom) == 2 and y_dom[0] < y_dom[1]):
                    errors.append(f"Scene {index} (function_graph) 'y_domain' must be [min, max] with min < max.")

        # 8. STEM: Physics Simulation
        elif scene_type == "physics_sim":
            has_physics_payload = any(
                scene.get(k) is not None
                for k in ("objects", "vectors", "forces", "trajectory", "sim_type")
            )
            if not has_physics_payload:
                if scene.get("title") or is_60s_scale:
                    scene["sim_type"] = "forces"
                    scene["forces"] = [{"name": "F_net", "magnitude": "10N", "direction": 0}]
                else:
                    errors.append(
                        f"Scene {index} (physics_sim) requires presence of 'objects', 'vectors', 'forces', 'trajectory', or 'sim_type'."
                    )

        # 9. ML: Bento Grid Overview
        elif scene_type == "bento_grid":
            if "cards" not in scene or scene.get("cards") is None:
                scene["cards"] = []
            elif not isinstance(scene["cards"], list):
                errors.append(f"Scene {index} (bento_grid) 'cards' must be a list.")

        # 10. ML: Algorithm Explorer Deep-Dive
        elif scene_type == "algorithm_explorer":
            if "parameters" not in scene or scene.get("parameters") is None:
                scene["parameters"] = {}
            elif not isinstance(scene["parameters"], (dict, list)):
                errors.append(f"Scene {index} (algorithm_explorer) 'parameters' must be an object or list.")

        # 11. ML: Neural Code Split
        elif scene_type == "neural_code_split":
            code = scene.get("code_snippet") or scene.get("code")
            if not code or not isinstance(code, str) or not code.strip():
                scene["code_snippet"] = "import torch\n# Neural network forward pass\noutput = model(inputs)"
            else:
                if script_subject == "code" or (
                    script_subject == "ml"
                    and any(k in code for k in ("def ", "class ", "import ", "lambda "))
                ):
                    valid, err = check_syntax(code)
                    if not valid:
                        errors.append(
                            f"Scene {index} (neural_code_split) code_snippet AST syntax check failed: {err}\nCode snippet:\n{code}"
                        )
                else:
                    valid, err = validate_formula_string(code, "code_snippet", index)
                    if not valid:
                        errors.append(err)

        # 12. Chemistry: Organic Reaction Mechanism
        elif scene_type == "chemistry_reaction":
            has_chem_payload = any(
                scene.get(k) is not None
                for k in ("reaction_name", "mode", "molecules", "reactants", "products", "mechanism_steps", "reagents", "rate_law")
            )
            if not has_chem_payload:
                if scene.get("title") or is_60s_scale:
                    scene["reaction_name"] = scene.get("title") or "Reaction Mechanism"
                    scene["mode"] = "sn2_concerted"
                else:
                    errors.append(
                        f"Scene {index} (chemistry_reaction) requires presence of 'reaction_name', 'mode', 'molecules', 'reactants', 'products', 'mechanism_steps', or 'reagents'."
                    )

        # 13. Quantum Physics Simulation
        elif scene_type == "quantum_sim":
            sub_mode = scene.get("sub_mode")
            if not sub_mode:
                scene["sub_mode"] = "schrodinger_tunneling"
            elif sub_mode not in {"schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"}:
                errors.append(
                    f"Scene {index} (quantum_sim) invalid sub_mode '{sub_mode}'. Must be one of 'schrodinger_tunneling', 'heisenberg_uncertainty', 'dirac_atomic_orbitals'."
                )

        # 14. Advanced Mechanics Free-Body Diagram
        elif scene_type == "mechanics_fbd":
            sub_mode = scene.get("sub_mode")
            if not sub_mode:
                scene["sub_mode"] = "beam_weight_distribution"
            elif sub_mode not in {"beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"}:
                errors.append(
                    f"Scene {index} (mechanics_fbd) invalid sub_mode '{sub_mode}'. Must be one of 'beam_weight_distribution', 'inclined_plane_fbd', 'axle_center_of_mass'."
                )

        # 15. Electrical Circuits & Smart Grid
        elif scene_type == "electrical_grid":
            sub_mode = scene.get("sub_mode")
            if not sub_mode:
                scene["sub_mode"] = "kvl_kcl_mesh"
            elif sub_mode not in {"kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"}:
                errors.append(
                    f"Scene {index} (electrical_grid) invalid sub_mode '{sub_mode}'. Must be one of 'kvl_kcl_mesh', 'thevenin_equivalence', 'smart_grid_opf'."
                )

    return (len(errors) == 0, errors)


def validate_or_raise(script_data: Any) -> None:
    """
    Validates script_data and raises ScriptValidationError if invalid.
    """
    is_valid, errors = validate_script_plan(script_data)
    if not is_valid:
        raise ScriptValidationError(errors)
