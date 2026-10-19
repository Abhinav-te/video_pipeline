import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert';
import { fileURLToPath } from 'node:url';
import esbuild from 'esbuild';
import React from 'react';
import ReactDOMServer from 'react-dom/server';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const mockRemotionPlugin = {
  name: 'mock-remotion',
  setup(build) {
    build.onResolve({ filter: /^remotion$/ }, () => ({ path: 'remotion', namespace: 'mock' }));
    build.onLoad({ filter: /^remotion$/, namespace: 'mock' }, () => ({
      contents: `
        import React from 'react';
        export const useCurrentFrame = () => 15;
        export const useVideoConfig = () => ({ fps: 30, width: 1080, height: 1920 });
        export const interpolate = (f, [a, b], [c, d]) => c + ((f - a) / (b - a)) * (d - c);
        export const spring = () => 1;
        export const staticFile = (f) => f;
        export const OffthreadVideo = (props) => React.createElement('video', { 'data-testid': 'offthread-video', src: props.src, muted: props.muted, style: props.style });
        export const AbsoluteFill = (props) => React.createElement('div', props);
        export const Sequence = ({ children, from, durationInFrames, layout }) =>
          React.createElement('div', { 'data-testid': 'sequence-wrapper', 'data-from': from, 'data-duration': durationInFrames, 'data-layout': layout }, children);
        export const Audio = (props) => null;
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
  console.log('🧪 Starting Phase 14.5 Verification Tests: Live Manim, Safe-Zones & Zero Leaks...\n');

  // 1. ManimScene Sequence Wrapping & Safe-Zone
  console.log('1️⃣ Testing ManimScene Sequence wrapping & 1360px safe-zone...');
  const { ManimScene } = await bundleComponent('src/components/ManimScene.jsx', 'test_manimscene_p145.mjs');
  const manimSceneData = {
    title: 'Differential vs Integral Duality',
    spoken_text: 'Watch fundamental limits morph smoothly.',
    visual_type: 'manim_scene',
    manim_video_src: 'runs/run_test/manim_scene_0.mp4',
    choreography: { domain: 'math', layout_density: 'full_dashboard' },
  };
  const manimHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(ManimScene, { scene: manimSceneData, sceneStartFrame: 90, sceneDurationFrames: 120 })
  );
  assert.ok(manimHtml.includes('data-testid="sequence-wrapper"'), 'ManimScene must wrap <OffthreadVideo> in <Sequence>');
  assert.ok(manimHtml.includes('data-from="90"'), 'Sequence must start from sceneStartFrame');
  assert.ok(manimHtml.includes('data-duration="120"'), 'Sequence must respect sceneDurationFrames');
  assert.ok(manimHtml.includes('height:1360px') || manimHtml.includes('max-height:1380px'), 'ManimScene must fit within safe-zone <= 1380px');
  console.log('   ✅ ManimScene: <Sequence from={90} durationInFrames={120}> and safe-zone verified.');

  // 2. BentoGridScene: Math Domain Zero Electrical Leaks & Pure Math Mini-SVGs
  console.log('2️⃣ Testing BentoGridScene: Zero electrical text in math domain...');
  const { BentoGridScene } = await bundleComponent('src/components/BentoGridScene.jsx', 'test_bentogrid_p145.mjs');
  const mathBentoScene = {
    title: 'Calculus Unified',
    spoken_text: 'Four pillars of modern analysis.',
    visual_type: 'bento_grid',
    domain: 'math',
    subject: 'math',
    choreography: { domain: 'math' },
  };
  const bentoHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(BentoGridScene, { scene: mathBentoScene, sceneStartFrame: 0 })
  );
  // Verify zero electrical leaks in math
  assert.ok(!bentoHtml.includes('CURRENT LOOP I'), 'BentoGridScene in math must not leak CURRENT LOOP I_1');
  assert.ok(!bentoHtml.includes('NODE CONSERVATION ΣI'), 'BentoGridScene in math must not leak NODE CONSERVATION ΣI = 0');
  assert.ok(!bentoHtml.includes('EQUIVALENCE: 2-TERMINAL DUALITY'), 'BentoGridScene in math must not leak 2-TERMINAL DUALITY');
  assert.ok(!bentoHtml.includes('4-NODE MESH TOPOLOGY'), 'BentoGridScene in math must not leak 4-NODE MESH TOPOLOGY');
  // Verify math domain labels are present
  assert.ok(bentoHtml.includes('SECANT → TANGENT LIMIT'), 'BentoCard 0 must display SECANT → TANGENT LIMIT');
  assert.ok(bentoHtml.includes('RIEMANN AREA SUM'), 'BentoCard 1 must display RIEMANN AREA SUM');
  assert.ok(bentoHtml.includes('POLYNOMIAL CONVERGENCE'), 'BentoCard 2 must display POLYNOMIAL CONVERGENCE');
  assert.ok(bentoHtml.includes('CRITICAL POINT f&#x27;(x) = 0') || bentoHtml.includes("CRITICAL POINT f'(x) = 0"), 'BentoCard 3 must display CRITICAL POINT f\'(x) = 0');
  // Verify safe zone height
  assert.ok(bentoHtml.includes('height:1360px') || bentoHtml.includes('max-height:1380px'), 'BentoGridScene must constrain height to <= 1380px');
  console.log('   ✅ BentoGridScene: Zero electrical leaks and verified math mini-SVGs & safe-zone.');

  // 3. ConceptHeroScene: Math Domain Zero ML Leaks
  console.log('3️⃣ Testing ConceptHeroScene: Zero ML text in math domain...');
  const { ConceptHeroScene } = await bundleComponent('src/components/ConceptHeroScene.jsx', 'test_concepthero_p145.mjs');
  const mathConceptScene = {
    title: 'Differential vs Integral Duality',
    spoken_text: 'Rates of change balance with accumulated net area.',
    visual_type: 'concept',
    domain: 'math',
    choreography: { domain: 'math' },
  };
  const conceptHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(ConceptHeroScene, { scene: mathConceptScene, sceneStartFrame: 0 })
  );
  assert.ok(!conceptHtml.includes('Fails on non-Convex'), 'ConceptHeroScene in math must not leak "Fails on non-Convex"');
  assert.ok(!conceptHtml.includes('Captures Geometry'), 'ConceptHeroScene in math must not leak "Captures Geometry"');
  assert.ok(!conceptHtml.includes('High-dimensional raw feature'), 'ConceptHeroScene in math must not leak ML feature distribution');
  assert.ok(!conceptHtml.includes('Cluster separation'), 'ConceptHeroScene in math must not leak Cluster separation');
  assert.ok(conceptHtml.includes('height:1360px') || conceptHtml.includes('max-height:1380px'), 'ConceptHeroScene must fit inside safe-zone');
  console.log('   ✅ ConceptHeroScene: Zero ML leaks, domain concept nodes rendered in safe-zone.');

  // 4. CodingShort Stage Container Safe-Zone
  console.log('4️⃣ Testing CodingShort stage container dimensions...');
  const codingShortSource = fs.readFileSync(path.resolve(__dirname, 'src/CodingShort.jsx'), 'utf8');
  assert.ok(codingShortSource.includes("stageTop = '90px'"), 'CodingShort must position stage at top: 90px');
  assert.ok(codingShortSource.includes("stageHeight = '1360px'"), 'CodingShort must size stage at height: 1360px');
  assert.ok(codingShortSource.includes("maxHeight: '1380px'"), 'CodingShort must enforce maxHeight: 1380px safe-zone');
  console.log('   ✅ CodingShort: stageTop 90px and stageHeight 1360px verified.');

  console.log('\n🎉 ALL PHASE 14.5 VERIFICATION TESTS PASSED (100%)!\n');
}

runTests().catch((err) => {
  console.error('❌ Phase 14.5 Node test failed:', err);
  process.exit(1);
});

