"""
Unit tests for Polymorphic Validation Gate across all STEM and non-code domains.
Verifies that:
1. Python ast.parse() checks are strictly restricted to subject == 'code' and Python visual types.
2. For all STEM subjects (quantum_physics, mechanics, electrical, chemistry, physics, math, ml),
   comparison and formula fields (problem_code, solution_code, code_snippet, etc.) are validated
   as formatted formula strings rather than Python source code.
3. Generic schema fields (scene_id, title, narration, visual_type, duration) are strictly validated
   without hardcoded topic-specific fallbacks.
"""

import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from validation.schema import (
    validate_script_plan,
    validate_or_raise,
    resolve_script_subject,
    validate_formula_string,
    ScriptValidationError,
    VALID_SCENE_TYPES,
    ALL_SUBJECTS,
    STEM_SUBJECTS,
)


class TestPolymorphicValidation(unittest.TestCase):

    def test_math_equations_pass_validation_without_python_ast(self):
        """
        Verify that mathematical LaTeX equations, limit definitions, and integrals
        in comparison and code fields pass validation cleanly when subject == 'math'.
        Under Python ast.parse(), backslashes, limits, and primes would fail as SyntaxError.
        """
        plan = {
            "title": "Fundamental Theorem of Calculus and Derivatives",
            "subject": "math",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Calculus bridges instantaneous rates of change with accumulated area.",
                    "display_text": "FUNDAMENTAL THEOREM OF CALCULUS",
                },
                {
                    "scene_type": "math_equation",
                    "spoken_text": "The derivative is formally defined using a first principles limit.",
                    "steps": [
                        {
                            "formula": r"\frac{df}{dx} = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}",
                            "explanation": "First-principles limit definition",
                        },
                        {
                            "formula": r"\int_a^b f'(x) dx = f(b) - f(a)",
                            "explanation": "Fundamental connection to definite integrals",
                        },
                    ],
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Notice how limit definitions contrast with power rule shortcuts.",
                    "problem_label": "Limit Definition (Rigorous)",
                    "problem_code": r"\lim_{h \to 0} \frac{(x+h)^2 - x^2}{h} = 2x",
                    "solution_label": "Power Rule (Direct)",
                    "solution_code": r"\frac{d}{dx}[x^n] = n \cdot x^{n-1} \implies 2x",
                },
                {
                    "scene_type": "function_graph",
                    "spoken_text": "The parabola and its tangent slope illustrate this rate.",
                    "functions": [{"fn": "x^2", "label": "f(x) = x^2"}],
                    "x_domain": [-4, 4],
                    "y_domain": [0, 16],
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected math plan with LaTeX to pass validation, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_physics_equations_pass_validation_without_python_ast(self):
        """
        Verify that physics vector equations and equilibrium equations in comparison
        fields pass validation without triggering Python AST errors when subject == 'physics'.
        """
        plan = {
            "title": "Newton's Laws and Classical Dynamics",
            "subject": "physics",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Every action force creates an equal and opposite reaction force.",
                    "display_text": "NEWTON'S THIRD LAW",
                },
                {
                    "scene_type": "physics_sim",
                    "spoken_text": "Consider a block resting on a surface under gravity.",
                    "sim_type": "forces",
                    "objects": [{"name": "block", "mass": 10}],
                    "forces": [{"name": "F_g", "direction": 270, "magnitude": 98.1}],
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Static equilibrium balances all net forces to exactly zero.",
                    "problem_label": "Dynamic Acceleration",
                    "problem_code": r"\vec{F}_{\text{net}} = m \frac{d\vec{v}}{dt} = m \vec{a}",
                    "solution_label": "Static Equilibrium",
                    "solution_code": r"\Sigma \vec{F} = \vec{F}_N + \vec{F}_g = 0",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected physics plan with LaTeX vectors to pass validation, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_quantum_physics_equations_pass_validation(self):
        """
        Verify that quantum physics commutators, wavepackets, and Dirac spinors pass validation.
        """
        plan = {
            "title": "Quantum Tunneling and Wavepacket Duality",
            "subject": "quantum_physics",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Quantum particles penetrate finite potential energy barriers through tunneling.",
                    "display_text": "QUANTUM TUNNELING DISCOVERY",
                },
                {
                    "scene_type": "quantum_sim",
                    "sub_mode": "schrodinger_tunneling",
                    "spoken_text": "A wavepacket hits the barrier with exponential evanescent decay.",
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Classical determinism gives way to canonical quantum uncertainty bounds.",
                    "problem_label": "Classical Mechanics",
                    "problem_code": r"[x, p]_{\text{PB}} = 0 \implies \Delta x \cdot \Delta p = 0",
                    "solution_label": "Quantum Mechanics",
                    "solution_code": r"[\hat{x}, \hat{p}] = i\hbar \implies \sigma_x \cdot \sigma_p \ge \frac{\hbar}{2}",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected quantum plan to pass validation, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_mechanics_equations_pass_validation(self):
        """
        Verify that structural mechanics torque and shear equations pass validation.
        """
        plan = {
            "title": "Beam Weight Distribution and Statics",
            "subject": "mechanics",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Structural beams maintain equilibrium by distributing vertical reaction forces.",
                    "display_text": "BEAM WEIGHT DISTRIBUTION",
                },
                {
                    "scene_type": "mechanics_fbd",
                    "sub_mode": "beam_weight_distribution",
                    "spoken_text": "Pin support and roller support react to applied point loads.",
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Torque and vertical force balance uniquely determine reaction magnitudes.",
                    "problem_label": "Force Equilibrium",
                    "problem_code": r"\Sigma F_y = R_A + R_B - W_1 - W_{\text{beam}} = 0",
                    "solution_label": "Torque Equilibrium",
                    "solution_code": r"\Sigma \tau_A = R_B \cdot L - W_1 \cdot x - W_{\text{beam}} \cdot \frac{L}{2} = 0",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected mechanics plan to pass validation, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_electrical_equations_pass_validation(self):
        """
        Verify that electrical circuits KVL/KCL and Thévenin equations pass validation.
        """
        plan = {
            "title": "Thévenin Equivalent Circuit Analysis",
            "subject": "electrical",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Any linear two terminal network reduces to single equivalent source.",
                    "display_text": "THÉVENIN EQUIVALENT CIRCUIT",
                },
                {
                    "scene_type": "electrical_grid",
                    "sub_mode": "thevenin_equivalence",
                    "spoken_text": "We determine the open circuit voltage across the terminals.",
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Maximum power transfer occurs when load impedance matches internal resistance.",
                    "problem_label": "Arbitrary Load",
                    "problem_code": r"P_L = I^2 R_L = \frac{V_{\text{th}}^2 R_L}{(R_{\text{th}} + R_L)^2}",
                    "solution_label": "Matched Load",
                    "solution_code": r"R_L = R_{\text{th}} \implies P_{\text{max}} = \frac{V_{\text{th}}^2}{4 R_{\text{th}}}",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected electrical plan to pass validation, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_chemistry_equations_pass_validation(self):
        """
        Verify that organic chemistry rate laws and mechanisms pass validation.
        """
        plan = {
            "title": "Nucleophilic Substitution SN1 vs SN2",
            "subject": "chemistry",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Nucleophilic substitution mechanisms divide between concerted and stepwise pathways.",
                    "display_text": "SN1 VS SN2 MECHANISMS",
                },
                {
                    "scene_type": "chemistry_reaction",
                    "reaction_name": "SN2 Substitution",
                    "mode": "sn2_substitution",
                    "spoken_text": "Hydroxide attacks backside while bromide leaves in single transition.",
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Second order kinetics contrast against unimolecular carbocation ionization.",
                    "problem_label": "Concerted SN2",
                    "problem_code": r"\text{Rate} = k [\text{R-X}][\text{Nu}^-] \quad (\text{Walden Inversion})",
                    "solution_label": "Stepwise SN1",
                    "solution_code": r"\text{Rate} = k [\text{R-X}] \quad (\text{50% R + 50% S Racemic})",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected chemistry plan to pass validation, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_ml_equations_pass_validation(self):
        """
        Verify that ML formulas and loss functions pass validation without AST parse errors.
        """
        plan = {
            "title": "Clustering Algorithms and Optimization",
            "subject": "ml",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Unsupervised clustering groups data points using geometric density relationships.",
                    "display_text": "UNSUPERVISED ML OVERVIEW",
                },
                {
                    "scene_type": "bento_grid",
                    "spoken_text": "We contrast spherical centroid models against density reachable clusters.",
                    "cards": [{"title": "K-Means"}, {"title": "DBSCAN"}],
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Linear separation fails when data forms non linear concentric geometries.",
                    "problem_label": "K-Means Inertia",
                    "problem_code": r"J = \sum_{j=1}^k \sum_{i=1}^n ||x_i^{(j)} - c_j||^2",
                    "solution_label": "DBSCAN Neighborhood",
                    "solution_code": r"N_\epsilon(p) = \{q \in D \mid \text{dist}(p, q) \le \epsilon\} \ge \text{minPts}",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected ML plan to pass validation, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_code_subject_strictly_enforces_ast_parse(self):
        """
        Verify that when subject == 'code', invalid Python syntax in comparison,
        code_reveal, code_transform, or neural_code_split is strictly caught by AST parsing.
        """
        # 1. Invalid comparison problem_code
        broken_code_plan = {
            "title": "Python Dictionary Keys Trick",
            "subject": "code",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Did you know dictionary keys can be tuples?",
                    "display_text": "TUPLE DICTIONARY KEYS",
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Never use mutable lists as dictionary key lookups.",
                    "problem_label": "Syntax Error Code",
                    "problem_code": "def broken(x: pass",  # Broken python syntax
                    "solution_label": "Valid Python Code",
                    "solution_code": "data = {(1, 2): True}",
                },
            ],
        }

        is_valid, errors = validate_script_plan(broken_code_plan)
        self.assertFalse(is_valid)
        self.assertTrue(any("problem_code AST syntax check failed" in e for e in errors))

        # 2. Invalid code_reveal code_snippet
        broken_reveal_plan = {
            "title": "Python Generator Tricks",
            "subject": "code",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Generators save memory by yielding elements one by one.",
                    "display_text": "PYTHON GENERATOR MEMORY",
                },
                {
                    "scene_type": "code_reveal",
                    "spoken_text": "Here is how you write a memory efficient generator.",
                    "code_snippet": "for in range(10): yield x",  # Missing target
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Lists consume memory while generators stream values on demand.",
                    "problem_code": "x = [i for i in range(1000)]",
                    "solution_code": "g = (i for i in range(1000))",
                },
            ],
        }

        is_valid, errors = validate_script_plan(broken_reveal_plan)
        self.assertFalse(is_valid)
        self.assertTrue(any("AST syntax check failed" in e for e in errors))

    def test_generic_schema_verification_across_subjects(self):
        """
        Verify that required JSON schema fields (scene_id, title, narration, visual_type, duration)
        are polymorphically validated across subjects.
        """
        # Test scene plan using modern schema naming: scene_id, title, narration, visual_type, duration
        plan = {
            "title": "Generic Schema Test Plan",
            "subject": "physics",
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "title": "Gravitational Acceleration",
                    "visual_type": "fullscreen_text",
                    "narration": "All free falling objects accelerate at nine point eight meters.",
                    "duration": 3.5,
                },
                {
                    "scene_id": "scene_02",
                    "title": "Kinematic Vector Profile",
                    "visual_type": "physics_sim",
                    "narration": "Velocity arrows grow linearly with every passing second elapsed.",
                    "duration": 4.0,
                    "sim_type": "forces",
                    "forces": [{"name": "F_g", "direction": 270, "magnitude": 9.8}],
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected generic schema fields to validate cleanly, got: {errors}")
        self.assertEqual(len(errors), 0)

        # Test failure: empty narration
        bad_plan = {
            "title": "Missing Narration Plan",
            "subject": "physics",
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "visual_type": "fullscreen_text",
                    "narration": "",  # Empty narration
                    "display_text": "EMPTY NARRATION",
                },
                {
                    "scene_id": "scene_02",
                    "visual_type": "physics_sim",
                    "narration": "Valid words for the second scene in test.",
                    "sim_type": "forces",
                },
            ],
        }
        is_valid, errors = validate_script_plan(bad_plan)
        self.assertFalse(is_valid)
        self.assertTrue(any("empty or non-string" in e for e in errors))

        # Test failure: invalid negative duration
        bad_duration_plan = {
            "title": "Negative Duration Plan",
            "subject": "math",
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "visual_type": "fullscreen_text",
                    "narration": "Initial hook for testing negative duration verification check.",
                    "display_text": "NEGATIVE DURATION",
                    "duration": -2.5,
                },
                {
                    "scene_id": "scene_02",
                    "visual_type": "math_equation",
                    "narration": "Equations verify correctly when steps are properly provided.",
                    "steps": ["f(x) = x^2"],
                },
            ],
        }
        is_valid, errors = validate_script_plan(bad_duration_plan)
        self.assertFalse(is_valid)
        self.assertTrue(any("invalid 'duration'" in e for e in errors))

    def test_resolve_script_subject_polymorphism(self):
        """
        Verify that resolve_script_subject accurately detects all 9 domains
        from explicit subject, visual primitives, and title heuristics.
        """
        for subj in ALL_SUBJECTS:
            self.assertEqual(resolve_script_subject({"subject": subj}), subj)
            self.assertEqual(resolve_script_subject({"domain": subj}), subj)

        # Inferred from primitives
        self.assertEqual(
            resolve_script_subject({"scenes": [{"scene_type": "quantum_sim"}]}),
            "quantum_physics",
        )
        self.assertEqual(
            resolve_script_subject({"scenes": [{"visual_type": "mechanics_fbd"}]}),
            "mechanics",
        )
        self.assertEqual(
            resolve_script_subject({"scenes": [{"visual_type": "electrical_grid"}]}),
            "electrical",
        )
        self.assertEqual(
            resolve_script_subject({"scenes": [{"visual_type": "chemistry_reaction"}]}),
            "chemistry",
        )
        self.assertEqual(
            resolve_script_subject({"scenes": [{"visual_type": "math_equation"}]}),
            "math",
        )
        self.assertEqual(
            resolve_script_subject({"scenes": [{"visual_type": "physics_sim"}]}),
            "physics",
        )
        self.assertEqual(
            resolve_script_subject({"scenes": [{"visual_type": "bento_grid"}]}),
            "ml",
        )

    def test_code_reveal_and_transform_with_formulas_on_stem_pass_without_ast(self):
        """
        Verify that code_reveal and code_transform scenes containing LaTeX or formulas
        pass validation without AST parsing when subject is a STEM domain, but fail
        under subject == 'code'.
        """
        stem_plan = {
            "title": "Maxwell's Equations and Wave Solutions",
            "subject": "physics",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "Maxwell unified electricity and magnetism into four symmetric differential laws.",
                    "display_text": "MAXWELL'S FIELD EQUATIONS",
                },
                {
                    "scene_type": "code_reveal",
                    "spoken_text": "Ampere's law accounts for the displacement current density.",
                    "code_snippet": r"\nabla \times \vec{B} = \mu_0 \vec{J} + \mu_0 \epsilon_0 \frac{\partial \vec{E}}{\partial t}",
                },
                {
                    "scene_type": "code_transform",
                    "spoken_text": "In a vacuum the wave equation emerges directly from the curl.",
                    "code_snippet": r"\nabla^2 \vec{E} - \frac{1}{c^2} \frac{\partial^2 \vec{E}}{\partial t^2} = 0",
                },
                {
                    "scene_type": "comparison",
                    "spoken_text": "Static Gauss equations contrast against dynamic time varying induction.",
                    "problem_label": "Static Gauss Law",
                    "problem_code": r"\nabla \cdot \vec{E} = \frac{\rho}{\epsilon_0}",
                    "solution_label": "Faraday Induction",
                    "solution_code": r"\nabla \times \vec{E} = -\frac{\partial \vec{B}}{\partial t}",
                },
            ],
        }

        # Passes cleanly for subject == 'physics'
        is_valid, errors = validate_script_plan(stem_plan)
        self.assertTrue(is_valid, f"Expected physics plan with LaTeX code_reveal to pass, got: {errors}")

        # The exact same plan marked as 'code' must fail AST parse on backslashes and formulas
        code_plan = dict(stem_plan)
        code_plan["subject"] = "code"
        is_valid, errors = validate_script_plan(code_plan)
        self.assertFalse(is_valid, "Expected code subject to fail AST parse on LaTeX formulas")
        self.assertTrue(any("AST syntax check failed" in err for err in errors))

    def test_neural_code_split_with_formula_on_ml_passes_without_ast(self):
        """
        Verify that neural_code_split scenes containing mathematical formulas or LaTeX
        pass validation under subject == 'ml' without being rejected by Python AST parsing.
        """
        formula_ml_plan = {
            "title": "Perceptron Forward Activation",
            "subject": "ml",
            "scenes": [
                {
                    "scene_type": "fullscreen_text",
                    "spoken_text": "The artificial neuron computes a linear combination before nonlinear activation.",
                    "display_text": "PERCEPTRON ACTIVATION",
                },
                {
                    "scene_type": "neural_code_split",
                    "spoken_text": "Logits pass through the sigmoid activation to output probabilities.",
                    "model_name": "Perceptron",
                    "code_snippet": r"\hat{y} = \sigma\left(\sum_{i=1}^d w_i x_i + b\right)",
                },
            ],
        }

        is_valid, errors = validate_script_plan(formula_ml_plan)
        self.assertTrue(is_valid, f"Expected ML neural_code_split with LaTeX formula to pass, got: {errors}")

    def test_comparison_across_all_stem_subjects_accepts_latex_formulas(self):
        """
        Verify that comparison scenes accept formatted LaTeX equation strings
        across all STEM subjects without any Python ast.parse() errors.
        """
        stem_samples = {
            "quantum_physics": (
                r"\langle \psi | \hat{H} | \psi \rangle \ge E_0",
                r"i\hbar \frac{\partial}{\partial t} | \Psi(t) \rangle = \hat{H} | \Psi(t) \rangle",
            ),
            "mechanics": (
                r"\tau = I \alpha = r \times F \sin\theta",
                r"L = I \omega \implies \frac{dL}{dt} = \tau_{\text{ext}}",
            ),
            "electrical": (
                r"V(t) = L \frac{di}{dt} + R i(t) + \frac{1}{C} \int i(t) dt",
                r"Z_C = \frac{1}{j \omega C}, \quad Z_L = j \omega L",
            ),
            "chemistry": (
                r"k = A e^{-\frac{E_a}{R T}}",
                r"\ln\left(\frac{k_2}{k_1}\right) = -\frac{E_a}{R} \left(\frac{1}{T_2} - \frac{1}{T_1}\right)",
            ),
            "physics": (
                r"E^2 = (p c)^2 + (m_0 c^2)^2",
                r"\gamma = \frac{1}{\sqrt{1 - \frac{v^2}{c^2}}}",
            ),
            "math": (
                r"\sum_{n=1}^\infty \frac{1}{n^s} = \prod_p \frac{1}{1 - p^{-s}}",
                r"\zeta(2) = \frac{\pi^2}{6}",
            ),
            "ml": (
                r"\mathcal{L}_{\text{CE}} = -\sum_{c=1}^C y_c \log(\hat{y}_c)",
                r"\frac{\partial \mathcal{L}}{\partial W} = \delta \cdot x^T",
            ),
            "systems": (
                r"S(N) = \frac{1}{(1 - P) + \frac{P}{N}} \quad (\text{Amdahl})",
                r"S(N) = N + (1 - N) s \quad (\text{Gustafson})",
            ),
        }

        for subj, (prob, sol) in stem_samples.items():
            plan = {
                "title": f"Polymorphic Test Plan for {subj}",
                "subject": subj,
                "scenes": [
                    {
                        "scene_type": "fullscreen_text",
                        "spoken_text": f"This is an introductory overview for the {subj} domain.",
                        "display_text": f"{subj.upper()} OVERVIEW",
                    },
                    {
                        "scene_type": "comparison",
                        "spoken_text": f"Notice the contrast between the foundational and advanced formulation.",
                        "problem_label": "Foundation",
                        "problem_code": prob,
                        "solution_label": "Advanced",
                        "solution_code": sol,
                    },
                ],
            }
            is_valid, errors = validate_script_plan(plan)
            self.assertTrue(
                is_valid,
                f"Subject '{subj}' failed comparison validation with LaTeX: {errors}",
            )

    def test_function_graph_without_functions_passes_validation(self):
        """
        Verify that a function_graph scene with only scene_id, title, narration,
        and visual_type='function_graph' (no functions or curves key) passes validation cleanly,
        and auto-populates fallback functions for stage 4 choreographer.
        """
        plan = {
            "title": "Electrical Power Systems Masterclass",
            "subject": "electrical",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Hook Introduction",
                    "narration": "Mastering circuit network theorems thoroughly.",
                    "visual_type": "fullscreen_text",
                    "display_text": "ELECTRICAL MASTERCLASS",
                },
                {
                    "scene_id": 6,
                    "title": "Thévenin Maximum Power Transfer Curve",
                    "narration": "Load power reaches peak when load resistance equals Thévenin resistance.",
                    "visual_type": "function_graph",
                },
                {
                    "scene_id": 11,
                    "title": "Mastery Decision Matrix Summary",
                    "narration": "Here is the master matrix cheat sheet for circuits.",
                    "visual_type": "bento_grid",
                },
            ],
        }

        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(
            is_valid,
            f"Expected function_graph with omitted functions to pass validation, got errors: {errors}",
        )
        self.assertEqual(len(errors), 0)

        # Verify auto-population of fallback functions for choreographer
        graph_scene = plan["scenes"][1]
        self.assertIn("functions", graph_scene)
        self.assertGreaterEqual(len(graph_scene["functions"]), 1)
        self.assertEqual(graph_scene["functions"][0]["fn"], "x^2")

    def test_all_stem_scenes_without_subfields_pass_validation(self):
        """
        Verify that math_equation, physics_sim, chemistry_reaction, quantum_sim,
        mechanics_fbd, electrical_grid pass validation with only minimal fields
        (scene_id, title, narration, visual_type).
        """
        stem_types = [
            ("math_equation", "math", "steps"),
            ("physics_sim", "physics", "sim_type"),
            ("chemistry_reaction", "chemistry", "mode"),
            ("quantum_sim", "quantum_physics", "sub_mode"),
            ("mechanics_fbd", "mechanics", "sub_mode"),
            ("electrical_grid", "electrical", "sub_mode"),
        ]

        for v_type, subj, expected_auto_field in stem_types:
            plan = {
                "title": f"Minimal {v_type} Test",
                "subject": subj,
                "duration": 60,
                "scenes": [
                    {
                        "scene_id": 1,
                        "title": "Intro Hook",
                        "narration": f"Exploring fundamental principles of {subj}.",
                        "visual_type": "fullscreen_text",
                    },
                    {
                        "scene_id": 2,
                        "title": f"Core {v_type} demonstration",
                        "narration": f"Here is the core demonstration of {subj} principles.",
                        "visual_type": v_type,
                    },
                ],
            }
            is_valid, errors = validate_script_plan(plan)
            self.assertTrue(
                is_valid,
                f"Scene type '{v_type}' failed validation when subfields were omitted: {errors}",
            )
            self.assertIn(
                expected_auto_field,
                plan["scenes"][1],
                f"Expected auto-populated '{expected_auto_field}' in scene 2",
            )

    def test_four_word_hook_and_outro_pass_validation(self):
        """
        Verify that 4-word hook and outro sentences pass validation cleanly without errors.
        """
        plan = {
            "title": "Four Word Sentences Test",
            "subject": "electrical",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Hook",
                    "narration": "Four words hook sentence.",  # 4 words
                    "visual_type": "fullscreen_text",
                },
                {
                    "scene_id": 2,
                    "title": "Circuits",
                    "narration": "Here is a detailed explanation of circuit theorems.",  # 8 words
                    "visual_type": "electrical_grid",
                },
                {
                    "scene_id": 3,
                    "title": "Outro",
                    "narration": "Final four words outro.",  # 4 words
                    "visual_type": "bento_grid",
                },
            ],
        }
        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(
            is_valid,
            f"Expected 4-word hook/outro to pass validation, got errors: {errors}",
        )

    def test_banned_placeholder_tokens_fail_when_absent_from_source(self):
        """
        Verify that banned ML/generic placeholder tokens fail narrative validation
        when they are absent from the source document.
        """
        plan = {
            "title": "Acme EdgeCache SDK Release",
            "subject": "devtools",
            "source_text": "Acme EdgeCache provides global async streaming.",
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Hook",
                    "narration": "Welcome to the edge cache release.",
                    "visual_type": "fullscreen_text",
                },
                {
                    "scene_id": 2,
                    "title": "Architectures",
                    "narration": "Here are our core system benchmarks.",
                    "visual_type": "bento_grid",
                    "cards": [
                        {"title": "K-Means", "description": "Clustering algorithm"}
                    ]
                },
            ],
        }
        is_valid, errors = validate_script_plan(plan)
        self.assertFalse(is_valid)
        self.assertTrue(any("k-means" in err.lower() for err in errors))

    def test_banned_placeholder_tokens_pass_when_present_in_source(self):
        """
        Verify that ML tokens are permitted when the source document is legitimately
        about those algorithms.
        """
        plan = {
            "title": "Unsupervised Clustering Tutorial",
            "subject": "ml",
            "source_text": "In this guide we explore K-Means clustering and DBSCAN density analysis.",
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Hook",
                    "narration": "Discover the foundations of spatial clustering.",
                    "visual_type": "fullscreen_text",
                },
                {
                    "scene_id": 2,
                    "title": "Algorithms",
                    "narration": "Compare K-Means partitioning against density clustering.",
                    "visual_type": "bento_grid",
                    "cards": [
                        {"title": "K-Means", "description": "Centroid partitioning"}
                    ]
                },
            ],
        }
        is_valid, errors = validate_script_plan(plan)
        self.assertTrue(is_valid, f"Expected legitimate ML plan to pass, got: {errors}")

    def test_unsanitized_cli_syntax_in_narration_fails(self):
        """
        Verify that raw un-sanitized CLI syntax (@scope/pkg, --flags, literal 'at ... slash')
        fails narration validation.
        """
        plan = {
            "title": "CLI Setup",
            "subject": "code",
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Install",
                    "narration": "Run npm install at acme slash sdk at latest right now.",
                    "visual_type": "fullscreen_text",
                },
                {
                    "scene_id": 2,
                    "title": "Flag",
                    "narration": "Pass the --save-dev flag to finish.",
                    "visual_type": "fullscreen_text",
                },
            ],
        }
        is_valid, errors = validate_script_plan(plan)
        self.assertFalse(is_valid)
        self.assertTrue(any("cli flag" in err.lower() or "slash" in err.lower() for err in errors))


if __name__ == "__main__":
    unittest.main()


