import React from 'react';
import { OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { QuantumIcon, SparklesIcon, LightningIcon, ScaleIcon } from './SvgIcons';

/**
 * QuantumScene (Engine 1 - Quantum Physics & Relativistic Mechanics)
 *
 * Viewport Breathing:
 *   - 'compact_punch': ~55% height (centered, maxHeight: 960px)
 *   - 'canvas_spotlight': ~72% height (1260px tall) - expands simulation canvas to 920x940
 *   - 'full_dashboard': ~88% height (1540px tall) - full 3-tier layout with live telemetry
 *
 * 3 Distinct Sub-Modes:
 *   1. 'schrodinger_tunneling': Time-Dependent Schrödinger Wavepacket & Barrier Tunneling
 *   2. 'heisenberg_uncertainty': Wavepacket Reciprocal Squeeze (Δx · Δp ≥ ℏ/2)
 *   3. 'dirac_atomic_orbitals': Relativistic Dirac Spinor & Orbitals (1s, 2p_z, 3d_x²-y²)
 */
export const QuantumScene = ({
  scene,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const layoutDensity = scene?.choreography?.layout_density || scene?.layout_density || 'canvas_spotlight';
  const isSpotlight = layoutDensity === 'canvas_spotlight';
  const isCompact = layoutDensity === 'compact_punch';

  const rawSubMode = scene?.sub_mode || scene?.quantum_mode || scene?.mode || 'schrodinger_tunneling';
  const textLower = `${scene?.title || ''} ${scene?.display_text || ''} ${scene?.narration || ''} ${scene?.spoken_text || ''}`.toLowerCase();

  let subMode = 'schrodinger_tunneling';
  if (rawSubMode === 'heisenberg_uncertainty' || textLower.includes('heisenberg') || textLower.includes('uncertainty') || textLower.includes('momentum') || textLower.includes('squeeze')) {
    subMode = 'heisenberg_uncertainty';
  } else if (rawSubMode === 'dirac_atomic_orbitals' || textLower.includes('dirac') || textLower.includes('orbital') || textLower.includes('spinor') || textLower.includes('spin')) {
    subMode = 'dirac_atomic_orbitals';
  } else {
    subMode = 'schrodinger_tunneling';
  }

  const title = scene?.title || (
    subMode === 'heisenberg_uncertainty'
      ? 'Heisenberg Reciprocal Squeeze'
      : subMode === 'dirac_atomic_orbitals'
      ? 'Dirac Spinor & Atomic Orbitals'
      : 'Quantum Wavepacket Tunneling'
  );

  const startFrame = scene?.choreography?.scene_start_frame || sceneStartFrame || 0;
  const endFrame = scene?.choreography?.scene_end_frame || (startFrame + 90);
  const totalFrames = Math.max(30, endFrame - startFrame);
  const localFrame = Math.max(0, Math.min(totalFrames, frame - startFrame));
  const progress = localFrame / totalFrames; // 0.0 to 1.0

  // 3-Phase Animation Slices
  const isPhase1 = progress < 0.35;
  const isPhase2 = progress >= 0.35 && progress < 0.70;
  const isPhase3 = progress >= 0.70;

  // Viewport Height
  const stageHeight = isSpotlight ? '1260px' : (isCompact ? '960px' : '1540px');
  const canvasHeight = isSpotlight ? 760 : (isCompact ? 520 : 680);
  const canvasWidth = 896;

  // Primary Theme Palette
  const palette = {
    primary: '#a855f7',
    secondary: '#38bdf8',
    accent: '#34d399',
    background: '#090614',
    border: 'rgba(168, 85, 247, 0.35)',
    glow: 'rgba(168, 85, 247, 0.22)',
  };

  // -------------------------------------------------------------------------
  // Sub-Mode 1: Schrödinger Wavepacket & Quantum Tunneling
  // -------------------------------------------------------------------------
  // Center of wavepacket sweeps from x = -3.5 to x = +3.5
  const packetCenter = interpolate(progress, [0, 1], [-3.8, 3.8]);
  const barrierX1 = -0.4;
  const barrierX2 = 1.4;
  const barrierHeight = 160;

  // Generate SVG curve points for Re[Psi] and |Psi|^2 envelope
  const tunnelPointsCount = 80;
  const psiRePoints = [];
  const psiProbPoints = [];

  const originX = canvasWidth / 2;
  const originY = canvasHeight / 2 + 50;
  const scaleX = 80;
  const scaleY = 120;

  for (let i = 0; i <= tunnelPointsCount; i++) {
    const x = -5.0 + (i / tunnelPointsCount) * 10.0;
    let amp = Math.exp(-Math.pow(x - packetCenter, 2) / 0.85);

    // If inside barrier, show exponential attenuation
    if (x >= barrierX1 && x <= barrierX2) {
      amp = amp * Math.exp(-1.8 * (x - barrierX1));
    } else if (x > barrierX2) {
      // Transmitted packet has ~8.2% transmission amplitude
      amp = amp * 0.28;
    }

    const phase = (x - packetCenter) * 8.0 - localFrame * 0.35;
    const rePsi = amp * Math.cos(phase);
    const probPsi = amp * amp;

    const screenX = originX + x * scaleX;
    const screenYRe = originY - rePsi * scaleY;
    const screenYProb = originY - probPsi * scaleY * 1.25;

    psiRePoints.push(`${i === 0 ? 'M' : 'L'} ${screenX.toFixed(1)} ${screenYRe.toFixed(1)}`);
    psiProbPoints.push(`${i === 0 ? 'M' : 'L'} ${screenX.toFixed(1)} ${screenYProb.toFixed(1)}`);
  }

  const psiRePath = psiRePoints.join(' ');
  const psiProbPath = psiProbPoints.join(' ');

  // -------------------------------------------------------------------------
  // Sub-Mode 2: Heisenberg Uncertainty Squeeze (Δx vs Δp)
  // -------------------------------------------------------------------------
  // Delta X squeezes down from 1.6 to 0.45; Delta P explodes from 0.65 to 2.3
  const deltaXVal = interpolate(progress, [0, 0.5, 1], [1.6, 0.45, 1.2]);
  const deltaPVal = Math.max(0.5, 0.55 / deltaXVal);
  const uncertaintyProduct = (deltaXVal * deltaPVal).toFixed(2);

  // Position plot path
  const posXPoints = [];
  const momPPoints = [];
  const plotWidth = 360;
  const posOriginX = 220;
  const momOriginX = 670;
  const plotsOriginY = isSpotlight ? 420 : 380;

  for (let i = -30; i <= 30; i++) {
    const u = i / 10.0;
    // Position Gaussian
    const yPos = Math.exp(-Math.pow(u, 2) / (2 * deltaXVal * deltaXVal)) * (1.1 / Math.sqrt(deltaXVal));
    const sxPos = posOriginX + u * 50;
    const syPos = plotsOriginY - yPos * 75;
    posXPoints.push(`${i === -30 ? 'M' : 'L'} ${sxPos.toFixed(1)} ${syPos.toFixed(1)}`);

    // Momentum Gaussian
    const yMom = Math.exp(-Math.pow(u, 2) / (2 * deltaPVal * deltaPVal)) * (1.1 / Math.sqrt(deltaPVal));
    const sxMom = momOriginX + u * 50;
    const syMom = plotsOriginY - yMom * 75;
    momPPoints.push(`${i === -30 ? 'M' : 'L'} ${sxMom.toFixed(1)} ${syMom.toFixed(1)}`);
  }

  // -------------------------------------------------------------------------
  // Sub-Mode 3: Dirac Atomic Orbitals (1s -> 2pz -> 3d)
  // -------------------------------------------------------------------------
  const orbitalStage = isPhase1 ? '1s' : (isPhase2 ? '2p_z' : '3d_xy');
  const spinPhase = localFrame * 0.15;
  const spinUp = Math.sin(spinPhase) >= 0;

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
      {/* 1. TOP EDITORIAL HEADER (190px) */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          height: '190px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
          transform: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <QuantumIcon size={28} color={palette.primary} />
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
              QUANTUM MECHANICS & SPIN DYNAMICS
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(168, 85, 247, 0.16)',
                border: `1.5px solid ${palette.primary}`,
                color: palette.primary,
                borderRadius: '8px',
                padding: '4px 14px',
                fontSize: '16px',
                fontFamily: 'monospace',
                fontWeight: 900,
              }}
            >
              {subMode === 'heisenberg_uncertainty'
                ? 'Δx·Δp ≥ ℏ/2'
                : subMode === 'dirac_atomic_orbitals'
                ? 'DIRAC 4-SPINOR'
                : 'TUNNELING: T = e^(-2κL)'}
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
              transform: 'none',
            }}
          >
            {title}
          </div>
          <div style={{ fontSize: '23px', color: '#94a3b8', marginTop: '4px', fontStyle: 'italic', transform: 'none' }}>
            {scene?.spoken_text || (
              subMode === 'heisenberg_uncertainty'
                ? 'Squeezing position space forces momentum uncertainty to explode reciprocally.'
                : subMode === 'dirac_atomic_orbitals'
                ? 'Relativistic Dirac equation yields electron spin and atomic orbital manifolds.'
                : 'A quantum wavepacket penetrates a barrier with exponential evanescent decay.'
            )}
          </div>
        </div>
      </div>

      {/* 2. CENTER ANIMATED QUANTUM CANVAS */}
      <div
        style={{
          height: `${canvasHeight}px`,
          backgroundColor: '#0a0518',
          borderRadius: '22px',
          border: '1.5px solid rgba(168, 85, 247, 0.25)',
          boxShadow: 'inset 0 0 36px rgba(0, 0, 0, 0.85), 0 0 24px rgba(168, 85, 247, 0.15)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'hidden',
          position: 'relative',
          transform: 'none',
        }}
      >
        {scene?.manim_video_src ? (
          <div style={{ position: 'relative', width: '100%', height: '100%' }}>
            <OffthreadVideo
              src={staticFile(scene.manim_video_src)}
              muted
              style={{ width: '100%', height: '100%', objectFit: 'contain', borderRadius: '20px' }}
            />
            <div
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                backgroundColor: 'rgba(10, 5, 24, 0.85)',
                border: '1px solid #c084fc',
                color: '#c084fc',
                borderRadius: '6px',
                padding: '4px 12px',
                fontSize: '13px',
                fontFamily: 'monospace',
                fontWeight: 800,
                zIndex: 10,
              }}
            >
              MANIM CAIRO ENGINE • 30 FPS
            </div>
          </div>
        ) : (
          <svg
            width={canvasWidth}
            height={canvasHeight}
            viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
            style={{ width: '100%', height: '100%' }}
          >
          <defs>
            {/* Barrier Hatch Pattern */}
            <pattern id="barrierHatch" width="12" height="12" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="12" stroke="#f59e0b" strokeWidth="2.5" strokeOpacity="0.4" />
            </pattern>
            {/* Orbital Radial Gradients */}
            <radialGradient id="orbitalGlow1s" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#c084fc" stopOpacity="0.95" />
              <stop offset="45%" stopColor="#a855f7" stopOpacity="0.6" />
              <stop offset="85%" stopColor="#7c3aed" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#0a0518" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="waveGradRe" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.2" />
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="1" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {/* Sub-Mode 1: Schrödinger Tunneling */}
          {subMode === 'schrodinger_tunneling' && (
            <g>
              {/* Coordinate Grid Lines */}
              <line x1="40" y1={originY} x2={canvasWidth - 40} y2={originY} stroke="rgba(255, 255, 255, 0.18)" strokeWidth="1.5" strokeDasharray="4 4" />
              <line x1={originX} y1="60" x2={originX} y2={canvasHeight - 60} stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1.5" />

              {/* Potential Barrier V_0 (Amber Shaded Box) */}
              <rect
                x={originX + barrierX1 * scaleX}
                y={originY - barrierHeight}
                width={(barrierX2 - barrierX1) * scaleX}
                height={barrierHeight}
                fill="url(#barrierHatch)"
                stroke="#f59e0b"
                strokeWidth="2.5"
                rx="6"
              />
              <text
                x={originX + ((barrierX1 + barrierX2) / 2) * scaleX}
                y={originY - barrierHeight - 16}
                fill="#f59e0b"
                fontSize="17"
                fontFamily="monospace"
                fontWeight="bold"
                textAnchor="middle"
              >
                Barrier V₀ = 8.5 eV (L = 1.2 nm)
              </text>

              {/* Energy Level Line E < V_0 */}
              <line
                x1="60"
                y1={originY - 95}
                x2={canvasWidth - 60}
                y2={originY - 95}
                stroke="#38bdf8"
                strokeWidth="2"
                strokeDasharray="6 4"
                strokeOpacity="0.6"
              />
              <text x="70" y={originY - 105} fill="#38bdf8" fontSize="15" fontFamily="monospace" fontWeight="bold">
                Incident Energy E = 5.2 eV &lt; V₀
              </text>

              {/* Probability Envelope |Psi|^2 (Emerald Glow) */}
              <path
                d={psiProbPath}
                fill="none"
                stroke="#34d399"
                strokeWidth="4"
                strokeLinecap="round"
              />

              {/* Real Component Re[Psi] (Cyan Oscillation) */}
              <path
                d={psiRePath}
                fill="none"
                stroke="#38bdf8"
                strokeWidth="2.5"
                strokeLinecap="round"
              />

              {/* Region Indicators */}
              <text x={originX - 220} y={canvasHeight - 45} fill="#94a3b8" fontSize="16" fontFamily="monospace" textAnchor="middle">
                Region I: Incident &amp; Reflected Wave
              </text>
              <text x={originX + ((barrierX1 + barrierX2) / 2) * scaleX} y={canvasHeight - 45} fill="#f59e0b" fontSize="16" fontFamily="monospace" textAnchor="middle">
                Region II: Evanescent ψ ~ e^(-κx)
              </text>
              <text x={originX + 260} y={canvasHeight - 45} fill="#34d399" fontSize="16" fontFamily="monospace" textAnchor="middle">
                Region III: Transmitted Tunneling (T ≈ 8.2%)
              </text>
            </g>
          )}

          {/* Sub-Mode 2: Heisenberg Uncertainty Squeeze */}
          {subMode === 'heisenberg_uncertainty' && (
            <g>
              {/* Left Plot: Position Space |psi(x)|^2 */}
              <g>
                <text x={posOriginX} y="75" fill="#38bdf8" fontSize="20" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  POSITION SPACE |ψ(x)|²
                </text>
                <text x={posOriginX} y="105" fill="#94a3b8" fontSize="16" fontFamily="monospace" textAnchor="middle">
                  {`Δx = ${deltaXVal.toFixed(2)} nm (Spatial Localization)`}
                </text>

                {/* Axes */}
                <line x1="70" y1={plotsOriginY} x2="370" y2={plotsOriginY} stroke="rgba(255, 255, 255, 0.2)" strokeWidth="2" />
                <line x1={posOriginX} y1="120" x2={posOriginX} y2={plotsOriginY + 20} stroke="rgba(255, 255, 255, 0.2)" strokeWidth="2" />

                {/* Squeezing Position Wave */}
                <path
                  d={posXPoints.join(' ')}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              </g>

              {/* Right Plot: Momentum Space |phi(p)|^2 */}
              <g>
                <text x={momOriginX} y="75" fill="#a855f7" fontSize="20" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  MOMENTUM SPACE |ϕ(p)|²
                </text>
                <text x={momOriginX} y="105" fill="#94a3b8" fontSize="16" fontFamily="monospace" textAnchor="middle">
                  {`Δp = ${deltaPVal.toFixed(2)} ℏ/nm (Momentum Explosion)`}
                </text>

                {/* Axes */}
                <line x1="520" y1={plotsOriginY} x2="820" y2={plotsOriginY} stroke="rgba(255, 255, 255, 0.2)" strokeWidth="2" />
                <line x1={momOriginX} y1="120" x2={momOriginX} y2={plotsOriginY + 20} stroke="rgba(255, 255, 255, 0.2)" strokeWidth="2" />

                {/* Reciprocally Spreading Momentum Wave */}
                <path
                  d={momPPoints.join(' ')}
                  fill="none"
                  stroke="#a855f7"
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              </g>

              {/* Center Phase-Space Uncertainty Ellipse */}
              <g transform={`translate(${canvasWidth / 2}, ${canvasHeight - 110})`}>
                <rect x="-190" y="-45" width="380" height="90" rx="14" fill="rgba(15, 23, 42, 0.85)" stroke="rgba(168, 85, 247, 0.4)" strokeWidth="1.5" />
                <ellipse cx="0" cy="0" rx={Math.max(25, deltaXVal * 35)} ry={Math.max(12, deltaPVal * 15)} fill="none" stroke="#34d399" strokeWidth="2.5" strokeDasharray="4 3" />
                <text x="0" y="28" fill="#34d399" fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  {`Phase Space Area: Δx·Δp = ${uncertaintyProduct} ℏ ≥ 0.5 ℏ`}
                </text>
              </g>
            </g>
          )}

          {/* Sub-Mode 3: Dirac Atomic Orbitals */}
          {subMode === 'dirac_atomic_orbitals' && (
            <g transform={`translate(${originX}, ${originY - 20})`}>
              {/* Radial Coordinate Circles */}
              {[60, 120, 180].map((r) => (
                <circle key={`rad-${r}`} cx="0" cy="0" r={r} fill="none" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1.2" strokeDasharray="4 4" />
              ))}

              {/* 1s Spherical Shell */}
              {isPhase1 && (
                <g>
                  <circle cx="0" cy="0" r="110" fill="url(#orbitalGlow1s)" />
                  <circle cx="0" cy="0" r="16" fill="#ffffff" />
                  <text x="0" y="160" fill="#c084fc" fontSize="20" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                    1s Orbital (n=1, l=0, ml=0) • Spherical Ground State
                  </text>
                </g>
              )}

              {/* 2p_z Dumbbell Orbital */}
              {isPhase2 && (
                <g>
                  {/* Upper Lobe (Positive Phase, Violet) */}
                  <ellipse cx="0" cy="-85" rx="55" ry="80" fill="rgba(168, 85, 247, 0.65)" stroke="#c084fc" strokeWidth="2.5" />
                  <text x="0" y="-80" fill="#ffffff" fontSize="22" fontFamily="monospace" fontWeight="bold" textAnchor="middle">+</text>

                  {/* Lower Lobe (Negative Phase, Cyan) */}
                  <ellipse cx="0" cy="85" rx="55" ry="80" fill="rgba(56, 189, 248, 0.65)" stroke="#38bdf8" strokeWidth="2.5" />
                  <text x="0" y="90" fill="#ffffff" fontSize="22" fontFamily="monospace" fontWeight="bold" textAnchor="middle">-</text>

                  {/* Nodal Plane at z=0 */}
                  <line x1="-160" y1="0" x2="160" y2="0" stroke="#f43f5e" strokeWidth="2" strokeDasharray="6 4" />
                  <text x="0" y="195" fill="#38bdf8" fontSize="20" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                    2pz Orbital (n=2, l=1, ml=0) • Nodal Plane at z=0
                  </text>
                </g>
              )}

              {/* 3d_x²-y² Cloverleaf Orbital */}
              {isPhase3 && (
                <g>
                  {/* 4 Cloverleaf Lobes */}
                  <ellipse cx="0" cy="-90" rx="42" ry="70" fill="rgba(168, 85, 247, 0.6)" stroke="#c084fc" strokeWidth="2" />
                  <ellipse cx="0" cy="90" rx="42" ry="70" fill="rgba(168, 85, 247, 0.6)" stroke="#c084fc" strokeWidth="2" />
                  <ellipse cx="-90" cy="0" rx="70" ry="42" fill="rgba(52, 211, 153, 0.6)" stroke="#34d399" strokeWidth="2" />
                  <ellipse cx="90" cy="0" rx="70" ry="42" fill="rgba(52, 211, 153, 0.6)" stroke="#34d399" strokeWidth="2" />
                  <circle cx="0" cy="0" r="12" fill="#ffffff" />
                  <text x="0" y="195" fill="#34d399" fontSize="20" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                    3d_x²-y² Orbital (n=3, l=2, ml=2) • 4-Lobe Cloverleaf
                  </text>
                </g>
              )}

              {/* Dirac Spinor Gauge Widget at Top Right */}
              <g transform="translate(260, -140)">
                <rect x="-70" y="-35" width="140" height="70" rx="10" fill="rgba(15, 23, 42, 0.9)" stroke="#a855f7" strokeWidth="1.5" />
                <text x="0" y="-12" fill="#94a3b8" fontSize="13" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  SPIN STATE
                </text>
                <text x="0" y="18" fill={spinUp ? '#34d399' : '#38bdf8'} fontSize="20" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  {spinUp ? 'SPIN UP (↑)' : 'SPIN DOWN (↓)'}
                </text>
              </g>
            </g>
          )}
        </svg>
        )}
      </div>

      {/* 3. BOTTOM TELEMETRY & EQUATION SOLVER (Hides in spotlight mode) */}
      {!isSpotlight && (
        <div
          style={{
            height: isCompact ? '180px' : '260px',
            display: 'grid',
            gridTemplateColumns: '1.2fr 1fr',
            gap: '18px',
            transform: 'none',
          }}
        >
          {/* Card 1: Master Equation Banner */}
          <div
            style={{
              backgroundColor: '#120d24',
              borderRadius: '18px',
              border: '1.5px solid rgba(168, 85, 247, 0.3)',
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              transform: 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <SparklesIcon size={22} color="#c084fc" />
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#c084fc', fontFamily: 'monospace' }}>
                {subMode === 'heisenberg_uncertainty'
                  ? 'CANONICAL COMMUTATOR & RECIPROCITY'
                  : subMode === 'dirac_atomic_orbitals'
                  ? 'RELATIVISTIC DIRAC BI-SPINOR'
                  : 'SCHRÖDINGER TIME-DEPENDENT WAVE EQUATION'}
              </span>
            </div>

            <div style={{ fontSize: '24px', color: '#ffffff', fontFamily: 'monospace', fontWeight: 'bold' }}>
              {subMode === 'heisenberg_uncertainty'
                ? '[x̂, p̂] = iℏ ⟹ σ_x · σ_p ≥ ℏ/2'
                : subMode === 'dirac_atomic_orbitals'
                ? '(iγ^μ ∂_μ - m)ψ = 0  (4-Component Bi-Spinor)'
                : 'iℏ ∂Ψ/∂t = [-(ℏ²/2m)∇² + V(x)]Ψ'}
            </div>

            <div style={{ fontSize: '16px', color: '#94a3b8', fontFamily: 'monospace' }}>
              {subMode === 'heisenberg_uncertainty'
                ? 'Fourier conjugate pairs impose non-zero phase space volume bound.'
                : subMode === 'dirac_atomic_orbitals'
                ? 'Unifies special relativity with quantum mechanics; predicts anti-matter.'
                : 'Evanescent wave inside barrier emerges as finite transmitted current.'}
            </div>
          </div>

          {/* Card 2: Live Quantum State Telemetry */}
          <div
            style={{
              backgroundColor: '#120d24',
              borderRadius: '18px',
              border: '1.5px solid rgba(56, 189, 248, 0.3)',
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              transform: 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <LightningIcon size={22} color="#38bdf8" />
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#38bdf8', fontFamily: 'monospace' }}>
                OBSERVABLE TELEMETRY
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '15px', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {subMode === 'heisenberg_uncertainty' ? 'POSITION Δx' : 'ENERGY STATE'}
                </div>
                <div style={{ fontSize: '26px', color: '#38bdf8', fontFamily: 'monospace', fontWeight: 'bold' }}>
                  {subMode === 'heisenberg_uncertainty' ? `${deltaXVal.toFixed(2)} nm` : 'E = +mc² (Spin Up)'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '15px', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {subMode === 'heisenberg_uncertainty' ? 'MOMENTUM Δp' : 'TRANSMISSION'}
                </div>
                <div style={{ fontSize: '26px', color: '#34d399', fontFamily: 'monospace', fontWeight: 'bold' }}>
                  {subMode === 'heisenberg_uncertainty' ? `${deltaPVal.toFixed(2)} ℏ/nm` : 'T = 8.2%'}
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '6px 12px',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                borderRadius: '8px',
                fontSize: '15px',
                color: '#38bdf8',
                fontFamily: 'monospace',
                fontWeight: 'bold',
              }}
            >
              STATUS: CONTINUOUS UNITARY TIME EVOLUTION
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuantumScene;

