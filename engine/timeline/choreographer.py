"""
Context-Aware AI Scene Choreographer (Stage 4 Timeline Enrichment).

Dynamically inspects topic domain, scene visual primitive, narration, and Whisper word
timestamps to enrich each scene in data.json with a high-craft `choreography` object:
  - Contextual theme and color palette injection (code_cyber, math_euler, physics_kinetic, warning_crimson, ml_amber)
  - Word-synchronized animation directives (step reveals, curve drawing, vector growth, projectile arcs, bento illumination, neural sweep)
  - Layout mode tagging (focused, split, stepped, hero, kinetic, bento, explorer, neural_split)
  - Strict non-empty content synthesis guarantees (Math, Graph, Physics, and ML scenes are NEVER empty)

Prime Directive: Strictly additive! Zero audio drift, no timestamp or word alignment mutations.
"""

import copy
import re
from typing import Any, Dict, List, Optional

try:
    from engine.timeline.beats import enforce_minimum_scene_durations
except ImportError:
    from timeline.beats import enforce_minimum_scene_durations

THEME_PALETTES = {
    "code_cyber": {
        "id": "code_cyber",
        "primary": "#58a6ff",
        "secondary": "#3fb950",
        "accent": "#ffd633",
        "background": "#161b22",
        "border": "rgba(88, 166, 255, 0.35)",
        "glow": "rgba(88, 166, 255, 0.16)",
        "badge_tag": "CODE",
    },
    "math_euler": {
        "id": "math_euler",
        "primary": "#79c0ff",
        "secondary": "#d2a8ff",
        "accent": "#56d364",
        "background": "#121d2f",
        "border": "rgba(121, 192, 255, 0.35)",
        "glow": "rgba(121, 192, 255, 0.18)",
        "badge_tag": "MATH",
    },
    "physics_kinetic": {
        "id": "physics_kinetic",
        "primary": "#ffa657",
        "secondary": "#7ee787",
        "accent": "#f0883e",
        "background": "#1c1917",
        "border": "rgba(255, 166, 87, 0.35)",
        "glow": "rgba(255, 166, 87, 0.18)",
        "badge_tag": "PHYSICS",
    },
    "warning_crimson": {
        "id": "warning_crimson",
        "primary": "#ff7b72",
        "secondary": "#f85149",
        "accent": "#ffa657",
        "background": "#2a0a12",
        "border": "rgba(255, 123, 114, 0.45)",
        "glow": "rgba(255, 123, 114, 0.18)",
        "badge_tag": "WARNING",
    },
    "ml_amber": {
        "id": "ml_amber",
        "primary": "#f59e0b",
        "secondary": "#10b981",
        "accent": "#6366f1",
        "background": "#0e131f",
        "border": "rgba(245, 158, 11, 0.35)",
        "glow": "rgba(245, 158, 11, 0.20)",
        "badge_tag": "ML & ALGORITHMS",
    },
    "chemistry_emerald": {
        "id": "chemistry_emerald",
        "primary": "#10b981",
        "secondary": "#38bdf8",
        "accent": "#ef4444",
        "background": "#070d14",
        "border": "rgba(16, 185, 129, 0.35)",
        "glow": "rgba(16, 185, 129, 0.20)",
        "badge_tag": "CHEMISTRY",
    },
    "quantum_violet": {
        "id": "quantum_violet",
        "primary": "#a855f7",
        "secondary": "#38bdf8",
        "accent": "#34d399",
        "background": "#090614",
        "border": "rgba(168, 85, 247, 0.35)",
        "glow": "rgba(168, 85, 247, 0.22)",
        "badge_tag": "QUANTUM PHYSICS",
    },
    "mechanics_industrial": {
        "id": "mechanics_industrial",
        "primary": "#f97316",
        "secondary": "#38bdf8",
        "accent": "#eab308",
        "background": "#111827",
        "border": "rgba(249, 115, 22, 0.35)",
        "glow": "rgba(249, 115, 22, 0.20)",
        "badge_tag": "ADVANCED MECHANICS",
    },
    "electrical_neon": {
        "id": "electrical_neon",
        "primary": "#00f0ff",
        "secondary": "#eab308",
        "accent": "#ef4444",
        "background": "#050b14",
        "border": "rgba(0, 240, 255, 0.35)",
        "glow": "rgba(0, 240, 255, 0.22)",
        "badge_tag": "SMART GRID & CIRCUITS",
    },
}

ML_PRIMITIVES = {"bento_grid", "algorithm_explorer", "neural_code_split"}
CHEMISTRY_PRIMITIVES = {"chemistry_reaction"}
QUANTUM_PRIMITIVES = {"quantum_sim"}
MECHANICS_PRIMITIVES = {"mechanics_fbd"}
ELECTRICAL_PRIMITIVES = {"electrical_grid"}

COMPARISON_FOOTERS = {
    "electrical": "KEY TAKEAWAY: NETWORK EQUIVALENCE & POWER FLOW — Linear network reduction simplifies multi-bus OPF solver complexity by 100x",
    "mechanics": "KEY TAKEAWAY: EQUILIBRIUM CONDITION — Resolving reaction moments eliminates structural collapse risks under peak loading",
    "quantum_physics": "KEY TAKEAWAY: COMMUTATION RELATION & UNCERTAINTY BOUND — Non-commuting operators dictate measurement precision and tunneling",
    "chemistry": "KEY TAKEAWAY: RATE LAW CONTRAST — Substrate hindrance determines whether concerted SN2 or carbocation SN1 dominates",
    "physics": "KEY TAKEAWAY: EQUILIBRIUM CONDITION — Net external force and energy conservation govern closed dynamical trajectories",
    "math": "KEY TAKEAWAY: Instantaneous derivative limits bridge discrete change with continuous accumulated area",
    "code": "KEY TAKEAWAY: ASYMPTOTIC COMPLEXITY ANALYSIS — Hash table indexing eliminates nested O(n²) bottlenecks in critical loops",
    "ml": "KEY TAKEAWAY: Density clustering partitions non-linear manifold geometry without spherical centroid assumptions",
    "systems": "KEY TAKEAWAY: Decoupled asynchronous architecture prevents cascading bottlenecks across microservices",
    "devtools": "KEY TAKEAWAY: v2 SDK reduces cold-start latency by 6x with 90% less code",
}

DOMAIN_MATH_STEPS = {
    "electrical": [
        {
            "formula": "\\sum_{i} P_{Gi} = P_{\\text{load}} + P_{\\text{loss}}",
            "explanation": "Active Power Balance Constraint",
        },
        {
            "formula": "\\frac{\\partial C_i}{\\partial P_{Gi}} = \\lambda \\quad \\text{subject to } |S_{ij}| \\le S_{ij,\\max}",
            "explanation": "Thermal Line Limit & Economic Dispatch",
        },
    ],
    "mechanics": [
        {
            "formula": "\\sum F_x = 0, \\quad \\sum F_y = R_A + R_B - \\sum W_i = 0",
            "explanation": "Translational Static Equilibrium",
        },
        {
            "formula": "\\sum \\tau_A = R_B \\cdot L - \\sum (W_i \\cdot x_i) = 0 \\implies M(x) = \\int V(x) dx",
            "explanation": "Rotational Moment Balance",
        },
    ],
    "quantum_physics": [
        {
            "formula": "\\hat{H}\\Psi = E\\Psi \\implies \\kappa = \\frac{\\sqrt{2m(V_0 - E)}}{\\hbar}",
            "explanation": "Wavefunction Attenuation Constant",
        },
        {
            "formula": "T \\approx e^{-2\\kappa L}, \\quad \\sigma_x \\sigma_p \\ge \\frac{\\hbar}{2}",
            "explanation": "Barrier Transmission & Phase-Space Bound",
        },
    ],
    "chemistry": [
        {
            "formula": "\\text{Rate}_{S_N2} = k[\\text{R-X}][\\text{Nu}^-], \\quad \\text{Rate}_{S_N1} = k[\\text{R-X}]",
            "explanation": "Kinetic Order Law",
        },
        {
            "formula": "k = A e^{-E_a / RT}, \\quad \\Delta G^\\ddagger = \\Delta H^\\ddagger - T\\Delta S^\\ddagger",
            "explanation": "Eyring-Arrhenius Activation Barrier",
        },
    ],
    "physics": [
        {
            "formula": "\\sum \\vec{F} = \\frac{d\\vec{p}}{dt} = m\\vec{a}",
            "explanation": "Newton's Second Law of Motion",
        },
        {
            "formula": "\\Delta E_{\\text{mech}} = W_{\\text{nc}} = \\int \\vec{F}_{\\text{ext}} \\cdot d\\vec{r}",
            "explanation": "Work-Energy Theorem",
        },
    ],
    "ml": [
        {
            "formula": "\\min_\\theta \\mathcal{L}(\\theta) = \\frac{1}{N} \\sum_{i=1}^N \\ell(f_\\theta(x_i), y_i)",
            "explanation": "Empirical Risk Minimization Objective",
        },
        {
            "formula": "\\theta_{t+1} = \\theta_t - \\eta \\nabla_\\theta \\mathcal{L}(\\theta_t)",
            "explanation": "Gradient Descent Optimization Step",
        },
    ],
    "code": [
        {
            "formula": "T(n) = a \\cdot T(n/b) + f(n)",
            "explanation": "Divide-and-Conquer Recurrence Relation",
        },
        {
            "formula": "T(n) = \\Theta(n^{\\log_b a}) \\quad \\text{for } f(n) = O(n^{\\log_b a - \\epsilon})",
            "explanation": "Master Theorem Asymptotic Runtime",
        },
    ],
    "math": [
        {
            "formula": "\\frac{df}{dx} = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}",
            "explanation": "First-Principles Derivative Limit",
        },
        {
            "formula": "\\int_a^b f'(x)\\,dx = f(b) - f(a)",
            "explanation": "Fundamental Theorem of Calculus",
        },
    ],
}

DOMAIN_MATH_INTUITION = {
    "electrical": {
        "text": "Lagrangian optimization dispatches lowest-cost generators while clamping branch currents below thermal sag thresholds.",
        "footer_label": "Optimal Power Flow (OPF)",
        "status": "CONVERGED",
    },
    "mechanics": {
        "text": "Internal shear and bending moments peak where reaction forces balance concentrated structural loads.",
        "footer_label": "Static Determinacy",
        "status": "EQUILIBRIUM",
    },
    "quantum_physics": {
        "text": "Non-zero probability amplitude inside classically forbidden barriers enables quantum tunneling.",
        "footer_label": "Unitary Evolution",
        "status": "PROVEN",
    },
    "chemistry": {
        "text": "Activation energy height dictates reaction rate; steric hindrance raises the concerted transition state barrier.",
        "footer_label": "Eyring Transition State",
        "status": "VERIFIED",
    },
    "physics": {
        "text": "Net external force dictates momentum transfer; conserved quantities remain invariant under continuous symmetry.",
        "footer_label": "Dynamical Conservation",
        "status": "CONSERVED",
    },
    "ml": {
        "text": "Backpropagation computes directional gradients along the loss surface toward local empirical risk minima.",
        "footer_label": "Optimization Convergence",
        "status": "OPTIMAL",
    },
    "code": {
        "text": "Logarithmic branch partitioning bounds worst-case recursive call depth within deterministic stack limits.",
        "footer_label": "Asymptotic Complexity",
        "status": "BOUNDED",
    },
    "math": {
        "text": "Infinitesimal differential limits bridge localized rates of change with global accumulated continuous area.",
        "footer_label": "Analytical Rigor",
        "status": "Q.E.D.",
    },
}


def resolve_domain(timed_scenes: List[Dict[str, Any]], domain_hint: str = "auto") -> str:
    """Resolves active domain from hint or scene primitives."""
    if domain_hint in {"code", "math", "physics", "systems", "ml", "chemistry", "quantum_physics", "mechanics", "electrical", "devtools"}:
        return domain_hint

    has_quantum = any(
        s.get("scene_type") in QUANTUM_PRIMITIVES or
        s.get("visual_type") in QUANTUM_PRIMITIVES
        for s in timed_scenes
    )
    if has_quantum:
        return "quantum_physics"

    has_mechanics = any(
        s.get("scene_type") in MECHANICS_PRIMITIVES or
        s.get("visual_type") in MECHANICS_PRIMITIVES
        for s in timed_scenes
    )
    if has_mechanics:
        return "mechanics"

    has_electrical = any(
        s.get("scene_type") in ELECTRICAL_PRIMITIVES or
        s.get("visual_type") in ELECTRICAL_PRIMITIVES
        for s in timed_scenes
    )
    if has_electrical:
        return "electrical"

    has_chem = any(
        s.get("scene_type") in CHEMISTRY_PRIMITIVES or
        s.get("visual_type") in CHEMISTRY_PRIMITIVES
        for s in timed_scenes
    )
    if has_chem:
        return "chemistry"

    has_ml = any(
        s.get("scene_type") in ML_PRIMITIVES or
        s.get("visual_type") in ML_PRIMITIVES
        for s in timed_scenes
    )
    if has_ml:
        return "ml"

    has_math = any(
        s.get("scene_type") in {"math_equation", "function_graph"} or
        s.get("visual_type") in {"math_equation", "function_graph"}
        for s in timed_scenes
    )
    if has_math:
        return "math"

    has_physics = any(
        s.get("scene_type") == "physics_sim" or s.get("visual_type") == "physics_sim"
        for s in timed_scenes
    )
    if has_physics:
        return "physics"

    return "code"


def assign_theme_id(scene: Dict[str, Any], domain: str) -> str:
    """Selects the best matching theme palette for an individual scene."""
    badge = scene.get("badge") or {}
    badge_type = badge.get("type")

    if badge_type in {"warning", "danger", "error"}:
        return "warning_crimson"

    scene_type = scene.get("scene_type") or scene.get("visual_type", "")

    if scene_type in QUANTUM_PRIMITIVES or domain == "quantum_physics":
        return "quantum_violet"
    if scene_type in MECHANICS_PRIMITIVES or domain == "mechanics":
        return "mechanics_industrial"
    if scene_type in ELECTRICAL_PRIMITIVES or domain == "electrical":
        return "electrical_neon"
    if scene_type in CHEMISTRY_PRIMITIVES or domain == "chemistry":
        return "chemistry_emerald"
    if scene_type in ML_PRIMITIVES or domain == "ml":
        return "ml_amber"
    if scene_type in {"math_equation", "function_graph"} or domain == "math":
        return "math_euler"
    if scene_type == "physics_sim" or domain == "physics":
        return "physics_kinetic"

    return "code_cyber"


def synthesize_math_steps(scene: Dict[str, Any], domain: str = "math") -> List[Dict[str, Any]]:
    """Synthesizes rich mathematical derivation steps if the LLM omits them or provides generic placeholders."""
    raw_steps = scene.get("steps") or scene.get("equations") or []
    is_generic = False
    if raw_steps and isinstance(raw_steps, list) and len(raw_steps) > 0:
        for s in raw_steps:
            formula = s if isinstance(s, str) else (s.get("formula") or s.get("latex") or "")
            if formula.strip() in {"f(x) = y", "y = f(x)", "f(x)=y", "y=f(x)"}:
                is_generic = True
                break
        if not is_generic:
            return raw_steps

    text = f"{scene.get('spoken_text', '')} {scene.get('narration', '')} {scene.get('title', '')} {scene.get('code_snippet', '')} {scene.get('display_text', '')}".lower()
    norm_domain = (domain or "math").lower()

    # Specialized STEM domains always take precedence
    if norm_domain in DOMAIN_MATH_STEPS and norm_domain not in {"math", "physics"}:
        return DOMAIN_MATH_STEPS[norm_domain]

    # Only return Euler's identity if Euler is explicitly mentioned in the text
    if any(k in text for k in ["euler", "complex analysis", "identity"]):
        return [
            {"formula": "e^{i\\theta} = \\cos(\\theta) + i\\sin(\\theta)", "explanation": "Euler's Formula on the complex unit circle"},
            {"formula": "\\theta = \\pi \\implies e^{i\\pi} = -1 + 0i", "explanation": "Evaluate at half-circle rotation"},
            {"formula": "e^{i\\pi} + 1 = 0", "explanation": "Euler's Identity combining fundamental constants"},
        ]
    elif any(k in text for k in ["pythagor", "triangle", "hypotenuse"]):
        return [
            {"formula": "a^2 + b^2 = c^2", "explanation": "Pythagorean Theorem on right Euclidean triangles"},
            {"formula": "c = \\sqrt{a^2 + b^2}", "explanation": "Euclidean metric distance computation"},
        ]
    elif any(k in text for k in ["derivative", "calculus", "gradient"]):
        return [
            {"formula": "\\frac{df}{dx} = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}", "explanation": "First-principles limit definition"},
            {"formula": "\\frac{d}{dx}[x^n] = n \\cdot x^{n-1}", "explanation": "Power Rule differentiation"},
        ]
    elif any(k in text for k in ["integral", "area"]):
        return [
            {"formula": "\\int_a^b f(x) dx = F(b) - F(a)", "explanation": "Fundamental Theorem of Calculus"},
            {"formula": "F'(x) = f(x)", "explanation": "Antiderivative relationship"},
        ]

    # Return domain matched math steps from the domain map
    return DOMAIN_MATH_STEPS.get(norm_domain, DOMAIN_MATH_STEPS["math"])


def synthesize_math_intuition(scene: Dict[str, Any], domain: str = "math") -> Dict[str, Any]:
    """Synthesizes domain-specific mathematical intuition and takeaway card data."""
    raw_intuition = scene.get("intuition")
    if isinstance(raw_intuition, dict) and raw_intuition.get("text"):
        return raw_intuition
    if isinstance(raw_intuition, str) and len(raw_intuition.strip()) > 10:
        return {
            "text": raw_intuition.strip(),
            "footer_label": "Mathematical Formulation",
            "status": "PROVEN",
        }

    text = f"{scene.get('spoken_text', '')} {scene.get('narration', '')} {scene.get('title', '')}".lower()
    norm_domain = (domain or "math").lower()

    if any(k in text for k in ["euler", "complex analysis", "identity"]):
        return {
            "text": "Multiplication by imaginary unit i represents a pure 90° rotation in the complex plane. Exponentiating by iπ rotates directly to -1.",
            "footer_label": "Constants Linked: e, i, π, 1, 0",
            "status": "Q.E.D.",
        }

    return DOMAIN_MATH_INTUITION.get(norm_domain, DOMAIN_MATH_INTUITION["math"])


def synthesize_function_graph(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Synthesizes function graph curve specifications if omitted."""
    raw_functions = scene.get("functions") or scene.get("curves") or []
    if raw_functions and isinstance(raw_functions, list) and len(raw_functions) > 0:
        return raw_functions

    text = f"{scene.get('spoken_text', '')} {scene.get('title', '')}".lower()
    if any(k in text for k in ["sin", "wave", "harmonic"]):
        return [{"fn": "sin(x)", "label": "f(x) = sin(x)"}]
    elif any(k in text for k in ["gauss", "normal", "bell"]):
        return [{"fn": "gaussian", "label": "f(x) = exp(-x^2 / 2)"}]
    elif any(k in text for k in ["cubic", "x^3"]):
        return [{"fn": "cubic", "label": "f(x) = x^3 / 6"}]

    return [{"fn": "x^2", "label": "f(x) = x^2 / 3"}]


def detect_physics_mode(scene: Dict[str, Any]) -> str:
    """Detects physics simulation mode (projectile vs wave vs forces) from narration/context."""
    explicit_mode = scene.get("sim_type")
    if explicit_mode in {"projectile", "wave", "forces"}:
        return explicit_mode

    text = f"{scene.get('spoken_text', '')} {scene.get('title', '')} {scene.get('display_text', '')}".lower()

    if any(k in text for k in [
        "projectile", "trajectory", "parabola", "parabolic", "launch",
        "horizontal", "vertical velocity", "v_x", "v_y", "vx", "vy",
        "cannon", "ball flight", "flight time", "angle", "elevation"
    ]):
        return "projectile"

    if any(k in text for k in [
        "wave", "oscillation", "harmonic", "frequency", "sine", "pendulum",
        "amplitude", "spring", "resonance", "vibration", "wavelength"
    ]):
        return "wave"

    return "forces"


def synthesize_physics_payload(scene: Dict[str, Any], sim_type: str) -> Dict[str, Any]:
    """Ensures rich physics simulation payloads are populated for the detected mode."""
    payload = {}
    if sim_type == "projectile":
        payload["trajectory"] = scene.get("trajectory") or {"v0": 24, "angle": 45, "g": 9.8}
        payload["v_x"] = scene.get("v_x", 18.0)
        payload["v_y"] = scene.get("v_y", 14.0)
    elif sim_type == "wave":
        payload["wave"] = scene.get("wave") or {"amplitude": 35, "frequency": 1.2, "wavelength": 140}
    else:  # forces
        payload["forces"] = scene.get("forces") or [
            {"name": "Fg", "magnitude": "98N", "direction": 270},
            {"name": "FN", "magnitude": "98N", "direction": 90},
            {"name": "Fapp", "magnitude": "40N", "direction": 0},
            {"name": "Ff", "magnitude": "40N", "direction": 180},
        ]
        payload["mass"] = scene.get("mass") or "10kg"
    return payload


def synthesize_domain_bento_data(scene: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """
    Synthesizes domain-specific 4-card bento matrices, headers, and subtitles for EVERY subject,
    guaranteeing that non-ML subjects never output 'UNSUPERVISED ML ALGORITHMS'.
    """
    domain = (domain or "code").lower()
    if domain == "electrical":
        return {
            "domain": "electrical",
            "section_title": scene.get("section_title") or "POWER SYSTEMS & NETWORK THEOREMS",
            "subtitle": scene.get("subtitle") or "GRID & CIRCUIT MASTER MATRIX",
            "cards": scene.get("cards") or [
                {
                    "title": "KCL & KVL Laws",
                    "algo_type": "kcl_kvl",
                    "category": "CONSERVATION",
                    "description": "Nodal charge balance ΣI = 0 • Closed loop drop ΣV = 0",
                },
                {
                    "title": "Thévenin & Norton",
                    "algo_type": "thevenin_norton",
                    "category": "NETWORK REDUCTION",
                    "description": "V_th ideal source with R_th • Dual Norton I_n = V_oc/R_th",
                },
                {
                    "title": "Economic Dispatch",
                    "algo_type": "economic_dispatch",
                    "category": "OPTIMIZATION",
                    "description": "Equal incremental cost λ • Minimum fuel cost $/MWh curve",
                },
                {
                    "title": "Optimal Power Flow",
                    "algo_type": "opf_grid",
                    "category": "GRID STABILITY",
                    "description": "Bus voltage profile • Transmission corridor thermal limit",
                },
            ],
        }
    elif domain == "mechanics":
        return {
            "domain": "mechanics",
            "section_title": scene.get("section_title") or "STRUCTURAL MECHANICS & STATICS",
            "subtitle": scene.get("subtitle") or "EQUILIBRIUM & LOAD MATRIX",
            "cards": scene.get("cards") or [
                {
                    "title": "Force Equilibrium",
                    "algo_type": "force_equilibrium",
                    "category": "FORCE BALANCE",
                    "description": "Net vertical ΣF_y = 0 • Net horizontal ΣF_x = 0",
                },
                {
                    "title": "Torque Balance",
                    "algo_type": "torque_balance",
                    "category": "ROTATIONAL STATICS",
                    "description": "Zero net moment Στ = 0 about pin support hinge",
                },
                {
                    "title": "Shear & Bending",
                    "algo_type": "shear_bending",
                    "category": "INTERNAL FORCES",
                    "description": "Shear step V(x) • Parabolic moment M(x) beam profile",
                },
                {
                    "title": "Axle Load Transfer",
                    "algo_type": "axle_transfer",
                    "category": "DYNAMIC SQUAT",
                    "description": "Center of mass load shift ΔW = (h/L)·m·a acceleration",
                },
            ],
        }
    elif domain == "quantum_physics":
        return {
            "domain": "quantum_physics",
            "section_title": scene.get("section_title") or "QUANTUM MECHANICS • WAVE DYNAMICS",
            "subtitle": scene.get("subtitle") or "QUANTUM OPERATOR & STATE MATRIX",
            "cards": scene.get("cards") or [
                {
                    "title": "Schrödinger Evolution",
                    "algo_type": "schrodinger",
                    "category": "WAVE EQUATION",
                    "description": "Unitary wavepacket propagation iℏ∂Ψ/∂t = ĤΨ",
                },
                {
                    "title": "Quantum Tunneling",
                    "algo_type": "tunneling",
                    "category": "BARRIER DYNAMICS",
                    "description": "Evanescent decay T = exp(-2κL) barrier penetration",
                },
                {
                    "title": "Heisenberg Uncertainty",
                    "algo_type": "heisenberg",
                    "category": "OBSERVABLES",
                    "description": "Canonical commutator [x̂, p̂] = iℏ • Δx·Δp ≥ ℏ/2",
                },
                {
                    "title": "Dirac Spinors & Orbitals",
                    "algo_type": "dirac_orbitals",
                    "category": "RELATIVISTIC QM",
                    "description": "4-component bi-spinor • Hydrogen spatial probability density",
                },
            ],
        }
    elif domain == "chemistry":
        return {
            "domain": "chemistry",
            "section_title": scene.get("section_title") or "SN1 VS SN2 DECISION MATRIX",
            "subtitle": scene.get("subtitle") or "REACTION MECHANISM MATRIX",
            "cards": scene.get("cards") or [
                {
                    "title": "SUBSTRATE",
                    "algo_type": "substrate",
                    "category": "BULKINESS",
                    "description": "SN2 prefers Methyl/1° • SN1 prefers bulky 3°",
                },
                {
                    "title": "NUCLEOPHILE",
                    "algo_type": "nucleophile",
                    "category": "STRENGTH",
                    "description": "SN2 requires strong Nu⁻ • SN1 works with weak neutral Nu",
                },
                {
                    "title": "SOLVENT",
                    "algo_type": "solvent",
                    "category": "POLARITY",
                    "description": "SN2 needs Polar Aprotic • SN1 needs Polar Protic (ionizing)",
                },
                {
                    "title": "STEREOCHEMISTRY",
                    "algo_type": "stereochem",
                    "category": "CHIRALITY",
                    "description": "SN2 gives 100% Inversion • SN1 yields 50/50 Racemic Mix",
                },
            ],
        }
    elif domain == "physics":
        return {
            "domain": "physics",
            "section_title": scene.get("section_title") or "CLASSICAL PHYSICS & KINEMATICS",
            "subtitle": scene.get("subtitle") or "DYNAMICS & CONSERVATION MATRIX",
            "cards": scene.get("cards") or [
                {
                    "title": "Newton's Laws",
                    "algo_type": "newton",
                    "category": "DYNAMICS",
                    "description": "Net force F_net = m·a • Action equals reaction",
                },
                {
                    "title": "Work & Energy",
                    "algo_type": "work_energy",
                    "category": "CONSERVATION",
                    "description": "Mechanical energy conservation E = K + U = constant",
                },
                {
                    "title": "Linear Momentum",
                    "algo_type": "momentum",
                    "category": "COLLISIONS",
                    "description": "Total momentum conservation Σp = const in isolated systems",
                },
                {
                    "title": "Harmonic Oscillation",
                    "algo_type": "harmonic",
                    "category": "PERIODIC MOTION",
                    "description": "Restoring force F = -k·x • Period T = 2π√(m/k)",
                },
            ],
        }
    elif domain == "math":
        return {
            "domain": "math",
            "section_title": scene.get("section_title") or "CALCULUS & ANALYTIC GEOMETRY",
            "subtitle": scene.get("subtitle") or "DERIVATIVES & INTEGRALS MATRIX",
            "cards": scene.get("cards") or [
                {
                    "title": "Limit Definition",
                    "algo_type": "limit",
                    "category": "FIRST PRINCIPLES",
                    "description": "df/dx = lim_{h→0} [f(x+h) - f(x)] / h instantaneous rate",
                },
                {
                    "title": "Fundamental Theorem",
                    "algo_type": "fundamental_theorem",
                    "category": "INTEGRATION",
                    "description": "∫ f'(x) dx = f(b) - f(a) area accumulation theorem",
                },
                {
                    "title": "Taylor Series",
                    "algo_type": "taylor",
                    "category": "POLYNOMIAL APPROX",
                    "description": "Expansion f(x) = Σ f^(n)(a)/n! (x-a)^n around point a",
                },
                {
                    "title": "Extrema & Curvature",
                    "algo_type": "curvature",
                    "category": "OPTIMIZATION",
                    "description": "Stationary points f'(x) = 0 • Concavity inflection f''(x) = 0",
                },
            ],
        }
    elif domain == "code":
        return {
            "domain": "code",
            "section_title": scene.get("section_title") or "SOFTWARE ARCHITECTURE & ALGORITHMS",
            "subtitle": scene.get("subtitle") or "COMPLEXITY & DESIGN MATRIX",
            "cards": scene.get("cards") or [
                {
                    "title": "Hash Tables & Sets",
                    "algo_type": "hash_table",
                    "category": "FAST LOOKUP",
                    "description": "O(1) average lookup • Immutable hash keys prevent collision",
                },
                {
                    "title": "Stream Generators",
                    "algo_type": "generator",
                    "category": "MEMORY EFFICIENCY",
                    "description": "O(1) memory yield • Lazy iterator streaming on demand",
                },
                {
                    "title": "Binary Heaps",
                    "algo_type": "heap",
                    "category": "PRIORITY QUEUES",
                    "description": "O(log n) insert and pop • Optimal priority scheduling",
                },
                {
                    "title": "Dynamic Programming",
                    "algo_type": "dp",
                    "category": "OPTIMIZATION",
                    "description": "Memoized overlapping subproblems • Optimal substructure",
                },
            ],
        }
    else:  # ml (default)
        return {
            "domain": "ml",
            "section_title": scene.get("section_title") or "MACHINE LEARNING ARCHITECTURES",
            "subtitle": scene.get("subtitle") or "UNSUPERVISED ML ALGORITHMS",
            "cards": scene.get("cards") or synthesize_ml_bento_cards(scene),
        }


def synthesize_domain_graph_data(scene: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """
    Synthesizes domain-specific 2D graph payloads, curves, labels, and telemetry cards
    for EVERY subject, ensuring non-calculus subjects never render calculus f(x) = x^2 / 4.
    """
    domain = (domain or "math").lower()
    if domain == "electrical":
        return {
            "domain": "electrical",
            "header": "POWER SYSTEMS • LOAD & DISPATCH CURVES",
            "title": scene.get("title") or "Maximum Power Transfer & Marginal Cost",
            "curve_type": "electrical_power_transfer",
            "curves": [
                {"fn": "power_transfer", "label": "P_L(R_L) = V_th²·R_L / (R_th + R_L)²", "color": "#00f0ff"},
                {"fn": "marginal_cost", "label": "Marginal Cost λ = dC/dP ($/MWh)", "color": "#eab308"},
            ],
            "x_label": "Load Resistance R_L (Ω) →",
            "y_label": "Delivered Power P_L (W) ↑",
            "critical_point": "Peak Power at R_L = R_th (6.0 Ω)",
            "breakdown": {
                "title": "MAXIMUM POWER TRANSFER THEOREM",
                "left_label": "MATCHED LOAD POWER",
                "left_value": "P_max = V_th² / (4·R_th)",
                "right_label": "THEORETICAL EFFICIENCY",
                "right_value": "η = 50% at Peak Transfer",
                "footer": "R_L = R_th ensures maximum power delivery across high-voltage corridors",
                "tag": "MAX EFFICIENCY: R_L = R_th",
            },
        }
    elif domain == "mechanics":
        return {
            "domain": "mechanics",
            "header": "STRUCTURAL ANALYSIS • INTERNAL FORCES",
            "title": scene.get("title") or "Shear Force (V) & Bending Moment (M) Diagram",
            "curve_type": "mechanics_shear_moment",
            "curves": [
                {"fn": "shear_diagram", "label": "Shear Force V(x) Step Function", "color": "#f97316"},
                {"fn": "moment_diagram", "label": "Bending Moment M(x) Parabola", "color": "#38bdf8"},
            ],
            "x_label": "Beam Position x (m) →",
            "y_label": "Shear V (kN) / Moment M (kN·m) ↑",
            "critical_point": "Max Moment M_max at V(x) = 0",
            "breakdown": {
                "title": "INTERNAL EQUILIBRIUM & MOMENT EXTREMA",
                "left_label": "DIFFERENTIAL RELATION",
                "left_value": "dM/dx = V(x) (Shear slope)",
                "right_label": "MAXIMUM BENDING MOMENT",
                "right_value": "M_max = W·L / 4 at Midspan",
                "footer": "Zero shear crossing V(x)=0 strictly pinpoints maximum bending moment",
                "tag": "CRITICAL MOMENT AT V(x) = 0",
            },
        }
    elif domain == "quantum_physics":
        return {
            "domain": "quantum_physics",
            "header": "QUANTUM WAVE MECHANICS • PROBABILITY DENSITY",
            "title": scene.get("title") or "Barrier Penetration & Uncertainty Envelope",
            "curve_type": "quantum_wave_barrier",
            "curves": [
                {"fn": "wavefunction_density", "label": "|Ψ(x)|² Probability Density", "color": "#a855f7"},
                {"fn": "barrier_potential", "label": "Finite Potential Barrier V₀", "color": "#ef4444"},
            ],
            "x_label": "Position x (nm) →",
            "y_label": "Probability Density |Ψ(x)|² ↑",
            "critical_point": "Evanescent Decay Inside Barrier",
            "breakdown": {
                "title": "TUNNELING TRANSMISSION & EVANESCENT PROBABILITY",
                "left_label": "TRANSMISSION COEFFICIENT",
                "left_value": "T ≈ 16(E/V₀)(1 - E/V₀)e^(-2κL)",
                "right_label": "DECAY CONSTANT",
                "right_value": "κ = √(2m(V₀ - E)) / ℏ",
                "footer": "Wavefunction does not vanish at boundary; decays exponentially through barrier",
                "tag": "TUNNELING: T > 0 FOR E < V₀",
            },
        }
    elif domain == "chemistry":
        return {
            "domain": "chemistry",
            "header": "REACTION COORDINATE & THERMODYNAMICS",
            "title": scene.get("title") or "Reaction Coordinate Energy Profile",
            "curve_type": "chemistry_reaction_energy",
            "curves": [
                {"fn": "sn2_curve", "label": "SN2: 1-Step Concerted [‡]", "color": "#38bdf8"},
                {"fn": "sn1_curve", "label": "SN1: 2-Step Carbocation C⁺", "color": "#f59e0b"},
            ],
            "x_label": "Reaction Coordinate →",
            "y_label": "Potential Energy (ΔG) ↑",
            "critical_point": "Transition State [Nu···C···X]‡",
            "breakdown": {
                "title": "ACTIVATION BARRIERS & REACTION KINETICS",
                "left_label": "CONCERTED ACTIVATION",
                "left_value": "ΔG‡_SN2 = 75 kJ/mol",
                "right_label": "IONIZATION BARRIER",
                "right_value": "ΔG‡_SN1 = 88 kJ/mol (RDS)",
                "footer": "Single peak concerted flip contrasts against two-peak carbocation intermediate",
                "tag": "WALDEN INVERSION vs RACEMIC",
            },
        }
    else:  # math / physics / ml / code
        return {
            "domain": domain,
            "header": "CALCULUS & ANALYTIC GEOMETRY",
            "title": scene.get("title") or "2D Function Graph & Extremum Analysis",
            "curve_type": "analytic_function",
            "curves": synthesize_function_graph(scene),
            "x_label": "x →",
            "y_label": "f(x) ↑",
            "critical_point": "Critical Point (0, 0): f'(x) = 0",
            "breakdown": {
                "title": "FIRST DERIVATIVE & CRITICAL EXTREMA",
                "left_label": "FIRST DERIVATIVE f'(x)",
                "left_value": "f'(x) = 0.80x = 0",
                "right_label": "SECOND DERIVATIVE TEST",
                "right_value": "f''(x) = 0.80 > 0 (Minimum)",
                "footer": "Domain: (-∞, +∞) • Range: [0, +∞)",
                "tag": "GLOBAL MINIMUM",
            },
        }


def synthesize_ml_bento_cards(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Synthesizes high-retention ML bento cards if omitted."""
    raw_cards = scene.get("cards")
    if raw_cards and isinstance(raw_cards, list) and len(raw_cards) >= 2:
        return raw_cards

    return [
        {
            "title": "K-Means",
            "algo_type": "kmeans",
            "category": "CLUSTERING",
            "description": "Centroid-based iterative partitioning into k clusters",
        },
        {
            "title": "DBSCAN",
            "algo_type": "dbscan",
            "category": "CLUSTERING",
            "description": "Density-based spatial clustering robust to noise outliers",
        },
        {
            "title": "PCA",
            "algo_type": "pca",
            "category": "DIMENSIONALITY REDUCTION",
            "description": "Orthogonal linear projection maximizing variance",
        },
        {
            "title": "t-SNE",
            "algo_type": "tsne",
            "category": "DIMENSIONALITY REDUCTION",
            "description": "Non-linear manifold embedding for high-dimensional visualization",
        },
    ]


def synthesize_algorithm_explorer(scene: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesizes deep-dive algorithm explorer payload if omitted."""
    return {
        "algorithm": scene.get("algorithm") or "dbscan",
        "parameters": scene.get("parameters") or {
            "epsilon": "0.4 radius",
            "min_points": "4 samples",
            "metric": "Euclidean",
        },
        "point_types": scene.get("point_types") or {
            "core": "Density reachable (>= min_points)",
            "border": "Within epsilon boundary",
            "noise": "Isolated outlier point (X)",
        },
        "concept_strip": scene.get("concept_strip") or [
            "OVERVIEW", "DBSCAN", "K-MEANS", "PCA", "HIERARCHICAL"
        ],
    }


def synthesize_neural_code_split(scene: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesizes neural network visualizer + code split payload if omitted."""
    default_code = (
        "def forward(x, W1, b1, W2, b2):\n"
        "    z1 = x @ W1 + b1\n"
        "    a1 = np.maximum(0, z1)  # ReLU\n"
        "    z2 = a1 @ W2 + b2\n"
        "    return softmax(z2)\n\n"
        "def backward(x, y, probs, a1, W2):\n"
        "    dz2 = probs - y  # Cross-Entropy Grad\n"
        "    dW2 = a1.T @ dz2\n"
        "    da1 = dz2 @ W2.T\n"
        "    dz1 = da1 * (a1 > 0)\n"
        "    return dW2, dz1"
    )
    return {
        "model_name": scene.get("model_name") or "Neural Network",
        "subtitle": scene.get("subtitle") or "FROM SCRATCH",
        "layers": scene.get("layers") or [8, 16, 10],
        "code_snippet": scene.get("code_snippet") or default_code,
    }


def detect_chemistry_mode(scene: Dict[str, Any]) -> str:
    """Detects organic chemistry reaction mode and sub_mode from scene properties or narration keywords."""
    explicit = scene.get("sub_mode") or scene.get("mode") or scene.get("reaction_type") or scene.get("chemistry_mode")
    if explicit in {
        "sn2_concerted", "steric_blockade", "sn1_ionization", "sn1_racemic",
        "sn2_substitution", "sn1_carbocation", "addition_alkene", "redox_combustion", "acid_base"
    }:
        return explicit

    text = f"{scene.get('spoken_text', '')} {scene.get('title', '')} {scene.get('display_text', '')}".lower()
    if any(k in text for k in ["steric", "bulky", "hindrance", "barrier", "blocked", "bounce", "methyl groups"]):
        return "steric_blockade"
    elif any(k in text for k in ["racemic", "both sides", "top and bottom", "50%", "dual attack", "enantiomer", "retention"]):
        return "sn1_racemic"
    elif any(k in text for k in ["ionization", "cleavage", "depart", "heterolytic", "step 1", "leaving group leaves"]):
        return "sn1_ionization"
    elif any(k in text for k in ["carbocation", "solvolysis"]):
        return "sn1_carbocation"
    elif any(k in text for k in ["alkene", "double bond", "markovnikov", "addition", "pi bond"]):
        return "addition_alkene"
    elif any(k in text for k in ["acid", "base", "proton", "redox", "combustion"]):
        return "redox_combustion"
    elif any(k in text for k in ["nucleophile", "alkyl halide", "sn2"]):
        return "sn2_substitution"
    elif any(k in text for k in ["backside", "walden", "180", "concerted"]):
        return "sn2_concerted"
    return "sn2_concerted"


def synthesize_chemistry_payload(scene: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """Synthesizes rich organic chemistry reaction payload based on sub_mode."""
    norm_mode = (mode or "").lower()
    text = f"{scene.get('spoken_text', '')} {scene.get('title', '')} {scene.get('display_text', '')}".lower()
    heat_applied = any(k in text for k in ["heat", "temperature", "delta", "thermal", "boiling", "warm", "355", "exothermic", "ionization"]) or scene.get("heat_applied", False)

    if norm_mode in {"steric_blockade", "steric_hindrance"}:
        return {
            "reaction_name": scene.get("reaction_name") or "Steric Hindrance Blockade",
            "mode": "steric_blockade",
            "sub_mode": "steric_blockade",
            "thermodynamic_badge": scene.get("thermodynamic_badge") or "ATTACK BLOCKED",
            "heat_applied": heat_applied,
            "temperature_kelvin": scene.get("temperature_kelvin") or 298,
            "reagents": scene.get("reagents") or "NaOH • (CH3)3C-Br (Tertiary)",
            "rate_law": scene.get("rate_law") or "Rate ≈ 0 (High Steric Barrier)",
            "stereochemistry": "No Inversion (Substrate Intact)",
            "energy_profile": scene.get("energy_profile") or {
                "activation_energy": 120,
                "delta_g": 0,
                "transition_state": "Steric Shield Repulsion",
                "num_barriers": 1,
            },
        }
    elif norm_mode in {"sn1_racemic", "racemic_mixture"}:
        return {
            "reaction_name": scene.get("reaction_name") or "SN1 Dual-Face Racemic Attack",
            "mode": "sn1_racemic",
            "sub_mode": "sn1_racemic",
            "thermodynamic_badge": scene.get("thermodynamic_badge") or "RACEMIC MIXTURE",
            "heat_applied": heat_applied,
            "temperature_kelvin": scene.get("temperature_kelvin") or 310,
            "reagents": scene.get("reagents") or "H2O Nucleophile • Polar Protic",
            "rate_law": scene.get("rate_law") or "Rate = k[Substrate] • Fast Step 2",
            "stereochemistry": "50% Front + 50% Back = Racemic Mixture",
            "energy_profile": scene.get("energy_profile") or {
                "activation_energy": 35,
                "delta_g": -50,
                "transition_state": "[H2O···C+···OH2]‡",
                "num_barriers": 2,
            },
        }
    elif norm_mode in {"sn1_ionization", "sn1_carbocation"}:
        return {
            "reaction_name": scene.get("reaction_name") or "SN1 Heterolytic Cleavage & Planar Carbocation",
            "mode": mode if mode in {"sn1_carbocation", "sn1_ionization"} else "sn1_ionization",
            "sub_mode": "sn1_ionization",
            "thermodynamic_badge": scene.get("thermodynamic_badge") or "RATE-LIMITING STEP",
            "heat_applied": True,
            "temperature_kelvin": scene.get("temperature_kelvin") or 335,
            "reagents": scene.get("reagents") or "Polar Protic Solvent (H2O/Ethanol)",
            "rate_law": scene.get("rate_law") or "Rate = k[(CH3)3C-Br] (Unimolecular RDS)",
            "stereochemistry": "Planar sp² Carbocation (Achiral)",
            "energy_profile": scene.get("energy_profile") or {
                "activation_energy": 88,
                "delta_g": -38,
                "transition_state": "[(CH3)3C···Br]‡ -> Planar sp² C+",
                "num_barriers": 2,
            },
        }
    elif norm_mode == "addition_alkene":
        return {
            "reaction_name": scene.get("reaction_name") or "Electrophilic Alkene Addition",
            "mode": "addition_alkene",
            "sub_mode": "addition_alkene",
            "thermodynamic_badge": scene.get("thermodynamic_badge") or "EXOTHERMIC",
            "heat_applied": heat_applied,
            "temperature_kelvin": scene.get("temperature_kelvin") or (345 if heat_applied else 298),
            "reagents": scene.get("reagents") or "HBr • Dichloromethane",
            "rate_law": scene.get("rate_law") or "Rate = k[Alkene][HBr]",
            "stereochemistry": scene.get("stereochemistry") or "Markovnikov Regioselectivity",
            "energy_profile": scene.get("energy_profile") or {
                "activation_energy": 64,
                "delta_g": -82,
                "transition_state": "[C=C···H···Br]‡",
                "num_barriers": 2,
            },
        }
    elif norm_mode == "redox_combustion":
        return {
            "reaction_name": scene.get("reaction_name") or "Exothermic Acid-Base / Redox Transfer",
            "mode": "redox_combustion",
            "sub_mode": "redox_combustion",
            "thermodynamic_badge": scene.get("thermodynamic_badge") or "HIGHLY EXOTHERMIC",
            "heat_applied": True,
            "temperature_kelvin": scene.get("temperature_kelvin") or 375,
            "reagents": scene.get("reagents") or "Acid / Base Catalyst • O2",
            "rate_law": scene.get("rate_law") or "Rate = k[Acid][Base]",
            "stereochemistry": scene.get("stereochemistry") or "Diffusion-Controlled Proton Exchange",
            "energy_profile": scene.get("energy_profile") or {
                "activation_energy": 42,
                "delta_g": -120,
                "transition_state": "[H3O+···OH-]‡",
                "num_barriers": 1,
            },
        }
    else:  # sn2_concerted / sn2_substitution (default)
        return {
            "reaction_name": scene.get("reaction_name") or "SN2 180° Backside Attack & Walden Inversion",
            "mode": mode if mode in {"sn2_substitution", "sn2_concerted"} else "sn2_concerted",
            "sub_mode": "sn2_concerted",
            "thermodynamic_badge": scene.get("thermodynamic_badge") or "CONCERTED MECHANISM",
            "heat_applied": heat_applied,
            "temperature_kelvin": scene.get("temperature_kelvin") or (355 if heat_applied else 298),
            "reagents": scene.get("reagents") or "NaOH • Acetone (Polar Aprotic)",
            "rate_law": scene.get("rate_law") or "Rate = k[CH3Br][OH⁻] (Second-Order)",
            "stereochemistry": "Walden Inversion (100% Inversion of Stereocenter)",
            "energy_profile": scene.get("energy_profile") or {
                "activation_energy": 75,
                "delta_g": -45,
                "transition_state": "[HO···C···Br]‡",
                "num_barriers": 1,
            },
        }


def detect_quantum_mode(scene: Dict[str, Any]) -> str:
    explicit = scene.get("sub_mode") or scene.get("quantum_mode") or scene.get("mode")
    if explicit in {"schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"}:
        return explicit
    text = f"{scene.get('spoken_text', '')} {scene.get('title', '')} {scene.get('display_text', '')}".lower()
    if any(k in text for k in ["heisenberg", "uncertainty", "momentum", "position", "squeeze", "reciprocal", "fourier", "sigma_x"]):
        return "heisenberg_uncertainty"
    if any(k in text for k in ["dirac", "orbital", "spin", "spinor", "relativistic", "1s", "2p", "3d", "electron cloud", "gamma"]):
        return "dirac_atomic_orbitals"
    return "schrodinger_tunneling"


def synthesize_quantum_payload(scene: Dict[str, Any], sub_mode: str) -> Dict[str, Any]:
    if sub_mode == "heisenberg_uncertainty":
        return {
            "sub_mode": "heisenberg_uncertainty",
            "equation": "\\sigma_x \\sigma_p \\ge \\frac{\\hbar}{2}",
            "position_delta_x": scene.get("position_delta_x") or "Δx = 0.18 nm (Localized)",
            "momentum_delta_p": scene.get("momentum_delta_p") or "Δp = 2.94×10⁻²⁴ kg·m/s",
            "uncertainty_product": scene.get("uncertainty_product") or "Δx·Δp = 0.53 ℏ ≥ 0.5 ℏ",
            "phase_space_area": "Phase Space Ellipse Area ≥ ℏ/2",
            "reciprocity_tag": "FOURIER CONJUGATE SQUEEZE",
        }
    elif sub_mode == "dirac_atomic_orbitals":
        return {
            "sub_mode": "dirac_atomic_orbitals",
            "equation": "(i\\gamma^\\mu \\partial_\\mu - m)\\psi = 0",
            "quantum_numbers": scene.get("quantum_numbers") or {"n": 2, "l": 1, "m_l": 0, "m_s": "+1/2"},
            "orbitals_active": ["1s (Spherical)", "2p_z (Figure-8)", "3d (Cloverleaf)"],
            "spinor_state": "Dirac Bi-Spinor (ψ_L, ψ_R) | Spin Up (↑)",
            "energy_eigenvalue": "E = +mc² (Electron Positive Energy)",
        }
    else:  # schrodinger_tunneling
        return {
            "sub_mode": "schrodinger_tunneling",
            "equation": "i\\hbar \\frac{\\partial}{\\partial t}\\Psi(x,t) = \\left(-\\frac{\\hbar^2}{2m}\\frac{\\partial^2}{\\partial x^2} + V(x)\\right)\\Psi(x,t)",
            "tunneling_formula": "T = e^{-2\\kappa L}, \\quad \\kappa = \\sqrt{2m(V_0 - E)/\\hbar^2}",
            "barrier_v0": scene.get("barrier_height_ev") or "8.5 eV",
            "particle_e": scene.get("particle_energy_ev") or "5.2 eV",
            "transmission_coeff": scene.get("transmission_coefficient") or "T ≈ 0.082 (8.2%)",
            "wave_envelope": "Gaussian Packet (Re: Cyan, Im: Violet, |Ψ|²: Emerald)",
        }


def detect_mechanics_mode(scene: Dict[str, Any]) -> str:
    explicit = scene.get("sub_mode") or scene.get("mechanics_mode") or scene.get("mode")
    if explicit in {"beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"}:
        return explicit
    text = f"{scene.get('spoken_text', '')} {scene.get('title', '')} {scene.get('display_text', '')}".lower()
    if any(k in text for k in ["incline", "inclined", "ramp", "angle", "slope", "friction", "normal force", "slide", "theta"]):
        return "inclined_plane_fbd"
    if any(k in text for k in ["axle", "center of mass", "center of gravity", "chassis", "car", "vehicle", "wheelbase", "acceleration load", "braking", "squat"]):
        return "axle_center_of_mass"
    return "beam_weight_distribution"


def synthesize_mechanics_payload(scene: Dict[str, Any], sub_mode: str) -> Dict[str, Any]:
    if sub_mode == "inclined_plane_fbd":
        return {
            "sub_mode": "inclined_plane_fbd",
            "ramp_angle": scene.get("ramp_angle_deg") or 30,
            "mass": scene.get("mass_kg") or 20,
            "gravity": "F_g = mg = 196.2 N ↓",
            "parallel_force": "mg·sin(θ) = 98.1 N ↙",
            "normal_force": "F_N = mg·cos(θ) = 169.9 N ↖",
            "friction_force": "f_s = μ_s·F_N = 101.9 N (μ_s = 0.60)",
            "motion_state": "Static Equilibrium (tan(θ) ≤ μ_s)",
            "sliding_acceleration": "a = g(sinθ - μ_k cosθ) = 1.63 m/s²",
        }
    elif sub_mode == "axle_center_of_mass":
        return {
            "sub_mode": "axle_center_of_mass",
            "wheelbase": scene.get("wheelbase_m") or "L = 2.80 m",
            "cg_height": "h = 0.55 m",
            "vehicle_mass": "m = 1,600 kg",
            "static_load": "Front: 55% (8.63 kN) | Rear: 45% (7.06 kN)",
            "load_transfer": "ΔN = m·a·h / L = 2.51 kN (Dynamic Squat)",
            "dynamic_rear_axle": "N_R = (mg·a_cg/L) + (m·a_accel·h/L) = 9.57 kN",
        }
    else:  # beam_weight_distribution
        return {
            "sub_mode": "beam_weight_distribution",
            "beam_length": scene.get("beam_length_m") or "L = 10.0 m",
            "point_load": scene.get("point_load_kn") or "W₁ = 50 kN at x = 7.0 m",
            "distributed_load": "w = 5.0 kN/m",
            "left_reaction_ra": "R_A = 27.5 kN ↑",
            "right_reaction_rb": "R_B = 72.5 kN ↑",
            "step1_torque": "Στ_A = 0 ⟹ R_B·L - W₁·x - W_beam·(L/2) = 0",
            "step2_vertical": "ΣF_y = 0 ⟹ R_A + R_B = W₁ + W_beam",
            "diagrams": "Live Shear Force V(x) & Bending Moment M(x) Curves",
        }


def detect_electrical_mode(scene: Dict[str, Any]) -> str:
    explicit = scene.get("sub_mode") or scene.get("electrical_mode") or scene.get("mode")
    if explicit in {"kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"}:
        return explicit
    text = f"{scene.get('spoken_text', '')} {scene.get('title', '')} {scene.get('display_text', '')}".lower()
    if any(k in text for k in ["thevenin", "thev", "norton", "equivalent", "open circuit", "short circuit", "max power", "maximum power"]):
        return "thevenin_equivalence"
    if any(k in text for k in ["grid", "power flow", "opf", "dispatch", "generator", "transmission", "substation", "thermal limit", "congestion", "battery", "duck curve", "equal incremental"]):
        return "smart_grid_opf"
    return "kvl_kcl_mesh"


def synthesize_electrical_payload(scene: Dict[str, Any], sub_mode: str) -> Dict[str, Any]:
    if sub_mode == "thevenin_equivalence":
        return {
            "sub_mode": "thevenin_equivalence",
            "open_circuit_voc": "V_th = V_oc = 18.0 V",
            "short_circuit_isc": "I_sc = 3.0 A",
            "thevenin_resistance": "R_th = V_oc / I_sc = 6.0 Ω",
            "matched_load": "R_L = 6.0 Ω (Maximum Power Transfer)",
            "max_power": "P_max = V_th² / (4·R_th) = 13.5 W",
            "step1_reduction": "Step 1: Open Terminals A-B ⟹ Compute V_th",
            "step2_zero_sources": "Step 2: Short Independent Sources ⟹ Compute R_th",
        }
    elif sub_mode == "smart_grid_opf":
        return {
            "sub_mode": "smart_grid_opf",
            "grid_topology": "4-Bus High-Voltage Transmission (765 kV / 230 kV)",
            "thermal_line_pct": "Line 1-2: 94.8% Thermal (Congestion Alert!)",
            "lambda_cost": "λ = $34.50 / MWh (Equal Incremental Cost)",
            "generation_dispatch": "Nuclear: 450 MW | Gas: 280 MW | Renewables: 310 MW",
            "battery_storage": "Utility ESS Discharging: 85 MW (Duck Curve Peak Shaving)",
            "frequency_sync": "60.00 Hz (Grid Frequency Regulation)",
        }
    else:  # kvl_kcl_mesh
        return {
            "sub_mode": "kvl_kcl_mesh",
            "source_voltage": "V₁ = 24.0 V, V₂ = 12.0 V",
            "node_voltage_va": "Node V_A = 16.8 V",
            "loop_currents": "Loop I₁ = 1.80 A, Loop I₂ = 0.60 A",
            "kcl_equation": "ΣI_in = ΣI_out ⟹ (V₁ - V_A)/R₁ = V_A/R₂ + (V_A - V₂)/R₃",
            "kvl_equation": "ΣV_loop = 0 ⟹ -V₁ + I₁R₁ + (I₁ - I₂)R₂ = 0",
            "matrix_solver": "[G]·[V] = [I] (Conductance Matrix Solution)",
        }



def synthesize_concept_card(scene: Dict[str, Any], domain: str = "auto") -> Dict[str, Any]:
    """
    Synthesizes a 100% data-driven concept card from the scene's actual title,
    spoken text, narration, and domain.
    Never leaks Autoencoder, K-Means, or ML strings into pure math, physics, or electrical subjects.
    """
    title = scene.get("title") or scene.get("display_text") or "Core Architectural Principle"
    spoken_text = str(scene.get("spoken_text") or scene.get("narration") or "").strip()
    dom = (domain or scene.get("domain") or scene.get("subject") or "auto").lower()

    # 1. Dynamic Takeaways / Points
    existing_points = scene.get("points") or scene.get("bullets") or scene.get("takeaways")
    if existing_points and isinstance(existing_points, list) and len(existing_points) >= 2:
        points = [str(p) for p in existing_points[:3]]
    else:
        # Extract meaningful sentences or clauses from spoken_text
        raw_sentences = [s.strip() for s in re.split(r"[.!?]+", spoken_text) if len(s.strip()) > 10]
        has_ae = "autoencoder" in title.lower() or "autoencoder" in spoken_text.lower()
        sentences = [s for s in raw_sentences if has_ae or "autoencoder" not in s.lower()]
        if len(sentences) >= 3:
            points = sentences[:3]
        elif len(sentences) == 2:
            points = [sentences[0], sentences[1], f"Key takeaway: {title} ensures optimal structural guarantees"]
        elif len(sentences) == 1:
            points = [
                sentences[0],
                f"Applies fundamental {title} principles across the processing pipeline",
                "Eliminates latency overhead while maintaining maximum correctness",
            ]
        else:
            if "math" in dom:
                points = [
                    f"Core duality: {title} links instantaneous change to continuous accumulation",
                    "Inverse operator identities resolve complex continuous bounds",
                    "Proven mathematical foundation for analysis and geometry",
                ]
            elif "quantum" in dom:
                points = [
                    f"Quantum state evolution governed by {title}",
                    "Unitary operators preserve total probability density across time",
                    "Observable bounds follow canonical Heisenberg commutation limits",
                ]
            elif "electr" in dom:
                points = [
                    f"Network conservation: {title} guarantees active and reactive balance",
                    "Node voltage and loop current solutions eliminate thermal overloads",
                    "Optimal power dispatch stabilizes transmission bus stability",
                ]
            elif "mechanic" in dom:
                points = [
                    f"Structural balance: {title} maintains static equilibrium",
                    "Linear force and rotational moment sums resolve to zero",
                    "Maximum internal bending and shear stresses remain strictly bounded",
                ]
            else:
                points = [
                    f"Core mechanism: {title} establishes deterministic invariant execution",
                    "Reduces algorithmic complexity and prevents edge-case regressions",
                    "Proven mathematical and architectural foundation in production environments",
                ]

    # 2. Dynamic Concept Nodes (100% domain-aware)
    existing_nodes = scene.get("concept_nodes")
    if existing_nodes and isinstance(existing_nodes, list) and len(existing_nodes) >= 2:
        concept_nodes = existing_nodes
    else:
        words = [w for w in re.findall(r"\b[A-Za-z]{3,}\b", spoken_text) if w.lower() not in {"this", "that", "with", "from", "then", "have", "they", "will", "does", "been", "when"}]
        kw1 = words[0].title() if len(words) > 0 else "Signal"
        kw2 = words[len(words) // 2].title() if len(words) > 2 else "Transformation"
        kw3 = words[-1].title() if len(words) > 1 else "Convergence"

        if "math" in dom:
            concept_nodes = [
                {"id": "node_input", "tag": "DOMAIN", "label": scene.get("input_label") or f"{kw1} Space", "detail": "Continuous interval [a, b] & partition grid"},
                {"id": "node_kernel", "tag": "TRANSFORM", "label": scene.get("kernel_label") or title, "detail": "Instantaneous rate f'(x) vs Riemann accumulation ∫f(x)dx"},
                {"id": "node_output", "tag": "CLOSURE", "label": scene.get("output_label") or f"{kw3} Limit", "detail": "Fundamental theorem evaluation F(b) - F(a)"},
            ]
        elif "quantum" in dom:
            concept_nodes = [
                {"id": "node_input", "tag": "STATE", "label": scene.get("input_label") or "Wavefunction Ψ", "detail": "Complex Hilbert space state probability distribution"},
                {"id": "node_kernel", "tag": "OPERATOR", "label": scene.get("kernel_label") or title, "detail": "Unitary Hamiltonian evolution iℏ∂Ψ/∂t = ĤΨ"},
                {"id": "node_output", "tag": "COLLAPSE", "label": scene.get("output_label") or "Eigenstate", "detail": "Deterministic observable expectation & quantum boundary"},
            ]
        elif "electr" in dom:
            concept_nodes = [
                {"id": "node_input", "tag": "TOPOLOGY", "label": scene.get("input_label") or "Bus Network", "detail": "Multi-node transmission topology & impedance matrix"},
                {"id": "node_kernel", "tag": "EQUILIBRIUM", "label": scene.get("kernel_label") or title, "detail": "KVL loop voltages and KCL nodal conservation ΣI = 0"},
                {"id": "node_output", "tag": "DISPATCH", "label": scene.get("output_label") or "Optimal Power", "detail": "Equal incremental cost λ dispatch & stable power flow"},
            ]
        elif "mechanic" in dom:
            concept_nodes = [
                {"id": "node_input", "tag": "LOAD", "label": scene.get("input_label") or "External Forces", "detail": "Applied load distribution and support boundary reactions"},
                {"id": "node_kernel", "tag": "STATICS", "label": scene.get("kernel_label") or title, "detail": "Static force equilibrium ΣF = 0 and moment balance Στ = 0"},
                {"id": "node_output", "tag": "STRESS", "label": scene.get("output_label") or "Peak Deflection", "detail": "Bending moment peak and structural safety margin"},
            ]
        elif "chem" in dom:
            concept_nodes = [
                {"id": "node_input", "tag": "REAGENTS", "label": scene.get("input_label") or "Substrate & Nu⁻", "detail": "Reactant stoichiometry and steric bulkiness"},
                {"id": "node_kernel", "tag": "KINETICS", "label": scene.get("kernel_label") or title, "detail": "Activation energy barrier and transition state geometry"},
                {"id": "node_output", "tag": "YIELD", "label": scene.get("output_label") or "Stereo Product", "detail": "Thermodynamic product yield and inversion outcome"},
            ]
        else:
            concept_nodes = [
                {"id": "node_input", "tag": "INPUT", "label": scene.get("input_label") or f"{kw1} Vector", "detail": "Input feature distribution & parameter state"},
                {"id": "node_kernel", "tag": "KERNEL", "label": scene.get("kernel_label") or title, "detail": "Invariant algorithmic transform & execution pipeline"},
                {"id": "node_output", "tag": "OUTPUT", "label": scene.get("output_label") or f"{kw3} State", "detail": "Deterministic convergence & verified correctness"},
            ]

    return {
        "concept_nodes": concept_nodes,
        "points": points,
        "bullets": points,
        "takeaways": points,
    }


def choreograph_scenes(
    timed_scenes: List[Dict[str, Any]],
    words: List[Dict[str, Any]],
    domain: str = "auto",
    fps: int = 30,
) -> List[Dict[str, Any]]:
    """
    Enriches timed scenes with domain-aware choreography directives and themes.

    Guarantees:
      - Does not alter audio paths, duration, or Whisper word timestamps.
      - Strictly additive (adds 'choreography', 'theme', 'palette' keys).
      - Guarantees zero empty cards across Math, Graph, Physics, Chemistry, and ML scenes.
      - Enforces minimum scene duration >= 2.5s with zero flash cuts.
      - Enforces No Back-to-Back Identical Visual Layout rule.
      - Automatically routes concluding scenes away from neural_code_split to comparison/concept.
      - 100% de-hardcoded concept card fallback (never displays Autoencoder unless explicitly in script).
    """
    if not timed_scenes:
        return []

    active_domain = resolve_domain(timed_scenes, domain)
    total_duration = max([float(w.get("end", 0.0)) for w in words], default=0.0) if words else 0.0

    enriched_scenes: List[Dict[str, Any]] = []
    prev_visual_type: Optional[str] = None
    prev_mode: Optional[str] = None
    consecutive_type_count = 0

    for i, orig_scene in enumerate(timed_scenes):
        scene = copy.deepcopy(orig_scene)
        scene_type = scene.get("scene_type") or scene.get("visual_type", "code_reveal")
        spoken_text_lower = f"{scene.get('spoken_text', '')} {scene.get('narration', '')} {scene.get('title', '')} {scene.get('display_text', '')}".lower()

        # Check if concluding / takeaway scene
        is_concluding_scene = (
            len(timed_scenes) > 2 and i == len(timed_scenes) - 1 and
            any(k in spoken_text_lower for k in [
                "takeaway", "conclusion", "summary", "in summary", "recap",
                "bottom line", "final thought", "key takeaway", "to summarize",
                "geometry beats", "beats deep learning", "instead of deep learning",
                "beats bloat", "never need", "simple beats"
            ])
        ) or any(k in spoken_text_lower for k in [
            "geometry beats", "beats deep learning", "instead of deep learning",
            "beats bloat", "why use neural networks when", "never need neural"
        ])

        # Layout density & sub_mode resolution
        layout_density = orig_scene.get("layout_density") or orig_scene.get("choreography", {}).get("layout_density")
        sub_mode = orig_scene.get("sub_mode") or orig_scene.get("chemistry_mode")

        # Check domain or topic
        is_chemistry = (
            active_domain == "chemistry" or
            scene_type in {"chemistry", "chemistry_reaction"} or
            (active_domain in {"auto", ""} and any(k in spoken_text_lower for k in [
                "reaction mechanism", "chemical reaction", "molecule", "molecular", "sn1", "sn2", "nucleophile",
                "electrophile", "substrate", "carbocation", "alkene", "enthalpy",
                "exothermic", "endothermic", "activation energy", "catalyst", "covalent bond"
            ]))
        )
        is_quantum = (
            active_domain == "quantum_physics" or
            scene_type in {"quantum_sim", "quantum_physics"} or
            (active_domain in {"auto", ""} and any(k in spoken_text_lower for k in [
                "quantum", "schrodinger", "wavefunction", "tunneling", "wavepacket",
                "heisenberg", "uncertainty", "dirac", "spinor", "atomic orbital"
            ]))
        )
        is_mechanics = (
            active_domain == "mechanics" or
            scene_type in {"mechanics_fbd", "mechanics"} or
            (active_domain in {"auto", ""} and any(k in spoken_text_lower for k in [
                "beam", "weight distribution", "free body", "fbd", "load distribution",
                "shear force", "bending moment", "inclined plane", "ramp", "friction threshold",
                "center of mass", "center of gravity", "load transfer", "torque equilibrium"
            ]))
        )
        is_electrical = (
            active_domain == "electrical" or
            scene_type in {"electrical_grid", "electrical"} or
            (active_domain in {"auto", ""} and any(k in spoken_text_lower for k in [
                "circuit", "kvl", "kcl", "kirchhoff", "thevenin", "thevenin equivalence",
                "mesh analysis", "nodal analysis", "smart grid", "power flow",
                "optimal power flow", "economic dispatch", "substation", "transmission line"
            ]))
        )

        if is_chemistry and not sub_mode:
            sub_mode = detect_chemistry_mode(orig_scene)
        elif is_quantum and not sub_mode:
            sub_mode = detect_quantum_mode(orig_scene)
        elif is_mechanics and not sub_mode:
            sub_mode = detect_mechanics_mode(orig_scene)
        elif is_electrical and not sub_mode:
            sub_mode = detect_electrical_mode(orig_scene)

        num_scenes = len(timed_scenes)

        has_explicit_code = bool(orig_scene.get("code") or (orig_scene.get("visual_type") == "code_reveal" and orig_scene.get("code")))
        if is_chemistry and not has_explicit_code and orig_scene.get("visual_type") != "math_equation":
            # Mandatory Visual Type Rotation & Structural Rhythm across full video (>= 5 scenes)
            if (active_domain == "chemistry" and num_scenes >= 5) or num_scenes >= 6:
                if i == 0:
                    scene_type = "comparison"
                    layout_density = layout_density or "compact_punch"
                    if not scene.get("comparison_sides"):
                        scene["comparison_sides"] = {
                            "left": {
                                "title": "SN2: CONCERTED FLIP",
                                "details": ["Single transition state [‡]", "180° Backside attack", "100% Walden inversion"],
                            },
                            "right": {
                                "title": "SN1: STEPWISE CARBOCATION",
                                "details": ["Planar sp² C⁺ intermediate", "Dual-face racemic attack", "Rate depends only on substrate"],
                            },
                        }
                    if not scene.get("problem_label"):
                        scene["problem_label"] = "SN2 SUBSTITUTION"
                        scene["problem_code"] = "1-Step Concerted Mechanism\n180° Backside Attack\nWalden Inversion (100%)\nPreferred: Methyl / 1° Substrate"
                    if not scene.get("solution_label"):
                        scene["solution_label"] = "SN1 SUBSTITUTION"
                        scene["solution_code"] = "2-Step Carbocation Pathway\nHeterolytic C-X Cleavage\nRacemic Mixture (50/50)\nPreferred: Bulky 3° Substrate"
                elif i == num_scenes - 1:
                    scene_type = "bento_grid"
                    layout_density = layout_density or "full_dashboard"
                elif num_scenes == 5:
                    scene_type = "chemistry_reaction"
                    chem_modes = ["sn2_concerted", "steric_blockade", "sn1_ionization"]
                    sub_mode = chem_modes[(i - 1) % len(chem_modes)]
                    layout_density = layout_density or ("full_dashboard" if sub_mode == "sn1_ionization" else "canvas_spotlight")
                elif num_scenes == 6:
                    if i == 4:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    else:
                        scene_type = "chemistry_reaction"
                        chem_modes = ["sn2_concerted", "steric_blockade", "sn1_ionization"]
                        sub_mode = chem_modes[(i - 1) % len(chem_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "sn1_ionization" else "canvas_spotlight")
                elif num_scenes == 7:
                    if i == 5:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    else:
                        scene_type = "chemistry_reaction"
                        chem_modes = ["sn2_concerted", "steric_blockade", "sn1_ionization", "sn1_racemic"]
                        sub_mode = chem_modes[(i - 1) % len(chem_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "sn1_ionization" else "canvas_spotlight")
                else:  # num_scenes >= 8
                    if i == 3:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 6:
                        scene_type = "math_equation"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 8:
                        scene_type = "comparison"
                        layout_density = layout_density or "compact_punch"
                    else:
                        scene_type = "chemistry_reaction"
                        slot_map = {1: 0, 2: 1, 4: 2, 5: 3, 7: 0, 9: 1, 10: 2, 11: 3}
                        s_idx = slot_map.get(i, (i - 1) % 4)
                        chem_modes = ["sn2_concerted", "steric_blockade", "sn1_ionization", "sn1_racemic"]
                        sub_mode = chem_modes[s_idx % len(chem_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "sn1_ionization" else "canvas_spotlight")
            else:
                scene_type = orig_scene.get("visual_type") or "chemistry_reaction"
                sub_mode = sub_mode or ("sn2_concerted" if i == 0 else "sn1_carbocation")
                layout_density = layout_density or ("compact_punch" if i == 0 else "canvas_spotlight")
        elif is_quantum and not has_explicit_code and orig_scene.get("visual_type") != "math_equation":
            if (active_domain == "quantum_physics" and num_scenes >= 5) or num_scenes >= 6:
                if i == 0:
                    scene_type = "comparison"
                    layout_density = layout_density or "compact_punch"
                    if not scene.get("comparison_sides"):
                        scene["comparison_sides"] = {
                            "left": {
                                "title": "CLASSICAL MECHANICS",
                                "details": ["Phase-space point (x, p)", "Zero barrier penetration (E < V₀)", "Commuting observables [x, p] = 0"],
                            },
                            "right": {
                                "title": "QUANTUM MECHANICS",
                                "details": ["Complex wavepacket Ψ(x,t)", "Tunneling transmission T = e^(-2κL)", "Non-commuting [x̂, p̂] = iℏ"],
                            },
                        }
                    if not scene.get("problem_label"):
                        scene["problem_label"] = "CLASSICAL DETERMINISM"
                        scene["problem_code"] = "Exact Phase Space Point\nZero Barrier Penetration\n[x, p] = 0 (Commuting)\nDeterministic Trajectory"
                    if not scene.get("solution_label"):
                        scene["solution_label"] = "QUANTUM WAVEPACKET"
                        scene["solution_code"] = "Wavefunction Ψ(x,t)\nEvanescent Tunneling Decay\n[x̂, p̂] = iℏ (Non-Commuting)\nUncertainty: Δx·Δp ≥ ℏ/2"
                elif i == num_scenes - 1:
                    scene_type = "bento_grid"
                    layout_density = layout_density or "full_dashboard"
                elif num_scenes == 5:
                    scene_type = "quantum_sim"
                    q_modes = ["schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"]
                    sub_mode = q_modes[(i - 1) % len(q_modes)]
                    layout_density = layout_density or ("full_dashboard" if sub_mode == "dirac_atomic_orbitals" else "canvas_spotlight")
                elif num_scenes == 6:
                    if i == 4:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    else:
                        scene_type = "quantum_sim"
                        q_modes = ["schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"]
                        sub_mode = q_modes[(i - 1) % len(q_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "dirac_atomic_orbitals" else "canvas_spotlight")
                elif num_scenes == 7:
                    if i == 5:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 4:
                        scene_type = "math_equation"
                        layout_density = layout_density or "canvas_spotlight"
                    else:
                        scene_type = "quantum_sim"
                        q_modes = ["schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"]
                        sub_mode = q_modes[(i - 1) % len(q_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "dirac_atomic_orbitals" else "canvas_spotlight")
                else:  # num_scenes >= 8
                    if i == 3:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 6:
                        scene_type = "math_equation"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 8:
                        scene_type = "comparison"
                        layout_density = layout_density or "compact_punch"
                    else:
                        scene_type = "quantum_sim"
                        slot_map = {1: 0, 2: 1, 4: 2, 5: 1, 7: 0, 9: 2, 10: 1, 11: 0}
                        s_idx = slot_map.get(i, (i - 1) % 3)
                        q_modes = ["schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"]
                        sub_mode = q_modes[s_idx % len(q_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "dirac_atomic_orbitals" else "canvas_spotlight")
            else:
                scene_type = orig_scene.get("visual_type") or "quantum_sim"
                sub_mode = sub_mode or detect_quantum_mode(orig_scene)
                layout_density = layout_density or ("compact_punch" if i == 0 else "canvas_spotlight")
        elif is_mechanics and not has_explicit_code and orig_scene.get("visual_type") != "math_equation":
            if (active_domain == "mechanics" and num_scenes >= 5) or num_scenes >= 6:
                if i == 0:
                    scene_type = "comparison"
                    layout_density = layout_density or "compact_punch"
                    if not scene.get("comparison_sides"):
                        scene["comparison_sides"] = {
                            "left": {
                                "title": "UNBALANCED SYSTEM",
                                "details": ["Net resultant force ΣF ≠ 0", "Unbalanced torque Στ ≠ 0", "Support reaction overload"],
                            },
                            "right": {
                                "title": "STATIC EQUILIBRIUM",
                                "details": ["Vertical equilibrium ΣFy = 0", "Torque balance ΣτA = 0", "Shear & Moment closed"],
                            },
                        }
                    if not scene.get("problem_label"):
                        scene["problem_label"] = "NON-EQUILIBRIUM"
                        scene["problem_code"] = "Resultant Force ΣF ≠ 0\nNet Torque Accelerates Beam\nSupport Reaction Overload\nStructure Destabilization"
                    if not scene.get("solution_label"):
                        scene["solution_label"] = "STATIC EQUILIBRIUM"
                        scene["solution_code"] = "Force Balance: ΣFy = 0\nTorque Balance: ΣτA = 0\nPin RA & Roller RB Resolved\nShear V(x) & Moment M(x) Solved"
                elif i == num_scenes - 1:
                    scene_type = "bento_grid"
                    layout_density = layout_density or "full_dashboard"
                elif num_scenes == 5:
                    scene_type = "mechanics_fbd"
                    m_modes = ["beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"]
                    sub_mode = m_modes[(i - 1) % len(m_modes)]
                    layout_density = layout_density or ("full_dashboard" if sub_mode == "axle_center_of_mass" else "canvas_spotlight")
                elif num_scenes == 6:
                    if i == 4:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    else:
                        scene_type = "mechanics_fbd"
                        m_modes = ["beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"]
                        sub_mode = m_modes[(i - 1) % len(m_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "axle_center_of_mass" else "canvas_spotlight")
                elif num_scenes == 7:
                    if i == 5:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 4:
                        scene_type = "math_equation"
                        layout_density = layout_density or "canvas_spotlight"
                    else:
                        scene_type = "mechanics_fbd"
                        m_modes = ["beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"]
                        sub_mode = m_modes[(i - 1) % len(m_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "axle_center_of_mass" else "canvas_spotlight")
                else:  # num_scenes >= 8
                    if i == 3:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 6:
                        scene_type = "math_equation"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 8:
                        scene_type = "comparison"
                        layout_density = layout_density or "compact_punch"
                    else:
                        scene_type = "mechanics_fbd"
                        slot_map = {1: 0, 2: 1, 4: 2, 5: 1, 7: 0, 9: 2, 10: 1, 11: 0}
                        s_idx = slot_map.get(i, (i - 1) % 3)
                        m_modes = ["beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"]
                        sub_mode = m_modes[s_idx % len(m_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "axle_center_of_mass" else "canvas_spotlight")
            else:
                scene_type = orig_scene.get("visual_type") or "mechanics_fbd"
                sub_mode = sub_mode or detect_mechanics_mode(orig_scene)
                layout_density = layout_density or ("compact_punch" if i == 0 else "canvas_spotlight")
        elif is_electrical and not has_explicit_code and orig_scene.get("visual_type") != "math_equation":
            if (active_domain == "electrical" and num_scenes >= 5) or num_scenes >= 6:
                if i == 0:
                    scene_type = "comparison"
                    layout_density = layout_density or "compact_punch"
                    if not scene.get("comparison_sides"):
                        scene["comparison_sides"] = {
                            "left": {
                                "title": "RAW MESH NETWORK",
                                "details": ["Multiple coupled loops", "Tedious KVL matrix solving", "Must re-solve on load change"],
                            },
                            "right": {
                                "title": "THÉVENIN EQUIVALENT",
                                "details": ["Single Vth ideal source", "Single series resistance Rth", "Peak power transfer at RL = Rth"],
                            },
                        }
                    if not scene.get("problem_label"):
                        scene["problem_label"] = "COMPLEX MESH NETWORK"
                        scene["problem_code"] = "Coupled Mesh Loops (I1, I2)\nConductance Matrix [G][V] = [I]\nRecalculate On Load Variation\nThermal Corridor Congestion"
                    if not scene.get("solution_label"):
                        scene["solution_label"] = "THÉVENIN EQUIVALENCE"
                        scene["solution_code"] = "Open-Circuit Voltage: Vth = Voc\nEquivalent Resistance: Rth = Voc/Isc\nDirect Load Current: IL = Vth/(Rth+RL)\nMatched Max Power: RL = Rth"
                elif i == num_scenes - 1:
                    scene_type = "bento_grid"
                    layout_density = layout_density or "full_dashboard"
                elif num_scenes == 5:
                    scene_type = "electrical_grid"
                    e_modes = ["kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"]
                    sub_mode = e_modes[(i - 1) % len(e_modes)]
                    layout_density = layout_density or ("full_dashboard" if sub_mode == "smart_grid_opf" else "canvas_spotlight")
                elif num_scenes == 6:
                    if i == 4:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    else:
                        scene_type = "electrical_grid"
                        e_modes = ["kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"]
                        sub_mode = e_modes[(i - 1) % len(e_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "smart_grid_opf" else "canvas_spotlight")
                elif num_scenes == 7:
                    if i == 5:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 4:
                        scene_type = "math_equation"
                        layout_density = layout_density or "canvas_spotlight"
                    else:
                        scene_type = "electrical_grid"
                        e_modes = ["kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"]
                        sub_mode = e_modes[(i - 1) % len(e_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "smart_grid_opf" else "canvas_spotlight")
                else:  # num_scenes >= 8
                    if i == 3:
                        scene_type = "function_graph"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 6:
                        scene_type = "math_equation"
                        layout_density = layout_density or "canvas_spotlight"
                    elif i == 8:
                        scene_type = "comparison"
                        layout_density = layout_density or "compact_punch"
                    else:
                        scene_type = "electrical_grid"
                        slot_map = {1: 0, 2: 1, 4: 2, 5: 1, 7: 0, 9: 2, 10: 1, 11: 0}
                        s_idx = slot_map.get(i, (i - 1) % 3)
                        e_modes = ["kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"]
                        sub_mode = e_modes[s_idx % len(e_modes)]
                        layout_density = layout_density or ("full_dashboard" if sub_mode == "smart_grid_opf" else "canvas_spotlight")
            else:
                scene_type = orig_scene.get("visual_type") or "electrical_grid"
                sub_mode = sub_mode or detect_electrical_mode(orig_scene)
                layout_density = layout_density or ("compact_punch" if i == 0 else "canvas_spotlight")
        elif not scene.get("diagram_mode") and not scene.get("concept_mode") and any(k in spoken_text_lower for k in [
            "neural network", "neural net", "autoencoder", "auto-encoder", "latent space",
            "deep learning", "backpropagation", "bottleneck layer", "reconstruction"
        ]):
            # If concluding takeaway scene, NEVER route to neural_code_split!
            if is_concluding_scene:
                if any(k in spoken_text_lower for k in ["vs", "versus", "beats", "against", "compared to", "differ"]):
                    scene_type = "comparison"
                else:
                    scene_type = "concept"
            else:
                scene_type = "neural_code_split"

        # General rule: Bento grid can NEVER appear before the final scene in full scripts!
        if num_scenes >= 5 and scene_type == "bento_grid" and i < num_scenes - 1:
            if is_electrical:
                scene_type = "electrical_grid"
                modes = ["kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"]
                sub_mode = sub_mode or modes[i % len(modes)]
            elif is_mechanics:
                scene_type = "mechanics_fbd"
                modes = ["beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"]
                sub_mode = sub_mode or modes[i % len(modes)]
            elif is_quantum:
                scene_type = "quantum_sim"
                modes = ["schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"]
                sub_mode = sub_mode or modes[i % len(modes)]
            elif is_chemistry:
                scene_type = "chemistry_reaction"
                modes = ["sn2_concerted", "steric_blockade", "sn1_ionization", "sn1_racemic"]
                sub_mode = sub_mode or modes[i % len(modes)]
            else:
                scene_type = "comparison" if i == 0 else "function_graph"

        # Enforce No Back-to-Back Identical Visual Layout rule:
        # If consecutive scenes resolve to the same visual_type, vary to avoid monotony
        if prev_visual_type is not None and scene_type == prev_visual_type:
            consecutive_type_count += 1
            if scene_type == "neural_code_split" and (consecutive_type_count >= 2 or is_concluding_scene):
                scene_type = "comparison" if any(k in spoken_text_lower for k in ["vs", "better", "beats"]) else "concept"
            elif num_scenes >= 5 and scene_type == "bento_grid" and i < num_scenes - 1:
                scene_type = "comparison"
        else:
            consecutive_type_count = 0

        # Assign layout density default if not explicitly defined
        if not layout_density:
            if i == 0 or is_concluding_scene or scene_type in {"comparison", "concept", "fullscreen_text"}:
                layout_density = "compact_punch"
            elif scene_type in {"bento_grid", "algorithm_explorer", "neural_code_split"}:
                layout_density = "full_dashboard"
            elif scene_type in {"function_graph", "physics_sim", "manim_scene"}:
                layout_density = "canvas_spotlight"
            elif scene_type in {"chemistry_reaction", "chemistry"}:
                layout_density = "full_dashboard" if sub_mode == "sn1_ionization" else "canvas_spotlight"
            elif scene_type in {"quantum_sim", "quantum_physics"}:
                layout_density = "full_dashboard" if sub_mode == "dirac_atomic_orbitals" else "canvas_spotlight"
            elif scene_type in {"mechanics_fbd", "mechanics"}:
                layout_density = "full_dashboard" if sub_mode == "axle_center_of_mass" else "canvas_spotlight"
            elif scene_type in {"electrical_grid", "electrical"}:
                layout_density = "full_dashboard" if sub_mode == "smart_grid_opf" else "canvas_spotlight"
            else:
                layout_density = "canvas_spotlight"

        if scene_type == "comparison":
            comp_footer = scene.get("comparison_footer")
            # If domain is not code, purge any CS algorithm / asymptotic complexity text
            if active_domain != "code" and comp_footer and any(x in comp_footer for x in ["ASYMPTOTIC", "O(n²)", "O(n)", "Complexity"]):
                comp_footer = None
            if not comp_footer:
                comp_footer = COMPARISON_FOOTERS.get(active_domain, "KEY TAKEAWAY: Evaluating trade-offs across both analytical regimes")
            if "|" in comp_footer:
                comp_footer = comp_footer.split("|")[0].strip()
            if not comp_footer.startswith("KEY TAKEAWAY:"):
                comp_footer = f"KEY TAKEAWAY: {comp_footer.replace('KEY TAKEAWAY:', '').strip()}"
            scene["comparison_footer"] = comp_footer

        scene["visual_type"] = scene_type
        scene["scene_type"] = scene_type
        scene["layout_density"] = layout_density
        if sub_mode:
            scene["sub_mode"] = sub_mode
            scene["chemistry_mode"] = orig_scene.get("chemistry_mode") or sub_mode

        start_time = float(scene.get("start_time", 0.0))
        if i == 0:
            start_time = 0.0
            scene["start_time"] = 0.0

        if "end_time" in scene and scene["end_time"] is not None:
            end_time = float(scene["end_time"])
        elif i + 1 < len(timed_scenes):
            end_time = float(timed_scenes[i + 1].get("start_time", start_time + 2.5))
        else:
            end_time = max(total_duration, start_time + 2.5)

        if end_time < start_time + 2.5:
            end_time = start_time + 2.5
        end_time = round(end_time, 3)
        scene["end_time"] = end_time

        scene_start_frame = max(0, round(start_time * fps))
        scene_end_frame = max(scene_start_frame + round(2.5 * fps), round(end_time * fps))

        emphasis_time = float(scene.get("emphasis_time", start_time + 0.5))
        if emphasis_time < start_time:
            emphasis_time = start_time
        emphasis_frame = max(scene_start_frame, round(emphasis_time * fps))

        # Words in this scene
        scene_words = [
            w for w in (words or [])
            if w.get("start", 0.0) >= (start_time - 0.05) and w.get("start", 0.0) <= (end_time + 0.05)
        ]

        # Theme resolution
        theme_id = assign_theme_id(scene, active_domain)
        palette = THEME_PALETTES.get(theme_id, THEME_PALETTES["code_cyber"])

        choreography: Dict[str, Any] = {
            "domain": active_domain,
            "theme": theme_id,
            "palette": palette,
            "layout_density": layout_density,
            "sub_mode": sub_mode,
            "scene_start_frame": scene_start_frame,
            "scene_end_frame": scene_end_frame,
            "emphasis_frame": emphasis_frame,
        }

        # ── Primitive-Specific Directives & Non-Empty Syntheses ───────────────

        # 1. Math Equation Derivations
        if scene_type == "math_equation":
            choreography["layout_mode"] = "stepped"
            raw_steps = synthesize_math_steps(scene, active_domain)
            scene["steps"] = raw_steps
            scene["equations"] = raw_steps
            intuition_payload = synthesize_math_intuition(scene, active_domain)
            scene["intuition"] = intuition_payload
            scene["domain"] = active_domain
            scene["subject"] = active_domain
            if not scene.get("title") or scene.get("title") == "Euler's Identity":
                scene["title"] = f"{active_domain.replace('_', ' ').title()} Mathematical Formulation"
            steps_count = max(1, len(raw_steps))
            step_duration = max(10, (scene_end_frame - scene_start_frame) // (steps_count + 1))

            steps_choreography = []
            for s_idx, step in enumerate(raw_steps):
                reveal_frame = scene_start_frame + s_idx * step_duration
                formula_str = step if isinstance(step, str) else (step.get("formula") or step.get("latex") or "")
                expl_str = "" if isinstance(step, str) else step.get("explanation", "")

                highlight_frame = reveal_frame + 4
                highlight_term = None
                tokens = formula_str.replace("=", " ").replace("+", " ").replace("-", " ").split()
                for token in tokens:
                    clean_token = token.strip()
                    if len(clean_token) >= 2:
                        for w in scene_words:
                            if clean_token.lower() in w.get("word", "").lower():
                                highlight_frame = round(w.get("start", 0.0) * fps)
                                highlight_term = clean_token
                                break
                    if highlight_term:
                        break

                steps_choreography.append({
                    "step_index": s_idx,
                    "formula": formula_str,
                    "explanation": expl_str,
                    "reveal_frame": reveal_frame,
                    "highlight_frame": highlight_frame,
                    "highlight_term": highlight_term,
                })

            choreography["steps"] = steps_choreography

        # 2. Function Graph 2D Plotting
        elif scene_type == "function_graph":
            choreography["layout_mode"] = "focused"
            graph_payload = synthesize_domain_graph_data(scene, active_domain)
            scene["graph_data"] = graph_payload
            scene["functions"] = graph_payload.get("curves", [])
            scene["title"] = graph_payload.get("title", scene.get("title"))
            scene["category_tag"] = graph_payload.get("header", scene.get("category_tag"))
            scene["x_label"] = graph_payload.get("x_label", "X Axis")
            scene["y_label"] = graph_payload.get("y_label", "Y Axis")
            scene["curve_type"] = graph_payload.get("curve_type", "quadratic")
            scene["breakdown"] = graph_payload.get("breakdown")
            scene["critical_point_label"] = graph_payload.get("critical_point")

            draw_start_frame = scene_start_frame + 4
            draw_end_frame = min(scene_start_frame + 35, emphasis_frame)
            if draw_end_frame <= draw_start_frame:
                draw_end_frame = draw_start_frame + 20

            tangent_frame = min(scene_end_frame - 4, emphasis_frame + 8)

            choreography["graph"] = {
                "draw_start_frame": draw_start_frame,
                "draw_end_frame": draw_end_frame,
                "emphasis_frame": emphasis_frame,
                "tangent_frame": tangent_frame,
                "critical_points": [
                    {
                        "x": 0.0,
                        "y": 0.0,
                        "label": scene.get("critical_point_label") or "Intercept / Critical Point",
                        "frame": emphasis_frame,
                    }
                ],
            }

        # 3. Physics Simulation & Vector Diagrams
        elif scene_type == "physics_sim":
            choreography["layout_mode"] = "kinetic"
            sim_mode = detect_physics_mode(scene)
            scene["sim_type"] = sim_mode

            phys_payload = synthesize_physics_payload(scene, sim_mode)
            for k, v in phys_payload.items():
                scene[k] = v

            vector_growth_start = scene_start_frame + 4
            vector_growth_end = min(scene_start_frame + 22, emphasis_frame)

            choreography["physics"] = {
                "sim_type": sim_mode,
                "vector_growth_start_frame": vector_growth_start,
                "vector_growth_end_frame": vector_growth_end,
                "motion_start_frame": emphasis_frame,
                "force_highlight_frame": emphasis_frame,
            }

        # 4. Bento Grid (Editorial Overview)
        elif scene_type == "bento_grid":
            choreography["layout_mode"] = "bento"
            bento_payload = synthesize_domain_bento_data(scene, active_domain)
            scene["bento_data"] = bento_payload
            scene["cards"] = bento_payload.get("cards", [])
            scene["section_title"] = bento_payload.get("section_title")
            scene["subtitle"] = bento_payload.get("subtitle")
            scene["domain"] = active_domain
            cards = scene["cards"]


            card_count = max(1, len(cards))
            card_duration = max(8, (scene_end_frame - scene_start_frame) // (card_count + 1))
            active_card_frames = []
            for c_idx, card in enumerate(cards):
                c_title = card.get("title", "")
                c_frame = scene_start_frame + c_idx * card_duration
                for w in scene_words:
                    if c_title.lower() in w.get("word", "").lower():
                        c_frame = round(w.get("start", 0.0) * fps)
                        break
                active_card_frames.append({"card_index": c_idx, "illumination_frame": c_frame})

            choreography["active_card_frames"] = active_card_frames

        # 5. Algorithm Explorer (Deep-Dive 3-Tier Layout)
        elif scene_type == "algorithm_explorer":
            choreography["layout_mode"] = "explorer"
            explorer_payload = synthesize_algorithm_explorer(scene)
            for k, v in explorer_payload.items():
                scene[k] = v

            choreography["explorer"] = {
                "scan_start_frame": scene_start_frame + 4,
                "scan_end_frame": scene_end_frame - 4,
                "active_concept_index": 1,
            }

        # 6. Neural Code Split (Vertical Split Visualizer + Code Window)
        elif scene_type == "neural_code_split":
            choreography["layout_mode"] = "neural_split"
            neural_payload = synthesize_neural_code_split(scene)
            for k, v in neural_payload.items():
                scene[k] = v

            code_lines = (scene.get("code_snippet") or "").split("\n")
            line_count = max(1, len(code_lines))
            line_interval = max(4, (scene_end_frame - scene_start_frame) // (line_count + 1))

            choreography["neural"] = {
                "line_highlight_frames": [
                    scene_start_frame + l_idx * line_interval for l_idx in range(line_count)
                ],
                "epoch_start": 1,
                "epoch_end": 300,
                "loss_start": 0.842,
                "loss_end": 0.206,
                "pulse_start_frame": scene_start_frame + 4,
            }

        # 7. Code Reveal & Terminal
        elif scene_type in {"code_reveal", "terminal"}:
            choreography["layout_mode"] = "stepped"
            lines = (scene.get("code_snippet") or "").split("\n")
            line_count = max(1, len(lines))
            choreography["step_activation_frames"] = [
                scene_start_frame + l_idx * 4 for l_idx in range(line_count)
            ]

        # 8. Code Transform & Comparison
        elif scene_type in {"code_transform", "comparison"}:
            choreography["layout_mode"] = "split"
            choreography["split_transition_frame"] = emphasis_frame
            if scene_type == "comparison":
                choreography["comparison_footer"] = scene.get("comparison_footer") or COMPARISON_FOOTERS.get(active_domain, "KEY TAKEAWAY: Evaluating trade-offs across both analytical regimes")

        # 9. Diagram
        elif scene_type == "diagram":
            choreography["layout_mode"] = "stepped"
            nodes = scene.get("nodes") or []
            node_count = max(1, len(nodes))
            interval = max(10, (scene_end_frame - scene_start_frame) // (node_count + 1))
            choreography["step_activation_frames"] = [
                scene_start_frame + n_idx * interval for n_idx in range(node_count)
            ]

        # 10. Chemistry Reaction Mechanism
        elif scene_type in {"chemistry_reaction", "chemistry"}:
            choreography["layout_mode"] = "chemistry_reaction"
            chem_mode = sub_mode or detect_chemistry_mode(scene)
            if prev_visual_type in {"chemistry_reaction", "chemistry"} and chem_mode == prev_mode and not sub_mode:
                modes = ["sn2_concerted", "steric_blockade", "sn1_ionization", "sn1_racemic"]
                next_idx = (modes.index(chem_mode) + 1) % len(modes) if chem_mode in modes else 0
                chem_mode = modes[next_idx]
            scene["sub_mode"] = chem_mode
            scene["chemistry_mode"] = chem_mode

            chem_payload = synthesize_chemistry_payload(scene, chem_mode)
            for k, v in chem_payload.items():
                scene[k] = v

            phase1_end_frame = scene_start_frame + int((scene_end_frame - scene_start_frame) * 0.35)
            phase2_end_frame = scene_start_frame + int((scene_end_frame - scene_start_frame) * 0.70)
            phase3_end_frame = scene_end_frame

            choreography["chemistry"] = {
                "mode": chem_mode,
                "sub_mode": chem_mode,
                "phase1_end_frame": phase1_end_frame,
                "phase2_end_frame": phase2_end_frame,
                "phase3_end_frame": phase3_end_frame,
                "heat_applied": chem_payload.get("heat_applied", False),
                "temperature_kelvin": chem_payload.get("temperature_kelvin", 298),
                "activation_energy": chem_payload.get("energy_profile", {}).get("activation_energy", 65),
                "delta_g": chem_payload.get("energy_profile", {}).get("delta_g", -45),
            }

        # 11. Quantum Physics Simulation
        elif scene_type in {"quantum_sim", "quantum_physics"}:
            choreography["layout_mode"] = "quantum_sim"
            q_mode = sub_mode or detect_quantum_mode(scene)
            if prev_visual_type in {"quantum_sim", "quantum_physics"} and q_mode == prev_mode and not sub_mode:
                q_modes = ["schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"]
                next_q = (q_modes.index(q_mode) + 1) % len(q_modes) if q_mode in q_modes else 0
                q_mode = q_modes[next_q]
            scene["sub_mode"] = q_mode
            scene["quantum_mode"] = q_mode

            q_payload = synthesize_quantum_payload(scene, q_mode)
            for k, v in q_payload.items():
                scene[k] = v
            choreography["quantum"] = q_payload

        # 12. Advanced Mechanics FBD & Weight Distribution
        elif scene_type in {"mechanics_fbd", "mechanics"}:
            choreography["layout_mode"] = "mechanics_fbd"
            m_mode = sub_mode or detect_mechanics_mode(scene)
            if prev_visual_type in {"mechanics_fbd", "mechanics"} and m_mode == prev_mode and not sub_mode:
                m_modes = ["beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"]
                next_m = (m_modes.index(m_mode) + 1) % len(m_modes) if m_mode in m_modes else 0
                m_mode = m_modes[next_m]
            scene["sub_mode"] = m_mode
            scene["mechanics_mode"] = m_mode

            m_payload = synthesize_mechanics_payload(scene, m_mode)
            for k, v in m_payload.items():
                scene[k] = v
            choreography["mechanics"] = m_payload

        # 13. Electrical Circuits & Smart Grid
        elif scene_type in {"electrical_grid", "electrical"}:
            choreography["layout_mode"] = "electrical_grid"
            e_mode = sub_mode or detect_electrical_mode(scene)
            if prev_visual_type in {"electrical_grid", "electrical"} and e_mode == prev_mode and not sub_mode:
                e_modes = ["kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"]
                next_e = (e_modes.index(e_mode) + 1) % len(e_modes) if e_mode in e_modes else 0
                e_mode = e_modes[next_e]
            scene["sub_mode"] = e_mode
            scene["electrical_mode"] = e_mode

            e_payload = synthesize_electrical_payload(scene, e_mode)
            for k, v in e_payload.items():
                scene[k] = v
            choreography["electrical"] = e_payload

        # 11. Hero / Fullscreen Concept Takeaway
        else:
            choreography["layout_mode"] = "hero"
            choreography["hero_reveal_frame"] = scene_start_frame + 6

            spoken_lower = str(scene.get("spoken_text") or scene.get("narration") or "").lower()
            title_lower = str(scene.get("title") or scene.get("display_text", "")).lower()
            corpus = f"{spoken_lower} {title_lower}"

            is_non_ml = active_domain in ("math", "quantum_physics", "physics", "electrical", "mechanics", "chemistry")

            if not is_non_ml and any(k in corpus for k in ["autoencoder", "auto-encoder", "latent space", "bottleneck layer", "reconstruction loss"]):
                diagram_mode = "autoencoder"
                default_pts = [
                    "Compresses high-dimensional noise into low-dimensional manifold",
                    "Bottleneck layer forces network to extract semantic invariant features",
                    "Reconstruction loss guarantees zero information loss on key signals",
                ]
            elif not is_non_ml and (any(k in corpus for k in ["non-convex", "non convex", "break", "moon", "linear cut", "curved", "arena", "voronoi"]) or (
                "k-means" in corpus and "fail" in corpus
            )):
                diagram_mode = "arena"
                default_pts = [
                    "K-Means assumes spherical clusters and Euclidean convex geometry",
                    "Density-based clustering links contiguous points regardless of curvature",
                    "Non-linear manifolds require geodesic or density connectivity",
                ]
            elif not is_non_ml and any(k in corpus for k in ["compute", "waste", "gpu", "vram", "latency", "hardware", "cost", "hours"]):
                diagram_mode = "benchmark"
                default_pts = [
                    "Avoid burning GPU hours where classical algorithms converge in milliseconds",
                    "Memory footprint drops from gigabytes to single megabytes",
                    "Instant cold-start with zero heavy model weights to download or initialize",
                ]
            else:
                diagram_mode = "concept_card"
                card_payload = synthesize_concept_card(scene, domain=active_domain)
                default_pts = card_payload["points"]
                scene["concept_nodes"] = card_payload["concept_nodes"]
                choreography["concept_nodes"] = card_payload["concept_nodes"]

            if prev_visual_type == "concept" and diagram_mode == prev_mode:
                diagram_mode = "concept_card" if prev_mode != "concept_card" else "benchmark"

            scene["diagram_mode"] = diagram_mode
            choreography["diagram_mode"] = diagram_mode

            if not scene.get("points") and not scene.get("bullets"):
                scene["points"] = default_pts
                scene["bullets"] = default_pts
            if not scene.get("takeaways"):
                scene["takeaways"] = scene.get("points") or default_pts

        prev_visual_type = scene_type
        prev_mode = scene.get("diagram_mode") or scene.get("chemistry_mode") or scene.get("sim_type") or scene.get("mode") or scene.get("sub_mode")

        scene["choreography"] = choreography
        scene["theme"] = theme_id
        scene["palette"] = palette

        enriched_scenes.append(scene)

    # Phase 12 Anti-Repetition & Single Bento Guarantee Post-Pass:
    # 1. Bento Grid must appear AT MOST ONCE in the entire video, strictly on the final scene.
    # 2. Never allow identical visual_type + sub_mode consecutively.
    num_enriched = len(enriched_scenes)
    if num_enriched >= 5:
        for idx in range(num_enriched - 1):
            if enriched_scenes[idx].get("visual_type") == "bento_grid" or enriched_scenes[idx].get("scene_type") == "bento_grid":
                if active_domain == "electrical":
                    enriched_scenes[idx]["visual_type"] = "electrical_grid"
                    enriched_scenes[idx]["scene_type"] = "electrical_grid"
                    modes = ["kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"]
                    enriched_scenes[idx]["sub_mode"] = modes[idx % len(modes)]
                elif active_domain == "mechanics":
                    enriched_scenes[idx]["visual_type"] = "mechanics_fbd"
                    enriched_scenes[idx]["scene_type"] = "mechanics_fbd"
                    modes = ["beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"]
                    enriched_scenes[idx]["sub_mode"] = modes[idx % len(modes)]
                elif active_domain == "quantum_physics":
                    enriched_scenes[idx]["visual_type"] = "quantum_sim"
                    enriched_scenes[idx]["scene_type"] = "quantum_sim"
                    modes = ["schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"]
                    enriched_scenes[idx]["sub_mode"] = modes[idx % len(modes)]
                elif active_domain == "chemistry":
                    enriched_scenes[idx]["visual_type"] = "chemistry_reaction"
                    enriched_scenes[idx]["scene_type"] = "chemistry_reaction"
                    modes = ["sn2_concerted", "steric_blockade", "sn1_ionization", "sn1_racemic"]
                    enriched_scenes[idx]["sub_mode"] = modes[idx % len(modes)]
                else:
                    enriched_scenes[idx]["visual_type"] = "function_graph"
                    enriched_scenes[idx]["scene_type"] = "function_graph"

        if num_enriched >= 5 and enriched_scenes[-1].get("visual_type") != "bento_grid":
            enriched_scenes[-1]["visual_type"] = "bento_grid"
            enriched_scenes[-1]["scene_type"] = "bento_grid"
            enriched_scenes[-1]["layout_density"] = "full_dashboard"
            b_payload = synthesize_domain_bento_data(enriched_scenes[-1], active_domain)
            enriched_scenes[-1]["bento_data"] = b_payload
            enriched_scenes[-1]["cards"] = b_payload.get("cards", [])
            enriched_scenes[-1]["section_title"] = b_payload.get("section_title")
            enriched_scenes[-1]["subtitle"] = b_payload.get("subtitle")

    for idx in range(1, num_enriched):
        curr_v = enriched_scenes[idx].get("visual_type")
        prev_v = enriched_scenes[idx - 1].get("visual_type")
        curr_m = enriched_scenes[idx].get("sub_mode")
        prev_m = enriched_scenes[idx - 1].get("sub_mode")
        if curr_v == prev_v:
            if curr_v in {"electrical_grid", "mechanics_fbd", "quantum_sim", "chemistry_reaction"} and curr_m == prev_m:
                if curr_v == "electrical_grid":
                    modes = ["kvl_kcl_mesh", "thevenin_equivalence", "smart_grid_opf"]
                elif curr_v == "mechanics_fbd":
                    modes = ["beam_weight_distribution", "inclined_plane_fbd", "axle_center_of_mass"]
                elif curr_v == "quantum_sim":
                    modes = ["schrodinger_tunneling", "heisenberg_uncertainty", "dirac_atomic_orbitals"]
                else:
                    modes = ["sn2_concerted", "steric_blockade", "sn1_ionization", "sn1_racemic"]
                nxt_idx = (modes.index(curr_m) + 1) % len(modes) if curr_m in modes else 1
                enriched_scenes[idx]["sub_mode"] = modes[nxt_idx]
            elif curr_v not in {"electrical_grid", "mechanics_fbd", "quantum_sim", "chemistry_reaction"} and idx < num_enriched - 1:
                enriched_scenes[idx]["visual_type"] = "function_graph" if curr_v != "function_graph" else "math_equation"

    # Step 4: For STEM domains, ensure at least 50% of body scenes (3 to 5 scenes)
    # are assigned to use compiled Manim video layers
    if active_domain in ("math", "quantum_physics", "physics", "mechanics", "electrical"):
        body_indices = [
            i for i in range(1, num_enriched - (1 if num_enriched >= 5 else 0))
            if enriched_scenes[i].get("visual_type") in ("math_equation", "function_graph", "quantum_sim", "physics_sim", "electrical_grid", "mechanics_fbd", "manim_scene", "comparison")
        ]
        if not body_indices:
            body_indices = list(range(1, max(1, num_enriched - 1)))

        target_count = min(len(body_indices), max(3, int(round(len(body_indices) * 0.5))))
        for idx in body_indices[:target_count]:
            enriched_scenes[idx]["needs_manim"] = True

    return enriched_scenes
