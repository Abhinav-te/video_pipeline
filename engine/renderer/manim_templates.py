"""
engine/renderer/manim_templates.py

Parameterized Manim Community (v0.18+) Scene templates configured strictly for Remotion:
- Resolution: 920x920
- Frame Rate: 30 fps
- Background: #0b0f19 (matches Remotion simulation card interior)

Templates:
1. ManimEquationMorphScene (sub_mode: "equation_morph")
2. ManimCalculusGraphScene (sub_mode: "calculus_graph")
3. ManimLinearVectorScene (sub_mode: "vector_field")
4. ManimQuantumWaveScene (sub_mode: "quantum_wave")
"""

import sys
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from manim import (
        Scene,
        MathTex,
        Text,
        Axes,
        NumberPlane,
        ArrowVectorField,
        Arrow,
        Dot,
        Rectangle,
        SurroundingRectangle,
        ValueTracker,
        always_redraw,
        Create,
        Write,
        FadeIn,
        FadeOut,
        ReplacementTransform,
        config,
        UP,
        DOWN,
        LEFT,
        RIGHT,
        ORIGIN,
        linear,
    )
    MANIM_AVAILABLE = True
except ImportError:
    Scene = object  # type: ignore
    MANIM_AVAILABLE = False


def configure_manim_environment(media_dir: Optional[str] = None, output_file: Optional[str] = None):
    """Applies standardized 920x920 30fps Remotion container settings."""
    if not MANIM_AVAILABLE:
        return
    config.pixel_width = 920
    config.pixel_height = 920
    config.frame_rate = 30
    config.background_color = "#0b0f19"
    if media_dir:
        config.media_dir = str(media_dir)
    if output_file:
        config.output_file = str(output_file)


def safe_math_tex(expr: str, **kwargs):
    """
    Renders MathTex with an automatic fallback to clean Text if LaTeX compilation fails.
    Guarantees no pipeline halts on uncommon LaTeX macros or uninstalled packages.
    """
    if not MANIM_AVAILABLE:
        raise RuntimeError("Manim is not available in the current environment.")

    clean_expr = str(expr or "").strip()
    if not clean_expr:
        clean_expr = "f(x) = y"

    try:
        return MathTex(clean_expr, **kwargs)
    except Exception:
        # Sanitize common math symbols to text representation
        clean_txt = (
            clean_expr.replace("\\\\", "\n")
            .replace("\\sum", "Σ")
            .replace("\\int", "∫")
            .replace("\\partial", "∂")
            .replace("\\lambda", "λ")
            .replace("\\Psi", "Ψ")
            .replace("\\psi", "ψ")
            .replace("\\hbar", "ℏ")
            .replace("\\approx", "≈")
            .replace("\\le", "≤")
            .replace("\\ge", "≥")
            .replace("\\text", "")
            .replace("\\", "")
            .replace("{", "")
            .replace("}", "")
            .replace("^", "")
            .replace("_", "")
            .strip()
        )
        return Text(clean_txt or "f(x) = y", **kwargs)


class ManimEquationMorphScene(Scene):
    """
    Step-by-step formula morphing with smooth variable highlighting and glowing bounding box.
    """

    def __init__(
        self,
        steps: Optional[List[Dict[str, Any]]] = None,
        duration: float = 4.0,
        title: Optional[str] = None,
        **kwargs,
    ):
        self.steps = steps or [
            {"latex": r"\sum_{i} P_{Gi} = P_{\text{load}} + P_{\text{loss}}", "label": "Active Power Balance"},
            {"latex": r"\frac{\partial C_i}{\partial P_{Gi}} = \lambda", "label": "Optimal Economic Dispatch"},
        ]
        self.duration = float(duration)
        self.title_text = title or "MATHEMATICAL FORMULATION"
        if MANIM_AVAILABLE:
            super().__init__()

    def construct(self):
        curr_mob = None
        curr_label = None
        n = len(self.steps)
        time_per_step = max(0.8, (self.duration - 0.6) / max(n, 1))

        for idx, step in enumerate(self.steps):
            raw_latex = step.get("latex") or step.get("formula") or ""
            label_text = step.get("label") or step.get("explanation") or f"Step {idx + 1}"

            new_mob = safe_math_tex(raw_latex, font_size=46)
            new_mob.set_color_by_gradient("#00f2fe", "#ffffff", "#10b981")
            new_label = Text(label_text, font_size=24, color="#94a3b8").next_to(new_mob, UP, buff=0.55)

            if curr_mob is None:
                self.play(Write(new_mob), FadeIn(new_label), run_time=0.8)
                curr_mob = new_mob
                curr_label = new_label
            else:
                self.play(
                    ReplacementTransform(curr_mob, new_mob),
                    ReplacementTransform(curr_label, new_label),
                    run_time=0.8,
                )
                curr_mob = new_mob
                curr_label = new_label

            hold = max(0.1, time_per_step - 0.8)
            self.wait(hold)

        # Final glowing bounding box
        if curr_mob is not None:
            box = SurroundingRectangle(curr_mob, color="#00f2fe", buff=0.25, corner_radius=0.15)
            self.play(Create(box), run_time=0.5)
            self.wait(0.5)


class ManimCalculusGraphScene(Scene):
    """
    Continuous curve with secant-to-tangent slope group and glowing Riemann sum integral convergence.
    """

    def __init__(
        self,
        fn_str: Optional[str] = None,
        duration: float = 4.0,
        title: str = "CALCULUS • DERIVATIVE & INTEGRAL",
        **kwargs,
    ):
        self.fn_str = fn_str
        self.duration = float(duration)
        self.title_text = title
        if MANIM_AVAILABLE:
            super().__init__()

    def construct(self):
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-0.5, 4.5, 1],
            x_length=7.0,
            y_length=5.8,
            axis_config={"color": "#475569"},
        ).to_edge(DOWN, buff=0.7)

        f = lambda x: 0.4 * x**2 + 0.2
        curve = axes.plot(f, color="#00f2fe", stroke_width=4)

        title_mob = Text(self.title_text, font_size=24, color="#94a3b8").to_edge(UP, buff=0.35)
        curve_label = safe_math_tex(r"f(x) = 0.4x^2 + 0.2", color="#00f2fe", font_size=30).next_to(
            title_mob, DOWN, buff=0.2
        )

        self.play(Create(axes), Write(title_mob), Write(curve_label), run_time=0.8)
        self.play(Create(curve), run_time=0.8)

        # Riemann sum rectangles converging to exact integral area
        rects = axes.get_riemann_rectangles(
            curve,
            x_range=[0, 2.5],
            dx=0.5,
            color="#10b981",
            fill_opacity=0.45,
            stroke_color="#00f2fe",
            stroke_width=1.5,
        )
        self.play(Create(rects), run_time=0.6)

        area = axes.get_area(curve, x_range=[0, 2.5], color=["#10b981", "#00f2fe"], opacity=0.55)
        self.play(ReplacementTransform(rects, area), run_time=0.6)

        # Tangent slope point
        t_dot = Dot(axes.c2p(1.5, f(1.5)), color="#f59e0b", radius=0.1)
        slope_line = axes.get_secant_slope_group(
            1.5, curve, dx=0.01, secant_line_length=3.0, secant_line_color="#f59e0b"
        )
        self.play(FadeIn(t_dot), Create(slope_line), run_time=0.6)

        remaining_time = max(0.4, self.duration - 3.4)
        self.wait(remaining_time)


class ManimLinearVectorScene(Scene):
    """
    2D linear matrix transformations, basis vectors (i_hat, j_hat), and vector phase space.
    """

    def __init__(
        self,
        matrix: Optional[List[List[float]]] = None,
        duration: float = 4.0,
        title: str = "LINEAR TRANSFORMATION & VECTOR FLOW",
        **kwargs,
    ):
        self.matrix = matrix or [[1.5, 0.5], [0.5, 1.2]]
        self.duration = float(duration)
        self.title_text = title
        if MANIM_AVAILABLE:
            super().__init__()

    def construct(self):
        plane = NumberPlane(
            x_range=[-4, 4, 1],
            y_range=[-4, 4, 1],
            x_length=6.6,
            y_length=6.6,
            background_line_style={"stroke_color": "#334155", "stroke_opacity": 0.6},
        )

        vf = ArrowVectorField(
            lambda p: np.array([-p[1], p[0], 0]) * 0.25,
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            colors=["#00f2fe", "#10b981", "#f59e0b"],
            length_func=lambda norm: 0.45 * np.tanh(norm),
        )

        title = Text(self.title_text, font_size=24, color="#94a3b8").to_edge(UP, buff=0.35)

        v_i = Arrow(plane.c2p(0, 0), plane.c2p(1, 0), buff=0, color="#10b981", stroke_width=4)
        v_j = Arrow(plane.c2p(0, 0), plane.c2p(0, 1), buff=0, color="#00f2fe", stroke_width=4)

        lbl_i = Text("î", font_size=20, color="#10b981").next_to(v_i, DOWN, buff=0.1)
        lbl_j = Text("ĵ", font_size=20, color="#00f2fe").next_to(v_j, LEFT, buff=0.1)

        self.play(Create(plane), Write(title), run_time=0.8)
        self.play(Create(v_i), Create(v_j), FadeIn(lbl_i), FadeIn(lbl_j), run_time=0.6)
        self.play(Create(vf), run_time=0.8)

        # Apply 2D linear transformation to plane and basis vectors
        m = self.matrix
        new_i = np.array([m[0][0], m[1][0], 0])
        new_j = np.array([m[0][1], m[1][1], 0])

        self.play(
            plane.animate.apply_matrix(m),
            v_i.animate.put_start_and_end_on(plane.c2p(0, 0), plane.c2p(new_i[0], new_i[1])),
            v_j.animate.put_start_and_end_on(plane.c2p(0, 0), plane.c2p(new_j[0], new_j[1])),
            lbl_i.animate.move_to(plane.c2p(new_i[0] + 0.3, new_i[1] - 0.2)),
            lbl_j.animate.move_to(plane.c2p(new_j[0] - 0.2, new_j[1] + 0.3)),
            run_time=1.0,
        )

        remaining_time = max(0.4, self.duration - 3.2)
        self.wait(remaining_time)


class ManimQuantumWaveScene(Scene):
    """
    Oscillating complex Gaussian wavepacket (Re[Psi], Im[Psi], |Psi|^2) tunneling through a potential barrier.
    """

    def __init__(
        self,
        barrier_x: float = 0.0,
        duration: float = 4.0,
        title: str = "QUANTUM TUNNELING: Ψ(x,t)",
        **kwargs,
    ):
        self.barrier_x = barrier_x
        self.duration = float(duration)
        self.title_text = title
        if MANIM_AVAILABLE:
            super().__init__()

    def construct(self):
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-1.5, 2.5, 1],
            x_length=7.4,
            y_length=5.8,
            axis_config={"color": "#475569"},
        ).to_edge(DOWN, buff=0.7)

        # Potential Barrier V_0
        b_x1, b_x2 = self.barrier_x - 0.35, self.barrier_x + 0.45
        b_p1 = axes.c2p(b_x1, 0)
        b_p2 = axes.c2p(b_x2, 2.0)
        barrier = Rectangle(
            width=abs(b_p2[0] - b_p1[0]),
            height=abs(b_p2[1] - b_p1[1]),
            stroke_color="#f59e0b",
            stroke_width=2.5,
            fill_color="#f59e0b",
            fill_opacity=0.25,
        ).move_to(axes.c2p((b_x1 + b_x2) / 2, 1.0))

        v_label = Text("V(x) = V₀", font_size=20, color="#f59e0b").next_to(barrier, UP, buff=0.15)
        title = Text(self.title_text, font_size=24, color="#c084fc").to_edge(UP, buff=0.35)

        self.play(Create(axes), FadeIn(barrier), Write(v_label), Write(title), run_time=0.8)

        t_track = ValueTracker(0.0)

        def get_psi(x, t):
            x0 = -2.6 + 1.6 * t
            sigma = 0.65
            k = 3.5
            amp = 1.0 if x < b_x1 else (np.exp(-2.5 * (x - b_x1)) if x <= b_x2 else 0.35)
            env = amp * np.exp(-((x - x0) ** 2) / (2 * (sigma**2)))
            phase = k * x - 2.5 * t
            re_val = env * np.cos(phase)
            prob = env**2
            return re_val, prob

        curve_re = always_redraw(
            lambda: axes.plot(
                lambda x: get_psi(x, t_track.get_value())[0],
                color="#00f2fe",
                stroke_width=3.5,
            )
        )

        curve_prob = always_redraw(
            lambda: axes.plot(
                lambda x: get_psi(x, t_track.get_value())[1],
                color="#c084fc",
                stroke_width=2.5,
            )
        )

        self.add(curve_re, curve_prob)
        sim_time = max(1.0, self.duration - 1.2)
        self.play(t_track.animate.set_value(2.5), run_time=sim_time, rate_func=linear)
        self.wait(0.4)
