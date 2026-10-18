import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { ChemistryIcon, SparklesIcon, WarningIcon, LightningIcon } from './SvgIcons';

/**
 * ChemistryScene (Phase 9 True Multi-Geometry Animations & Dynamic Viewport Breathing)
 *
 * Viewport Breathing:
 *   - 'compact_punch': ~55% height (centered, maxHeight: 960px)
 *   - 'canvas_spotlight': ~72% height (1260px tall) - hides bottom 2 cards, expands reaction canvas to 920x960!
 *   - 'full_dashboard': ~88% height (1540px tall) - full 3-tier layout with reaction coordinates
 *
 * 4 Distinct SVG Reaction Mechanisms:
 *   1. 'sn2_concerted': 180° Backside attack on CH3Br -> transition state [‡] -> Walden inversion
 *   2. 'steric_blockade': Central C with 3 bulky methyls + red steric barrier arc; OH⁻ hits & bounces back!
 *   3. 'sn1_ionization': ZERO OH⁻! Heat applied (Δ) -> C-Br snaps heterolytically -> flat planar C⁺ with huge figure-8 p-orbital!
 *   4. 'sn1_racemic': Planar C⁺ with figure-8 p-orbital; TWO nucleophiles attack simultaneously from TOP and BOTTOM -> 50/50 Racemic!
 */
export const ChemistryScene = ({
  scene,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Viewport Breathing density
  const layoutDensity = scene?.choreography?.layout_density || scene?.layout_density || 'canvas_spotlight';
  const isSpotlight = layoutDensity === 'canvas_spotlight';
  const isCompact = layoutDensity === 'compact_punch';

  // Sub-mode normalization
  const rawSubMode = scene?.sub_mode || scene?.chemistry_mode || scene?.mode || 'sn2_concerted';
  const textLower = `${scene?.title || ''} ${scene?.reaction_name || ''} ${scene?.display_text || ''} ${scene?.narration || ''} ${scene?.spoken_text || ''}`.toLowerCase();

  let subMode = 'sn2_concerted';
  if (rawSubMode === 'steric_blockade' || rawSubMode === 'steric_hindrance' || textLower.includes('steric') || textLower.includes('hindrance') || textLower.includes('bulky')) {
    subMode = 'steric_blockade';
  } else if (rawSubMode === 'sn1_racemic' || textLower.includes('racemic') || textLower.includes('both sides') || textLower.includes('top and bottom') || textLower.includes('dual attack')) {
    subMode = 'sn1_racemic';
  } else if (rawSubMode === 'sn1_ionization' || rawSubMode === 'sn1_carbocation' || textLower.includes('ionization') || textLower.includes('carbocation') || textLower.includes('cleavage') || textLower.includes('heterolytic')) {
    subMode = 'sn1_ionization';
  } else {
    subMode = 'sn2_concerted';
  }

  // Header & conditions
  const title = scene?.reaction_name || scene?.title || (
    subMode === 'steric_blockade'
      ? 'Steric Hindrance Blockade'
      : subMode === 'sn1_ionization'
      ? 'SN1 Ionization & Planar Carbocation'
      : subMode === 'sn1_racemic'
      ? 'SN1 Dual-Face Racemic Attack'
      : 'SN2 Bimolecular Substitution'
  );

  const heatApplied = Boolean(scene?.heat_applied) || subMode === 'sn1_ionization';
  const tempKelvin = scene?.temperature_kelvin || (heatApplied ? 355 : 298);

  const reagents = scene?.reagents || (
    subMode === 'steric_blockade'
      ? 'NaOH • (CH₃)₃C-Br (Tertiary Substrate)'
      : subMode === 'sn1_ionization'
      ? 'Polar Protic Solvent (H₂O • Ethanol)'
      : subMode === 'sn1_racemic'
      ? 'H₂O Nucleophile • Polar Protic'
      : 'NaOH • Acetone (Polar Aprotic)'
  );

  const rateLaw = scene?.rate_law || (
    subMode === 'steric_blockade'
      ? 'Rate ≈ 0 (High Steric Barrier)'
      : subMode === 'sn1_ionization'
      ? 'Rate = k[(CH₃)₃C-Br] (First-Order RDS)'
      : subMode === 'sn1_racemic'
      ? 'Rate = k[Substrate] • Fast Step 2'
      : 'Rate = k[R-X][Nu⁻] (Second-Order)'
  );

  const stereochem = scene?.stereochemistry || (
    subMode === 'steric_blockade'
      ? 'No Inversion (Substrate Intact)'
      : subMode === 'sn1_ionization'
      ? 'Planar sp² Carbocation (Achiral)'
      : subMode === 'sn1_racemic'
      ? '50% Front + 50% Back = Racemic Mixture'
      : 'Walden Inversion (100% Inversion)'
  );

  const thermoBadge = scene?.thermodynamic_badge || (
    subMode === 'steric_blockade'
      ? 'ATTACK BLOCKED'
      : subMode === 'sn1_ionization'
      ? 'RATE-LIMITING RDS'
      : subMode === 'sn1_racemic'
      ? 'RACEMIC MIXTURE'
      : 'CONCERTED MECHANISM'
  );

  const energyProfile = scene?.energy_profile || {
    activation_energy: subMode === 'steric_blockade' ? 120 : (subMode.startsWith('sn1') ? 88 : 75),
    delta_g: subMode === 'steric_blockade' ? 0 : (subMode.startsWith('sn1') ? -38 : -45),
    transition_state: subMode === 'steric_blockade' ? 'Steric Repulsion' : (subMode.startsWith('sn1') ? '[R···Br]‡ -> C+' : '[HO···C···Br]‡'),
    num_barriers: subMode.startsWith('sn1') ? 2 : 1,
  };

  // Frame timing calculation
  const startFrame = scene?.choreography?.scene_start_frame || sceneStartFrame || 0;
  const endFrame = scene?.choreography?.scene_end_frame || (startFrame + 90);
  const totalFrames = Math.max(30, endFrame - startFrame);
  const localFrame = Math.max(0, Math.min(totalFrames, frame - startFrame));
  const progress = localFrame / totalFrames; // 0.0 to 1.0

  // 3-Phase Animation Boundaries
  const isPhase1 = progress < 0.35;
  const isPhase2 = progress >= 0.35 && progress < 0.70;
  const isPhase3 = progress >= 0.70;

  const phaseProgress = isPhase1
    ? progress / 0.35
    : isPhase2
    ? (progress - 0.35) / 0.35
    : (progress - 0.70) / 0.30;

  // Geometry dimensions (full_dashboard default: height: '1540px', vessel height: '840px')
  let stageHeight = isSpotlight ? '1260px' : (isCompact ? '960px' : '1540px');
  let vesselHeight = isSpotlight ? '1040px' : (isCompact ? '760px' : '840px');
  const svgHeight = isSpotlight ? 840 : (isCompact ? 580 : 680);
  const cX = 455;
  const cY = isSpotlight ? 420 : (isCompact ? 290 : 330);

  // Thermal jitter for atoms when heat applied
  const thermalJitter = heatApplied ? Math.sin(frame * 0.45) * 3 : 0;

  // Tracking dot for 2-hump curve in SN1 or 1-hump curve in SN2
  const curveX = interpolate(progress, [0, 1], [80, 420]);
  let curveY = 280;
  if (energyProfile.num_barriers === 2) {
    if (progress < 0.35) {
      const p = progress / 0.35;
      curveY = 280 - Math.sin(p * Math.PI) * 160;
    } else if (progress < 0.65) {
      const p = (progress - 0.35) / 0.30;
      curveY = 200 - Math.sin(p * Math.PI) * 100;
    } else {
      const p = (progress - 0.65) / 0.35;
      curveY = 240 + p * 80;
    }
  } else {
    if (progress <= 0.5) {
      const p = progress / 0.5;
      curveY = 260 - Math.sin(p * (Math.PI / 2)) * 180;
    } else {
      const p = (progress - 0.5) / 0.5;
      curveY = 80 + Math.sin(p * (Math.PI / 2)) * 260;
    }
  }

  // =========================================================================
  // RENDERER 1: SN2 CONCERTED (Backside Attack -> Transition State -> Walden Inversion)
  // =========================================================================
  const renderSN2ConcertedSVG = () => {
    const nuX = isPhase1
      ? interpolate(phaseProgress, [0, 1], [140, 330])
      : isPhase2
      ? interpolate(phaseProgress, [0, 1], [330, 395])
      : 395;

    const brX = isPhase1
      ? 515
      : isPhase2
      ? interpolate(phaseProgress, [0, 1], [515, 580])
      : interpolate(phaseProgress, [0, 1], [580, 820]);

    const umbrellaAngle = isPhase1
      ? -35
      : isPhase2
      ? interpolate(phaseProgress, [0, 1], [-35, 35])
      : 35;

    const arrowDashOffset = isPhase1 ? interpolate(phaseProgress, [0, 1], [240, 0]) : 0;

    return (
      <g key="sn2-concerted-group">
        {/* Curved Electron-Pushing Arrow (Nu -> C) in Phase 1 */}
        {isPhase1 && (
          <path
            d={`M ${nuX + 24} ${cY - 18} C ${nuX + 90} ${cY - 90}, ${cX - 70} ${cY - 80}, ${cX - 20} ${cY - 14}`}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeDasharray="240"
            strokeDashoffset={arrowDashOffset}
            markerEnd="url(#electronArrow)"
          />
        )}

        {/* Leaving Group Arrow in Phase 2 */}
        {isPhase2 && (
          <path
            d={`M ${(cX + brX) / 2} ${cY - 12} Q ${brX - 10} ${cY - 60} ${brX - 12} ${cY - 22}`}
            fill="none"
            stroke="#ef4444"
            strokeWidth="3"
            strokeLinecap="round"
            markerEnd="url(#leavingArrow)"
          />
        )}

        {/* Forming Bond (Nu-C) */}
        {isPhase2 && (
          <line
            x1={nuX + 20}
            y1={cY}
            x2={cX - 20}
            y2={cY}
            stroke="#10b981"
            strokeWidth="4"
            strokeDasharray="8 6"
          />
        )}
        {isPhase3 && (
          <line
            x1={nuX + 20}
            y1={cY}
            x2={cX - 20}
            y2={cY}
            stroke="#38bdf8"
            strokeWidth="4.5"
            strokeLinecap="round"
          />
        )}

        {/* Breaking Bond (C-Br) */}
        {isPhase1 && (
          <line
            x1={cX + 20}
            y1={cY}
            x2={brX - 20}
            y2={cY}
            stroke="#f59e0b"
            strokeWidth="4.5"
            strokeLinecap="round"
          />
        )}
        {isPhase2 && (
          <line
            x1={cX + 20}
            y1={cY}
            x2={brX - 20}
            y2={cY}
            stroke="#ef4444"
            strokeWidth="3.5"
            strokeDasharray="6 6"
          />
        )}

        {/* Central Carbon & Hydrogen Umbrella Flipping */}
        <g transform={`translate(${cX + thermalJitter}, ${cY})`}>
          <g transform={`rotate(${umbrellaAngle})`}>
            <line x1="0" y1="-20" x2="0" y2="-120" stroke="#94a3b8" strokeWidth="3" />
            <circle cx="0" cy="-120" r="14" fill="#1e293b" stroke="#f8fafc" strokeWidth="2" />
            <text x="0" y="-115" textAnchor="middle" fill="#f8fafc" fontSize="16" fontWeight="bold" fontFamily="monospace">
              H
            </text>
          </g>

          <g transform={`rotate(${umbrellaAngle - 40})`}>
            <polygon points="-6,18 6,18 16,110 -16,110" fill="#38bdf8" opacity="0.8" />
            <circle cx="0" cy="116" r="14" fill="#1e293b" stroke="#f8fafc" strokeWidth="2" />
            <text x="0" y="121" textAnchor="middle" fill="#f8fafc" fontSize="16" fontWeight="bold" fontFamily="monospace">
              H
            </text>
          </g>

          <g transform={`rotate(${umbrellaAngle + 40})`}>
            {[-30, -50, -70, -90, -110].map((dy, idx) => (
              <line key={idx} x1="-12" y1={-dy} x2="12" y2={-dy} stroke="#64748b" strokeWidth="2.5" />
            ))}
            <circle cx="0" cy="116" r="14" fill="#1e293b" stroke="#f8fafc" strokeWidth="2" />
            <text x="0" y="121" textAnchor="middle" fill="#f8fafc" fontSize="16" fontWeight="bold" fontFamily="monospace">
              H
            </text>
          </g>

          <circle
            cx="0"
            cy="0"
            r="26"
            fill="#0f172a"
            stroke="#38bdf8"
            strokeWidth="3.5"
          />
          <text x="0" y="8" textAnchor="middle" fill="#38bdf8" fontSize="24" fontWeight="900" fontFamily="monospace">
            C
          </text>
          {isPhase2 && (
            <text x="0" y="-36" textAnchor="middle" fill="#38bdf8" fontSize="18" fontWeight="bold" fontFamily="monospace">
              δ⁺
            </text>
          )}
        </g>

        {/* Nu OH Atom */}
        <g transform={`translate(${nuX}, ${cY})`}>
          <circle
            cx="0"
            cy="0"
            r="24"
            fill="#1b0c13"
            stroke="#ef4444"
            strokeWidth="3"
          />
          <text x="0" y="7" textAnchor="middle" fill="#f87171" fontSize="20" fontWeight="900" fontFamily="monospace">
            OH
          </text>
          <circle cx="-16" cy="-14" r="2.5" fill="#f59e0b" />
          <circle cx="-22" cy="-8" r="2.5" fill="#f59e0b" />
          <circle cx="-16" cy="14" r="2.5" fill="#f59e0b" />
          <circle cx="-22" cy="8" r="2.5" fill="#f59e0b" />
          <text x="-4" y="-30" textAnchor="middle" fill="#f87171" fontSize="18" fontWeight="bold" fontFamily="monospace">
            {isPhase1 ? '⁻' : isPhase2 ? 'δ⁻' : ''}
          </text>
        </g>

        {/* Leaving Group Br */}
        <g transform={`translate(${brX}, ${cY})`}>
          <circle
            cx="0"
            cy="0"
            r="26"
            fill="#201509"
            stroke="#f59e0b"
            strokeWidth="3"
          />
          <text x="0" y="8" textAnchor="middle" fill="#fbbf24" fontSize="22" fontWeight="900" fontFamily="monospace">
            Br
          </text>
          <text x="0" y="-34" textAnchor="middle" fill="#fbbf24" fontSize="18" fontWeight="bold" fontFamily="monospace">
            {isPhase1 ? 'δ⁻' : isPhase2 ? 'δ⁻' : '⁻'}
          </text>
        </g>

        {/* Transition State Brackets */}
        {isPhase2 && (
          <g transform={`translate(${cX}, ${cY})`}>
            <path d="M -130 -160 L -150 -160 L -150 160 L -130 160" fill="none" stroke="#fbbf24" strokeWidth="2.5" />
            <path d="M 170 -160 L 190 -160 L 190 160 L 170 160" fill="none" stroke="#fbbf24" strokeWidth="2.5" />
            <text x="210" y="-140" fill="#fbbf24" fontSize="36" fontWeight="900" fontFamily="monospace">
              ‡
            </text>
            <text x="0" y="-175" textAnchor="middle" fill="#fbbf24" fontSize="20" fontWeight="800" fontFamily="monospace">
              {energyProfile.transition_state || '[HO···C···Br]‡'}
            </text>
          </g>
        )}

        {/* Walden Inversion Badge in Phase 3 */}
        {isPhase3 && (
          <g transform={`translate(${cX}, ${cY - 220})`}>
            <rect x="-200" y="-22" width="400" height="44" rx="12" fill="rgba(16, 185, 129, 0.2)" stroke="#10b981" strokeWidth="2" />
            <text x="0" y="7" textAnchor="middle" fill="#34d399" fontSize="18" fontWeight="bold" fontFamily="monospace">
              WALDEN INVERSION COMPLETED (sp³ INVERTED)
            </text>
          </g>
        )}
      </g>
    );
  };

  // =========================================================================
  // RENDERER 2: STERIC BLOCKADE (3 Bulky Methyl Clusters + Shockwave Bounce)
  // =========================================================================
  const renderStericBlockadeSVG = () => {
    // OH approach (0 -> 0.45), hit red steric shield at 0.45, bounce backward (0.45 -> 1.0)
    const isApproach = progress < 0.45;
    const nuX = isApproach
      ? interpolate(progress, [0, 0.45], [100, cX - 190])
      : interpolate(progress, [0.45, 1.0], [cX - 190, 110]);

    const hitProgress = Math.max(0, (progress - 0.45) / 0.55);
    const shockRadius = interpolate(hitProgress, [0, 1], [15, 130]);
    const shockAlpha = interpolate(hitProgress, [0, 1], [1, 0]);

    return (
      <g key="steric-blockade-group">
        {/* Pulsing Red Dashed Steric Barrier Arc on Left */}
        <path
          d={`M ${cX - 175} ${cY - 210} Q ${cX - 130} ${cY} ${cX - 175} ${cY + 210}`}
          fill="none"
          stroke="#ef4444"
          strokeWidth="4"
          strokeDasharray="10 8"
        />
        <text
          x={cX - 210}
          y={cY - 160}
          fill="#ef4444"
          fontSize="17"
          fontWeight="900"
          fontFamily="monospace"
          textAnchor="end"
          letterSpacing="1px"
        >
          STERIC BARRIER
        </text>

        {/* Central Carbon */}
        <g transform={`translate(${cX}, ${cY})`}>
          <circle cx="0" cy="0" r="28" fill="#0f172a" stroke="#38bdf8" strokeWidth="3.5" />
          <text x="0" y="8" textAnchor="middle" fill="#38bdf8" fontSize="24" fontWeight="900" fontFamily="monospace">
            C
          </text>

          {/* Intact C-Br Bond to the right */}
          <line x1="28" y1="0" x2="160" y2="0" stroke="#f59e0b" strokeWidth="5.5" strokeLinecap="round" />
          <circle cx="185" cy="0" r="26" fill="#201509" stroke="#f59e0b" strokeWidth="3" />
          <text x="185" y="8" textAnchor="middle" fill="#fbbf24" fontSize="22" fontWeight="900" fontFamily="monospace">
            Br
          </text>
          <text x="185" y="-34" textAnchor="middle" fill="#fbbf24" fontSize="16" fontWeight="bold" fontFamily="monospace">
            INTACT
          </text>

          {/* 3 Huge Bulky Methyl (-CH3) Groups */}
          {/* 1. Top Bulky Methyl Cluster */}
          <g transform="translate(-40, -120)">
            <line x1="20" y1="70" x2="0" y2="0" stroke="#38bdf8" strokeWidth="4.5" />
            <circle cx="0" cy="0" r="46" fill="#1e293b" stroke="#38bdf8" strokeWidth="3" />
            <text x="0" y="8" textAnchor="middle" fill="#38bdf8" fontSize="22" fontWeight="900" fontFamily="monospace">
              -CH₃
            </text>
            <circle cx="-34" cy="-24" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="-34" y="-20" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
            <circle cx="0" cy="-42" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="0" y="-38" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
            <circle cx="34" cy="-24" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="34" y="-20" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
          </g>

          {/* 2. Bottom Bulky Methyl Cluster */}
          <g transform="translate(-40, 120)">
            <line x1="20" y1="-70" x2="0" y2="0" stroke="#38bdf8" strokeWidth="4.5" />
            <circle cx="0" cy="0" r="46" fill="#1e293b" stroke="#38bdf8" strokeWidth="3" />
            <text x="0" y="8" textAnchor="middle" fill="#38bdf8" fontSize="22" fontWeight="900" fontFamily="monospace">
              -CH₃
            </text>
            <circle cx="-34" cy="24" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="-34" y="28" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
            <circle cx="0" cy="42" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="0" y="46" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
            <circle cx="34" cy="24" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="34" y="28" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
          </g>

          {/* 3. Back Left Bulky Methyl Cluster */}
          <g transform="translate(-130, 0)">
            <line x1="80" y1="0" x2="0" y2="0" stroke="#38bdf8" strokeWidth="4.5" />
            <circle cx="0" cy="0" r="46" fill="#1e293b" stroke="#38bdf8" strokeWidth="3" />
            <text x="0" y="8" textAnchor="middle" fill="#38bdf8" fontSize="22" fontWeight="900" fontFamily="monospace">
              -CH₃
            </text>
            <circle cx="-42" cy="0" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="-42" y="4" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
            <circle cx="-24" cy="-34" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="-24" y="-30" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
            <circle cx="-24" cy="34" r="13" fill="#0f172a" stroke="#f8fafc" strokeWidth="1.5" />
            <text x="-24" y="38" textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="bold" fontFamily="monospace">H</text>
          </g>
        </g>

        {/* OH Nucleophile rushing in & bouncing */}
        <g transform={`translate(${nuX}, ${cY})`}>
          <circle cx="0" cy="0" r="26" fill="#1b0c13" stroke="#ef4444" strokeWidth="3.5" />
          <text x="0" y="7" textAnchor="middle" fill="#f87171" fontSize="20" fontWeight="900" fontFamily="monospace">
            OH⁻
          </text>
          {isApproach ? (
            <path d="M 30 0 L 70 0" stroke="#f59e0b" strokeWidth="3" markerEnd="url(#electronArrow)" />
          ) : (
            <path d="M -30 0 L -80 0" stroke="#ef4444" strokeWidth="3.5" markerEnd="url(#leavingArrow)" />
          )}
        </g>

        {/* Expanding Red Shockwave on Impact (progress >= 0.45) */}
        {!isApproach && (
          <g>
            <circle
              cx={cX - 175}
              cy={cY}
              r={shockRadius}
              fill="rgba(239, 68, 68, 0.12)"
              stroke="#ef4444"
              strokeWidth="4"
              opacity={shockAlpha}
            />
            <g transform={`translate(${cX - 175}, ${cY - 220})`}>
              <rect x="-180" y="-22" width="360" height="44" rx="12" fill="rgba(239, 68, 68, 0.25)" stroke="#ef4444" strokeWidth="2" />
              <text x="0" y="7" textAnchor="middle" fill="#f87171" fontSize="18" fontWeight="900" fontFamily="monospace">
                [BLOCKED] STERIC HINDRANCE BLOCKADE
              </text>
            </g>
          </g>
        )}
      </g>
    );
  };

  // =========================================================================
  // RENDERER 3: SN1 IONIZATION (Heterolytic Cleavage -> Planar sp² C⁺ Carbocation, ZERO OH⁻)
  // =========================================================================
  const renderSN1IonizationSVG = () => {
    // Progress < 0.35: thermal agitation on substrate
    // Progress >= 0.35: C-Br snaps heterolytically, Br drifts away, C flattens into planar sp² with huge figure-8 p-orbital
    const isCleaved = progress >= 0.35;
    const brX = isCleaved ? interpolate(progress, [0.35, 1.0], [cX + 120, 840]) : (cX + 120 + thermalJitter);
    const flattenProgress = isCleaved ? Math.min(1, (progress - 0.35) / 0.35) : 0;

    // Angle of 3 methyls flattening to 120° trigonal planar
    const mAngle1 = interpolate(flattenProgress, [0, 1], [-130, -180]); // Left
    const mAngle2 = interpolate(flattenProgress, [0, 1], [-40, -60]);   // Top-Right
    const mAngle3 = interpolate(flattenProgress, [0, 1], [40, 60]);     // Bottom-Right

    return (
      <g key="sn1-ionization-group">
        {/* Rising Animated Thermal Heat Waves at Bottom */}
        <g opacity="0.8">
          {[0, 1, 2, 3, 4, 5, 6].map((idx) => {
            const wx = 120 + idx * 115;
            const waveShift = ((frame * 4 + idx * 22) % 110);
            const wy = (cY + 240) - waveShift;
            const waveAlpha = 1 - waveShift / 110;
            return (
              <path
                key={`heat-${idx}`}
                d={`M ${wx} ${wy} Q ${wx + 15} ${wy - 15} ${wx} ${wy - 30} T ${wx} ${wy - 60}`}
                fill="none"
                stroke="#f59e0b"
                strokeWidth="3"
                strokeLinecap="round"
                opacity={waveAlpha * 0.8}
              />
            );
          })}
        </g>
        <text x="455" y={cY + 270} textAnchor="middle" fill="#f59e0b" fontSize="17" fontWeight="bold" fontFamily="monospace">
          Δ HEAT APPLIED • POLAR PROTIC SOLVOLYSIS (RDS)
        </text>

        {/* Central Carbon & Planar Trigonal Rehybridization */}
        <g transform={`translate(${cX + thermalJitter}, ${cY})`}>
          {/* Heterolytic Cleavage curved arrow at snap point */}
          {!isCleaved && (
            <line x1="28" y1="0" x2="100" y2="0" stroke="#f59e0b" strokeWidth="5" />
          )}
          {isCleaved && progress < 0.60 && (
            <path
              d="M 40 -10 Q 70 -50 100 -20"
              fill="none"
              stroke="#ef4444"
              strokeWidth="3.5"
              markerEnd="url(#leavingArrow)"
            />
          )}

          {/* Huge Glowing Purple/Cyan Figure-8 p-Orbital (spans above and below) */}
          {isCleaved && (
            <g>
              {/* Upper Lobe (Cyan) */}
              <path
                d="M 0 0 C -45 -40 -45 -140 0 -170 C 45 -140 45 -40 0 0 Z"
                fill="rgba(56, 189, 248, 0.35)"
                stroke="#38bdf8"
                strokeWidth="2.5"
              />
              <text x="0" y="-85" textAnchor="middle" fill="#38bdf8" fontSize="16" fontWeight="bold" fontFamily="monospace">
                + p-lobe
              </text>

              {/* Lower Lobe (Purple) */}
              <path
                d="M 0 0 C -45 40 -45 140 0 170 C 45 140 45 40 0 0 Z"
                fill="rgba(192, 132, 252, 0.35)"
                stroke="#c084fc"
                strokeWidth="2.5"
              />
              <text x="0" y="95" textAnchor="middle" fill="#c084fc" fontSize="16" fontWeight="bold" fontFamily="monospace">
                - p-lobe
              </text>
            </g>
          )}

          {/* 3 Methyl Groups Flattening into 120° Trigonal Planar */}
          {[
            { angle: mAngle1, len: 120 },
            { angle: mAngle2, len: 120 },
            { angle: mAngle3, len: 120 },
          ].map((m, idx) => {
            const rad = (m.angle * Math.PI) / 180;
            const mx = Math.cos(rad) * m.len;
            const my = Math.sin(rad) * m.len;
            return (
              <g key={`planar-m-${idx}`}>
                <line x1="0" y1="0" x2={mx} y2={my} stroke="#38bdf8" strokeWidth="4" />
                <circle cx={mx} cy={my} r="32" fill="#1e293b" stroke="#38bdf8" strokeWidth="2.5" />
                <text x={mx} y={my + 6} textAnchor="middle" fill="#38bdf8" fontSize="18" fontWeight="bold" fontFamily="monospace">
                  -CH₃
                </text>
              </g>
            );
          })}

          {/* Central C+ Atom */}
          <circle cx="0" cy="0" r="30" fill="#0f172a" stroke={isCleaved ? '#38bdf8' : '#64748b'} strokeWidth="4" />
          <text x="0" y="8" textAnchor="middle" fill={isCleaved ? '#38bdf8' : '#f8fafc'} fontSize="26" fontWeight="900" fontFamily="monospace">
            {isCleaved ? 'C⁺' : 'C'}
          </text>
          {isCleaved && (
            <text x="24" y="-22" fill="#38bdf8" fontSize="24" fontWeight="900" fontFamily="monospace">
              +
            </text>
          )}
        </g>

        {/* Detaching Br- Leaving Group */}
        <g transform={`translate(${brX}, ${cY})`}>
          <circle cx="0" cy="0" r="28" fill="#201509" stroke="#ef4444" strokeWidth="3" />
          <text x="0" y="8" textAnchor="middle" fill="#f87171" fontSize="22" fontWeight="900" fontFamily="monospace">
            Br
          </text>
          <text x="0" y="-34" textAnchor="middle" fill="#f87171" fontSize="20" fontWeight="bold" fontFamily="monospace">
            {isCleaved ? '⁻' : 'δ⁻'}
          </text>
        </g>

        {/* Status Callout Pill */}
        {isCleaved && (
          <g transform={`translate(${cX}, ${cY - 220})`}>
            <rect x="-240" y="-22" width="480" height="44" rx="12" fill="rgba(56, 189, 248, 0.2)" stroke="#38bdf8" strokeWidth="2" />
            <text x="0" y="7" textAnchor="middle" fill="#38bdf8" fontSize="17" fontWeight="bold" fontFamily="monospace">
              PLANAR sp² CARBOCATION FORMED (EMPTY p-ORBITAL)
            </text>
          </g>
        )}
      </g>
    );
  };

  // =========================================================================
  // RENDERER 4: SN1 RACEMIC (Simultaneous Dual Top/Bottom Nucleophile Attack)
  // =========================================================================
  const renderSN1RacemicSVG = () => {
    // Two nucleophiles dive in simultaneously:
    // Top Nu dives down: y: 80 -> cY - 100
    // Bottom Nu rises up: y: cY + 220 -> cY + 100
    const attackYTop = interpolate(progress, [0, 0.65], [cY - 230, cY - 110]);
    const attackYBot = interpolate(progress, [0, 0.65], [cY + 230, cY + 110]);
    const isResolved = progress > 0.65;

    return (
      <g key="sn1-racemic-group">
        {/* Central Planar C+ with Vertical p-Orbital at (cX - 80, cY) */}
        <g transform={`translate(${cX - 90}, ${cY})`}>
          {/* Vertical Figure-8 p-Orbital */}
          <path
            d="M 0 0 C -40 -35 -40 -120 0 -150 C 40 -120 40 -35 0 0 Z"
            fill="rgba(56, 189, 248, 0.3)"
            stroke="#38bdf8"
            strokeWidth="2.5"
          />
          <path
            d="M 0 0 C -40 35 -40 120 0 150 C 40 120 40 35 0 0 Z"
            fill="rgba(192, 132, 252, 0.3)"
            stroke="#c084fc"
            strokeWidth="2.5"
          />

          {/* Central C+ */}
          <circle cx="0" cy="0" r="28" fill="#0f172a" stroke="#38bdf8" strokeWidth="3.5" />
          <text x="0" y="8" textAnchor="middle" fill="#38bdf8" fontSize="24" fontWeight="900" fontFamily="monospace">
            C⁺
          </text>

          {/* Planar Methyl Groups */}
          <line x1="-28" y1="0" x2="-120" y2="0" stroke="#38bdf8" strokeWidth="4" />
          <circle cx="-120" cy="0" r="30" fill="#1e293b" stroke="#38bdf8" strokeWidth="2" />
          <text x="-120" y="6" textAnchor="middle" fill="#38bdf8" fontSize="16" fontWeight="bold" fontFamily="monospace">-CH₃</text>
        </g>

        {/* 1. TOP NUCLEOPHILE (Diving Down) */}
        <g transform={`translate(${cX - 90}, ${attackYTop})`}>
          <circle cx="0" cy="0" r="24" fill="#1b0c13" stroke="#ef4444" strokeWidth="3" />
          <text x="0" y="7" textAnchor="middle" fill="#f87171" fontSize="18" fontWeight="bold" fontFamily="monospace">
            OH⁻
          </text>
          <path d="M 0 24 L 0 55" stroke="#f59e0b" strokeWidth="3.5" markerEnd="url(#electronArrow)" />
          <text x="36" y="6" fill="#38bdf8" fontSize="16" fontWeight="bold" fontFamily="monospace">
            TOP ATTACK (50%)
          </text>
        </g>

        {/* 2. BOTTOM NUCLEOPHILE (Rising Up) */}
        <g transform={`translate(${cX - 90}, ${attackYBot})`}>
          <circle cx="0" cy="0" r="24" fill="#1b0c13" stroke="#ef4444" strokeWidth="3" />
          <text x="0" y="7" textAnchor="middle" fill="#f87171" fontSize="18" fontWeight="bold" fontFamily="monospace">
            OH⁻
          </text>
          <path d="M 0 -24 L 0 -55" stroke="#f59e0b" strokeWidth="3.5" markerEnd="url(#electronArrow)" />
          <text x="36" y="6" fill="#fbbf24" fontSize="16" fontWeight="bold" fontFamily="monospace">
            BOTTOM ATTACK (50%)
          </text>
        </g>

        {/* Side-by-Side Product Boxes on Right (progress > 0.65) */}
        {isResolved && (
          <g transform={`translate(${cX + 160}, ${cY})`}>
            {/* Top Product Box (R) */}
            <g transform="translate(0, -120)">
              <rect x="0" y="-35" width="260" height="70" rx="14" fill="rgba(56, 189, 248, 0.16)" stroke="#38bdf8" strokeWidth="2" />
              <text x="130" y="-8" textAnchor="middle" fill="#38bdf8" fontSize="17" fontWeight="900" fontFamily="monospace">
                50% (R)-ENANTIOMER
              </text>
              <text x="130" y="16" textAnchor="middle" fill="#94a3b8" fontSize="14" fontFamily="monospace">
                Front Attack • Retention
              </text>
            </g>

            {/* Bottom Product Box (S) */}
            <g transform="translate(0, 30)">
              <rect x="0" y="-35" width="260" height="70" rx="14" fill="rgba(245, 158, 11, 0.16)" stroke="#f59e0b" strokeWidth="2" />
              <text x="130" y="-8" textAnchor="middle" fill="#fbbf24" fontSize="17" fontWeight="900" fontFamily="monospace">
                50% (S)-ENANTIOMER
              </text>
              <text x="130" y="16" textAnchor="middle" fill="#94a3b8" fontSize="14" fontFamily="monospace">
                Back Attack • Inversion
              </text>
            </g>

            {/* Racemic Banner */}
            <g transform="translate(0, 125)">
              <rect x="0" y="-22" width="260" height="44" rx="10" fill="rgba(16, 185, 129, 0.22)" stroke="#10b981" strokeWidth="2" />
              <text x="130" y="6" textAnchor="middle" fill="#34d399" fontSize="15" fontWeight="900" fontFamily="monospace">
                RACEMIC MIXTURE (50/50)
              </text>
            </g>
          </g>
        )}
      </g>
    );
  };

  return (
    <div
      style={{
        width: '960px',
        height: stageHeight || '1540px',
        minHeight: stageHeight || '1540px',
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
      {/* 1. TOP HEADER (180px tall) */}
      <div
        style={{
          height: '180px',
          backgroundColor: '#0c161f',
          borderRadius: '24px',
          border: '1.5px solid rgba(16, 185, 129, 0.35)',
          boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.8), 0 0 24px rgba(16, 185, 129, 0.14)',
          padding: '24px 32px',
          display: 'flex',
          alignItems: 'center',
          gap: '24px',
          boxSizing: 'border-box',
          transform: 'none',
        }}
      >
        <div
          style={{
            width: '84px',
            height: '84px',
            borderRadius: '50%',
            backgroundColor: 'rgba(16, 185, 129, 0.16)',
            border: '2px solid rgba(16, 185, 129, 0.6)',
            boxShadow: '0 0 24px rgba(16, 185, 129, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <ChemistryIcon size={44} color="#10b981" />
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span
              style={{
                fontSize: '20px',
                fontWeight: 900,
                color: '#10b981',
                letterSpacing: '2.5px',
                textTransform: 'uppercase',
                fontFamily: 'monospace',
              }}
            >
              ORGANIC CHEMISTRY • REACTION MECHANISM
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  backgroundColor: heatApplied ? 'rgba(245, 158, 11, 0.18)' : 'rgba(16, 185, 129, 0.18)',
                  border: `1.5px solid ${heatApplied ? '#f59e0b' : '#10b981'}`,
                  color: heatApplied ? '#f59e0b' : '#34d399',
                  padding: '4px 12px',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: 800,
                  fontFamily: 'monospace',
                  letterSpacing: '0.5px',
                }}
              >
                {thermoBadge}
              </span>
              {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
            </div>
          </div>

          <h1
            style={{
              fontSize: '42px',
              fontWeight: 900,
              color: '#f8fafc',
              lineHeight: 1.15,
              margin: 0,
              letterSpacing: '-0.5px',
            }}
          >
            {title}
          </h1>
        </div>
      </div>

      {/* 2. CENTER INTERACTIVE MOLECULAR REACTION VESSEL */}
      <div
        style={{
          height: vesselHeight || '840px',
          backgroundColor: '#070d14',
          borderRadius: '24px',
          border: '1.5px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.85)',
          padding: '20px 24px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxSizing: 'border-box',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Conditions bar */}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '18px', fontWeight: 700, color: '#94a3b8', fontFamily: 'monospace' }}>
              REAGENTS & SOLVENT:
            </span>
            <span
              style={{
                backgroundColor: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                color: '#38bdf8',
                padding: '3px 10px',
                borderRadius: '6px',
                fontSize: '18px',
                fontWeight: 700,
                fontFamily: 'monospace',
              }}
            >
              {reagents}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                backgroundColor: heatApplied ? 'rgba(239, 68, 68, 0.16)' : 'rgba(16, 185, 129, 0.14)',
                border: `1px solid ${heatApplied ? '#ef4444' : '#10b981'}`,
                color: heatApplied ? '#f87171' : '#34d399',
                padding: '4px 12px',
                borderRadius: '6px',
                fontSize: '18px',
                fontWeight: 800,
                fontFamily: 'monospace',
              }}
            >
              T = {tempKelvin} K {heatApplied ? '• Δ HEAT' : '• 25°C'}
            </span>
            <span
              style={{
                backgroundColor: isPhase2 ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                border: `1px solid ${isPhase2 ? '#f59e0b' : 'rgba(255, 255, 255, 0.15)'}`,
                color: isPhase2 ? '#fbbf24' : '#94a3b8',
                padding: '4px 12px',
                borderRadius: '6px',
                fontSize: '18px',
                fontWeight: 800,
                fontFamily: 'monospace',
              }}
            >
              {subMode === 'steric_blockade'
                ? (isPhase1 ? 'PHASE 1: NUCLEOPHILE APPROACH' : 'PHASE 2: SHOCKWAVE BOUNCE')
                : subMode === 'sn1_ionization'
                ? (isPhase1 ? 'PHASE 1: THERMAL EXCITATION' : 'PHASE 2: HETEROLYTIC CLEAVAGE')
                : subMode === 'sn1_racemic'
                ? (isPhase1 ? 'PHASE 1: DUAL-FACE APPROACH' : 'PHASE 2: RACEMIC RESOLUTION')
                : (isPhase1 ? 'PHASE 1: NUCLEOPHILE APPROACH' : isPhase2 ? 'PHASE 2: TRANSITION STATE [‡]' : 'PHASE 3: INVERTED PRODUCT')}
            </span>
          </div>
        </div>

        {/* SVG Molecular Canvas */}
        <svg
          width="910"
          height={svgHeight}
          viewBox={`0 0 910 ${svgHeight}`}
          style={{ overflow: 'visible', margin: '0 auto' }}
        >
          <defs>
            <marker id="electronArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#f59e0b" />
            </marker>
            <marker id="leavingArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#ef4444" />
            </marker>
          </defs>

          {/* Background Grid Pattern */}
          <line x1="40" y1="180" x2="870" y2="180" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
          <line x1="40" y1={cY} x2="870" y2={cY} stroke="rgba(255,255,255,0.04)" strokeWidth="1" />

          {/* Render One of the 4 Distinct Reaction Mechanisms */}
          {subMode === 'steric_blockade' && renderStericBlockadeSVG()}
          {subMode === 'sn1_ionization' && renderSN1IonizationSVG()}
          {subMode === 'sn1_racemic' && renderSN1RacemicSVG()}
          {subMode === 'sn2_concerted' && renderSN2ConcertedSVG()}
        </svg>

        {/* Reaction Phase Footer Strip */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            paddingTop: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '18px', fontFamily: 'monospace' }}>
            <span>MECHANISM STATUS:</span>
            <span style={{ color: subMode === 'steric_blockade' ? '#ef4444' : '#10b981', fontWeight: 800 }}>
              {subMode === 'steric_blockade'
                ? 'STERIC HINDRANCE BLOCKADE (ATTACK DEFLECTED)'
                : subMode === 'sn1_ionization'
                ? 'STEP 1 (SLOW): HETEROLYTIC CLEAVAGE -> PLANAR sp² CARBOCATION'
                : subMode === 'sn1_racemic'
                ? '50% (R) FRONT + 50% (S) BACK = RACEMIC MIXTURE'
                : '180° BACKSIDE ATTACK -> WALDEN INVERSION'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '18px', fontFamily: 'monospace' }}>
            <span>HYBRIDIZATION:</span>
            <span style={{ color: '#38bdf8', fontWeight: 800 }}>
              {subMode.startsWith('sn1') ? 'sp² TRIGONAL PLANAR' : (isPhase1 ? 'sp³ TETRAHEDRAL' : isPhase2 ? 'sp² TRIGONAL PLANAR‡' : 'sp³ INVERTED')}
            </span>
          </div>
        </div>
      </div>

      {/* 3. BOTTOM SPLIT ENERGY & KINETICS CARDS (460px tall - Only displayed in full_dashboard mode) */}
      {!isSpotlight && !isCompact && (
        <div
          style={{
            height: '460px',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '20px',
            boxSizing: 'border-box',
          }}
        >
          {/* Left Column: Reaction Coordinate Energy Profile */}
          <div
            style={{
              backgroundColor: '#0a0f18',
              borderRadius: '20px',
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.65)',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#f59e0b', fontFamily: 'monospace', letterSpacing: '1px' }}>
                REACTION COORDINATE • ENERGY PROFILE
              </span>
              <span
                style={{
                  backgroundColor: 'rgba(245, 158, 11, 0.15)',
                  border: '1px solid #f59e0b',
                  color: '#f59e0b',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  fontFamily: 'monospace',
                }}
              >
                Ea = {energyProfile.activation_energy} kJ/mol
              </span>
            </div>

            <svg width="420" height="320" viewBox="0 0 460 380" style={{ overflow: 'visible', margin: '0 auto' }}>
              <line x1="50" y1="40" x2="50" y2="350" stroke="#475569" strokeWidth="2" />
              <line x1="50" y1="350" x2="440" y2="350" stroke="#475569" strokeWidth="2" />
              <text x="35" y="50" fill="#94a3b8" fontSize="16" fontFamily="monospace" textAnchor="end">
                G
              </text>
              <text x="440" y="375" fill="#94a3b8" fontSize="15" fontFamily="monospace" textAnchor="end">
                Reaction Progress →
              </text>

              {/* Potential Energy Bezier Curve (1 or 2 barriers) */}
              {energyProfile.num_barriers === 2 ? (
                <path
                  d="M 60 280 C 110 280 130 110 180 110 C 220 110 240 210 280 210 C 320 210 340 130 380 130 C 410 130 420 320 440 320"
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="3.5"
                />
              ) : (
                <path
                  d="M 60 260 C 140 260 190 80 250 80 C 310 80 350 340 430 340"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="3.5"
                />
              )}

              {/* Glowing Real-Time Tracking Dot */}
              <circle
                cx={curveX}
                cy={curveY}
                r="10"
                fill="#fbbf24"
                stroke="#ffffff"
                strokeWidth="2.5"
              />
            </svg>

            <div
              style={{
                padding: '8px 12px',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                borderRadius: '8px',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                fontSize: '16px',
                color: '#38bdf8',
                fontFamily: 'monospace',
                textAlign: 'center',
              }}
            >
              ΔG = {energyProfile.delta_g} kJ/mol ({energyProfile.num_barriers === 2 ? '2-Step Intermediate Pathway' : '1-Step Concerted Pathway'})
            </div>
          </div>

          {/* Right Column: Kinetics & Stereochemistry Telemetry */}
          <div
            style={{
              backgroundColor: '#0a0f18',
              borderRadius: '20px',
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.65)',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#10b981', fontFamily: 'monospace', letterSpacing: '1px' }}>
                KINETICS & STEREOCHEMISTRY
              </span>
              <span
                style={{
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid #10b981',
                  color: '#34d399',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  fontFamily: 'monospace',
                }}
              >
                ORDER = {subMode.startsWith('sn1') ? '1' : '2'}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  backgroundColor: '#111726',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '12px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#94a3b8', fontFamily: 'monospace' }}>
                  EXPERIMENTALLY OBSERVED RATE LAW:
                </span>
                <span style={{ fontSize: '22px', fontWeight: 900, color: '#38bdf8', fontFamily: 'monospace' }}>
                  {rateLaw}
                </span>
              </div>

              <div
                style={{
                  backgroundColor: '#111726',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '12px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#94a3b8', fontFamily: 'monospace' }}>
                  STEREOCHEMICAL OUTCOME:
                </span>
                <span style={{ fontSize: '20px', fontWeight: 800, color: '#10b981', fontFamily: 'monospace' }}>
                  {stereochem}
                </span>
              </div>
            </div>

            <div
              style={{
                padding: '8px 12px',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderRadius: '8px',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                fontSize: '16px',
                color: '#34d399',
                fontFamily: 'monospace',
                textAlign: 'center',
              }}
            >
              {subMode.startsWith('sn1')
                ? 'Polar Protic Solvent Stabilizes Carbocation RDS'
                : 'Polar Aprotic Solvent Accelerates Nu⁻ Nucleophilicity'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChemistryScene;
