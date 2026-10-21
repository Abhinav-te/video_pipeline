import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { useBrand } from '../context/BrandContext';
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
    items?: BentoCardItem[];
    cards?: BentoCardItem[];
    metrics?: BentoCardItem[];
    evidence_ids?: string[];
    badge?: { text?: string };
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

export const EvidenceBentoScene: React.FC<EvidenceBentoSceneProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const brand = useBrand();
  const localFrame = Math.max(0, frame - sceneStartFrame);

  // Cards strictly populated from props (items, cards, or metrics)
  const cards: BentoCardItem[] = scene?.items || scene?.cards || scene?.metrics || [];
  if (cards.length === 0) {
    throw new Error(
      `[EvidenceBentoScene] Validation Error: 'items', 'cards', or 'metrics' array is required and must not be empty. Scene: "${scene?.title || 'untitled'}"`
    );
  }

  // Validate every card has required data (Zero fake assurance labels)
  cards.forEach((card, idx) => {
    const val = card.value || card.metric;
    const title = card.title;
    if (!val || !title) {
      throw new Error(
        `[EvidenceBentoScene] Validation Error: Card ${idx + 1} is missing required 'title' or 'value'/'metric'. Found title=${title}, value=${val}`
      );
    }
  });

  const headline = scene?.title || 'System Verification';

  const cardColors = [
    { text: '#34d399', bg: 'rgba(52, 211, 153, 0.12)', border: 'rgba(52, 211, 153, 0.35)' },
    { text: '#38bdf8', bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56, 189, 248, 0.35)' },
    { text: '#fbbf24', bg: 'rgba(251, 191, 36, 0.12)', border: 'rgba(251, 191, 36, 0.35)' },
    { text: '#c084fc', bg: 'rgba(192, 132, 252, 0.12)', border: 'rgba(192, 132, 252, 0.35)' },
  ];

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
      {/* Editorial Header Badge if present in scene */}
      {scene?.badge?.text ? (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 16px',
            borderRadius: '999px',
            backgroundColor: 'rgba(99, 102, 241, 0.12)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            color: '#818cf8',
            fontSize: '18px',
            fontWeight: 700,
            fontFamily: brand.font_mono,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '14px',
          }}
        >
          <SparklesIcon size={16} color="#818cf8" />
          {scene.badge.text}
        </div>
      ) : null}

      <h1
        style={{
          fontSize: isWidescreen ? '42px' : '44px',
          fontWeight: 900,
          color: '#ffffff',
          textAlign: 'center',
          lineHeight: 1.2,
          margin: 0,
          marginBottom: isWidescreen ? '36px' : '40px',
          maxWidth: isWidescreen ? '1200px' : '900px',
        }}
      >
        {headline}
      </h1>

      {/* Responsive Bento Grid */}
      <div
        style={{
          width: '100%',
          maxWidth: isWidescreen ? '1440px' : '920px',
          display: 'grid',
          gridTemplateColumns: isWidescreen ? `repeat(${Math.min(cards.length, 3)}, 1fr)` : '1fr',
          gap: isWidescreen ? '28px' : '20px',
        }}
      >
        {cards.map((card, idx) => {
          const c = cardColors[idx % cardColors.length];
          const delay = idx * 6;
          const cardOpacity = interpolate(localFrame, [delay, delay + 8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const cardY = interpolate(localFrame, [delay, delay + 8], [15, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

          const val = card.value || card.metric || '';
          const title = card.title || '';
          const subtitle = card.subtitle || card.description || '';
          const tag = card.tag || (card.evidence_id ? `#${card.evidence_id}` : undefined);

          return (
            <div
              key={idx}
              style={{
                backgroundColor: 'rgba(17, 19, 28, 0.9)',
                borderRadius: '24px',
                border: `1.5px solid ${c.border}`,
                boxShadow: `0 20px 40px -12px rgba(0, 0, 0, 0.8), 0 0 24px ${c.bg}`,
                padding: isWidescreen ? '32px 28px' : '28px 24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                backdropFilter: 'blur(16px)',
                opacity: cardOpacity,
                transform: `translateY(${cardY}px)`,
                minHeight: isWidescreen ? '240px' : 'auto',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '4px',
                  backgroundColor: c.text,
                }}
              />

              {/* Tag / Badge */}
              {tag ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <span
                    style={{
                      fontSize: '18px',
                      fontWeight: 800,
                      color: c.text,
                      fontFamily: brand.font_mono,
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      backgroundColor: c.bg,
                      border: `1px solid ${c.border}`,
                    }}
                  >
                    {tag}
                  </span>

                  <CheckIcon size={18} color={c.text} />
                </div>
              ) : null}

              {/* Big Bold Stat / Metric */}
              <div
                style={{
                  fontSize: isWidescreen ? '44px' : '46px',
                  fontWeight: 900,
                  color: '#ffffff',
                  fontFamily: brand.font_mono,
                  letterSpacing: '-0.02em',
                  marginBottom: '10px',
                  lineHeight: 1,
                  textShadow: `0 0 24px ${c.text}55`,
                }}
              >
                {val}
              </div>

              {/* Title & Subtitle */}
              <div>
                <div
                  style={{
                    fontSize: isWidescreen ? '32px' : '28px',
                    fontWeight: 800,
                    color: '#f8fafc',
                    marginBottom: '6px',
                  }}
                >
                  {title}
                </div>
                {subtitle ? (
                  <div
                    style={{
                      fontSize: isWidescreen ? '24px' : '20px',
                      color: '#94a3b8',
                      lineHeight: 1.45,
                    }}
                  >
                    {subtitle}
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
