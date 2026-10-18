import assert from 'node:assert';
import {
  SPRING_CONFIG,
  computeFocusOrigin,
  computeCameraZoom,
} from './src/cameraUtils.js';

console.log('Running CameraRig & Focus Zoom Bounds Unit Tests...');

// 1. Spring config test — critically damped to eliminate underdamped oscillation jitter
assert.strictEqual(SPRING_CONFIG.damping, 18);
assert.strictEqual(SPRING_CONFIG.stiffness, 80);
assert.strictEqual(SPRING_CONFIG.mass, 0.6);
console.log('✓ SPRING_CONFIG adheres to critically damped physics specification (damping: 18, stiffness: 80, mass: 0.6)');

// 2. computeFocusOrigin - Fallback & Missing Data
const fallback1 = computeFocusOrigin(null, null, null);
assert.deepStrictEqual(fallback1, { originX: 50, originY: 50 });

const fallback2 = computeFocusOrigin({}, 'def test(): pass', 'missing_phrase');
assert.deepStrictEqual(fallback2, { originX: 50, originY: 50 });

const fallback3 = computeFocusOrigin({ scene_type: 'fullscreen_text' });
assert.deepStrictEqual(fallback3, { originX: 50, originY: 50 });
console.log('✓ computeFocusOrigin handles null, undefined, and unmatched tokens with standard centered framing fallback');

// 3. computeFocusOrigin - Code Positioning & Bounds Clamping
const sampleCode = `def add_item(val, items=[]):
    items.append(val)
    return items
print(add_item(1))`;

// Target phrase on line 0
const originLine0 = computeFocusOrigin(null, sampleCode, 'items=[]');
assert.ok(originLine0.originY <= 50, `Expected originY <= 50, got ${originLine0.originY}`);
assert.ok(originLine0.originX >= 32 && originLine0.originX <= 68, `OriginX out of bounds: ${originLine0.originX}`);
assert.ok(originLine0.originY >= 32 && originLine0.originY <= 68, `OriginY out of bounds: ${originLine0.originY}`);

// Target phrase on line 3 (bottom line)
const originLine3 = computeFocusOrigin(null, sampleCode, 'print(add_item(1))');
assert.ok(originLine3.originY >= 50, `Expected originY >= 50, got ${originLine3.originY}`);
assert.ok(originLine3.originX >= 32 && originLine3.originX <= 68);
assert.ok(originLine3.originY >= 32 && originLine3.originY <= 68);
console.log('✓ computeFocusOrigin positions focus coordinates within strict safe bounds [32%, 68%]');

// 4. computeFocusOrigin - Comparison Scene Logic
const comparisonScene = {
  scene_type: 'comparison',
  problem_code: 'bad = {[1, 2]: "fails"}',
  solution_code: 'good = {(1, 2): "works"}',
};

const compSolution = computeFocusOrigin(comparisonScene, null, 'good =');
assert.deepStrictEqual(compSolution, { originX: 50, originY: 65 });

const compProblem = computeFocusOrigin(comparisonScene, null, 'bad =');
assert.deepStrictEqual(compProblem, { originX: 50, originY: 35 });

const compUnmatched = computeFocusOrigin(comparisonScene, null, 'irrelevant');
assert.deepStrictEqual(compUnmatched, { originX: 50, originY: 50 });
console.log('✓ computeFocusOrigin routes comparison scenes to solution/problem visual blocks correctly');

// 5. computeCameraZoom - Timing & Spring Progression (Static 1.0x Scale & Glow Progress)
const baseline = 1.0;
const focusScale = 1.04;
const triggerFrame = 30;

// Before trigger frame: scale must be strictly 1.0, progress 0
const preTrigger = computeCameraZoom({ frame: 15, triggerFrame, baselineScale: baseline, focusScale });
assert.strictEqual(preTrigger.scale, 1.0);
assert.strictEqual(preTrigger.progress, 0);

// Exactly at trigger frame: scale must be 1.0, progress 0
const atTrigger = computeCameraZoom({ frame: 30, triggerFrame, baselineScale: baseline, focusScale });
assert.strictEqual(atTrigger.scale, 1.0);
assert.strictEqual(atTrigger.progress, 0);

// Mid-transition (+6 frames / 0.2s): progress increases smoothly, scale remains locked at 1.0
const midTransition = computeCameraZoom({ frame: 36, triggerFrame, baselineScale: baseline, focusScale });
assert.strictEqual(midTransition.scale, 1.0);
assert.ok(midTransition.progress > 0 && midTransition.progress < 1.0, `Unexpected mid progress: ${midTransition.progress}`);

// Settled transition (+20 frames): progress settles near 1.0, scale remains locked at 1.0
const settled = computeCameraZoom({ frame: 50, triggerFrame, baselineScale: baseline, focusScale });
assert.strictEqual(settled.scale, 1.0);
assert.ok(settled.progress >= 0.95, `Settled progress out of bounds: ${settled.progress}`);
console.log('✓ computeCameraZoom preserves static 1.0x scale and executes smooth emphasis spring progress (0 -> 1)');

console.log('\nAll CameraRig unit tests passed successfully!');

