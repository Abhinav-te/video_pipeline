import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import {
  SPRING_CONFIG,
  computeFocusOrigin,
  computeCameraZoom,
} from './cameraUtils';

export { SPRING_CONFIG, computeFocusOrigin, computeCameraZoom };

/**
 * CameraRig Component
 *
 * Provides optical emphasis aura around content cards without continuous scale transforms.
 *
 * Permanent Anti-Jitter Architecture:
 * - Lock to 1.0x scale (transform: none) to eliminate Chromium font hinting and
 *   subpixel rasterization vibration across frames.
 * - Card-level emphasis aura: animates a subtle boxShadow glow expansion and border
 *   accent illumination at emphasis_time driven by critically damped spring progress.
 * - Text and code containers remain on a 100% static pixel grid.
 */
export const CameraRig = ({
  children,
  scene,
  startTime,
  emphasisTime,
  baselineScale = 1.0,
  focusScale = 1.04,
  springConfig = SPRING_CONFIG,
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Resolve timing boundaries safely
  const sceneStart = typeof startTime === 'number'
    ? startTime
    : (typeof scene?.start_time === 'number' ? scene.start_time : 0);

  const sceneEmphasis = typeof emphasisTime === 'number'
    ? emphasisTime
    : (typeof scene?.emphasis_time === 'number' ? scene.emphasis_time : sceneStart);

  const triggerTime = Math.max(sceneStart, sceneEmphasis);
  const triggerFrame = Math.round(triggerTime * fps);

  const { progress, scale } = computeCameraZoom({
    frame,
    triggerFrame,
    fps,
    config: springConfig,
    baselineScale,
    focusScale,
  });

  // Scale is locked to 1.0 to eliminate font hinting noise
  const roundedScale = Math.round(scale * 10000) / 10000;

  // Visual emphasis aura (animated glow intensity + border accent pulse)
  const glowBlur = Math.round(interpolate(progress, [0, 1], [0, 36]));
  const glowSpread = Math.round(interpolate(progress, [0, 1], [0, 4]));
  const glowOpacity = Math.round(interpolate(progress, [0, 1], [0, 0.45]) * 1000) / 1000;

  const auraBoxShadow = progress > 0.01
    ? `0 0 ${glowBlur}px ${glowSpread}px rgba(88, 166, 255, ${glowOpacity}), 0 20px 40px -10px rgba(0, 0, 0, 0.7)`
    : '0 20px 40px -10px rgba(0, 0, 0, 0.7)';

  return (
    <div
      style={{
        // Text stability: transform is locked to 'none' on a 1:1 pixel grid
        transform: 'none',
        transformOrigin: 'center center',
        boxShadow: auraBoxShadow,
        borderRadius: '24px',
        width: '100%',
        boxSizing: 'border-box',
        backfaceVisibility: 'hidden',
        willChange: 'box-shadow',
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export default CameraRig;
