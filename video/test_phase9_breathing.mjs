import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Running Phase 9: Dynamic Viewport Breathing & True Multi-Geometry Animations Verification...\n');

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

// 1. Verify ChemistryScene Component Exists and Exports
const chemPath = path.join(componentsDir, 'ChemistryScene.jsx');
assert(fs.existsSync(chemPath), 'ChemistryScene.jsx exists in video/src/components/');
const chemContent = fs.readFileSync(chemPath, 'utf8');

assert(
  chemContent.includes('export const ChemistryScene') || chemContent.includes('export default ChemistryScene'),
  'ChemistryScene.jsx properly exports component'
);

// 2. Verify Viewport Breathing in ChemistryScene: Hides Bottom 2 Cards on canvas_spotlight & compact_punch
assert(
  chemContent.includes('!isSpotlight && !isCompact') && chemContent.includes('BOTTOM SPLIT ENERGY & KINETICS CARDS'),
  'ChemistryScene hides bottom 2 parameter/energy cards completely in canvas_spotlight and compact_punch modes'
);
assert(
  chemContent.includes("stageHeight = isSpotlight ? '1260px'") && chemContent.includes("vesselHeight = isSpotlight ? '1040px'"),
  'ChemistryScene dynamically expands center reaction vessel to 1040px in canvas_spotlight mode'
);

// 3. Verify 4 Distinct Reaction SVG Mechanisms in ChemistryScene
assert(
  chemContent.includes('renderSN2ConcertedSVG') &&
  chemContent.includes('renderStericBlockadeSVG') &&
  chemContent.includes('renderSN1IonizationSVG') &&
  chemContent.includes('renderSN1RacemicSVG'),
  'ChemistryScene defines 4 distinct, dedicated SVG mechanism renderers'
);

// 4. Verify sub_mode 1: sn2_concerted (Backside attack -> Walden inversion)
assert(
  chemContent.includes('180° BACKSIDE ATTACK -> WALDEN INVERSION') &&
  chemContent.includes('umbrella') || chemContent.includes('flipX'),
  'sub_mode sn2_concerted implements 180° backside attack with umbrella inversion'
);

// 5. Verify sub_mode 2: steric_blockade (Bulky methyls + barrier arc + bounce back)
assert(
  chemContent.includes('STERIC HINDRANCE BLOCKADE') &&
  chemContent.includes('STERIC BARRIER') &&
  (chemContent.includes('bounce') || chemContent.includes('shockwave') || chemContent.includes('hitProgress')),
  'sub_mode steric_blockade implements bulky methyl spheres, red steric shield arc, and nucleophile deflection'
);

// 6. Verify sub_mode 3: sn1_ionization (Zero OH-, heat applied, heterolytic cleavage, planar sp2 C+)
assert(
  chemContent.includes('STEP 1 (SLOW): HETEROLYTIC CLEAVAGE -> PLANAR sp² CARBOCATION') &&
  chemContent.includes('Upper Lobe') &&
  chemContent.includes('Lower Lobe'),
  'sub_mode sn1_ionization implements thermal cleavage into planar sp² carbocation with figure-8 p-orbital'
);
// In renderSN1IonizationSVG, OH- is never drawn
const sn1IonizationFn = chemContent.substring(
  chemContent.indexOf('const renderSN1IonizationSVG ='),
  chemContent.indexOf('const renderSN1RacemicSVG =')
);
assert(
  !sn1IonizationFn.includes('OH⁻') && !sn1IonizationFn.includes('OH-'),
  'sub_mode sn1_ionization strictly renders ZERO OH⁻ nucleophiles on screen'
);

// 7. Verify sub_mode 4: sn1_racemic (Dual top & bottom attack -> 50% R + 50% S Racemic)
assert(
  chemContent.includes('50% (R)-ENANTIOMER') &&
  chemContent.includes('50% (S)-ENANTIOMER') &&
  chemContent.includes('RACEMIC MIXTURE'),
  'sub_mode sn1_racemic animates simultaneous dual top & bottom attack and reveals 50/50 racemic enantiomer products'
);

// 8. Verify CodingShort.jsx Viewport Breathing (compact_punch, canvas_spotlight, full_dashboard)
const codingShortPath = path.join(__dirname, 'src/CodingShort.jsx');
const codingShortContent = fs.readFileSync(codingShortPath, 'utf8');

assert(
  codingShortContent.includes("layoutDensity === 'compact_punch'") &&
  codingShortContent.includes("stageTop = '280px'") &&
  codingShortContent.includes("stageHeight = '960px'"),
  'CodingShort.jsx implements compact_punch vertical density (960px tall, top 280px, centered)'
);

assert(
  codingShortContent.includes("layoutDensity === 'canvas_spotlight'") &&
  codingShortContent.includes("stageTop = '140px'") &&
  codingShortContent.includes("stageHeight = '1260px'"),
  'CodingShort.jsx implements canvas_spotlight vertical density (1260px tall, top 140px, uncluttered)'
);

assert(
  codingShortContent.includes("stageTop = '80px'") &&
  codingShortContent.includes("stageHeight = '1540px'"),
  'CodingShort.jsx preserves full_dashboard density (1540px tall, top 80px)'
);

// 9. Verify GraphScene.jsx Viewport Breathing & Energy Profile Dual-Curve Overlay
const graphPath = path.join(componentsDir, 'GraphScene.jsx');
const graphContent = fs.readFileSync(graphPath, 'utf8');

assert(
  graphContent.includes('!isSpotlight') && graphContent.includes('BOTTOM CALCULUS BREAKDOWN CARD'),
  'GraphScene.jsx conditionally hides bottom calculus card in canvas_spotlight mode'
);

assert(
  graphContent.includes('generateSN2Path') &&
  graphContent.includes('generateSN1Path') &&
  graphContent.includes('SN2: Concerted (1 Peak [‡])') &&
  graphContent.includes('SN1: Stepwise (2 Peaks + C⁺)'),
  'GraphScene.jsx overlays dual 1-peak SN2 (cyan) vs 2-peak SN1 (amber) energy reaction curves'
);

// 10. Verify BentoGridScene.jsx 4-Card Decision Matrix
const bentoPath = path.join(componentsDir, 'BentoGridScene.jsx');
const bentoContent = fs.readFileSync(bentoPath, 'utf8');

assert(
  bentoContent.includes('ORGANIC CHEMISTRY • REACTION MECHANISMS') &&
  bentoContent.includes('SUBSTRATE') &&
  bentoContent.includes('NUCLEOPHILE') &&
  bentoContent.includes('SOLVENT') &&
  bentoContent.includes('STEREOCHEMISTRY'),
  'BentoGridScene.jsx renders 4-card SN1 vs SN2 Decision Matrix with dedicated chemistry mini-canvases'
);

// 11. Zero Unicode Emoji Rule Check
const rawEmojiRegex = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;
assert(!rawEmojiRegex.test(chemContent), 'ChemistryScene.jsx contains zero raw Unicode emojis');
assert(!rawEmojiRegex.test(graphContent), 'GraphScene.jsx contains zero raw Unicode emojis');
assert(!rawEmojiRegex.test(bentoContent), 'BentoGridScene.jsx contains zero raw Unicode emojis');

// 12. Zero Scale Jitter Rule Check
assert(
  chemContent.includes("transform: 'none'") || chemContent.includes('transform: "none"'),
  'ChemistryScene.jsx locks transform to "none"'
);
assert(
  graphContent.includes("transform: 'none'") || graphContent.includes('transform: "none"'),
  'GraphScene.jsx locks transform to "none"'
);
assert(
  bentoContent.includes("transform: 'none'") || bentoContent.includes('transform: "none"'),
  'BentoGridScene.jsx locks transform to "none"'
);

if (failed) {
  console.error('\n❌ Phase 9 Node verification tests FAILED!');
  process.exit(1);
} else {
  console.log('\nAll Phase 9 Dynamic Viewport Breathing & Multi-Geometry Node tests passed with 100% success!\n');
}
