import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { useBrand } from '../context/BrandContext';
import { WarningIcon, CheckIcon, LightningIcon, SparklesIcon } from './SvgIcons';

export interface HookSceneProps {
  scene: {
    title?: string;
    display_text?: string;
    badge?: { text?: string; type?: string; label?: string };
    items?: Array<{
      label?: string;
      title?: string;
      detail?: string;
      subtitle?: string;
      status?: 'done' | 'crashed' | 'warning' | 'duplicate_risk' | string;
    }>;
    narration?: string;
    spoken_text?: string;
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

export const HookScene: React.FC<HookSceneProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const brand = useBrand();
  const localFrame = Math.max(0, frame - sceneStartFrame);

  // Status pill text from props — NEVER hardcoded ANTI-PATTERN
  const pillText = scene?.badge?.text || scene?.badge?.label || scene?.display_text || 'PROBLEM • DISTRIBUTED EXECUTION';
  const headline = scene?.title || 'The Distributed Execution Failure Mode';

  // Items for Problem / Outcome Flow Diagram
  const items = scene?.items && scene.items.length > 0 ? scene.items : [];

  // Micro animations
  const titleOpacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const titleY = interpolate(localFrame, [0, 10], [15, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'done':
        return { text: '#34d399', bg: 'rgba(52, 211, 153, 0.12)', border: 'rgba(52, 211, 153, 0.35)', icon: <CheckIcon size={20} color="#34d399" /> };
      case 'crashed':
        return { text: '#f87171', bg: 'rgba(248, 113, 113, 0.14)', border: 'rgba(248, 113, 113, 0.45)', icon: <WarningIcon size={20} color="#f87171" /> };
      case 'duplicate_risk':
      case 'warning':
      default:
        return { text: '#fbbf24', bg: 'rgba(251, 191, 36, 0.14)', border: 'rgba(251, 191, 36, 0.45)', icon: <LightningIcon size={20} color="#fbbf24" /> };
    }
  };

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: isWidescreen ? '20px 40px' : '20px 10px',
        boxSizing: 'border-box',
        fontFamily: brand.font_sans,
      }}
    >
      {/* Top Contextual Status Pill */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 20px',
          borderRadius: '999px',
          backgroundColor: 'rgba(245, 158, 11, 0.12)',
          border: '1px solid rgba(245, 158, 11, 0.35)',
          color: '#fbbf24',
          fontSize: isWidescreen ? '15px' : '16px',
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          marginBottom: isWidescreen ? '18px' : '24px',
          boxShadow: '0 0 20px rgba(245, 158, 11, 0.15)',
        }}
      >
        <SparklesIcon size={16} color="#fbbf24" />
        {pillText}
      </div>

      {/* Main Headline */}
      <h1
        style={{
          fontSize: isWidescreen ? '44px' : '46px',
          fontWeight: 900,
          color: '#ffffff',
          textAlign: 'center',
          lineHeight: 1.15,
          maxWidth: isWidescreen ? '1200px' : '900px',
          margin: 0,
          marginBottom: isWidescreen ? '36px' : '48px',
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          letterSpacing: '-0.02em',
          textShadow: '0 4px 20px rgba(0,0,0,0.8)',
        }}
      >
        {headline}
      </h1>

      {/* Problem / Outcome Flow Diagram */}
      <div
        style={{
          width: '100%',
          maxWidth: isWidescreen ? '1380px' : '920px',
          display: 'flex',
          flexDirection: isWidescreen ? 'row' : 'column',
          alignItems: 'stretch',
          justifyContent: 'center',
          gap: isWidescreen ? '24px' : '20px',
        }}
      >
        {items.map((item, idx) => {
          const cfg = getStatusColor(item.status);
          const itemDelay = idx * 6;
          const itemOpacity = interpolate(localFrame, [itemDelay, itemDelay + 8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const itemScale = interpolate(localFrame, [itemDelay, itemDelay + 8], [0.94, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

          return (
            <React.Fragment key={idx}>
              <div
                style={{
                  flex: 1,
                  backgroundColor: 'rgba(17, 19, 28, 0.85)',
                  border: `1.5px solid ${cfg.border}`,
                  borderRadius: '20px',
                  padding: isWidescreen ? '28px 24px' : '26px 28px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: `0 16px 36px -10px rgba(0,0,0,0.7), 0 0 24px ${cfg.bg}`,
                  backdropFilter: 'blur(16px)',
                  opacity: itemOpacity,
                  transform: `scale(${itemScale})`,
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {/* Accent top gradient bar */}
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '4px',
                    backgroundColor: cfg.text,
                    opacity: 0.8,
                  }}
                />

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <span
                    style={{
                      fontFamily: brand.font_mono,
                      fontSize: '14px',
                      fontWeight: 700,
                      color: '#94a3b8',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                    }}
                  >
                    {item.label || `Node 0${idx + 1}`}
                  </span>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 10px',
                      borderRadius: '8px',
                      backgroundColor: cfg.bg,
                      color: cfg.text,
                      fontSize: '12px',
                      fontWeight: 800,
                      fontFamily: brand.font_mono,
                      textTransform: 'uppercase',
                    }}
                  >
                    {cfg.icon}
                    {item.status?.replace('_', ' ') || 'ACTIVE'}
                  </div>
                </div>

                <div
                  style={{
                    fontSize: isWidescreen ? '28px' : '22px',
                    fontWeight: 700,
                    color: '#f8fafc',
                    lineHeight: 1.35,
                  }}
                >
                  {item.detail || item.title || item.subtitle}
                </div>
              </div>

              {/* Connector line between steps */}
              {idx < items.length - 1 && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: isWidescreen ? '0 4px' : '4px 0',
                    color: '#64748b',
                    fontSize: isWidescreen ? '26px' : '22px',
                    opacity: itemOpacity,
                  }}
                >
                  {isWidescreen ? '➔' : '⬇'}
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default HookScene;

