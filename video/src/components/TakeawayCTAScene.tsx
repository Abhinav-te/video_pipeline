import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { useBrand } from '../context/BrandContext';
import { SparklesIcon, CodeIcon, CheckIcon } from './SvgIcons';

export interface TakeawayCTASceneProps {
  scene: {
    title?: string;
    display_text?: string;
    cta_url?: string;
    quickstart?: string;
    narration?: string;
    spoken_text?: string;
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

export const TakeawayCTAScene: React.FC<TakeawayCTASceneProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const brand = useBrand();
  const localFrame = Math.max(0, frame - sceneStartFrame);

  const headline = scene?.title || 'Durable Execution Primitives';
  const takeaway = scene?.spoken_text || scene?.narration || 'Wrap operations in step.run() for isolated retries and memoized state recovery.';
  const quickstart = scene?.quickstart || `npm install ${brand.company_name.toLowerCase()}`;
  const docsUrl = scene?.cta_url || brand.docs_url_display || 'inngest.com/docs/step-run';

  const cardOpacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const cardScale = interpolate(localFrame, [0, 10], [0.95, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

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
      {/* Brand Outro Card */}
      <div
        style={{
          width: '100%',
          maxWidth: isWidescreen ? '1100px' : '920px',
          backgroundColor: '#0c0e17',
          borderRadius: '32px',
          border: '2px solid rgba(99, 102, 241, 0.4)',
          boxShadow: '0 40px 80px -20px rgba(0, 0, 0, 0.95), 0 0 40px rgba(99, 102, 241, 0.25)',
          padding: isWidescreen ? '48px 56px' : '40px 32px',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          backdropFilter: 'blur(20px)',
          opacity: cardOpacity,
          transform: `scale(${cardScale})`,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Ambient Top Glow */}
        <div
          style={{
            position: 'absolute',
            top: '-60px',
            width: '360px',
            height: '120px',
            background: 'radial-gradient(ellipse at center, rgba(99, 102, 241, 0.35) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        {/* Brand Badge / Logo */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 24px',
            borderRadius: '999px',
            backgroundColor: 'rgba(99, 102, 241, 0.15)',
            border: '1.5px solid #6366F1',
            color: '#ffffff',
            fontSize: '18px',
            fontWeight: 900,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            fontFamily: brand.font_mono,
            marginBottom: '28px',
            boxShadow: '0 0 24px rgba(99, 102, 241, 0.4)',
          }}
        >
          <SparklesIcon size={18} color="#818cf8" />
          {brand.logo_text}
        </div>

        {/* Core Takeaway Headline */}
        <h1
          style={{
            fontSize: isWidescreen ? '46px' : '48px',
            fontWeight: 900,
            color: '#ffffff',
            lineHeight: 1.15,
            margin: 0,
            marginBottom: '18px',
            letterSpacing: '-0.02em',
          }}
        >
          {headline}
        </h1>

        {/* Supporting Takeaway Summary */}
        <p
          style={{
            fontSize: isWidescreen ? '22px' : '20px',
            color: '#cbd5e1',
            lineHeight: 1.5,
            maxWidth: isWidescreen ? '840px' : '760px',
            margin: 0,
            marginBottom: '36px',
          }}
        >
          {takeaway}
        </p>

        {/* Quickstart Command Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            backgroundColor: '#111320',
            border: '1.5px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '16px',
            padding: '14px 26px',
            marginBottom: '28px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
          }}
        >
          <CodeIcon size={20} color="#60a5fa" />
          <span
            style={{
              fontFamily: brand.font_mono,
              fontSize: isWidescreen ? '20px' : '20px',
              color: '#34d399',
              fontWeight: 700,
            }}
          >
            {quickstart}
          </span>
        </div>

        {/* Prominent Official Documentation Link Pill */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 28px',
            borderRadius: '999px',
            backgroundColor: '#6366F1',
            color: '#ffffff',
            fontSize: isWidescreen ? '18px' : '17px',
            fontWeight: 800,
            fontFamily: brand.font_mono,
            boxShadow: '0 12px 28px -6px rgba(99, 102, 241, 0.6)',
            letterSpacing: '0.02em',
          }}
        >
          <span>Official Docs:</span>
          <span style={{ textDecoration: 'underline', color: '#ffffff' }}>
            {docsUrl}
          </span>
          <CheckIcon size={18} color="#ffffff" />
        </div>
      </div>
    </div>
  );
};

export default TakeawayCTAScene;

