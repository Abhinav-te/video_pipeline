try:
    from .script import (
        generate_script,
        detect_domain,
        get_system_prompt,
        DOMAINS,
        DEFAULT_MODEL_CHAIN,
        calculate_target_scenes,
        merge_excess_scenes,
    )
except ImportError:
    from director.script import (
        generate_script,
        detect_domain,
        get_system_prompt,
        DOMAINS,
        DEFAULT_MODEL_CHAIN,
        calculate_target_scenes,
        merge_excess_scenes,
    )

__all__ = [
    "generate_script",
    "detect_domain",
    "get_system_prompt",
    "DOMAINS",
    "DEFAULT_MODEL_CHAIN",
    "calculate_target_scenes",
    "merge_excess_scenes",
]

