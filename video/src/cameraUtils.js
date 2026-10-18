import { spring, interpolate } from 'remotion';

export const SPRING_CONFIG = {
  damping: 18,
  stiffness: 80,
  mass: 0.6,
};

/**
 * Computes the 2D transform-origin focal point based on the code snippet and target focus phrase.
 * Returns { originX: number, originY: number } with percentages clamped inside safe bounds.
 */
export const computeFocusOrigin = (scene, codeSnippet, focusPhrase) => {
  const code = codeSnippet || scene?.code_snippet;
  const phrase = focusPhrase || scene?.focus_phrase;
  const sceneType = scene?.scene_type;

  const defaultOrigin = { originX: 50, originY: 50 };

  if (sceneType === 'comparison') {
    const problemCode = scene?.problem_code || '';
    const solutionCode = scene?.solution_code || '';

    if (phrase && solutionCode.includes(phrase)) {
      return { originX: 50, originY: 65 };
    }
    if (phrase && problemCode.includes(phrase)) {
      return { originX: 50, originY: 35 };
    }
    return defaultOrigin;
  }

  if (!code || !phrase || typeof code !== 'string' || typeof phrase !== 'string') {
    return defaultOrigin;
  }

  if (!code.includes(phrase)) {
    return defaultOrigin;
  }

  const lines = code.split('\n');
  const lineIdx = lines.findIndex((l) => l.includes(phrase));
  if (lineIdx === -1 || lines.length === 0) {
    return defaultOrigin;
  }

  // Vertical position: map line index to safe origin bound [32%, 68%]
  const lineRatio = (lineIdx + 0.5) / lines.length;
  const originY = Math.min(68, Math.max(32, Math.round(35 + lineRatio * 30)));

  // Horizontal position: map column offset within target line to safe bound [32%, 68%]
  const targetLine = lines[lineIdx];
  const colIdx = targetLine.indexOf(phrase);
  const colRatio = (colIdx + phrase.length / 2) / Math.max(1, targetLine.length);
  const originX = Math.min(68, Math.max(32, Math.round(35 + colRatio * 30)));

  return { originX, originY };
};

/**
 * Calculates spring progress for camera emphasis aura.
 * Note: scale is permanently locked to 1.0 to eliminate Chromium font hinting jitter.
 * Visual emphasis is driven via optical glow aura (boxShadow) and border brightness.
 */
export const computeCameraZoom = ({
  frame,
  triggerFrame,
  fps = 30,
  config = SPRING_CONFIG,
  baselineScale = 1.0,
  focusScale = 1.04,
}) => {
  if (frame < triggerFrame) {
    return {
      progress: 0,
      scale: 1.0,
      isEmphasized: false,
    };
  }

  const relativeFrame = frame - triggerFrame;
  const progress = spring({
    frame: relativeFrame,
    fps,
    config,
  });

  const clampedProgress = Math.max(0, Math.min(progress, 1.0));

  return {
    progress: clampedProgress,
    scale: 1.0,
    isEmphasized: clampedProgress > 0.05,
  };
};


