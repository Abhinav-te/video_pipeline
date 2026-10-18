import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { DynamicBadgeIcon, SparklesIcon, WarningIcon, LightningIcon, ScaleIcon } from './SvgIcons';

export const resolveConceptMode = (scene) => {
  const spokenLower = (scene?.spoken_text || scene?.narration || '').toLowerCase();
  const titleLower = (scene?.title || scene?.display_text || '').toLowerCase();
  const textContext = `${spokenLower} ${titleLower}`;

  if (scene?.concept_mode) return scene.concept_mode;
  if (scene?.diagram_mode) return scene.diagram_mode;

  if (
    textContext.includes('non-convex') ||
    textContext.includes('non convex') ||
    textContext.includes('break') ||
    textContext.includes('moon') ||
    textContext.includes('linear cut') ||
    textContext.includes('curved') ||
    (textContext.includes('k-means') && textContext.includes('fail')) ||
    textContext.includes('arena') ||
    textContext.includes('voronoi')
  ) {
    return 'arena';
  }

  if (
    textContext.includes('compute') ||
    textContext.includes('waste') ||
    textContext.includes('gpu') ||
    textContext.includes('vram') ||
    textContext.includes('latency') ||
    textContext.includes('hardware') ||
    textContext.includes('cost') ||
    textContext.includes('hours') ||
    textContext.includes('benchmark')
  ) {
    return 'benchmark';
  }

  if (
    textContext.includes('autoencoder') ||
    textContext.includes('auto-encoder') ||
    textContext.includes('latent space') ||
    textContext.includes('bottleneck layer') ||
    textContext.includes('reconstruction loss')
  ) {
    return 'autoencoder';
  }

  return 'concept_card';
};

/**
 * ConceptHeroScene (Phase 6 & 7 Data-Driven Diagrams & Split Comparisons)
 * Full-Screen 3-Part Vertical Stack (1540px Stage Height):
 *   1. Top Hero Title Card (260px tall) with SVG icon badge & 52px bold headline
 *   2. Center Context-Driven Visual Diagram (780px tall):
 *        • Head-to-Head Split Arena: K-Means linear failure vs Manifold density victory on non-convex shapes
 *        • Compute & Latency Benchmark Comparison: GPU VRAM, O(n²) vs O(n log n), Latency bars
 *        • Data-Driven Multi-Stage Concept Card / Flow Pipeline: 100% dynamic for any STEM domain
 *        • Autoencoder Latent Space Manifold: only when autoencoder explicitly mentioned
 *   3. Bottom 3 Key Takeaway Pills (420px tall) revealing sequentially across the scene duration
 */
export const ConceptHeroScene = ({
  scene,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const displayText = scene?.display_text || scene?.title || 'Core Architecture Insight';
  const icon = scene?.icon || scene?.badge?.icon || 'bulb';

  // Deterministically select diagram mode based on scene context
  const conceptMode = resolveConceptMode(scene);

  const arenaDefaultPoints = [
    'K-Means assumes spherical clusters and Euclidean convex geometry',
    'Density-based clustering links contiguous points regardless of curvature',
    'Non-linear manifolds require geodesic or density connectivity',
  ];

  const benchmarkDefaultPoints = [
    'Avoid burning GPU hours where classical algorithms converge in milliseconds',
    'Memory footprint drops from gigabytes to single megabytes',
    'Instant cold-start with zero heavy model weights to download or initialize',
  ];

  const autoencoderDefaultPoints = [
    'Compresses high-dimensional noise into low-dimensional manifold',
    'Bottleneck layer forces network to extract semantic invariant features',
    'Reconstruction loss guarantees zero information loss on key signals',
  ];

  const conceptCardDefaultPoints = [
    scene?.title ? `Mastering ${scene.title} core guarantees` : 'Deterministic execution with zero redundant operations',
    'Invariant state transitions enforce optimal runtime complexity',
    'Proven production foundation maximizing performance and correctness',
  ];

  const defaultPoints = conceptMode === 'arena'
    ? arenaDefaultPoints
    : (conceptMode === 'benchmark'
        ? benchmarkDefaultPoints
        : (conceptMode === 'autoencoder' ? autoencoderDefaultPoints : conceptCardDefaultPoints));

  const points = (scene?.points && scene.points.length > 0)
    ? scene.points
    : (scene?.bullets && scene.bullets.length > 0
        ? scene.bullets
        : (scene?.takeaways && scene.takeaways.length > 0 ? scene.takeaways : defaultPoints));
  // points.map progressive reveals for key takeaways

  // Pulse animation for latent bottleneck and architecture signal lines
  const pulse = 1 + Math.sin(frame * 0.12) * 0.1;
  const signalOffset = (frame * 12) % 360;

  return (
    <div
      style={{
        width: '960px',
        height: '1540px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        position: 'relative',
        margin: '0 auto',
      }}
    >
      {/* 1. TOP HERO TITLE CARD (260px tall) */}
      <div
        style={{
          height: '260px',
          backgroundColor: '#111724',
          borderRadius: '24px',
          border: '1.5px solid rgba(245, 158, 11, 0.3)',
          boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.8), 0 0 24px rgba(245, 158, 11, 0.14)',
          padding: '24px 36px',
          display: 'flex',
          alignItems: 'center',
          gap: '28px',
          boxSizing: 'border-box',
          transform: 'none',
        }}
      >
        {/* Animated Hero SVG Icon Badge */}
        <div
          style={{
            width: '90px',
            height: '90px',
            borderRadius: '50%',
            backgroundColor: 'rgba(245, 158, 11, 0.16)',
            border: '2px solid rgba(245, 158, 11, 0.6)',
            boxShadow: '0 0 24px rgba(245, 158, 11, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <DynamicBadgeIcon icon={icon} size={48} color="#f59e0b" />
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span
              style={{
                fontSize: '22px',
                fontWeight: 900,
                color: '#f59e0b',
                letterSpacing: '3px',
                textTransform: 'uppercase',
                fontFamily: 'monospace',
              }}
            >
              CORE CONCEPT ARCHITECTURE
            </span>
            {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
          </div>

          <h1
            style={{
              fontSize: '48px',
              fontWeight: 900,
              color: '#f8fafc',
              lineHeight: 1.15,
              margin: 0,
              letterSpacing: '-0.5px',
            }}
          >
            {displayText}
          </h1>
        </div>
      </div>

      {/* 2. CENTER ANIMATED VISUAL DIAGRAM (780px tall) */}
      <div
        style={{
          height: '780px',
          backgroundColor: '#0a0e17',
          borderRadius: '24px',
          border: '1.5px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.85)',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxSizing: 'border-box',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Diagram Eyebrow Header */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            paddingBottom: '12px',
          }}
        >
          <span style={{ fontSize: '24px', fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace' }}>
            {conceptMode === 'arena'
              ? 'Head-to-Head Split Arena: Non-Convex Benchmark'
              : (conceptMode === 'benchmark'
                  ? 'Compute Efficiency & Latency Benchmark'
                  : (conceptMode === 'autoencoder'
                      ? 'Autoencoder Latent Bottleneck Manifold'
                      : (scene?.diagram_title || scene?.title || 'System Architectural Pipeline')))}
          </span>
          <span
            style={{
              backgroundColor: conceptMode === 'arena'
                ? 'rgba(239, 68, 68, 0.16)'
                : (conceptMode === 'concept_card' ? 'rgba(16, 185, 129, 0.16)' : 'rgba(56, 189, 248, 0.16)'),
              border: `1px solid ${conceptMode === 'arena'
                ? '#ef4444'
                : (conceptMode === 'concept_card' ? '#10b981' : '#38bdf8')}`,
              color: conceptMode === 'arena'
                ? '#f87171'
                : (conceptMode === 'concept_card' ? '#34d399' : '#38bdf8'),
              padding: '4px 14px',
              borderRadius: '8px',
              fontSize: '18px',
              fontWeight: 800,
              fontFamily: 'monospace',
            }}
          >
            {conceptMode === 'arena'
              ? 'MANIFOLD VS VORONOI'
              : (conceptMode === 'benchmark'
                  ? '375× HARDWARE SPEEDUP'
                  : (conceptMode === 'autoencoder' ? '8× COMPRESSION RATIO' : 'GUARANTEED INVARIANT'))}
          </span>
        </div>

        {/* MODE A: HEAD-TO-HEAD SPLIT ARENA (Non-Convex Failure vs Density Victory) */}
        // Contract: Left: ❌ Fails on Non-Convex: 54% Acc | Right: ✅ Captures Geometry: 99% Acc
        {conceptMode === 'arena' && (
          <div
            style={{
              width: '100%',
              height: '660px',
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '20px',
              boxSizing: 'border-box',
              padding: '12px 0',
            }}
          >
            {/* Left Arena: K-Means Rigid Cut Failure */}
            <div
              style={{
                backgroundColor: '#1b0c13',
                borderRadius: '18px',
                border: '1.5px solid rgba(255, 123, 114, 0.5)',
                boxShadow: '0 12px 32px rgba(0,0,0,0.6)',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxSizing: 'border-box',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <WarningIcon size={24} color="#ff7b72" />
                  <span style={{ fontSize: '22px', fontWeight: 800, color: '#ff7b72', fontFamily: 'monospace' }}>
                    K-MEANS VORONOI
                  </span>
                </div>
                <span
                  style={{
                    backgroundColor: 'rgba(255, 123, 114, 0.2)',
                    border: '1px solid #ff7b72',
                    color: '#ff7b72',
                    padding: '2px 8px',
                    borderRadius: '6px',
                    fontSize: '15px',
                    fontWeight: 'bold',
                    fontFamily: 'monospace',
                  }}
                >
                  54% ACC • FAILS
                </span>
              </div>

              {/* SVG Moon Crescent with Harsh Linear Cut */}
              <svg width="400" height="380" viewBox="0 0 400 380" style={{ overflow: 'visible', margin: '0 auto' }}>
                {/* Rigid Voronoi Cut Line */}
                <line x1="200" y1="30" x2="200" y2="350" stroke="#ff7b72" strokeWidth="3" strokeDasharray="6 4" />
                <text x="210" y="50" fill="#ff7b72" fontSize="16" fontFamily="monospace" fontWeight="bold">
                  Linear Voronoi Cut
                </text>

                {/* Upper Moon Arc (Arbitrarily split left/right) */}
                {[
                  { x: 80, y: 160 }, { x: 110, y: 120 }, { x: 150, y: 90 }, { x: 190, y: 80 },
                  { x: 230, y: 85 }, { x: 270, y: 105 }, { x: 310, y: 140 }, { x: 330, y: 180 },
                ].map((pt, i) => (
                  <circle
                    key={`m1-${i}`}
                    cx={pt.x}
                    cy={pt.y}
                    r="10"
                    fill={pt.x < 200 ? '#f59e0b' : '#38bdf8'}
                    stroke="#ffffff"
                    strokeWidth="1.5"
                  />
                ))}

                {/* Lower Interlocking Moon Arc (Arbitrarily split left/right) */}
                {[
                  { x: 140, y: 220 }, { x: 170, y: 260 }, { x: 210, y: 285 }, { x: 250, y: 290 },
                  { x: 290, y: 280 }, { x: 320, y: 250 }, { x: 340, y: 210 },
                ].map((pt, i) => (
                  <circle
                    key={`m2-${i}`}
                    cx={pt.x}
                    cy={pt.y}
                    r="10"
                    fill={pt.x < 200 ? '#f59e0b' : '#38bdf8'}
                    stroke="#ffffff"
                    strokeWidth="1.5"
                  />
                ))}
              </svg>

              <div
                style={{
                  padding: '10px 14px',
                  backgroundColor: 'rgba(255, 123, 114, 0.12)',
                  borderRadius: '10px',
                  border: '1px solid rgba(255, 123, 114, 0.3)',
                  fontSize: '18px',
                  color: '#ff7b72',
                  fontWeight: 600,
                  fontFamily: 'monospace',
                  textAlign: 'center',
                }}
              >
                Fails on Non-Convex: 54% Acc
              </div>
            </div>

            {/* Right Arena: Density Manifold Captures Geometry */}
            <div
              style={{
                backgroundColor: '#0a1d13',
                borderRadius: '18px',
                border: '1.5px solid rgba(63, 185, 80, 0.6)',
                boxShadow: '0 12px 32px rgba(0,0,0,0.6), 0 0 24px rgba(63, 185, 80, 0.15)',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxSizing: 'border-box',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <SparklesIcon size={24} color="#3fb950" />
                  <span style={{ fontSize: '22px', fontWeight: 800, color: '#3fb950', fontFamily: 'monospace' }}>
                    DENSITY / MANIFOLD
                  </span>
                </div>
                <span
                  style={{
                    backgroundColor: 'rgba(63, 185, 80, 0.2)',
                    border: '1px solid #3fb950',
                    color: '#3fb950',
                    padding: '2px 8px',
                    borderRadius: '6px',
                    fontSize: '15px',
                    fontWeight: 'bold',
                    fontFamily: 'monospace',
                  }}
                >
                  99% ACC • VICTORY
                </span>
              </div>

              {/* SVG Moon Crescent Tracing Manifold Curvature */}
              <svg width="400" height="380" viewBox="0 0 400 380" style={{ overflow: 'visible', margin: '0 auto' }}>
                {/* Flowing Manifold Arc 1 Path */}
                <path
                  d="M 80,160 Q 190,40 330,180"
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="3.5"
                  opacity="0.8"
                />
                {[
                  { x: 80, y: 160 }, { x: 110, y: 120 }, { x: 150, y: 90 }, { x: 190, y: 80 },
                  { x: 230, y: 85 }, { x: 270, y: 105 }, { x: 310, y: 140 }, { x: 330, y: 180 },
                ].map((pt, i) => (
                  <circle
                    key={`m1d-${i}`}
                    cx={pt.x}
                    cy={pt.y}
                    r="10"
                    fill="#f59e0b"
                    stroke="#ffffff"
                    strokeWidth="2"
                  />
                ))}

                {/* Flowing Manifold Arc 2 Path */}
                <path
                  d="M 140,220 Q 250,330 340,210"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="3.5"
                  opacity="0.8"
                />
                {[
                  { x: 140, y: 220 }, { x: 170, y: 260 }, { x: 210, y: 285 }, { x: 250, y: 290 },
                  { x: 290, y: 280 }, { x: 320, y: 250 }, { x: 340, y: 210 },
                ].map((pt, i) => (
                  <circle
                    key={`m2d-${i}`}
                    cx={pt.x}
                    cy={pt.y}
                    r="10"
                    fill="#38bdf8"
                    stroke="#ffffff"
                    strokeWidth="2"
                  />
                ))}
              </svg>

              <div
                style={{
                  padding: '10px 14px',
                  backgroundColor: 'rgba(63, 185, 80, 0.14)',
                  borderRadius: '10px',
                  border: '1px solid rgba(63, 185, 80, 0.4)',
                  fontSize: '18px',
                  color: '#3fb950',
                  fontWeight: 600,
                  fontFamily: 'monospace',
                  textAlign: 'center',
                }}
              >
                Captures Geometry: 99% Acc
              </div>
            </div>
          </div>
        )}

        {/* MODE B: COMPUTE & LATENCY BENCHMARK COMPARISON */}
        {conceptMode === 'benchmark' && (
          <div
            style={{
              width: '100%',
              height: '660px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-around',
              boxSizing: 'border-box',
              padding: '16px 20px',
            }}
          >
            {/* Metric 1: Hardware Memory & VRAM */}
            <div
              style={{
                backgroundColor: '#111726',
                borderRadius: '18px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '22px', fontWeight: 'bold', color: '#f8fafc', fontFamily: 'monospace' }}>
                  HARDWARE MEMORY & VRAM FOOTPRINT
                </span>
                <span style={{ color: '#10b981', fontWeight: 'bold', fontSize: '18px', fontFamily: 'monospace' }}>
                  1,300× REDUCTION
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', color: '#ff7b72', fontFamily: 'monospace' }}>
                  <span>Massive Deep Net</span>
                  <span>GPU VRAM: 14.2 GB</span>
                </div>
                <div style={{ width: '100%', height: '14px', backgroundColor: '#1e293b', borderRadius: '7px', overflow: 'hidden' }}>
                  <div style={{ width: '92%', height: '100%', backgroundColor: '#ff7b72', borderRadius: '7px' }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', color: '#10b981', fontFamily: 'monospace' }}>
                  <span>Classical Clustering</span>
                  <span>CPU MEMORY: 38 MB</span>
                </div>
                <div style={{ width: '100%', height: '14px', backgroundColor: '#1e293b', borderRadius: '7px', overflow: 'hidden' }}>
                  <div style={{ width: '7%', height: '100%', backgroundColor: '#10b981', borderRadius: '7px' }} />
                </div>
              </div>
            </div>

            {/* Metric 2: Time Complexity Scaling */}
            <div
              style={{
                backgroundColor: '#111726',
                borderRadius: '18px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '22px', fontWeight: 'bold', color: '#f8fafc', fontFamily: 'monospace' }}>
                  TIME COMPLEXITY SCALING (N = 100,000)
                </span>
                <span style={{ color: '#38bdf8', fontWeight: 'bold', fontSize: '18px', fontFamily: 'monospace' }}>
                  350× SPEEDUP
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', color: '#f59e0b', fontFamily: 'monospace' }}>
                  <span>Naive Quadratic O(n²)</span>
                  <span>840 ms / batch</span>
                </div>
                <div style={{ width: '100%', height: '14px', backgroundColor: '#1e293b', borderRadius: '7px', overflow: 'hidden' }}>
                  <div style={{ width: '85%', height: '100%', backgroundColor: '#f59e0b', borderRadius: '7px' }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', color: '#38bdf8', fontFamily: 'monospace' }}>
                  <span>Spatial Indexed O(n log n)</span>
                  <span>2.4 ms / batch</span>
                </div>
                <div style={{ width: '100%', height: '14px', backgroundColor: '#1e293b', borderRadius: '7px', overflow: 'hidden' }}>
                  <div style={{ width: '9%', height: '100%', backgroundColor: '#38bdf8', borderRadius: '7px' }} />
                </div>
              </div>
            </div>

            {/* Metric 3: Latency & Cold Start */}
            <div
              style={{
                backgroundColor: '#111726',
                borderRadius: '18px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '22px', fontWeight: 'bold', color: '#f8fafc', fontFamily: 'monospace' }}>
                  THROUGHPUT & COLD-START INFERENCE
                </span>
                <span style={{ color: '#10b981', fontWeight: 'bold', fontSize: '18px', fontFamily: 'monospace' }}>
                  INSTANT BOOT
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '20px', fontFamily: 'monospace' }}>
                <div style={{ color: '#94a3b8' }}>
                  Deep Net: <b style={{ color: '#ff7b72' }}>12 req/sec</b> (4.8s load)
                </div>
                <div style={{ color: '#94a3b8' }}>
                  Deterministic: <b style={{ color: '#10b981' }}>4,500 req/sec</b> (0.001s load)
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MODE C: AUTOENCODER LATENT SPACE MANIFOLD */}
        {conceptMode === 'autoencoder' && (
          <svg width="910" height="660" viewBox="0 0 910 660" style={{ overflow: 'visible' }}>
            {/* Subtle Grid Backing */}
            <line x1="40" y1="160" x2="870" y2="160" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
            <line x1="40" y1="330" x2="870" y2="330" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
            <line x1="40" y1="500" x2="870" y2="500" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />

            {/* 1. INPUT LAYER (x: 120) */}
            <g transform="translate(100, 100)">
              <rect x="-30" y="-30" width="100" height="480" rx="16" fill="#141820" stroke="rgba(56, 189, 248, 0.35)" strokeWidth="2" />
              <text x="20" y="-45" textAnchor="middle" fill="#38bdf8" fontSize="24" fontWeight="bold" fontFamily="monospace">
                INPUT X
              </text>
              <text x="20" y="475" textAnchor="middle" fill="#64748b" fontSize="18" fontFamily="monospace">
                784 dims
              </text>
              {[0, 60, 120, 180, 240, 300, 360, 420].map((y, idx) => (
                <circle key={idx} cx="20" cy={y} r="14" fill="#38bdf8" />
              ))}
            </g>

            {/* ENCODER CONE (Trapezoid from x: 190 to x: 420) */}
            <polygon
              points="190,70 190,550 420,400 420,220"
              fill="rgba(56, 189, 248, 0.05)"
              stroke="rgba(56, 189, 248, 0.3)"
              strokeWidth="2"
              strokeDasharray="6 4"
            />
            <text x="290" y="325" fill="#38bdf8" fontSize="26" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
              ENCODER
            </text>

            {/* Signal Stream Particles Traveling Left to Right */}
            {[140, 220, 300, 380].map((y, i) => (
              <line
                key={i}
                x1={190 + (signalOffset % 230)}
                y1={y}
                x2={230 + (signalOffset % 230)}
                y2={y}
                stroke="#ffd633"
                strokeWidth="4"
                strokeLinecap="round"
                opacity="0.85"
              />
            ))}

            {/* 2. LATENT BOTTLENECK SPACE Z (x: 455) */}
            <g transform={`translate(455, 310) scale(${pulse}) translate(-455, -310)`}>
              <rect
                x="400"
                y="180"
                width="110"
                height="260"
                rx="20"
                fill="#1e1810"
                stroke="#f59e0b"
                strokeWidth="3.5"
              />
              <text x="455" y="145" textAnchor="middle" fill="#f59e0b" fontSize="26" fontWeight="900" fontFamily="monospace">
                LATENT Z
              </text>
              <text x="455" y="475" textAnchor="middle" fill="#f59e0b" fontSize="20" fontWeight="bold" fontFamily="monospace">
                32 dims
              </text>
              {[230, 290, 350, 410].map((y, idx) => (
                <circle
                  key={idx}
                  cx="455"
                  cy={y}
                  r="16"
                  fill="#f59e0b"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              ))}
            </g>

            {/* DECODER CONE (Trapezoid from x: 490 to x: 720) */}
            <polygon
              points="490,220 490,400 720,550 720,70"
              fill="rgba(16, 185, 129, 0.05)"
              stroke="rgba(16, 185, 129, 0.3)"
              strokeWidth="2"
              strokeDasharray="6 4"
            />
            <text x="610" y="325" fill="#10b981" fontSize="26" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
              DECODER
            </text>

            {/* 3. OUTPUT RECONSTRUCTION X_HAT (x: 750) */}
            <g transform="translate(730, 100)">
              <rect x="-30" y="-30" width="100" height="480" rx="16" fill="#141820" stroke="rgba(16, 185, 129, 0.35)" strokeWidth="2" />
              <text x="20" y="-45" textAnchor="middle" fill="#10b981" fontSize="24" fontWeight="bold" fontFamily="monospace">
                RECON X̂
              </text>
              <text x="20" y="475" textAnchor="middle" fill="#64748b" fontSize="18" fontFamily="monospace">
                Loss: 0.014
              </text>
              {[0, 60, 120, 180, 240, 300, 360, 420].map((y, idx) => (
                <circle key={idx} cx="20" cy={y} r="14" fill="#10b981" />
              ))}
            </g>
          </svg>
        )}

        {/* MODE D: 100% DATA-DRIVEN CONCEPT CARD & SPLIT COMPARISON */}
        {conceptMode === 'concept_card' && (
          <div
            style={{
              width: '100%',
              height: '660px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              padding: '12px 0',
            }}
          >
            {/* If comparison_sides provided, render Split Arena */}
            {scene?.comparison_sides ? (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '20px',
                }}
              >
                {/* Left Side */}
                <div
                  style={{
                    backgroundColor: '#16131c',
                    borderRadius: '18px',
                    border: '1.5px solid rgba(248, 113, 113, 0.4)',
                    boxShadow: '0 12px 32px rgba(0,0,0,0.6)',
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <span style={{ fontSize: '18px', fontWeight: 800, color: '#f87171', fontFamily: 'monospace' }}>
                      {scene.comparison_sides.left?.tag || 'BASELINE / CONVENTIONAL'}
                    </span>
                    <h3 style={{ fontSize: '28px', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                      {scene.comparison_sides.left?.title || 'Standard Implementation'}
                    </h3>
                    <p style={{ fontSize: '20px', color: '#94a3b8', lineHeight: 1.4, margin: '8px 0 0' }}>
                      {scene.comparison_sides.left?.detail || 'High computational latency with unbounded memory scaling.'}
                    </p>
                  </div>
                  <div
                    style={{
                      padding: '12px',
                      backgroundColor: 'rgba(248, 113, 113, 0.1)',
                      border: '1px solid rgba(248, 113, 113, 0.3)',
                      borderRadius: '12px',
                      fontSize: '18px',
                      color: '#f87171',
                      fontFamily: 'monospace',
                      fontWeight: 700,
                      textAlign: 'center',
                    }}
                  >
                    {scene.comparison_sides.left?.metric || 'O(n²) COMPLEXITY'}
                  </div>
                </div>

                {/* Right Side */}
                <div
                  style={{
                    backgroundColor: '#0d1f18',
                    borderRadius: '18px',
                    border: '1.5px solid rgba(52, 211, 153, 0.6)',
                    boxShadow: '0 12px 32px rgba(0,0,0,0.6), 0 0 24px rgba(52, 211, 153, 0.2)',
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <span style={{ fontSize: '18px', fontWeight: 800, color: '#34d399', fontFamily: 'monospace' }}>
                      {scene.comparison_sides.right?.tag || 'OPTIMAL / INVARIANT'}
                    </span>
                    <h3 style={{ fontSize: '28px', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                      {scene.comparison_sides.right?.title || (scene.title || 'Guaranteed Architecture')}
                    </h3>
                    <p style={{ fontSize: '20px', color: '#94a3b8', lineHeight: 1.4, margin: '8px 0 0' }}>
                      {scene.comparison_sides.right?.detail || 'Deterministic convergence with constant bounded memory overhead.'}
                    </p>
                  </div>
                  <div
                    style={{
                      padding: '12px',
                      backgroundColor: 'rgba(52, 211, 153, 0.12)',
                      border: '1px solid rgba(52, 211, 153, 0.4)',
                      borderRadius: '12px',
                      fontSize: '18px',
                      color: '#34d399',
                      fontFamily: 'monospace',
                      fontWeight: 700,
                      textAlign: 'center',
                    }}
                  >
                    {scene.comparison_sides.right?.metric || 'O(n log n) GUARANTEE'}
                  </div>
                </div>
              </div>
            ) : (
              /* Dynamic Multi-Stage Flow Diagram */
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '16px',
                }}
              >
                {(scene?.concept_nodes && scene.concept_nodes.length > 0 ? scene.concept_nodes : [
                  { id: 'node_1', tag: 'INPUT / VECTOR', label: scene?.title ? `${scene.title} Feature Space` : 'Raw Input Vector', detail: 'Bounded feature distribution and topological boundary' },
                  { id: 'node_2', tag: 'KERNEL / MECHANISM', label: 'Deterministic Invariant Transform', detail: 'Mathematical reduction enforcing zero redundant state transitions' },
                  { id: 'node_3', tag: 'OUTPUT / CONVERGENCE', label: 'Guaranteed Optimal State', detail: 'Sub-millisecond latency with verified structural correctness' },
                ]).slice(0, 3).map((node, nIdx) => {
                  const nodeColors = ['#f59e0b', '#38bdf8', '#10b981'];
                  const c = nodeColors[nIdx % nodeColors.length];
                  return (
                    <div
                      key={node.id || nIdx}
                      style={{
                        flex: 1,
                        backgroundColor: '#111726',
                        borderRadius: '16px',
                        border: `1.5px solid ${c}55`,
                        boxShadow: `0 8px 24px rgba(0,0,0,0.4), 0 0 16px ${c}22`,
                        padding: '18px 24px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '20px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                        <div
                          style={{
                            width: '54px',
                            height: '54px',
                            borderRadius: '14px',
                            backgroundColor: `${c}22`,
                            border: `2px solid ${c}`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '22px',
                            fontWeight: 900,
                            color: c,
                            fontFamily: 'monospace',
                            flexShrink: 0,
                          }}
                        >
                          0{nIdx + 1}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <span style={{ fontSize: '16px', fontWeight: 800, color: c, fontFamily: 'monospace', letterSpacing: '1px' }}>
                            {node.tag || `STAGE 0${nIdx + 1}`}
                          </span>
                          <span style={{ fontSize: '26px', fontWeight: 800, color: '#f8fafc' }}>
                            {node.label}
                          </span>
                          <span style={{ fontSize: '18px', color: '#94a3b8', lineHeight: 1.25 }}>
                            {node.detail}
                          </span>
                        </div>
                      </div>
                      <div
                        style={{
                          backgroundColor: `${c}16`,
                          border: `1px solid ${c}66`,
                          color: c,
                          padding: '6px 14px',
                          borderRadius: '8px',
                          fontSize: '16px',
                          fontWeight: 700,
                          fontFamily: 'monospace',
                          whiteSpace: 'nowrap',
                          flexShrink: 0,
                        }}
                      >
                        {nIdx === 0 ? 'ENTRY' : (nIdx === 1 ? 'PROCESSING' : 'VERIFIED')}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. BOTTOM 3 KEY TAKEAWAY PILLS (420px tall) */}
      <div
        style={{
          height: '420px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '14px',
          boxSizing: 'border-box',
        }}
      >
        {points.slice(0, 3).map((pt, idx) => {
          const ptStart = sceneStartFrame + 6 + idx * 8;
          const isRevealed = frame >= ptStart;
          const colors = ['#f59e0b', '#38bdf8', '#10b981'];
          const activeColor = colors[idx % colors.length];

          return (
            <div
              key={idx}
              style={{
                height: '124px',
                backgroundColor: isRevealed ? '#141824' : '#0d1117',
                border: isRevealed ? `1.5px solid ${activeColor}` : '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: isRevealed ? `0 8px 24px rgba(0, 0, 0, 0.6), 0 0 16px ${activeColor}33` : 'none',
                borderRadius: '18px',
                padding: '20px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: '20px',
                boxSizing: 'border-box',
                opacity: isRevealed ? 1 : 0.4,
                transition: 'all 0.2s ease',
              }}
            >
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '12px',
                  backgroundColor: `${activeColor}22`,
                  border: `1.5px solid ${activeColor}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px',
                  fontWeight: 900,
                  color: activeColor,
                  fontFamily: 'monospace',
                  flexShrink: 0,
                }}
              >
                0{idx + 1}
              </div>

              <div
                style={{
                  fontSize: '24px',
                  color: isRevealed ? '#f8fafc' : '#94a3b8',
                  fontWeight: 600,
                  lineHeight: 1.3,
                  transform: 'none',
                }}
              >
                {pt}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ConceptHeroScene;
