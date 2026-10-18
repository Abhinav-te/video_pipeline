import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { MechanicsIcon, SparklesIcon, LightningIcon, ScaleIcon } from './SvgIcons';

/**
 * MechanicsScene (Engine 2 - Advanced Mechanics, Weight Distribution & Statics)
 *
 * Viewport Breathing:
 *   - 'compact_punch': ~55% height (centered, maxHeight: 960px)
 *   - 'canvas_spotlight': ~72% height (1260px tall) - expands FBD canvas to 920x940
 *   - 'full_dashboard': ~88% height (1540px tall) - full 3-tier layout with step-by-step solver
 *
 * 3 Distinct Sub-Modes:
 *   1. 'beam_weight_distribution': Multi-support bridge load distribution & torque equilibrium
 *   2. 'inclined_plane_fbd': Inclined plane vector decomposition & friction slip threshold
 *   3. 'axle_center_of_mass': Vehicle chassis CG & dynamic axle load transfer during acceleration
 */
export const MechanicsScene = ({
  scene,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const layoutDensity = scene?.choreography?.layout_density || scene?.layout_density || 'canvas_spotlight';
  const isSpotlight = layoutDensity === 'canvas_spotlight';
  const isCompact = layoutDensity === 'compact_punch';

  const rawSubMode = scene?.sub_mode || scene?.mechanics_mode || scene?.mode || 'beam_weight_distribution';
  const textLower = `${scene?.title || ''} ${scene?.display_text || ''} ${scene?.narration || ''} ${scene?.spoken_text || ''}`.toLowerCase();

  let subMode = 'beam_weight_distribution';
  if (rawSubMode === 'inclined_plane_fbd' || textLower.includes('incline') || textLower.includes('ramp') || textLower.includes('angle') || textLower.includes('friction')) {
    subMode = 'inclined_plane_fbd';
  } else if (rawSubMode === 'axle_center_of_mass' || textLower.includes('axle') || textLower.includes('center of mass') || textLower.includes('wheelbase') || textLower.includes('chassis')) {
    subMode = 'axle_center_of_mass';
  } else {
    subMode = 'beam_weight_distribution';
  }

  const title = scene?.title || (
    subMode === 'inclined_plane_fbd'
      ? 'Inclined Plane Vector Statics'
      : subMode === 'axle_center_of_mass'
      ? 'Dynamic Axle Load Transfer'
      : 'Structural Beam Load Distribution'
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

  // Palette (Industrial Orange & Steel Slate)
  const palette = {
    primary: '#f97316',
    secondary: '#38bdf8',
    accent: '#eab308',
    background: '#0d131f',
    border: 'rgba(249, 115, 22, 0.35)',
    glow: 'rgba(249, 115, 22, 0.20)',
  };

  // -------------------------------------------------------------------------
  // Sub-Mode 1: Structural Beam Load Distribution (L = 10m)
  // -------------------------------------------------------------------------
  // As point load W1 scrubs across the beam from x = 2m to x = 8m
  const beamLengthM = 10.0;
  const beamLeftX = 120;
  const beamRightX = 776;
  const beamSpanPx = beamRightX - beamLeftX;
  const beamY = 240;

  const loadXMeters = interpolate(progress, [0, 1], [2.0, 8.0]);
  const loadXPx = beamLeftX + (loadXMeters / beamLengthM) * beamSpanPx;
  const loadW1Kn = 50.0;
  const beamWeightKn = 50.0; // uniform 5 kN/m * 10m

  // Equilibrium reactions:
  // Στ_A = 0 => R_B * 10 - W1 * x - W_beam * 5 = 0
  const reactionRbKn = ((loadW1Kn * loadXMeters) + (beamWeightKn * 5.0)) / beamLengthM;
  const reactionRaKn = (loadW1Kn + beamWeightKn) - reactionRbKn;

  // Vector arrow heights
  const arrowScale = 1.35;
  const arrowRaHeight = Math.max(25, reactionRaKn * arrowScale);
  const arrowRbHeight = Math.max(25, reactionRbKn * arrowScale);

  // Shear Force and Moment Curves
  const shearPoints = [];
  const momentPoints = [];
  const shearBaseY = isSpotlight ? 500 : 450;
  const momentBaseY = isSpotlight ? 660 : 590;

  for (let s = 0; s <= 20; s++) {
    const xPos = beamLeftX + (s / 20) * beamSpanPx;
    const xM = (s / 20) * beamLengthM;

    // Shear V(x)
    let vVal = reactionRaKn - 5.0 * xM;
    if (xM >= loadXMeters) {
      vVal -= loadW1Kn;
    }
    const sy = shearBaseY - vVal * 1.5;
    shearPoints.push(`${s === 0 ? 'M' : 'L'} ${xPos.toFixed(1)} ${sy.toFixed(1)}`);

    // Bending Moment M(x)
    let mVal = reactionRaKn * xM - 0.5 * 5.0 * xM * xM;
    if (xM >= loadXMeters) {
      mVal -= loadW1Kn * (xM - loadXMeters);
    }
    const my = momentBaseY - mVal * 0.5;
    momentPoints.push(`${s === 0 ? 'M' : 'L'} ${xPos.toFixed(1)} ${my.toFixed(1)}`);
  }

  // -------------------------------------------------------------------------
  // Sub-Mode 2: Inclined Plane FBD (θ sweeps 15° -> 40°)
  // -------------------------------------------------------------------------
  const rampAngleDeg = interpolate(progress, [0, 1], [15, 40]);
  const rampAngleRad = (rampAngleDeg * Math.PI) / 180;
  const massKg = 20;
  const gAcc = 9.81;
  const fGravity = massKg * gAcc; // 196.2 N
  const fParallel = fGravity * Math.sin(rampAngleRad);
  const fNormal = fGravity * Math.cos(rampAngleRad);
  const muStatic = 0.55;
  const maxStaticFriction = muStatic * fNormal;
  const isSliding = fParallel > maxStaticFriction;
  const slidingAcc = isSliding ? (fParallel - 0.4 * fNormal) / massKg : 0.0;

  // Block position down the ramp if sliding
  const blockSlideOffset = isSliding ? interpolate(progress, [0.55, 1], [0, 140]) : 0;

  // -------------------------------------------------------------------------
  // Sub-Mode 3: Axle Center of Mass Load Transfer
  // -------------------------------------------------------------------------
  const isAccelerating = progress > 0.30;
  const accelG = isAccelerating ? interpolate(progress, [0.3, 0.7, 1], [0.1, 0.65, 0.4]) : 0.0;
  const staticFrontPct = 55;
  const staticRearPct = 45;
  const transferPct = accelG * 25.0; // Dynamic squat transfer
  const dynFrontPct = Math.max(25, (staticFrontPct - transferPct)).toFixed(1);
  const dynRearPct = Math.min(75, (staticRearPct + transferPct)).toFixed(1);

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
            <MechanicsIcon size={28} color={palette.primary} />
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
              ADVANCED MECHANICS &amp; STATICS
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(249, 115, 22, 0.16)',
                border: `1.5px solid ${palette.primary}`,
                color: palette.primary,
                borderRadius: '8px',
                padding: '4px 14px',
                fontSize: '16px',
                fontFamily: 'monospace',
                fontWeight: 900,
              }}
            >
              {subMode === 'inclined_plane_fbd'
                ? `θ = ${rampAngleDeg.toFixed(1)}° (${isSliding ? 'SLIDING a>0' : 'STATIC'})`
                : subMode === 'axle_center_of_mass'
                ? `DYNAMIC SQUAT: +${transferPct.toFixed(0)}% REAR`
                : `ΣF_y = 0 • Στ_A = 0`}
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
              subMode === 'inclined_plane_fbd'
                ? 'Decomposing gravity into parallel and normal vectors determines static slip.'
                : subMode === 'axle_center_of_mass'
                ? 'Longitudinal acceleration transfers normal load from front to rear axle.'
                : 'Scrubbing point load alters support reactions RA and RB dynamically.'
            )}
          </div>
        </div>
      </div>

      {/* 2. CENTER ANIMATED MECHANICS CANVAS */}
      <div
        style={{
          height: `${canvasHeight}px`,
          backgroundColor: '#0a0f19',
          borderRadius: '22px',
          border: '1.5px solid rgba(249, 115, 22, 0.25)',
          boxShadow: 'inset 0 0 36px rgba(0, 0, 0, 0.85), 0 0 24px rgba(249, 115, 22, 0.12)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'hidden',
          position: 'relative',
          transform: 'none',
        }}
      >
        <svg
          width={canvasWidth}
          height={canvasHeight}
          viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
          style={{ width: '100%', height: '100%' }}
        >
          <defs>
            <linearGradient id="beamSteelGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#334155" />
              <stop offset="50%" stopColor="#475569" />
              <stop offset="100%" stopColor="#1e293b" />
            </linearGradient>
            <marker id="arrowUpOrange" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
              <path d="M4 0 L8 8 L0 8 Z" fill="#f97316" />
            </marker>
            <marker id="arrowDownCyan" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
              <path d="M4 8 L8 0 L0 0 Z" fill="#38bdf8" />
            </marker>
            <marker id="arrowDownRed" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
              <path d="M4 8 L8 0 L0 0 Z" fill="#ef4444" />
            </marker>
          </defs>

          {/* Sub-Mode 1: Structural Beam Load Distribution */}
          {subMode === 'beam_weight_distribution' && (
            <g>
              {/* Distributed Load Arrows (w = 5 kN/m) */}
              {Array.from({ length: 11 }).map((_, idx) => {
                const wx = beamLeftX + (idx / 10) * beamSpanPx;
                return (
                  <g key={`dist-${idx}`}>
                    <line x1={wx} y1={beamY - 45} x2={wx} y2={beamY - 14} stroke="#38bdf8" strokeWidth="2" markerEnd="url(#arrowDownCyan)" />
                  </g>
                );
              })}
              <line x1={beamLeftX} y1={beamY - 45} x2={beamRightX} y2={beamY - 45} stroke="#38bdf8" strokeWidth="2.5" />
              <text x={(beamLeftX + beamRightX) / 2} y={beamY - 55} fill="#38bdf8" fontSize="16" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                Uniform Distributed Load w = 5.0 kN/m
              </text>

              {/* Structural I-Beam */}
              <rect x={beamLeftX} y={beamY - 12} width={beamSpanPx} height="24" rx="4" fill="url(#beamSteelGrad)" stroke="#64748b" strokeWidth="2" />

              {/* Left Pin Support (RA) */}
              <polygon points={`${beamLeftX},${beamY + 12} ${beamLeftX - 18},${beamY + 46} ${beamLeftX + 18},${beamY + 46}`} fill="#1e293b" stroke="#f97316" strokeWidth="2.5" />
              <circle cx={beamLeftX} cy={beamY + 14} r="4" fill="#f97316" />
              <line x1={beamLeftX - 30} y1={beamY + 46} x2={beamLeftX + 30} y2={beamY + 46} stroke="#f97316" strokeWidth="3" />
              {/* RA Reaction Vector Arrow */}
              <line x1={beamLeftX} y1={beamY + 160} x2={beamLeftX} y2={beamY + 160 - arrowRaHeight} stroke="#f97316" strokeWidth="5" markerEnd="url(#arrowUpOrange)" />
              <text x={beamLeftX - 16} y={beamY + 130} fill="#f97316" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="end">
                {`R_A = ${reactionRaKn.toFixed(1)} kN`}
              </text>

              {/* Right Roller Support (RB) */}
              <polygon points={`${beamRightX},${beamY + 12} ${beamRightX - 18},${beamY + 36} ${beamRightX + 18},${beamY + 36}`} fill="#1e293b" stroke="#34d399" strokeWidth="2.5" />
              <circle cx={beamRightX - 10} cy={beamY + 42} r="5" fill="#34d399" />
              <circle cx={beamRightX + 10} cy={beamY + 42} r="5" fill="#34d399" />
              <line x1={beamRightX - 30} y1={beamY + 48} x2={beamRightX + 30} y2={beamY + 48} stroke="#34d399" strokeWidth="3" />
              {/* RB Reaction Vector Arrow */}
              <line x1={beamRightX} y1={beamY + 160} x2={beamRightX} y2={beamY + 160 - arrowRbHeight} stroke="#34d399" strokeWidth="5" markerEnd="url(#arrowUpOrange)" />
              <text x={beamRightX + 16} y={beamY + 130} fill="#34d399" fontSize="18" fontFamily="monospace" fontWeight="bold">
                {`R_B = ${reactionRbKn.toFixed(1)} kN`}
              </text>

              {/* Scrubbing Point Load W1 (Heavy Red Arrow) */}
              <line x1={loadXPx} y1={beamY - 110} x2={loadXPx} y2={beamY - 16} stroke="#ef4444" strokeWidth="6" markerEnd="url(#arrowDownRed)" />
              <rect x={loadXPx - 55} y={beamY - 145} width="110" height="30" rx="6" fill="#1e293b" stroke="#ef4444" strokeWidth="1.5" />
              <text x={loadXPx} y={beamY - 125} fill="#ef4444" fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                {`W₁ = 50 kN`}
              </text>
              <text x={loadXPx} y={beamY + 28} fill="#ef4444" fontSize="15" fontFamily="monospace" textAnchor="middle">
                {`x = ${loadXMeters.toFixed(1)}m`}
              </text>

              {/* Shear Diagram V(x) */}
              <text x="50" y={shearBaseY - 15} fill="#94a3b8" fontSize="14" fontFamily="monospace" fontWeight="bold">
                SHEAR V(x)
              </text>
              <line x1={beamLeftX} y1={shearBaseY} x2={beamRightX} y2={shearBaseY} stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" />
              <path d={shearPoints.join(' ')} fill="none" stroke="#f97316" strokeWidth="3.5" />

              {/* Bending Moment Diagram M(x) */}
              <text x="50" y={momentBaseY - 15} fill="#94a3b8" fontSize="14" fontFamily="monospace" fontWeight="bold">
                MOMENT M(x)
              </text>
              <line x1={beamLeftX} y1={momentBaseY} x2={beamRightX} y2={momentBaseY} stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" />
              <path d={momentPoints.join(' ')} fill="none" stroke="#38bdf8" strokeWidth="3.5" />
            </g>
          )}

          {/* Sub-Mode 2: Inclined Plane Free-Body Decomposition */}
          {subMode === 'inclined_plane_fbd' && (
            <g transform="translate(180, 120)">
              {/* Ramp Base Geometry */}
              <polygon
                points={`0,440 600,440 600,${440 - 600 * Math.tan(rampAngleRad)}`}
                fill="rgba(30, 41, 59, 0.8)"
                stroke="#64748b"
                strokeWidth="2.5"
              />
              <path
                d={`M 80,440 A 80 80 0 0 0 ${80 * Math.cos(rampAngleRad)},${440 - 80 * Math.sin(rampAngleRad)}`}
                fill="none"
                stroke="#f97316"
                strokeWidth="2.5"
              />
              <text x="110" y="425" fill="#f97316" fontSize="20" fontFamily="monospace" fontWeight="bold">
                {`θ = ${rampAngleDeg.toFixed(1)}°`}
              </text>

              {/* Mass Block m on Tilted Ramp */}
              <g
                transform={`
                  translate(${300 + blockSlideOffset * Math.cos(rampAngleRad)}, ${440 - 300 * Math.tan(rampAngleRad) + blockSlideOffset * Math.sin(rampAngleRad)})
                  rotate(${-rampAngleDeg})
                `}
              >
                {/* Block Body */}
                <rect x="-60" y="-80" width="120" height="80" rx="8" fill="#1e293b" stroke="#f97316" strokeWidth="2.5" />
                <text x="0" y="-35" fill="#ffffff" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  {`m = 20 kg`}
                </text>

                {/* Normal Force F_N (Perpendicular ↖) */}
                <line x1="0" y1="-80" x2="0" y2="-170" stroke="#38bdf8" strokeWidth="4" markerEnd="url(#arrowUpOrange)" />
                <text x="-12" y="-140" fill="#38bdf8" fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="end">
                  {`F_N = ${fNormal.toFixed(1)} N`}
                </text>

                {/* Friction Force f_s (Opposing slide ↗) */}
                <line x1="60" y1="-10" x2="150" y2="-10" stroke="#eab308" strokeWidth="4" />
                <text x="110" y="-22" fill="#eab308" fontSize="14" fontFamily="monospace" fontWeight="bold">
                  {`f_s = ${maxStaticFriction.toFixed(1)} N`}
                </text>

                {/* Gravity Component mg·sin(θ) (Down-ramp ↙) */}
                <line x1="-60" y1="-10" x2="-150" y2="-10" stroke="#ef4444" strokeWidth="4" />
                <text x="-160" y="-22" fill="#ef4444" fontSize="14" fontFamily="monospace" fontWeight="bold" textAnchor="end">
                  {`mg·sinθ = ${fParallel.toFixed(1)} N`}
                </text>
              </g>

              {/* Status Banner */}
              <g transform="translate(300, 480)">
                <rect x="-180" y="-25" width="360" height="50" rx="10" fill="rgba(15, 23, 42, 0.9)" stroke={isSliding ? '#ef4444' : '#34d399'} strokeWidth="1.5" />
                <text x="0" y="8" fill={isSliding ? '#ef4444' : '#34d399'} fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  {isSliding ? `SLIDING ACCEL: a = ${slidingAcc.toFixed(2)} m/s²` : 'STATIC EQUILIBRIUM: tan(θ) ≤ μ_s'}
                </text>
              </g>
            </g>
          )}

          {/* Sub-Mode 3: Vehicle Axle Load Transfer */}
          {subMode === 'axle_center_of_mass' && (
            <g transform="translate(140, 160)">
              {/* Ground Line */}
              <line x1="20" y1="360" x2="620" y2="360" stroke="#475569" strokeWidth="3" />

              {/* Vehicle Chassis */}
              <path d="M 60,320 L 140,320 L 180,240 L 440,240 L 520,300 L 580,320 L 580,350 L 60,350 Z" fill="#1e293b" stroke="#f97316" strokeWidth="2.5" />
              {/* Front Wheel */}
              <circle cx="140" cy="355" r="32" fill="#0f172a" stroke="#64748b" strokeWidth="4" />
              {/* Rear Wheel */}
              <circle cx="500" cy="355" r="32" fill="#0f172a" stroke="#64748b" strokeWidth="4" />

              {/* Center of Gravity Marker */}
              <circle cx="310" cy="275" r="14" fill="#f97316" />
              <circle cx="310" cy="275" r="6" fill="#ffffff" />
              <text x="310" y="250" fill="#ffffff" fontSize="16" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                CG (h = 0.55m)
              </text>

              {/* Acceleration Force Vector */}
              {isAccelerating && (
                <g>
                  <line x1="330" y1="275" x2="430" y2="275" stroke="#34d399" strokeWidth="5" markerEnd="url(#arrowUpOrange)" />
                  <text x="445" y="280" fill="#34d399" fontSize="15" fontFamily="monospace" fontWeight="bold">
                    {`a = ${(accelG * gAcc).toFixed(1)} m/s²`}
                  </text>
                </g>
              )}

              {/* Normal Load Vectors */}
              {/* Front Axle Load NF */}
              <line x1="140" y1="440" x2="140" y2={440 - (dynFrontPct * 1.6)} stroke="#38bdf8" strokeWidth="6" markerEnd="url(#arrowUpOrange)" />
              <text x="140" y="470" fill="#38bdf8" fontSize="16" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                {`FRONT: ${dynFrontPct}%`}
              </text>

              {/* Rear Axle Load NR */}
              <line x1="500" y1="440" x2="500" y2={440 - (dynRearPct * 1.6)} stroke="#f97316" strokeWidth="6" markerEnd="url(#arrowUpOrange)" />
              <text x="500" y="470" fill="#f97316" fontSize="16" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                {`REAR: ${dynRearPct}% (+${transferPct.toFixed(0)}%)`}
              </text>
            </g>
          )}
        </svg>
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
          {/* Card 1: Master Equilibrium Equations */}
          <div
            style={{
              backgroundColor: '#111827',
              borderRadius: '18px',
              border: '1.5px solid rgba(249, 115, 22, 0.3)',
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              transform: 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ScaleIcon size={22} color="#f97316" />
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#f97316', fontFamily: 'monospace' }}>
                {subMode === 'inclined_plane_fbd'
                  ? 'COORDINATE DECOMPOSITION & FRICTION'
                  : subMode === 'axle_center_of_mass'
                  ? 'DYNAMIC AXLE LOAD EQUILIBRIUM'
                  : 'STATIC MOMENT & FORCE EQUILIBRIUM'}
              </span>
            </div>

            <div style={{ fontSize: '24px', color: '#ffffff', fontFamily: 'monospace', fontWeight: 'bold' }}>
              {subMode === 'inclined_plane_fbd'
                ? 'ΣFx = mg·sinθ - fs = ma | ΣFy = FN - mg·cosθ = 0'
                : subMode === 'axle_center_of_mass'
                ? 'N_R = (mg·a_cg / L) + (m·a_accel·h / L)'
                : 'Στ_A = 0 ⟹ R_B·L - W₁·x - W_beam·(L/2) = 0'}
            </div>

            <div style={{ fontSize: '16px', color: '#94a3b8', fontFamily: 'monospace' }}>
              {subMode === 'inclined_plane_fbd'
                ? 'Slip occurs as soon as ramp angle satisfies tan(θ) > μ_s.'
                : subMode === 'axle_center_of_mass'
                ? 'Height of center of mass multiplies longitudinal acceleration into squat torque.'
                : 'Supports continuously rebalance vertical and shear forces to prevent beam deflection.'}
            </div>
          </div>

          {/* Card 2: Live Sensor Telemetry */}
          <div
            style={{
              backgroundColor: '#111827',
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
                LOAD CELL TELEMETRY
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '15px', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {subMode === 'inclined_plane_fbd' ? 'NORMAL FORCE FN' : (subMode === 'axle_center_of_mass' ? 'FRONT LOAD' : 'SUPPORT RA')}
                </div>
                <div style={{ fontSize: '26px', color: '#38bdf8', fontFamily: 'monospace', fontWeight: 'bold' }}>
                  {subMode === 'inclined_plane_fbd' ? `${fNormal.toFixed(1)} N` : (subMode === 'axle_center_of_mass' ? `${dynFrontPct}%` : `${reactionRaKn.toFixed(1)} kN`)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '15px', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {subMode === 'inclined_plane_fbd' ? 'DOWN-RAMP F_PAR' : (subMode === 'axle_center_of_mass' ? 'REAR LOAD' : 'SUPPORT RB')}
                </div>
                <div style={{ fontSize: '26px', color: '#f97316', fontFamily: 'monospace', fontWeight: 'bold' }}>
                  {subMode === 'inclined_plane_fbd' ? `${fParallel.toFixed(1)} N` : (subMode === 'axle_center_of_mass' ? `${dynRearPct}%` : `${reactionRbKn.toFixed(1)} kN`)}
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '6px 12px',
                backgroundColor: 'rgba(249, 115, 22, 0.1)',
                borderRadius: '8px',
                fontSize: '15px',
                color: '#f97316',
                fontFamily: 'monospace',
                fontWeight: 'bold',
              }}
            >
              SAFETY FACTOR: 2.85 (EQUILIBRIUM MAINTAINED)
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MechanicsScene;

