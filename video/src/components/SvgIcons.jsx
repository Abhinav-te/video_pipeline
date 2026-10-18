import React from 'react';

/**
 * Inline SVG Vector Icons replacing Unicode emoji glyphs (preventing headless Linux Chromium tofu boxes [▯]).
 */

export const WarningIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <circle cx="12" cy="17" r="1" fill={color} />
  </svg>
);

export const SparklesIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color} style={{ flexShrink: 0 }}>
    <path d="M12 2L14.2 8.3L20.5 10.5L14.2 12.7L12 19L9.8 12.7L3.5 10.5L9.8 8.3L12 2Z" />
    <path d="M19 16L20.1 18.9L23 20L20.1 21.1L19 24L17.9 21.1L15 20L17.9 18.9L19 16Z" opacity="0.8" />
  </svg>
);

export const LightningIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color} style={{ flexShrink: 0 }}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

export const BulbIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M9 18h6" />
    <path d="M10 22h4" />
    <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A6 6 0 1 0 7.5 11.5c.76.76 1.23 1.52 1.41 2.5h6.18z" />
  </svg>
);

export const ScaleIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <line x1="12" y1="3" x2="12" y2="21" />
    <path d="M5 8l7-4 7 4" />
    <path d="M4 14l3-6 3 6a3 3 0 0 1-6 0z" />
    <path d="M14 14l3-6 3 6a3 3 0 0 1-6 0z" />
    <line x1="4" y1="21" x2="20" y2="21" />
  </svg>
);

export const BrainIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M9.5 2A4.5 4.5 0 0 0 5 6.5C5 7.4 5.3 8.2 5.8 9A4 4 0 0 0 4 12a4 4 0 0 0 1.2 2.8A4.5 4.5 0 0 0 9.5 22c.5 0 1-.1 1.5-.3" />
    <path d="M14.5 2A4.5 4.5 0 0 1 19 6.5c0 .9-.3 1.7-.8 2.5A4 4 0 0 1 20 12a4 4 0 0 1-1.2 2.8A4.5 4.5 0 0 1 14.5 22c-.5 0-1-.1-1.5-.3" />
    <path d="M12 2v20" />
  </svg>
);

export const TargetIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" fill={color} />
  </svg>
);

export const GearIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

export const LayersIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <polygon points="12 2 2 7 12 12 22 7 12 2" />
    <polyline points="2 17 12 22 22 17" />
    <polyline points="2 12 12 17 22 12" />
  </svg>
);

export const CodeIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <polyline points="16 18 22 12 16 6" />
    <polyline points="8 6 2 12 8 18" />
  </svg>
);

export const MathIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M19 5h-7l-4 14-3-7H2" />
  </svg>
);

export const PhysicsIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(30 12 12)" />
    <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(-30 12 12)" />
    <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(90 12 12)" />
    <circle cx="12" cy="12" r="2.5" fill={color} />
  </svg>
);

export const GraphIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
    <polyline points="16 7 22 7 22 13" />
  </svg>
);

export const ChemistryIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M10 2v7.5L4.5 19.5A2 2 0 0 0 6.2 22h11.6a2 2 0 0 0 1.7-2.5L14 9.5V2" />
    <line x1="8.5" y1="2" x2="15.5" y2="2" />
    <path d="M7 16h10" />
    <circle cx="10" cy="18.5" r="1" fill={color} />
    <circle cx="13.5" cy="17" r="0.8" fill={color} />
  </svg>
);

export const QuantumIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="3" fill={color} />
    <path d="M4 12c0-3.5 3.6-7 8-7s8 3.5 8 7-3.6 7-8 7-8-3.5-8-7z" strokeDasharray="3 2" />
    <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(45 12 12)" />
    <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(-45 12 12)" />
  </svg>
);

export const MechanicsIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <rect x="2" y="8" width="20" height="4" rx="1" fill={color} fillOpacity="0.2" />
    <polygon points="5,17 3,21 7,21" strokeWidth="2" />
    <circle cx="19" cy="19" r="2" strokeWidth="2" />
    <line x1="12" y1="2" x2="12" y2="8" strokeWidth="2.5" />
    <polyline points="10,5 12,8 14,5" strokeWidth="2.5" />
  </svg>
);

export const ElectricalIcon = ({ size = 20, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill={color} fillOpacity="0.15" />
    <circle cx="4" cy="4" r="1.5" />
    <circle cx="20" cy="20" r="1.5" />
  </svg>
);

/**
 * Dynamic Badge Icon Resolver: Safely intercepts Unicode emojis or type names
 * and returns the appropriate crisp inline SVG vector.
 */
export const DynamicBadgeIcon = ({ icon, type, size = 22, color = 'currentColor' }) => {
  const iconStr = String(icon || type || '').toLowerCase();

  if (iconStr.includes('quantum') || iconStr.includes('tunnel') || iconStr.includes('schrodinger') || iconStr.includes('dirac')) {
    return <QuantumIcon size={size} color={color} />;
  }
  if (iconStr.includes('mechanic') || iconStr.includes('beam') || iconStr.includes('fbd') || iconStr.includes('axle') || iconStr.includes('statics')) {
    return <MechanicsIcon size={size} color={color} />;
  }
  if (iconStr.includes('electr') || iconStr.includes('grid') || iconStr.includes('circuit') || iconStr.includes('thevenin') || iconStr.includes('kvl') || iconStr.includes('kcl')) {
    return <ElectricalIcon size={size} color={color} />;
  }
  if (iconStr.includes('warn') || iconStr.includes('anti') || iconStr.includes('⚠️')) {
    return <WarningIcon size={size} color={color} />;
  }
  if (iconStr.includes('spark') || iconStr.includes('solution') || iconStr.includes('best') || iconStr.includes('✨')) {
    return <SparklesIcon size={size} color={color} />;
  }
  if (iconStr.includes('light') || iconStr.includes('perf') || iconStr.includes('fast') || iconStr.includes('⚡')) {
    return <LightningIcon size={size} color={color} />;
  }
  if (iconStr.includes('bulb') || iconStr.includes('insight') || iconStr.includes('concept') || iconStr.includes('💡')) {
    return <BulbIcon size={size} color={color} />;
  }
  if (iconStr.includes('scale') || iconStr.includes('comp') || iconStr.includes('⚖')) {
    return <ScaleIcon size={size} color={color} />;
  }
  if (iconStr.includes('brain') || iconStr.includes('neural') || iconStr.includes('ml') || iconStr.includes('🧠')) {
    return <BrainIcon size={size} color={color} />;
  }
  if (iconStr.includes('phys') || iconStr.includes('atom') || iconStr.includes('⚛')) {
    return <PhysicsIcon size={size} color={color} />;
  }
  if (iconStr.includes('chem') || iconStr.includes('flask') || iconStr.includes('molecule') || iconStr.includes('reaction') || iconStr.includes('🧪') || iconStr.includes('⚗')) {
    return <ChemistryIcon size={size} color={color} />;
  }
  if (iconStr.includes('graph') || iconStr.includes('plot') || iconStr.includes('cartesian') || iconStr.includes('📈')) {
    return <GraphIcon size={size} color={color} />;
  }
  if (iconStr.includes('math') || iconStr.includes('euler') || iconStr.includes('📐') || iconStr.includes('∫')) {
    return <MathIcon size={size} color={color} />;
  }
  if (iconStr.includes('gear') || iconStr.includes('param') || iconStr.includes('⚙')) {
    return <GearIcon size={size} color={color} />;
  }
  if (iconStr.includes('target') || iconStr.includes('point') || iconStr.includes('🎯')) {
    return <TargetIcon size={size} color={color} />;
  }
  if (iconStr.includes('layer') || iconStr.includes('stack')) {
    return <LayersIcon size={size} color={color} />;
  }
  if (iconStr.includes('code') || iconStr.includes('term')) {
    return <CodeIcon size={size} color={color} />;
  }

  // Default fallback is SparklesIcon
  return <SparklesIcon size={size} color={color} />;
};
