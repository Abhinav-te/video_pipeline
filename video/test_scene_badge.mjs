import assert from 'node:assert';
import {
  SPRING_BADGE_CONFIG,
  BADGE_THEMES,
} from './src/badgeUtils.js';

console.log('Running SceneBadge Component & Physics Unit Tests...');

// 1. Spring physics configuration
assert.strictEqual(SPRING_BADGE_CONFIG.damping, 18, 'Damping must be 18');
assert.strictEqual(SPRING_BADGE_CONFIG.stiffness, 80, 'Stiffness must be 80');
assert.strictEqual(SPRING_BADGE_CONFIG.mass, 0.6, 'Mass must be 0.6');
console.log('✓ SPRING_BADGE_CONFIG matches critically damped stabilization physics (damping: 18, stiffness: 80, mass: 0.6)');

// 2. Palette and theme presets (warning, success, accent, info)
const expectedThemes = ['warning', 'success', 'accent', 'info', 'performance', 'insight'];
for (const theme of expectedThemes) {
  assert.ok(BADGE_THEMES[theme], `Missing theme preset: ${theme}`);
  assert.ok(BADGE_THEMES[theme].background, `Theme ${theme} missing background`);
  assert.ok(BADGE_THEMES[theme].border, `Theme ${theme} missing border`);
  assert.ok(BADGE_THEMES[theme].color, `Theme ${theme} missing color`);
  assert.ok(BADGE_THEMES[theme].boxShadow, `Theme ${theme} missing boxShadow`);
}
console.log('✓ BADGE_THEMES defines rich visual palettes for warning, success, accent, info, performance, insight');

// 3. Fallback color resolution
assert.strictEqual(BADGE_THEMES.warning.color, '#ff7b72', 'Warning color mismatch');
assert.strictEqual(BADGE_THEMES.success.color, '#3fb950', 'Success color mismatch');
assert.strictEqual(BADGE_THEMES.accent.color, '#e3b341', 'Accent color mismatch');
assert.strictEqual(BADGE_THEMES.performance.color, '#e3b341', 'Performance color mismatch');
assert.strictEqual(BADGE_THEMES.insight.color, '#d2a8ff', 'Insight color mismatch');
assert.strictEqual(BADGE_THEMES.info.color, '#58a6ff', 'Info color mismatch');
console.log('✓ Color tokens verified across all semantic categories');

console.log('\nAll SceneBadge unit tests passed successfully!');
