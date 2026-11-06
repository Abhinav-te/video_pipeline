import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { useBrand, useTheme, ThemeTokens } from '../context/BrandContext';
import { SparklesIcon, CheckIcon } from './SvgIcons';

export interface BentoCardItem {
  title?: string;
  value?: string;
  metric?: string;
  subtitle?: string;
  description?: string;
  tag?: string;
  evidence_id?: string;
}

export interface EvidenceBentoSceneProps {
  scene: {
    title?: string;
    subtitle?: string;
    items?: BentoCardItem[];
    cards?: BentoCardItem[];
    metrics?: BentoCardItem[];
    evidence_ids?: string[];
    badge?: { text?: string };
    start_time?: number;
    end_time?: number;
    duration?: number;
    caption_chunks?: Array<{
      start: number;
      end: number;
      text: string;
      words?: Array<{ word: string; start: number; end: number }>;
    }>;
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

// Crisp inline vector icons (preventing headless Linux Chromium emoji tofu [▯])
const AlertIcon: React.FC<{ size?: number; color?: string }> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <circle cx="12" cy="17" r="1" fill={color} />
  </svg>
);

const LockIcon: React.FC<{ size?: number; color?: string }> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const ShieldCheckIcon: React.FC<{ size?: number; color?: string }> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <polyline points="9 12 11 14 15 10" />
  </svg>
);

export const EvidenceBentoScene: React.FC<EvidenceBentoSceneProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const brand = useBrand();
  const theme = useTheme();

  const localFrame = Math.max(0, frame - sceneStartFrame);
  const localSec = localFrame / fps;
  const sceneStart = scene?.start_time || 0;
  const sceneDuration = scene?.duration || 8;

  // Cards strictly populated from props (items, cards, or metrics)
  const rawCards: BentoCardItem[] = scene?.items || scene?.cards || scene?.metrics || [];
  if (rawCards.length === 0) {
    throw new Error(
      `[EvidenceBentoScene] Validation Error: 'items', 'cards', or 'metrics' array is required and must not be empty. Scene: "${scene?.title || 'untitled'}"`
    );
  }

  // Validate every card has substantive content
  rawCards.forEach((card, idx) => {
    const val = card.value || card.metric;
    const title = card.title;
    if (!val && !title) {
      throw new Error(
        `[EvidenceBentoScene] Validation Error: Card ${idx + 1} is missing required 'title' or 'value'/'metric'.`
      );
    }
  });

  const headline = scene?.title || 'System Verification';

  // Smooth entrance interpolations
  const titleOpacity = interpolate(localFrame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const titleY = interpolate(localFrame, [0, 8], [8, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stageOpacity = interpolate(localFrame, [2, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stageY = interpolate(localFrame, [2, 10], [10, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Segregate cards into Guarantees/Capabilities vs Constraints/Limitations
  const isLimitationItem = (item: BentoCardItem): boolean => {
    const tag = (item.tag || '').toUpperCase();
    const val = (item.value || '').toUpperCase();
    return (
      tag === 'LIMITATION' ||
      tag === 'CAVEAT' ||
      val.includes('LIMIT') ||
      val.includes('CONSTRAINT') ||
      val.includes('REQUIREMENT') ||
      val.includes('CAVEAT')
    );
  };

  const guarantees = rawCards.filter((c) => !isLimitationItem(c));
  const limitations = rawCards.filter((c) => isLimitationItem(c));

  // Determine narration-synchronized limitation transition timestamp
  let limitationTriggerSec = sceneDuration * 0.45;
  if (scene?.caption_chunks && scene.caption_chunks.length > 0) {
    const limKeywords = ['limitation', 'side effect', 'idempotent', 'caution', 'warning', 'constraint', 'retried step'];
    for (const chunk of scene.caption_chunks) {
      const lower = chunk.text.toLowerCase();
      if (limKeywords.some((k) => lower.includes(k))) {
        limitationTriggerSec = Math.max(0, chunk.start - sceneStart);
        break;
      }
    }
  }

  const isLimitationActive = localSec >= limitationTriggerSec;

  // Limitation illumination animation
  const limAge = Math.max(0, localSec - limitationTriggerSec);
  const limPulse = isLimitationActive
    ? interpolate(limAge, [0, 0.5], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 0;

  // Render individual evidence card with strict theme tokens and clear hierarchy
  const renderCard = (card: BentoCardItem, idx: number, isLim: boolean) => {
    const val = card.value || card.metric || '';
    const title = card.title || '';
    const subtitle = card.subtitle || card.description || '';
    const tag = card.tag || (card.evidence_id ? `#${card.evidence_id}` : undefined);

    const isDurability = (card.tag || '').toUpperCase() === 'DURABILITY' || val.includes('STATE');
    const isResilience = (card.tag || '').toUpperCase() === 'RESILIENCE' || val.includes('RETRY');

    // Semantic accent color determination
    let accentColor = theme.text_secondary;
    let badgeBg = 'rgba(255, 255, 255, 0.04)';
    let badgeBorder = theme.border_subtle;

    if (isLim) {
      accentColor = theme.status_warning; // #E5A743
      badgeBg = 'rgba(229, 167, 67, 0.10)';
      badgeBorder = isLimitationActive ? 'rgba(229, 167, 67, 0.45)' : 'rgba(229, 167, 67, 0.25)';
    } else if (isDurability) {
      accentColor = theme.status_success; // #36A982
      badgeBg = 'rgba(54, 169, 130, 0.10)';
      badgeBorder = 'rgba(54, 169, 130, 0.35)';
    } else if (isResilience) {
      accentColor = theme.syntax_function; // #93C5FD
      badgeBg = 'rgba(147, 197, 253, 0.08)';
      badgeBorder = 'rgba(147, 197, 253, 0.30)';
    }

    const cardBorderColor = isLim
      ? isLimitationActive
        ? `rgba(229, 167, 67, ${0.35 + 0.25 * limPulse})`
        : theme.border_subtle
      : !isLimitationActive
      ? `rgba(54, 169, 130, 0.35)`
      : theme.border_subtle;

    const cardOpacity = isLim
      ? isLimitationActive ? 1 : 0.70
      : isLimitationActive ? 0.85 : 1;

    return (
      <div
        key={idx}
        style={{
          backgroundColor: theme.surface_elevated,
          borderRadius: '16px',
          border: `1.5px solid ${cardBorderColor}`,
          padding: isWidescreen ? '20px 22px' : '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '12px',
          boxSizing: 'border-box',
          boxShadow: isLim && isLimitationActive
            ? '0 16px 36px -10px rgba(0, 0, 0, 0.8), 0 0 20px rgba(229, 167, 67, 0.12)'
            : '0 16px 36px -10px rgba(0, 0, 0, 0.75)',
          opacity: cardOpacity,
          transition: 'all 0.25s ease',
        }}
      >
        {/* Top Header Row: Category Badge + Evidence ID Tag */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '8px',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '6px',
              backgroundColor: badgeBg,
              border: `1px solid ${badgeBorder}`,
              color: accentColor,
              fontSize: '11px',
              fontWeight: 800,
              fontFamily: brand.font_mono,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            {isLim ? (
              <AlertIcon size={12} color={accentColor} />
            ) : isDurability ? (
              <LockIcon size={12} color={accentColor} />
            ) : (
              <CheckIcon size={12} color={accentColor} />
            )}
            <span>{val || (isLim ? 'SAFETY CONSTRAINT' : 'SYSTEM GUARANTEE')}</span>
          </div>

          {card.evidence_id && (
            <div
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: theme.text_muted,
                fontFamily: brand.font_mono,
                letterSpacing: '0.04em',
              }}
            >
              #{card.evidence_id}
            </div>
          )}
        </div>

        {/* Substantive Headline & Description */}
        <div>
          <div
            style={{
              fontSize: isWidescreen ? '18px' : '17px',
              fontWeight: 800,
              color: theme.text_primary,
              lineHeight: 1.3,
              marginBottom: '6px',
              fontFamily: brand.font_mono,
              letterSpacing: '-0.01em',
            }}
          >
            {title}
          </div>

          {subtitle && (
            <div
              style={{
                fontSize: '13px',
                color: theme.text_secondary,
                lineHeight: 1.45,
                fontFamily: brand.font_sans,
              }}
            >
              {subtitle}
            </div>
          )}
        </div>

        {/* Provenance Footer: Specification Source Citation */}
        <div
          style={{
            borderTop: `1px solid ${theme.border_subtle}`,
            paddingTop: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '11px',
            fontFamily: brand.font_mono,
            color: theme.text_muted,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: accentColor }}>●</span>
            <span>{isLim ? 'Documented Caveat' : 'Official Docs Specification'}</span>
          </div>
          <span>CITED PROVENANCE</span>
        </div>
      </div>
    );
  };

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: isWidescreen ? '14px 32px' : '16px 12px',
        boxSizing: 'border-box',
        fontFamily: brand.font_sans,
      }}
    >
      {/* Level 1 & 2: Restrained Scene Heading & Contextual Pill */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          marginBottom: isWidescreen ? '16px' : '18px',
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '5px 14px',
            borderRadius: '999px',
            backgroundColor: 'rgba(147, 197, 253, 0.08)',
            border: '1px solid rgba(147, 197, 253, 0.22)',
            color: '#93C5FD',
            fontSize: '12px',
            fontWeight: 700,
            fontFamily: brand.font_mono,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: '8px',
          }}
        >
          <SparklesIcon size={13} color="#93C5FD" />
          {scene?.badge?.text || 'EVIDENCE AUDIT • ARCHITECTURAL GUARANTEES'}
        </div>

        <h1
          style={{
            fontSize: isWidescreen ? '30px' : '32px',
            fontWeight: 800,
            color: theme.text_primary,
            lineHeight: 1.25,
            letterSpacing: '-0.02em',
            margin: 0,
            maxWidth: isWidescreen ? '1320px' : '920px',
            textShadow: '0 4px 16px rgba(0, 0, 0, 0.85)',
          }}
        >
          {headline}
        </h1>
        {scene.subtitle && (
          <div
            style={{
              fontSize: '13px',
              color: theme.text_secondary,
              fontFamily: brand.font_mono,
              marginTop: '6px',
            }}
          >
            {scene.subtitle}
          </div>
        )}
      </div>

      {/* Main Evidence Board Stage */}
      <div
        style={{
          width: '100%',
          maxWidth: isWidescreen ? '1540px' : '960px',
          display: 'flex',
          flexDirection: isWidescreen ? 'row' : 'column',
          alignItems: isWidescreen ? 'stretch' : 'center',
          justifyContent: 'center',
          gap: isWidescreen ? '24px' : '14px',
          opacity: stageOpacity,
          transform: `translateY(${stageY}px)`,
          boxSizing: 'border-box',
        }}
      >
        {/* Section A: Verified System Guarantees */}
        <div
          style={{
            flex: isWidescreen ? '0 0 54%' : 'none',
            width: '100%',
            backgroundColor: theme.surface,
            borderRadius: '16px',
            border: `1px solid ${!isLimitationActive ? 'rgba(54, 169, 130, 0.35)' : theme.border_subtle}`,
            padding: isWidescreen ? '18px 20px' : '14px 16px',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.7)',
            transition: 'border 0.25s ease',
          }}
        >
          {/* Section Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: `1px solid ${theme.border_subtle}`,
              paddingBottom: '8px',
            }}
          >
            <div
              style={{
                fontSize: '11px',
                fontWeight: 800,
                color: theme.text_muted,
                fontFamily: brand.font_mono,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <ShieldCheckIcon size={13} color={theme.status_success} />
              <span>PRIMARY SYSTEM GUARANTEES</span>
            </div>

            <div
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: theme.status_success,
                fontFamily: brand.font_mono,
              }}
            >
              {guarantees.length} VERIFIED SPECIFICATIONS
            </div>
          </div>

          {/* Guarantee Cards List */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: isWidescreen && guarantees.length >= 2 ? 'repeat(2, 1fr)' : '1fr',
              gap: '12px',
            }}
          >
            {guarantees.map((card, idx) => renderCard(card, idx, false))}
          </div>
        </div>

        {/* Section B: Documented Operational Limitations & Caveats */}
        <div
          style={{
            flex: isWidescreen ? '0 0 46%' : 'none',
            width: '100%',
            backgroundColor: theme.surface,
            borderRadius: '16px',
            border: `1.5px solid ${isLimitationActive ? 'rgba(229, 167, 67, 0.45)' : theme.border_subtle}`,
            padding: isWidescreen ? '18px 20px' : '14px 16px',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            boxShadow: isLimitationActive
              ? '0 20px 40px -10px rgba(0, 0, 0, 0.8), 0 0 24px rgba(229, 167, 67, 0.12)'
              : '0 20px 40px -10px rgba(0, 0, 0, 0.7)',
            transition: 'all 0.25s ease',
          }}
        >
          {/* Section Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: `1px solid ${theme.border_subtle}`,
              paddingBottom: '8px',
            }}
          >
            <div
              style={{
                fontSize: '11px',
                fontWeight: 800,
                color: isLimitationActive ? theme.status_warning : theme.text_muted,
                fontFamily: brand.font_mono,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <AlertIcon size={13} color={isLimitationActive ? theme.status_warning : theme.text_muted} />
              <span>DOCUMENTED OPERATIONAL CONSTRAINTS</span>
            </div>

            <div
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: isLimitationActive ? theme.status_warning : theme.text_disabled,
                fontFamily: brand.font_mono,
              }}
            >
              {isLimitationActive ? 'ACTIVE CAVEAT AUDIT' : `${limitations.length} CONSTRAINTS`}
            </div>
          </div>

          {/* Limitation Cards List */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {limitations.map((card, idx) => renderCard(card, idx + guarantees.length, true))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvidenceBentoScene;
