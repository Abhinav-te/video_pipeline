import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { PhysicsIcon, SparklesIcon, LightningIcon } from './SvgIcons';
import { SPRING_CONFIG } from '../cameraUtils';

/**
 * Animated SVG Vector Arrow with arrowhead and magnitude label.
 */
const VectorArrow = ({
  startX,
  startY,
  endX,
  endY,
  growthProgress,
  color = '#ffa657',
  label = '',
  magnitude = '',
}) => {
  const currentEndX = startX + (endX - startX) * growthProgress;
  const currentEndY = startY + (endY - startY) * growthProgress;

  // Arrowhead angle
  const angle = Math.atan2(endY - startY, endX - startX);
  const headLength = 16 * Math.min(1, growthProgress * 2);

  const head1X = currentEndX - headLength * Math.cos(angle - Math.PI / 6);
  const head1Y = currentEndY - headLength * Math.sin(angle - Math.PI / 6);
  const head2X = currentEndX - headLength * Math.cos(angle + Math.PI / 6);
  const head2Y = currentEndY - headLength * Math.sin(angle + Math.PI / 6);

  return (
    <g>
      {/* Arrow Stem */}
      <line
        x1={startX}
        y1={startY}
        x2={currentEndX}
        y2={currentEndY}
        stroke={color}
        strokeWidth="5"
        strokeLinecap="round"
      />
      {/* Arrowhead */}
      {growthProgress > 0.1 && (
        <polygon
          points={`${currentEndX},${currentEndY} ${head1X},${head1Y} ${head2X},${head2Y}`}
          fill={color}
        />
      )}
      {/* Vector Label */}
      {growthProgress >= 0.7 && label && (
        <g>
          <rect
            x={currentEndX + (currentEndX >= startX ? 12 : -110)}
            y={currentEndY - 18}
            width="100"
            height="34"
            rx="8"
            fill="#161b22"
            stroke={color}
            strokeWidth="1.5"
          />
          <text
            x={currentEndX + (currentEndX >= startX ? 20 : -100)}
            y={currentEndY + 6}
            fill="#ffffff"
            fontSize="18"
            fontWeight="bold"
            fontFamily="monospace"
          >
            {label} {magnitude}
          </text>
        </g>
      )}
    </g>
  );
};

/**
 * PhysicsScene (Phase 5 - 1540px Vertical Stage Layout)
 * Full-height 1540px layout filling 85% of the 1080x1920 canvas:
 *   - Top Editorial Header (220px): 52px bold title, PhysicsIcon, category eyebrow, active badge.
 *   - Center Simulation SVG (840px): Dynamic frame-driven physics simulation (forces, projectile, or wave)
 *     with generous bounds and zero text/arrow overlap.
 *   - Bottom Telemetry & Vector Breakdown Card (420px): 24px–26px typography for Net Force, Acceleration, and Energy.
 */
export const PhysicsScene = ({
  scene,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const choreography = scene?.choreography || {};
  const physicsChoreo = choreography.physics || {};

  const simType = scene?.sim_type || physicsChoreo.sim_type || 'forces';
  const growthStart = physicsChoreo.vector_growth_start_frame || (sceneStartFrame + 4);
  const growthEnd = physicsChoreo.vector_growth_end_frame || (sceneStartFrame + 24);
  const emphasisFrame = physicsChoreo.force_highlight_frame || (sceneStartFrame + 28);

  const palette = choreography.palette || {
    primary: '#ffa657',
    secondary: '#ff7b72',
    accent: '#7ee787',
    background: '#1c1917',
    border: 'rgba(255, 166, 87, 0.35)',
    glow: 'rgba(255, 166, 87, 0.18)',
  };

  const vectorProgress = interpolate(
    frame,
    [growthStart, growthEnd],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const isEmphasized = frame >= emphasisFrame;

  // Header and title info
  let modeLabel = 'Free Body Diagram & Forces';
  let badgeLabel = isEmphasized ? 'EQUILIBRIUM BALANCED' : 'FORCES ACTIVE';
  if (simType === 'projectile') {
    modeLabel = 'Parabolic Trajectory & Velocity';
    badgeLabel = 'TRAJECTORY ACTIVE';
  } else if (simType === 'wave') {
    modeLabel = 'Harmonic Wave & Oscillation';
    badgeLabel = 'PROPAGATING WAVE';
  }

  const title = scene?.title || modeLabel;
  const canvasWidth = 896;
  const canvasHeight = 820;

  return (
    <div
      style={{
        backgroundColor: palette.background,
        borderRadius: '28px',
        border: `1.5px solid ${palette.border}`,
        boxShadow: `0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 40px ${palette.glow}`,
        width: '960px',
        height: '1540px',
        minHeight: '1540px',
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
      {/* 1. TOP EDITORIAL HEADER (220px) */}
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
            <PhysicsIcon size={28} color={palette.primary} />
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
              KINETIC PHYSICS SIMULATION
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(255, 166, 87, 0.16)',
                border: `1.5px solid ${palette.primary}`,
                color: palette.primary,
                borderRadius: '8px',
                padding: '4px 14px',
                fontSize: '17px',
                fontFamily: 'monospace',
                fontWeight: 900,
              }}
            >
              {badgeLabel}
            </span>
            {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
          </div>
        </div>

        <div>
          <div
            style={{
              fontSize: '50px',
              fontWeight: 900,
              color: '#ffffff',
              fontFamily: 'sans-serif',
              letterSpacing: '-0.5px',
              lineHeight: '1.15',
            }}
          >
            {title}
          </div>
          <div style={{ fontSize: '24px', color: '#94a3b8', marginTop: '4px', fontStyle: 'italic' }}>
            {scene?.spoken_text || 'Newtonian mechanics & vector field dynamics.'}
          </div>
        </div>
      </div>

      {/* 2. CENTER SIMULATION SVG (840px) */}
      <div
        style={{
          height: '840px',
          backgroundColor: '#0d1117',
          borderRadius: '22px',
          border: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxShadow: 'inset 0 0 36px rgba(0, 0, 0, 0.8), 0 0 24px rgba(255, 166, 87, 0.12)',
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
          {/* Subtle Gridlines */}
          {[160, 320, 480, 640, 800].map((gx) => (
            <line key={`gx-${gx}`} x1={gx} y1="40" x2={gx} y2={canvasHeight - 40} stroke="rgba(255,255,255,0.03)" strokeWidth="1.5" />
          ))}
          {[160, 320, 480, 640].map((gy) => (
            <line key={`gy-${gy}`} x1="40" y1={gy} x2={canvasWidth - 40} y2={gy} stroke="rgba(255,255,255,0.03)" strokeWidth="1.5" />
          ))}

          {/* SIMULATION 1: FORCES (FREE-BODY DIAGRAM) */}
          {simType === 'forces' && (() => {
            const centerX = canvasWidth / 2;
            const centerY = canvasHeight / 2 - 20;
            const boxW = 180;
            const boxWidth = Math.max(boxW, 240);
            const boxHeight = 160;
            const boxLeft = centerX - boxWidth / 2;
            const boxRight = centerX + boxWidth / 2;
            const boxTop = centerY - boxHeight / 2;
            const boxBottom = centerY + boxHeight / 2;
            const gap = 20;

            return (
              <g>
                {/* Surface Ground */}
                <line x1="100" y1={boxBottom + 1} x2={canvasWidth - 100} y2={boxBottom + 1} stroke="rgba(255,255,255,0.3)" strokeWidth="3" />
                {Array.from({ length: 16 }).map((_, idx) => (
                  <line
                    key={`hatch-${idx}`}
                    x1={120 + idx * 42}
                    y1={boxBottom + 2}
                    x2={100 + idx * 42}
                    y2={boxBottom + 18}
                    stroke="rgba(255,255,255,0.15)"
                    strokeWidth="2"
                  />
                ))}

                {/* Central Mass Box */}
                <rect
                  x={boxLeft}
                  y={boxTop}
                  width={boxWidth}
                  height={boxHeight}
                  rx="16"
                  fill="#21262d"
                  stroke={palette.primary}
                  strokeWidth="3"
                />
                <text
                  x={centerX}
                  y={centerY - 8}
                  fill="#ffffff"
                  fontSize="32"
                  fontWeight="bold"
                  fontFamily="monospace"
                  textAnchor="middle"
                >
                  m = 10kg
                </text>
                <text
                  x={centerX}
                  y={centerY + 28}
                  fill={palette.primary}
                  fontSize="22"
                  fontWeight="bold"
                  fontFamily="monospace"
                  textAnchor="middle"
                >
                  RIGID BODY
                </text>

                {/* Vector 1: Normal Force (Upward) */}
                <VectorArrow
                  startX={centerX}
                  startY={boxTop - gap}
                  endX={centerX}
                  endY={boxTop - gap - 160}
                  growthProgress={vectorProgress}
                  color="#7ee787"
                  label="FN"
                  magnitude="98N"
                />

                {/* Vector 2: Gravity Force (Downward) */}
                <VectorArrow
                  startX={centerX}
                  startY={boxBottom + gap}
                  endX={centerX}
                  endY={boxBottom + gap + 160}
                  growthProgress={vectorProgress}
                  color="#ffa657"
                  label="Fg"
                  magnitude="98N"
                />

                {/* Vector 3: Applied Force (Rightward) */}
                <VectorArrow
                  startX={boxRight + gap}
                  startY={centerY}
                  endX={boxRight + gap + 180}
                  endY={centerY}
                  growthProgress={vectorProgress}
                  color="#79c0ff"
                  label="Fapp"
                  magnitude="40N"
                />

                {/* Vector 4: Friction Force (Leftward) */}
                <VectorArrow
                  startX={boxLeft - gap}
                  startY={centerY}
                  endX={boxLeft - gap - 180}
                  endY={centerY}
                  growthProgress={vectorProgress}
                  color="#ff7b72"
                  label="Ff"
                  magnitude="40N"
                />
              </g>
            );
          })()}

          {/* SIMULATION 2: PROJECTILE TRAJECTORY */}
          {simType === 'projectile' && (() => {
            const startX = 120;
            const startY = 640;
            const peakX = 448;
            const peakY = 220;
            const endX = 776;
            const endY = 640;

            const projT = interpolate(frame, [growthStart, growthEnd + 20], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });

            // Parabolic path: y = -4 * h / w^2 * (x - peakX)^2 + peakY
            const ballX = startX + (endX - startX) * projT;
            const w = endX - startX;
            const h = startY - peakY;
            const ballY = startY - 4 * h * (projT - projT * projT);

            const vx = 35;
            const vy = (1 - 2 * projT) * 45;
            const vxLen = vx * 2.5;
            const vyNorm = vy * 2.5;
            const trajectoryPath = `M ${startX} ${startY} Q ${peakX} ${peakY - (startY - peakY)} ${endX} ${endY}`;

            return (
              <g>
                <line x1="80" y1="650" x2={canvasWidth - 80} y2="650" stroke="rgba(255,255,255,0.3)" strokeWidth="3" />

                {/* Parabolic Trajectory Guide Line */}
                <path
                  d={trajectoryPath}
                  fill="none"
                  stroke="rgba(255, 166, 87, 0.4)"
                  strokeWidth="3"
                  strokeDasharray="8 6"
                />

                {/* Moving Ball */}
                <circle cx={ballX} cy={ballY} r="18" fill="#ffa657" stroke="#ffffff" strokeWidth="3" />

                {/* Dynamic vx Arrow */}
                <VectorArrow
                  startX={ballX}
                  startY={ballY}
                  endX={ballX + vxLen}
                  endY={ballY}
                  growthProgress={1}
                  color="#79c0ff"
                  label="vx"
                  magnitude="25m/s"
                />

                {/* Dynamic vy Arrow */}
                <VectorArrow
                  startX={ballX}
                  startY={ballY}
                  endX={ballX}
                  endY={ballY - vyNorm}
                  growthProgress={1}
                  color={vy >= 0 ? '#7ee787' : '#ff7b72'}
                  label="vy"
                  magnitude={`${Math.round(Math.abs(vy))}m/s`}
                />
              </g>
            );
          })()}

          {/* SIMULATION 3: WAVE PROPAGATION */}
          {simType === 'wave' && (() => {
            const wavePoints = [];
            for (let x = 80; x <= canvasWidth - 80; x += 8) {
              const y = 410 + Math.sin((x / 50) - (frame * 0.15)) * 120;
              wavePoints.push(`${x === 80 ? 'M' : 'L'} ${x} ${y}`);
            }
            return (
              <g>
                <line x1="80" y1="410" x2={canvasWidth - 80} y2="410" stroke="rgba(255,255,255,0.1)" strokeWidth="2" strokeDasharray="4 4" />
                <path d={wavePoints.join(' ')} fill="none" stroke="#79c0ff" strokeWidth="5" strokeLinecap="round" />
              </g>
            );
          })()}
        </svg>
      </div>

      {/* 3. BOTTOM TELEMETRY & VECTOR BREAKDOWN CARD (420px) */}
      <div
        style={{
          height: '420px',
          backgroundColor: '#161b22',
          borderRadius: '22px',
          border: '1.5px solid rgba(255, 166, 87, 0.3)',
          boxShadow: '0 16px 32px rgba(0, 0, 0, 0.6)',
          padding: '28px 32px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <LightningIcon size={26} color={palette.primary} />
          <span
            style={{
              fontSize: '26px',
              fontWeight: 900,
              color: palette.primary,
              fontFamily: 'monospace',
              letterSpacing: '1.5px',
            }}
          >
            NEWTON'S SECOND LAW • EQUILIBRIUM
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
              HORIZONTAL NET FORCE (ΣFx)
            </div>
            <div style={{ fontSize: '30px', color: '#7ee787', fontWeight: 'bold', fontFamily: 'monospace' }}>
              ΣFx = Fapp - Ff = 0 N
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
              VERTICAL NET FORCE (ΣFy)
            </div>
            <div style={{ fontSize: '30px', color: '#79c0ff', fontWeight: 'bold', fontFamily: 'monospace' }}>
              ΣFy = FN - Fg = 0 N
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '14px 20px',
            backgroundColor: 'rgba(255, 166, 87, 0.12)',
            borderRadius: '12px',
            border: '1px solid rgba(255, 166, 87, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span style={{ fontSize: '24px', color: '#ffa657', fontFamily: 'monospace', fontWeight: 'bold' }}>
            Acceleration: a = 0.0 m/s² (Constant Velocity)
          </span>
          <span style={{ fontSize: '18px', color: '#7ee787', fontFamily: 'monospace', fontWeight: 800 }}>
            BALANCED
          </span>
        </div>
      </div>
    </div>
  );
};

export default PhysicsScene;
