import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { KineticCallout } from './KineticCallout';
import { CodeIcon, LightningIcon, SparklesIcon } from './SvgIcons';
import { splitCodeByToken, resolveCalloutTiming } from '../calloutUtils';

// Blinking terminal cursor at ~2Hz (every 15 frames at 30fps)
export const TerminalCursor = () => {
  const frame = useCurrentFrame();
  const isVisible = Math.floor(frame / 15) % 2 === 0;

  return (
    <span
      style={{
        display: 'inline-block',
        width: '12px',
        height: '1.1em',
        backgroundColor: '#58a6ff',
        marginLeft: '6px',
        verticalAlign: 'text-bottom',
        borderRadius: '2px',
        opacity: isVisible ? 0.9 : 0.05,
        boxShadow: isVisible ? '0 0 10px rgba(88, 166, 255, 0.7)' : 'none',
        transform: 'none',
        backfaceVisibility: 'hidden',
        pointerEvents: 'none',
      }}
    />
  );
};

// Line-level code renderer with kinetic token callout support
const CodeLine = ({
  lineText,
  lineIdx,
  focusPhrase,
  scene,
  words,
  fps,
  nextSceneStartTime,
  isLatestRevealed,
  showCursor,
}) => {
  const target = focusPhrase || scene?.focus_phrase || scene?.emphasis_word;
  const tokenData = lineText ? splitCodeByToken(lineText, target) : null;

  let content = lineText;
  if (tokenData && tokenData.match) {
    const { before, match, after } = tokenData;
    const { startFrame, endFrame } = resolveCalloutTiming({
      scene,
      words,
      fps,
      nextSceneStartTime,
    });

    content = (
      <>
        {before}
        <KineticCallout
          startFrame={startFrame}
          endFrame={endFrame}
          styleVariant={scene?.scene_type === 'code_transform' ? 'box_glow' : 'pill'}
        >
          {match}
        </KineticCallout>
        {after}
      </>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'baseline',
        lineHeight: '1.5',
        fontFamily: 'monospace',
        fontSize: '28px',
        color: '#c9d1d9',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
      }}
    >
      <span
        style={{
          width: '50px',
          flexShrink: 0,
          color: '#484f58',
          userSelect: 'none',
          fontSize: '24px',
          textAlign: 'right',
          marginRight: '24px',
          transform: 'none',
        }}
      >
        {String(lineIdx + 1).padStart(2, '0')}
      </span>
      <span
        style={{
          flex: 1,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          transform: 'none',
        }}
      >
        {content}
        {isLatestRevealed && showCursor && <TerminalCursor />}
      </span>
    </div>
  );
};

/**
 * CodeRevealScene (Phase 5 - 1540px Vertical Stage Layout)
 * Full-height 1540px layout filling 85% of the 1080x1920 canvas:
 *   - Top Editorial Header (140px): CodeIcon, filename, macOS controls, SceneBadge.
 *   - Center Code Editor (980px): Line-by-line typewriter code reveal with 28px font and blinking cursor.
 *   - Bottom Execution Console (380px): Simulated terminal runner ($ python3 solution.py) with test results.
 */
export const CodeRevealScene = ({
  scene,
  words = [],
  sceneStartFrame = 0,
  nextSceneStartTime = null,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const code = scene?.code_snippet || '';
  const lines = code ? code.split('\n') : [''];
  const filename = scene?.filename || 'solution.py';

  // Stagger each line entrance by 4 frames
  const staggerFrames = 4;
  const revealDuration = 6;

  // Find the index of the latest revealed line
  let latestRevealedIdx = 0;
  lines.forEach((_, idx) => {
    const lineStart = sceneStartFrame + idx * staggerFrames;
    if (frame >= lineStart) {
      latestRevealedIdx = idx;
    }
  });

  return (
    <div
      style={{
        backgroundColor: '#161b22',
        borderRadius: '28px',
        border: '1.5px solid rgba(255, 255, 255, 0.12)',
        boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 0 1px rgba(255, 255, 255, 0.06)',
        width: '960px',
        height: '1540px',
        overflow: 'hidden',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        position: 'relative',
        padding: '32px 32px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      {/* 1. TOP TERMINAL HEADER BAR (140px) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '110px',
          paddingBottom: '16px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
        }}
      >
        {/* macOS Window Controls + Filename */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#ff5f56', display: 'inline-block', boxShadow: '0 0 8px rgba(255,95,86,0.5)' }} />
          <span style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#ffbd2e', display: 'inline-block', boxShadow: '0 0 8px rgba(255,189,46,0.5)' }} />
          <span style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#27c93f', display: 'inline-block', boxShadow: '0 0 8px rgba(39,201,63,0.5)' }} />
          <div
            style={{
              marginLeft: '16px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '6px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <LightningIcon size={20} color="#58a6ff" />
            <span
              style={{
                fontSize: '22px',
                color: '#e6edf3',
                fontFamily: 'monospace',
                fontWeight: 'bold',
                letterSpacing: '0.5px',
              }}
            >
              {filename}
            </span>
          </div>
        </div>

        {/* Scene Badge */}
        {scene?.badge ? (
          <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} />
        ) : null}
      </div>

      {/* 2. CODE AREA (980px) */}
      <div
        style={{
          height: '980px',
          padding: '28px 24px',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-around',
          backgroundColor: '#0d1117',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        {lines.map((line, idx) => {
          const lineStart = sceneStartFrame + idx * staggerFrames;
          const isStarted = frame >= lineStart;

          let lineOpacity = 0;
          if (isStarted) {
            const elapsed = frame - lineStart;
            lineOpacity = elapsed < revealDuration ? Math.round((elapsed / revealDuration) * 100) / 100 : 1;
          }

          return (
            <div
              key={idx}
              style={{
                opacity: lineOpacity,
                visibility: isStarted ? 'visible' : 'hidden',
                boxSizing: 'border-box',
              }}
            >
              <CodeLine
                lineText={line}
                lineIdx={idx}
                focusPhrase={scene.focus_phrase}
                scene={scene}
                words={words}
                fps={fps}
                nextSceneStartTime={nextSceneStartTime}
                isLatestRevealed={idx === latestRevealedIdx}
                showCursor={true}
              />
            </div>
          );
        })}
      </div>

      {/* 3. BOTTOM TERMINAL EXECUTION CONSOLE (380px) */}
      <div
        style={{
          height: '380px',
          backgroundColor: '#090d13',
          borderRadius: '22px',
          border: '1.5px solid rgba(88, 166, 255, 0.3)',
          boxShadow: '0 16px 32px rgba(0, 0, 0, 0.6)',
          padding: '24px 28px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          fontFamily: 'monospace',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <CodeIcon size={24} color="#58a6ff" />
            <span style={{ fontSize: '22px', color: '#58a6ff', fontWeight: 900, letterSpacing: '1px' }}>
              STDOUT • EXECUTION ENVIRONMENT
            </span>
          </div>
          <span style={{ fontSize: '18px', color: '#56d364', fontWeight: 'bold' }}>
            EXIT CODE: 0
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '22px' }}>
          <div style={{ color: '#8b949e' }}>
            $ python3 -m pytest {filename} -v
          </div>
          <div style={{ color: '#56d364', fontWeight: 'bold' }}>
            PASSED 42/42 tests in 0.038s
          </div>
          <div style={{ color: '#79c0ff' }}>
            Peak Memory: 12.8 MB • Aux Space: O(1)
          </div>
        </div>

        <div
          style={{
            padding: '12px 18px',
            backgroundColor: 'rgba(88, 166, 255, 0.1)',
            borderRadius: '10px',
            border: '1px solid rgba(88, 166, 255, 0.25)',
            fontSize: '20px',
            color: '#c9d1d9',
          }}
        >
          {scene?.spoken_text || 'Execution finishes in optimal asymptotic bounds.'}
        </div>
      </div>
    </div>
  );
};

export default CodeRevealScene;
