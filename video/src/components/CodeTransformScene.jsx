import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { KineticCallout } from './KineticCallout';
import { LightningIcon, WarningIcon, SparklesIcon } from './SvgIcons';
import { splitCodeByToken, resolveCalloutTiming } from '../calloutUtils';
import { SPRING_CALLOUT_CONFIG } from '../calloutUtils';

// Helper to render diff line with '-' or '+' diff badge
const DiffLine = ({ text, type = 'normal', fontSize = 24 }) => {
  const isRemoved = type === 'removed';
  const isAdded = type === 'added';

  const badgeColor = isRemoved ? '#ff7b72' : (isAdded ? '#3fb950' : '#8b949e');
  const badgeSymbol = isRemoved ? '−' : (isAdded ? '+' : ' ');
  const textColor = isRemoved ? '#ffa198' : (isAdded ? '#7ee787' : '#e6edf3');

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'baseline',
        lineHeight: 1.5,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontSize: `${fontSize}px`,
        color: textColor,
        backgroundColor: isRemoved ? 'rgba(255, 123, 114, 0.08)' : (isAdded ? 'rgba(63, 185, 80, 0.08)' : 'transparent'),
        padding: '2px 8px',
        borderRadius: '4px',
        boxSizing: 'border-box',
      }}
    >
      <span
        style={{
          width: '24px',
          flexShrink: 0,
          color: badgeColor,
          fontWeight: 900,
          userSelect: 'none',
        }}
      >
        {badgeSymbol}
      </span>
      <span style={{ flex: 1, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
        {text}
      </span>
    </div>
  );
};

/**
 * CodeTransformScene (Phase A DevTool Primitive)
 * Before -> After Code Diff / Migration:
 *   - Supports before_code, after_code, before_label, and after_label
 *   - Stacks red-tinted removed lines (-) and emerald-tinted added lines (+)
 *   - Dynamic font auto-scaling and safe layout
 */
export const CodeTransformScene = ({
  scene,
  words = [],
  sceneStartFrame = 0,
  nextSceneStartTime = null,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const beforeCode = scene?.before_code || scene?.problem_code || scene?.code_snippet || '';
  const afterCode = scene?.after_code || scene?.solution_code || scene?.code_snippet || '';

  // ⚠️ Before and ✨ After header badges
  const beforeLabel = scene?.before_label || 'Legacy v1 (28 lines)';
  const afterLabel = scene?.after_label || 'New v2 SDK (4 lines)';
  const filename = scene?.filename || 'migration.ts';

  const beforeLines = beforeCode ? beforeCode.split('\n') : [''];
  const afterLines = afterCode ? afterCode.split('\n') : [''];

  // Font auto-scaling based on max line length
  const allLines = [...beforeLines, ...afterLines];
  const maxLineLen = Math.max(...allLines.map((l) => l.length), 0);
  const maxCardLines = Math.max(beforeLines.length, afterLines.length);

  let fontSize = 24;
  if (maxLineLen > 52 || maxCardLines > 8) {
    fontSize = 19;
  } else if (maxLineLen > 44 || maxCardLines > 6) {
    fontSize = 21;
  }

  const emphasisTime = typeof scene?.emphasis_time === 'number'
    ? scene.emphasis_time
    : (scene?.start_time || 0) + 1.0;
  const emphasisFrame = Math.round(emphasisTime * fps);

  // Transition spring progress (0 -> 1)
  const isPostEmphasis = frame >= emphasisFrame;
  let transformProgress = 0;
  if (isPostEmphasis) {
    const rawSpring = spring({
      frame: frame - emphasisFrame,
      fps,
      config: SPRING_CALLOUT_CONFIG,
    });
    transformProgress = Math.max(0, Math.min(rawSpring, 1.0));
  }

  const dividerGlow = isPostEmphasis
    ? Math.round(interpolate(transformProgress, [0, 1], [0, 24]))
    : 0;

  return (
    <div
      style={{
        backgroundColor: '#161b22',
        borderRadius: '28px',
        border: '1.5px solid rgba(255, 255, 255, 0.12)',
        boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95)',
        width: '960px',
        height: '1540px',
        overflow: 'hidden',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        position: 'relative',
        padding: '30px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      {/* 1. TOP TERMINAL HEADER BAR (100px) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '80px',
          paddingBottom: '14px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#ff5f56', display: 'inline-block' }} />
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#ffbd2e', display: 'inline-block' }} />
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#27c93f', display: 'inline-block' }} />
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

          <span
            style={{
              backgroundColor: 'rgba(168, 85, 247, 0.15)',
              border: '1px solid #a855f7',
              color: '#d8b4fe',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '14px',
              fontFamily: 'monospace',
              fontWeight: 800,
            }}
          >
            DIFF / MIGRATION
          </span>
        </div>

        {scene?.badge ? (
          <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} />
        ) : null}
      </div>

      {/* 2. BEFORE CODE BLOCK (540px) */}
      <div
        style={{
          height: '520px',
          backgroundColor: isPostEmphasis ? '#150f12' : '#220b12',
          borderRadius: '20px',
          border: isPostEmphasis
            ? '1.5px solid rgba(255, 123, 114, 0.35)'
            : '2px solid rgba(255, 123, 114, 0.85)',
          padding: '20px 24px',
          opacity: isPostEmphasis ? 0.65 : 1.0,
          transition: 'all 0.15s ease',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'rgba(255, 123, 114, 0.15)',
            border: '1px solid rgba(255, 123, 114, 0.35)',
            color: '#ff7b72',
            borderRadius: '8px',
            padding: '4px 14px',
            fontSize: '17px',
            fontWeight: 'bold',
            alignSelf: 'flex-start',
          }}
        >
          <WarningIcon size={18} color="#ff7b72" />
          <span>{beforeLabel}</span>
        </div>

        <div style={{ flex: 1, margin: '14px 0', overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '4px' }}>
          {beforeLines.map((line, idx) => (
            <DiffLine key={idx} text={line} type="removed" fontSize={fontSize} />
          ))}
        </div>
      </div>

      {/* 3. ANIMATED TRANSITION DIVIDER (60px) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '18px',
          height: '60px',
          boxSizing: 'border-box',
        }}
      >
        <div
          style={{
            flex: 1,
            height: '2px',
            backgroundColor: isPostEmphasis ? '#3fb950' : 'rgba(255, 255, 255, 0.15)',
            transition: 'background-color 0.15s ease',
          }}
        />
        <div
          style={{
            backgroundColor: isPostEmphasis ? '#0f2d19' : '#161b22',
            border: isPostEmphasis
              ? '1.5px solid #3fb950'
              : '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '24px',
            padding: '6px 20px',
            fontSize: '16px',
            fontWeight: 800,
            color: isPostEmphasis ? '#3fb950' : '#8b949e',
            boxShadow: isPostEmphasis ? `0 0 ${dividerGlow}px rgba(63, 185, 80, 0.7)` : 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            letterSpacing: '1px',
            textTransform: 'uppercase',
          }}
        >
          {isPostEmphasis ? (
            <>
              <SparklesIcon size={16} color="#3fb950" />
              <span>Transformed</span>
            </>
          ) : (
            <span>Optimizing Code...</span>
          )}
        </div>
        <div
          style={{
            flex: 1,
            height: '2px',
            backgroundColor: isPostEmphasis ? '#3fb950' : 'rgba(255, 255, 255, 0.15)',
            transition: 'background-color 0.15s ease',
          }}
        />
      </div>

      {/* 4. AFTER CODE BLOCK (540px) */}
      <div
        style={{
          height: '520px',
          backgroundColor: isPostEmphasis ? '#0a2213' : '#101b13',
          borderRadius: '20px',
          border: isPostEmphasis
            ? '2px solid rgba(63, 185, 80, 0.9)'
            : '1.5px dashed rgba(63, 185, 80, 0.35)',
          boxShadow: isPostEmphasis
            ? `0 0 ${Math.round(transformProgress * 28)}px rgba(63, 185, 80, 0.4)`
            : 'none',
          padding: '20px 24px',
          opacity: isPostEmphasis ? 1.0 : 0.5,
          transition: 'all 0.15s ease',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'rgba(63, 185, 80, 0.15)',
            border: '1px solid rgba(63, 185, 80, 0.35)',
            color: '#3fb950',
            borderRadius: '8px',
            padding: '4px 14px',
            fontSize: '17px',
            fontWeight: 'bold',
            alignSelf: 'flex-start',
          }}
        >
          <SparklesIcon size={18} color="#3fb950" />
          <span>{afterLabel}</span>
        </div>

        <div style={{ flex: 1, margin: '14px 0', overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '4px' }}>
          {afterLines.map((line, idx) => (
            <DiffLine key={idx} text={line} type="added" fontSize={fontSize} />
          ))}
        </div>
      </div>

      {/* 5. BOTTOM TECHNICAL STATUS BAR */}
      <div
        style={{
          height: '60px',
          backgroundColor: '#090d13',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '0 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#3fb950', display: 'inline-block', boxShadow: '0 0 8px rgba(63, 185, 80, 0.7)' }} />
          <span style={{ fontSize: '16px', color: '#3fb950', fontWeight: 'bold', fontFamily: 'monospace' }}>
            DIFF: -24 LINES • TYPESAFE ASYNC PROMISES
          </span>
        </div>
        <span
          style={{
            backgroundColor: 'rgba(63, 185, 80, 0.15)',
            border: '1px solid #3fb950',
            color: '#3fb950',
            borderRadius: '6px',
            padding: '3px 10px',
            fontSize: '14px',
            fontFamily: 'monospace',
            fontWeight: 'bold',
          }}
        >
          VERIFIED
        </span>
      </div>
    </div>
  );
};

export default CodeTransformScene;
