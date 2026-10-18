# Agent Instructions: Video Pipeline Engine — Phase 13 Final Production Lock (Zero Hardcoded Math/Bento Artifacts & Clean Graph Layout)

You are an expert systems and audio/video pipeline software engineer.
Your objective is to eliminate the final 4 visual artifacts identified in our 60-second production review so the pipeline can reliably batch-produce ready-to-post videos across all subjects over the coming weeks.

---

## 1. Four Final Production Fixes (Must Execute Together)

### Fix 1: Purge Hardcoded `"Euler's Identity"` & Imaginary Unit Text from `MathScene.jsx` & `choreographer.py`
- **Bug Observed (`00:48–00:50`)**: When `MathScene.jsx` rendered during an Electrical Engineering scene (*"Automated optimal dispatch protects transmission lines..."*), it displayed a hardcoded title `"Euler's identity"`, generic steps `"f(x) = y"`, and a hardcoded footer `"Multiplication by imaginary unit i represents a pure 90° rotation... Constants Linked: e, i, π, 1, 0"`.
- **Mandatory Fix**:
  1. Never fall back to `"Euler's identity"`, `"EULER DERIVATION STUDIO"`, or the imaginary unit $i$ paragraph in `MathScene.jsx` or `choreographer.py`!
  2. Use `scene.title` as the card title, use the domain eyebrow (`subject.upper() + " • MATHEMATICAL FORMULATION"`), and populate domain-specific derivation steps & intuition footers when `scene.steps` are generic or missing:
     - **`electrical`**:
       - Step 1: $\sum_{i} P_{Gi} = P_{\text{load}} + P_{\text{loss}}$ (Active Power Balance Constraint)
       - Step 2: $\frac{\partial C_i}{\partial P_{Gi}} = \lambda \quad \text{subject to } |S_{ij}| \le S_{ij,\max}$ (Thermal Line Limit & Economic Dispatch)
       - Intuition Footer: `Lagrangian optimization dispatches lowest-cost generators while clamping branch currents below thermal sag thresholds.`
     - **`mechanics`**:
       - Step 1: $\sum F_x = 0, \quad \sum F_y = R_A + R_B - \sum W_i = 0$ (Translational Static Equilibrium)
       - Step 2: $\sum \tau_A = R_B \cdot L - \sum (W_i \cdot x_i) = 0 \implies M(x) = \int V(x)\,dx$ (Rotational Moment Balance)
       - Intuition Footer: `Internal shear and bending moments peak where reaction forces balance concentrated structural loads.`
     - **`quantum_physics`**:
       - Step 1: $\hat{H}\Psi = E\Psi \implies \kappa = \frac{\sqrt{2m(V_0 - E)}}{\hbar}$ (Wavefunction Attenuation Constant)
       - Step 2: $T \approx e^{-2\kappa L}, \quad \sigma_x \sigma_p \ge \frac{\hbar}{2}$ (Barrier Transmission & Phase-Space Bound)
       - Intuition Footer: `Non-zero probability amplitude inside classically forbidden barriers enables quantum tunneling.`
     - **`chemistry`**:
       - Step 1: $\text{Rate}_{S_N2} = k[\text{R-X}][\text{Nu}^-], \quad \text{Rate}_{S_N1} = k[\text{R-X}]$ (Kinetic Order Law)
       - Step 2: $k = A e^{-E_a / RT}, \quad \Delta G^\ddagger = \Delta H^\ddagger - T\Delta S^\ddagger$ (Eyring-Arrhenius Activation Barrier)
       - Intuition Footer: `Activation energy height dictates reaction rate; steric hindrance raises the concerted transition state barrier.`
     - **`math` / `physics` / `code` / `ml`**: Derive steps and intuition directly from `scene.narration` and `scene.title`.

### Fix 2: Distinct Mini-SVGs Inside `BentoGridScene.jsx` & Stop Holding `bento_grid` for the Last 3 Scenes (`00:51–01:07`)
- **Bug Observed (`00:51–01:07`)**:
  1. The last 2–3 scenes of the video (`00:51–01:07`, 16 seconds straight) still rendered `BentoGridScene` back-to-back.
  2. Inside `BentoGridScene.jsx`, all 4 cards (`KVL & KCL`, `Thévenin / Norton`, `Max Power`, `Smart Grid OPF`) rendered the **exact same 3 dotted circles (`t-SNE` fallback graphic)**!
- **Mandatory Fix**:
  1. In `choreographer.py`, verify why scenes after index 8 routed to `bento_grid`: strictly enforce that **ONLY the final scene (`i == len(scenes) - 1`)** can have `visual_type == "bento_grid"`. If `len(scenes)` is 10 or 11, scenes `7, 8, 9` MUST route to distinct visual types (e.g., `electrical_grid` sub-modes, `comparison`, `function_graph`, `math_equation`) and NEVER `bento_grid`!
  2. In `BentoGridScene.jsx`, render **4 visually distinct mini-SVG graphics** based on card index (`0, 1, 2, 3`) or card type when custom mini-SVGs aren't ML clustering:
     - Card 0: Animated Node/Network Loop or Vector Diagram SVG.
     - Card 1: Animated Dual-Terminal / Wave / Equilibrium Balance SVG.
     - Card 2: Animated Rising Peak Curve / Energy Barrier SVG.
     - Card 3: Animated 4-Node Grid / Matrix Topology SVG.
     - Never render the 3 `t-SNE` dotted rings in all 4 boxes!

### Fix 3: Fix Legend Overlapping Y-Axis Title in `GraphScene.jsx` (`00:29–00:34`)
- **Bug Observed (`00:29`)**: In `GraphScene.jsx`, the top-right legend box overlaps the centered Y-axis header text `Power P_L (W) / Cost ($/MWh)`.
- **Mandatory Fix**:
  - Left-align the Y-axis label at `x = 90, y = 55` (`textAnchor="start"`) OR move the legend box down/right (`x = 560, y = 80`) and keep the Y-axis title at `x = 100, y = 48` so the legend box NEVER collides with the axis title text.

### Fix 4: Clean Up Bottom Takeaway Box in `comparison` Cards (`CodingShort.jsx` & `choreographer.py`)
- **Bug Observed (`00:00–00:04`)**: The bottom green box in Scene 1 displays: `NETWORK EQUIVALENCE: Linear network reduction simplifies multi-bus OPF solver complexity by 100x | NETWORK EQUIVALENCE: V_th = V_oc, R_th = V_oc / I_sc | POWER FLOW: ΣP_gen = ΣP_load + P_loss` (repeating the exact strings already shown in the two boxes directly above it)!
- **Mandatory Fix**:
  - In `CodingShort.jsx` (and `choreographer.py`), strip any `| NETWORK EQUIVALENCE:...` suffix from the bottom green summary bar so it ONLY displays the clean 1-sentence takeaway (`KEY TAKEAWAY: Linear network reduction simplifies multi-bus OPF solver complexity by 100x`).

---

## 2. Verification & Testing
- Add unit tests in Python and Node verifying:
  - `MathScene.jsx` and `choreographer.py` never output `"Euler's identity"` or `"Multiplication by imaginary unit"` unless the topic explicitly mentions Euler.
  - On an 11-scene script, `choreographer.py` assigns `bento_grid` to **at most 1 scene** (`scenes[-1]`), and `scenes[-2]` / `scenes[-3]` are NOT `bento_grid`.
  - `BentoGridScene.jsx` renders 4 distinct SVG graphic types across its 4 cards rather than repeating the `t-SNE` rings 4 times.
  - `GraphScene.jsx` Y-axis title and legend bounding boxes do not overlap.
- Run all Python and Node unit tests and confirm 100% pass rate.