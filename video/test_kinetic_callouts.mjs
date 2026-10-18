import assert from 'node:assert/strict';
import {
  SPRING_CALLOUT_CONFIG,
  CALLOUT_STYLES,
  normalizeText,
  findTokenMatch,
  splitCodeByToken,
  resolveCalloutTiming,
} from './src/calloutUtils.js';

console.log('Running Kinetic Callout & Word-Synchronized Token Highlight Unit Tests...');

// 1. Spring physics specification (critically damped stabilization)
assert.deepEqual(
  SPRING_CALLOUT_CONFIG,
  { damping: 18, stiffness: 80, mass: 0.6 },
  'SPRING_CALLOUT_CONFIG must adhere strictly to critically damped spring physics'
);
console.log('✓ SPRING_CALLOUT_CONFIG matches critically damped stabilization physics (damping: 18, stiffness: 80, mass: 0.6)');

// 2. Style presets
assert.ok(CALLOUT_STYLES.pill, 'CALLOUT_STYLES.pill must exist');
assert.ok(CALLOUT_STYLES.box_glow, 'CALLOUT_STYLES.box_glow must exist');
assert.ok(CALLOUT_STYLES.badge, 'CALLOUT_STYLES.badge must exist');
assert.ok(CALLOUT_STYLES.pill.borderRadius, 'pill must specify borderRadius');
assert.ok(CALLOUT_STYLES.box_glow.border.includes('58a6ff'), 'box_glow must have blue glow border');
assert.ok(CALLOUT_STYLES.badge.background.includes('gradient'), 'badge must have gradient styling');
console.log('✓ CALLOUT_STYLES exposes pill, box_glow, and badge visual presets');

// 3. Text normalization
assert.equal(normalizeText('  Python, Dev!  '), 'python dev');
assert.equal(normalizeText(null), '');
assert.equal(normalizeText(undefined), '');
assert.equal(normalizeText(123), '');
console.log('✓ normalizeText sanitizes whitespace, casing, and punctuation');

// 4. Robust token matching
const sampleCode = `data = "developer"\nlength = len(data)\nif length > 5:\n    print(length)`;

// 4a. Exact match
const exact = findTokenMatch(sampleCode, 'length = len(data)');
assert.ok(exact, 'Should find exact match');
assert.equal(sampleCode.slice(exact.index, exact.index + exact.length), 'length = len(data)');

// 4b. Case-insensitive match
const caseInsensitive = findTokenMatch(sampleCode, 'LENGTH = LEN(DATA)');
assert.ok(caseInsensitive, 'Should match case-insensitively');
assert.equal(sampleCode.slice(caseInsensitive.index, caseInsensitive.index + caseInsensitive.length), 'length = len(data)');

// 4c. Whitespace-tolerant match
const whitespaceTolerant = findTokenMatch(sampleCode, 'length=len(data)');
assert.ok(whitespaceTolerant, 'Should match despite whitespace variations');

// 4d. Unmatched / null / empty fallback
assert.equal(findTokenMatch(sampleCode, 'non_existent_token'), null);
assert.equal(findTokenMatch(sampleCode, ''), null);
assert.equal(findTokenMatch(null, 'test'), null);
assert.equal(findTokenMatch(sampleCode, null), null);
console.log('✓ findTokenMatch handles exact, case-insensitive, whitespace variations, and safe fallbacks');

// 5. Code splitting by token
const splitResult = splitCodeByToken(sampleCode, 'length = len(data)');
assert.equal(splitResult.before, 'data = "developer"\n');
assert.equal(splitResult.match, 'length = len(data)');
assert.equal(splitResult.after, '\nif length > 5:\n    print(length)');

const fallbackSplit = splitCodeByToken(sampleCode, 'unknown_token');
assert.equal(fallbackSplit.before, sampleCode);
assert.equal(fallbackSplit.match, null);
assert.equal(fallbackSplit.after, '');
console.log('✓ splitCodeByToken decomposes snippet into before, match, and after segments cleanly');

// 6. Timing resolution with Whisper words
const mockWords = [
  { word: 'Usually,', start: 4.22, end: 4.94 },
  { word: 'you', start: 5.0, end: 5.2 },
  { word: 'create', start: 5.2, end: 5.6 },
  { word: 'temporary', start: 5.6, end: 6.2 },
  { word: 'variables', start: 6.2, end: 6.8 },
  { word: 'for', start: 6.8, end: 7.0 },
  { word: 'conditions.', start: 7.0, end: 7.6 },
];

const mockSceneWithWord = {
  scene_type: 'code_reveal',
  start_time: 4.22,
  emphasis_time: 5.6,
  emphasis_word: 'temporary',
  focus_phrase: 'temporary variables',
};

const timingMatched = resolveCalloutTiming({
  scene: mockSceneWithWord,
  words: mockWords,
  fps: 30,
  nextSceneStartTime: 8.88,
});

assert.equal(timingMatched.matchedWord?.word, 'temporary');
assert.equal(timingMatched.startFrame, Math.round(5.6 * 30));
assert.ok(timingMatched.endFrame > timingMatched.startFrame);
assert.ok(timingMatched.endFrame <= Math.round(8.88 * 30));

// 7. Timing resolution graceful fallback without Whisper word match
const mockSceneFallback = {
  scene_type: 'code_reveal',
  start_time: 4.22,
  emphasis_time: 5.0,
  emphasis_word: 'unspoken_word',
};

const timingFallback = resolveCalloutTiming({
  scene: mockSceneFallback,
  words: mockWords,
  fps: 30,
  nextSceneStartTime: 8.88,
});

assert.equal(timingFallback.matchedWord, null);
assert.equal(timingFallback.startFrame, Math.round(5.0 * 30));
assert.ok(timingFallback.endFrame > timingFallback.startFrame);

console.log('✓ resolveCalloutTiming extracts exact Whisper word timestamps with graceful fallback to emphasis_time');

console.log('\nAll Kinetic Callout unit tests passed successfully!');

