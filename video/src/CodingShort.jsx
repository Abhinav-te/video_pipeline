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
import { TerminalScene } from './components/TerminalScene';
import { WorkflowStateTransition } from './components/WorkflowStateTransition';
import { HookScene } from './components/HookScene';
import { CodeSpotlightScene } from './components/CodeSpotlightScene';
import { EvidenceBentoScene } from './components/EvidenceBentoScene';
import { TakeawayCTAScene } from './components/TakeawayCTAScene';
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
  WorkflowStateTransition,
  HookScene,
  CodeSpotlightScene,
  EvidenceBentoScene,
  TakeawayCTAScene,
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

// Functional stopwords to suppress from high-contrast neon flashes
const FUNCTIONAL_WORDS = new Set([
  'THE', 'A', 'AN', 'IN', 'ON', 'FOR', 'OF', 'TO', 'AND', 'OR', 'IS', 'ARE', 'WAS', 'BE', 'BEEN',
  'BY', 'FROM', 'THIS', 'THAT', 'INTO', 'YOUR', 'YOU', 'WE', 'IT', 'ITS', 'WITH', 'AT', 'SLASH',
  'AS', 'OUR', 'SO', 'BUT', 'IF', 'THEN', 'UP', 'OUT', 'ALL', 'ANY', 'CAN', 'WILL', 'JUST'
]);

// Meaningful technical keywords that receive prominent emphasis
const TECHNICAL_KEYWORDS = new Set([
  'STREAMING', 'NPM', 'INSTALL', 'ASYNC', 'GENERATOR', 'EDGE', 'GATEWAY', 'CACHE', 'LATENCY',
  'SDK', 'API', 'BOILERPLATE', 'MIGRATION', 'CLUSTER', 'CLIENT', 'PROMISES', 'TYPESCRIPT', 'KEYS',
  'HIT', 'RATE', 'REDUCTION', 'OPTIMIZATION', 'IMPORT', 'EXPORT', 'FAST', 'CONTAINER', 'RUNTIME',
  'EXECUTION', 'DIFF', 'ZERO', 'DEPLOY', 'PACKAGES', 'VERIFIED', 'JSON', 'BENCHMARK', 'TRANSFORM'
]);

// Subtitle component rendering strictly from pre-chunked caption_chunks with zero cross-sentence bleeding
export const Subtitles = ({ words: rawWords, captionChunks: preChunked, isWidescreen = false }) => {
  const words = React.useMemo(() => mergeHyphenatedTokens(rawWords), [rawWords]);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  // Derive or use pre-chunked caption_chunks
  const chunks = React.useMemo(() => {
    if (preChunked && preChunked.length > 0) return preChunked;
    if (!words || words.length === 0) return [];

    // Fallback: chunk strictly by sentence punctuation (. ! ? ; :) and length <= 28 chars
    const generated = [];
    let currentWords = [];
    let currentText = '';

    words.forEach((w) => {
      const wordStr = (w.word || '').trim();
      currentWords.push(w);
      currentText += (currentText ? ' ' : '') + wordStr;

      const endsWithSentencePunct = /[.!?]$/.test(wordStr);
      const endsWithClausePunct = /[,;:]$/.test(wordStr);
      const isTooLong = currentWords.length >= 5 || currentText.length >= 28;

      if (endsWithSentencePunct || (currentWords.length >= 3 && endsWithClausePunct) || isTooLong) {
        generated.push({
          start: currentWords[0].start,
          end: currentWords[currentWords.length - 1].end,
          text: currentText,
          words: [...currentWords],
        });
        currentWords = [];
        currentText = '';
      }
    });

    if (currentWords.length > 0) {
      generated.push({
        start: currentWords[0].start,
        end: currentWords[currentWords.length - 1].end,
        text: currentText,
        words: [...currentWords],
      });
    }

    return generated;
  }, [preChunked, words]);

  if (!chunks || chunks.length === 0) return null;

  // Find active chunk
  let activeChunk = chunks.find((c) => currentTime >= c.start && currentTime <= c.end);
  let opacity = 1;

  if (!activeChunk) {
    // Check if in brief pause (<= 0.5s) after preceding chunk
    let lastChunk = null;
    for (let i = chunks.length - 1; i >= 0; i--) {
      if (chunks[i].start <= currentTime) {
        lastChunk = chunks[i];
        break;
      }
    }
    if (lastChunk) {
      const gap = currentTime - lastChunk.end;
      if (gap <= 0.5) {
        activeChunk = lastChunk;
        opacity = Math.max(0, 1 - gap / 0.5);
      }
    }
  }

  if (!activeChunk || opacity <= 0.05) {
    return null;
  }

  const chunkWords = activeChunk.words || [];

  return (
    <div
      style={{
        position: 'absolute',
        bottom: isWidescreen ? '40px' : '120px',
        width: '100%',
        textAlign: 'center',
        padding: isWidescreen ? '0 100px' : '0 40px',
        boxSizing: 'border-box',
        height: isWidescreen ? '60px' : '100px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 50,
        pointerEvents: 'none',
        opacity,
        transition: 'opacity 0.1s ease',
      }}
    >
      <div
        style={{
          fontSize: isWidescreen ? '42px' : '48px',
          fontWeight: 900,
          textTransform: 'uppercase',
          lineHeight: isWidescreen ? '52px' : '60px',
          height: isWidescreen ? '52px' : '60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: isWidescreen ? '10px' : '14px',
        }}
      >
        {chunkWords.map((w, i) => {
          const isActive = currentTime >= w.start && currentTime <= w.end;
          const cleanWord = (w.word || '').replace(/[^a-zA-Z0-9_-]/g, '').toUpperCase();
          const isFunctional = FUNCTIONAL_WORDS.has(cleanWord);
          const isTechnical = TECHNICAL_KEYWORDS.has(cleanWord) || (!isFunctional && cleanWord.length >= 6);

          let wordColor = '#ffffff';
          let bgColor = 'transparent';
          let borderStyle = '1px solid transparent';
          let textShadow = '0 4px 12px rgba(0,0,0,0.9)';

          if (isActive) {
            if (isFunctional) {
              wordColor = '#e2e8f0';
              bgColor = 'rgba(255, 255, 255, 0.08)';
              borderStyle = '1px solid rgba(255, 255, 255, 0.15)';
              textShadow = '0 2px 8px rgba(0,0,0,0.8)';
            } else if (isTechnical) {
              wordColor = '#ffd633';
              bgColor = 'rgba(255, 214, 51, 0.22)';
              borderStyle = '1.5px solid rgba(255, 214, 51, 0.6)';
              textShadow = '0 0 28px rgba(255, 214, 51, 0.85)';
            } else {
              wordColor = '#f8fafc';
              bgColor = 'rgba(255, 255, 255, 0.14)';
              borderStyle = '1px solid rgba(255, 255, 255, 0.25)';
              textShadow = '0 0 16px rgba(255, 255, 255, 0.5)';
            }
          }

          return (
            <span
              key={`${w.word}-${w.start}-${i}`}
              style={{
                color: wordColor,
                backgroundColor: bgColor,
                borderRadius: '8px',
                padding: '2px 14px',
                height: '56px',
                lineHeight: '56px',
                display: 'inline-flex',
                alignItems: 'center',
                transform: 'none',
                textShadow,
                border: borderStyle,
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
  const { width, height, fps } = useVideoConfig();
  const isWidescreen = width > height;
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

  const rawSceneType = activeScene?.scene_type || activeScene?.visual_type;
  const hasManim = Boolean(activeScene?.manim_asset_url || activeScene?.manim_video_src);
  const sceneType = hasManim ? 'manim_scene' : rawSceneType;

  let stageTop = isWidescreen ? '40px' : '90px';
  let stageLeft = isWidescreen ? '180px' : '60px';
  let stageWidth = isWidescreen ? '1560px' : '960px';
  let stageHeight = isWidescreen ? '840px' : '1360px';
  let stageJustify = 'center';

  if (!isWidescreen) {
    if (sceneType === 'terminal') {
      stageTop = '160px';
      stageHeight = '1200px';
      stageJustify = 'center';
    } else if (sceneType === 'code_reveal') {
      stageTop = '140px';
      stageHeight = '1240px';
      stageJustify = 'center';
    } else if (layoutDensity === 'compact_punch') {
      stageTop = '280px';
      stageHeight = '960px';
      stageJustify = 'center';
    } else if (layoutDensity === 'canvas_spotlight') {
      stageTop = '140px';
      stageHeight = '1260px';
      stageJustify = 'flex-start';
    } else {
      stageTop = '90px';
      stageHeight = '1360px';
      stageJustify = 'space-between';
    }
  }

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

      {/* Stabilized Bottom Subtitles Overlay */}
      <Subtitles words={data.words} captionChunks={data.caption_chunks} isWidescreen={isWidescreen} />

      {/*
        Responsive Stage Container:
        Widescreen (16:9): 1680px x 860px, top 50px, left 120px.
        Vertical (9:16): 960px x 1360px, top 90px, left 60px.
      */}
      <div
        style={{
          position: 'absolute',
          top: stageTop,
          left: stageLeft,
          width: stageWidth,
          height: stageHeight,
          maxHeight: isWidescreen ? '920px' : '1380px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: stageJustify,
          zIndex: 10,
          boxSizing: 'border-box',
          transition: 'all 0.2s ease',
        }}
      >
        {/* Ambient Backdrop Glow */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: stageWidth,
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
              case 'takeaway_cta':
              case 'brand_outro':
                return (
                  <SceneErrorBoundary>
                    <TakeawayCTAScene
                      scene={activeScene}
                      sceneStartFrame={sceneStartFrame}
                      isWidescreen={isWidescreen}
                    />
                  </SceneErrorBoundary>
                );
              case 'hook_scene':
              case 'problem_scene':
                return (
                  <SceneErrorBoundary>
                    <HookScene
                      scene={activeScene}
                      sceneStartFrame={sceneStartFrame}
                      isWidescreen={isWidescreen}
                    />
                  </SceneErrorBoundary>
                );
              case 'workflow_state_transition':
              case 'workflow_transition':
                return (
                  <SceneErrorBoundary>
                    <WorkflowStateTransition
                      scene={activeScene}
                      sceneStartFrame={sceneStartFrame}
                      isWidescreen={isWidescreen}
                    />
                  </SceneErrorBoundary>
                );
              case 'show_code':
              case 'highlight_code':
              case 'code_reveal':
                return (
                  <SceneErrorBoundary>
                    <CodeSpotlightScene
                      scene={activeScene}
                      sceneStartFrame={sceneStartFrame}
                      isWidescreen={isWidescreen}
                    />
                  </SceneErrorBoundary>
                );
              case 'show_metric':
              case 'bento_grid':
                return (
                  <SceneErrorBoundary>
                    <EvidenceBentoScene
                      scene={activeScene}
                      sceneStartFrame={sceneStartFrame}
                      isWidescreen={isWidescreen}
                    />
                  </SceneErrorBoundary>
                );
              case 'show_terminal':
              case 'terminal':
                return (
                  <SceneErrorBoundary>
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: stageWidth, height: stageHeight, maxHeight: stageHeight }}>
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
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: stageWidth, height: stageHeight, maxHeight: stageHeight }}>
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
                    <CameraRig scene={activeScene} focusScale={1.04} style={{ width: stageWidth, height: stageHeight, maxHeight: stageHeight }}>
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
              case 'show_request_response':
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
              case 'fullscreen_text':
              case 'concept':
              case 'callout_card':
              default:
                if (actualIndex === scenes.length - 1 || activeScene?.scene_type === 'takeaway_cta') {
                  return (
                    <SceneErrorBoundary>
                      <TakeawayCTAScene
                        scene={activeScene}
                        sceneStartFrame={sceneStartFrame}
                        isWidescreen={isWidescreen}
                      />
                    </SceneErrorBoundary>
                  );
                }
                return (
                  <SceneErrorBoundary>
                    <HookScene
                      scene={activeScene}
                      sceneStartFrame={sceneStartFrame}
                      isWidescreen={isWidescreen}
                    />
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