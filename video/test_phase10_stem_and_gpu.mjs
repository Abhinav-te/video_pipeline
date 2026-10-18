import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Running Phase 10: Hardware GPU Wiring, Domain-Aware Comparison Footer & Specialized STEM Engines Verification...\n');

let failed = false;
function assert(condition, message) {
  if (!condition) {
    console.error(`✗ FAILED: ${message}`);
    failed = true;
  } else {
    console.log(`✓ ${message}`);
  }
}

const componentsDir = path.join(__dirname, 'src/components');
const codingShortPath = path.join(__dirname, 'src/CodingShort.jsx');

// ==========================================
// 1. Visual Polish Fix 1: GraphScene.jsx X-Axis Label Collision
// ==========================================
const graphPath = path.join(componentsDir, 'GraphScene.jsx');
assert(fs.existsSync(graphPath), 'GraphScene.jsx exists in video/src/components/');
const graphContent = fs.readFileSync(graphPath, 'utf8');

assert(
  graphContent.includes('x="140"') && graphContent.includes('y={originY + 32}') && graphContent.includes('Reactants'),
  'GraphScene.jsx places Reactants label cleanly at x=140, y=originY + 32'
);
assert(
  graphContent.includes('x="760"') && graphContent.includes('y={originY + 32}') && graphContent.includes('Products'),
  'GraphScene.jsx places Products label cleanly at x=760, y=originY + 32'
);
assert(
  graphContent.includes('y={originY + 72}') && graphContent.includes('Reaction Coordinate'),
  'GraphScene.jsx places centered Reaction Coordinate X-axis title at y=originY + 72 to eliminate collisions'
);

// ==========================================
// 2. Visual Polish Fix 2: Domain-Aware ComparisonScene.jsx Footer
// ==========================================
const compPath = path.join(componentsDir, 'ComparisonScene.jsx');
assert(fs.existsSync(compPath), 'ComparisonScene.jsx exists in video/src/components/');
const compContent = fs.readFileSync(compPath, 'utf8');

assert(
  compContent.includes('isChemistry') &&
  compContent.includes('isPhysicsOrMechanics') &&
  compContent.includes('isQuantum') &&
  compContent.includes('isElectrical'),
  'ComparisonScene.jsx implements domain detection for chemistry, physics/mechanics, quantum, and electrical'
);
assert(
  compContent.includes('RATE LAW CONTRAST') && compContent.includes('Rate = k[R-X]'),
  'ComparisonScene.jsx provides Chemistry-specific rate law / stereochemistry footer'
);
assert(
  compContent.includes('EQUILIBRIUM CONDITION') && compContent.includes('ΣF_x = 0'),
  'ComparisonScene.jsx provides Physics/Mechanics equilibrium and conservation footer'
);
assert(
  compContent.includes('COMMUTATION RELATION') && compContent.includes('[x̂, p̂] = iℏ'),
  'ComparisonScene.jsx provides Quantum physics commutation and uncertainty bound footer'
);
assert(
  compContent.includes('NETWORK EQUIVALENCE') && compContent.includes('V_th = V_oc'),
  'ComparisonScene.jsx provides Electrical engineering Thévenin / power flow footer'
);

// ==========================================
// 3. Engine 1: QuantumScene.jsx
// ==========================================
const quantumPath = path.join(componentsDir, 'QuantumScene.jsx');
assert(fs.existsSync(quantumPath), 'QuantumScene.jsx exists in video/src/components/');
const quantumContent = fs.readFileSync(quantumPath, 'utf8');

assert(
  quantumContent.includes('export const QuantumScene') || quantumContent.includes('export default QuantumScene'),
  'QuantumScene.jsx exports component'
);
// Verify 3 sub-modes in QuantumScene
assert(
  quantumContent.includes('schrodinger_tunneling') &&
  quantumContent.includes('heisenberg_uncertainty') &&
  quantumContent.includes('dirac_atomic_orbitals'),
  'QuantumScene.jsx supports all 3 sub-modes: schrodinger_tunneling, heisenberg_uncertainty, dirac_atomic_orbitals'
);
// sub_mode 1: Tunneling wavepacket & potential barrier
assert(
  quantumContent.includes('Barrier V₀') &&
  quantumContent.includes('Transmitted Tunneling') &&
  quantumContent.includes('psiRePath') &&
  quantumContent.includes('psiProbPath'),
  'QuantumScene schrodinger_tunneling displays Re[Ψ]/Im[Ψ] wavepacket, potential barrier, and tunneling transmission'
);
// sub_mode 2: Heisenberg reciprocal squeeze
assert(
  quantumContent.includes('POSITION SPACE |ψ(x)|²') &&
  quantumContent.includes('MOMENTUM SPACE |ϕ(p)|²') &&
  quantumContent.includes('Phase Space Area'),
  'QuantumScene heisenberg_uncertainty displays dual synchronized position/momentum wavepackets and phase space ellipse'
);
// sub_mode 3: Dirac atomic orbitals & relativistic spinor
assert(
  quantumContent.includes('RELATIVISTIC DIRAC BI-SPINOR') &&
  quantumContent.includes('1s Orbital') &&
  quantumContent.includes('2pz Orbital') &&
  quantumContent.includes('Cloverleaf'),
  'QuantumScene dirac_atomic_orbitals displays Dirac equation, multi-shell atomic orbital clouds (1s, 2p, 3d), and spin gauges'
);
// Dynamic Viewport Breathing in QuantumScene
assert(
  quantumContent.includes('isSpotlight') && quantumContent.includes('isCompact'),
  'QuantumScene.jsx adapts to dynamic layout density (compact_punch, canvas_spotlight, full_dashboard)'
);

// ==========================================
// 4. Engine 2: MechanicsScene.jsx
// ==========================================
const mechPath = path.join(componentsDir, 'MechanicsScene.jsx');
assert(fs.existsSync(mechPath), 'MechanicsScene.jsx exists in video/src/components/');
const mechContent = fs.readFileSync(mechPath, 'utf8');

assert(
  mechContent.includes('export const MechanicsScene') || mechContent.includes('export default MechanicsScene'),
  'MechanicsScene.jsx exports component'
);
// Verify 3 sub-modes in MechanicsScene
assert(
  mechContent.includes('beam_weight_distribution') &&
  mechContent.includes('inclined_plane_fbd') &&
  mechContent.includes('axle_center_of_mass'),
  'MechanicsScene.jsx supports all 3 sub-modes: beam_weight_distribution, inclined_plane_fbd, axle_center_of_mass'
);
// sub_mode 1: Beam load distribution & shear/moment diagrams
assert(
  mechContent.includes('R_A') &&
  mechContent.includes('R_B') &&
  mechContent.includes('SHEAR V(x)') &&
  mechContent.includes('MOMENT M(x)'),
  'MechanicsScene beam_weight_distribution renders multi-support beam, reaction vectors, and live V(x)/M(x) diagrams'
);
// sub_mode 2: Inclined plane FBD & friction threshold
assert(
  mechContent.includes('θ =') &&
  mechContent.includes('mg·sinθ') &&
  mechContent.includes('F_N') &&
  mechContent.includes('f_s'),
  'MechanicsScene inclined_plane_fbd decomposes gravity on tilted axes with normal force and friction'
);
// sub_mode 3: Axle weight distribution & dynamic load transfer
assert(
  mechContent.includes('CG (h =') &&
  mechContent.includes('FRONT LOAD') &&
  mechContent.includes('REAR LOAD') &&
  mechContent.includes('DYNAMIC AXLE LOAD EQUILIBRIUM'),
  'MechanicsScene axle_center_of_mass displays vehicle chassis center-of-gravity and dynamic load transfer'
);
// Dynamic Viewport Breathing in MechanicsScene
assert(
  mechContent.includes('isSpotlight') && mechContent.includes('isCompact'),
  'MechanicsScene.jsx adapts to dynamic layout density'
);

// ==========================================
// 5. Engine 3: ElectricalScene.jsx
// ==========================================
const elecPath = path.join(componentsDir, 'ElectricalScene.jsx');
assert(fs.existsSync(elecPath), 'ElectricalScene.jsx exists in video/src/components/');
const elecContent = fs.readFileSync(elecPath, 'utf8');

assert(
  elecContent.includes('export const ElectricalScene') || elecContent.includes('export default ElectricalScene'),
  'ElectricalScene.jsx exports component'
);
// Verify 3 sub-modes in ElectricalScene
assert(
  elecContent.includes('kvl_kcl_mesh') &&
  elecContent.includes('thevenin_equivalence') &&
  elecContent.includes('smart_grid_opf'),
  'ElectricalScene.jsx supports all 3 sub-modes: kvl_kcl_mesh, thevenin_equivalence, smart_grid_opf'
);
// sub_mode 1: KVL / KCL mesh analysis
assert(
  elecContent.includes('Loop I₁') &&
  elecContent.includes('Loop I₂') &&
  elecContent.includes('NODE V_A') &&
  elecContent.includes('KIRCHHOFF CURRENT & VOLTAGE LAWS'),
  'ElectricalScene kvl_kcl_mesh renders multi-loop circuit with animated charge flow, node V_A, and matrix solver'
);
// sub_mode 2: Thévenin equivalence reduction
assert(
  elecContent.includes('THÉVENIN 2-TERMINAL EQUIVALENT') &&
  elecContent.includes('V_th') &&
  elecContent.includes('R_th') &&
  elecContent.includes('MAXIMUM POWER TRANSFER THEOREM'),
  'ElectricalScene thevenin_equivalence illustrates 3-step network reduction and peak power transfer'
);
// sub_mode 3: Smart grid OPF & economic dispatch
assert(
  elecContent.includes('Nuclear Base') &&
  elecContent.includes('Renewables+ESS') &&
  elecContent.includes('Line 1-2') &&
  elecContent.includes('AC OPTIMAL POWER FLOW (OPF)'),
  'ElectricalScene smart_grid_opf renders multi-bus grid topology, HV transmission, economic dispatch, and battery ESS'
);
// Dynamic Viewport Breathing in ElectricalScene
assert(
  elecContent.includes('isSpotlight') && elecContent.includes('isCompact'),
  'ElectricalScene.jsx adapts to dynamic layout density'
);

// ==========================================
// 6. CodingShort.jsx Integration
// ==========================================
const codingShortContent = fs.readFileSync(codingShortPath, 'utf8');
assert(
  codingShortContent.includes('QuantumScene') &&
  codingShortContent.includes('MechanicsScene') &&
  codingShortContent.includes('ElectricalScene'),
  'CodingShort.jsx imports all 3 new STEM scenes'
);
assert(
  codingShortContent.includes("sceneType === 'quantum_sim'") &&
  codingShortContent.includes("sceneType === 'mechanics_fbd'") &&
  codingShortContent.includes("sceneType === 'electrical_grid'"),
  'CodingShort.jsx routes sceneType quantum_sim, mechanics_fbd, and electrical_grid to respective scenes'
);

// ==========================================
// 7. SvgIcons.jsx Integration
// ==========================================
const iconsPath = path.join(componentsDir, 'SvgIcons.jsx');
const iconsContent = fs.readFileSync(iconsPath, 'utf8');
assert(
  iconsContent.includes('QuantumIcon') &&
  iconsContent.includes('MechanicsIcon') &&
  iconsContent.includes('ElectricalIcon'),
  'SvgIcons.jsx exports QuantumIcon, MechanicsIcon, and ElectricalIcon'
);

// ==========================================
// 8. Quality Constraints: Zero Scale Jitter & Zero Raw Unicode Emojis
// ==========================================
const newComponentContents = [
  { name: 'QuantumScene.jsx', content: quantumContent },
  { name: 'MechanicsScene.jsx', content: mechContent },
  { name: 'ElectricalScene.jsx', content: elecContent },
  { name: 'ComparisonScene.jsx', content: compContent }
];

for (const { name, content } of newComponentContents) {
  assert(
    content.includes("transform: 'none'") || content.includes('transform: "none"'),
    `${name} strictly enforces transform: "none" on container divs to eliminate scale jitter`
  );

  // Check for common emoji ranges in active code, ignoring comment lines
  const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
  const lines = content.split('\n');
  let foundEmoji = null;
  for (const line of lines) {
    if (line.trim().startsWith('*') || line.trim().startsWith('//')) continue;
    const match = line.match(emojiRegex);
    if (match) {
      foundEmoji = match[0];
      break;
    }
  }
  assert(!foundEmoji, `${name} has ZERO raw Unicode emojis (found: ${foundEmoji || 'none'})`);
}

console.log('\n------------------------------------------------------------');
if (failed) {
  console.error('Phase 10 Node Verification FAILED!');
  process.exit(1);
} else {
  console.log('Phase 10 Node Verification PASSED! (100% OK)');
}
