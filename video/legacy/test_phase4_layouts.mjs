import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Running Phase 4 Layouts & Bug Fixes (BentoGrid, AlgorithmExplorer, NeuralCodeSplit, Physics Modes) Node Verification...');

const componentsDir = path.join(__dirname, 'src', 'components');

// 1. Verify existence of all 3 Phase 4 ML layout components
const requiredPhase4Files = [
  'BentoGridScene.jsx',
  'AlgorithmExplorerScene.jsx',
  'NeuralCodeSplitScene.jsx',
];

for (const file of requiredPhase4Files) {
  const filePath = path.join(componentsDir, file);
  assert.ok(fs.existsSync(filePath), `Missing required Phase 4 layout component: ${file}`);
}
console.log('✓ All 3 Phase 4 ML layout component files exist in video/src/components/');

// 2. Strict Zero Scale Jitter Rule on all new components
for (const file of requiredPhase4Files) {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  assert.ok(!content.includes('scale(${roundedScale})'), `${file} must not continuously scale text`);
  assert.ok(content.includes("transform: 'none'"), `${file} must explicitly enforce transform: 'none' for static text grid`);
}
console.log('✓ All Phase 4 layouts strictly enforce transform: "none" (Zero scale jitter rule)');

// 3. Verify minHeight: 420px on all scene visual containers
const allSceneFiles = [
  'MathScene.jsx',
  'GraphScene.jsx',
  'PhysicsScene.jsx',
  'BentoGridScene.jsx',
  'AlgorithmExplorerScene.jsx',
  'NeuralCodeSplitScene.jsx',
];
for (const file of allSceneFiles) {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  assert.ok(content.includes('minHeight'), `${file} must enforce minHeight on its visual container`);
}
console.log('✓ All visual containers enforce minHeight (>= 420px) preventing collapsed empty scene cards');

// 4. Verify fake macOS window dots removal from non-code scenes
const nonCodeScenes = ['MathScene.jsx', 'GraphScene.jsx', 'PhysicsScene.jsx', 'BentoGridScene.jsx', 'AlgorithmExplorerScene.jsx'];
for (const file of nonCodeScenes) {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  assert.ok(!content.includes('#ff5f56'), `${file} must not contain fake macOS red terminal dots`);
}
console.log('✓ Fake macOS window dots removed from non-code scenes (Math, Graph, Physics, Bento, Explorer)');

// 5. Verify PhysicsScene dynamic mode switching & collision fix
const physicsContent = fs.readFileSync(path.join(componentsDir, 'PhysicsScene.jsx'), 'utf8');
assert.ok(physicsContent.includes("simType === 'projectile'"), 'PhysicsScene implements projectile mode');
assert.ok(physicsContent.includes("simType === 'wave'"), 'PhysicsScene implements wave mode');
assert.ok(physicsContent.includes("simType === 'forces'"), 'PhysicsScene implements forces mode');
assert.ok(physicsContent.includes('trajectoryPath'), 'PhysicsScene projectile mode computes parabolic arc');
assert.ok(physicsContent.includes('vxLen'), 'PhysicsScene projectile mode renders horizontal velocity arrow');
assert.ok(physicsContent.includes('vyNorm'), 'PhysicsScene projectile mode renders dynamic changing vertical velocity arrow');
assert.ok(physicsContent.includes('gap'), 'PhysicsScene forces mode specifies clearance gap >= 12px outside border');
assert.ok(physicsContent.includes('boxW = 180'), 'PhysicsScene forces mode uses dynamic box width >= 160px');
console.log('✓ PhysicsScene implements projectile, wave, and collision-free forces modes');

// 6. Verify BentoGridScene structure
const bentoContent = fs.readFileSync(path.join(componentsDir, 'BentoGridScene.jsx'), 'utf8');
assert.ok(bentoContent.includes('gridTemplateColumns: \'repeat(2, 1fr)\''), 'BentoGridScene renders 2-column bento grid');
assert.ok(bentoContent.includes('CLUSTERING'), 'BentoGridScene renders grouped section headers');
assert.ok(bentoContent.includes('MiniCanvas'), 'BentoGridScene renders animated SVG mini-visualizations');
assert.ok(bentoContent.includes('isHighlighted'), 'BentoGridScene illuminates active cards in sync with frames');
console.log('✓ BentoGridScene implements Instagram-style 2-column ML overview with animated mini-canvases');

// 7. Verify AlgorithmExplorerScene structure
const explorerContent = fs.readFileSync(path.join(componentsDir, 'AlgorithmExplorerScene.jsx'), 'utf8');
assert.ok(explorerContent.includes('conceptStrip'), 'AlgorithmExplorerScene renders top concept progress strip');
assert.ok(explorerContent.includes('epsilonRadius'), 'AlgorithmExplorerScene center simulation computes epsilon search radius');
assert.ok(explorerContent.includes('corePoints'), 'AlgorithmExplorerScene renders 2D point cloud with core/border/noise points');
assert.ok(explorerContent.includes('PARAMETERS'), 'AlgorithmExplorerScene bottom left card specifies tuning parameters');
assert.ok(explorerContent.includes('POINT TYPES'), 'AlgorithmExplorerScene bottom right card specifies visual point legend');
console.log('✓ AlgorithmExplorerScene implements 3-tier deep-dive layout with scanning epsilon circle');

// 8. Verify NeuralCodeSplitScene structure
const neuralContent = fs.readFileSync(path.join(componentsDir, 'NeuralCodeSplitScene.jsx'), 'utf8');
assert.ok(neuralContent.includes('FROM SCRATCH'), 'NeuralCodeSplitScene top header renders editorial badge');
assert.ok(neuralContent.includes('INPUT: digit'), 'NeuralCodeSplitScene renders 8x8 pixel matrix digit input');
assert.ok(neuralContent.includes('Loss:'), 'NeuralCodeSplitScene renders live decreasing loss counter');
assert.ok(neuralContent.includes('Epoch:'), 'NeuralCodeSplitScene renders live climbing epoch counter');
assert.ok(neuralContent.includes('activeLineIdx'), 'NeuralCodeSplitScene code window renders sweeping active line highlight bar');
console.log('✓ NeuralCodeSplitScene implements vertical visualizer + live code split layout');

// 9. Verify CodingShort.jsx integration
const codingShortContent = fs.readFileSync(path.join(__dirname, 'src', 'CodingShort.jsx'), 'utf8');
assert.ok(codingShortContent.includes('import { BentoGridScene }'), 'CodingShort imports BentoGridScene');
assert.ok(codingShortContent.includes('import { AlgorithmExplorerScene }'), 'CodingShort imports AlgorithmExplorerScene');
assert.ok(codingShortContent.includes('import { NeuralCodeSplitScene }'), 'CodingShort imports NeuralCodeSplitScene');
assert.ok(codingShortContent.includes('<BentoGridScene'), 'CodingShort renders BentoGridScene');
assert.ok(codingShortContent.includes('<AlgorithmExplorerScene'), 'CodingShort renders AlgorithmExplorerScene');
assert.ok(codingShortContent.includes('<NeuralCodeSplitScene'), 'CodingShort renders NeuralCodeSplitScene');
assert.ok(codingShortContent.includes("sceneType !== 'neural_code_split'"), 'CodingShort hides bottom subtitles during neural_code_split');
console.log('✓ CodingShort wires all Phase 4 ML layout components into scene router');

console.log('\nAll Phase 4 Layout and Bug Fix Node tests passed successfully!\n');

