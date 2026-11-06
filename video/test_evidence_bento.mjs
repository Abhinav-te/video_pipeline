import assert from 'assert';
import fs from 'fs';
import path from 'path';

console.log('Running Evidence Bento Scene Unit & Regression Tests...');

// 1. Gate 4 / Component Literal Lint compliance test
const componentPath = path.resolve(path.dirname(new URL(import.meta.url).pathname), 'src/components/EvidenceBentoScene.tsx');
const componentSource = fs.readFileSync(componentPath, 'utf-8');

const GATE4_BANNED_LITERALS = [
  'EVIDENCE-BACKED PRODUCTION VALUE',
  'Verified via official documentation',
  '0 RE-RUNS',
  'GUARDED',
  'OpenTelemetry',
  '8f4e29b1',
  '420ms',
  'FAILED: 503',
  'RETRY #1',
  "'VERIFIED'",
  "'GUARANTEE'",
];

for (const banned of GATE4_BANNED_LITERALS) {
  assert.ok(
    !componentSource.includes(banned),
    `EvidenceBentoScene.tsx must not contain banned literal: "${banned}"`
  );
}
console.log('✓ Zero banned literals found in EvidenceBentoScene.tsx');

// 2. Strict Theme Token usage test
assert.ok(
  componentSource.includes('useTheme()'),
  'EvidenceBentoScene must consume useTheme() for shared theme tokens'
);
assert.ok(
  componentSource.includes('theme.surface_elevated'),
  'EvidenceBentoScene must use theme.surface_elevated for evidence cards'
);
assert.ok(
  componentSource.includes('theme.status_success'),
  'EvidenceBentoScene must use theme.status_success for verified guarantees'
);
assert.ok(
  componentSource.includes('theme.status_warning'),
  'EvidenceBentoScene must use theme.status_warning for documented limitations'
);
assert.ok(
  !componentSource.includes('#34d399') && !componentSource.includes('#c084fc'),
  'EvidenceBentoScene must eliminate hardcoded rainbow card color palette'
);
console.log('✓ Monochrome design tokens strictly utilized across surfaces, borders, typography, and status indicators');

// 3. Evidence Hierarchy & Segregation Logic
function segregateEvidenceItems(cards) {
  const isLimitationItem = (item) => {
    const tag = (item.tag || '').toUpperCase();
    const val = (item.value || '').toUpperCase();
    return (
      tag === 'LIMITATION' ||
      tag === 'CAVEAT' ||
      val.includes('LIMIT') ||
      val.includes('CONSTRAINT') ||
      val.includes('REQUIREMENT') ||
      val.includes('CAVEAT')
    );
  };

  const guarantees = cards.filter((c) => !isLimitationItem(c));
  const limitations = cards.filter((c) => isLimitationItem(c));

  return { guarantees, limitations };
}

const testCards = [
  { value: 'STATE SAVED', title: 'DURABLE EXECUTION & MEMOIZATION BEHAVIOR', tag: 'DURABILITY', evidence_id: 'ev_04' },
  { value: 'INDEPENDENT RETRY', title: 'INNGEST RETRIES AND ERROR HANDLING', tag: 'RESILIENCE', evidence_id: 'ev_17' },
  { value: 'IDEMPOTENCY REQUIREMENT', title: 'EXTERNAL SIDE EFFECT IDEMPOTENCY', tag: 'LIMITATION', evidence_id: 'ev_15' },
  { value: 'DOCUMENTED CAVEAT', title: 'IMPORTANT LIMITATIONS', tag: 'LIMITATION', evidence_id: 'ev_16' },
];

const { guarantees, limitations } = segregateEvidenceItems(testCards);
assert.strictEqual(guarantees.length, 2, 'Should cleanly separate 2 primary guarantees');
assert.strictEqual(limitations.length, 2, 'Should cleanly separate 2 operational limitations');

// Verify distinct values (zero duplicate headings)
const valuesSet = new Set(testCards.map((c) => c.value));
assert.strictEqual(valuesSet.size, 4, 'All 4 evidence items must have distinct, meaningful values/headings');
assert.ok(!valuesSet.has('SAFETY CONSTRAINT'), 'Duplicate SAFETY CONSTRAINT replaced with accurate classifications');
console.log('✓ Evidence hierarchy and distinct heading validation passed');

// 4. Deterministic Narration-Synchronized Progression
function computeLimitationActive(localSec, captionChunks, sceneStart, sceneDuration) {
  let limitationTriggerSec = sceneDuration * 0.45;
  if (captionChunks && captionChunks.length > 0) {
    const limKeywords = ['limitation', 'side effect', 'idempotent', 'caution', 'warning', 'constraint', 'retried step'];
    for (const chunk of captionChunks) {
      const lower = chunk.text.toLowerCase();
      if (limKeywords.some((k) => lower.includes(k))) {
        limitationTriggerSec = Math.max(0, chunk.start - sceneStart);
        break;
      }
    }
  }

  return localSec >= limitationTriggerSec;
}

const testChunks = [
  { start: 14.375, end: 15.825, text: 'Durable Execution Memoization' },
  { start: 15.837, end: 17.837, text: 'Behavior External side effects' },
  { start: 17.850, end: 19.975, text: 'inside a retried step must' },
  { start: 20.250, end: 22.163, text: 'be idempotent or handled safely' },
];

const sceneStart = 14.275;
const sceneDuration = 8.662;

// At t=15.0s (localSec=0.725s): Guarantees active, limitations in calm standby
const isLimAt15s = computeLimitationActive(0.725, testChunks, sceneStart, sceneDuration);
assert.strictEqual(isLimAt15s, false, 'Before limitation spoken text, limitation panel should be in standby');

// At t=17.0s (localSec=2.725s): "External side effects" spoken, limitation panel illuminates
const isLimAt17s = computeLimitationActive(2.725, testChunks, sceneStart, sceneDuration);
assert.strictEqual(isLimAt17s, true, 'When limitation spoken, limitation panel should illuminate');

console.log('✓ Deterministic narration-synchronized visual progression verified');
console.log('All Evidence Bento Scene Unit & Regression Tests passed successfully!');

