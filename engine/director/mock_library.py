"""
engine/director/mock_library.py
Definitive Local Mock Director Library.

Provides pre-validated, high-quality multi-scene JSON scripts covering:
- math (35s, 60s)
- quantum_physics (35s, 60s)
- electrical (35s, 60s)
- mechanics (35s, 60s)
- chemistry (35s, 60s)
- code (35s, 60s)

Each STEM script defines rich manim_spec configurations on 3 to 5 body scenes
so offline compilation and Remotion compositing can be tested in sub-second time.
"""

import copy
import re
from typing import Dict, Any


MOCK_SCRIPTS: Dict[str, Dict[int, Dict[str, Any]]] = {
    "math": {
        35: {
            "title": "Fundamental Theorem of Calculus",
            "subject": "math",
            "duration": 35,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Differential vs Integral Duality",
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Differentiation and integration are inverse operations of each other.",
                    "display_text": "THE FUNDAMENTAL THEOREM OF CALCULUS",
                    "emphasis_word": "inverse",
                },
                {
                    "scene_id": 2,
                    "title": "Slopes vs Continuous Area",
                    "visual_type": "comparison",
                    "spoken_text": "Derivatives track instant slopes while integrals accumulate continuous area.",
                    "problem_label": "Differentiation",
                    "problem_code": "f'(x) = lim_{h->0} [f(x+h) - f(x)] / h",
                    "solution_label": "Integration",
                    "solution_code": "\\int_a^b f(x)dx = F(b) - F(a)",
                },
                {
                    "scene_id": 3,
                    "visual_type": "function_graph",
                    "title": "Area Accumulation Function",
                    "spoken_text": "Sweeping forward, tiny Riemann rectangles accumulate total net area.",
                    "functions": [{"fn": "0.5 * x^2 + 1", "label": "f(x) = 0.5x^2 + 1"}],
                    "x_domain": [0, 4],
                    "y_domain": [0, 10],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "0.5 * x**2 + 1",
                        "x_range": [0, 4, 1],
                        "y_range": [0, 10, 2],
                        "riemann_rectangles": True,
                        "tangent_line": True,
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Derivative of Accumulation",
                    "spoken_text": "The rate accumulated area grows equals the current curve height.",
                    "steps": [
                        {"step": 1, "formula": "A(x) = \\int_a^x f(t) dt", "label": "Accumulation Function"},
                        {"step": 2, "formula": "A'(x) = \\frac{d}{dx} \\int_a^x f(t) dt = f(x)", "label": "Rate of Growth"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "A(x) = \\int_a^x f(t) dt",
                            "\\frac{dA}{dx} = f(x)",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "function_graph",
                    "title": "Evaluation Theorem Integral",
                    "spoken_text": "Total accumulation equals antiderivative values evaluated at the bounds.",
                    "functions": [{"fn": "x^2", "label": "f(x) = x^2"}],
                    "x_domain": [0, 3],
                    "y_domain": [0, 9],
                    "manim_spec": {
                        "template": "riemann_refinement",
                        "function_expr": "1.2 + sin(1.5*x)",
                        "x_range": [0, 3, 1],
                        "y_range": [0, 9, 3],
                        "riemann_rectangles": True,
                        "tangent_line": False,
                    },
                },
                {
                    "scene_id": 6,
                    "title": "Calculus Unified",
                    "visual_type": "concept",
                    "spoken_text": "Integration and differentiation reveal two sides of one truth.",
                    "display_text": "CALCULUS UNIFIED",
                    "emphasis_word": "unified",
                },
            ],
        },
        60: {
            "title": "Fundamental Theorem of Calculus Masterclass",
            "subject": "math",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Calculus bridges the infinite gap between microscopic slopes and massive accumulated geometry.",
                    "display_text": "THE HEART OF CALCULUS",
                    "emphasis_word": "bridges",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Where differentiation dissects instantaneous change, integration accumulates an infinite continuum of slices.",
                    "problem_label": "Slope Operator",
                    "problem_code": "d/dx [F(x)] = f(x)",
                    "solution_label": "Area Operator",
                    "solution_code": "\\int_a^b f(x) dx = F(b) - F(a)",
                },
                {
                    "scene_id": 3,
                    "visual_type": "function_graph",
                    "title": "Riemann Sum Convergence",
                    "spoken_text": "When rectangle widths collapse toward zero, finite Riemann sums converge into exact definite integrals.",
                    "functions": [{"fn": "0.3 * x^3 - x + 2", "label": "f(x)"}],
                    "x_domain": [0, 4],
                    "y_domain": [0, 18],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "0.3 * x**3 - x + 2",
                        "x_range": [0, 4, 1],
                        "y_range": [0, 18, 4],
                        "riemann_rectangles": True,
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "First Fundamental Theorem",
                    "spoken_text": "Differentiating an integral accumulator function unlocks the exact original curve height dynamically.",
                    "steps": [
                        {"step": 1, "formula": "G(x) = \\int_0^x f(t) dt", "label": "Area Function"},
                        {"step": 2, "formula": "G'(x) = \\lim_{h \\to 0} \\frac{1}{h} \\int_x^{x+h} f(t) dt", "label": "Difference Quotient"},
                        {"step": 3, "formula": "G'(x) = f(x)", "label": "Instantaneous Rate"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "G(x) = \\int_0^x f(t) dt",
                            "G'(x) = f(x)",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "function_graph",
                    "title": "Moving Tangent Vector",
                    "spoken_text": "The derivative creates a dynamic local velocity vector along every point of the smooth curve.",
                    "functions": [{"fn": "sin(x) + 2", "label": "f(x) = sin(x) + 2"}],
                    "x_domain": [0, 6],
                    "y_domain": [0, 4],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "np.sin(x) + 2",
                        "x_range": [0, 6, 1],
                        "y_range": [0, 4, 1],
                        "tangent_line": True,
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "math_equation",
                    "title": "Second Fundamental Theorem",
                    "spoken_text": "To find any definite area, we simply compute the net change of its antiderivative function.",
                    "steps": [
                        {"step": 1, "formula": "\\int_a^b f(x) dx = F(b) - F(a)", "label": "Evaluation Theorem"},
                        {"step": 2, "formula": "F'(x) = f(x)", "label": "Antiderivative Definition"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "\\int_a^b f(x) dx = [F(x)]_a^b",
                            "\\int_a^b f(x) dx = F(b) - F(a)",
                        ],
                    },
                },
                {
                    "scene_id": 7,
                    "visual_type": "function_graph",
                    "title": "Nonlinear Area Sweep",
                    "spoken_text": "Parabolic curves sweep out exactly one third the volume of their enclosing coordinate bounding boxes.",
                    "functions": [{"fn": "x^2", "label": "y = x^2"}],
                    "x_domain": [0, 3],
                    "y_domain": [0, 9],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "x**2",
                        "x_range": [0, 3, 1],
                        "y_range": [0, 9, 3],
                        "riemann_rectangles": True,
                    },
                },
                {
                    "scene_id": 8,
                    "visual_type": "math_equation",
                    "title": "Euler Identity Connection",
                    "spoken_text": "Exponential growth and trigonometric rotation join seamlessly through the magic of complex Taylor series expansions.",
                    "steps": [
                        {"step": 1, "formula": "e^{ix} = \\cos(x) + i \\sin(x)", "label": "Euler Formula"},
                        {"step": 2, "formula": "e^{i\\pi} + 1 = 0", "label": "Euler Identity"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "e^{ix} = \\cos(x) + i \\sin(x)",
                            "e^{i\\pi} + 1 = 0",
                        ],
                    },
                },
                {
                    "scene_id": 9,
                    "visual_type": "concept",
                    "spoken_text": "Differential equations govern physics because nature computes rates and areas simultaneously in real time.",
                    "display_text": "CALCULUS POWERS REALITY",
                    "emphasis_word": "powers",
                },
                {
                    "scene_id": 10,
                    "visual_type": "bento_grid",
                    "title": "Calculus Core Pillars",
                    "spoken_text": "Master limits, derivatives, integrals, and series to unlock every physical law in the universe.",
                    "cards": [
                        {"title": "Limits", "description": "Foundation of Continuity"},
                        {"title": "Derivatives", "description": "Instantaneous Slopes"},
                        {"title": "Integrals", "description": "Accumulated Area"},
                        {"title": "Series", "description": "Infinite Polynomials"},
                    ],
                },
            ],
        },
    },
    "quantum_physics": {
        35: {
            "title": "Schrödinger Wavepacket Barrier Tunneling",
            "subject": "quantum_physics",
            "duration": 35,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "In quantum mechanics, particles can penetrate energetic barriers.",
                    "display_text": "QUANTUM TUNNELING",
                    "emphasis_word": "particles",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Classical mechanics predicts reflection, but wavefunctions penetrate barriers.",
                    "problem_label": "Classical Mechanics",
                    "problem_code": "E < V_0  =>  Transmission = 0",
                    "solution_label": "Quantum Mechanics",
                    "solution_code": "T \\approx e^{-2 \\kappa L} > 0",
                },
                {
                    "scene_id": 3,
                    "visual_type": "quantum_sim",
                    "title": "Wavepacket Collision",
                    "spoken_text": "A Gaussian probability wavepacket propagates toward potential barriers.",
                    "sub_mode": "schrodinger_tunneling",
                    "manim_spec": {
                        "template": "quantum_wave",
                        "wave_speed": 1.5,
                        "barrier_x": 0.0,
                        "barrier_height": 3.0,
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Evanescent Wave Decay",
                    "spoken_text": "Inside the barrier, the wavefunction decays exponentially fast.",
                    "steps": [
                        {"step": 1, "formula": "\\psi(x) = \\psi_0 e^{-\\kappa x}", "label": "Decay Law"},
                        {"step": 2, "formula": "\\kappa = \\sqrt{2m(V_0 - E)} / \\hbar", "label": "Decay Constant"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "\\psi(x) = \\psi_0 e^{-\\kappa x}",
                            "T = e^{-2\\kappa L}",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "quantum_sim",
                    "title": "Transmitted Probability Packet",
                    "spoken_text": "An attenuated probability packet emerges on the other side.",
                    "sub_mode": "schrodinger_tunneling",
                    "manim_spec": {
                        "template": "quantum_wave",
                        "wave_speed": 1.2,
                        "barrier_x": 0.0,
                        "barrier_height": 2.5,
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "concept",
                    "spoken_text": "Tunneling powers stellar nuclear fusion and modern electronics.",
                    "display_text": "TUNNELING CREATES LIGHT",
                    "emphasis_word": "powers",
                },
            ],
        },
        60: {
            "title": "Quantum Wavepacket Dynamics Masterclass",
            "subject": "quantum_physics",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Matter is fundamentally composed of oscillating probability waves rather than solid rigid spheres.",
                    "display_text": "PROBABILITY WAVE REALITY",
                    "emphasis_word": "waves",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Newtonian physics assumes deterministic point trajectories, while Schrödinger equations evolve complex probability clouds.",
                    "problem_label": "Deterministic Orbit",
                    "problem_code": "F = m \\cdot a(t)",
                    "solution_label": "Wavefunction State",
                    "solution_code": "i\\hbar \\frac{\\partial \\psi}{\\partial t} = \\hat{H} \\psi",
                },
                {
                    "scene_id": 3,
                    "visual_type": "quantum_sim",
                    "title": "Incident Gaussian Wavepacket",
                    "spoken_text": "A cohesive quantum wavepacket accelerates through coordinate space with constant envelope velocity.",
                    "sub_mode": "schrodinger_tunneling",
                    "manim_spec": {
                        "template": "quantum_wave",
                        "wave_speed": 1.8,
                        "barrier_x": 1.0,
                        "barrier_height": 3.0,
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Time-Dependent Schrödinger Equation",
                    "spoken_text": "The Hamiltonian operator maps spatial curvature directly into instantaneous temporal phase rotation.",
                    "steps": [
                        {"step": 1, "formula": "\\hat{H} = -\\frac{\\hbar^2}{2m} \\nabla^2 + V(x)", "label": "Hamiltonian"},
                        {"step": 2, "formula": "i\\hbar \\dot{\\psi} = \\hat{H} \\psi", "label": "Time Evolution"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "i\\hbar \\frac{\\partial \\psi}{\\partial t} = \\hat{H} \\psi",
                            "\\hat{H} = -\\frac{\\hbar^2}{2m} \\nabla^2 + V(x)",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "quantum_sim",
                    "title": "Evanescent Barrier Penetration",
                    "spoken_text": "Upon reaching the barrier, the phase locks and amplitude decays exponentially within the forbidden region.",
                    "sub_mode": "schrodinger_tunneling",
                    "manim_spec": {
                        "template": "quantum_wave",
                        "wave_speed": 1.0,
                        "barrier_x": 0.0,
                        "barrier_height": 4.0,
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "math_equation",
                    "title": "Heisenberg Uncertainty Limit",
                    "spoken_text": "Confining a particle in spatial coordinates inherently disperses its conjugate momentum distribution outward.",
                    "steps": [
                        {"step": 1, "formula": "\\Delta x \\cdot \\Delta p \\ge \\frac{\\hbar}{2}", "label": "Uncertainty Principle"},
                        {"step": 2, "formula": "[\\hat{x}, \\hat{p}] = i\\hbar", "label": "Canonical Commutator"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "\\Delta x \\cdot \\Delta p \\ge \\frac{\\hbar}{2}",
                            "[\\hat{x}, \\hat{p}] = i\\hbar",
                        ],
                    },
                },
                {
                    "scene_id": 7,
                    "visual_type": "quantum_sim",
                    "title": "Transmitted & Reflected Packets",
                    "spoken_text": "The original packet bifurcates cleanly into a reflected pulse and an attenuated forward wave.",
                    "sub_mode": "schrodinger_tunneling",
                    "manim_spec": {
                        "template": "quantum_wave",
                        "wave_speed": 1.4,
                        "barrier_x": -0.5,
                        "barrier_height": 2.5,
                    },
                },
                {
                    "scene_id": 8,
                    "visual_type": "math_equation",
                    "title": "Probability Density Conservation",
                    "spoken_text": "The integral of probability density over all spatial coordinates remains strictly normalized to unity.",
                    "steps": [
                        {"step": 1, "formula": "P(x) = |\\psi(x)|^2", "label": "Born Rule"},
                        {"step": 2, "formula": "\\int_{-\\infty}^{\\infty} |\\psi(x)|^2 dx = 1", "label": "Unit Normalization"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "P(x) = |\\psi(x)|^2",
                            "\\int |\\psi|^2 dx = 1",
                        ],
                    },
                },
                {
                    "scene_id": 9,
                    "visual_type": "concept",
                    "spoken_text": "Quantum mechanics reveals that nature operates on probabilities rather than classical clockwork certainty.",
                    "display_text": "PROBABILITY REIGNS",
                    "emphasis_word": "probabilities",
                },
                {
                    "scene_id": 10,
                    "visual_type": "bento_grid",
                    "title": "Quantum Foundations",
                    "spoken_text": "Wave-particle duality, uncertainty, superposition, and tunneling form the cornerstones of modern quantum computing.",
                    "cards": [
                        {"title": "Duality", "description": "Wave and Particle"},
                        {"title": "Uncertainty", "description": "Delta x * Delta p >= hbar/2"},
                        {"title": "Superposition", "description": "Linear State Vector"},
                        {"title": "Tunneling", "description": "Barrier Penetration"},
                    ],
                },
            ],
        },
    },
    "electrical": {
        35: {
            "title": "Thévenin Equivalent Circuit Theorems",
            "subject": "electrical",
            "duration": 35,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Complex circuits reduce to one voltage and resistance.",
                    "display_text": "THEVENIN THEOREM",
                    "emphasis_word": "reduce",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Massive loops collapse cleanly into a simple equivalent.",
                    "problem_label": "Complex Network",
                    "problem_code": "V_in = \\sum (I_k R_k)  [12 Loops]",
                    "solution_label": "Thévenin Equivalent",
                    "solution_code": "V_{th} = V_{oc},  R_{th} = R_{eq}",
                },
                {
                    "scene_id": 3,
                    "visual_type": "electrical_grid",
                    "title": "Linear Network Reduction",
                    "spoken_text": "Zeroing sources reveals the equivalent driving point resistance.",
                    "sub_mode": "thevenin_equivalence",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[-y, x]",
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Maximum Power Transfer Condition",
                    "spoken_text": "Maximum power transfers when load resistance matches the source.",
                    "steps": [
                        {"step": 1, "formula": "P_L = I^2 R_L = \\frac{V_{th}^2 R_L}{(R_{th} + R_L)^2}", "label": "Power Expression"},
                        {"step": 2, "formula": "\\frac{dP_L}{dR_L} = 0 \\implies R_L = R_{th}", "label": "Impedance Match"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "P_L = \\frac{V_{th}^2 R_L}{(R_{th} + R_L)^2}",
                            "R_L = R_{th} \\implies P_{max}",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "function_graph",
                    "title": "Power vs Resistance Bell Curve",
                    "spoken_text": "The curve peaks sharply at the match point.",
                    "functions": [{"fn": "4 * x / ((1 + x)^2)", "label": "P(R_L)"}],
                    "x_domain": [0, 4],
                    "y_domain": [0, 1.2],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "4 * x / ((1 + x)**2)",
                        "x_range": [0, 4, 1],
                        "y_range": [0, 1.5, 0.5],
                        "tangent_line": True,
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "concept",
                    "spoken_text": "Matching enables high-speed communications and efficient electrical grids.",
                    "display_text": "PERFECT IMPEDANCE MATCH",
                    "emphasis_word": "matching",
                },
            ],
        },
        60: {
            "title": "Electrical Power Systems and Circuit Theorems",
            "subject": "electrical",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Modern electrical power systems rely on fundamental circuit laws to balance terawatts of energy.",
                    "display_text": "CIRCUIT LAWS & POWER GRIDS",
                    "emphasis_word": "balance",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Kirchhoff Current Law balances node charges, while Voltage Law conserves electric potential across closed loops.",
                    "problem_label": "KCL (Nodes)",
                    "problem_code": "\\sum I_{in} = \\sum I_{out} = 0",
                    "solution_label": "KVL (Loops)",
                    "solution_code": "\\sum \\Delta V_{loop} = 0",
                },
                {
                    "scene_id": 3,
                    "visual_type": "electrical_grid",
                    "title": "Mesh Current Analysis",
                    "spoken_text": "Matrix impedance formulations allow computers to calculate currents across thousands of grid substations simultaneously.",
                    "sub_mode": "kvl_kcl_mesh",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[-y, x]",
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Complex AC Power Equation",
                    "spoken_text": "Apparent power splits vectorially into active real work and oscillating reactive magnetic fields.",
                    "steps": [
                        {"step": 1, "formula": "S = P + jQ = V_{rms} I_{rms}^*", "label": "Complex Power"},
                        {"step": 2, "formula": "|S| = \\sqrt{P^2 + Q^2}", "label": "Power Triangle"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "S = P + jQ",
                            "|S| = \\sqrt{P^2 + Q^2}",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "electrical_grid",
                    "title": "Thévenin Source Reduction",
                    "spoken_text": "Every regional generator substation reduces mathematically to an open-circuit voltage and internal series impedance.",
                    "sub_mode": "thevenin_equivalence",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[x, y]",
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "function_graph",
                    "title": "Maximum Power Transfer Curve",
                    "spoken_text": "Load power delivery reaches its theoretical maximum when load impedance matches the conjugate source impedance.",
                    "functions": [{"fn": "4 * x / ((1 + x)^2)", "label": "P(R)"}],
                    "x_domain": [0, 4],
                    "y_domain": [0, 1.2],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "4 * x / ((1 + x)**2)",
                        "x_range": [0, 4, 1],
                        "y_range": [0, 1.5, 0.5],
                        "tangent_line": True,
                    },
                },
                {
                    "scene_id": 7,
                    "visual_type": "math_equation",
                    "title": "Power Factor Correction",
                    "spoken_text": "Installing shunt capacitors counteracts inductive motor lag, restoring unity power factor efficiency.",
                    "steps": [
                        {"step": 1, "formula": "\\cos(\\phi) = \\frac{P}{|S|}", "label": "Power Factor"},
                        {"step": 2, "formula": "Q_C = P(\\tan\\phi_1 - \\tan\\phi_2)", "label": "Correction Var"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "\\cos(\\phi) = \\frac{P}{|S|}",
                            "Q_C = P(\\tan\\phi_1 - \\tan\\phi_2)",
                        ],
                    },
                },
                {
                    "scene_id": 8,
                    "visual_type": "electrical_grid",
                    "title": "Smart Grid Optimal Flow",
                    "spoken_text": "Automated dispatchers dynamically optimize bus voltage angles to prevent blackout transmission overloads.",
                    "sub_mode": "smart_grid_opf",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[-y, x]",
                    },
                },
                {
                    "scene_id": 9,
                    "visual_type": "concept",
                    "spoken_text": "Rigorous circuit analysis transforms chaotic electromagnetic fields into reliable civilization-scale power.",
                    "display_text": "RELIABLE ENERGY GRIDS",
                    "emphasis_word": "transforms",
                },
                {
                    "scene_id": 10,
                    "visual_type": "bento_grid",
                    "title": "Power Engineering Matrix",
                    "spoken_text": "Master KVL, Thévenin equivalents, AC phasors, and power factor to engineer modern electrical infrastructure.",
                    "cards": [
                        {"title": "KVL / KCL", "description": "Conservation Laws"},
                        {"title": "Thévenin", "description": "Linear Network Reduction"},
                        {"title": "AC Phasors", "description": "Complex Power Vector"},
                        {"title": "Grid OPF", "description": "Optimal Power Flow"},
                    ],
                },
            ],
        },
    },
    "mechanics": {
        35: {
            "title": "Statics and Beam Reaction Forces",
            "subject": "mechanics",
            "duration": 35,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Every structure stands because reactions balance gravity.",
                    "display_text": "STRUCTURAL STATICS",
                    "emphasis_word": "balance",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Translational forces and rotational moments must sum zero.",
                    "problem_label": "Translational Equilibrium",
                    "problem_code": "\\sum F_x = 0,  \\sum F_y = 0",
                    "solution_label": "Rotational Equilibrium",
                    "solution_code": "\\sum M_O = \\sum (r \\times F) = 0",
                },
                {
                    "scene_id": 3,
                    "visual_type": "mechanics_fbd",
                    "title": "Simply Supported Beam FBD",
                    "spoken_text": "Loads distribute reaction forces into both pin supports.",
                    "sub_mode": "beam_weight_distribution",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[0, -y]",
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Moment Equilibrium Derivation",
                    "spoken_text": "Moments around pin A resolve vertical reaction B.",
                    "steps": [
                        {"step": 1, "formula": "\\sum M_A = R_B \\cdot L - P \\cdot a = 0", "label": "Moment Balance"},
                        {"step": 2, "formula": "R_B = P \\cdot \\frac{a}{L}", "label": "Reaction at B"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "\\sum M_A = R_B L - P a = 0",
                            "R_B = P \\frac{a}{L}",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "function_graph",
                    "title": "Bending Moment Diagram",
                    "spoken_text": "Bending moment peaks beneath the concentrated load.",
                    "functions": [{"fn": "x * (4 - x)", "label": "M(x)"}],
                    "x_domain": [0, 4],
                    "y_domain": [0, 5],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "x * (4 - x)",
                        "x_range": [0, 4, 1],
                        "y_range": [0, 5, 1],
                        "tangent_line": True,
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "concept",
                    "spoken_text": "Equilibrium ensures civil structures withstand heavy dynamic loads.",
                    "display_text": "EQUILIBRIUM STANDS TALL",
                    "emphasis_word": "equilibrium",
                },
            ],
        },
        60: {
            "title": "Mechanics and Structural Statics Masterclass",
            "subject": "mechanics",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Structural integrity begins with Newton's laws applied to static equilibrium and stress distribution.",
                    "display_text": "MECHANICS & EQUILIBRIUM",
                    "emphasis_word": "integrity",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "External forces induce internal shear and bending moments that must not exceed material yield strengths.",
                    "problem_label": "Internal Shear",
                    "problem_code": "V(x) = \\frac{dM}{dx}",
                    "solution_label": "Bending Stress",
                    "solution_code": "\\sigma = \\frac{M \\cdot y}{I}",
                },
                {
                    "scene_id": 3,
                    "visual_type": "mechanics_fbd",
                    "title": "Beam Weight Distribution",
                    "spoken_text": "Distributed dead loads combine with point live loads to determine multi-axis pin reactions.",
                    "sub_mode": "beam_weight_distribution",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[0, -y]",
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Shear Force Derivative",
                    "spoken_text": "The derivative of bending moment along the beam's axis equals the internal shear force.",
                    "steps": [
                        {"step": 1, "formula": "\\frac{dV}{dx} = -w(x)", "label": "Distributed Load"},
                        {"step": 2, "formula": "\\frac{dM}{dx} = V(x)", "label": "Moment Derivative"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "\\frac{dM}{dx} = V(x)",
                            "\\sigma_{max} = \\frac{M c}{I}",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "mechanics_fbd",
                    "title": "Inclined Plane Vector Resolution",
                    "spoken_text": "Gravity decomposes into normal compression and tangential sliding force vectors along inclined ramps.",
                    "sub_mode": "inclined_plane_fbd",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[x, -y]",
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "function_graph",
                    "title": "Deflection Curve Under Load",
                    "spoken_text": "Euler-Bernoulli beam theory models elastic deflection as the fourth integral of the load profile.",
                    "functions": [{"fn": "x * (3 - x)", "label": "Deflection w(x)"}],
                    "x_domain": [0, 3],
                    "y_domain": [0, 3],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "x * (3 - x)",
                        "x_range": [0, 3, 1],
                        "y_range": [0, 3, 1],
                        "tangent_line": True,
                    },
                },
                {
                    "scene_id": 7,
                    "visual_type": "math_equation",
                    "title": "Euler-Bernoulli Elastic Equation",
                    "spoken_text": "The second derivative of elastic deflection curve relates directly to bending stiffness EI.",
                    "steps": [
                        {"step": 1, "formula": "EI \\frac{d^2 w}{dx^2} = -M(x)", "label": "Curvature Equation"},
                        {"step": 2, "formula": "w_{max} = \\frac{5 w L^4}{384 EI}", "label": "Uniform Load Deflection"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "EI \\frac{d^2 w}{dx^2} = -M(x)",
                            "w_{max} = \\frac{5 w L^4}{384 EI}",
                        ],
                    },
                },
                {
                    "scene_id": 8,
                    "visual_type": "mechanics_fbd",
                    "title": "Chassis Dynamic Load Transfer",
                    "spoken_text": "Acceleration shifts normal tire contact patches during aggressive braking and turning maneuvers.",
                    "sub_mode": "axle_center_of_mass",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[-x, y]",
                    },
                },
                {
                    "scene_id": 9,
                    "visual_type": "concept",
                    "spoken_text": "Statics and dynamics provide the exact mathematical blueprint for all aerospace and civil engineering.",
                    "display_text": "MECHANICS SHAPES THE WORLD",
                    "emphasis_word": "blueprint",
                },
                {
                    "scene_id": 10,
                    "visual_type": "bento_grid",
                    "title": "Structural Engineering Toolkit",
                    "spoken_text": "Equilibrium, free-body diagrams, shear diagrams, and elasticity define the mechanics master toolkit.",
                    "cards": [
                        {"title": "Equilibrium", "description": "Sum F = 0, Sum M = 0"},
                        {"title": "FBD", "description": "Vector Isolation"},
                        {"title": "Shear & Moment", "description": "V(x) and M(x) Profiles"},
                        {"title": "Elasticity", "description": "Stress, Strain, Deflection"},
                    ],
                },
            ],
        },
    },
    "chemistry": {
        35: {
            "title": "SN2 Nucleophilic Substitution Mechanism",
            "subject": "chemistry",
            "duration": 35,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Nucleophiles attack backside in one concerted step.",
                    "display_text": "SN2 REACTION MECHANISM",
                    "emphasis_word": "concerted",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Concerted SN2 inverts stereocenters, whereas SN1 racemizes.",
                    "problem_label": "SN1 Mechanism",
                    "problem_code": "Rate = k[R-X]  (Racemization)",
                    "solution_label": "SN2 Mechanism",
                    "solution_code": "Rate = k[Nu:][R-X]  (Walden Inversion)",
                },
                {
                    "scene_id": 3,
                    "visual_type": "chemistry_reaction",
                    "title": "Backside Attack & Inversion",
                    "spoken_text": "The nucleophile donates electrons into the carbon antibonding orbital.",
                    "mode": "sn2_concerted",
                    "reaction_name": "Backside Nucleophilic Inversion",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[-x, 0]",
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Bimolecular Rate Law",
                    "spoken_text": "Kinetics depend on both substrate and nucleophile concentrations.",
                    "steps": [
                        {"step": 1, "formula": "Rate = k [Nu^-] [R-X]", "label": "Bimolecular Kinetics"},
                        {"step": 2, "formula": "\\Delta G^\\ddagger = -RT \\ln(k / A)", "label": "Arrhenius Barrier"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "\\text{Rate} = k [\\text{Nu}^-] [\\text{R-X}]",
                            "k = A e^{-\\frac{E_a}{RT}}",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "function_graph",
                    "title": "Reaction Coordinate Free Energy Profile",
                    "spoken_text": "A single transition state peak separates product stereocenters.",
                    "functions": [{"fn": "4 * x * (1 - x)", "label": "\\Delta G(x)"}],
                    "x_domain": [0, 1],
                    "y_domain": [0, 1.5],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "4 * x * (1 - x)",
                        "x_range": [0, 1, 0.25],
                        "y_range": [0, 1.5, 0.5],
                        "tangent_line": True,
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "concept",
                    "spoken_text": "Walden inversion enables synthesis of chiral enantiomer drugs.",
                    "display_text": "CHIRAL SYNTHESIS MASTERY",
                    "emphasis_word": "enables",
                },
            ],
        },
        60: {
            "title": "Organic Reaction Mechanisms Masterclass",
            "subject": "chemistry",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Organic synthesis relies on curved arrow electron flow and molecular orbital interactions.",
                    "display_text": "ORGANIC MECHANISMS",
                    "emphasis_word": "interactions",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Nucleophiles donate electron density to electrophiles, displacing leaving groups across transition states.",
                    "problem_label": "Nucleophile (Nu:)",
                    "problem_code": "HOMO \\text{ Electron Rich}",
                    "solution_label": "Electrophile (E+)",
                    "solution_code": "LUMO \\text{ Electron Deficient}",
                },
                {
                    "scene_id": 3,
                    "visual_type": "chemistry_reaction",
                    "title": "Concerted Backside Attack",
                    "spoken_text": "In SN2, nucleophile approach opposite the carbon-halogen bond triggers complete umbrella inversion.",
                    "mode": "sn2_concerted",
                    "reaction_name": "SN2 Backside Attack",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[-x, 0]",
                    },
                },
                {
                    "scene_id": 4,
                    "visual_type": "math_equation",
                    "title": "Transition State Kinetics",
                    "spoken_text": "The rate constant scales exponentially with the inverse of thermal energy times activation barrier.",
                    "steps": [
                        {"step": 1, "formula": "k = \\frac{k_B T}{h} e^{-\\Delta G^\\ddagger / RT}", "label": "Eyring Equation"},
                        {"step": 2, "formula": "\\Delta G^\\ddagger = \\Delta H^\\ddagger - T\\Delta S^\\ddagger", "label": "Free Energy"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "k = \\frac{k_B T}{h} e^{-\\frac{\\Delta G^\\ddagger}{RT}}",
                            "\\text{Rate} = k [\\text{Nu}] [\\text{Substrate}]",
                        ],
                    },
                },
                {
                    "scene_id": 5,
                    "visual_type": "function_graph",
                    "title": "Double-Well SN1 Energy Landscape",
                    "spoken_text": "In SN1 pathways, an intermediate carbocation creates a shallow local minimum between two peaks.",
                    "functions": [{"fn": "x^4 - 2 * x^2 + 1", "label": "G(x)"}],
                    "x_domain": [-1.5, 1.5],
                    "y_domain": [0, 2],
                    "manim_spec": {
                        "template": "calculus_graph",
                        "function_expr": "x**4 - 2 * x**2 + 1",
                        "x_range": [-1.5, 1.5, 0.5],
                        "y_range": [0, 2, 0.5],
                        "tangent_line": True,
                    },
                },
                {
                    "scene_id": 6,
                    "visual_type": "chemistry_reaction",
                    "title": "Carbocation Intermediate Trapping",
                    "spoken_text": "The planar sp2 carbocation accepts nucleophilic attack with equal probability from either side.",
                    "mode": "sn1_carbocation",
                    "reaction_name": "Carbocation Trapping",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[x, -y]",
                    },
                },
                {
                    "scene_id": 7,
                    "visual_type": "math_equation",
                    "title": "Hammett Linear Free Energy Relation",
                    "spoken_text": "Substituent electronics alter reaction rates systematically via resonance and inductive dipole moments.",
                    "steps": [
                        {"step": 1, "formula": "\\log(k / k_0) = \\rho \\cdot \\sigma", "label": "Hammett Equation"},
                        {"step": 2, "formula": "\\sigma = \\sigma_I + \\sigma_R", "label": "Inductive + Resonance"},
                    ],
                    "manim_spec": {
                        "template": "equation_morph",
                        "equations": [
                            "\\log(k / k_0) = \\rho \\sigma",
                            "\\Delta \\Delta G^\\ddagger = -2.303 RT \\rho \\sigma",
                        ],
                    },
                },
                {
                    "scene_id": 8,
                    "visual_type": "chemistry_reaction",
                    "title": "E2 Elimination Competition",
                    "spoken_text": "Strong bulky bases favor anti-periplanar beta elimination, yielding thermodynamic alkenes.",
                    "mode": "e2_elimination",
                    "reaction_name": "Anti-Periplanar E2 Elimination",
                    "manim_spec": {
                        "template": "vector_field",
                        "vector_field_expr": "[0, -y]",
                    },
                },
                {
                    "scene_id": 9,
                    "visual_type": "concept",
                    "spoken_text": "Controlling reaction coordinates allows chemical synthesis of life-saving medicines and advanced polymers.",
                    "display_text": "CHEMISTRY CREATES MOLECULES",
                    "emphasis_word": "synthesis",
                },
                {
                    "scene_id": 10,
                    "visual_type": "bento_grid",
                    "title": "Reaction Mechanisms Grid",
                    "spoken_text": "SN1, SN2, E1, and E2 mechanisms determine every nucleophile and electrophile reaction outcome.",
                    "cards": [
                        {"title": "SN2", "description": "Concerted Backside Attack"},
                        {"title": "SN1", "description": "Carbocation Intermediate"},
                        {"title": "E2", "description": "Anti-Periplanar Elimination"},
                        {"title": "E1", "description": "Carbocation Elimination"},
                    ],
                },
            ],
        },
    },
    "code": {
        35: {
            "title": "Python Dictionary Hash Table Optimization",
            "subject": "code",
            "duration": 35,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Python dictionaries deliver constant time lookups using compact hash tables.",
                    "display_text": "PYTHON HASH TABLES",
                    "emphasis_word": "constant",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Linear list scanning takes O(N), but hash lookups take O(1).",
                    "problem_label": "Linear Search O(N)",
                    "problem_code": "for item in data:\n    if item == target:\n        return True",
                    "solution_label": "Hash Lookup O(1)",
                    "solution_code": "return target in hash_table",
                },
                {
                    "scene_id": 3,
                    "visual_type": "code_reveal",
                    "title": "Compact Hash Table Architecture",
                    "spoken_text": "Python separates sparse indices from dense key-value arrays.",
                    "code_snippet": "class CompactDict:\n    def __init__(self):\n        self.indices = [-1] * 8\n        self.entries = []",
                },
                {
                    "scene_id": 4,
                    "visual_type": "terminal",
                    "title": "Collision Resolution Benchmark",
                    "spoken_text": "Perturbation indexing minimizes collisions and maintains fast insertions.",
                    "code_snippet": "$ python -m bench_dict\nHash index lookup: 14.2 ns\nStatus: OPTIMAL",
                    "terminal_output": "$ python -m bench_dict\nHash index lookup: 14.2 ns\nCollision resolution: 0 probe overhead\nStatus: OPTIMAL [O(1)]",
                },
                {
                    "scene_id": 5,
                    "visual_type": "diagram",
                    "title": "Hash Table Index Mapping",
                    "spoken_text": "Keys hash directly into sparse buckets pointing to entries.",
                    "nodes": ["Hash Key", "Sparse Index", "Dense Slot"],
                },
                {
                    "scene_id": 6,
                    "visual_type": "concept",
                    "spoken_text": "Compact hash tables save memory and power high-performance software globally.",
                    "display_text": "O(1) RUNTIME MASTERY",
                    "emphasis_word": "memory",
                },
            ],
        },
        60: {
            "title": "Python Hash Tables and Algorithm Engineering",
            "subject": "code",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Modern programming languages achieve blistering speed by engineering cache-friendly algorithmic data structures.",
                    "display_text": "ALGORITHM ENGINEERING",
                    "emphasis_word": "speed",
                },
                {
                    "scene_id": 2,
                    "visual_type": "comparison",
                    "spoken_text": "Traditional sparse hash tables waste massive memory, while compact arrays preserve insertion order naturally.",
                    "problem_label": "Sparse Array Table",
                    "problem_code": "table = [None, (k1, v1), None, None, (k2, v2)]",
                    "solution_label": "Compact Dense Table",
                    "solution_code": "indices = [1, 0, -1]\nentries = [(k2, v2), (k1, v1)]",
                },
                {
                    "scene_id": 3,
                    "visual_type": "code_reveal",
                    "title": "Hash Value Computation",
                    "spoken_text": "Every immutable object implements a fast uniform hashing function with avalanche properties.",
                    "code_snippet": "def hash_key(key: str) -> int:\n    h = 0x811c9dc5\n    for char in key.encode('utf-8'):\n        h = ((h ^ char) * 0x01000193) & 0xFFFFFFFF\n    return h",
                },
                {
                    "scene_id": 4,
                    "visual_type": "code_transform",
                    "title": "Open Addressing Probe Function",
                    "spoken_text": "Perturbation probing guarantees every hash slot in the table is visited without clustering.",
                    "code_snippet": "def probe(h, mask):\n    return ((5 * h) + 1) & mask",
                    "code_before": "def probe(h, mask):\n    return (h + 1) & mask",
                    "code_after": "def probe(h, perturb, mask):\n    return ((5 * h) + 1 + perturb) & mask",
                },
                {
                    "scene_id": 5,
                    "visual_type": "diagram",
                    "title": "Memory Indirection Flow",
                    "spoken_text": "The sparse index array maps directly into dense contiguous entry vectors in memory.",
                    "nodes": ["Hash Key", "Sparse Slot", "Dense Storage"],
                },
                {
                    "scene_id": 6,
                    "visual_type": "terminal",
                    "title": "Memory Footprint Reduction",
                    "spoken_text": "Compact storage cuts dictionary memory overhead by thirty percent across modern Python applications.",
                    "code_snippet": "$ python memory_audit.py\nLegacy: 288B\nCompact: 184B",
                    "terminal_output": "$ python memory_audit.py\nLegacy dict size: 288 bytes\nCompact dict size: 184 bytes\nNet savings: 36.1% reduced RAM",
                },
                {
                    "scene_id": 7,
                    "visual_type": "code_reveal",
                    "title": "Dynamic Resizing amortized O(1)",
                    "spoken_text": "When table fullness exceeds sixty-six percent, the array quadruples to preserve constant lookup guarantees.",
                    "code_snippet": "def maybe_resize(self):\n    if len(self.entries) * 3 >= len(self.indices) * 2:\n        self._resize(len(self.indices) * 4)",
                },
                {
                    "scene_id": 8,
                    "visual_type": "comparison",
                    "spoken_text": "Amortized constant insertion cost ensures rare doubling operations never degrade overall application throughput.",
                    "problem_label": "Worst Case Resize",
                    "problem_code": "resize_cost = O(N)",
                    "solution_label": "Amortized Runtime",
                    "solution_code": "average_cost = O(1)",
                },
                {
                    "scene_id": 9,
                    "visual_type": "concept",
                    "spoken_text": "Mastering low-level data structure layout turns ordinary code into blazing high-performance infrastructure.",
                    "display_text": "CACHE CONSCIOUS ARCHITECTURE",
                    "emphasis_word": "layout",
                },
                {
                    "scene_id": 10,
                    "visual_type": "bento_grid",
                    "title": "Data Structure Engineering",
                    "spoken_text": "Hash functions, collision resolution, cache locality, and resize policies comprise the performance pillars.",
                    "cards": [
                        {"title": "Uniform Hashing", "description": "Avalanche Distribution"},
                        {"title": "Open Addressing", "description": "Perturbation Probe"},
                        {"title": "Dense Packing", "description": "CPU Cache Locality"},
                        {"title": "Amortized O(1)", "description": "Dynamic Array Doubling"},
                    ],
                },
            ],
        },
    },
    "devtools": {
        35: {
            "title": "Acme Cloud SDK v2 Launch",
            "subject": "devtools",
            "duration": 35,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Acme Cloud SDK v2 Launch",
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Acme SDK version two delivers streaming with zero boilerplate.",
                    "display_text": "ACME SDK v2.0 LAUNCH",
                    "emphasis_word": "boilerplate",
                },
                {
                    "scene_id": 2,
                    "title": "CLI Installation",
                    "visual_type": "terminal",
                    "spoken_text": "Upgrade instantly by installing the latest Acme SDK package with npm.",
                    "commands": [
                        {
                            "cmd": "npm install @acme/sdk@latest",
                            "output": [
                                "+ @acme/sdk@2.0.0",
                                "added 1 package in 140ms",
                                "✓ Audited 42 packages with 0 vulnerabilities",
                            ],
                            "status": "✓ Built in 140ms",
                        }
                    ],
                    "code_snippet": "$ npm install @acme/sdk@latest\n+ @acme/sdk@2.0.0\n✓ Installed in 140ms",
                },
                {
                    "scene_id": 3,
                    "title": "V1 to V2 Migration",
                    "visual_type": "code_transform",
                    "spoken_text": "Migrate twenty-eight lines of verbose boilerplate into four declarative lines.",
                    "before_label": "Legacy v1 (28 lines)",
                    "after_label": "New v2 SDK (4 lines)",
                    "before_code": "client = AcmeClient(api_key, retry_limit=5)\nsession = client.create_session(timeout=30)\nreq = session.prepare_request(model='agent')\nres = session.execute(req)\nreturn res.data",
                    "after_code": "client = Acme(api_key)\nreturn client.agents.stream(prompt)",
                },
                {
                    "scene_id": 4,
                    "title": "Agent Execution Stream",
                    "visual_type": "code_reveal",
                    "spoken_text": "Stream token responses directly with native async generator support.",
                    "filename": "agent.ts",
                    "language": "typescript",
                    "code": "import { Acme } from '@acme/sdk';\n\nconst client = new Acme({ apiKey: process.env.ACME_KEY });\n\nfor await (const chunk of client.agents.stream('deploy')) {\n  process.stdout.write(chunk.text);\n}",
                    "code_snippet": "import { Acme } from '@acme/sdk';\n\nconst client = new Acme({ apiKey: process.env.ACME_KEY });\n\nfor await (const chunk of client.agents.stream('deploy')) {\n  process.stdout.write(chunk.text);\n}",
                    "highlight_lines": [5, 6],
                    "focus_phrase": "client.agents.stream",
                },
                {
                    "scene_id": 5,
                    "title": "Edge Architecture & Flow",
                    "visual_type": "diagram",
                    "spoken_text": "Client requests stream through edge gateways directly into vector indexes.",
                    "nodes": ["Client SDK", "Edge Gateway", "Vector DB"],
                    "request_method": "POST /v2/agents/stream",
                    "request_payload": '{\n  "model": "acme-2",\n  "stream": true,\n  "max_tokens": 1024\n}',
                    "response_status": "200 OK • 14ms",
                    "response_payload": '{\n  "status": 200,\n  "latency_ms": 14,\n  "stream": "active"\n}',
                },
                {
                    "scene_id": 6,
                    "title": "Performance & DX Benchmark",
                    "visual_type": "comparison",
                    "spoken_text": "Cut cold-start latency by eighty percent with ninety percent fewer lines.",
                    "problem_label": "Legacy SDK v1",
                    "problem_code": "latency: 840ms\nboilerplate: 28 lines\nerror_rate: 4.2%",
                    "solution_label": "New v2 SDK",
                    "solution_code": "latency: 140ms\nboilerplate: 4 lines\nerror_rate: 0.01%",
                    "comparison_sides": {
                        "left": {"tag": "LEGACY V1", "metric": "840ms Latency"},
                        "right": {"tag": "NEW V2 SDK", "metric": "140ms Latency (6x Faster)"},
                    },
                    "comparison_footer": "KEY TAKEAWAY: v2 SDK reduces cold-start latency by 6x with 90% less code",
                },
            ],
        },
        60: {
            "title": "Acme Cloud SDK v2 Launch & Migration Guide",
            "subject": "devtools",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Acme Cloud SDK v2 Launch",
                    "visual_type": "fullscreen_text",
                    "spoken_text": "Welcome to the next generation of cloud developer tools where lightning fast SDK performance meets zero configuration.",
                    "display_text": "ACME SDK v2.0 LAUNCH",
                    "emphasis_word": "performance",
                },
                {
                    "scene_id": 2,
                    "title": "CLI Installation",
                    "visual_type": "terminal",
                    "spoken_text": "Upgrade your project dependencies in a single step by installing the latest Acme SDK package with zero peer conflicts.",
                    "commands": [
                        {
                            "cmd": "npm install @acme/sdk@latest",
                            "output": [
                                "+ @acme/sdk@2.0.0",
                                "added 1 package in 140ms",
                                "✓ Audited 42 packages with 0 vulnerabilities",
                            ],
                            "status": "✓ Built in 140ms",
                        }
                    ],
                    "code_snippet": "$ npm install @acme/sdk@latest\n+ @acme/sdk@2.0.0\n✓ Installed in 140ms",
                },
                {
                    "scene_id": 3,
                    "title": "V1 to V2 Migration",
                    "visual_type": "code_transform",
                    "spoken_text": "Replace twenty-eight lines of legacy session connection boilerplate with four clean declarative lines of code.",
                    "before_label": "Legacy v1 (28 lines)",
                    "after_label": "New v2 SDK (4 lines)",
                    "before_code": "client = AcmeClient(api_key, retry_limit=5)\nsession = client.create_session(timeout=30)\nreq = session.prepare_request(model='agent')\nres = session.execute(req)\nreturn res.data",
                    "after_code": "client = Acme(api_key)\nreturn client.agents.stream(prompt)",
                },
                {
                    "scene_id": 4,
                    "title": "Agent Execution Stream",
                    "visual_type": "code_reveal",
                    "spoken_text": "Stream real-time tokens directly to your client interface using native async generators and structured TypeScript typing.",
                    "filename": "agent.ts",
                    "language": "typescript",
                    "code": "import { Acme } from '@acme/sdk';\n\nconst client = new Acme({ apiKey: process.env.ACME_KEY });\n\nfor await (const chunk of client.agents.stream('deploy')) {\n  process.stdout.write(chunk.text);\n}",
                    "code_snippet": "import { Acme } from '@acme/sdk';\n\nconst client = new Acme({ apiKey: process.env.ACME_KEY });\n\nfor await (const chunk of client.agents.stream('deploy')) {\n  process.stdout.write(chunk.text);\n}",
                    "highlight_lines": [5, 6],
                    "focus_phrase": "client.agents.stream",
                },
                {
                    "scene_id": 5,
                    "title": "Edge Architecture & Flow",
                    "visual_type": "diagram",
                    "spoken_text": "Client payloads stream across global edge nodes with automatic failover directly querying low latency vector search indices.",
                    "nodes": ["Client SDK", "Edge Gateway", "Vector DB"],
                    "request_method": "POST /v2/agents/stream",
                    "request_payload": '{\n  "model": "acme-2",\n  "stream": true,\n  "max_tokens": 1024\n}',
                    "response_status": "200 OK • 14ms",
                    "response_payload": '{\n  "status": 200,\n  "latency_ms": 14,\n  "stream": "active"\n}',
                },
                {
                    "scene_id": 6,
                    "title": "Performance & DX Benchmark",
                    "visual_type": "comparison",
                    "spoken_text": "Cut cold start latency by eighty percent while reducing boilerplate maintenance by ninety percent across all engineering teams.",
                    "problem_label": "Legacy SDK v1",
                    "problem_code": "latency: 840ms\nboilerplate: 28 lines\nerror_rate: 4.2%",
                    "solution_label": "New v2 SDK",
                    "solution_code": "latency: 140ms\nboilerplate: 4 lines\nerror_rate: 0.01%",
                    "comparison_sides": {
                        "left": {"tag": "LEGACY V1", "metric": "840ms Latency"},
                        "right": {"tag": "NEW V2 SDK", "metric": "140ms Latency (6x Faster)"},
                    },
                    "comparison_footer": "KEY TAKEAWAY: v2 SDK reduces cold-start latency by 6x with 90% less code",
                },
            ],
        },
    },
}


def inject_source_facts_into_mock(script: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    """Inject customer ground-truth facts (CLI commands, snippets, endpoints) directly into mock scenes."""
    if not facts:
        return script

    prod_name = facts.get("product_name") or ""
    prod_title = prod_name if prod_name.lower().endswith("release") else f"{prod_name} Release"
    prod_clean = re.sub(r'\s+release\b', '', prod_name, flags=re.IGNORECASE).strip() or prod_name
    cmds = facts.get("cli_commands") or []
    snippets = facts.get("code_snippets") or []
    endpoints = facts.get("api_endpoints") or []
    key_points = facts.get("key_points") or []

    script["source_facts"] = facts

    for sc in script.get("scenes", []):
        sc["source_facts"] = facts
        v_type = sc.get("visual_type") or sc.get("scene_type")

        # 1. Fullscreen Text / Hero Hook
        if v_type in {"fullscreen_text", "concept"} and prod_name:
            short_name = prod_name.split()[0] if prod_name else "this platform"
            sc["title"] = prod_title
            sc["display_text"] = prod_title.upper()
            sc["spoken_text"] = f"Introducing {short_name}: distributed caching built for the modern edge."
            install_cmd = cmds[0] if cmds else f"npm install {prod_name}"
            top_pt = key_points[0] if key_points else "Sub-millisecond Edge Latency"
            second_pt = key_points[1] if len(key_points) > 1 else "6x Faster Cold Starts"
            sc["concept_nodes"] = [
                {"id": "node_install", "tag": "INSTALL", "label": install_cmd, "detail": "One-step setup with zero peer conflicts"},
                {"id": "node_stream", "tag": "STREAMING", "label": "Native Async Streaming", "detail": "Declarative client streaming with zero boilerplate"},
                {"id": "node_perf", "tag": "BENCHMARK", "label": top_pt, "detail": second_pt},
            ]
            sc["points"] = [
                f"{prod_name} engineered for distributed edge runtimes",
                "Declarative TypeScript async generator streaming",
                f"{top_pt} with verified zero-config reliability",
            ]

        # 2. Terminal CLI Simulator
        elif v_type == "terminal" and cmds:
            primary_cmd = cmds[0]
            sc["title"] = f"Install {prod_clean or 'CLI'}"
            sc["spoken_text"] = f"Install the latest {short_name or 'package'} SDK with npm."
            sc["commands"] = [
                {
                    "cmd": primary_cmd,
                    "output": [
                        f"+ {prod_name or 'package'}@2.0.0",
                        "added 1 package, audited 48 packages in 140ms",
                        "found 0 vulnerabilities",
                    ],
                    "status": "✓ Package verified & ready • 140ms",
                }
            ]
            sc["code_snippet"] = f"$ {primary_cmd}\n+ {prod_name or 'package'}@2.0.0\n✓ Package verified & ready"

        # 3. Code Reveal
        elif v_type == "code_reveal" and snippets:
            chosen = snippets[1] if len(snippets) >= 2 else snippets[0]
            sc["code"] = chosen["code"]
            sc["code_snippet"] = chosen["code"]
            if chosen.get("language"):
                sc["language"] = chosen["language"]
            if prod_name:
                sc["title"] = f"{prod_clean} Integration"
            sc["spoken_text"] = "Stream cached values with native async generator support."

        # 4. Code Transform (Before -> After Morph)
        elif v_type == "code_transform" and snippets:
            if len(snippets) >= 2:
                sc["before_code"] = snippets[0]["code"]
                sc["after_code"] = snippets[1]["code"]
                sc["before_label"] = f"Legacy v1 ({len(snippets[0]['code'].splitlines())} lines)"
                sc["after_label"] = f"New {prod_clean or 'v2'} ({len(snippets[1]['code'].splitlines())} lines)"
            else:
                sc["after_code"] = snippets[0]["code"]
                sc["after_label"] = f"New {prod_clean or 'v2'} SDK"
            sc["spoken_text"] = "Migrate verbose legacy callback patterns into declarative async streaming."

        # 5. Diagram
        elif v_type == "diagram":
            if endpoints:
                sc["request_method"] = endpoints[0]
            if prod_name:
                sc["nodes"] = ["Client SDK", f"{prod_clean} Gateway", "Origin DB"]
                sc["title"] = f"{prod_clean} Architecture"
            sc["spoken_text"] = "Global client requests resolve at edge nodes before touching origin databases."

        # 6. Bento Grid / Conclusion / Comparison
        elif v_type in {"bento_grid", "comparison"}:
            sc["title"] = "Production Scale & Benchmarks"
            sc["spoken_text"] = "Cut cold-start latency by eighty percent with ninety percent less code."
            top_metric = key_points[0] if key_points else "99.9% Cache Hit Rate"
            latency_metric = key_points[1] if len(key_points) > 1 else "1.4ms Edge Lookup"
            cold_metric = key_points[2] if len(key_points) > 2 else "6x Faster Cold Starts"
            lines_metric = key_points[3] if len(key_points) > 3 else "90% Boilerplate Cut"

            bento_cards = [
                {
                    "title": "-80% Latency",
                    "algo_type": "latency_drop",
                    "category": "COLD START",
                    "description": latency_metric,
                },
                {
                    "title": "90% Fewer Lines",
                    "algo_type": "boilerplate_cut",
                    "category": "DEVELOPER DX",
                    "description": lines_metric,
                },
                {
                    "title": "99.9% Hit Rate",
                    "algo_type": "cache_hit",
                    "category": "CACHE EFFICIENCY",
                    "description": top_metric,
                },
                {
                    "title": "Zero Conflicts",
                    "algo_type": "async_stream",
                    "category": "PACKAGE INSTALL",
                    "description": "Native ESM and TypeScript async promise streaming",
                },
            ]
            sc["cards"] = bento_cards
            sc["bento_data"] = {
                "domain": "code",
                "section_title": "PRODUCTION SCALE & BENCHMARKS",
                "subtitle": "Measured Performance Across 40 Global Edge Regions",
                "cards": bento_cards,
                "cta": f"{cmds[0] if cmds else 'npm install @acme/edgecache'} • docs.acme.dev",
            }
            sc["section_title"] = "PRODUCTION SCALE & BENCHMARKS"
            sc["subtitle"] = "Measured Performance Across 40 Global Edge Regions"
            sc["comparison_sides"] = {
                "left": {"tag": "LEGACY V1", "metric": "840ms Latency (Callback Hell)"},
                "right": {"tag": "NEW V2 SDK", "metric": "1.4ms Latency (6x Faster)"},
            }
            sc["comparison_footer"] = "KEY TAKEAWAY: v2 SDK cuts cold-start latency by 80% with 90% fewer lines"
            sc["problem_label"] = "Legacy SDK v1"
            sc["problem_code"] = "latency: 840ms\nboilerplate: 28 lines\nerror_rate: 4.2%"
            sc["solution_label"] = "New v2 SDK"
            sc["solution_code"] = f"{top_metric}\n{latency_metric}\n{cold_metric}"

    return script


def get_mock_script(
    topic: str,
    duration: int,
    subject: str = "auto",
    source_text: Any = None,
    source_facts: Any = None,
) -> Dict[str, Any]:
    """
    Returns a rich, pre-validated mock script from the library for offline testing.
    Falls back gracefully across subjects and durations.
    Injects customer-provided ground-truth source facts into scenes.
    """
    subj = (subject or "math").lower()
    t = (topic or "").lower()

    if subj == "devtools" or (source_text and str(source_text).strip()) or any(w in t for w in ("sdk", "devtools", "api", "cli", "migration", "changelog", "endpoint")):
        subj = "devtools"
    elif subj not in MOCK_SCRIPTS:
        if any(w in t for w in ("quantum", "tunnel", "wave", "schrodinger")):
            subj = "quantum_physics"
        elif any(w in t for w in ("circuit", "voltage", "grid", "electrical", "thevenin")):
            subj = "electrical"
        elif any(w in t for w in ("beam", "statics", "mechanics", "stress", "force")):
            subj = "mechanics"
        elif any(w in t for w in ("sn2", "chemistry", "reaction", "molecule", "chiral")):
            subj = "chemistry"
        elif any(w in t for w in ("python", "code", "algorithm", "dict", "hash")):
            subj = "code"
        else:
            subj = "math"

    dur = 60 if duration >= 50 else 35
    if dur not in MOCK_SCRIPTS[subj]:
        dur = 35

    import copy
    script = copy.deepcopy(MOCK_SCRIPTS[subj][dur])
    if topic:
        script["title"] = topic.strip()

    # Extract source facts if not explicitly provided
    facts = source_facts
    if not facts and source_text and isinstance(source_text, str) and source_text.strip():
        try:
            try:
                from engine.ingestion.source_loader import extract_source_facts
            except ImportError:
                from ingestion.source_loader import extract_source_facts
            facts = extract_source_facts(source_text.strip())
        except Exception:
            facts = None

    if facts:
        script = inject_source_facts_into_mock(script, facts)

    return script

