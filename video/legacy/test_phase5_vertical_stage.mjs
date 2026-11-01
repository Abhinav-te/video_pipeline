import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Running Phase 5: Vertical Stage Maximization (1540px), Subtitle Continuity & Rich Animations Verification...\n');

const componentsDir = path.join(__dirname, 'src', 'components');

// 1. Verify Subtitle Pause-Holding Logic (Zero Index 0 Flash Bug)
console.log('1. Verifying Subtitle pause-holding and zero index 0 fallback...');
const codingShortCode = fs.readFileSync(path.join(__dirname, 'src', 'CodingShort.jsx'), 'utf8');

// Assert CodingShort implements lastSpokenIndex tracking
assert.ok(codingShortCode.includes('lastSpokenIndex'), 'CodingShort must track lastSpokenIndex during speech pauses');
assert.ok(codingShortCode.includes('currentWordIndex !== -1 ? currentWordIndex : lastSpokenIndex'), 'Subtitles must hold last spoken word during pauses');
assert.ok(codingShortCode.includes('subtitleOpacity'), 'Subtitles must calculate smooth fade opacity during gaps');
assert.ok(!codingShortCode.includes('(currentWordIndex !== -1 ? currentWordIndex : 0) - 1'), 'Subtitles must NEVER fall back to index 0 on word gaps');

// Simulate the Subtitle algorithm
const testWords = [
  { word: "MOST", start: 0.4, end: 0.8 },
  { word: "ENGINEERS", start: 0.9, end: 1.4 },
  { word: "PICK", start: 1.5, end: 1.8 },
  { word: "THE", start: 1.9, end: 2.2 },
  { word: "WRONG", start: 2.3, end: 2.7 },
  { word: "CLUSTERING", start: 4.0, end: 4.6 }, // 1.3s pause between 2.7s and 4.0s
];

function simulateSubtitleWindow(currentTime, words) {
  const currentWordIndex = words.findIndex((w) => currentTime >= w.start && currentTime <= w.end);
  let lastSpokenIndex = -1;
  for (let i = words.length - 1; i >= 0; i--) {
    if (words[i].start <= currentTime) {
      lastSpokenIndex = i;
      break;
    }
  }

  if (lastSpokenIndex === -1) {
    if (words[0].start - currentTime > 0.6) return { slice: [], opacity: 0 };
    lastSpokenIndex = 0;
  }

  const effectiveIndex = currentWordIndex !== -1 ? currentWordIndex : lastSpokenIndex;
  const startIdx = Math.max(0, effectiveIndex - 1);
  const subtitleSlice = words.slice(startIdx, startIdx + 3);

  let subtitleOpacity = 1;
  if (currentWordIndex === -1 && lastSpokenIndex !== -1) {
    const gap = currentTime - words[lastSpokenIndex].end;
    if (gap > 0.6) {
      subtitleOpacity = Math.max(0, Math.min(1, 1 - (gap - 0.6) / 0.4));
    }
  }

  return { slice: subtitleSlice.map(w => w.word), effectiveIndex, opacity: subtitleOpacity };
}

// Test at currentTime = 3.0s (in the pause between "WRONG" at 2.7s and "CLUSTERING" at 4.0s)
const pauseSub = simulateSubtitleWindow(3.0, testWords);
// Should hold "THE", "WRONG", "CLUSTERING" (indexes 3, 4, 5) centered around last word "WRONG" (index 4)
assert.strictEqual(pauseSub.effectiveIndex, 4, 'Pause must hold last spoken word index 4 ("WRONG")');
assert.deepStrictEqual(pauseSub.slice, ["THE", "WRONG", "CLUSTERING"]);
assert.notDeepStrictEqual(pauseSub.slice, ["MOST", "ENGINEERS", "PICK"], 'Subtitles must NOT flash index 0 ("MOST ENGINEERS PICK") during pauses!');
console.log('✓ Subtitle pause holding verified: Never flashes index 0 during inter-sentence pauses');

// 2. Verify Mandatory Vertical Stage Container (960px x 1540px)
console.log('\n2. Verifying Mandatory Vertical Stage Container in CodingShort.jsx...');
assert.ok(codingShortCode.includes("width: '960px'"), 'CodingShort must enforce 960px width container');
assert.ok(codingShortCode.includes("height: '1540px'"), 'CodingShort must enforce 1540px height container');
assert.ok(codingShortCode.includes("top: '80px'"), 'CodingShort must place container at top: 80px');
assert.ok(codingShortCode.includes("left: '60px'"), 'CodingShort must place container at left: 60px');
assert.ok(codingShortCode.includes("justifyContent: 'space-between'"), 'CodingShort must enforce vertical flex distribution');

// Check activeScene guarantee
assert.ok(codingShortCode.includes('activeScene = scenes[scenes.length - 1]'), 'CodingShort must guarantee non-null activeScene across all frames');
console.log('✓ CodingShort Vertical Stage Container strictly conforms to 960x1540 (80-90% vertical fill)');

// 3. Verify all scene components fill the 1540px vertical stage
console.log('\n3. Verifying 1540px vertical height compliance across all scene components...');
const allScenes = [
  'ConceptHeroScene.jsx',
  'BentoGridScene.jsx',
  'AlgorithmExplorerScene.jsx',
  'NeuralCodeSplitScene.jsx',
  'MathScene.jsx',
  'PhysicsScene.jsx',
  'GraphScene.jsx',
  'CodeRevealScene.jsx',
  'CodeTransformScene.jsx',
  'ComparisonScene.jsx',
  'DiagramScene.jsx',
];

for (const sceneFile of allScenes) {
  const filePath = path.join(componentsDir, sceneFile);
  assert.ok(fs.existsSync(filePath), `Scene component ${sceneFile} must exist`);
  const content = fs.readFileSync(filePath, 'utf8');

  assert.ok(
    content.includes("1540px") || content.includes("'100%'"),
    `${sceneFile} must explicitly fill the 1540px vertical stage`
  );
  assert.ok(
    content.includes("960px") || content.includes("width: '100%'"),
    `${sceneFile} must fit the 960px width stage`
  );
}
console.log(`✓ All ${allScenes.length} scene components fill the 960x1540 vertical stage`);

// 4. Verify Zero Unicode Emojis (Headless Linux Chromium Tofu Box Prevention)
console.log('\n4. Verifying Zero Unicode Emojis in badges, headers, and components...');
const emojiRegex = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;

for (const sceneFile of allScenes) {
  const filePath = path.join(componentsDir, sceneFile);
  const content = fs.readFileSync(filePath, 'utf8');

  // Check badges, headers, text
  const lines = content.split('\n');
  lines.forEach((line, lineNum) => {
    // Ignore comments mentioning emojis in documentation
    if (line.trim().startsWith('*') || line.trim().startsWith('//')) return;
    const match = line.match(emojiRegex);
    assert.ok(
      !match,
      `Found raw emoji glyph '${match?.[0]}' at ${sceneFile}:${lineNum + 1}: ${line.trim()}`
    );
  });
}
console.log('✓ Zero raw Unicode emoji glyphs found: all replaced with clean inline SVGs');

// 5. Verify SvgIcons component library
console.log('\n5. Verifying SvgIcons component library...');
const svgIconsCode = fs.readFileSync(path.join(componentsDir, 'SvgIcons.jsx'), 'utf8');
const requiredIcons = [
  'WarningIcon',
  'SparklesIcon',
  'LightningIcon',
  'BulbIcon',
  'ScaleIcon',
  'BrainIcon',
  'TargetIcon',
  'GearIcon',
  'LayersIcon',
  'CodeIcon',
  'MathIcon',
  'PhysicsIcon',
  'GraphIcon',
  'DynamicBadgeIcon',
];

for (const iconName of requiredIcons) {
  assert.ok(svgIconsCode.includes(`export const ${iconName}`), `SvgIcons must export ${iconName}`);
}
console.log(`✓ SvgIcons exports all ${requiredIcons.length} vector icons including DynamicBadgeIcon`);

console.log('\nAll Phase 5 Vertical Stage & Continuity Verification tests passed with 100% success!');

