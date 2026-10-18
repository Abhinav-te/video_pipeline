"""
Stage 4.5 Manim Community Sub-Renderer Integration.
Provides parameterized 3Blue1Brown-style mathematical templates and Remotion bridge.
"""
from engine.renderer.manim_templates import (
    ManimEquationMorphScene,
    ManimCalculusGraphScene,
    ManimLinearVectorScene,
    ManimQuantumWaveScene,
    safe_math_tex,
)
from engine.renderer.manim_bridge import (
    render_manim_clips_for_timeline,
    is_manim_available,
)

__all__ = [
    "ManimEquationMorphScene",
    "ManimCalculusGraphScene",
    "ManimLinearVectorScene",
    "ManimQuantumWaveScene",
    "safe_math_tex",
    "render_manim_clips_for_timeline",
    "is_manim_available",
]

