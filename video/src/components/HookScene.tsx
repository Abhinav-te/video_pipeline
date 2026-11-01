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

const cleanProse = (text?: string): string => {
  if (!text) return '';
  return text.replace(/^#+\s*/gm, '').replace(/\*\*(.*?)\*\*/g, '$1').trim();
};

const normalizeForComparison = (text?: string): string => {
  return (text || '').toLowerCase().replace(/[^a-z0-9]/g, '');
};

export const HookScene: React.FC<HookSceneProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const brand = useBrand();
  const localFrame = Math.max(0, frame - sceneStartFrame);

  // Derive a clean, concise category label without echoing the entire scene title
  const deriveCategoryLabel = (): string => {
    if (scene?.badge?.label) return cleanProse(scene.badge.label).toUpperCase();
    if (scene?.badge?.type) {
      const t = scene.badge.type.toLowerCase();
      if (t === 'warning' || t === 'problem') return 'SYSTEM FAILURE';
      if (t === 'accent') return 'CORE ARCHITECTURE';
      if (t === 'success') return 'VERIFIED BEHAVIOR';
      return t.toUpperCase();
    }
    const rawPill = scene?.badge?.text || scene?.display_text || '';
    if (rawPill) {
      const clean = cleanProse(rawPill);
      if (clean.includes('•')) {
        const prefix = clean.split('•')[0].trim();
        if (prefix.length > 0 && prefix.length <= 20) return prefix.toUpperCase();
      }
      if (clean.includes(':')) {
        const prefix = clean.split(':')[0].trim();
        if (prefix.length > 0 && prefix.length <= 20) return prefix.toUpperCase();
      }
      const titleNorm = normalizeForComparison(scene?.title);
      const cleanNorm = normalizeForComparison(clean);
      if (clean.length <= 24 && cleanNorm !== titleNorm) {
        return clean.toUpperCase();
      }
    }
    return 'PROBLEM';
  };

  const categoryLabel = deriveCategoryLabel();
  const headline = cleanProse(scene?.title || 'System Execution Failure');
  const headlineNorm = normalizeForComparison(headline);

  // Items for Problem / Consequence Architecture Flow
  const rawItems = scene?.items && scene.items.length > 0 ? scene.items : [];

  // Deduplicate card content if detail/title is an exact normalized duplicate of headline
  const resolveCardItem = (item: NonNullable<HookSceneProps['scene']['items']>[0]) => {
    const rawDetail = cleanProse(item.detail);
    const rawTitle = cleanProse(item.title);
    const rawSubtitle = cleanProse(item.subtitle);

    let primary = rawDetail || rawTitle || rawSubtitle || '';
    let secondary: string | undefined = undefined;

    if (rawSubtitle && normalizeForComparison(rawSubtitle) !== headlineNorm) {
      secondary = rawSubtitle;
    }

    // Check if primary is an exact duplicate of the headline
    if (normalizeForComparison(primary) === headlineNorm) {
      if (rawTitle && normalizeForComparison(rawTitle) !== headlineNorm) {
        primary = rawTitle;
      } else if (rawSubtitle && normalizeForComparison(rawSubtitle) !== headlineNorm) {
        primary = rawSubtitle;
      } else {
        // Differentiate by semantic role
        if (item.status === 'crashed') {
          primary = 'Step Execution Interruption';
          secondary = 'Process halted before checkpoint completion';
        } else if (item.status === 'warning') {
          primary = 'Side Effect Boundary Risk';
          secondary = 'Requires idempotent handler verification';
        } else {
          primary = `${cleanProse(item.label) || 'Diagnostic'} Checkpoint`;
        }
      }
    }

    return {
      label: cleanProse(item.label) || 'Workflow State',
      status: item.status || 'warning',
      primaryText: primary,
      secondaryText: secondary,
    };
  };

  const processedItems = rawItems.map(resolveCardItem);

  // Micro animations
  const titleOpacity = interpolate(localFrame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const titleY = interpolate(localFrame, [0, 8], [12, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'done':
        return {
          text: '#10B981',
          bg: 'rgba(16, 185, 129, 0.12)',
          border: 'rgba(16, 185, 129, 0.35)',
          topAccent: '#10B981',
          icon: <CheckIcon size={18} color="#10B981" />,
        };
      case 'crashed':
        return {
          text: '#EF4444',
          bg: 'rgba(239, 68, 68, 0.12)',
          border: 'rgba(239, 68, 68, 0.35)',
          topAccent: '#EF4444',
          icon: <WarningIcon size={18} color="#EF4444" />,
        };
      case 'duplicate_risk':
      case 'warning':
      default:
        return {
          text: '#F59E0B',
          bg: 'rgba(245, 158, 11, 0.12)',
          border: 'rgba(245, 158, 11, 0.35)',
          topAccent: '#F59E0B',
          icon: <LightningIcon size={18} color="#F59E0B" />,
        };
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
      {/* Level 1: Semantic Category Badge (Restrained, No Title Echo) */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 16px',
          borderRadius: '999px',
          backgroundColor: 'rgba(245, 158, 11, 0.10)',
          border: '1px solid rgba(245, 158, 11, 0.28)',
          color: '#F59E0B',
          fontSize: isWidescreen ? '13px' : '14px',
          fontWeight: 700,
          fontFamily: brand.font_mono,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          marginBottom: isWidescreen ? '16px' : '20px',
        }}
      >
        <SparklesIcon size={14} color="#F59E0B" />
        {categoryLabel}
      </div>

      {/* Level 2: Principal Heading */}
      <h1
        style={{
          fontSize: isWidescreen ? '38px' : '40px',
          fontWeight: 800,
          color: '#F8FAFC',
          textAlign: 'center',
          lineHeight: 1.2,
          maxWidth: isWidescreen ? '1280px' : '920px',
          margin: 0,
          marginBottom: isWidescreen ? '36px' : '44px',
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          letterSpacing: '-0.02em',
          textShadow: '0 4px 16px rgba(0, 0, 0, 0.85)',
        }}
      >
        {headline}
      </h1>

      {/* Level 3: Problem / Consequence Architecture Flow */}
      <div
        style={{
          width: '100%',
          maxWidth: isWidescreen ? '1520px' : '960px',
          display: 'flex',
          flexDirection: isWidescreen ? 'row' : 'column',
          alignItems: 'stretch',
          justifyContent: 'center',
          gap: isWidescreen ? '20px' : '16px',
        }}
      >
        {processedItems.map((item, idx) => {
          const cfg = getStatusColor(item.status);
          const itemDelay = idx * 5;
          const itemOpacity = interpolate(localFrame, [itemDelay, itemDelay + 8], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const itemTranslateY = interpolate(localFrame, [itemDelay, itemDelay + 8], [10, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          return (
            <React.Fragment key={idx}>
              <div
                style={{
                  flex: 1,
                  backgroundColor: 'rgba(17, 20, 29, 0.88)',
                  border: `1px solid ${cfg.border}`,
                  borderRadius: '18px',
                  padding: isWidescreen ? '30px 32px' : '26px 28px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: `0 20px 40px -15px rgba(0, 0, 0, 0.75), 0 0 20px -5px ${cfg.bg}`,
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  opacity: itemOpacity,
                  transform: `translateY(${itemTranslateY}px)`,
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {/* Semantic Top Inset Accent Bar */}
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '3px',
                    backgroundColor: cfg.topAccent,
                    opacity: 0.9,
                  }}
                />

                {/* Card Header Row: Label & Status Badge */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '16px',
                  }}
                >
                  <span
                    style={{
                      fontFamily: brand.font_mono,
                      fontSize: '13px',
                      fontWeight: 700,
                      color: '#94A3B8',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                    }}
                  >
                    {item.label}
                  </span>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      backgroundColor: cfg.bg,
                      color: cfg.text,
                      fontSize: '12px',
                      fontWeight: 700,
                      fontFamily: brand.font_mono,
                      textTransform: 'uppercase',
                    }}
                  >
                    {cfg.icon}
                    {item.status.replace('_', ' ')}
                  </div>
                </div>

                {/* Primary Card Heading */}
                <div
                  style={{
                    fontSize: isWidescreen ? '26px' : '22px',
                    fontWeight: 700,
                    color: '#F8FAFC',
                    lineHeight: 1.3,
                  }}
                >
                  {item.primaryText}
                </div>

                {/* Secondary Supporting Context (if distinct) */}
                {item.secondaryText ? (
                  <div
                    style={{
                      fontSize: isWidescreen ? '15px' : '14px',
                      color: '#94A3B8',
                      lineHeight: 1.45,
                      marginTop: '10px',
                    }}
                  >
                    {item.secondaryText}
                  </div>
                ) : null}
              </div>

              {/* Connector between flow steps */}
              {idx < processedItems.length - 1 && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: isWidescreen ? '0 4px' : '4px 0',
                    color: '#64748B',
                    fontSize: isWidescreen ? '22px' : '20px',
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
