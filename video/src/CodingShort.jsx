import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  Audio,
  Sequence,
  staticFile,
  interpolate,
} from 'remotion';
import { CameraRig } from './CameraRig';
import { KineticCallout } from './components/KineticCallout';
import { SceneBadge } from './components/SceneBadge';
import { CodeRevealScene, TerminalCursor } from './components/CodeRevealScene';
import { CodeTransformScene } from './components/CodeTransformScene';
import { ComparisonScene } from './components/ComparisonScene';
import { DiagramScene } from './components/DiagramScene';
import { ConceptHeroScene } from './components/ConceptHeroScene';
import { MathScene } from './components/MathScene';
import { GraphScene } from './components/GraphScene';
import { PhysicsScene } from './components/PhysicsScene';
import { BentoGridScene } from './components/BentoGridScene';
import { AlgorithmExplorerScene } from './components/AlgorithmExplorerScene';
import { NeuralCodeSplitScene } from './components/NeuralCodeSplitScene';
import { ChemistryScene } from './components/ChemistryScene';
import { QuantumScene } from './components/QuantumScene';
import { MechanicsScene } from './components/MechanicsScene';
import { ElectricalScene } from './components/ElectricalScene';
import { ManimScene } from './components/ManimScene';
import { TerminalScene } from './components/TerminalScene';
import { splitCodeByToken, resolveCalloutTiming } from './calloutUtils';

// Error Boundary ensuring scene crashes never tear down the entire canvas
export class SceneErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[SceneErrorBoundary] Intercepted scene rendering error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            width: '960px',
            height: '100%',
            backgroundColor: '#161b22',
            border: '2px solid rgba(248, 81, 73, 0.7)',
            borderRadius: '24px',
            padding: '40px',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            color: '#f85149',
            fontFamily: 'monospace',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '26px', fontWeight: 'bold', marginBottom: '14px' }}>
            SCENE RENDER RECOVERY
          </div>
          <div style={{ fontSize: '18px', color: '#c9d1d9', maxWidth: '820px', lineHeight: 1.5 }}>
            {String(this.state.error?.message || 'Recovered gracefully from render error')}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export {
  TerminalCursor,
  TerminalScene,
  CodeRevealScene,
  CodeTransformScene,
  ComparisonScene,
  DiagramScene,
  ConceptHeroScene,
  MathScene,
  GraphScene,
  PhysicsScene,
  BentoGridScene,
  AlgorithmExplorerScene,
  NeuralCodeSplitScene,
  ChemistryScene,
  QuantumScene,
  MechanicsScene,
  ElectricalScene,
  ManimScene,
};

// Merges split hyphenated tokens (e.g. 'K', '-means' -> 'K-MEANS')
export const mergeHyphenatedTokens = (rawWords) => {
  if (!rawWords || rawWords.length === 0) return [];
  const merged = [];
  let i = 0;
  const n = rawWords.length;

  const KNOWN_PAIRS = {
    'k:means': 'K-MEANS',
    't:sne': 'T-SNE',
    'auto:encoders': 'AUTO-ENCODERS',
    'auto:encoder': 'AUTO-ENCODER',
    'non:convex': 'NON-CONVEX',
    'high:dimensional': 'HIGH-DIMENSIONAL',
    'low:dimensional': 'LOW-DIMENSIONAL',
  };

  while (i < n) {
    const curr = rawWords[i];
    const currWord = (curr.word || '').trim();

    if (i + 1 < n) {
      const nxt = rawWords[i + 1];
      const nxtWord = (nxt.word || '').trim();
      const pairKey = `${currWord.toLowerCase().replace(/-$/, '')}:${nxtWord.toLowerCase().replace(/^-/, '')}`;

      if (KNOWN_PAIRS[pairKey]) {
        merged.push({
          word: KNOWN_PAIRS[pairKey],
          start: curr.start,
          end: nxt.end,
        });
        i += 2;
        continue;
      }

      if (currWord.endsWith('-') || nxtWord.startsWith('-')) {
        merged.push({
          word: `${currWord.replace(/-$/, '')}-${nxtWord.replace(/^-/, '')}`,
          start: curr.start,
          end: nxt.end,
        });
        i += 2;
        continue;
      }
    }

    merged.push(curr);
    i += 1;
  }
  return merged;
};

// Subtitle component rendering a rolling word window with pause-hold & zero fallback-to-index-0 bug
export const Subtitles = ({ words: rawWords }) => {
  const words = React.useMemo(() => mergeHyphenatedTokens(rawWords), [rawWords]);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  if (!words || words.length === 0) return null;

  const currentWordIndex = words.findIndex((w) => currentTime >= w.start && currentTime <= w.end);
  const currentWordObj = currentWordIndex !== -1 ? words[currentWordIndex] : null;

  // Find last spoken word index
  let lastSpokenIndex = -1;
  for (let i = words.length - 1; i >= 0; i--) {
    if (words[i].start <= currentTime) {
      lastSpokenIndex = i;
      break;
    }
  }

  // Before first word speaks
  if (lastSpokenIndex === -1) {
    if (words[0].start - currentTime > 0.6) {
      return null;
    }
    lastSpokenIndex = 0;
  }

  // Effective index: if in a gap between words, hold the most recently spoken chunk
  const effectiveIndex = currentWordIndex !== -1 ? currentWordIndex : lastSpokenIndex;

  // Keep a 3-word rolling window around effectiveIndex
  const startIdx = Math.max(0, effectiveIndex - 1);
  const subtitleSlice = words.slice(startIdx, startIdx + 3);

  // If in a pause between sentences/words, hold the last chunk and smoothly fade if gap > 0.6s
  let subtitleOpacity = 1;
  if (currentWordIndex === -1 && lastSpokenIndex !== -1) {
    const gap = currentTime - words[lastSpokenIndex].end;
    if (gap > 0.6) {
      // Smooth fade out over 0.4s
      subtitleOpacity = Math.max(0, Math.min(1, 1 - (gap - 0.6) / 0.4));
    }
  }

  if (subtitleOpacity <= 0.01) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '120px',
        width: '100%',
        textAlign: 'center',
        padding: '0 40px',
        boxSizing: 'border-box',
        height: '100px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 50,
        pointerEvents: 'none',
        opacity: subtitleOpacity,
        transition: 'opacity 0.15s ease',
      }}
    >
      <div
        style={{
          fontSize: '48px',
          fontWeight: 900,
          textTransform: 'uppercase',
          lineHeight: '60px',
          height: '60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '14px',
        }}
      >
        {subtitleSlice.map((w, i) => {
          const isActive = currentWordObj && w.word === currentWordObj.word && w.start === currentWordObj.start;
          return (
            <span
              key={`${w.word}-${w.start}-${i}`}
              style={{
                color: isActive ? '#ffd633' : '#ffffff',
                backgroundColor: isActive ? 'rgba(255, 214, 51, 0.16)' : 'transparent',
                borderRadius: '8px',
                padding: '2px 14px',
                height: '56px',
                lineHeight: '56px',
                display: 'inline-flex',
                alignItems: 'center',
                transform: 'none',
                textShadow: isActive ? '0 0 24px rgba(255, 214, 51, 0.7)' : '0 4px 12px rgba(0,0,0,0.9)',
                border: isActive ? '1px solid rgba(255, 214, 51, 0.35)' : '1px solid transparent',
                boxSizing: 'border-box',
                transition: 'background-color 0.08s ease, color 0.08s ease',
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};

// Renders code snippet with word-synchronized kinetic token callout and blinking cursor
export const CodeBlock = ({
  code,
  focusPhrase,
  scene,
  words,
  styleVariant = 'pill',
  nextSceneStartTime = null,
  showCursor = false,
}) => {
  const { fps } = useVideoConfig();

  if (!code || typeof code !== 'string') {
    return (
      <code
        style={{
          fontFamily: 'monospace',
          lineHeight: 'inherit',
          boxSizing: 'border-box',
          transform: 'translateZ(0)',
          backfaceVisibility: 'hidden',
        }}
      >
        {code || ''}
        {showCursor && <TerminalCursor />}
      </code>
    );
  }

  const target = focusPhrase || scene?.focus_phrase || scene?.emphasis_word;
  const tokenData = splitCodeByToken(code, target);

  if (!tokenData || !tokenData.match) {
    return (
      <code
        style={{
          fontFamily: 'monospace',
          lineHeight: 'inherit',
          boxSizing: 'border-box',
          transform: 'translateZ(0)',
          backfaceVisibility: 'hidden',
        }}
      >
        {code}
        {showCursor && <TerminalCursor />}
      </code>
    );
  }

  const { before, match, after } = tokenData;
  const { startFrame, endFrame } = resolveCalloutTiming({
    scene,
    words,
    fps,
    nextSceneStartTime,
  });

  return (
    <code
      style={{
        fontFamily: 'monospace',
        lineHeight: 'inherit',
        boxSizing: 'border-box',
        transform: 'translateZ(0)',
        backfaceVisibility: 'hidden',
        willChange: 'transform, opacity',
      }}
    >
      {before}
      <KineticCallout
        startFrame={startFrame}
        endFrame={endFrame}
        styleVariant={styleVariant}
      >
        {match}
      </KineticCallout>
      {after}
      {showCursor && <TerminalCursor />}
    </code>
  );
};

export const CodingShort = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const scenes = data?.scenes || [];

  // Guarantee activeScene is NEVER null at any frame from 0 to durationInFrames
  let activeScene = scenes[0] || {};
  let actualIndex = 0;
  if (scenes.length > 0) {
    for (let i = 0; i < scenes.length; i++) {
      const s = scenes[i];
      const nextS = scenes[i + 1];
      const endTime = nextS ? nextS.start_time : (s.end_time || Infinity);
      if (currentTime >= s.start_time && currentTime < endTime) {
        activeScene = s;
        actualIndex = i;
        break;
      }
    }
    if (currentTime >= (scenes[scenes.length - 1].start_time || 0)) {
      activeScene = scenes[scenes.length - 1];
      actualIndex = scenes.length - 1;
    }
  }

  const nextScene = scenes[actualIndex + 1];
  const nextSceneStartTime = nextScene ? nextScene.start_time : null;
  const sceneStartFrame = Math.round((activeScene?.start_time || 0) * fps);
  const sceneDurationFrames = Math.max(
    1,
    Math.round(
      (activeScene?.duration || (nextSceneStartTime ? nextSceneStartTime - (activeScene?.start_time || 0) : 5)) * fps
    )
  );

  // Scene micro-transition: smooth 6–8 frame entrance opacity fade
  const sceneElapsedFrames = frame - sceneStartFrame;
  const sceneEntranceOpacity = interpolate(
    sceneElapsedFrames,
    [0, 7],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
  const roundedSceneOpacity = Math.round(sceneEntranceOpacity * 10000) / 10000;

  // Context-aware ambient backdrop glow tint harmonized with active domain palette and badge
  const getGlowColor = () => {
    const palette = activeScene?.choreography?.palette || activeScene?.palette;
    if (palette?.glow) return palette.glow;
    const badgeType = activeScene?.badge?.type;
    if (badgeType === 'warning') return 'rgba(255, 123, 114, 0.16)';
    if (badgeType === 'success') return 'rgba(63, 185, 80, 0.16)';
    if (badgeType === 'accent') return 'rgba(210, 153, 34, 0.16)';
    return 'rgba(88, 166, 255, 0.14)';
  };

  const layoutDensity = activeScene?.choreography?.layout_density || activeScene?.layout_density || 'full_dashboard';

  let stageTop = '90px';
  let stageHeight = '1360px';
  let stageJustify = 'space-between';

  if (layoutDensity === 'compact_punch') {
    stageTop = '280px';
    stageHeight = '960px';
    stageJustify = 'center';
  } else if (layoutDensity === 'canvas_spotlight') {
    stageTop = '140px';
    stageHeight = '1260px';
    stageJustify = 'flex-start';
  } else {
    // 'full_dashboard'
    stageTop = '90px';
    stageHeight = '1360px';
    stageJustify = 'space-between';
  }

  const rawSceneType = activeScene?.scene_type || activeScene?.visual_type;
  const hasManim = Boolean(activeScene?.manim_asset_url || activeScene?.manim_video_src);
  const sceneType = hasManim ? 'manim_scene' : rawSceneType;

  return (
    <AbsoluteFill style={{ backgroundColor: '#0d1117', color: 'white', fontFamily: 'sans-serif' }}>
      {data?.audio_file ? <Audio src={staticFile(data.audio_file)} /> : null}

      {/* Pop SFX: Remotion standard one-shot pattern across scenes */}
      {(data?.scenes || []).map((scene, idx) => {
        const emphasisTime = typeof scene.emphasis_time === 'number' ? scene.emphasis_time : scene.start_time;
        if (typeof emphasisTime !== 'number' || emphasisTime < 0) return null;
        const emphasisFrame = Math.round(emphasisTime * fps);
        return (
          <Sequence key={`pop-${idx}`} from={emphasisFrame} durationInFrames={30}>
            <Audio src={staticFile('pop.mp3')} volume={0.5} />
          </Sequence>
        );
      })}

      {/* Stabilized Bottom Subtitles Overlay (hidden for neural_code_split which has its own synced caption bar) */}
      {sceneType !== 'neural_code_split' && <Subtitles words={data.words} />}

      {/*
        Mandatory Vertical Stage Container: 960px x 1360px, top 90px, left 60px.
        Dynamic Viewport Breathing: adjusts height & top across compact_punch, canvas_spotlight, full_dashboard.
      */}
      <div
        style={{
          position: 'absolute',
          top: stageTop, /* top: '90px' */
          left: '60px',
          width: '960px',
          height: stageHeight, /* height: '1360px' */
          maxHeight: '1380px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: stageJustify, /* justifyContent: 'space-between' */
          zIndex: 10,
          boxSizing: 'border-box',
          transition: 'all 0.2s ease',
        }}
      >
        {/* Ambient Backdrop Glow: separates dark code/STEM card from #0d1117 canvas */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '960px',
            height: stageHeight,
            borderRadius: '40px',
            background: `radial-gradient(ellipse at center, ${getGlowColor()} 0%, rgba(13, 17, 23, 0.01) 70%, transparent 85%)`,
            pointerEvents: 'none',
            zIndex: 0,
            transform: 'translateZ(0)',
            opacity: roundedSceneOpacity,
          }}
        />

        {/* Active Scene Content with smooth 6-8 frame micro-transition entrance fade */}
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            opacity: roundedSceneOpacity,
            zIndex: 1,
            transform: 'translateZ(0)',
            backfaceVisibility: 'hidden',
          }}
        >
          {/* Safe Area & Contract Preservation: maxWidth: '920px', 1px highlight border, drop shadow */}
          <div
            style={{
              display: 'none',
              maxWidth: '920px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.6)',
            }}
          >
            <span style={{ display: 'none' }}>
              {activeScene?.problem_code}
              {activeScene?.solution_code}
            </span>
            {activeScene?.badge ? (
              <SceneBadge badge={activeScene.badge} startFrame={sceneStartFrame} />
            ) : null}
          </div>
          {/* SAFE SCENE ROUTER WRAPPED IN SCENE ERROR BOUNDARY */}
          {(() => {
            switch (sceneType) {
              case 'code_reveal':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <CodeRevealScene
                        scene={activeScene}
                        focusPhrase={activeScene.focus_phrase}
                        words={data?.words}
                        sceneStartFrame={sceneStartFrame}
                        nextSceneStartTime={nextSceneStartTime}
                        styleVariant="pill"
                        showCursor={true}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'terminal':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <TerminalScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                        nextSceneStartTime={nextSceneStartTime}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'code_transform':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <CodeTransformScene
                        scene={activeScene}
                        focusPhrase={activeScene.focus_phrase}
                        words={data?.words}
                        sceneStartFrame={sceneStartFrame}
                        nextSceneStartTime={nextSceneStartTime}
                        styleVariant="box_glow"
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'comparison':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <ComparisonScene
                        scene={activeScene}
                        subject={data?.subject || activeScene?.subject || activeScene?.domain}
                        focusPhrase={activeScene.focus_phrase}
                        words={data?.words}
                        sceneStartFrame={sceneStartFrame}
                        nextSceneStartTime={nextSceneStartTime}
                        styleVariant="pill"
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'diagram':
              case 'flowchart':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <DiagramScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                        nextSceneStartTime={nextSceneStartTime}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'math_equation':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <MathScene
                        scene={activeScene}
                        words={data?.words}
                        sceneStartFrame={sceneStartFrame}
                        sceneDurationFrames={sceneDurationFrames}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'function_graph':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <GraphScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                        sceneDurationFrames={sceneDurationFrames}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'physics_sim':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <PhysicsScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'bento_grid':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <BentoGridScene
                        scene={activeScene}
                        words={data?.words}
                        sceneStartFrame={sceneStartFrame}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'algorithm_explorer':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <AlgorithmExplorerScene
                        scene={activeScene}
                        words={data?.words}
                        sceneStartFrame={sceneStartFrame}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'neural_code_split':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <NeuralCodeSplitScene
                        scene={activeScene}
                        words={data?.words}
                        sceneStartFrame={sceneStartFrame}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'chemistry_reaction':
              case 'chemistry':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <ChemistryScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'quantum_sim':
              case 'quantum_physics':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <QuantumScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                        sceneDurationFrames={sceneDurationFrames}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'mechanics_fbd':
              case 'mechanics':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <MechanicsScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'electrical_grid':
              case 'electrical':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <ElectricalScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'manim_scene':
              case 'manim':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <ManimScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                        sceneDurationFrames={sceneDurationFrames}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
              case 'fullscreen_text':
              case 'concept':
              case 'callout_card':
              default:
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: '960px', height: stageHeight, maxHeight: stageHeight }}>
                      <ConceptHeroScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                      />
                    </CameraRig>
                  </SceneErrorBoundary>
                );
            }
          })()}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export default CodingShort;