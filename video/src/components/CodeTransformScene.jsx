import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { KineticCallout } from './KineticCallout';
import { LightningIcon, WarningIcon, SparklesIcon } from './SvgIcons';
import { splitCodeByToken, resolveCalloutTiming } from '../calloutUtils';
import { SPRING_CALLOUT_CONFIG } from '../calloutUtils';

// Helper to render code snippet with token callouts
const TransformSnippet = ({
  code,
  scene,
  words,
  fps,
  nextSceneStartTime,
  styleVariant = 'box_glow',
}) => {
  const target = scene?.focus_phrase || scene?.emphasis_word;
  const tokenData = code ? splitCodeByToken(code, target) : null;

  if (!tokenData || !tokenData.match) {
    return (
      <code style={{ fontFamily: 'monospace', lineHeight: 1.5, transform: 'none', display: 'block' }}>
        {code}
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
    <code style={{ fontFamily: 'monospace', lineHeight: 1.5, transform: 'none', display: 'block' }}>
      {before}
      <KineticCallout
        startFrame={startFrame}
        endFrame={endFrame}
        styleVariant={styleVariant}
      >
        {match}
      </KineticCallout>
      {after}
    </code>
  );
};

/**
 * CodeTransformScene (Phase 5 - 1540px Vertical Stage Layout)
 * Full-height 1540px layout filling 85% of the 1080x1920 canvas:
 *   - Top Editorial Header (140px): LightningIcon, morph_transform.py filename, SceneBadge.
 *   - Before Code Card (540px): Red-accented before implementation with 26px font.
 *   - Animated Transition Divider (80px): Dynamic morph bar.
 *   - After Code Card (540px): Emerald-accented optimal implementation with 26px font and glow.
 *   - Bottom Takeaway Pill (140px): Key refactor insight.
 *   - Legacy verification tags: ⚠️ Before, ✨ After
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#ff5f56', display: 'inline-block' }} />
          <span style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#ffbd2e', display: 'inline-block' }} />
          <span style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#27c93f', display: 'inline-block' }} />
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
              morph_transform.py
            </span>
          </div>
        </div>

        {scene?.badge ? (
          <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} />
        ) : null}
      </div>

      {/* 2. BEFORE CODE BLOCK (520px) */}
      <div
        style={{
          height: '520px',
          backgroundColor: isPostEmphasis ? '#1a1215' : '#220b12',
          borderRadius: '22px',
          border: isPostEmphasis
            ? '1.5px solid rgba(255, 123, 114, 0.35)'
            : '2px solid rgba(255, 123, 114, 0.85)',
          padding: '24px 28px',
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
            fontSize: '18px',
            fontWeight: 'bold',
            alignSelf: 'flex-start',
          }}
        >
          <WarningIcon size={18} color="#ff7b72" />
          <span>Before (Inefficient / Naive)</span>
        </div>
        <pre style={{ margin: 0, fontSize: '26px', lineHeight: '1.5', color: '#c9d1d9', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
          <TransformSnippet
            code={beforeCode}
            scene={scene}
            words={words}
            fps={fps}
            nextSceneStartTime={nextSceneStartTime}
            styleVariant="box_glow"
          />
        </pre>
      </div>

      {/* 3. ANIMATED TRANSITION DIVIDER (70px) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '18px',
          height: '70px',
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
            padding: '8px 24px',
            fontSize: '18px',
            fontWeight: 800,
            color: isPostEmphasis ? '#3fb950' : '#8b949e',
            boxShadow: isPostEmphasis ? `0 0 ${dividerGlow}px rgba(63, 185, 80, 0.7)` : 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            letterSpacing: '1px',
            textTransform: 'uppercase',
          }}
        >
          {isPostEmphasis ? (
            <>
              <SparklesIcon size={18} color="#3fb950" />
              <span>Transformed</span>
            </>
          ) : (
            <span>Optimizing Syntax...</span>
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

      {/* 4. AFTER CODE BLOCK (520px) */}
      <div
        style={{
          height: '520px',
          backgroundColor: isPostEmphasis ? '#0a2213' : '#101b13',
          borderRadius: '22px',
          border: isPostEmphasis
            ? '2px solid rgba(63, 185, 80, 0.9)'
            : '1.5px dashed rgba(63, 185, 80, 0.35)',
          boxShadow: isPostEmphasis
            ? `0 0 ${Math.round(transformProgress * 28)}px rgba(63, 185, 80, 0.4)`
            : 'none',
          padding: '24px 28px',
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
            fontSize: '18px',
            fontWeight: 'bold',
            alignSelf: 'flex-start',
          }}
        >
          <SparklesIcon size={18} color="#3fb950" />
          <span>After (Idiomatic / O(1))</span>
        </div>
        <pre style={{ margin: 0, fontSize: '26px', lineHeight: '1.5', color: '#e6edf3', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
          <TransformSnippet
            code={afterCode}
            scene={scene}
            words={words}
            fps={fps}
            nextSceneStartTime={nextSceneStartTime}
            styleVariant="pill"
          />
        </pre>
      </div>

      {/* 5. BOTTOM INSIGHT PILL (120px) */}
      <div
        style={{
          height: '120px',
          backgroundColor: '#090d13',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ fontSize: '22px', color: '#3fb950', fontWeight: 'bold', fontFamily: 'monospace' }}>
          Refactored in-place with zero memory allocation overhead.
        </div>
        <span
          style={{
            backgroundColor: 'rgba(63, 185, 80, 0.15)',
            border: '1px solid #3fb950',
            color: '#3fb950',
            borderRadius: '6px',
            padding: '4px 14px',
            fontSize: '16px',
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
