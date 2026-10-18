/**
 * badgeUtils.js
 * Visual theme palettes, damped spring physics, and helpers for semantic scene badges.
 */

export const SPRING_BADGE_CONFIG = {
  damping: 18,
  stiffness: 80,
  mass: 0.6,
};

export const BADGE_THEMES = {
  warning: {
    background: 'rgba(255, 123, 114, 0.16)',
    border: '1.5px solid rgba(255, 123, 114, 0.65)',
    color: '#ff7b72',
    boxShadow: '0 4px 16px rgba(255, 123, 114, 0.35)',
  },
  success: {
    background: 'rgba(63, 185, 80, 0.16)',
    border: '1.5px solid rgba(63, 185, 80, 0.65)',
    color: '#3fb950',
    boxShadow: '0 4px 16px rgba(63, 185, 80, 0.35)',
  },
  accent: {
    background: 'rgba(210, 153, 34, 0.16)',
    border: '1.5px solid rgba(210, 153, 34, 0.65)',
    color: '#e3b341',
    boxShadow: '0 4px 16px rgba(210, 153, 34, 0.35)',
  },
  performance: {
    background: 'rgba(210, 153, 34, 0.16)',
    border: '1.5px solid rgba(210, 153, 34, 0.65)',
    color: '#e3b341',
    boxShadow: '0 4px 16px rgba(210, 153, 34, 0.35)',
  },
  insight: {
    background: 'rgba(163, 113, 247, 0.16)',
    border: '1.5px solid rgba(163, 113, 247, 0.65)',
    color: '#d2a8ff',
    boxShadow: '0 4px 16px rgba(163, 113, 247, 0.35)',
  },
  info: {
    background: 'rgba(88, 166, 255, 0.16)',
    border: '1.5px solid rgba(88, 166, 255, 0.65)',
    color: '#58a6ff',
    boxShadow: '0 4px 16px rgba(88, 166, 255, 0.35)',
  },
};
