import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Running STEM Scene Renderers (Math, Graph, Physics) Node Verification...');

const componentsDir = path.join(__dirname, 'src', 'components');

// 1. Verify existence of all three STEM component files
const requiredStemFiles = [
  'MathScene.jsx',
  'GraphScene.jsx',
  'PhysicsScene.jsx',
];

for (const file of requiredStemFiles) {
  const filePath = path.join(componentsDir, file);
  assert.ok(fs.existsSync(filePath), `Missing required STEM component: ${file}`);
}
console.log('✓ All 3 STEM component files (MathScene, GraphScene, PhysicsScene) exist');

// 2. Strict Rule: Zero transform: scale() on text containers or formulas
for (const file of requiredStemFiles) {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  assert.ok(!content.includes('scale(${roundedScale})'), `${file} must not scale text by roundedScale`);
  assert.ok(!content.includes('scale(${highlightScale})'), `${file} must not scale text by highlightScale`);
  assert.ok(content.includes("transform: 'none'"), `${file} must explicitly use transform: 'none' for static text grid`);
}
console.log('✓ All STEM components strictly enforce transform: "none" (Zero scale jitter rule)');

// 3. Verify MathScene properties and derivation logic
const mathContent = fs.readFileSync(path.join(componentsDir, 'MathScene.jsx'), 'utf8');
assert.ok(mathContent.includes('MATHEMATICAL FORMULATION'), 'MathScene contains derivation studio tag');
assert.ok(mathContent.includes('normalizedSteps.map'), 'MathScene renders sequential derivation steps');
assert.ok(mathContent.includes('ACTIVE FOCUS'), 'MathScene includes active focus term highlight');
console.log('✓ MathScene implements multi-step derivations with active term highlights');

// 4. Verify GraphScene SVG Cartesian plotting
const graphContent = fs.readFileSync(path.join(componentsDir, 'GraphScene.jsx'), 'utf8');
assert.ok(graphContent.includes('<svg'), 'GraphScene renders SVG Cartesian coordinate plane');
assert.ok(graphContent.includes('strokeDashoffset'), 'GraphScene uses strokeDashoffset for smooth curve draw');
assert.ok(graphContent.includes('Critical (0, 0)'), 'GraphScene includes pulsed critical point callouts');
console.log('✓ GraphScene implements 2D Cartesian plane with stroke-animated curves and critical points');

// 5. Verify PhysicsScene Free-Body Diagram & Vectors
const physicsContent = fs.readFileSync(path.join(componentsDir, 'PhysicsScene.jsx'), 'utf8');
assert.ok(physicsContent.includes('VectorArrow'), 'PhysicsScene contains VectorArrow component');
assert.ok(physicsContent.includes('m = 10kg'), 'PhysicsScene renders central body mass');
assert.ok(physicsContent.includes('Fg'), 'PhysicsScene renders gravity force vector');
assert.ok(physicsContent.includes('FN'), 'PhysicsScene renders normal force vector');
console.log('✓ PhysicsScene implements Free-Body Diagram with animated force vector arrows');

// 6. Verify CodingShort.jsx integration
const codingShortContent = fs.readFileSync(path.join(__dirname, 'src', 'CodingShort.jsx'), 'utf8');
assert.ok(codingShortContent.includes('import { MathScene }'), 'CodingShort imports MathScene');
assert.ok(codingShortContent.includes('import { GraphScene }'), 'CodingShort imports GraphScene');
assert.ok(codingShortContent.includes('import { PhysicsScene }'), 'CodingShort imports PhysicsScene');
assert.ok(codingShortContent.includes('<MathScene'), 'CodingShort renders MathScene');
assert.ok(codingShortContent.includes('<GraphScene'), 'CodingShort renders GraphScene');
assert.ok(codingShortContent.includes('<PhysicsScene'), 'CodingShort renders PhysicsScene');
console.log('✓ CodingShort wires MathScene, GraphScene, and PhysicsScene into scene router');

console.log('\nAll STEM Scene Renderer Node tests passed successfully!\n');

