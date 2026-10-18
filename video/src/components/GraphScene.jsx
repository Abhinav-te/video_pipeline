import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { GraphIcon, SparklesIcon } from './SvgIcons';

/**
 * Generates an SVG path string for a mathematical curve sampled across x_domain.
 */
function generateCurvePath(fnType, xMin, xMax, steps, toScreenX, toScreenY) {
  const points = [];
  const dx = (xMax - xMin) / steps;

  for (let i = 0; i <= steps; i++) {
    const x = xMin + i * dx;
    let y = 0;

    if (fnType === 'sin' || fnType === 'sine') {
      y = Math.sin(x) * 2.2;
    } else if (fnType === 'cubic') {
      y = (x * x * x) / 5;
    } else if (fnType === 'gaussian') {
      y = Math.exp(-x * x / 2) * 3.5;
    } else {
      // Default: parabolic quadratic
      y = (x * x) / 2.5;
    }

    const sx = toScreenX(x);
    const sy = toScreenY(y);
    points.push(`${i === 0 ? 'M' : 'L'} ${Math.round(sx * 10) / 10} ${Math.round(sy * 10) / 10}`);
  }

  return points.join(' ');
}

/**
 * Generates an SVG path string for an SN2 1-step concerted reaction coordinate.
 */
function generateSN2Path(toScreenX, toScreenY) {
  const points = [];
  const steps = 60;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = -4.5 + t * 9.0;
    const bell = Math.exp(-Math.pow(x / 1.6, 2));
    const baseline = 0.8 - 0.5 * t;
    const y = baseline + 3.2 * bell;
    const sx = toScreenX(x);
    const sy = toScreenY(y);
    points.push(`${i === 0 ? 'M' : 'L'} ${Math.round(sx * 10) / 10} ${Math.round(sy * 10) / 10}`);
  }
  return points.join(' ');
}

/**
 * Generates an SVG path string for an SN1 2-step reaction coordinate with intermediate valley.
 */
function generateSN1Path(toScreenX, toScreenY) {
  const points = [];
  const steps = 60;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = -4.5 + t * 9.0;
    const peak1 = 3.6 * Math.exp(-Math.pow((x + 1.8) / 1.1, 2));
    const peak2 = 2.4 * Math.exp(-Math.pow((x - 2.0) / 1.0, 2));
    const valley = 1.6 * Math.exp(-Math.pow((x - 0.1) / 1.2, 2));
    const baseline = 0.8 - 0.5 * t;
    const y = baseline + peak1 + peak2 - (x > -1.2 && x < 1.4 ? valley * 0.45 : 0);
    const sx = toScreenX(x);
    const sy = toScreenY(y);
    points.push(`${i === 0 ? 'M' : 'L'} ${Math.round(sx * 10) / 10} ${Math.round(sy * 10) / 10}`);
  }
  return points.join(' ');
}

/**
 * Generates an SVG path string for Electrical Maximum Power Transfer curve.
 */
function generatePowerTransferPath(toScreenX, toScreenY) {
  const points = [];
  const steps = 60;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const rl = 0.5 + t * 19.5;
    const rth = 6.0;
    const pl = (4 * 3.8 * (rl / rth)) / Math.pow(1 + rl / rth, 2);
    const x = -5 + t * 10;
    const sx = toScreenX(x);
    const sy = toScreenY(pl);
    points.push(`${i === 0 ? 'M' : 'L'} ${Math.round(sx * 10) / 10} ${Math.round(sy * 10) / 10}`);
  }
  return points.join(' ');
}

function generateMarginalCostPath(toScreenX, toScreenY) {
  const points = [];
  const steps = 40;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = -5 + t * 10;
    const y = 0.8 + 0.32 * (x + 5);
    const sx = toScreenX(x);
    const sy = toScreenY(y);
    points.push(`${i === 0 ? 'M' : 'L'} ${Math.round(sx * 10) / 10} ${Math.round(sy * 10) / 10}`);
  }
  return points.join(' ');
}

/**
 * Generates SVG path strings for Mechanics Shear step and Bending Moment parabola.
 */
function generateShearStepPath(toScreenX, toScreenY) {
  const p1 = `${toScreenX(-5)} ${toScreenY(2.6)}`;
  const p2 = `${toScreenX(0)} ${toScreenY(2.6)}`;
  const p3 = `${toScreenX(0)} ${toScreenY(-2.6)}`;
  const p4 = `${toScreenX(5)} ${toScreenY(-2.6)}`;
  return `M ${p1} L ${p2} L ${p3} L ${p4}`;
}

function generateBendingMomentPath(toScreenX, toScreenY) {
  const points = [];
  const steps = 60;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = -5 + t * 10;
    const y = 3.6 - (x * x) * 0.14;
    const sx = toScreenX(x);
    const sy = toScreenY(y);
    points.push(`${i === 0 ? 'M' : 'L'} ${Math.round(sx * 10) / 10} ${Math.round(sy * 10) / 10}`);
  }
  return points.join(' ');
}

/**
 * Generates an SVG path string for Quantum barrier penetration wavepacket.
 */
function generateQuantumWavePath(toScreenX, toScreenY) {
  const points = [];
  const steps = 80;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = -5 + t * 10;
    let y = 0;
    if (x < -1) {
      y = 1.8 + Math.sin(x * 3.5) * 1.5;
    } else if (x <= 1) {
      const decay = Math.exp(-1.6 * (x + 1));
      y = 1.8 + 1.5 * decay;
    } else {
      y = 1.8 + Math.sin(x * 3.5) * 0.45;
    }
    const sx = toScreenX(x);
    const sy = toScreenY(y);
    points.push(`${i === 0 ? 'M' : 'L'} ${Math.round(sx * 10) / 10} ${Math.round(sy * 10) / 10}`);
  }
  return points.join(' ');
}

/**
 * GraphScene (Phase 12 - True Multi-Domain 2D Visualizer & Zero Calculus Fallbacks)
 * Automatically renders domain-accurate curves, telemetry, and decision cards across
 * Electrical, Mechanics, Quantum Physics, Chemistry, and Math.
 */
export const GraphScene = ({
  scene,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const choreography = scene?.choreography || {};
  const graphChoreo = choreography.graph || {};

  const drawStart = graphChoreo.draw_start_frame || (sceneStartFrame + 4);
  const drawEnd = graphChoreo.draw_end_frame || (sceneStartFrame + 34);
  const emphasisFrame = graphChoreo.emphasis_frame || (sceneStartFrame + 25);
  const tangentFrame = graphChoreo.tangent_frame || (emphasisFrame + 8);

  const graphData = scene?.graph_data || {};
  const domain = (
    graphData.domain ||
    scene?.domain ||
    scene?.subject ||
    scene?.choreography?.domain ||
    ''
  ).toLowerCase();

  // Curve resolution & domain checks
  const rawFunctions = scene?.functions || scene?.curves || graphData.curves || [];
  const firstFn = Array.isArray(rawFunctions) && rawFunctions.length > 0 ? rawFunctions[0] : rawFunctions;
  const fnLabel = typeof firstFn === 'string'
    ? firstFn
    : (firstFn?.label || firstFn?.fn || 'y = f(x) = x² / 2.5');

  const fnLower = (typeof firstFn === 'string' ? firstFn : (firstFn?.fn || '')).toLowerCase();
  const isEnergyProfile = fnLower.includes('energy') || fnLower.includes('sn1') || fnLower.includes('sn2') || domain.includes('chem');
  const isElectrical = domain.includes('electr') || fnLower.includes('power') || fnLower.includes('thevenin') || fnLower.includes('marginal');
  const isMechanics = domain.includes('mechanic') || fnLower.includes('shear') || fnLower.includes('moment') || fnLower.includes('beam');
  const isQuantum = domain.includes('quantum') || fnLower.includes('tunnel') || fnLower.includes('wave') || fnLower.includes('schrodinger');
  const isChemistry = isEnergyProfile;

  const palette = choreography.palette || {
    primary: isElectrical ? '#00f0ff' : isQuantum ? '#c084fc' : isChemistry ? '#38bdf8' : isMechanics ? '#34d399' : '#79c0ff',
    secondary: isElectrical ? '#eab308' : isQuantum ? '#38bdf8' : isChemistry ? '#f59e0b' : isMechanics ? '#f59e0b' : '#d2a8ff',
    accent: '#56d364',
    background: '#0a101b',
    border: isElectrical ? 'rgba(0, 240, 255, 0.35)' : isQuantum ? 'rgba(192, 132, 252, 0.35)' : 'rgba(121, 192, 255, 0.35)',
    glow: isElectrical ? 'rgba(0, 240, 255, 0.2)' : isQuantum ? 'rgba(192, 132, 252, 0.2)' : 'rgba(121, 192, 255, 0.2)',
  };

  const layoutDensity = scene?.choreography?.layout_density || scene?.layout_density || 'canvas_spotlight';
  const isSpotlight = layoutDensity === 'canvas_spotlight';

  // Dimensions
  const canvasWidth = 896;
  const canvasHeight = isSpotlight ? 960 : 820;
  const originX = canvasWidth / 2;
  const originY = canvasHeight / 2 + (isSpotlight ? 40 : 60);
  const scaleUnit = 60;

  const toScreenX = (x) => originX + x * scaleUnit;
  const toScreenY = (y) => originY - y * scaleUnit;

  let fnType = 'quadratic';
  if (fnLower.includes('sin')) fnType = 'sin';
  else if (fnLower.includes('cubic') || fnLower.includes('x^3')) fnType = 'cubic';
  else if (fnLower.includes('gauss') || fnLower.includes('exp')) fnType = 'gaussian';

  const curvePath = generateCurvePath(fnType, -6, 6, 80, toScreenX, toScreenY);
  const sn2Path = generateSN2Path(toScreenX, toScreenY);
  const sn1Path = generateSN1Path(toScreenX, toScreenY);
  const powerPath = generatePowerTransferPath(toScreenX, toScreenY);
  const marginalPath = generateMarginalCostPath(toScreenX, toScreenY);
  const shearPath = generateShearStepPath(toScreenX, toScreenY);
  const momentPath = generateBendingMomentPath(toScreenX, toScreenY);
  const quantumPath = generateQuantumWavePath(toScreenX, toScreenY);

  const pathLength = 1500;
  const drawProgress = interpolate(
    frame,
    [drawStart, drawEnd],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
  const strokeDashoffset = Math.round(pathLength * (1 - drawProgress));

  const isCriticalPointActive = frame >= emphasisFrame;
  const isTangentActive = frame >= tangentFrame;

  // Domain-Aware Header & Eyebrow
  const headerEyebrow = graphData.header || scene?.category_tag || (
    isElectrical ? 'POWER SYSTEMS • LOAD & DISPATCH CURVES' :
    isMechanics ? 'STRUCTURAL ANALYSIS • INTERNAL FORCES' :
    isQuantum ? 'QUANTUM WAVE MECHANICS • PROBABILITY DENSITY' :
    isChemistry ? 'REACTION COORDINATE & THERMODYNAMICS' :
    'CALCULUS & ANALYTIC GEOMETRY'
  );

  const formulaPill = graphData.critical_point || scene?.critical_point_label || (
    isElectrical ? 'P_max = V_th² / (4·R_th)' :
    isMechanics ? 'V(x) = -w·x • M(x) = -w·x²/2' :
    isQuantum ? 'T = e^(-2κL) • Δx·Δp ≥ ℏ/2' :
    isChemistry ? 'ΔG‡ & ACTIVATION BARRIER' :
    fnLabel
  );

  const title = graphData.title || scene?.title || (
    isElectrical ? 'Maximum Power Transfer & Marginal Cost' :
    isMechanics ? 'Shear Force (V) & Bending Moment (M) Diagram' :
    isQuantum ? 'Barrier Penetration & Uncertainty Envelope' :
    isChemistry ? 'Energy Landscape: SN2 vs SN1' :
    '2D Function Graph'
  );

  const subtitle = scene?.spoken_text || scene?.narration || (
    isElectrical ? 'Load power reaches global maximum when load resistance matches Thévenin resistance.' :
    isMechanics ? 'Internal shear force drop equals concentrated load while bending moment peaks at mid-span.' :
    isQuantum ? 'Wavepacket decays exponentially inside potential barrier with finite transmission coefficient.' :
    isChemistry ? 'Comparing concerted 1-peak SN2 curve against stepwise 2-peak SN1 curve.' :
    'Continuous real-valued function visualization.'
  );

  // Domain Breakdown Card Defaults (Zero Calculus Fallbacks)
  const defaultBreakdown = isElectrical ? {
    title: 'MAXIMUM POWER TRANSFER THEOREM',
    left_label: 'MATCHED LOAD POWER',
    left_value: 'P_max = V_th² / (4·R_th)',
    right_label: 'THEORETICAL EFFICIENCY',
    right_value: 'η = 50% at Peak Transfer',
    footer: 'R_L = R_th ensures maximum power delivery across high-voltage corridors',
    tag: 'MAX EFFICIENCY: R_L = R_th',
  } : isMechanics ? {
    title: 'INTERNAL SHEAR & MOMENT EQUILIBRIUM',
    left_label: 'MAX SHEAR FORCE',
    left_value: 'V_max = w·L / 2',
    right_label: 'MAX BENDING MOMENT',
    right_value: 'M_max = w·L² / 8',
    footer: 'Governed by dM/dx = V(x) and dV/dx = -w(x) equilibrium differential',
    tag: 'EQUILIBRIUM: dM/dx = V(x)',
  } : isQuantum ? {
    title: 'TUNNELING TRANSMISSION COEFFICIENT',
    left_label: 'TRANSMISSION PROBABILITY',
    left_value: 'T ≈ e^(-2κL)',
    right_label: 'UNCERTAINTY PRODUCT',
    right_value: 'Δx·Δp ≥ ℏ/2',
    footer: 'Wavefunction evanescent decay through classically forbidden barrier V₀',
    tag: 'QUANTUM LEAKAGE: E < V₀',
  } : isChemistry ? {
    title: 'FREE ENERGY OF ACTIVATION',
    left_label: 'SN2 CONCERTED BARRIER',
    left_value: 'ΔG‡_concerted = 75 kJ/mol',
    right_label: 'SN1 CARBOCATION INTERMEDIATE',
    right_value: 'ΔG‡_1 > ΔG‡_2 (Rate Limiting)',
    footer: 'Concerted single transition state vs 2-step carbocation valley',
    tag: 'KINETIC VS THERMODYNAMIC',
  } : {
    title: 'FIRST DERIVATIVE & CRITICAL EXTREMA',
    left_label: "FIRST DERIVATIVE f'(x)",
    left_value: "f'(x) = 0.80x = 0",
    right_label: 'SECOND DERIVATIVE TEST',
    right_value: "f''(x) = 0.80 > 0 (Minimum)",
    footer: 'Domain: (-∞, +∞) • Range: [0, +∞)',
    tag: 'GLOBAL MINIMUM',
  };

  const breakdown = graphData.breakdown || scene?.breakdown || defaultBreakdown;

  return (
    <div
      style={{
        backgroundColor: palette.background,
        borderRadius: '28px',
        border: `1.5px solid ${palette.border}`,
        boxShadow: `0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 40px ${palette.glow}`,
        width: '960px',
        height: isSpotlight ? '1260px' : '1540px',
        minHeight: isSpotlight ? '1260px' : '1540px',
        overflow: 'hidden',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        position: 'relative',
        padding: '32px 32px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      {/* 1. TOP EDITORIAL HEADER (200px) */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          height: '200px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <GraphIcon size={28} color={palette.primary} />
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
              {headerEyebrow}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: `1.5px solid ${palette.primary}`,
                color: palette.primary,
                borderRadius: '8px',
                padding: '4px 14px',
                fontSize: '17px',
                fontFamily: 'monospace',
                fontWeight: 900,
              }}
            >
              {formulaPill}
            </span>
            {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
          </div>
        </div>

        <div>
          <div
            style={{
              fontSize: '48px',
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

      {/* 2. CENTER 2D CARTESIAN CANVAS (840px / 960px) */}
      <div
        style={{
          height: isSpotlight ? '960px' : '840px',
          backgroundColor: '#0a101b',
          borderRadius: '22px',
          border: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxShadow: 'inset 0 0 36px rgba(0, 0, 0, 0.8), 0 0 24px rgba(0, 240, 255, 0.08)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'hidden',
          boxSizing: 'border-box',
          position: 'relative',
        }}
      >
        <svg
          width={canvasWidth}
          height={canvasHeight}
          viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
          style={{ width: '100%', height: '100%' }}
        >
          {/* Subtle Grid Lines */}
          {[-5, -4, -3, -2, -1, 1, 2, 3, 4, 5].map((u) => {
            const sx = toScreenX(u);
            return (
              <line
                key={`gx-${u}`}
                x1={sx}
                y1="30"
                x2={sx}
                y2={canvasHeight - 30}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeWidth="1.5"
              />
            );
          })}
          {[-2, -1, 1, 2, 3, 4, 5, 6].map((u) => {
            const sy = toScreenY(u);
            return (
              <line
                key={`gy-${u}`}
                x1="30"
                y1={sy}
                x2={canvasWidth - 30}
                y2={sy}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeWidth="1.5"
              />
            );
          })}

          {/* X Axis */}
          <line
            x1="30"
            y1={originY}
            x2={canvasWidth - 30}
            y2={originY}
            stroke="rgba(255, 255, 255, 0.4)"
            strokeWidth="2.5"
          />
          {/* Y Axis */}
          <line
            x1={originX}
            y1="30"
            x2={originX}
            y2={canvasHeight - 30}
            stroke="rgba(255, 255, 255, 0.4)"
            strokeWidth="2.5"
          />

          {isElectrical ? (
            /* Electrical Power & Cost Canvas */
            <g>
              <text x={originX} y={originY + 45} fill="#00f0ff" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                Load Resistance R_L (Ω) →
              </text>
              <text x="90" y="55" fill="#eab308" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="start">
                Power P_L (W) &amp; $/MWh ↑
              </text>

              {/* Legend Box at Top Right */}
              <g transform={`translate(${canvasWidth - 360}, 40)`}>
                <rect x="0" y="0" width="330" height="90" rx="12" fill="rgba(15, 23, 42, 0.85)" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.5" />
                <line x1="20" y1="30" x2="60" y2="30" stroke="#00f0ff" strokeWidth="4.5" />
                <circle cx="40" cy="30" r="5" fill="#00f0ff" />
                <text x="75" y="36" fill="#00f0ff" fontSize="17" fontFamily="monospace" fontWeight="bold">
                  P_L(R_L) Power Transfer
                </text>
                <line x1="20" y1="65" x2="60" y2="65" stroke="#eab308" strokeWidth="4.5" />
                <circle cx="40" cy="65" r="5" fill="#eab308" />
                <text x="75" y="71" fill="#eab308" fontSize="17" fontFamily="monospace" fontWeight="bold">
                  Marginal Cost λ ($/MWh)
                </text>
              </g>

              {/* Power Transfer Curve */}
              <path
                d={powerPath}
                fill="none"
                stroke="#00f0ff"
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={pathLength}
                strokeDashoffset={strokeDashoffset}
              />

              {/* Marginal Cost Line */}
              <path
                d={marginalPath}
                fill="none"
                stroke="#eab308"
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray="8 6"
              />

              {/* Peak Power Point */}
              {isCriticalPointActive && (
                <g transform={`translate(${originX}, ${toScreenY(3.8)})`}>
                  <circle cx="0" cy="0" r="12" fill="#00f0ff" stroke="#ffffff" strokeWidth="3" />
                  <rect x="-130" y="-50" width="260" height="38" rx="8" fill="#050b14" stroke="#00f0ff" strokeWidth="1.5" />
                  <text x="0" y="-25" fill="#00f0ff" fontSize="16" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                    Peak Power: R_L = R_th (6.0 Ω)
                  </text>
                </g>
              )}
            </g>
          ) : isMechanics ? (
            /* Mechanics Shear & Moment Canvas */
            <g>
              <text x={originX} y={originY + 45} fill="#38bdf8" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                Beam Position x / L →
              </text>
              <text x="90" y="55" fill="#34d399" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="start">
                Internal Forces V(x), M(x) ↑
              </text>

              <g transform={`translate(${canvasWidth - 360}, 40)`}>
                <rect x="0" y="0" width="330" height="90" rx="12" fill="rgba(15, 23, 42, 0.85)" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.5" />
                <line x1="20" y1="30" x2="60" y2="30" stroke="#38bdf8" strokeWidth="4.5" />
                <circle cx="40" cy="30" r="5" fill="#38bdf8" />
                <text x="75" y="36" fill="#38bdf8" fontSize="17" fontFamily="monospace" fontWeight="bold">
                  Shear Step V(x)
                </text>
                <line x1="20" y1="65" x2="60" y2="65" stroke="#34d399" strokeWidth="4.5" />
                <circle cx="40" cy="65" r="5" fill="#34d399" />
                <text x="75" y="71" fill="#34d399" fontSize="17" fontFamily="monospace" fontWeight="bold">
                  Bending Moment M(x)
                </text>
              </g>

              <path
                d={shearPath}
                fill="none"
                stroke="#38bdf8"
                strokeWidth="4.5"
                strokeLinecap="round"
                strokeDasharray="8 6"
              />

              <path
                d={momentPath}
                fill="none"
                stroke="#34d399"
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={pathLength}
                strokeDashoffset={strokeDashoffset}
              />

              {isCriticalPointActive && (
                <g transform={`translate(${originX}, ${toScreenY(3.6)})`}>
                  <circle cx="0" cy="0" r="12" fill="#34d399" stroke="#ffffff" strokeWidth="3" />
                  <rect x="-130" y="-50" width="260" height="38" rx="8" fill="#0f172a" stroke="#34d399" strokeWidth="1.5" />
                  <text x="0" y="-25" fill="#34d399" fontSize="16" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                    Max Moment: M_max = wL²/8
                  </text>
                </g>
              )}
            </g>
          ) : isQuantum ? (
            /* Quantum Barrier Penetration Canvas */
            <g>
              <text x={originX} y={originY + 45} fill="#c084fc" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                Spatial Coordinate x →
              </text>
              <text x="90" y="55" fill="#a855f7" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="start">
                Probability Density |Ψ(x)|² ↑
              </text>

              {/* Barrier Region */}
              <rect
                x={toScreenX(-1)}
                y={toScreenY(4.5)}
                width={scaleUnit * 2}
                height={scaleUnit * 4.5}
                fill="rgba(239, 68, 68, 0.18)"
                stroke="#ef4444"
                strokeWidth="2.5"
              />
              <text x={originX} y={toScreenY(4.0)} fill="#ef4444" fontSize="16" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                Barrier V₀ (E &lt; V₀)
              </text>

              <path
                d={quantumPath}
                fill="none"
                stroke="#c084fc"
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={pathLength}
                strokeDashoffset={strokeDashoffset}
              />

              {isCriticalPointActive && (
                <g transform={`translate(${toScreenX(1)}, ${toScreenY(2.2)})`}>
                  <circle cx="0" cy="0" r="10" fill="#38bdf8" stroke="#ffffff" strokeWidth="2.5" />
                  <rect x="-110" y="-45" width="220" height="34" rx="8" fill="#1e293b" stroke="#38bdf8" strokeWidth="1.5" />
                  <text x="0" y="-23" fill="#38bdf8" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                    Decay: ψ(x) ~ e^(-κx)
                  </text>
                </g>
              )}
            </g>
          ) : isChemistry ? (
            /* Energy Profile Coordinates & Labels */
            <g>
              <text x="140" y={originY + 32} fill="#38bdf8" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                Reactants (R-X)
              </text>
              <text x="760" y={originY + 32} fill="#34d399" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                Products (R-Nu)
              </text>
              <text x={canvasWidth / 2} y={originY + 72} fill="#94a3b8" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="middle">
                Reaction Coordinate →
              </text>
              <text x="90" y="55" fill="#f59e0b" fontSize="18" fontFamily="monospace" fontWeight="bold" textAnchor="start">
                Potential Energy (ΔG) ↑
              </text>

              <g transform={`translate(${canvasWidth - 360}, 40)`}>
                <rect x="0" y="0" width="330" height="90" rx="12" fill="rgba(15, 23, 42, 0.85)" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.5" />
                <line x1="20" y1="30" x2="60" y2="30" stroke="#38bdf8" strokeWidth="4.5" />
                <circle cx="40" cy="30" r="5" fill="#38bdf8" />
                <text x="75" y="36" fill="#38bdf8" fontSize="17" fontFamily="monospace" fontWeight="bold">
                  SN2: Concerted (1 Peak [‡])
                </text>
                <line x1="20" y1="65" x2="60" y2="65" stroke="#f59e0b" strokeWidth="4.5" />
                <circle cx="40" cy="65" r="5" fill="#f59e0b" />
                <text x="75" y="71" fill="#f59e0b" fontSize="17" fontFamily="monospace" fontWeight="bold">
                  SN1: Stepwise (2 Peaks + C⁺)
                </text>
              </g>

              <path
                d={sn2Path}
                fill="none"
                stroke="#38bdf8"
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={pathLength}
                strokeDashoffset={strokeDashoffset}
              />

              <path
                d={sn1Path}
                fill="none"
                stroke="#f59e0b"
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={pathLength}
                strokeDashoffset={strokeDashoffset}
              />

              <g transform={`translate(${toScreenX(-1.8)}, ${toScreenY(4.4)})`}>
                <circle cx="0" cy="0" r="10" fill="#f59e0b" stroke="#ffffff" strokeWidth="2.5" />
                <rect x="-80" y="-45" width="160" height="34" rx="8" fill="#1e293b" stroke="#f59e0b" strokeWidth="1.5" />
                <text x="0" y="-23" fill="#f59e0b" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                  TS 1 [‡₁] (Slow RDS)
                </text>
              </g>

              <g transform={`translate(${toScreenX(0.1)}, ${toScreenY(1.9)})`}>
                <circle cx="0" cy="0" r="10" fill="#a855f7" stroke="#ffffff" strokeWidth="2.5" />
                <rect x="-85" y="16" width="170" height="34" rx="8" fill="#1e293b" stroke="#a855f7" strokeWidth="1.5" />
                <text x="0" y="38" fill="#c084fc" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                  [C⁺] Carbocation Int.
                </text>
              </g>

              <g transform={`translate(${toScreenX(0)}, ${toScreenY(3.5)})`}>
                <circle cx="0" cy="0" r="10" fill="#38bdf8" stroke="#ffffff" strokeWidth="2.5" />
                <rect x="-80" y="-45" width="160" height="34" rx="8" fill="#0f172a" stroke="#38bdf8" strokeWidth="1.5" />
                <text x="0" y="-23" fill="#38bdf8" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                  SN2 TS [‡] (Concerted)
                </text>
              </g>
            </g>
          ) : (
            /* Standard Cartesian Math Plotting */
            <g>
              {[-4, -2, 2, 4].map((u) => (
                <text
                  key={`lbl-x-${u}`}
                  x={toScreenX(u)}
                  y={originY + 28}
                  fill="#94a3b8"
                  fontSize="20"
                  fontFamily="monospace"
                  fontWeight="bold"
                  textAnchor="middle"
                >
                  {u}
                </text>
              ))}
              {[2, 4, 6].map((u) => (
                <text
                  key={`lbl-y-${u}`}
                  x={originX - 16}
                  y={toScreenY(u) + 6}
                  fill="#94a3b8"
                  fontSize="20"
                  fontFamily="monospace"
                  fontWeight="bold"
                  textAnchor="end"
                >
                  {u}
                </text>
              ))}

              <path
                d={curvePath}
                fill="none"
                stroke={palette.primary}
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={pathLength}
                strokeDashoffset={strokeDashoffset}
              />

              {isTangentActive && (
                <line
                  x1={toScreenX(-3)}
                  y1={originY}
                  x2={toScreenX(3)}
                  y2={originY}
                  stroke="#56d364"
                  strokeWidth="3.5"
                  strokeDasharray="8 6"
                />
              )}

              {isCriticalPointActive && (
                <g>
                  <circle
                    cx={originX}
                    cy={originY}
                    r="14"
                    fill="#56d364"
                    stroke="#ffffff"
                    strokeWidth="3"
                  />
                  <rect
                    x={originX + 24}
                    y={originY - 38}
                    width="220"
                    height="44"
                    rx="10"
                    fill="#161b22"
                    stroke="#56d364"
                    strokeWidth="1.5"
                  />
                  <text
                    x={originX + 36}
                    y={originY - 10}
                    fill="#ffffff"
                    fontSize="20"
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    Critical (0, 0): f'(x) = 0
                  </text>
                </g>
              )}
            </g>
          )}
        </svg>
      </div>

      {/* 3. BOTTOM DOMAIN BREAKDOWN CARD / BOTTOM CALCULUS BREAKDOWN CARD (420px) - Hidden in canvas_spotlight mode */}
      {!isSpotlight && (
        <div
          style={{
            height: '420px',
            backgroundColor: '#161b22',
            borderRadius: '22px',
            border: `1.5px solid ${palette.border}`,
            boxShadow: '0 16px 32px rgba(0, 0, 0, 0.6)',
            padding: '28px 32px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <SparklesIcon size={26} color={palette.primary} />
            <span
              style={{
                fontSize: '26px',
                fontWeight: 900,
                color: palette.primary,
                fontFamily: 'monospace',
                letterSpacing: '1.5px',
              }}
            >
              {breakdown.title}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div
              style={{
                padding: '18px 22px',
                backgroundColor: '#0d1117',
                borderRadius: '14px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div style={{ fontSize: '18px', color: '#94a3b8', fontFamily: 'monospace', marginBottom: '6px' }}>
                {breakdown.left_label}
              </div>
              <div style={{ fontSize: '28px', color: '#38bdf8', fontWeight: 'bold', fontFamily: 'monospace' }}>
                {breakdown.left_value}
              </div>
            </div>

            <div
              style={{
                padding: '18px 22px',
                backgroundColor: '#0d1117',
                borderRadius: '14px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div style={{ fontSize: '18px', color: '#94a3b8', fontFamily: 'monospace', marginBottom: '6px' }}>
                {breakdown.right_label}
              </div>
              <div style={{ fontSize: '28px', color: '#34d399', fontWeight: 'bold', fontFamily: 'monospace' }}>
                {breakdown.right_value}
              </div>
            </div>
          </div>

          <div
            style={{
              padding: '14px 20px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              borderRadius: '12px',
              border: `1px solid ${palette.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontSize: '22px', color: '#cbd5e1', fontFamily: 'monospace', fontWeight: 'bold' }}>
              {breakdown.footer}
            </span>
            <span style={{ fontSize: '18px', color: palette.primary, fontFamily: 'monospace', fontWeight: 800 }}>
              {breakdown.tag}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphScene;
