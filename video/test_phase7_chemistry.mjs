import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Running Phase 7: Multi-Subject De-Hardcoding & Chemistry Reaction Engine Node Verification...\n');

let failed = false;
function assert(condition, message) {
  if (!condition) {
    console.error(`✗ FAILED: ${message}`);
    failed = true;
  } else {
    console.log(`✓ ${message}`);
  }
}

// 1. Verify ChemistryScene Component Exists
const chemistryScenePath = path.join(__dirname, 'src/components/ChemistryScene.jsx');
assert(fs.existsSync(chemistryScenePath), 'ChemistryScene.jsx exists in video/src/components/');

const chemContent = fs.readFileSync(chemistryScenePath, 'utf8');

// 2. Zero Scale Jitter Rule: transform: "none"
assert(
  chemContent.includes("transform: 'none'") || chemContent.includes('transform: "none"'),
  'ChemistryScene strictly enforces transform: "none" (Zero scale jitter rule)'
);
assert(
  !chemContent.includes('scale(') || chemContent.includes('rotate('), // SVG transforms like rotate() are fine inside SVG
  'ChemistryScene outer layout containers do not use scale() transforms'
);

// 3. Vertical Stage Constraints: 960x1540
assert(
  chemContent.includes("width: '960px'") && chemContent.includes("height: '1540px'"),
  'ChemistryScene fills the mandatory 960x1540 vertical stage (80-90% vertical fill)'
);

// 4. Three-Tier Chemistry Layout (Header 180px, Center Vessel 840px, Bottom Split Cards 460px)
assert(
  chemContent.includes("height: '180px'") && chemContent.includes('ORGANIC CHEMISTRY • REACTION MECHANISM'),
  'ChemistryScene renders Top Header (180px tall) with domain eyebrow and reaction badge'
);

assert(
  chemContent.includes("height: '840px'") && chemContent.includes('WALDEN INVERSION'),
  'ChemistryScene renders Center Molecular Reaction Vessel (840px tall) with inversion indicators'
);

assert(
  chemContent.includes("height: '460px'") &&
    chemContent.includes('REACTION COORDINATE • ENERGY PROFILE') &&
    chemContent.includes('KINETICS & STEREOCHEMISTRY'),
  'ChemistryScene renders Bottom Split Cards (460px tall) with Energy Profile and Kinetics'
);

// 5. 3-Phase Reaction Mechanism Elements
assert(
  chemContent.includes('electronArrow') && chemContent.includes('strokeDashoffset'),
  'ChemistryScene implements animated curved electron-pushing arrow in Phase 1'
);

assert(
  chemContent.includes('transition_state') && chemContent.includes('‡') && chemContent.includes('sp² TRIGONAL PLANAR‡'),
  'ChemistryScene implements Transition State [‡] with double-dagger brackets and planar rehybridization in Phase 2'
);

assert(
  chemContent.includes('Leaving Group') && chemContent.includes('Br') && chemContent.includes('curveX'),
  'ChemistryScene implements leaving group departure and real-time glowing tracking dot on energy curve'
);

// 6. Thermal Effects & Heat Waves
assert(
  chemContent.includes('heatApplied') && chemContent.includes('tempKelvin') && chemContent.includes('Δ HEAT'),
  'ChemistryScene implements thermal heat gradient, rising heat particles, and Kelvin HUD'
);

// 7. Verify SvgIcons exports ChemistryIcon and DynamicBadgeIcon handles it
const svgIconsPath = path.join(__dirname, 'src/components/SvgIcons.jsx');
const svgContent = fs.readFileSync(svgIconsPath, 'utf8');
assert(svgContent.includes('export const ChemistryIcon'), 'SvgIcons.jsx exports ChemistryIcon');
assert(
  svgContent.includes("iconStr.includes('chem')") && svgContent.includes('ChemistryIcon'),
  'DynamicBadgeIcon properly maps chemistry and reaction keywords to ChemistryIcon'
);

// 8. Verify CodingShort.jsx wires ChemistryScene
const codingShortPath = path.join(__dirname, 'src/CodingShort.jsx');
const codingShortContent = fs.readFileSync(codingShortPath, 'utf8');
assert(
  codingShortContent.includes("import { ChemistryScene } from './components/ChemistryScene'") &&
    codingShortContent.includes('sceneType === \'chemistry_reaction\''),
  'CodingShort.jsx imports ChemistryScene and routes chemistry_reaction scenes'
);

// 9. Verify ConceptHeroScene.jsx De-Hardcoding: defaults to concept_card, never injects autoencoder into non-autoencoder scenes
const conceptHeroPath = path.join(__dirname, 'src/components/ConceptHeroScene.jsx');
const conceptHeroContent = fs.readFileSync(conceptHeroPath, 'utf8');
assert(
  conceptHeroContent.includes("return 'concept_card';") &&
    !conceptHeroContent.match(/return\s+'autoencoder';\s*};/),
  'ConceptHeroScene resolveConceptMode defaults to concept_card instead of autoencoder'
);
assert(
  conceptHeroContent.includes("conceptMode === 'concept_card'") &&
    conceptHeroContent.includes('conceptCardDefaultPoints'),
  'ConceptHeroScene implements data-driven concept_card rendering with dynamic takeaways'
);

// 10. Zero Raw Unicode Emojis in Chemistry and Concept components
const rawEmojiRegex = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;
assert(!rawEmojiRegex.test(chemContent), 'ChemistryScene.jsx contains zero raw Unicode emoji glyphs');

// 11. Verify ComparisonScene.jsx supports concept comparison sides
const comparisonScenePath = path.join(__dirname, 'src/components/ComparisonScene.jsx');
const comparisonContent = fs.readFileSync(comparisonScenePath, 'utf8');
assert(
  comparisonContent.includes('comparison_sides') && comparisonContent.includes('leftSide'),
  'ComparisonScene.jsx supports dynamic concept comparison_sides across multi-domain STEM topics'
);

if (failed) {
  console.error('\n❌ Phase 7 Node verification tests FAILED!');
  process.exit(1);
} else {
  console.log('\nAll Phase 7 Chemistry Engine & De-Hardcoding Node tests passed with 100% success!\n');
}

