import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { SPRING_BADGE_CONFIG, BADGE_THEMES } from '../badgeUtils';

export { SPRING_BADGE_CONFIG, BADGE_THEMES };

/**
 * SceneBadge Component
 *
 * Renders an animated semantic badge ({ label, type, icon, category })
 * over the active code card using Remotion damped springs.
 *
 * Characteristics:
 * - Damped spring entrance (damping: 18, stiffness: 80, mass: 0.6).
 * - Clamped progress and 4-decimal rounded scale/opacity eliminate rasterization jitter.
 * - Hardware acceleration via translateZ(0) and backfaceVisibility: hidden.
 * - Displays icon + label with category-specific color palette.
 */
import { DynamicBadgeIcon } from './SvgIcons';

export const SceneBadge = ({
  badge,
  startFrame = 0,
  springConfig = SPRING_BADGE_CONFIG,
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!badge || !badge.label) {
    return null;
  }

  const currentFrame = frame - startFrame;
  if (currentFrame < 0) {
    return null;
  }

  const springVal = spring({
    frame: currentFrame,
    fps,
    config: springConfig,
  });

  // Clamp overshoot to eliminate jitter
  const progress = Math.max(0, Math.min(springVal, 1.0));
  const scale = Math.round(interpolate(progress, [0, 1], [0.8, 1.0]) * 10000) / 10000;
  const opacity = Math.round(interpolate(progress, [0, 1], [0, 1]) * 10000) / 10000;

  const theme = BADGE_THEMES[badge.type] ||
    BADGE_THEMES[badge.category] ||
    BADGE_THEMES.info;

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '10px',
        padding: '8px 18px',
        borderRadius: '16px',
        backgroundColor: theme.background,
        border: theme.border,
        boxShadow: theme.boxShadow,
        color: theme.color,
        fontSize: '22px',
        fontWeight: 800,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
        transform: `scale(${scale}) translateZ(0)`,
        transformOrigin: 'center center',
        opacity,
        pointerEvents: 'none',
        zIndex: 20,
        boxSizing: 'border-box',
        backfaceVisibility: 'hidden',
        willChange: 'transform, opacity',
        ...style,
      }}
    >
      <DynamicBadgeIcon icon={badge.icon} type={badge.type || badge.category} size={22} color={theme.color} />
      <span>{badge.label}</span>
    </div>
  );
};

export default SceneBadge;

