import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { ElectricalIcon, SparklesIcon, LightningIcon } from './SvgIcons';

/**
 * ElectricalScene (Engine 3 - Electrical Engineering, Circuit Theorems & Smart Grid OPF)
 *
 * Viewport Breathing:
 *   - 'compact_punch': ~55% height (centered, maxHeight: 960px)
 *   - 'canvas_spotlight': ~72% height (1260px tall) - expands schematic canvas to 920x940
 *   - 'full_dashboard': ~88% height (1540px tall) - full 3-tier layout with live matrix & telemetry
 *
 * 3 Distinct Sub-Modes:
 *   1. 'kvl_kcl_mesh': 2-loop circuit solver with flowing charge particles and node convergence
 *   2. 'thevenin_equivalence': Step-by-step reduction to Vth & Rth with Maximum Power Transfer curve
 *   3. 'smart_grid_opf': Multi-bus power grid, 765 kV transmission congestion & economic dispatch
 */
export const ElectricalScene = ({
  scene,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const layoutDensity = scene?.choreography?.layout_density || scene?.layout_density || 'canvas_spotlight';
  const isSpotlight = layoutDensity === 'canvas_spotlight';
  const isCompact = layoutDensity === 'compact_punch';

  const rawSubMode = scene?.sub_mode || scene?.electrical_mode || scene?.mode || 'kvl_kcl_mesh';
  const textLower = `${scene?.title || ''} ${scene?.display_text || ''} ${scene?.narration || ''} ${scene?.spoken_text || ''}`.toLowerCase();

  let subMode = 'kvl_kcl_mesh';
  if (rawSubMode === 'thevenin_equivalence' || textLower.includes('thevenin') || textLower.includes('equivalent') || textLower.includes('norton') || textLower.includes('max power')) {
    subMode = 'thevenin_equivalence';
  } else if (rawSubMode === 'smart_grid_opf' || textLower.includes('grid') || textLower.includes('power flow') || textLower.includes('transmission') || textLower.includes('economic dispatch') || textLower.includes('duck curve')) {
    subMode = 'smart_grid_opf';
  } else {
    subMode = 'kvl_kcl_mesh';
  }

  const title = scene?.title || (
    subMode === 'thevenin_equivalence'
      ? "Thévenin's Reduction & Maximum Power"
      : subMode === 'smart_grid_opf'
      ? 'Smart Grid Optimal Power Flow'
      : 'Kirchhoff Mesh & Node Analysis'
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

  // Palette (Neon Cyan & Electric Yellow)
  const palette = {
    primary: '#00f0ff',
    secondary: '#eab308',
    accent: '#ef4444',
    background: '#050b14',
    border: 'rgba(0, 240, 255, 0.35)',
    glow: 'rgba(0, 240, 255, 0.22)',
  };

  // Charge particle animation phase for circuits
  const particlePhase1 = (localFrame * 0.12) % 1;
  const particlePhase2 = (localFrame * 0.08) % 1;

  // -------------------------------------------------------------------------
  // Sub-Mode 2: Maximum Power Curve Points
  // -------------------------------------------------------------------------
  const maxPowerCurvePoints = [];
  const vTh = 18.0;
  const rTh = 6.0;
  for (let rl = 1; rl <= 20; rl++) {
    // P_L = (Vth * RL / (Rth + RL))^2 / RL
    const il = vTh / (rTh + rl);
    const pl = il * il * rl;
    const px = 520 + (rl / 20) * 320;
    const py = 360 - (pl / 14.0) * 160;
    maxPowerCurvePoints.push(`${rl === 1 ? 'M' : 'L'} ${px.toFixed(1)} ${py.toFixed(1)}`);
  }

  // -------------------------------------------------------------------------
  // Sub-Mode 3: Smart Grid Thermal Loading & Congestion
  // -------------------------------------------------------------------------
  const line12Thermal = interpolate(progress, [0, 0.5, 1], [78.5, 94.8, 86.2]).toFixed(1);
  const isCongested = parseFloat(line12Thermal) >= 90.0;
  const essDischargeMw = interpolate(progress, [0, 0.5, 1], [20, 85, 60]).toFixed(0);

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
            <ElectricalIcon size={28} color={palette.primary} />
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
              CIRCUITS &amp; POWER SYSTEMS
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(0, 240, 255, 0.16)',
                border: `1.5px solid ${palette.primary}`,
                color: palette.primary,
                borderRadius: '8px',
                padding: '4px 14px',
                fontSize: '16px',
                fontFamily: 'monospace',
                fontWeight: 900,
              }}
            >
              {subMode === 'thevenin_equivalence'
                ? 'R_L = R_th ⟹ P_max'
                : subMode === 'smart_grid_opf'
                ? `LINE 1-2: ${line12Thermal}% THERMAL`
                : 'KCL NODE A • KVL LOOPS'}
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
              subMode === 'thevenin_equivalence'
                ? 'Any linear two-terminal circuit collapses into a single ideal source and resistance.'
                : subMode === 'smart_grid_opf'
                ? 'Optimal power flow routes generation to minimize cost without overloading corridors.'
                : 'Mesh loop currents and nodal conservation laws solve complex circuit topologies.'
            )}
          </div>
        </div>
      </div>

      {/* 2. CENTER ANIMATED ELECTRICAL CANVAS */}
      <div
        style={{
          height: `${canvasHeight}px`,
          backgroundColor: '#040812',
          borderRadius: '22px',
          border: '1.5px solid rgba(0, 240, 255, 0.25)',
          boxShadow: 'inset 0 0 36px rgba(0, 0, 0, 0.85), 0 0 24px rgba(0, 240, 255, 0.12)',
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

          {/* Sub-Mode 1: KVL & KCL 2-Loop Mesh Network */}
          {subMode === 'kvl_kcl_mesh' && (
            <g transform="translate(100, 60)">
              {/* Loop 1 Wires (Left Loop: 0,80 -> 340,80 -> 340,380 -> 0,380) */}
              <rect x="60" y="80" width="280" height="300" fill="none" stroke="#00f0ff" strokeWidth="3" />
              {/* Loop 2 Wires (Right Loop: 340,80 -> 620,80 -> 620,380 -> 340,380) */}
              <rect x="340" y="80" width="280" height="300" fill="none" stroke="#eab308" strokeWidth="3" />

              {/* Source V1 (Left Branch) */}
              <g transform="translate(60, 230)">
                <circle cx="0" cy="0" r="26" fill="#0d1b2a" stroke="#00f0ff" strokeWidth="2.5" />
                <text x="0" y="-4" fill="#00f0ff" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">+</text>
                <text x="0" y="14" fill="#00f0ff" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">-</text>
                <text x="-40" y="5" fill="#00f0ff" fontSize="16" fontFamily="monospace" fontWeight="bold" textAnchor="end">V₁ = 24V</text>
              </g>

              {/* Resistor R1 (Top Left Branch) */}
              <g transform="translate(200, 80)">
                <rect x="-35" y="-12" width="70" height="24" fill="#1e293b" stroke="#00f0ff" strokeWidth="2" />
                <text x="0" y="6" fill="#ffffff" fontSize="14" fontFamily="monospace" fontWeight="bold" textAnchor="middle">R₁ = 4Ω</text>
              </g>

              {/* Shared Central Branch: Node A and Resistor R2 */}
              {/* Node A (Principal Node) */}
              <circle cx="340" cy="80" r="8" fill="#ff4d4f" />
              <rect x="300" y="40" width="80" height="28" rx="6" fill="#1e293b" stroke="#ff4d4f" strokeWidth="1.5" />
              <text x="340" y="60" fill="#ff4d4f" fontSize="14" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                NODE V_A
              </text>

              {/* Resistor R2 (Shared Branch) */}
              <g transform="translate(340, 230)">
                <rect x="-14" y="-35" width="28" height="70" fill="#1e293b" stroke="#ffffff" strokeWidth="2" />
                <text x="24" y="5" fill="#ffffff" fontSize="14" fontFamily="monospace" fontWeight="bold">R₂ = 6Ω</text>
                {/* Branch Current I_3 */}
                <text x="-24" y="5" fill="#34d399" fontSize="14" fontFamily="monospace" fontWeight="bold" textAnchor="end">
                  I₂ = I₁ - I₂
                </text>
              </g>

              {/* Resistor R3 (Top Right Branch) */}
              <g transform="translate(480, 80)">
                <rect x="-35" y="-12" width="70" height="24" fill="#1e293b" stroke="#eab308" strokeWidth="2" />
                <text x="0" y="6" fill="#ffffff" fontSize="14" fontFamily="monospace" fontWeight="bold" textAnchor="middle">R₃ = 8Ω</text>
              </g>

              {/* Source V2 (Right Branch) */}
              <g transform="translate(620, 230)">
                <circle cx="0" cy="0" r="26" fill="#0d1b2a" stroke="#eab308" strokeWidth="2.5" />
                <text x="0" y="-4" fill="#eab308" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">+</text>
                <text x="0" y="14" fill="#eab308" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">-</text>
                <text x="36" y="5" fill="#eab308" fontSize="16" fontFamily="monospace" fontWeight="bold">V₂ = 12V</text>
              </g>

              {/* Node B / Ground */}
              <circle cx="340" cy="380" r="8" fill="#64748b" />
              <line x1="330" y1="390" x2="350" y2="390" stroke="#64748b" strokeWidth="2.5" />
              <line x1="334" y1="395" x2="346" y2="395" stroke="#64748b" strokeWidth="2" />
              <line x1="338" y1="400" x2="342" y2="400" stroke="#64748b" strokeWidth="1.5" />

              {/* Circulating Loop 1 Current Vector Arrow */}
              <g transform="translate(200, 230)">
                <path d="M -30,-30 A 45 45 0 1 1 30,30" fill="none" stroke="#00f0ff" strokeWidth="3" strokeDasharray="6 4" />
                <polygon points="30,30 20,24 24,18" fill="#00f0ff" />
                <text x="0" y="5" fill="#00f0ff" fontSize="16" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  Loop I₁ = 1.8A
                </text>
              </g>

              {/* Circulating Loop 2 Current Vector Arrow */}
              <g transform="translate(480, 230)">
                <path d="M -30,-30 A 45 45 0 1 1 30,30" fill="none" stroke="#eab308" strokeWidth="3" strokeDasharray="6 4" />
                <polygon points="30,30 20,24 24,18" fill="#eab308" />
                <text x="0" y="5" fill="#eab308" fontSize="16" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  Loop I₂ = 0.6A
                </text>
              </g>

              {/* Live Flowing Charge Particles on Wires */}
              <circle cx={60 + particlePhase1 * 280} cy="80" r="5" fill="#ffffff" stroke="#00f0ff" strokeWidth="1.5" />
              <circle cx="340" cy={80 + particlePhase1 * 300} r="5" fill="#ffffff" stroke="#00f0ff" strokeWidth="1.5" />
              <circle cx={620 - particlePhase2 * 280} cy="80" r="5" fill="#ffffff" stroke="#00f0ff" strokeWidth="1.5" />
            </g>
          )}

          {/* Sub-Mode 2: Thévenin Equivalence & Maximum Power */}
          {subMode === 'thevenin_equivalence' && (
            <g transform="translate(50, 60)">
              {/* Left Side: Thévenin Equivalent Circuit Box */}
              <g>
                <text x="220" y="40" fill="#00f0ff" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  THÉVENIN 2-TERMINAL EQUIVALENT
                </text>
                <rect x="60" y="70" width="320" height="260" rx="14" fill="rgba(15, 23, 42, 0.85)" stroke="#00f0ff" strokeWidth="2" strokeDasharray="8 6" />

                {/* Vth Source */}
                <circle cx="110" cy="200" r="26" fill="#0d1b2a" stroke="#00f0ff" strokeWidth="2.5" />
                <text x="110" y="196" fill="#00f0ff" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">+</text>
                <text x="110" y="214" fill="#00f0ff" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">-</text>
                <text x="110" y="246" fill="#00f0ff" fontSize="15" fontFamily="monospace" textAnchor="middle">V_th = 18V</text>

                {/* Series Resistor Rth */}
                <rect x="200" y="90" width="60" height="24" fill="#1e293b" stroke="#00f0ff" strokeWidth="2" />
                <text x="230" y="106" fill="#ffffff" fontSize="14" fontFamily="monospace" textAnchor="middle">R_th = 6Ω</text>

                {/* Wire connecting Vth to Rth */}
                <line x1="110" y1="174" x2="110" y2="102" stroke="#00f0ff" strokeWidth="2.5" />
                <line x1="110" y1="102" x2="200" y2="102" stroke="#00f0ff" strokeWidth="2.5" />
                <line x1="260" y1="102" x2="340" y2="102" stroke="#00f0ff" strokeWidth="2.5" />
                {/* Terminal A */}
                <circle cx="340" cy="102" r="6" fill="#eab308" />
                <text x="356" y="106" fill="#eab308" fontSize="16" fontFamily="monospace" fontWeight="bold">A</text>

                {/* Return Wire */}
                <line x1="110" y1="226" x2="110" y2="290" stroke="#00f0ff" strokeWidth="2.5" />
                <line x1="110" y1="290" x2="340" y2="290" stroke="#00f0ff" strokeWidth="2.5" />
                {/* Terminal B */}
                <circle cx="340" cy="290" r="6" fill="#eab308" />
                <text x="356" y="296" fill="#eab308" fontSize="16" fontFamily="monospace" fontWeight="bold">B</text>

                {/* Variable Load Resistor RL */}
                <line x1="340" y1="102" x2="400" y2="102" stroke="#eab308" strokeWidth="2.5" />
                <line x1="400" y1="102" x2="400" y2="160" stroke="#eab308" strokeWidth="2.5" />
                <rect x="388" y="160" width="24" height="70" fill="#1e293b" stroke="#eab308" strokeWidth="2" />
                <text x="424" y="200" fill="#eab308" fontSize="15" fontFamily="monospace" fontWeight="bold">R_L = 6Ω</text>
                <line x1="400" y1="230" x2="400" y2="290" stroke="#eab308" strokeWidth="2.5" />
                <line x1="400" y1="290" x2="340" y2="290" stroke="#eab308" strokeWidth="2.5" />
              </g>

              {/* Right Side: Maximum Power Transfer Curve */}
              <g transform="translate(20, 0)">
                <text x="680" y="40" fill="#34d399" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  MAXIMUM POWER TRANSFER THEOREM
                </text>
                <line x1="520" y1="360" x2="840" y2="360" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                <line x1="520" y1="140" x2="520" y2="360" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />

                {/* Plot Curve */}
                <path d={maxPowerCurvePoints.join(' ')} fill="none" stroke="#34d399" strokeWidth="3.5" />

                {/* Peak Point RL = Rth = 6 Ohm */}
                <circle cx={520 + (6 / 20) * 320} cy={360 - (13.5 / 14.0) * 160} r="7" fill="#ffffff" stroke="#34d399" strokeWidth="2.5" />
                <rect x={520 + (6 / 20) * 320 - 70} y={360 - (13.5 / 14.0) * 160 - 45} width="140" height="32" rx="6" fill="#1e293b" stroke="#34d399" strokeWidth="1.5" />
                <text x={520 + (6 / 20) * 320} y={360 - (13.5 / 14.0) * 160 - 24} fill="#34d399" fontSize="14" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  Peak P = 13.5W
                </text>
                <text x="680" y="390" fill="#94a3b8" fontSize="15" fontFamily="monospace" textAnchor="middle">
                  Matched Load Condition: R_L = R_th (50% Efficiency)
                </text>
              </g>
            </g>
          )}

          {/* Sub-Mode 3: Smart Grid OPF & Congestion Management */}
          {subMode === 'smart_grid_opf' && (
            <g transform="translate(60, 40)">
              {/* Bus 1: Nuclear Baseload (Top Left) */}
              <g transform="translate(100, 100)">
                <circle cx="0" cy="0" r="38" fill="#1e293b" stroke="#00f0ff" strokeWidth="3" />
                <text x="0" y="-8" fill="#00f0ff" fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="middle">BUS 1</text>
                <text x="0" y="14" fill="#ffffff" fontSize="13" fontFamily="monospace" textAnchor="middle">450 MW</text>
                <text x="0" y="55" fill="#00f0ff" fontSize="14" fontFamily="monospace" textAnchor="middle">Nuclear Base</text>
              </g>

              {/* Bus 2: Solar/Wind + Battery ESS (Top Right) */}
              <g transform="translate(660, 100)">
                <circle cx="0" cy="0" r="38" fill="#1e293b" stroke="#34d399" strokeWidth="3" />
                <text x="0" y="-8" fill="#34d399" fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="middle">BUS 2</text>
                <text x="0" y="14" fill="#ffffff" fontSize="13" fontFamily="monospace" textAnchor="middle">310 MW</text>
                <text x="0" y="55" fill="#34d399" fontSize="14" fontFamily="monospace" textAnchor="middle">Renewables+ESS</text>
              </g>

              {/* 765 kV Transmission Line 1-2 with live thermal load bar */}
              <line x1="138" y1="100" x2="622" y2="100" stroke={isCongested ? '#ef4444' : '#00f0ff'} strokeWidth="5" />
              <rect x="300" y="70" width="160" height="40" rx="8" fill="#0f172a" stroke={isCongested ? '#ef4444' : '#00f0ff'} strokeWidth="1.5" />
              <text x="380" y="95" fill={isCongested ? '#ef4444' : '#00f0ff'} fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                {`Line 1-2: ${line12Thermal}%`}
              </text>

              {/* Bus 3: Industrial Substation (Bottom Left) */}
              <g transform="translate(100, 380)">
                <circle cx="0" cy="0" r="38" fill="#1e293b" stroke="#eab308" strokeWidth="3" />
                <text x="0" y="-8" fill="#eab308" fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="middle">BUS 3</text>
                <text x="0" y="14" fill="#ffffff" fontSize="13" fontFamily="monospace" textAnchor="middle">340 MW</text>
                <text x="0" y="55" fill="#eab308" fontSize="14" fontFamily="monospace" textAnchor="middle">Heavy Industry</text>
              </g>

              {/* Bus 4: Metro City Center (Bottom Right) */}
              <g transform="translate(660, 380)">
                <circle cx="0" cy="0" r="38" fill="#1e293b" stroke="#38bdf8" strokeWidth="3" />
                <text x="0" y="-8" fill="#38bdf8" fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="middle">BUS 4</text>
                <text x="0" y="14" fill="#ffffff" fontSize="13" fontFamily="monospace" textAnchor="middle">420 MW</text>
                <text x="0" y="55" fill="#38bdf8" fontSize="14" fontFamily="monospace" textAnchor="middle">Metro Demand</text>
              </g>

              {/* Cross Transmission Interconnects */}
              <line x1="100" y1="138" x2="100" y2="342" stroke="#64748b" strokeWidth="3.5" />
              <line x1="660" y1="138" x2="660" y2="342" stroke="#64748b" strokeWidth="3.5" />
              <line x1="138" y1="380" x2="622" y2="380" stroke="#64748b" strokeWidth="3.5" />

              {/* Central Optimization Telemetry HUD */}
              <g transform="translate(380, 240)">
                <rect x="-140" y="-45" width="280" height="90" rx="12" fill="rgba(15, 23, 42, 0.9)" stroke="#00f0ff" strokeWidth="1.5" />
                <text x="0" y="-18" fill="#00f0ff" fontSize="15" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                  AC OPTIMAL POWER FLOW (OPF)
                </text>
                <text x="0" y="8" fill="#ffffff" fontSize="14" fontFamily="monospace" textAnchor="middle">
                  Marginal Cost λ = $34.50/MWh
                </text>
                <text x="0" y="30" fill="#34d399" fontSize="14" fontFamily="monospace" textAnchor="middle">
                  {`Battery Peak Shaving: ${essDischargeMw} MW`}
                </text>
              </g>
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
          {/* Card 1: Master Circuit Equations */}
          <div
            style={{
              backgroundColor: '#0a101f',
              borderRadius: '18px',
              border: '1.5px solid rgba(0, 240, 255, 0.3)',
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              transform: 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <SparklesIcon size={22} color="#00f0ff" />
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#00f0ff', fontFamily: 'monospace' }}>
                {subMode === 'thevenin_equivalence'
                  ? 'MAXIMUM POWER & THEVENIN REDUCTION'
                  : subMode === 'smart_grid_opf'
                  ? 'EQUAL INCREMENTAL COST & OPF'
                  : 'KIRCHHOFF CURRENT & VOLTAGE LAWS'}
              </span>
            </div>

            <div style={{ fontSize: '24px', color: '#ffffff', fontFamily: 'monospace', fontWeight: 'bold' }}>
              {subMode === 'thevenin_equivalence'
                ? 'P_max = V_th² / (4·R_th)  at  R_L = R_th'
                : subMode === 'smart_grid_opf'
                ? '∂C₁/∂P_G1 = ∂C₂/∂P_G2 = λ (Equal Incremental Cost)'
                : 'ΣI_in = ΣI_out  |  ΣV_loop = 0'}
            </div>

            <div style={{ fontSize: '16px', color: '#94a3b8', fontFamily: 'monospace' }}>
              {subMode === 'thevenin_equivalence'
                ? 'Open-circuit voltage determines Vth; zeroing sources yields equivalent Rth.'
                : subMode === 'smart_grid_opf'
                ? 'Constrained optimization enforces 765 kV line thermal limits and 60 Hz sync.'
                : 'Node voltages satisfy conductance matrix [G][V] = [I] without numerical drift.'}
            </div>
          </div>

          {/* Card 2: Live Sensor Telemetry */}
          <div
            style={{
              backgroundColor: '#0a101f',
              borderRadius: '18px',
              border: '1.5px solid rgba(234, 179, 8, 0.3)',
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              transform: 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <LightningIcon size={22} color="#eab308" />
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#eab308', fontFamily: 'monospace' }}>
                GRID SCADA TELEMETRY
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '15px', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {subMode === 'thevenin_equivalence' ? 'OPEN-CIRCUIT V_TH' : (subMode === 'smart_grid_opf' ? 'GRID FREQ' : 'NODE V_A')}
                </div>
                <div style={{ fontSize: '26px', color: '#00f0ff', fontFamily: 'monospace', fontWeight: 'bold' }}>
                  {subMode === 'thevenin_equivalence' ? '18.0 V' : (subMode === 'smart_grid_opf' ? '60.00 Hz' : '16.8 V')}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '15px', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {subMode === 'thevenin_equivalence' ? 'R_TH IMPEDANCE' : (subMode === 'smart_grid_opf' ? 'LINE 1-2' : 'LOOP CURRENT I₁')}
                </div>
                <div style={{ fontSize: '26px', color: '#eab308', fontFamily: 'monospace', fontWeight: 'bold' }}>
                  {subMode === 'thevenin_equivalence' ? '6.0 Ω' : (subMode === 'smart_grid_opf' ? `${line12Thermal}%` : '1.80 A')}
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '6px 12px',
                backgroundColor: 'rgba(0, 240, 255, 0.1)',
                borderRadius: '8px',
                fontSize: '15px',
                color: '#00f0ff',
                fontFamily: 'monospace',
                fontWeight: 'bold',
              }}
            >
              STATUS: CONTINUOUS POWER BALANCE (ΣP_gen = ΣP_load + P_loss)
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ElectricalScene;

