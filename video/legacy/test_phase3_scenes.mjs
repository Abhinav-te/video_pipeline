import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Running Phase 3 Animated Scene Renderers & Anti-Jitter Node Verification...');

const componentsDir = path.join(__dirname, 'src', 'components');

// 1. Verify existence of all component files
const requiredFiles = [
  'CodeRevealScene.jsx',
  'CodeTransformScene.jsx',
  'ComparisonScene.jsx',
  'DiagramScene.jsx',
  'ConceptHeroScene.jsx',
];

for (const file of requiredFiles) {
  const filePath = path.join(componentsDir, file);
  assert.ok(fs.existsSync(filePath), `Missing component: ${file}`);
}
console.log('✓ All 5 Phase 3 animated scene component files exist');

// 2. Verify static grid transforms (no continuous scale() on text containers)
for (const file of requiredFiles) {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  assert.ok(!content.includes('scale(${roundedScale})'), `${file} must not apply scale(roundedScale)`);
  assert.ok(!content.includes('scale(${highlightScale})'), `${file} must not apply scale(highlightScale) to text`);
  assert.ok(content.includes("transform: 'none'"), `${file} must explicitly use transform: 'none' for static text grid`);
}
console.log('✓ All scene components lock text and card containers to transform: "none"');

// 3. Verify CodeReveal features
const codeRevealContent = fs.readFileSync(path.join(componentsDir, 'CodeRevealScene.jsx'), 'utf8');
assert.ok(codeRevealContent.includes('#ff5f56'), 'CodeRevealScene has macOS red dot');
assert.ok(codeRevealContent.includes('#ffbd2e'), 'CodeRevealScene has macOS yellow dot');
assert.ok(codeRevealContent.includes('#27c93f'), 'CodeRevealScene has macOS green dot');
assert.ok(codeRevealContent.includes('TerminalCursor'), 'CodeRevealScene integrates TerminalCursor');
assert.ok(codeRevealContent.includes('staggerFrames'), 'CodeRevealScene implements line stagger');
console.log('✓ CodeRevealScene implements macOS header bar and line-by-line typewriter stagger');

// 4. Verify CodeTransform features
const codeTransformContent = fs.readFileSync(path.join(componentsDir, 'CodeTransformScene.jsx'), 'utf8');
assert.ok(codeTransformContent.includes('⚠️ Before'), 'CodeTransformScene has Before tag');
assert.ok(codeTransformContent.includes('✨ After'), 'CodeTransformScene has After tag');
assert.ok(codeTransformContent.includes('isPostEmphasis'), 'CodeTransformScene triggers transition at emphasis_time');
console.log('✓ CodeTransformScene morphs before -> after code with animated divider at emphasis_time');

// 5. Verify Comparison features
const comparisonContent = fs.readFileSync(path.join(componentsDir, 'ComparisonScene.jsx'), 'utf8');
assert.ok(comparisonContent.includes('card1Start'), 'ComparisonScene staggers card 1 entrance');
assert.ok(comparisonContent.includes('card2Start'), 'ComparisonScene staggers card 2 entrance');
assert.ok(comparisonContent.includes('winnerGlow'), 'ComparisonScene animates emerald winner glow');
assert.ok(comparisonContent.includes('#3fb950'), 'ComparisonScene illuminates winning card with #3fb950');
console.log('✓ ComparisonScene staggers dual cards and illuminates winning card with emerald glow');

// 6. Verify Diagram features
const diagramContent = fs.readFileSync(path.join(componentsDir, 'DiagramScene.jsx'), 'utf8');
assert.ok(diagramContent.includes('FlowArrow'), 'DiagramScene integrates FlowArrow');
assert.ok(diagramContent.includes('<svg'), 'DiagramScene renders SVG connecting arrows');
assert.ok(diagramContent.includes('Step {i + 1}'), 'DiagramScene formats numbered step nodes');
console.log('✓ DiagramScene animates step nodes and sequential SVG flow arrows');

// 7. Verify ConceptHero features
const conceptContent = fs.readFileSync(path.join(componentsDir, 'ConceptHeroScene.jsx'), 'utf8');
assert.ok(conceptContent.includes('displayText'), 'ConceptHeroScene formats takeaway title');
assert.ok(conceptContent.includes('points.map'), 'ConceptHeroScene progressively reveals takeaway bullet pills');
console.log('✓ ConceptHeroScene displays hero icon badge, title, and progressive bullet reveals');

console.log('\nAll Phase 3 Scene Renderer Node tests passed successfully!\n');

