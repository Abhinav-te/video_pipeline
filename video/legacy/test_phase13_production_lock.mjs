/**
 * video/test_phase13_production_lock.mjs
 * Node unit tests for Phase 13 Final Production Lock:
 *   1. MathScene.jsx zero hardcoded Euler/imaginary unit text on non-Euler domains.
 *   2. BentoGridScene.jsx renders 4 visually distinct mini-SVGs rather than repeating t-SNE rings.
 *   3. GraphScene.jsx Y-axis title and legend box bounding coordinates never overlap.
 *   4. ComparisonScene.jsx bottom green summary bar strips pipe duplicate suffixes.
 */

import esbuild from 'esbuild';
import ReactDOMServer from 'react-dom/server';
import React from 'react';
import fs from 'fs';
import path from 'path';
import assert from 'assert';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const mockRemotionPlugin = {
  name: 'mock-remotion',
  setup(build) {
    build.onResolve({ filter: /^remotion$/ }, () => ({ path: 'remotion', namespace: 'mock' }));
    build.onLoad({ filter: /^remotion$/, namespace: 'mock' }, () => ({
      contents: `
        export const useCurrentFrame = () => 15;
        export const useVideoConfig = () => ({ fps: 30, width: 1080, height: 1920 });
        export const interpolate = (f, [a, b], [c, d]) => c + ((f - a) / (b - a)) * (d - c);
        export const spring = () => 1;
        export const staticFile = (path) => path;
        export const OffthreadVideo = (props) => null;
        export const Sequence = ({ children }) => children;
        export const AbsoluteFill = (props) => null;
      `,
      loader: 'js',
    }));
  },
};

const cacheDir = path.resolve(__dirname, 'node_modules/.cache');
fs.mkdirSync(cacheDir, { recursive: true });

async function bundleComponent(entryRelPath, outName) {
  const outfile = path.join(cacheDir, outName);
  await esbuild.build({
    entryPoints: [path.resolve(__dirname, entryRelPath)],
    bundle: true,
    format: 'esm',
    outfile,
    plugins: [mockRemotionPlugin],
    external: ['react', 'react-dom'],
  });
  return await import(outfile);
}

async function runTests() {
  console.log('🧪 Starting Phase 13 Node Production Lock Tests...\n');

  // ── 1. MathScene.jsx De-Hardcoding ──────────────────────────────────────────
  console.log('1️⃣ Testing MathScene.jsx zero hardcoded Euler/imaginary unit text...');
  const { MathScene } = await bundleComponent('src/components/MathScene.jsx', 'test_mathscene.mjs');

  const testDomains = ['electrical', 'mechanics', 'quantum_physics', 'chemistry'];
  for (const dom of testDomains) {
    const html = ReactDOMServer.renderToStaticMarkup(React.createElement(MathScene, {
      scene: {
        domain: dom,
        title: `${dom.toUpperCase()} Fundamental Theorem`,
        spoken_text: `Rigorous mathematical formulation for ${dom}.`,
      },
      sceneStartFrame: 0,
    }));

    assert(!html.includes("Euler's Identity"), `MathScene leaked "Euler's Identity" in domain ${dom}`);
    assert(!html.includes("EULER DERIVATION"), `MathScene leaked "EULER DERIVATION" in domain ${dom}`);
    assert(!html.includes("imaginary unit"), `MathScene leaked "imaginary unit" in domain ${dom}`);
    assert(!html.includes("Constants Linked: e, i, π, 1, 0"), `MathScene leaked Euler constants in domain ${dom}`);
    assert(html.includes(`${dom.toUpperCase()} • MATHEMATICAL FORMULATION`), `MathScene missing domain eyebrow in ${dom}`);
  }

  // Electrical specific check
  const elecHtml = ReactDOMServer.renderToStaticMarkup(React.createElement(MathScene, {
    scene: {
      domain: 'electrical',
      title: 'Optimal Power Flow Dispatch',
      spoken_text: 'Active power balance and branch thermal limit.',
    },
    sceneStartFrame: 0,
  }));
  assert(elecHtml.includes('Active Power Balance Constraint'), 'Electrical MathScene missing Active Power Balance');
  assert(elecHtml.includes('Thermal Line Limit &amp; Economic Dispatch'), 'Electrical MathScene missing Thermal Line Limit');
  assert(elecHtml.includes('Optimal Power Flow (OPF)'), 'Electrical MathScene missing OPF footer label');
  console.log('   ✅ MathScene: zero Euler leakage, domain steps & intuition verified.');

  // ── 2. BentoGridScene.jsx 4 Distinct Mini-SVGs ──────────────────────────────
  console.log('2️⃣ Testing BentoGridScene.jsx distinct 4 mini-SVG rendering...');
  const { BentoGridScene } = await bundleComponent('src/components/BentoGridScene.jsx', 'test_bentogrid.mjs');

  const genericBentoHtml = ReactDOMServer.renderToStaticMarkup(React.createElement(BentoGridScene, {
    scene: {
      domain: 'electrical',
      section_title: 'POWER SYSTEMS MASTER MATRIX',
      subtitle: '4 Foundational Principles',
      cards: [
        { title: 'KVL & KCL', algo_type: 'unknown_law_1', category: 'CIRCUIT', description: 'Conservation laws' },
        { title: 'Thévenin / Norton', algo_type: 'unknown_law_2', category: 'EQUIVALENCE', description: 'Linear reduction' },
        { title: 'Max Power', algo_type: 'unknown_law_3', category: 'IMPEDANCE', description: 'Peak transfer' },
        { title: 'Smart Grid OPF', algo_type: 'unknown_law_4', category: 'DISPATCH', description: 'Optimal power flow' },
      ],
    },
    sceneStartFrame: 0,
  }));

  // Card 0: Loop / Node
  assert(genericBentoHtml.includes('NODE CONSERVATION ΣI = 0'), 'Bento Card 0 missing Node Conservation graphic');
  // Card 1: Duality / Equivalence
  assert(genericBentoHtml.includes('EQUIVALENCE: 2-TERMINAL DUALITY'), 'Bento Card 1 missing 2-Terminal Duality graphic');
  // Card 2: Peak Curve
  assert(genericBentoHtml.includes('MAXIMUM TRANSFER: dP/dR = 0'), 'Bento Card 2 missing Maximum Transfer Peak curve');
  // Card 3: 4-Node Grid
  assert(genericBentoHtml.includes('4-NODE MESH TOPOLOGY &amp; OPF FLOW'), 'Bento Card 3 missing 4-Node Mesh topology graphic');

  // Verify that the 3 t-SNE rings (r="38") are NOT repeated 4 times across cards
  const tsneRingMatches = (genericBentoHtml.match(/r="38"/g) || []).length;
  assert.strictEqual(tsneRingMatches, 0, `t-SNE fallback rings (r="38") found in non-ML bento grid (${tsneRingMatches} times)`);
  console.log('   ✅ BentoGridScene: 4 distinct mini-SVGs rendered without repeating t-SNE rings.');

  // ── 3. GraphScene.jsx Legend & Y-Axis Title Layout ──────────────────────────
  console.log('3️⃣ Testing GraphScene.jsx Y-axis title coordinates and legend clearance...');
  const { GraphScene } = await bundleComponent('src/components/GraphScene.jsx', 'test_graphscene.mjs');

  const graphHtml = ReactDOMServer.renderToStaticMarkup(React.createElement(GraphScene, {
    scene: {
      domain: 'electrical',
      title: 'Power Transfer & Marginal Cost Curves',
      graph_data: {
        x_label: 'Load Resistance R_L (Ω)',
        y_label: 'Power P_L (W) & $/MWh',
      },
    },
    sceneStartFrame: 0,
  }));

  // Verify Y-axis title is left-aligned at x="90" y="55" with textAnchor="start"
  assert(graphHtml.includes('x="90" y="55"'), 'Electrical Y-axis title missing left-aligned coordinates x="90" y="55"');
  assert(graphHtml.includes('textAnchor="start"') || graphHtml.includes('text-anchor="start"'), 'Electrical Y-axis title missing text-anchor="start"');

  // Verify legend box starts at x >= 536 (canvasWidth - 360 = 536 or canvasWidth - 350 = 546)
  const legendMatch = graphHtml.match(/transform="translate\((\d+),\s*40\)"/);
  assert(legendMatch, 'Legend box translation not found in GraphScene');
  const legendX = parseInt(legendMatch[1], 10);
  assert(legendX >= 530, `Legend X coordinate (${legendX}) is too close to left Y-axis title`);

  // Clearance calculation: Title at x=90 is ~230px wide (ends at x=320), legend starts at legendX >= 536. Gap is > 200px!
  const clearanceGap = legendX - (90 + 230);
  assert(clearanceGap > 100, `Clearance between Y-axis title and legend is insufficient: ${clearanceGap}px`);
  console.log(`   ✅ GraphScene: Y-axis title left-aligned at x=90, legend at x=${legendX} (Clearance: ${clearanceGap}px gap, zero collision).`);

  // ── 4. ComparisonScene.jsx Clean Summary Deduplication ──────────────────────
  console.log('4️⃣ Testing ComparisonScene.jsx bottom green summary bar deduplication...');
  const { ComparisonScene } = await bundleComponent('src/components/ComparisonScene.jsx', 'test_comparisonscene.mjs');

  const compHtml = ReactDOMServer.renderToStaticMarkup(React.createElement(ComparisonScene, {
    scene: {
      domain: 'electrical',
      title: 'Circuit Reduction Methods',
      comparison_footer: 'NETWORK EQUIVALENCE: Linear network reduction simplifies multi-bus OPF solver complexity by 100x | NETWORK EQUIVALENCE: V_th = V_oc, R_th = V_oc / I_sc | POWER FLOW: ΣP_gen = ΣP_load + P_loss',
    },
    sceneStartFrame: 0,
  }));

  // Bottom green box must have clean 1-sentence takeaway
  assert(compHtml.includes('KEY TAKEAWAY: Linear network reduction simplifies multi-bus OPF solver complexity by 100x'), 'Missing clean 1-sentence KEY TAKEAWAY');
  assert(!compHtml.includes('Linear network reduction simplifies multi-bus OPF solver complexity by 100x | NETWORK EQUIVALENCE: V_th = V_oc'), 'Duplicate pipe suffix was not stripped in comparison footer');
  console.log('   ✅ ComparisonScene: Pipe duplicate suffixes stripped, clean 1-sentence takeaway rendered.');

  console.log('\n🎉 ALL 4 PHASE 13 NODE PRODUCTION LOCK TESTS PASSED (100%)!\n');
}

runTests().catch((err) => {
  console.error('\n❌ Test failed with error:', err);
  process.exit(1);
});

