import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { KineticCallout } from './KineticCallout';
import { CodeIcon, LightningIcon } from './SvgIcons';
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

// Line-level code renderer with progressive spotlight highlighting
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
  isHighlighted = true,
  hasActiveSpotlight = false,
  fontSize = 28,
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

  // Spotlight line styles: keep non-spotlighted lines readable context
  const isLineActive = isHighlighted || !hasActiveSpotlight;
  const lineOpacity = isLineActive ? 1.0 : 0.55;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'baseline',
        lineHeight: '1.45',
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontSize: `${fontSize}px`,
        color: isLineActive ? '#f1f5f9' : '#94a3b8',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        opacity: lineOpacity,
        backgroundColor: (hasActiveSpotlight && isHighlighted) ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
        borderLeft: (hasActiveSpotlight && isHighlighted) ? '4px solid #38bdf8' : '4px solid transparent',
        paddingLeft: (hasActiveSpotlight && isHighlighted) ? '8px' : '0px',
        borderRadius: '4px',
        transition: 'all 0.15s ease',
      }}
    >
      <span
        style={{
          width: '46px',
          flexShrink: 0,
          color: (hasActiveSpotlight && isHighlighted) ? '#38bdf8' : '#475569',
          userSelect: 'none',
          fontSize: `${Math.max(16, fontSize - 4)}px`,
          textAlign: 'right',
          marginRight: '20px',
          fontWeight: (hasActiveSpotlight && isHighlighted) ? 'bold' : 'normal',
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
 * CodeRevealScene (Phase A DevTool Primitive)
 * Progressive Line Spotlight Code Inspector:
 *   - Supports code, language, filename (e.g. agent.ts), highlight_lines: number[]
 *   - Dims non-active lines (opacity: 0.38) while spotlighting active lines with cyan accent bar
 *   - Auto-scales font size (19px-28px) to prevent horizontal card overflow
 *   - Context-aware execution console
 */
export const CodeRevealScene = ({
  scene,
  words = [],
  sceneStartFrame = 0,
  nextSceneStartTime = null,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const code = scene?.code || scene?.code_snippet || '';
  const lines = code ? code.split('\n') : [''];
  const filename = scene?.filename || 'solution.py';
  const language = (scene?.language || (filename.endsWith('.ts') ? 'typescript' : (filename.endsWith('.py') ? 'python' : 'code'))).toLowerCase();

  // Highlight lines (1-indexed)
  const rawHighlights = scene?.highlight_lines || [];
  const highlightSet = new Set(Array.isArray(rawHighlights) ? rawHighlights : []);
  const hasActiveSpotlight = highlightSet.size > 0;

  // Font auto-scaling based on max line length and line count
  const maxLineLen = Math.max(...lines.map((l) => l.length), 0);
  const lineCount = lines.length;

  let fontSize = 28;
  if (maxLineLen > 52 || lineCount > 13) {
    fontSize = 19;
  } else if (maxLineLen > 44 || lineCount > 10) {
    fontSize = 22;
  } else if (maxLineLen > 36 || lineCount > 8) {
    fontSize = 25;
  }

  // Stagger each line entrance by 4 frames
  const staggerFrames = 4;
  const revealDuration = 6;

  let latestRevealedIdx = 0;
  lines.forEach((_, idx) => {
    const lineStart = sceneStartFrame + idx * staggerFrames;
    if (frame >= lineStart) {
      latestRevealedIdx = idx;
    }
  });

  // Dynamic console labels based on language
  const isTypeScript = language === 'typescript' || language === 'ts' || filename.endsWith('.ts');
  const consoleCommand = isTypeScript
    ? `$ npx tsx ${filename}`
    : `$ python3 -m pytest ${filename} -v`;
  const consoleStatus = isTypeScript
    ? 'STREAM ACTIVE • 200 OK'
    : 'PASSED 42/42 tests in 0.038s';
  const consoleBadge = isTypeScript ? 'TS 5.4 • ESM' : 'EXIT CODE: 0';

  return (
    <div
      style={{
        backgroundColor: '#161b22',
        borderRadius: '28px',
        border: '1.5px solid rgba(255, 255, 255, 0.12)',
        boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 0 1px rgba(255, 255, 255, 0.06)',
        width: '960px',
        height: 'fit-content',
        maxHeight: '1240px',
        overflow: 'hidden',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        position: 'relative',
        padding: '26px 28px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        margin: 'auto 0',
      }}
    >
      {/* 1. TOP TERMINAL HEADER BAR (110px) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '90px',
          paddingBottom: '16px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#ff5f56', display: 'inline-block', boxShadow: '0 0 8px rgba(255,95,86,0.5)' }} />
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#ffbd2e', display: 'inline-block', boxShadow: '0 0 8px rgba(255,189,46,0.5)' }} />
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#27c93f', display: 'inline-block', boxShadow: '0 0 8px rgba(39,201,63,0.5)' }} />
          <div
            style={{
              marginLeft: '14px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '6px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <LightningIcon size={18} color="#58a6ff" />
            <span
              style={{
                fontSize: '20px',
                color: '#e6edf3',
                fontFamily: 'monospace',
                fontWeight: 'bold',
                letterSpacing: '0.5px',
              }}
            >
              {filename}
            </span>
          </div>

          {/* Language Badge */}
          <span
            style={{
              backgroundColor: isTypeScript ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 214, 51, 0.15)',
              border: `1px solid ${isTypeScript ? '#38bdf8' : '#ffd633'}`,
              color: isTypeScript ? '#38bdf8' : '#ffd633',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '14px',
              fontFamily: 'monospace',
              fontWeight: 800,
            }}
          >
            {isTypeScript ? 'TS' : 'PYTHON'}
          </span>
        </div>

        {/* Scene Badge */}
        {scene?.badge ? (
          <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} />
        ) : null}
      </div>

      {/* 2. CODE AREA (IDE BUFFER) */}
      <div
        style={{
          flex: 1,
          margin: '14px 0',
          padding: '20px 20px',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
          gap: '6px',
          backgroundColor: '#0d1117',
          borderRadius: '18px',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          overflow: 'hidden',
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

          const isHighlighted = highlightSet.has(idx + 1);

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
                isHighlighted={isHighlighted}
                hasActiveSpotlight={hasActiveSpotlight}
                fontSize={fontSize}
              />
            </div>
          );
        })}
      </div>

      {/* 3. BOTTOM TERMINAL EXECUTION CONSOLE */}
      <div
        style={{
          height: '92px',
          backgroundColor: '#090d13',
          borderRadius: '16px',
          border: '1.5px solid rgba(88, 166, 255, 0.3)',
          boxShadow: '0 16px 32px rgba(0, 0, 0, 0.6)',
          padding: '16px 22px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          fontFamily: 'monospace',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <CodeIcon size={20} color="#58a6ff" />
            <span style={{ fontSize: '18px', color: '#58a6ff', fontWeight: 900, letterSpacing: '1px' }}>
              STDOUT • EXECUTION ENVIRONMENT
            </span>
          </div>
          <span style={{ fontSize: '15px', color: '#56d364', fontWeight: 'bold' }}>
            {consoleBadge}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '16px' }}>
          <div style={{ color: '#8b949e' }}>
            {consoleCommand}
          </div>
          <div style={{ color: '#56d364', fontWeight: 'bold' }}>
            {consoleStatus}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodeRevealScene;
