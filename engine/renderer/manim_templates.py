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
        VGroup,
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
    Continuously animates across the entire duration with zero frozen frames.
    """

    def __init__(
        self,
        steps: Optional[List[Dict[str, Any]]] = None,
        duration: float = 4.0,
        title: Optional[str] = None,
        **kwargs,
    ):
        if MANIM_AVAILABLE:
            super().__init__()
        self.steps = steps or [
            {"latex": r"\int_{a}^{b} f(x)\,dx = F(b) - F(a)", "label": "Fundamental Theorem of Calculus"},
            {"latex": r"\frac{d}{dx}\left[ \int_{a}^{x} f(t)\,dt \right] = f(x)", "label": "Inverse Operator Duality"},
        ]
        self.scene_duration = max(2.5, float(duration)) + 0.5
        self.title_text = title or "MATHEMATICAL FORMULATION"

    def construct(self):
        curr_mob = None
        curr_label = None
        n = max(1, len(self.steps))

        intro_time = min(0.9, self.scene_duration * 0.25)
        step_time = max(0.8, (self.scene_duration * 0.55) / n)

        for idx, step in enumerate(self.steps):
            raw_latex = step.get("latex") or step.get("formula") or ""
            label_text = step.get("label") or step.get("explanation") or f"Step {idx + 1}"

            new_mob = safe_math_tex(raw_latex, font_size=46)
            new_mob.set_color_by_gradient("#00f2fe", "#ffffff", "#10b981")
            new_label = Text(label_text, font_size=24, color="#94a3b8").next_to(new_mob, UP, buff=0.55)

            if curr_mob is None:
                self.play(Write(new_mob), FadeIn(new_label), run_time=intro_time)
                curr_mob = new_mob
                curr_label = new_label
            else:
                self.play(
                    ReplacementTransform(curr_mob, new_mob),
                    ReplacementTransform(curr_label, new_label),
                    run_time=step_time,
                )
                curr_mob = new_mob
                curr_label = new_label

        # Step 3: Glowing bounding box animation and pulsing highlight sweep across equation
        if curr_mob is not None:
            box = SurroundingRectangle(curr_mob, color="#00f2fe", buff=0.25, corner_radius=0.15)
            pulse_time = max(0.5, self.scene_duration * 0.12)
            self.play(Create(box), run_time=pulse_time)
            self.play(box.animate.set_color("#10b981").set_stroke(width=4.5), run_time=pulse_time)
            remaining = max(0.2, self.scene_duration - (intro_time + step_time * (n - 1) + 2 * pulse_time))
            self.wait(remaining)


class ManimCalculusGraphScene(Scene):
    """
    Continuous curve with ValueTracker sweeping x from -2.0 to +2.2.
    Green Riemann rectangles dynamically accumulate across the curve left-to-right
    while the orange tangent line + point slide smoothly along the curve across the full duration.
    """

    def __init__(
        self,
        fn_str: Optional[str] = None,
        duration: float = 4.0,
        title: str = "CALCULUS • DERIVATIVE & INTEGRAL",
        **kwargs,
    ):
        if MANIM_AVAILABLE:
            super().__init__()
        self.fn_str = fn_str or "0.4 * x**2 + 0.2"
        self.scene_duration = max(2.5, float(duration)) + 0.5
        self.title_text = title

    def construct(self):
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-0.5, 4.5, 1],
            x_length=7.0,
            y_length=5.6,
            axis_config={"color": "#475569"},
        ).to_edge(DOWN, buff=0.7)

        f = lambda x: 0.4 * (x ** 2) + 0.2
        curve = axes.plot(f, color="#00f2fe", stroke_width=4)

        title_mob = Text(self.title_text, font_size=24, color="#94a3b8").to_edge(UP, buff=0.35)
        curve_label = safe_math_tex(r"f(x) = 0.4x^2 + 0.2", color="#00f2fe", font_size=28).next_to(
            title_mob, DOWN, buff=0.2
        )

        intro_time = min(0.8, self.scene_duration * 0.22)
        self.play(Create(axes), Write(title_mob), Write(curve_label), Create(curve), run_time=intro_time)

        t_tracker = ValueTracker(-2.0)

        def get_rects():
            val = t_tracker.get_value()
            if val <= -1.8:
                return VGroup()
            dx = max(0.2, (val - (-2.0)) / 12)
            return axes.get_riemann_rectangles(
                curve,
                x_range=[-2.0, val],
                dx=dx,
                color="#10b981",
                fill_opacity=0.45,
                stroke_color="#00f2fe",
                stroke_width=1.5,
            )

        dynamic_rects = always_redraw(get_rects)
        dynamic_dot = always_redraw(
            lambda: Dot(axes.c2p(t_tracker.get_value(), f(t_tracker.get_value())), color="#f59e0b", radius=0.09)
        )
        dynamic_tangent = always_redraw(
            lambda: axes.get_secant_slope_group(
                t_tracker.get_value(), curve, dx=0.001, secant_line_length=2.6, secant_line_color="#f59e0b"
            )
        )

        self.add(dynamic_rects, dynamic_tangent, dynamic_dot)

        sweep_time = max(1.2, self.scene_duration - intro_time - 0.4)
        self.play(t_tracker.animate.set_value(2.2), run_time=sweep_time, rate_func=linear)
        self.wait(0.4)


class ManimRiemannRefinementScene(Scene):
    """
    Second distinct graph scene: Riemann rectangle refinement N = 4 -> N = 8 -> N = 16 -> N = 32
    converging smoothly to exact definite integral area under f(x) = 1.2 + sin(1.5x).
    Guarantees Scene 3 and Scene 5 never look identical!
    """

    def __init__(
        self,
        duration: float = 4.0,
        title: str = "RIEMANN INTEGRAL REFINEMENT • LIMIT AS N → ∞",
        **kwargs,
    ):
        if MANIM_AVAILABLE:
            super().__init__()
        self.scene_duration = max(2.5, float(duration)) + 0.5
        self.title_text = title

    def construct(self):
        axes = Axes(
            x_range=[0, 3.5, 1],
            y_range=[-0.5, 4.5, 1],
            x_length=7.2,
            y_length=5.6,
            axis_config={"color": "#475569"},
        ).to_edge(DOWN, buff=0.7)

        f = lambda x: 1.2 + np.sin(1.5 * x)
        curve = axes.plot(f, x_range=[0, 3.2], color="#38bdf8", stroke_width=4)

        title_mob = Text(self.title_text, font_size=23, color="#94a3b8").to_edge(UP, buff=0.35)
        curve_label = safe_math_tex(
            r"\lim_{N \to \infty} \sum_{i=1}^N f(x_i^*)\,\Delta x = \int_0^3 f(x)\,dx",
            color="#38bdf8",
            font_size=26,
        ).next_to(title_mob, DOWN, buff=0.2)

        intro_time = min(0.8, self.scene_duration * 0.18)
        self.play(Create(axes), Write(title_mob), Write(curve_label), Create(curve), run_time=intro_time)

        n_values = [4, 8, 16, 32]
        step_time = max(0.45, (self.scene_duration - intro_time - 1.2) / len(n_values))

        current_rects = None
        current_n_label = None

        for n in n_values:
            dx = 3.0 / n
            new_rects = axes.get_riemann_rectangles(
                curve,
                x_range=[0.0, 3.0],
                dx=dx,
                color="#10b981",
                fill_opacity=0.45,
                stroke_color="#38bdf8",
                stroke_width=1.5,
            )
            new_label = safe_math_tex(f"N = {n}\\text{{ partitions}}", color="#10b981", font_size=24).to_corner(UP + RIGHT, buff=0.8)

            if current_rects is None:
                self.play(Create(new_rects), FadeIn(new_label), run_time=step_time)
            else:
                self.play(
                    ReplacementTransform(current_rects, new_rects),
                    ReplacementTransform(current_n_label, new_label),
                    run_time=step_time,
                )
            current_rects = new_rects
            current_n_label = new_label

        exact_area = axes.get_area(curve, x_range=[0.0, 3.0], color=["#10b981", "#38bdf8"], opacity=0.6)
        final_label = safe_math_tex(r"\text{Exact Definite Integral Area}", color="#00f2fe", font_size=22).to_corner(UP + RIGHT, buff=0.8)

        if current_rects is not None:
            self.play(
                ReplacementTransform(current_rects, exact_area),
                ReplacementTransform(current_n_label, final_label),
                run_time=0.6,
            )
        elapsed = intro_time + step_time * len(n_values) + 0.6
        remaining = max(0.4, self.scene_duration - elapsed)
        self.wait(remaining)


class ManimAntiderivativeBoundsScene(Scene):
    """
    Dual stacked curves: f(x) = cos(x) on top vs F(x) = sin(x) on bottom
    with a synchronized vertical scanning bar connecting slope to accumulated height.
    """

    def __init__(
        self,
        duration: float = 4.0,
        title: str = "FUNDAMENTAL THEOREM • DUAL STACKED CURVES",
        **kwargs,
    ):
        if MANIM_AVAILABLE:
            super().__init__()
        self.scene_duration = max(2.5, float(duration)) + 0.5
        self.title_text = title

    def construct(self):
        # Top axes: f(x) = cos(x)
        top_axes = Axes(
            x_range=[-0.5, 3.5, 1],
            y_range=[-1.5, 1.5, 1],
            x_length=7.0,
            y_length=2.5,
            axis_config={"color": "#475569"},
        ).to_edge(UP, buff=1.0)

        # Bottom axes: F(x) = sin(x)
        bot_axes = Axes(
            x_range=[-0.5, 3.5, 1],
            y_range=[-0.5, 1.5, 1],
            x_length=7.0,
            y_length=2.5,
            axis_config={"color": "#475569"},
        ).to_edge(DOWN, buff=0.8)

        f_curve = top_axes.plot(lambda x: np.cos(x), x_range=[0, 3.14], color="#00f2fe", stroke_width=3.5)
        int_curve = bot_axes.plot(lambda x: np.sin(x), x_range=[0, 3.14], color="#10b981", stroke_width=3.5)

        lbl_top = safe_math_tex(r"f(t) = \cos(t)\quad (\text{Rate / Slope})", color="#00f2fe", font_size=22).next_to(top_axes, UP, buff=0.15)
        lbl_bot = safe_math_tex(r"F(x) = \int_0^x \cos(t)\,dt = \sin(x)\quad (\text{Accumulation})", color="#10b981", font_size=22).next_to(bot_axes, UP, buff=0.15)

        intro_time = min(0.8, self.scene_duration * 0.22)
        self.play(
            Create(top_axes), Create(bot_axes),
            Create(f_curve), Create(int_curve),
            Write(lbl_top), Write(lbl_bot),
            run_time=intro_time,
        )

        scan_tracker = ValueTracker(0.1)

        scanner_top = always_redraw(
            lambda: Dot(top_axes.c2p(scan_tracker.get_value(), np.cos(scan_tracker.get_value())), color="#f59e0b", radius=0.08)
        )
        scanner_bot = always_redraw(
            lambda: Dot(bot_axes.c2p(scan_tracker.get_value(), np.sin(scan_tracker.get_value())), color="#f59e0b", radius=0.08)
        )
        scan_area = always_redraw(
            lambda: bot_axes.get_area(int_curve, x_range=[0, scan_tracker.get_value()], color="#10b981", opacity=0.45)
        )

        self.add(scan_area, scanner_top, scanner_bot)

        sweep_time = max(1.2, self.scene_duration - intro_time - 0.4)
        self.play(scan_tracker.animate.set_value(3.14), run_time=sweep_time, rate_func=linear)
        self.wait(0.4)


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
        if MANIM_AVAILABLE:
            super().__init__()
        self.matrix = matrix or [[1.5, 0.5], [0.5, 1.2]]
        self.scene_duration = max(2.5, float(duration)) + 0.5
        self.title_text = title

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

        remaining_time = max(0.4, self.scene_duration - 3.2)
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
        if MANIM_AVAILABLE:
            super().__init__()
        self.barrier_x = barrier_x
        self.scene_duration = max(2.5, float(duration)) + 0.5
        self.title_text = title

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
        sim_time = max(1.0, self.scene_duration - 1.2)
        self.play(t_track.animate.set_value(2.5), run_time=sim_time, rate_func=linear)
        self.wait(0.4)
