import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { CALLOUT_STYLES, SPRING_CALLOUT_CONFIG } from '../calloutUtils';

/**
 * KineticCallout
 * Reusable Remotion component for word-synchronized token callouts with spring entrance
 * and smooth exit fade across three visual styles: 'pill', 'box_glow', and 'badge'.
 *
 * Permanent Anti-Jitter Architecture:
 * - Text span is locked to transform: none on a 1:1 static pixel grid.
 * - Background highlight pill uses position: absolute; inset: -2px -6px; z-index: -1; border-radius: 6px;
 * - Only opacity and boxShadow are animated — NO scale transforms on text or background.
 * - Outer wrapper is display: inline (NOT inline-block) for zero height contribution.
 */
export const KineticCallout = ({
  children,
  startFrame = 0,
  endFrame = Infinity,
  exitDurationFrames = 12,
  styleVariant = 'pill',
  springConfig = SPRING_CALLOUT_CONFIG,
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Resolve preset variant (pill, box_glow, badge)
  const variant = CALLOUT_STYLES[styleVariant] || CALLOUT_STYLES.pill;

  // Calculate entrance and exit animation progress
  let highlightScale = 1.0;
  let highlightOpacity = 0;
  let isActive = false;

  if (frame >= startFrame) {
    if (frame < endFrame) {
      // Entrance phase via native Remotion spring()
      const springVal = spring({
        frame: frame - startFrame,
        fps,
        config: springConfig,
      });
      // Clamp overshoots to eliminate any underdamped micro-vibrations
      const progress = Math.max(0, Math.min(springVal, 1.0));
      // Preserved scale progression value for backward compatibility: [0.8, 1.0]
      highlightScale = Math.round(interpolate(progress, [0, 1], [0.8, 1.0]) * 10000) / 10000;
      highlightOpacity = Math.round(interpolate(progress, [0, 1], [0, 1]) * 10000) / 10000;
      isActive = true;
    } else {
      // Exit fade phase
      const exitProgress = interpolate(
        frame,
        [endFrame, endFrame + exitDurationFrames],
        [1, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      );
      highlightScale = 1.0;
      highlightOpacity = Math.round(exitProgress * 10000) / 10000;
      isActive = exitProgress > 0;
    }
  }

  // Active text color punch during highlight
  const textColor = isActive && highlightOpacity > 0.05
    ? variant.textColor
    : 'inherit';
  const textShadow = isActive && highlightOpacity > 0.05
    ? variant.textShadow
    : 'none';

  return (
    <span
      style={{
        // display:inline (NOT inline-block) → zero height contribution, no line-height shift
        position: 'relative',
        display: 'inline',
        verticalAlign: 'baseline',
        lineHeight: 'inherit',
        fontFamily: 'inherit',
        fontSize: 'inherit',
        transform: 'none',
        backfaceVisibility: 'hidden',
        ...style,
      }}
    >
      {/*
        Decorative Background Highlight Pill:
        Positioned behind text (z-index: -1).
        Locked to transform: none to eliminate Chromium sub-pixel font hinting vibration.
        Animates opacity and boxShadow only.
      */}
      <span
        style={{
          position: 'absolute',
          inset: '-2px -6px',
          background: variant.background,
          border: variant.border,
          borderRadius: '6px',
          boxShadow: variant.boxShadow,
          opacity: highlightOpacity,
          transform: 'none',
          transformOrigin: 'center center',
          pointerEvents: 'none',
          zIndex: -1,
          willChange: 'opacity, box-shadow',
          backfaceVisibility: 'hidden',
        }}
      />

      {/* Stable Monospace Text Content — locked to transform: none on a 1:1 pixel grid */}
      <span
        style={{
          position: 'relative',
          zIndex: 1,
          color: textColor,
          textShadow,
          fontFamily: 'inherit',
          fontSize: 'inherit',
          lineHeight: 'inherit',
          boxSizing: 'border-box',
          display: 'inline',
          transform: 'none',
          backfaceVisibility: 'hidden',
        }}
      >
        {children}
      </span>
    </span>
  );
};

export default KineticCallout;
