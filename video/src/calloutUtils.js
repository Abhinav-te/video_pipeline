/**
 * calloutUtils.js
 * Utility helpers for kinetic token highlighting, fuzzy matching, and Whisper timing alignment.
 */

export const SPRING_CALLOUT_CONFIG = {
  damping: 18,
  stiffness: 80,
  mass: 0.6,
};

/**
 * Normalizes text for robust token comparison (lowercased, stripped punctuation).
 */
export function normalizeText(text) {
  if (!text || typeof text !== 'string') return '';
  return text.trim().toLowerCase().replace(/[.,!?:;'"(){}[\]<>]/g, '');
}

/**
 * Robust, case-insensitive, whitespace-tolerant token matching in code snippets.
 * Returns { index: number, length: number } or null.
 */
export function findTokenMatch(code, targetPhrase) {
  if (!code || !targetPhrase || typeof code !== 'string' || typeof targetPhrase !== 'string') {
    return null;
  }

  const trimmedTarget = targetPhrase.trim();
  if (!trimmedTarget) return null;

  // 1. Direct exact match
  const exactIndex = code.indexOf(trimmedTarget);
  if (exactIndex !== -1) {
    return { index: exactIndex, length: trimmedTarget.length };
  }

  // 2. Case-insensitive exact match
  const lowerCode = code.toLowerCase();
  const lowerTarget = trimmedTarget.toLowerCase();
  const lowerIndex = lowerCode.indexOf(lowerTarget);
  if (lowerIndex !== -1) {
    return { index: lowerIndex, length: trimmedTarget.length };
  }

  // 3. Flexible whitespace & punctuation matching via regex
  try {
    const tokens = trimmedTarget.split(/\s+/).filter(Boolean);
    if (tokens.length > 0) {
      const escaped = tokens
        .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
        .join('\\s*');
      const regex = new RegExp(escaped, 'i');
      const match = regex.exec(code);
      if (match) {
        return { index: match.index, length: match[0].length };
      }
    }
  } catch (_) {
    // Regex parsing fallback
  }

  // 4. Token-level fallback for key alphanumeric identifiers
  try {
    const words = trimmedTarget
      .split(/[^a-zA-Z0-9_]+/)
      .filter((w) => w.length > 2);
    for (const word of words) {
      const wordRegex = new RegExp(`\\b${word}\\b`, 'i');
      const match = wordRegex.exec(code);
      if (match) {
        return { index: match.index, length: match[0].length };
      }
    }
  } catch (_) {
    // Regex parsing fallback
  }

  return null;
}

/**
 * Splits code into { before, match, after } around the target phrase.
 * If no match is found, match is null and entire code is in before.
 */
export function splitCodeByToken(code, targetPhrase) {
  if (!code || typeof code !== 'string') {
    return { before: '', match: null, after: '' };
  }

  const matchInfo = findTokenMatch(code, targetPhrase);
  if (!matchInfo) {
    return { before: code, match: null, after: '' };
  }

  const { index, length } = matchInfo;
  return {
    before: code.slice(0, index),
    match: code.slice(index, index + length),
    after: code.slice(index + length),
  };
}

/**
 * Resolves startFrame and endFrame for a callout using Whisper word timings.
 */
export function resolveCalloutTiming({
  scene,
  words = [],
  fps = 30,
  nextSceneStartTime = null,
}) {
  if (!scene) {
    return { startFrame: 0, endFrame: 60, matchedWord: null };
  }

  const sceneStart = typeof scene.start_time === 'number' ? scene.start_time : 0;
  const sceneEnd = typeof nextSceneStartTime === 'number' && nextSceneStartTime > sceneStart
    ? nextSceneStartTime
    : sceneStart + 4.0;

  // Search words in Whisper array
  let matchedWord = null;
  const targetCandidates = [];

  if (scene.emphasis_word) {
    targetCandidates.push(normalizeText(scene.emphasis_word));
  }
  if (scene.focus_phrase) {
    const phraseWords = scene.focus_phrase
      .split(/[^a-zA-Z0-9_]+/)
      .map(normalizeText)
      .filter((w) => w.length > 2);
    targetCandidates.push(...phraseWords);
  }

  if (Array.isArray(words) && words.length > 0 && targetCandidates.length > 0) {
    for (const w of words) {
      if (w.start >= sceneStart - 0.25 && w.end <= sceneEnd + 0.25) {
        const normWord = normalizeText(w.word);
        if (targetCandidates.includes(normWord)) {
          matchedWord = w;
          break;
        }
      }
    }
  }

  let startSec;
  let endSec;

  if (matchedWord && typeof matchedWord.start === 'number') {
    startSec = matchedWord.start;
    // Hold highlight at least 1.6s or until scene boundary
    endSec = Math.max(matchedWord.end + 1.2, startSec + 1.6);
    if (typeof nextSceneStartTime === 'number' && nextSceneStartTime > startSec) {
      endSec = Math.min(endSec, nextSceneStartTime);
    }
  } else if (typeof scene.emphasis_time === 'number' && scene.emphasis_time >= 0) {
    startSec = scene.emphasis_time;
    endSec = typeof nextSceneStartTime === 'number' && nextSceneStartTime > startSec
      ? nextSceneStartTime
      : startSec + 2.0;
  } else {
    startSec = sceneStart;
    endSec = typeof nextSceneStartTime === 'number' && nextSceneStartTime > startSec
      ? nextSceneStartTime
      : startSec + 2.0;
  }

  const startFrame = Math.max(0, Math.round(startSec * fps));
  const endFrame = Math.max(startFrame + 15, Math.round(endSec * fps));

  return {
    startFrame,
    endFrame,
    matchedWord,
  };
}

/**
 * Styling presets for accent visual styles:
 * 1. pill / background_pill
 * 2. box_glow / box_border_glow
 * 3. badge / badge_tag
 */
export const CALLOUT_STYLES = {
  pill: {
    background: 'rgba(255, 214, 51, 0.22)',
    border: '1px solid rgba(255, 214, 51, 0.6)',
    borderRadius: '8px',
    boxShadow: '0 0 16px rgba(255, 214, 51, 0.45)',
    textColor: '#ffd633',
    textShadow: '0 0 12px rgba(255, 214, 51, 0.6)',
  },
  box_glow: {
    background: 'rgba(88, 166, 255, 0.18)',
    border: '2px solid #58a6ff',
    borderRadius: '6px',
    boxShadow: '0 0 20px rgba(88, 166, 255, 0.65), inset 0 0 10px rgba(88, 166, 255, 0.25)',
    textColor: '#79c0ff',
    textShadow: '0 0 14px rgba(88, 166, 255, 0.7)',
  },
  badge: {
    background: 'linear-gradient(135deg, rgba(255, 123, 114, 0.35), rgba(210, 153, 34, 0.35))',
    border: '1px solid #ff7b72',
    borderRadius: '6px',
    boxShadow: '0 4px 14px rgba(0, 0, 0, 0.5), 0 0 14px rgba(255, 123, 114, 0.5)',
    textColor: '#ffffff',
    textShadow: '0 0 10px rgba(255, 123, 114, 0.7)',
  },
};

