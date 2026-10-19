import json
import os
import re
import time
from pathlib import Path
from google import genai
from google.genai import types

try:
    from engine.timeline.beats import calculate_target_scenes, merge_excess_scenes
except ImportError:
    from timeline.beats import calculate_target_scenes, merge_excess_scenes

DOMAINS = {"code", "devtools", "math", "physics", "systems", "ml", "chemistry", "quantum_physics", "mechanics", "electrical"}


def _read_env_file(path: Path) -> dict:
    env_vars = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k:
                        env_vars[k] = v
        except Exception:
            pass
    return env_vars


def _merge_env_at_startup():
    repo_dir = Path(__file__).resolve().parent.parent.parent
    for p in [Path.cwd() / ".env", repo_dir / ".env", repo_dir / "engine" / ".env"]:
        env_dict = _read_env_file(p)
        for var in ("GEMINI_API_KEY", "GEMINI_API_KEYS"):
            if var in env_dict:
                existing = os.environ.get(var, "")
                if existing:
                    merged = list(dict.fromkeys([k.strip() for k in existing.split(",") + env_dict[var].split(",") if k.strip()]))
                    os.environ[var] = ",".join(merged)
                else:
                    os.environ[var] = env_dict[var]


_merge_env_at_startup()


def get_api_keys():
    raw = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEYS", "")
    if not raw:
        _merge_env_at_startup()
        raw = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEYS", "")
    if not raw:
        raise KeyError("GEMINI_API_KEY environment variable is not set.")
    keys = []
    seen = set()
    for k in raw.split(","):
        k = k.strip()
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    return keys


_clients = {}


def _get_client(api_key):
    if api_key not in _clients:
        _clients[api_key] = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30000),
        )
    return _clients[api_key]


import pydantic
from typing import List, Optional, Dict, Any


class ScenePlanModel(pydantic.BaseModel):
    scene_id: int
    title: str
    spoken_text: str
    visual_type: str
    display_text: Optional[str] = None
    emphasis_word: Optional[str] = None
    sub_mode: Optional[str] = None
    formula: Optional[str] = None
    latex: Optional[str] = None
    functions: Optional[List[str]] = None
    curves: Optional[List[str]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    equations: Optional[List[Dict[str, Any]]] = None
    problem_code: Optional[str] = None
    solution_code: Optional[str] = None
    problem_label: Optional[str] = None
    solution_label: Optional[str] = None
    manim_spec: Optional[Dict[str, Any]] = None
    # DevTool Primitives Fields (Phase A)
    code: Optional[str] = None
    code_snippet: Optional[str] = None
    filename: Optional[str] = None
    language: Optional[str] = None
    highlight_lines: Optional[List[int]] = None
    focus_phrase: Optional[str] = None
    before_code: Optional[str] = None
    after_code: Optional[str] = None
    before_label: Optional[str] = None
    after_label: Optional[str] = None
    commands: Optional[List[Dict[str, Any]]] = None
    nodes: Optional[List[str]] = None
    request_payload: Optional[str] = None
    response_payload: Optional[str] = None
    request_method: Optional[str] = None
    response_status: Optional[str] = None
    comparison_footer: Optional[str] = None


class DirectorScriptPlanModel(pydantic.BaseModel):
    topic: str
    title: str
    subject: str
    duration: float
    scenes: List[ScenePlanModel]


# GEMINI_MODEL can be a single model or a comma-separated fallback chain,
# e.g. GEMINI_MODEL="gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash,gemini-2.5-flash,gemini-2.0-flash,gemini-2.5-pro"
# Active verified v1beta models discovered via client.models.list()
DEFAULT_MODEL_CHAIN = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
]


def detect_domain(topic: str) -> str:
    """
    Auto-detects whether a topic belongs to 'code', 'math', 'physics', 'systems', 'ml',
    'chemistry', 'quantum_physics', 'mechanics', or 'electrical'.
    """
    t = (topic or "").lower()

    quantum_kw = [
        "quantum", "schrodinger", "wavefunction", "wave packet", "wavepacket",
        "tunneling", "quantum tunneling", "heisenberg", "uncertainty principle",
        "dirac", "dirac equation", "spinor", "atomic orbital", "atomic orbitals",
        "orbital probability", "quantum numbers", "superposition", "commutator",
        "commutation relation", "evanescent", "planck"
    ]
    mechanics_kw = [
        "mechanics", "beam", "weight distribution", "load distribution",
        "shear force", "bending moment", "inclined plane", "ramp", "friction threshold",
        "axle", "center of mass", "center of gravity", "load transfer",
        "torque equilibrium", "statics", "truss", "roller support", "pin support"
    ]
    electrical_kw = [
        "circuit", "kvl", "kcl", "kirchhoff", "thevenin", "thevenin equivalence",
        "norton", "mesh analysis", "nodal analysis", "smart grid", "power flow",
        "optimal power flow", "economic dispatch", "transmission line", "substation",
        "transformer", "duck curve", "peak shaving", "bus admittance", "grid optimization"
    ]
    chemistry_kw = [
        "chemistry", "organic chemistry", "molecule", "reaction", "bond", "covalent",
        "sn1", "sn2", "nucleophile", "electrophile", "leaving group", "alkene", "alkyne",
        "carbocation", "acid", "base", "enthalpy", "exothermic", "endothermic", "catalysis",
        "catalyst", "activation energy", "transition state", "stereochemistry", "chirality",
        "walden inversion", "substitution", "redox", "oxidation", "reduction", "equilibrium",
        "hydration", "markovnikov", "mechanism", "hybridization", "resonance"
    ]
    ml_kw = [
        "machine learning", "deep learning", "neural network", "neural net", "unsupervised",
        "supervised", "clustering", "kmeans", "k-means", "dbscan", "pca", "t-sne", "tsne",
        "dendrogram", "loss function", "backpropagation", "backprop", "epoch", "classifier",
        "classification", "regression", "reinforcement learning", "random forest",
        "gradient descent", "transformer", "llm", "embedding", "data science", "latent space",
        "overfitting", "underfitting", "convolutional", "cnn", "rnn"
    ]
    math_kw = [
        "calculus", "derivative", "integral", "matrix", "linear algebra", "eigen",
        "equation", "theorem", "euler", "pythagor", "geometry", "probability",
        "statistics", "fibonacci", "fourier", "trigonometry", "logarithm", "limit",
        "algebra", "polynomial", "prime number", "differential", "sine", "cosine", "math"
    ]
    physics_kw = [
        "physics", "force", "gravity", "velocity", "acceleration", "newton",
        "kinetic", "potential", "friction", "momentum", "energy",
        "relativity", "wave", "harmonic", "oscillation", "electromagnet",
        "thermodynamics", "projectile", "trajectory", "mass", "centripetal", "optics"
    ]
    systems_kw = [
        "distributed system", "kafka", "raft", "database", "caching", "microservice",
        "concurrency", "thread", "process", "deadlock", "networking", "tcp", "udp",
        "load balancer", "paxos", "consensus", "system design", "sharding", "replication"
    ]
    devtools_kw = [
        "sdk", "api", "cli", "devtools", "endpoint", "changelog", "migration",
        "npm install", "pip install", "request", "response", "webhook", "rest api",
        "sdk release", "b2b", "developer tool", "v1 to v2", "v2 sdk"
    ]

    for kw in devtools_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "devtools"
    for kw in quantum_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "quantum_physics"
    for kw in mechanics_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "mechanics"
    for kw in electrical_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "electrical"
    for kw in chemistry_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "chemistry"
    for kw in ml_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "ml"
    for kw in math_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "math"
    for kw in physics_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "physics"
    for kw in systems_kw:
        if re.search(rf"\b{re.escape(kw)}", t):
            return "systems"

    return "code"


def _is_404_error(exc: Exception) -> bool:
    """Detects 404 Not Found / Model Not Found client errors."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 404:
        return True
    msg = str(exc).lower()
    return "404" in msg or "not_found" in msg or "not found" in msg


def _is_invalid_key_error(exc: Exception) -> bool:
    """Detects invalid API key errors (e.g. API_KEY_INVALID, 400 Bad Request on key)."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    msg = str(exc).lower()
    return (
        (code == 400 and any(k in msg for k in ["key", "api_key", "invalid", "credential"]))
        or "api_key_invalid" in msg
        or "api key not valid" in msg
        or "invalid api key" in msg
        or "api key expired" in msg
        or ("permission_denied" in msg and "api_key" in msg)
    )


def get_model_chain():
    raw = os.getenv("GEMINI_MODEL", "").strip()
    if not raw:
        return DEFAULT_MODEL_CHAIN
    models = [m.strip() for m in raw.split(",") if m.strip()]
    return models or DEFAULT_MODEL_CHAIN


def get_system_prompt(duration, subject="code"):
    try:
        dur_val = float(duration)
    except (TypeError, ValueError):
        dur_val = 35.0

    target_scenes = calculate_target_scenes(dur_val)
    target_words = int(round(dur_val * 2.25))
    words_per_scene = int(round(target_words / target_scenes))

    if dur_val >= 50:
        min_words_per_scene = 11
        max_words_per_scene = 18
        target_words_min = 120
        target_words_max = 150
        density_instruction = (
            f"SCENE NARRATION DENSITY (MANDATORY FOR 60s): Each scene's \"spoken_text\" MUST contain between "
            f"{min_words_per_scene} and {max_words_per_scene} words (aim for {words_per_scene} words per scene across "
            f"two rich, informative sentences). Never output fewer than {min_words_per_scene} words in any scene. "
            f"The entire script MUST total between {target_words_min} and {target_words_max} spoken words so the spoken narration fills the full 60 seconds."
        )
    else:
        min_words_per_scene = 5
        max_words_per_scene = 11
        target_words_min = max(30, target_words - 15)
        target_words_max = target_words + 15
        density_instruction = (
            f"STRICT WORD LIMIT PER BEAT: Each \"spoken_text\" MUST be between {min_words_per_scene} and "
            f"{max_words_per_scene} words maximum. Never exceed {max_words_per_scene} words in a single beat."
        )

    target_beats = f"STRICTLY {target_scenes} scenes (no more, no less)"
    word_limit = (
        f"Total spoken words across the entire script: between {target_words_min} and {target_words_max} words total "
        f"(target ~{target_words} words across {target_scenes} scenes for a {int(dur_val)}s video)."
    )

    if subject == "math":
        domain_desc = "educational short on Mathematics, Calculus, and Applied Geometry"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact hook, reset, or core theorem. Uses "display_text".
- "math_equation": Step-by-step mathematical derivation. Uses "steps" (list of step objects or strings, e.g. [{"formula": "E = mc^2", "explanation": "Mass-energy equivalence"}]) or "equations".
- "function_graph": Animated 2D coordinate plot. Uses "functions": [{"fn": "x^2", "label": "f(x) = x^2"}], "x_domain": [-5, 5], "y_domain": [0, 25], "x_label": "x", "y_label": "f(x)".
- "diagram": Conceptual flowchart or proof map. Uses "nodes" (2-3 items max).
- "concept": High-impact hero takeaway card. Uses "display_text"."""
        extra_rules = """7. MATH INTEGRITY: Every "math_equation" MUST include non-empty formula strings. For "function_graph", provide clean x_domain, y_domain, and curve labels."""

    elif subject == "physics":
        domain_desc = "educational short on Classical Mechanics, Kinematics, Waves, and Physical Systems"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact hook or physical principle. Uses "display_text".
- "physics_sim": Deterministic physics diagram/simulation. Uses "sim_type" ("forces" | "projectile" | "wave"), "forces": [{"name": "F_g", "direction": 270, "magnitude": 9.8}], "objects": [{"name": "block", "mass": 5}], "trajectory": {"v0": 20, "angle": 45}.
- "function_graph": Kinematic curve or harmonic oscillation plot. Uses "functions", "x_domain", "y_domain", "x_label", "y_label".
- "math_equation": Physical law derivation (e.g., F = ma). Uses "steps" or "equations".
- "diagram": Conceptual flow or energy state breakdown. Uses "nodes" (2-3 items max)."""
        extra_rules = """7. PHYSICS INTEGRITY: For "physics_sim", specify valid vector arrows, forces, or trajectory parameters."""

    elif subject == "systems":
        domain_desc = "educational short on Distributed Systems, Software Architecture, and Concurrency"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact architectural hook or concept punch. Uses "display_text".
- "diagram": Architecture flow or protocol state machine. Uses "nodes" (2-3 items max).
- "comparison": Architectural trade-off (e.g. Sync vs Async, SQL vs NoSQL). Uses "problem_label", "problem_code", "solution_label", "solution_code".
- "code_reveal": Architecture implementation or configuration snippet. Uses "code_snippet".
- "concept": High-impact takeaway card. Uses "display_text"."""
        extra_rules = """7. SYSTEMS INTEGRITY: Diagrams must have clean, clear nodes (2-3 max). Comparisons must clearly contrast problem vs solution architecture."""

    elif subject == "ml":
        domain_desc = "educational short on Machine Learning, Deep Learning, and Data Science Algorithms"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact editorial hook, reset, or core thesis. Uses "display_text".
- "bento_grid": High-retention editorial 2-column bento overview of algorithms. Uses "section_title" (e.g. "UNSUPERVISED ML ALGORITHMS"), "subtitle" (e.g. "YOU NEED TO KNOW"), and "cards" (list of card objects with "title", "algo_type" ["kmeans"|"dbscan"|"pca"|"dendrogram"|"tsne"], "category" ["CLUSTERING"|"DIMENSIONALITY REDUCTION"], "description").
- "algorithm_explorer": 3-tier deep-dive interactive visual simulation. Uses "algorithm" ("dbscan"|"kmeans"|"pca"), "parameters" (e.g. {"epsilon": "0.4 radius", "min_pts": "4 points"}), "point_types" (e.g. {"core": "Density reachable", "border": "Within epsilon", "noise": "Outlier"}).
- "neural_code_split": Vertical split visualizer + live code layout. Uses "model_name" ("Neural Network"), "subtitle" ("FROM SCRATCH"), "code_snippet" (clean Python code for forward/backprop), "layers": [8, 16, 10], "focus_phrase".
- "concept": High-impact hero takeaway card. Uses "display_text"."""
        extra_rules = """7. ML INTEGRITY: For "bento_grid", provide 2 to 4 structured algorithm cards. For "algorithm_explorer", specify valid algorithm and parameters. For "neural_code_split", "code_snippet" MUST be valid Python code."""

    elif subject == "chemistry":
        domain_desc = "educational short on Chemistry, Organic Reaction Mechanisms, and Molecular Dynamics"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact chemical curiosity hook or fundamental principle. Uses "display_text".
- "chemistry_reaction": Interactive 2D molecular structures and mechanism visualizer. Uses:
    "reaction_name": (e.g. "SN2 Substitution"),
    "mode": ("sn2_substitution" | "sn1_carbocation" | "addition_alkene" | "redox_combustion" | "acid_base"),
    "thermodynamic_badge": ("EXOTHERMIC" | "ENDOTHERMIC" | "CONCERTED MECHANISM" | "CATALYZED"),
    "heat_applied": (true | false - triggers rising heat wave particles and temperature HUD),
    "temperature_kelvin": 355,
    "reagents": "NaOH • Acetone (Polar Aprotic)",
    "rate_law": "Rate = k[R-X][Nu-]",
    "stereochemistry": "Walden Inversion (100% Inversion)",
    "energy_profile": {"activation_energy": 75, "delta_g": -45, "transition_state": "[Nu...C...X]‡"}.
- "comparison": Mechanistic comparison (e.g. SN1 vs SN2 or Polar Protic vs Polar Aprotic). Uses "problem_label", "problem_code", "solution_label", "solution_code".
- "diagram": Reaction coordinate pathway or catalytic cycle. Uses "nodes" (2-3 items max).
- "concept": High-impact chemical takeaway card. Uses "display_text"."""
        extra_rules = """7. CHEMISTRY INTEGRITY: For "chemistry_reaction", specify valid "reaction_name", "mode", "thermodynamic_badge", and "rate_law"."""

    elif subject == "quantum_physics":
        domain_desc = "educational short on Quantum Mechanics, Wave-Particle Duality, and Relativistic Spinors"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact quantum paradox hook or foundational postulate. Uses "display_text".
- "quantum_sim": Interactive quantum physics simulation. Uses "sub_mode" ("schrodinger_tunneling" | "heisenberg_uncertainty" | "dirac_atomic_orbitals"), "barrier_height_ev", "particle_energy_ev", "transmission_coefficient", "quantum_numbers": {"n": 2, "l": 1, "m_l": 0, "m_s": "+1/2"}.
- "math_equation": Quantum wave equations, commutators, or uncertainty relations. Uses "steps" or "equations".
- "comparison": Classical vs Quantum contrasting principles (e.g. Determinism vs Probabilistic Wavepacket). Uses "problem_label", "problem_code", "solution_label", "solution_code".
- "concept": High-impact hero takeaway card. Uses "display_text"."""
        extra_rules = """7. QUANTUM INTEGRITY: For "quantum_sim", specify valid sub_mode ("schrodinger_tunneling", "heisenberg_uncertainty", or "dirac_atomic_orbitals")."""

    elif subject == "mechanics":
        domain_desc = "educational short on Advanced Mechanics, Weight Distribution, and Structural Statics"
        beat_types = r"""AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact engineering hook or equilibrium principle. Uses "display_text".
- "mechanics_fbd": Step-by-step free-body diagram and equilibrium solver. Uses "sub_mode" ("beam_weight_distribution" | "inclined_plane_fbd" | "axle_center_of_mass"), "beam_length_m", "point_load_kn", "ramp_angle_deg", "friction_coeff", "wheelbase_m".
- "math_equation": Statics and torque equilibrium derivations (e.g. \Sigma F = 0, \Sigma \tau = 0). Uses "steps" or "equations".
- "comparison": Static vs Dynamic load distribution or friction regimes. Uses "problem_label", "problem_code", "solution_label", "solution_code".
- "concept": High-impact engineering takeaway card. Uses "display_text"."""
        extra_rules = """7. MECHANICS INTEGRITY: For "mechanics_fbd", specify valid sub_mode ("beam_weight_distribution", "inclined_plane_fbd", or "axle_center_of_mass")."""

    elif subject == "electrical":
        domain_desc = "educational short on Electrical Engineering, Circuit Theorems, and Smart Grid Optimization"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact circuit paradox or power grid telemetry hook. Uses "display_text".
- "electrical_grid": Interactive circuit schematic, Thévenin reduction, or multi-bus power grid solver. Uses "sub_mode" ("kvl_kcl_mesh" | "thevenin_equivalence" | "smart_grid_opf"), "voltage_v", "resistors_ohms", "grid_buses", "thermal_load_pct", "transmission_lines".
- "math_equation": Circuit equations, Kirchhoff loop laws, or Equal Incremental Cost. Uses "steps" or "equations".
- "comparison": Thévenin vs Norton, or AC vs DC power transmission trade-offs. Uses "problem_label", "problem_code", "solution_label", "solution_code".
- "concept": High-impact electrical takeaway card. Uses "display_text"."""
        extra_rules = """7. ELECTRICAL INTEGRITY: For "electrical_grid", specify valid sub_mode ("kvl_kcl_mesh", "thevenin_equivalence", or "smart_grid_opf")."""

    elif subject == "devtools":
        domain_desc = "code-first B2B developer-tool video (SDK release, API flow, CLI workflow, or code migration)"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact hook or release headline. Uses "display_text".
- "terminal": Authentic dark terminal CLI command and output simulator. Uses "commands" (list of {"cmd": "npm install @acme/sdk@latest", "output": ["+ @acme/sdk@2.0.0", "added 1 package in 140ms"], "status": "✓ Built in 140ms"}) or "code_snippet".
- "code_transform": Before -> After code diff showing dramatic lines-of-code reduction and modern SDK migration. Uses "before_code", "after_code", "before_label" (e.g. "Legacy v1 (28 lines)"), "after_label" (e.g. "New v2 SDK (4 lines)").
- "code_reveal": Core SDK code snippet with progressive line spotlight. Uses "code_snippet" (or "code"), "filename" (e.g. "agent.ts"), "language" (e.g. "typescript"), "highlight_lines" (list of line numbers to spotlight e.g. [5, 6]), and optional "focus_phrase".
- "diagram": Architecture and API request/response flow. Uses "nodes" (2-3 connected nodes e.g. ["Client SDK", "Edge Gateway", "Vector DB"]), "request_method", "request_payload", "response_status", "response_payload".
- "comparison": Performance, latency, or lines-of-code takeaway card. Uses "problem_label", "problem_code", "solution_label", "solution_code", "comparison_footer"."""
        extra_rules = """7. DEVTOOL ACCURACY CONTRACT: When source material (README, changelog, code snippet, API doc) is provided, preserve exact function names, CLI commands, imports, types, method calls, and JSON keys from the source material. Never invent fake or hallucinated SDK methods."""

    else:  # code (default)
        domain_desc = "high-retention Python educational short"
        beat_types = """AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact hook, reset, or single concept punch. Uses "display_text".
- "code_reveal": Introduces a new code block. Uses "code_snippet" and optional "focus_phrase" (exact substring to highlight).
- "code_transform": Updates/modifies code. Uses "code_snippet" and optional "focus_phrase".
- "terminal": Command line run or traceback output. Uses "code_snippet".
- "diagram": Conceptual flow using nodes. Uses "nodes" (2-3 items max).
- "comparison": Side-by-side / top-bottom fix. Uses "problem_label", "problem_code", "solution_label", "solution_code"."""
        extra_rules = """7. CODE VALIDATION: Every "code_snippet" MUST parse as valid Python syntax. If revealing a partial function or loop, you MUST include "pass" or "..." to prevent IndentationErrors."""

    return f"""You are the director and scriptwriter for a {domain_desc}.
Your job is to architect the video by mapping the spoken script to rapid semantic visual beats.

{beat_types}

OUTPUT FORMAT: Strict JSON only matching this skeleton:
{{
  "title": "Short topic",
  "subject": "{subject}",
  "schema_version": "2.1",
  "scenes": [
    {{
      "scene_type": "fullscreen_text",
      "spoken_text": "This mistake will ruin your results.",
      "display_text": "THIS WILL RUIN YOUR RESULTS",
      "emphasis_word": "ruin"
    }}
  ]
}}

EDITORIAL INTELLIGENCE RULES:
1. TARGET BEATS: Generate {target_beats}.
2. {word_limit}
3. {density_instruction}
4. Scene 1 MUST be "fullscreen_text" with a curiosity gap hook.
5. Pacing: Never linger. The final takeaway beat must be punchy and decisive.
6. Write naturally for text-to-speech.
{extra_rules}
"""


def _call_model(client, model, contents, prompt, max_retries=2):
    """
    Calls one model with a strict 30s timeout and fast 1s, 2s max backoff.
    Raises immediately (no retry) on 429/RESOURCE_EXHAUSTED or 404/NOT_FOUND so the caller
    can fall through to the next model right away.
    """
    last_err = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    response_mime_type="application/json",
                    response_schema=DirectorScriptPlanModel,
                    http_options=types.HttpOptions(timeout=30000),
                ),
            )
            raw_text = response.text.strip()
            # Strip markdown code fences if the model wrapped them
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text,
                              flags=re.MULTILINE | re.IGNORECASE)
            raw_text = re.sub(r"```\s*$", "", raw_text,
                              flags=re.MULTILINE).strip()
            # Extract first outer JSON object if extra text slipped in
            match = re.search(r"(\{.*\})", raw_text, flags=re.DOTALL)
            if match:
                raw_text = match.group(1)
            return json.loads(raw_text)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                raise  # quota issue — don't waste retries on the same model
            if _is_404_error(e):
                raise  # model not found / 404 — don't waste retries on the same model
            if _is_invalid_key_error(e):
                raise  # invalid API key — don't waste retries
            last_err = e
            is_timeout_or_stall = any(
                k in msg.lower() for k in ("timeout", "timed out", "deadline", "ssl", "readtimeout", "connecterror")
            ) or isinstance(e, (TimeoutError, OSError))
            is_503 = "503" in msg or "UNAVAILABLE" in msg

            if (is_503 or is_timeout_or_stall) and attempt + 1 < max_retries:
                wait = min(2, attempt + 1)  # 1s on attempt 0, 2s max on attempt 1
                print(
                    f"[DIRECTOR:RETRY] ⚠️ {model} transient error ({type(e).__name__}), retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue
            raise
    raise last_err


def generate_script(topic, duration, subject="auto", source_text=None, source_facts=None):
    """Generates the script using Gemini, walking a fallback chain of
    (API key × model) combinations.
    """
    if not subject or subject == "auto":
        subject = detect_domain(topic)

    prompt = get_system_prompt(duration, subject=subject)

    if subject == "devtools":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Create a 6-scene B2B developer tool video: "
            f"Scene 1 'fullscreen_text' (hook) -> Scene 2 'terminal' (CLI install) -> Scene 3 'code_transform' (v1 to v2 migration) -> "
            f"Scene 4 'code_reveal' (SDK spotlight) -> Scene 5 'diagram' (API request/response flow) -> Scene 6 'comparison' (benchmark/DX takeaway)."
        )
    elif subject == "math":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text' (hook). "
            f"Include at least one 'math_equation' derivation scene and optionally 'function_graph'."
        )
    elif subject == "physics":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text' (hook). "
            f"Include at least one 'physics_sim' visualization scene."
        )
    elif subject == "systems":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text' (hook). "
            f"Include at least one 'diagram' or 'comparison' scene."
        )
    elif subject == "ml":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text' (hook). "
            f"Include at least one 'bento_grid', 'algorithm_explorer', or 'neural_code_split' scene."
        )
    elif subject == "chemistry":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text' (hook). "
            f"Rotate visual types across scenes: include 'comparison' (SN1 vs SN2 contrast), "
            f"'chemistry_reaction' (mechanisms), 'function_graph' (energy profile), and 'bento_grid' (summary cheat-sheet)."
        )
    elif subject == "electrical":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text' (hook). "
            f"Include 'comparison' (Thévenin vs Norton / Mesh vs Nodal), 'electrical_grid' (circuits / OPF power flow), "
            f"'function_graph' (maximum power transfer curve), and 'bento_grid' (final summary sheet)."
        )
    elif subject == "mechanics":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text' (hook). "
            f"Include 'comparison' (Static vs Dynamic equilibrium), 'mechanics_fbd' (free-body diagrams / beam load), "
            f"'function_graph' (shear and moment diagram), and 'bento_grid' (final statics cheat sheet)."
        )
    elif subject == "quantum_physics":
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text' (hook). "
            f"Include 'comparison' (Classical vs Quantum observables), 'quantum_sim' (wavepacket tunneling / uncertainty), "
            f"'function_graph' (barrier penetration decay), and 'bento_grid' (quantum operator cheat sheet)."
        )
    else:  # code
        contents = (
            f"Topic: {topic}. Domain: {subject}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text'. "
            f"You MUST also include at least one 'comparison' scene."
        )

    if source_text and source_text.strip():
        contents += (
            f"\n\nSOURCE DOCUMENTATION / CODE MATERIAL:\n{source_text.strip()}\n\n"
            f"STRICT ACCURACY CONTRACT: Preserve exact function names, CLI commands, imports, types, "
            f"and JSON response keys from the source material above. Never invent fake or hallucinated SDK methods."
        )

    if source_facts:
        p_name = source_facts.get("product_name") or ""
        cmds = source_facts.get("cli_commands") or []
        endpoints = source_facts.get("api_endpoints") or []
        points = source_facts.get("key_points") or []
        facts_summary = f"PRODUCT NAME: {p_name}\n"
        if cmds:
            facts_summary += f"CLI COMMANDS: {', '.join(cmds)}\n"
        if endpoints:
            facts_summary += f"API ENDPOINTS: {', '.join(endpoints)}\n"
        if points:
            facts_summary += f"KEY BENCHMARKS: {'; '.join(points[:4])}\n"

        contents += (
            f"\n\nCUSTOMER GROUND-TRUTH EXTRACTED FACTS:\n{facts_summary}\n"
            f"STRICT COMPONENT CONTRACT: When generating visual scenes, you MUST inject the exact "
            f"CLI commands into the terminal scene, the exact API endpoints into diagram scenes, "
            f"and the exact code snippets from the source documentation into code_reveal / code_transform scenes."
        )

    keys = get_api_keys()
    model_chain = get_model_chain()
    last_err = None

    for key_index, api_key in enumerate(keys):
        client = _get_client(api_key)
        key_label = f"key #{key_index + 1}/{len(keys)}"

        for i, model in enumerate(model_chain):
            try:
                print(
                    f"[DIRECTOR:INFO] 🤖 Trying {model} on {key_label} ({i + 1}/{len(model_chain)})")
                script_obj = _call_model(client, model, contents, prompt)
                if isinstance(script_obj, dict):
                    if "subject" not in script_obj:
                        script_obj["subject"] = subject
                    target_scenes = calculate_target_scenes(duration)
                    if "scenes" in script_obj and isinstance(script_obj["scenes"], list):
                        if len(script_obj["scenes"]) > target_scenes + 1:
                            script_obj["scenes"] = merge_excess_scenes(script_obj["scenes"], target_scenes=target_scenes)
                return script_obj
            except Exception as e:
                last_err = e
                msg = str(e)
                if _is_invalid_key_error(e):
                    print(
                        f"[DIRECTOR:WARN] ⚠️ Invalid API key on {key_label} (API_KEY_INVALID), skipping remaining models on this key...")
                    break
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                    print(
                        f"[DIRECTOR:WARN] ⚠️ {model} quota exhausted on {key_label}, trying next model...")
                    continue
                if _is_404_error(e):
                    print(
                        f"[DIRECTOR:WARN] ⚠️ {model} not found / unsupported (404) on {key_label}, trying next model in chain...")
                    continue
                if "503" in msg or "UNAVAILABLE" in msg:
                    print(
                        f"[DIRECTOR:WARN] ⚠️ {model} still unavailable after retries on {key_label}, trying next model...")
                    continue
                if any(k in msg.lower() for k in ("timeout", "timed out", "deadline", "ssl", "readtimeout", "connecterror")) or isinstance(e, (TimeoutError, OSError)):
                    print(
                        f"[DIRECTOR:WARN] ⚠️ {model} timed out / stalled on {key_label}, jumping to next model in chain...")
                    continue
                print(
                    f"[DIRECTOR:WARN] ⚠️ {model} failed on {key_label} ({type(e).__name__}: {msg[:100]}), trying next model in chain...")
                continue

        print(f"[DIRECTOR:WARN] ⚠️ All models exhausted on {key_label}.")
        if key_index + 1 < len(keys):
            print(
                "[DIRECTOR:INFO] 🔁 Switching to next API key (separate project quota)...")

    raise RuntimeError(
        f"All {len(keys)} key(s) × {len(model_chain)} model(s) exhausted or failed. "
        f"Last error: {last_err}"
    )
