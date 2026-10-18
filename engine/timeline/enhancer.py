"""
engine/timeline/enhancer.py

Deterministic Semantic Visual Enhancer Pass (Phase 2).
Classifies timeline scenes into semantic categories:
  - 'anti_pattern': Pitfalls, bugs, slow/redundant code, bad habits ({ label: 'Anti-Pattern', type: 'warning', icon: '⚠️' }).
  - 'solution': Best practices, clean idiomatic fixes, optimized code ({ label: 'Best Practice', type: 'success', icon: '✨' }).
  - 'performance': Algorithmic speed, O(1)/O(n) complexity, memory, latency ({ label: 'Performance', type: 'accent', icon: '⚡' }).
  - 'insight': Architectural mental models, core principles, diagrams ({ label: 'Key Concept', type: 'info', icon: '💡' }).
  - 'comparison': Contrasting approaches, trade-offs, side-by-side analysis ({ label: 'Comparison', type: 'info', icon: '⚖️' }).

Guarantees:
  - Strictly additive: never mutates timestamps, word boundaries, or scene order.
  - Safe fallbacks: returns None or leaves scene untouched if no category matches.
  - Preserves existing custom badges if already defined.
"""

from typing import Any, Dict, List, Optional

SEMANTIC_BADGES: Dict[str, Dict[str, str]] = {
    "anti_pattern": {
        "category": "anti_pattern",
        "label": "Anti-Pattern",
        "type": "warning",
        "icon": "⚠️",
    },
    "solution": {
        "category": "solution",
        "label": "Best Practice",
        "type": "success",
        "icon": "✨",
    },
    "performance": {
        "category": "performance",
        "label": "Performance",
        "type": "accent",
        "icon": "⚡",
    },
    "insight": {
        "category": "insight",
        "label": "Key Concept",
        "type": "info",
        "icon": "💡",
    },
    "comparison": {
        "category": "comparison",
        "label": "Comparison",
        "type": "info",
        "icon": "⚖️",
    },
}

import re

# Categorized keyword sets for deterministic text matching
_NEGATIVE_IMPERATIVES_RE = re.compile(
    r"\b(stop|never|don'?t|avoid|wrong|fails?|breaks?|waste|wasteful|mistakes?|anti-?pattern|naive|broken|ugly|bug|pitfall)\b",
    re.IGNORECASE,
)

_ANTI_PATTERN_KEYWORDS = [
    "anti-pattern", "antipattern", "anti pattern", "bad approach", "slow approach",
    "wrong approach", "ugly", "bug", "gotcha", "mistake", "danger", "leaks", "leak",
    "redundant", "waste", "avoid", "worst", "inefficient", "fails", "broken",
    "don't do", "never do", "tedious", "pitfall", "duplicated", "bad =", "wasteful",
    "problem", "naive", "stop", "never", "breaks", "wrong", "don't",
]

_PERFORMANCE_KEYWORDS = [
    "performance", "faster", "fast", "speed", "o(1)", "o(n)", "o(log n)",
    "complexity", "overhead", "latency", "throughput", "bottleneck", "cache",
    "caching", "benchmark", "optimization", "cpu", "allocation", "memory usage",
    "scale", "efficient",
]

_SOLUTION_KEYWORDS = [
    "better way", "best practice", "solution", "optimized", "cleaner",
    "idiomatic", "pythonic", "the fix", "works", "modern", "recommended",
    "walrus", "one-liner", "neat", "clean", "eliminate", "solves", "good =",
    "proper", "correct",
]

_INSIGHT_KEYWORDS = [
    "insight", "pro tip", "key concept", "remember", "how it works",
    "under the hood", "secret", "rule", "takeaway", "deep dive",
    "explanation", "binds", "evaluates", "statement", "expression",
    "concept", "principle", "mental model", "foundation", "mechanism",
]

_COMPARISON_KEYWORDS = [
    "comparison", "versus", "vs", "compare", "tradeoff", "trade-off",
    "difference", "contrast",
]


def classify_scene(scene: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Deterministically inspects scene code, narration, visual_type, and focus_phrase
    to classify the scene into a semantic category.

    Returns:
        A badge dictionary { 'category', 'label', 'type', 'icon' }, or None.
    """
    if not isinstance(scene, dict):
        return None

    # Preserve explicit custom badges if already validly attached
    existing_badge = scene.get("badge")
    if isinstance(existing_badge, dict) and "label" in existing_badge and "type" in existing_badge:
        return dict(existing_badge)

    scene_type = str(scene.get("scene_type") or scene.get("visual_type") or "").strip().lower()
    spoken_text = str(scene.get("spoken_text", "")).lower()
    display_text = str(scene.get("display_text", "")).lower()
    code = str(scene.get("code_snippet", "")).lower()
    problem_label = str(scene.get("problem_label", "")).lower()
    problem_code = str(scene.get("problem_code", "")).lower()
    solution_label = str(scene.get("solution_label", "")).lower()
    solution_code = str(scene.get("solution_code", "")).lower()
    focus_phrase = str(scene.get("focus_phrase", "")).lower()

    text_corpus = (
        f"{spoken_text} {display_text} {focus_phrase} {problem_label} "
        f"{solution_label} {code} {problem_code} {solution_code}"
    )

    title_text = str(scene.get("title", "")).lower()
    negative_corpus = f"{spoken_text} {display_text} {title_text} {problem_label} {focus_phrase}"

    # 1. Phase 6: Prioritize negative / warning imperatives FIRST
    # (stop, never, don't, avoid, wrong, fails, breaks, waste, mistake)
    # If any appear in narration, title, or problem label, force badge to Anti-Pattern
    if _NEGATIVE_IMPERATIVES_RE.search(negative_corpus):
        return dict(SEMANTIC_BADGES["anti_pattern"])

    # 2. Comparison scene handling
    if scene_type == "comparison":
        # If the comparison specifically centers on speed/complexity, badge with performance
        if any(term in text_corpus for term in ["faster", "speed", "latency", "o(1)", "o(n)", "overhead", "benchmark"]):
            return dict(SEMANTIC_BADGES["performance"])
        return dict(SEMANTIC_BADGES["comparison"])

    # 3. Anti-pattern secondary check
    if any(term in text_corpus for term in _ANTI_PATTERN_KEYWORDS):
        return dict(SEMANTIC_BADGES["anti_pattern"])

    # 3. Performance priority check
    if any(term in text_corpus for term in _PERFORMANCE_KEYWORDS):
        return dict(SEMANTIC_BADGES["performance"])

    # 4. Solution / Best Practice check
    if any(term in text_corpus for term in _SOLUTION_KEYWORDS):
        return dict(SEMANTIC_BADGES["solution"])

    # 5. Diagram & Conceptual Insight check
    if scene_type == "diagram":
        return dict(SEMANTIC_BADGES["insight"])

    if any(term in text_corpus for term in _INSIGHT_KEYWORDS):
        return dict(SEMANTIC_BADGES["insight"])

    # 6. Comparison keyword check
    if any(term in text_corpus for term in _COMPARISON_KEYWORDS):
        return dict(SEMANTIC_BADGES["comparison"])

    # 7. Code transform fallback -> solution
    if scene_type == "code_transform":
        return dict(SEMANTIC_BADGES["solution"])

    return None


def enhance_scenes(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enriches a list of scenes with deterministic semantic badges.

    Strictly additive:
      - Does not alter scene count or ordering.
      - Keeps all start_time, emphasis_time, and word alignment untouched.
      - Returns new scene dicts without mutating caller arguments.
    """
    if not isinstance(scenes, list):
        return []

    enhanced: List[Dict[str, Any]] = []

    for scene in scenes:
        if not isinstance(scene, dict):
            enhanced.append(scene)
            continue

        scene_copy = dict(scene)
        badge = classify_scene(scene_copy)
        if badge is not None:
            scene_copy["badge"] = badge

        enhanced.append(scene_copy)

    return enhanced
