import React from 'react';
import { OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { MathIcon, SparklesIcon } from './SvgIcons';

/**
 * ManimScene (Phase 14 - Hybrid Manim Community Sub-Renderer Component)
 * Embeds high-precision 3Blue1Brown-style Manim .mp4 clips via <OffthreadVideo>
 * inside the 920x920 canvas while preserving Remotion domain headers and HUD cards.
 */
export const ManimScene = ({
  scene,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const title = scene?.title || 'MATHEMATICAL VISUALIZATION';
  const subtitle = scene?.spoken_text || 'Deterministic mathematical simulation rendered via Manim Community.';
  const subMode = scene?.sub_mode || 'equation_morph';

  const domain = (
    scene?.domain ||
    scene?.subject ||
    scene?.choreography?.domain ||
    'math'
  ).toLowerCase();

  const palette = scene?.choreography?.palette || {
    primary: '#00f2fe',
    secondary: '#10b981',
    accent: '#f59e0b',
    background: '#0b0f19',
    border: 'rgba(0, 242, 254, 0.35)',
    glow: 'rgba(0, 242, 254, 0.20)',
  };

  const layoutDensity = scene?.choreography?.layout_density || scene?.layout_density || 'canvas_spotlight';
  const isSpotlight = layoutDensity === 'canvas_spotlight';
  const stageHeight = isSpotlight ? '1260px' : '1540px';
  const canvasHeight = isSpotlight ? 920 : 800;

  const manimVideoSrc = scene?.manim_video_src;

  const subModeLabel =
    subMode === 'equation_morph'
      ? 'EQUATION MORPH STUDIO'
      : subMode === 'calculus_graph'
      ? 'CALCULUS & RIEMANN INTEGRAL'
      : subMode === 'vector_field'
      ? 'LINEAR TRANSFORMATION & FLOW'
      : subMode === 'quantum_wave'
      ? 'SCHRÖDINGER TUNNELING'
      : 'MANIM CE ENGINE';

  return (
    <div
      style={{
        backgroundColor: palette.background,
        borderRadius: '28px',
        border: `1.5px solid ${palette.border}`,
        boxShadow: `0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 40px ${palette.glow}`,
        width: '960px',
        height: stageHeight,
        minHeight: stageHeight,
        maxHeight: stageHeight,
        overflow: 'hidden',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        position: 'relative',
        padding: '30px 32px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      {/* 1. TOP EDITORIAL HEADER */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          height: '190px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <MathIcon size={28} color={palette.primary} />
            <span
              style={{
                fontSize: '22px',
                fontWeight: 800,
                color: palette.primary,
                fontFamily: 'monospace',
                letterSpacing: '2.5px',
                textTransform: 'uppercase',
              }}
            >
              {domain.toUpperCase()} • MANIM CE PRE-RENDER
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(0, 242, 254, 0.15)',
                border: `1.5px solid ${palette.primary}`,
                color: palette.primary,
                borderRadius: '8px',
                padding: '4px 14px',
                fontSize: '16px',
                fontFamily: 'monospace',
                fontWeight: 900,
              }}
            >
              {subModeLabel}
            </span>
            {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
          </div>
        </div>

        <div>
          <div
            style={{
              fontSize: '46px',
              fontWeight: 900,
              color: '#ffffff',
              fontFamily: 'sans-serif',
              letterSpacing: '-0.5px',
              lineHeight: '1.15',
            }}
          >
            {title}
          </div>
          <div style={{ fontSize: '23px', color: '#94a3b8', marginTop: '4px', fontStyle: 'italic' }}>
            {subtitle}
          </div>
        </div>
      </div>

      {/* 2. CENTER MANIM VIDEO CONTAINER */}
      <div
        style={{
          height: `${canvasHeight}px`,
          backgroundColor: '#0b0f19',
          borderRadius: '22px',
          border: '1.5px solid rgba(0, 242, 254, 0.25)',
          boxShadow: 'inset 0 0 36px rgba(0, 0, 0, 0.85), 0 0 24px rgba(0, 242, 254, 0.12)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'hidden',
          position: 'relative',
          boxSizing: 'border-box',
        }}
      >
        {manimVideoSrc ? (
          <div style={{ position: 'relative', width: '100%', height: '100%' }}>
            <OffthreadVideo
              src={staticFile(manimVideoSrc)}
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                borderRadius: '16px',
              }}
            />
            {/* Top-Right Telemetry HUD Badge */}
            <div
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                backgroundColor: 'rgba(11, 15, 25, 0.85)',
                border: '1px solid #00f2fe',
                color: '#00f2fe',
                borderRadius: '6px',
                padding: '4px 12px',
                fontSize: '13px',
                fontFamily: 'monospace',
                fontWeight: 800,
                letterSpacing: '1px',
                zIndex: 10,
              }}
            >
              MANIM CAIRO ENGINE • 30 FPS
            </div>
            {/* Bottom-Left Phase Tag */}
            <div
              style={{
                position: 'absolute',
                bottom: '16px',
                left: '16px',
                backgroundColor: 'rgba(11, 15, 25, 0.85)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#94a3b8',
                borderRadius: '6px',
                padding: '4px 12px',
                fontSize: '13px',
                fontFamily: 'monospace',
                fontWeight: 700,
                zIndex: 10,
              }}
            >
              DETERMINISTIC PRE-RENDER STAGE 4.5
            </div>
          </div>
        ) : (
          /* Safe SVG Fallback when Manim video src is absent */
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '20px',
              width: '100%',
              height: '100%',
              color: '#ffffff',
              padding: '30px',
              boxSizing: 'border-box',
            }}
          >
            <SparklesIcon size={48} color={palette.primary} />
            <div style={{ fontSize: '36px', fontWeight: 900, fontFamily: 'monospace', color: palette.primary }}>
              {scene?.formula || 'f(x) = y'}
            </div>
            <div style={{ fontSize: '20px', color: '#94a3b8', textAlign: 'center', maxWidth: '700px' }}>
              Native SVG Mathematical Render (Pre-render fallback active)
            </div>
          </div>
        )}
      </div>

      {/* 3. BOTTOM INTUITION / TELEMETRY CARD (Present in full_dashboard layout) */}
      {!isSpotlight && (
        <div
          style={{
            height: '240px',
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '18px',
            border: '1.5px solid rgba(255, 255, 255, 0.08)',
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '18px', fontWeight: 800, color: palette.primary, fontFamily: 'monospace' }}>
              MATHEMATICAL INTUITION & TELEMETRY
            </span>
            <span style={{ fontSize: '14px', color: '#10b981', fontFamily: 'monospace', fontWeight: 700 }}>
              PRECISION VERIFIED
            </span>
          </div>
          <div style={{ fontSize: '22px', color: '#e2e8f0', lineHeight: '1.4' }}>
            {scene?.intuition || 'Mathematical transformations preserve underlying coordinate invariants and topological properties.'}
          </div>
          <div style={{ fontSize: '15px', color: '#64748b', fontFamily: 'monospace' }}>
            COMPOSITOR: REMOTION 1080x1920 • SUB-RENDERER: MANIM 920x920
          </div>
        </div>
      )}
    </div>
  );
};

export default ManimScene;

