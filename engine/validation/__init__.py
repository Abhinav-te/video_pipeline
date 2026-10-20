"""
Validation Gate package: AST syntax checks, schema contracts, beat validation, and post-render video output validation.
"""

from .schema import (
    validate_script_plan,
    validate_or_raise,
    check_narrative_consistency,
    BANNED_PLACEHOLDER_TOKENS,
    ML_PLACEHOLDER_TOKENS,
    resolve_script_subject,
    validate_formula_string,
    ScriptValidationError,
    VALID_SCENE_TYPES,
    ALL_SUBJECTS,
    STEM_SUBJECTS,
    MIN_WORDS_PER_BEAT,
    MAX_WORDS_PER_BEAT,
    MAX_DIAGRAM_NODES,
    MIN_SCENES,
    MAX_SCENES,
)
from .code import (
    check_syntax,
    check_terminal_snippet,
    run_in_sandbox,
)
from .output import (
    validate_video_output,
    validate_video_or_raise,
    OutputValidationError,
    get_media_duration,
    inspect_video_file,
    REQUIRED_WIDTH,
    REQUIRED_HEIGHT,
    TARGET_FPS,
)
from .reflection import (
    write_reflection_error,
    read_reflection_error,
    clear_reflection_error,
    auto_heal_timeline_payload,
)

__all__ = [
    "validate_script_plan",
    "validate_or_raise",
    "check_narrative_consistency",
    "BANNED_PLACEHOLDER_TOKENS",
    "resolve_script_subject",
    "validate_formula_string",
    "ScriptValidationError",
    "VALID_SCENE_TYPES",
    "ALL_SUBJECTS",
    "STEM_SUBJECTS",
    "MIN_WORDS_PER_BEAT",
    "MAX_WORDS_PER_BEAT",
    "MAX_DIAGRAM_NODES",
    "MIN_SCENES",
    "MAX_SCENES",
    "check_syntax",
    "check_terminal_snippet",
    "run_in_sandbox",
    "validate_video_output",
    "validate_video_or_raise",
    "OutputValidationError",
    "get_media_duration",
    "inspect_video_file",
    "REQUIRED_WIDTH",
    "REQUIRED_HEIGHT",
    "TARGET_FPS",
    "write_reflection_error",
    "read_reflection_error",
    "clear_reflection_error",
    "auto_heal_timeline_payload",
]
