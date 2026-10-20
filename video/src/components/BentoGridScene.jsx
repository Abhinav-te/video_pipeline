import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { SparklesIcon, LayersIcon } from './SvgIcons';

/**
 * Animated SVG Mini-Visualization for Bento Cards
 * Large 180px canvases with rich multi-stage animations.
 */
const MiniCanvas = ({ algoType, cardIndex = 0, isHighlighted, frame, domain = '' }) => {
  const normType = (algoType || '').toLowerCase();

  // K-Means: animated colored point clusters with moving X centroids
  if (normType.includes('kmeans') || normType.includes('k-means')) {
    const pulse = 1 + Math.sin(frame * 0.15) * 0.15;
    const moveX = Math.sin(frame * 0.08) * 8;
    const moveY = Math.cos(frame * 0.08) * 6;

    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        {/* Cluster A (Cyan) */}
        <circle cx="85" cy="85" r="8" fill="#38bdf8" opacity="0.85" />
        <circle cx="115" cy="65" r="7" fill="#38bdf8" opacity="0.85" />
        <circle cx="95" cy="115" r="8" fill="#38bdf8" opacity="0.85" />
        <circle cx="68" cy="80" r="6" fill="#38bdf8" opacity="0.75" />
        <circle cx="120" cy="105" r="7" fill="#38bdf8" opacity="0.8" />
        {/* Centroid A */}
        <g transform={`translate(${95 + moveX}, ${88 + moveY}) scale(${pulse}) translate(-95, -88)`}>
          <line x1="82" y1="75" x2="108" y2="101" stroke="#f59e0b" strokeWidth="4.5" strokeLinecap="round" />
          <line x1="108" y1="75" x2="82" y2="101" stroke="#f59e0b" strokeWidth="4.5" strokeLinecap="round" />
        </g>

        {/* Cluster B (Emerald) */}
        <circle cx="280" cy="75" r="8" fill="#34d399" opacity="0.85" />
        <circle cx="305" cy="95" r="7" fill="#34d399" opacity="0.85" />
        <circle cx="260" cy="115" r="8" fill="#34d399" opacity="0.85" />
        <circle cx="310" cy="60" r="6" fill="#34d399" opacity="0.75" />
        <circle cx="255" cy="70" r="7" fill="#34d399" opacity="0.8" />
        {/* Centroid B */}
        <g transform={`translate(${280 - moveX}, ${85 - moveY}) scale(${pulse}) translate(-280, -85)`}>
          <line x1="267" y1="72" x2="293" y2="98" stroke="#f59e0b" strokeWidth="4.5" strokeLinecap="round" />
          <line x1="293" y1="72" x2="267" y2="98" stroke="#f59e0b" strokeWidth="4.5" strokeLinecap="round" />
        </g>
      </svg>
    );
  }

  // Dendrogram / Hierarchical: tree drawing with branching hierarchy
  if (normType.includes('dendro') || normType.includes('hierarch')) {
    const branchGrow = Math.min(1, ((frame % 90) + 10) / 70);
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <path
          d={`M 190 25 L 190 60 M 100 60 L 280 60 M 100 60 L 100 ${60 + 55 * branchGrow} M 280 60 L 280 ${60 + 55 * branchGrow} M 60 115 L 140 115 M 60 115 L 60 150 M 140 115 L 140 150 M 240 115 L 320 115 M 240 115 L 240 150 M 320 115 L 320 150`}
          fill="none"
          stroke={isHighlighted ? '#f59e0b' : '#38bdf8'}
          strokeWidth="3.5"
          strokeLinecap="round"
        />
        {[60, 140, 240, 320].map((cx, i) => (
          <circle key={i} cx={cx} cy="150" r="7" fill="#34d399" />
        ))}
      </svg>
    );
  }

  // DBSCAN: wide featured card with sweeping radar rings & noise handling
  if (normType.includes('dbscan') || normType.includes('density')) {
    const radarSweep = (frame * 3) % 360;
    const scanOffset = Math.sin(frame * 0.1) * 25;

    return (
      <svg width="100%" height="180" viewBox="0 0 840 180">
        {/* Core Cluster 1 (Left) */}
        <circle cx={240 + scanOffset} cy="90" r="65" fill="rgba(245, 158, 11, 0.12)" stroke="#f59e0b" strokeWidth="2.5" strokeDasharray="8 6" />
        {[
          { x: 210, y: 75 }, { x: 250, y: 70 }, { x: 270, y: 100 },
          { x: 230, y: 110 }, { x: 260, y: 85 }, { x: 215, y: 95 }
        ].map((pt, i) => (
          <circle key={`d1-${i}`} cx={pt.x} cy={pt.y} r="8" fill="#10b981" />
        ))}

        {/* Core Cluster 2 (Right) */}
        <circle cx={580 - scanOffset} cy="90" r="65" fill="rgba(56, 189, 248, 0.12)" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray="8 6" />
        {[
          { x: 550, y: 75 }, { x: 590, y: 70 }, { x: 610, y: 100 },
          { x: 570, y: 110 }, { x: 600, y: 85 }, { x: 555, y: 95 }
        ].map((pt, i) => (
          <circle key={`d2-${i}`} cx={pt.x} cy={pt.y} r="8" fill="#38bdf8" />
        ))}

        {/* Noise Outliers (X) */}
        {[
          { x: 80, y: 40 }, { x: 120, y: 140 }, { x: 740, y: 50 }, { x: 780, y: 130 }
        ].map((pt, i) => (
          <g key={`noise-${i}`} stroke="#94a3b8" strokeWidth="3">
            <line x1={pt.x - 7} y1={pt.y - 7} x2={pt.x + 7} y2={pt.y + 7} />
            <line x1={pt.x + 7} y1={pt.y - 7} x2={pt.x - 7} y2={pt.y + 7} />
          </g>
        ))}
      </svg>
    );
  }

  // PCA: rotating projection vector with points projecting onto axis
  if (normType.includes('pca')) {
    const angle = (frame * 0.04) % (2 * Math.PI);
    const cosA = Math.cos(angle);
    const sinA = Math.sin(angle);

    return (
      <svg width="100%" height="220" viewBox="0 0 400 220">
        {/* Scatter Points */}
        {[
          { x: 140, y: 150 }, { x: 170, y: 130 }, { x: 200, y: 110 },
          { x: 230, y: 90 }, { x: 260, y: 70 }, { x: 190, y: 140 }
        ].map((pt, i) => (
          <circle key={i} cx={pt.x} cy={pt.y} r="7" fill="#64748b" opacity="0.7" />
        ))}
        {/* Primary Axis (PC1) */}
        <line
          x1={200 - 130 * cosA}
          y1={110 - 130 * sinA}
          x2={200 + 130 * cosA}
          y2={110 + 130 * sinA}
          stroke="#f59e0b"
          strokeWidth="4"
        />
        <text x="290" y="55" fill="#f59e0b" fontSize="22" fontWeight="bold" fontFamily="monospace">
          PC1
        </text>
      </svg>
    );
  }

  // Chemistry: Substrate bulkiness comparison (1° unhindered vs 3° bulky)
  if (normType.includes('substrate') || normType.includes('bulk')) {
    return (
      <svg width="100%" height="200" viewBox="0 0 380 200">
        <g transform="translate(10, 0)">
          <rect x="10" y="20" width="165" height="160" rx="14" fill="rgba(56, 189, 248, 0.08)" stroke="rgba(56, 189, 248, 0.3)" />
          <text x="92" y="48" fill="#38bdf8" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">1° / METHYL</text>
          <circle cx="92" cy="100" r="22" fill="#0284c7" stroke="#38bdf8" strokeWidth="2.5" />
          <text x="92" y="107" fill="#ffffff" fontSize="20" fontWeight="bold" textAnchor="middle">C</text>
          <circle cx="58" cy="100" r="10" fill="#64748b" />
          <text x="58" y="104" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">H</text>
          <circle cx="132" cy="100" r="14" fill="#f43f5e" />
          <text x="132" y="105" fill="#ffffff" fontSize="13" fontWeight="bold" textAnchor="middle">Br</text>
          <text x="92" y="160" fill="#34d399" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">SN2 UNHINDERED</text>
        </g>
        <g transform="translate(185, 0)">
          <rect x="10" y="20" width="165" height="160" rx="14" fill="rgba(245, 158, 11, 0.08)" stroke="rgba(245, 158, 11, 0.3)" />
          <text x="92" y="48" fill="#f59e0b" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">3° TERTIARY</text>
          <circle cx="92" cy="100" r="22" fill="#d97706" stroke="#f59e0b" strokeWidth="2.5" />
          <text x="92" y="107" fill="#ffffff" fontSize="20" fontWeight="bold" textAnchor="middle">C</text>
          <circle cx="60" cy="74" r="14" fill="#9333ea" />
          <text x="60" y="78" fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">CH₃</text>
          <circle cx="60" cy="126" r="14" fill="#9333ea" />
          <text x="60" y="130" fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">CH₃</text>
          <circle cx="132" cy="100" r="14" fill="#f43f5e" />
          <text x="132" y="105" fill="#ffffff" fontSize="13" fontWeight="bold" textAnchor="middle">Br</text>
          <text x="92" y="160" fill="#f59e0b" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">SN1 STABLE C⁺</text>
        </g>
      </svg>
    );
  }

  // Chemistry: Nucleophile strength comparison (Strong Nu- vs Weak Nu)
  if (normType.includes('nucleophile') || normType.includes('strength')) {
    return (
      <svg width="100%" height="200" viewBox="0 0 380 200">
        <g transform="translate(10, 0)">
          <rect x="10" y="20" width="165" height="160" rx="14" fill="rgba(56, 189, 248, 0.08)" stroke="rgba(56, 189, 248, 0.3)" />
          <text x="92" y="48" fill="#38bdf8" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">STRONG Nu⁻ (SN2)</text>
          <circle cx="70" cy="98" r="22" fill="#0284c7" stroke="#38bdf8" strokeWidth="2.5" />
          <text x="70" y="105" fill="#ffffff" fontSize="16" fontWeight="bold" textAnchor="middle">OH⁻</text>
          <line x1="98" y1="98" x2="135" y2="98" stroke="#38bdf8" strokeWidth="4" strokeLinecap="round" />
          <polygon points="135,92 147,98 135,104" fill="#38bdf8" />
          <text x="92" y="160" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">OH⁻, CN⁻, RO⁻</text>
        </g>
        <g transform="translate(185, 0)">
          <rect x="10" y="20" width="165" height="160" rx="14" fill="rgba(245, 158, 11, 0.08)" stroke="rgba(245, 158, 11, 0.3)" />
          <text x="92" y="48" fill="#f59e0b" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">WEAK Nu (SN1)</text>
          <circle cx="92" cy="98" r="22" fill="#b45309" stroke="#f59e0b" strokeWidth="2.5" />
          <text x="92" y="105" fill="#ffffff" fontSize="15" fontWeight="bold" textAnchor="middle">H₂O</text>
          <text x="92" y="160" fill="#f59e0b" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">H₂O, ROH (Neutral)</text>
        </g>
      </svg>
    );
  }

  // Chemistry: Solvent polarity (Polar Aprotic vs Polar Protic)
  if (normType.includes('solvent') || normType.includes('polar')) {
    return (
      <svg width="100%" height="200" viewBox="0 0 380 200">
        <g transform="translate(10, 0)">
          <rect x="10" y="20" width="165" height="160" rx="14" fill="rgba(56, 189, 248, 0.08)" stroke="rgba(56, 189, 248, 0.3)" />
          <text x="92" y="48" fill="#38bdf8" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">POLAR APROTIC</text>
          <rect x="35" y="70" width="115" height="48" rx="8" fill="#0f172a" stroke="#38bdf8" strokeWidth="2" />
          <text x="92" y="100" fill="#38bdf8" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Acetone / DMSO</text>
          <text x="92" y="160" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">SN2 NAKED Nu⁻</text>
        </g>
        <g transform="translate(185, 0)">
          <rect x="10" y="20" width="165" height="160" rx="14" fill="rgba(245, 158, 11, 0.08)" stroke="rgba(245, 158, 11, 0.3)" />
          <text x="92" y="48" fill="#f59e0b" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">POLAR PROTIC</text>
          <rect x="35" y="70" width="115" height="48" rx="8" fill="#0f172a" stroke="#f59e0b" strokeWidth="2" />
          <text x="92" y="100" fill="#f59e0b" fontSize="15" fontWeight="bold" fontFamily="monospace" textAnchor="middle">H₂O / EtOH</text>
          <text x="92" y="160" fill="#f59e0b" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">SN1 IONIZING</text>
        </g>
      </svg>
    );
  }

  // Chemistry: Stereochemistry (100% Inversion vs 50/50 Racemic)
  if (normType.includes('stereo') || normType.includes('chirality')) {
    return (
      <svg width="100%" height="200" viewBox="0 0 380 200">
        <g transform="translate(10, 0)">
          <rect x="10" y="20" width="165" height="160" rx="14" fill="rgba(56, 189, 248, 0.08)" stroke="rgba(56, 189, 248, 0.3)" />
          <text x="92" y="48" fill="#38bdf8" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">SN2 STEREOCHEM</text>
          <path d="M 60 90 Q 92 65 124 90" fill="none" stroke="#38bdf8" strokeWidth="3.5" />
          <line x1="92" y1="65" x2="92" y2="115" stroke="#38bdf8" strokeWidth="3" />
          <text x="92" y="138" fill="#ffffff" fontSize="13" fontWeight="bold" textAnchor="middle">100% INVERSION</text>
          <text x="92" y="160" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Walden Umbrella</text>
        </g>
        <g transform="translate(185, 0)">
          <rect x="10" y="20" width="165" height="160" rx="14" fill="rgba(168, 85, 247, 0.08)" stroke="rgba(168, 85, 247, 0.3)" />
          <text x="92" y="48" fill="#c084fc" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">SN1 STEREOCHEM</text>
          <path d="M 65 80 L 92 100 L 65 120" fill="none" stroke="#34d399" strokeWidth="2.5" />
          <path d="M 120 80 L 92 100 L 120 120" fill="none" stroke="#a855f7" strokeWidth="2.5" />
          <text x="92" y="138" fill="#ffffff" fontSize="13" fontWeight="bold" textAnchor="middle">50% R + 50% S</text>
          <text x="92" y="160" fill="#c084fc" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Racemic Mixture</text>
        </g>
      </svg>
    );
  }

  // Electrical: KCL & KVL Laws (node & loop currents)
  if (normType.includes('kcl') || normType.includes('kvl') || normType.includes('loop')) {
    const dashOffset = (frame * 3) % 40;
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <rect x="50" y="30" width="280" height="120" rx="16" fill="none" stroke="#00f0ff" strokeWidth="3" strokeDasharray="10 6" strokeDashoffset={-dashOffset} />
        <circle cx="190" cy="30" r="12" fill="#eab308" stroke="#ffffff" strokeWidth="2.5" />
        <text x="190" y="20" fill="#eab308" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">NODE A (ΣI=0)</text>
        <path d="M 160 150 L 170 140 L 180 160 L 190 140 L 200 160 L 210 140 L 220 150" fill="none" stroke="#38bdf8" strokeWidth="4" />
        <text x="190" y="172" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">R₁ = 6.0 Ω</text>
        <polygon points="120,25 135,30 120,35" fill="#00f0ff" />
        <text x="100" y="55" fill="#00f0ff" fontSize="14" fontWeight="bold" fontFamily="monospace">I₁ →</text>
      </svg>
    );
  }

  // Electrical: Thévenin & Norton Reduction (2-terminal source)
  if (normType.includes('thevenin') || normType.includes('norton') || normType.includes('equiv')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <circle cx="90" cy="90" r="28" fill="rgba(0, 240, 255, 0.12)" stroke="#00f0ff" strokeWidth="3" />
        <text x="90" y="97" fill="#00f0ff" fontSize="20" fontWeight="bold" textAnchor="middle">Vth</text>
        <line x1="118" y1="90" x2="160" y2="90" stroke="#00f0ff" strokeWidth="3" />
        <rect x="160" y="76" width="60" height="28" rx="6" fill="#141824" stroke="#eab308" strokeWidth="2.5" />
        <text x="190" y="95" fill="#eab308" fontSize="14" fontWeight="bold" textAnchor="middle">Rth</text>
        <line x1="220" y1="90" x2="290" y2="90" stroke="#00f0ff" strokeWidth="3" />
        <circle cx="290" cy="90" r="7" fill="#34d399" />
        <text x="310" y="95" fill="#34d399" fontSize="16" fontWeight="bold" fontFamily="monospace">A</text>
        <circle cx="290" cy="140" r="7" fill="#34d399" />
        <line x1="90" y1="118" x2="90" y2="140" stroke="#00f0ff" strokeWidth="3" />
        <line x1="90" y1="140" x2="290" y2="140" stroke="#00f0ff" strokeWidth="3" />
        <text x="310" y="145" fill="#34d399" fontSize="16" fontWeight="bold" fontFamily="monospace">B</text>
        <text x="190" y="165" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">RL = Rth (Max Power)</text>
      </svg>
    );
  }

  // Electrical: Economic Dispatch & Marginal Cost Curve
  if (normType.includes('dispatch') || normType.includes('marginal') || normType.includes('cost')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <line x1="60" y1="140" x2="330" y2="140" stroke="#64748b" strokeWidth="2" />
        <line x1="60" y1="20" x2="60" y2="140" stroke="#64748b" strokeWidth="2" />
        <line x1="70" y1="120" x2="310" y2="40" stroke="#eab308" strokeWidth="4" />
        <circle cx="190" cy="80" r="8" fill="#eab308" stroke="#ffffff" strokeWidth="2" />
        <text x="205" y="75" fill="#eab308" fontSize="14" fontWeight="bold" fontFamily="monospace">λ = $34.50/MWh</text>
        <text x="190" y="165" fill="#94a3b8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Power Output P (MW) →</text>
        <text x="65" y="30" fill="#eab308" fontSize="13" fontWeight="bold" fontFamily="monospace">$/MWh ↑</text>
      </svg>
    );
  }

  // Electrical: Optimal Power Flow & Transmission Corridor
  if (normType.includes('opf') || normType.includes('grid') || normType.includes('power_flow')) {
    const pulseThermal = 0.5 + 0.5 * Math.sin(frame * 0.1);
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <rect x="50" y="50" width="80" height="35" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2.5" />
        <text x="90" y="73" fill="#00f0ff" fontSize="14" fontWeight="bold" textAnchor="middle">BUS 1 (765kV)</text>
        <rect x="250" y="50" width="80" height="35" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2.5" />
        <text x="290" y="73" fill="#00f0ff" fontSize="14" fontWeight="bold" textAnchor="middle">BUS 2 (230kV)</text>
        <line x1="130" y1="67" x2="250" y2="67" stroke="#ef4444" strokeWidth="5" strokeDasharray="8 4" />
        <rect x="70" y="115" width="240" height="18" rx="9" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
        <rect x="72" y="117" width={180 + 35 * pulseThermal} height="14" rx="7" fill="#ef4444" />
        <text x="190" y="155" fill="#ef4444" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">THERMAL LOADING: 94.8%</text>
      </svg>
    );
  }

  // Mechanics: Force Equilibrium (ΣF = 0)
  if (normType.includes('force_equilibrium') || normType.includes('equilibrium')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <rect x="60" y="75" width="260" height="20" rx="4" fill="#334155" stroke="#38bdf8" strokeWidth="2" />
        <polygon points="80,95 65,125 95,125" fill="#0284c7" />
        <text x="80" y="145" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">RA = 15 kN ↑</text>
        <circle cx="300" cy="105" r="10" fill="#0284c7" />
        <line x1="285" y1="117" x2="315" y2="117" stroke="#38bdf8" strokeWidth="3" />
        <text x="300" y="145" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">RB = 15 kN ↑</text>
        <line x1="190" y1="20" x2="190" y2="70" stroke="#ef4444" strokeWidth="4" />
        <polygon points="183,65 190,75 197,65" fill="#ef4444" />
        <text x="190" y="16" fill="#ef4444" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">F = 30 kN ↓</text>
      </svg>
    );
  }

  // Mechanics: Torque Balance (Στ = 0)
  if (normType.includes('torque') || normType.includes('moment')) {
    const angle = Math.sin(frame * 0.08) * 8;
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <g transform={`rotate(${angle}, 190, 100)`}>
          <rect x="50" y="94" width="280" height="14" rx="4" fill="#475569" stroke="#f59e0b" strokeWidth="2" />
          <circle cx="80" cy="80" r="14" fill="#ef4444" />
          <text x="80" y="85" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle">m₁</text>
          <circle cx="300" cy="80" r="14" fill="#34d399" />
          <text x="300" y="85" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle">m₂</text>
        </g>
        <polygon points="190,105 170,145 210,145" fill="#d97706" />
        <text x="190" y="168" fill="#f59e0b" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Στ = F₁·r₁ - F₂·r₂ = 0</text>
      </svg>
    );
  }

  // Mechanics: Shear & Bending (V & M)
  if (normType.includes('shear') || normType.includes('bending')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <path d="M 60 45 L 190 45 L 190 85 L 320 85" fill="none" stroke="#38bdf8" strokeWidth="3" />
        <line x1="60" y1="65" x2="320" y2="65" stroke="#64748b" strokeWidth="1.5" strokeDasharray="4 4" />
        <text x="60" y="35" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace">+V_max</text>
        <text x="320" y="105" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="end">-V_max</text>
        <path d="M 60 160 Q 190 110 320 160" fill="none" stroke="#34d399" strokeWidth="3.5" />
        <circle cx="190" cy="135" r="6" fill="#34d399" />
        <text x="190" y="125" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">M_max = wL²/8</text>
      </svg>
    );
  }

  // Mechanics: Ramp & Axle Load Transfer
  if (normType.includes('axle') || normType.includes('ramp')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <polygon points="50,150 330,150 330,60" fill="rgba(56, 189, 248, 0.08)" stroke="#38bdf8" strokeWidth="2.5" />
        <g transform="translate(180, 85) rotate(-18)">
          <rect x="-30" y="-20" width="60" height="40" rx="6" fill="#0f172a" stroke="#f59e0b" strokeWidth="2.5" />
          <line x1="0" y1="-20" x2="0" y2="-55" stroke="#34d399" strokeWidth="3" />
          <polygon points="-6,-50 0,-58 6,-50" fill="#34d399" />
          <text x="10" y="-40" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace">N</text>
        </g>
        <text x="190" y="170" fill="#f59e0b" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Friction Threshold: fs ≤ μs·N</text>
      </svg>
    );
  }

  // Quantum: Schrödinger Evolution
  if (normType.includes('schrodinger') || normType.includes('evolution')) {
    const waveShift = (frame * 0.15) % (2 * Math.PI);
    const wavePoints = [];
    for (let x = 60; x <= 320; x += 5) {
      const envelope = Math.exp(-Math.pow((x - 190) / 60, 2));
      const osc = Math.sin((x * 0.1) - waveShift);
      const y = 90 - 50 * envelope * osc;
      wavePoints.push(`${x === 60 ? 'M' : 'L'} ${x} ${y.toFixed(1)}`);
    }
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <path d={wavePoints.join(' ')} fill="none" stroke="#a855f7" strokeWidth="3.5" />
        <text x="190" y="160" fill="#c084fc" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">iℏ ∂Ψ/∂t = ĤΨ (Wavepacket)</text>
      </svg>
    );
  }

  // Quantum: Tunneling
  if (normType.includes('tunneling') || normType.includes('barrier')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <rect x="150" y="30" width="80" height="110" fill="rgba(239, 68, 68, 0.18)" stroke="#ef4444" strokeWidth="2.5" />
        <text x="190" y="55" fill="#ef4444" fontSize="14" fontWeight="bold" textAnchor="middle">V₀ (E &lt; V₀)</text>
        <path d="M 60 90 Q 80 65 100 90 T 140 90 L 150 90" fill="none" stroke="#38bdf8" strokeWidth="3.5" />
        <path d="M 150 90 Q 180 93 230 115" fill="none" stroke="#f59e0b" strokeWidth="3" strokeDasharray="4 3" />
        <path d="M 230 115 Q 245 102 260 115 T 300 115" fill="none" stroke="#34d399" strokeWidth="2.5" />
        <text x="190" y="165" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">T ≈ exp(-2κL) Transmission</text>
      </svg>
    );
  }

  // Quantum: Heisenberg Uncertainty
  if (normType.includes('heisenberg') || normType.includes('uncertainty')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <path d="M 60 130 Q 120 40 180 130" fill="none" stroke="#38bdf8" strokeWidth="3.5" />
        <text x="120" y="150" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Δx (Position)</text>
        <path d="M 200 130 Q 260 20 320 130" fill="none" stroke="#a855f7" strokeWidth="3.5" />
        <text x="260" y="150" fill="#c084fc" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Δp (Momentum)</text>
        <text x="190" y="172" fill="#eab308" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Δx · Δp ≥ ℏ/2</text>
      </svg>
    );
  }

  // Quantum: Dirac Orbitals
  if (normType.includes('dirac') || normType.includes('orbital')) {
    const pulseOrb = 1 + 0.1 * Math.sin(frame * 0.12);
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <g transform={`translate(190, 85) scale(${pulseOrb})`}>
          <path d="M 0 0 C -35 -25 -35 -65 0 -65 C 35 -65 35 -25 0 0" fill="rgba(56, 189, 248, 0.4)" stroke="#38bdf8" strokeWidth="2.5" />
          <path d="M 0 0 C -35 25 -35 65 0 65 C 35 65 35 25 0 0" fill="rgba(168, 85, 247, 0.4)" stroke="#a855f7" strokeWidth="2.5" />
          <circle cx="0" cy="0" r="5" fill="#ffffff" />
        </g>
        <text x="190" y="165" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">p-Orbital Boundary Y_1,0(θ,φ)</text>
      </svg>
    );
  }

  // Code / CS Algorithms: Hash Table, Generator, Heap
  if (normType.includes('hash')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <rect x="70" y="30" width="100" height="35" rx="6" fill="#1e293b" stroke="#38bdf8" strokeWidth="2" />
        <text x="120" y="52" fill="#38bdf8" fontSize="14" fontWeight="bold" textAnchor="middle">key.hash()</text>
        <line x1="170" y1="47" x2="210" y2="47" stroke="#38bdf8" strokeWidth="3" />
        <polygon points="210,42 220,47 210,52" fill="#38bdf8" />
        <rect x="220" y="25" width="90" height="90" rx="8" fill="#0f172a" stroke="#34d399" strokeWidth="2" />
        <text x="265" y="50" fill="#34d399" fontSize="13" fontWeight="bold" textAnchor="middle">Bucket [3]</text>
        <text x="265" y="75" fill="#cbd5e1" fontSize="12" textAnchor="middle">O(1) Val</text>
        <text x="190" y="155" fill="#34d399" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Average O(1) Instant Lookup</text>
      </svg>
    );
  }

  if (normType.includes('generator') || normType.includes('stream')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <rect x="60" y="40" width="120" height="40" rx="8" fill="#1e293b" stroke="#eab308" strokeWidth="2" />
        <text x="120" y="65" fill="#eab308" fontSize="14" fontWeight="bold" textAnchor="middle">yield item</text>
        <line x1="180" y1="60" x2="230" y2="60" stroke="#eab308" strokeWidth="3" strokeDasharray="6 4" />
        <polygon points="230,55 240,60 230,65" fill="#eab308" />
        <circle cx="270" cy="60" r="18" fill="#10b981" />
        <text x="270" y="66" fill="#ffffff" fontSize="14" fontWeight="bold" textAnchor="middle">1</text>
        <text x="190" y="145" fill="#10b981" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">O(1) Memory Lazy Pipeline</text>
      </svg>
    );
  }

  if (normType.includes('heap') || normType.includes('tree')) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <circle cx="190" cy="35" r="16" fill="#0284c7" />
        <text x="190" y="41" fill="#ffffff" fontSize="14" fontWeight="bold" textAnchor="middle">4</text>
        <line x1="178" y1="47" x2="132" y2="78" stroke="#38bdf8" strokeWidth="2.5" />
        <line x1="202" y1="47" x2="248" y2="78" stroke="#38bdf8" strokeWidth="2.5" />
        <circle cx="120" cy="90" r="15" fill="#0284c7" />
        <text x="120" y="96" fill="#ffffff" fontSize="13" fontWeight="bold" textAnchor="middle">10</text>
        <circle cx="260" cy="90" r="15" fill="#0284c7" />
        <text x="260" y="96" fill="#ffffff" fontSize="13" fontWeight="bold" textAnchor="middle">7</text>
        <text x="190" y="150" fill="#38bdf8" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">Min-Heap Invariant: O(log n)</text>
      </svg>
    );
  }

  // t-SNE / UMAP: strictly only if explicitly requested for ML dimensionality reduction
  if (normType.includes('tsne') || normType.includes('umap')) {
    const sep = 1 + Math.sin(frame * 0.1) * 0.15;
    return (
      <svg width="100%" height="220" viewBox="0 0 400 220">
        <circle cx={130 - 10 * sep} cy="110" r="38" fill="none" stroke="#38bdf8" strokeWidth="4" strokeDasharray="8 6" />
        <circle cx={130 - 10 * sep} cy="110" r="14" fill="#38bdf8" />
        <circle cx={270 + 10 * sep} cy="80" r="38" fill="none" stroke="#a855f7" strokeWidth="4" strokeDasharray="8 6" />
        <circle cx={270 + 10 * sep} cy="80" r="14" fill="#a855f7" />
        <circle cx={220} cy={160 + 10 * sep} r="32" fill="none" stroke="#34d399" strokeWidth="4" strokeDasharray="8 6" />
        <circle cx={220} cy={160 + 10 * sep} r="12" fill="#34d399" />
      </svg>
    );
  }

  // 4 Distinct Domain-Aware Mini-SVGs for Bento Cards
  const slot = Math.abs(cardIndex || 0) % 4;
  const normDomain = (domain || '').toLowerCase();
  const isMathDomain = normDomain.includes('math') || normType.includes('limit') || normType.includes('integral') || normType.includes('riemann') || normType.includes('taylor') || normType.includes('curv') || normType.includes('extrema') || normType.includes('secant') || normType.includes('derivative');
  const isQuantumDomain = normDomain.includes('quantum') || normType.includes('schrodinger') || normType.includes('tunnel') || normType.includes('heisenberg') || normType.includes('dirac');
  const isMechanicsDomain = normDomain.includes('mechanic') || normType.includes('equilibrium') || normType.includes('torque') || normType.includes('shear') || normType.includes('axle') || normType.includes('truss');
  const isElectricalDomain = normDomain.includes('electr') || normType.includes('kcl') || normType.includes('thevenin') || normType.includes('dispatch') || normType.includes('opf');
  const isCodeDomain = normDomain.includes('code') || normDomain.includes('devtool') || normDomain.includes('system') || normDomain.includes('software') || normType.includes('latency') || normType.includes('lines') || normType.includes('cache') || normType.includes('conflict') || normType.includes('perf');

  // 1. PURE MATHEMATICS & CALCULUS MINI-SVGS
  if (isMathDomain) {
    if (slot === 0) {
      const secantShift = 30 * Math.max(0.05, (1 + Math.cos(frame * 0.08)) / 2);
      const x0 = 120;
      const y0 = 125;
      const x1 = 120 + secantShift + 40;
      const y1 = 125 - (secantShift + 40) * 0.85;
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="40" y1="140" x2="340" y2="140" stroke="#334155" strokeWidth="2" />
          <line x1="60" y1="20" x2="60" y2="150" stroke="#334155" strokeWidth="2" />
          <path d="M 60 140 Q 160 130 320 25" fill="none" stroke="#38bdf8" strokeWidth="3" />
          <line x1={x0 - 30} y1={y0 + 25} x2={x1 + 45} y2={y1 - 35} stroke="#f59e0b" strokeWidth="2.5" strokeDasharray="6 4" />
          <circle cx={x0} cy={y0} r="6" fill="#38bdf8" />
          <circle cx={x1} cy={y1} r="5" fill="#f59e0b" />
          <line x1={x0} y1={y0} x2={x1} y2={y0} stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="3 3" />
          <line x1={x1} y1={y0} x2={x1} y2={y1} stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="3 3" />
          <text x="190" y="22" fill="#f59e0b" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            SECANT → TANGENT LIMIT
          </text>
          <text x="190" y="166" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            lim Δx→0 [Δy / Δx] = f'(x)
          </text>
        </svg>
      );
    }
    if (slot === 1) {
      const bars = [
        { x: 80, w: 32, h: 42 },
        { x: 115, w: 32, h: 62 },
        { x: 150, w: 32, h: 78 },
        { x: 185, w: 32, h: 86 },
        { x: 220, w: 32, h: 80 },
        { x: 255, w: 32, h: 60 },
      ];
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="50" y1="140" x2="330" y2="140" stroke="#334155" strokeWidth="2" />
          {bars.map((b, i) => (
            <rect
              key={i}
              x={b.x}
              y={140 - b.h}
              width={b.w - 3}
              height={b.h}
              fill="rgba(52, 211, 153, 0.35)"
              stroke="#34d399"
              strokeWidth="2"
            />
          ))}
          <path d="M 60 130 C 120 68, 200 45, 310 130" fill="none" stroke="#38bdf8" strokeWidth="3" />
          <text x="190" y="24" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            RIEMANN AREA SUM ∫f(x)dx
          </text>
          <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            ACCUMULATED NET AREA: Σ f(xᵢ)·Δx
          </text>
        </svg>
      );
    }
    if (slot === 2) {
      const osc = Math.sin(frame * 0.1) * 8;
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="50" y1="140" x2="330" y2="140" stroke="#334155" strokeWidth="2" />
          <line x1="50" y1="20" x2="50" y2="140" stroke="#334155" strokeWidth="2" />
          <path d="M 60 130 Q 190 20 320 130" fill="none" stroke="#64748b" strokeWidth="2" strokeDasharray="6 4" />
          <path d={`M 60 ${130 - osc} Q 190 ${25 + osc * 0.5} 320 ${130 - osc}`} fill="none" stroke="#a855f7" strokeWidth="3.5" />
          <circle cx="190" cy="25" r="5" fill="#f59e0b" />
          <text x="190" y="22" fill="#a855f7" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            POLYNOMIAL CONVERGENCE
          </text>
          <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            TAYLOR EXPANSION: Pₙ(x) → f(x)
          </text>
        </svg>
      );
    }
    // Card 3: Critical Extrema (slot === 3)
    const peakGlow = 0.5 + 0.5 * Math.sin(frame * 0.14);
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <line x1="50" y1="140" x2="330" y2="140" stroke="#334155" strokeWidth="2" />
        <path d="M 70 135 Q 190 30 310 135" fill="none" stroke="#38bdf8" strokeWidth="3" />
        <line x1="130" y1="30" x2="250" y2="30" stroke="#f59e0b" strokeWidth="2.5" strokeDasharray="6 4" />
        <circle cx="190" cy="30" r={6 + 2 * peakGlow} fill="#f59e0b" stroke="#ffffff" strokeWidth="2" />
        <line x1="190" y1="30" x2="190" y2="140" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4 4" />
        <text x="190" y="22" fill="#f59e0b" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          CRITICAL POINT f'(x) = 0
        </text>
        <text x="190" y="166" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          EXTREMA &amp; CONCAVITY: f''(x) &lt; 0
        </text>
      </svg>
    );
  }

  // 2. QUANTUM MECHANICS MINI-SVGS
  if (isQuantumDomain) {
    if (slot === 0 || normType.includes('schrodinger')) {
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="40" y1="90" x2="340" y2="90" stroke="#334155" strokeWidth="1.5" />
          <path d="M 60 90 Q 120 40 190 90 T 320 90" fill="none" stroke="#c084fc" strokeWidth="3" />
          <path d="M 100 90 Q 190 20 280 90" fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="4 4" />
          <text x="190" y="24" fill="#c084fc" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            WAVEFUNCTION Ψ(x,t)
          </text>
          <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            iℏ ∂Ψ/∂t = ĤΨ • UNITARY PROPAGATION
          </text>
        </svg>
      );
    }
    if (slot === 1 || normType.includes('tunnel')) {
      const decay = Math.sin(frame * 0.1) * 4;
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <rect x="150" y="40" width="70" height="90" rx="4" fill="rgba(192, 132, 252, 0.15)" stroke="#c084fc" strokeWidth="2" />
          <path d="M 60 85 Q 100 60 150 85" fill="none" stroke="#38bdf8" strokeWidth="3" />
          <path d={`M 150 85 Q 185 ${95 + decay} 220 110`} fill="none" stroke="#f59e0b" strokeWidth="2.5" />
          <path d="M 220 110 Q 270 95 320 110" fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="4 4" />
          <text x="190" y="24" fill="#f59e0b" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            BARRIER TUNNELING T &gt; 0
          </text>
          <text x="190" y="166" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            EVANESCENT PENETRATION: T ≈ e^(-2κL)
          </text>
        </svg>
      );
    }
    if (slot === 2 || normType.includes('heisenberg')) {
      const squeeze = 18 * Math.sin(frame * 0.12);
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <ellipse cx="130" cy="85" rx={35 + squeeze} ry={25 - squeeze * 0.5} fill="rgba(56, 189, 248, 0.2)" stroke="#38bdf8" strokeWidth="2" />
          <text x="130" y="90" fill="#38bdf8" fontSize="12" fontWeight="bold" textAnchor="middle">Δx</text>
          <ellipse cx="250" cy="85" rx={35 - squeeze} ry={25 + squeeze * 0.5} fill="rgba(168, 85, 247, 0.2)" stroke="#a855f7" strokeWidth="2" />
          <text x="250" y="90" fill="#a855f7" fontSize="12" fontWeight="bold" textAnchor="middle">Δp</text>
          <text x="190" y="24" fill="#a855f7" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            UNCERTAINTY Δx·Δp ≥ ℏ/2
          </text>
          <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            CANONICAL COMMUTATOR: [x̂, p̂] = iℏ
          </text>
        </svg>
      );
    }
    // Card 3: Dirac Spinor
    const rot = (frame * 2.5) % 360;
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <g transform={`translate(190, 85) rotate(${rot}) translate(-190, -85)`}>
          <ellipse cx="190" cy="60" rx="18" ry="28" fill="rgba(192, 132, 252, 0.3)" stroke="#c084fc" strokeWidth="2" />
          <ellipse cx="190" cy="110" rx="18" ry="28" fill="rgba(56, 189, 248, 0.3)" stroke="#38bdf8" strokeWidth="2" />
        </g>
        <circle cx="190" cy="85" r="5" fill="#ffffff" />
        <text x="190" y="24" fill="#c084fc" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          SPINOR ORBITAL STATE
        </text>
        <text x="190" y="166" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          RELATIVISTIC DIRAC 4-SPINOR (1s, 2p)
        </text>
      </svg>
    );
  }

  // 3. STRUCTURAL MECHANICS MINI-SVGS
  if (isMechanicsDomain) {
    if (slot === 0 || normType.includes('force')) {
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="190" y1="85" x2="270" y2="85" stroke="#34d399" strokeWidth="3" />
          <line x1="190" y1="85" x2="110" y2="85" stroke="#34d399" strokeWidth="3" />
          <line x1="190" y1="85" x2="190" y2="35" stroke="#38bdf8" strokeWidth="3" />
          <line x1="190" y1="85" x2="190" y2="135" stroke="#38bdf8" strokeWidth="3" />
          <circle cx="190" cy="85" r="8" fill="#f59e0b" />
          <text x="190" y="24" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            FORCE BALANCE ΣF = 0
          </text>
          <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            ΣF_x = 0 • ΣF_y = 0 TRANSLATIONAL EQUILIBRIUM
          </text>
        </svg>
      );
    }
    if (slot === 1 || normType.includes('torque')) {
      const tilt = Math.sin(frame * 0.08) * 8;
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="90" y1={85 + tilt} x2="290" y2={85 - tilt} stroke="#f59e0b" strokeWidth="5" strokeLinecap="round" />
          <polygon points="180,120 200,120 190,87" fill="#64748b" />
          <line x1="70" y1="120" x2="310" y2="120" stroke="#334155" strokeWidth="2" />
          <text x="190" y="24" fill="#f59e0b" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            MOMENT EQUILIBRIUM Στ = 0
          </text>
          <text x="190" y="166" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            ZERO ROTATIONAL MOMENT ABOUT PIN SUPPORT
          </text>
        </svg>
      );
    }
    if (slot === 2 || normType.includes('shear')) {
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="60" y1="85" x2="320" y2="85" stroke="#334155" strokeWidth="1.5" />
          <path d="M 70 85 Q 190 25 310 85" fill="none" stroke="#38bdf8" strokeWidth="3" />
          <circle cx="190" cy="25" r="5" fill="#f59e0b" />
          <text x="190" y="22" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            BENDING MOMENT PEAK
          </text>
          <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            INTERNAL SHEAR &amp; MOMENT: dM/dx = V(x)
          </text>
        </svg>
      );
    }
    // Card 3: Truss / Axle
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <polygon points="100,120 190,50 280,120" fill="none" stroke="#38bdf8" strokeWidth="3" />
        <line x1="190" y1="50" x2="190" y2="120" stroke="#38bdf8" strokeWidth="2.5" />
        <circle cx="100" cy="120" r="5" fill="#f59e0b" />
        <circle cx="280" cy="120" r="5" fill="#f59e0b" />
        <circle cx="190" cy="50" r="5" fill="#f59e0b" />
        <text x="190" y="24" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          TRUSS LOAD TRANSFER
        </text>
        <text x="190" y="166" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          AXIAL TENSION &amp; COMPRESSION PIN DYNAMICS
        </text>
      </svg>
    );
  }

  // 4. ELECTRICAL ENGINEERING MINI-SVGS (STRICTLY FOR ELECTRICAL DOMAIN)
  if (isElectricalDomain) {
    if (slot === 0) {
      const loopOffset = (frame * 2.5) % 40;
      const pulseNode = 1 + Math.sin(frame * 0.12) * 0.1;
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <rect x="50" y="30" width="280" height="120" rx="18" fill="none" stroke="#00f0ff" strokeWidth="2.5" strokeDasharray="10 6" strokeDashoffset={-loopOffset} />
          <g transform={`translate(190, 90) scale(${pulseNode}) translate(-190, -90)`}>
            <circle cx="190" cy="90" r="22" fill="rgba(0, 240, 255, 0.2)" stroke="#00f0ff" strokeWidth="3" />
            <circle cx="190" cy="90" r="10" fill="#00f0ff" />
          </g>
          <polygon points="175,25 195,30 175,35" fill="#00f0ff" />
          <polygon points="205,145 185,150 205,155" fill="#00f0ff" />
          <text x="190" y="22" fill="#00f0ff" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            CURRENT LOOP I₁ →
          </text>
          <circle cx="90" cy="90" r="6" fill="#34d399" />
          <circle cx="290" cy="90" r="6" fill="#34d399" />
          <line x1="90" y1="90" x2="168" y2="90" stroke="#34d399" strokeWidth="2.5" strokeDasharray="4 4" />
          <line x1="212" y1="90" x2="290" y2="90" stroke="#34d399" strokeWidth="2.5" strokeDasharray="4 4" />
          <text x="190" y="130" fill="#cbd5e1" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            NODE CONSERVATION ΣI = 0
          </text>
        </svg>
      );
    }
    if (slot === 1) {
      const oscWave = Math.sin(frame * 0.1) * 12;
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <circle cx="85" cy="85" r="26" fill="rgba(56, 189, 248, 0.15)" stroke="#38bdf8" strokeWidth="2.5" />
          <text x="85" y="92" fill="#38bdf8" fontSize="17" fontWeight="bold" textAnchor="middle">V_th</text>
          <line x1="111" y1="85" x2="155" y2="85" stroke="#38bdf8" strokeWidth="2.5" />
          <rect x="155" y="71" width="70" height="28" rx="6" fill="#0f172a" stroke="#f59e0b" strokeWidth="2.5" />
          <text x="190" y="90" fill="#f59e0b" fontSize="13" fontWeight="bold" textAnchor="middle">Z_eq / R_th</text>
          <line x1="225" y1="85" x2="295" y2="85" stroke="#38bdf8" strokeWidth="2.5" />
          <circle cx="295" cy="85" r="6" fill="#34d399" />
          <text x="315" y="90" fill="#34d399" fontSize="15" fontWeight="bold" fontFamily="monospace">A</text>
          <circle cx="295" cy="135" r="6" fill="#34d399" />
          <text x="315" y="140" fill="#34d399" fontSize="15" fontWeight="bold" fontFamily="monospace">B</text>
          <line x1="85" y1="111" x2="85" y2="135" stroke="#38bdf8" strokeWidth="2.5" />
          <line x1="85" y1="135" x2="295" y2="135" stroke="#38bdf8" strokeWidth="2.5" />
          <path d={`M 130 ${45 + oscWave} Q 190 ${30 - oscWave} 250 ${45 + oscWave}`} fill="none" stroke="#a855f7" strokeWidth="3" />
          <text x="190" y="165" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            EQUIVALENCE: 2-TERMINAL DUALITY
          </text>
        </svg>
      );
    }
    if (slot === 2) {
      const peakGlow = 0.5 + 0.5 * Math.sin(frame * 0.14);
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="50" y1="140" x2="330" y2="140" stroke="#64748b" strokeWidth="2" />
          <line x1="50" y1="25" x2="50" y2="140" stroke="#64748b" strokeWidth="2" />
          <path d="M 60 135 Q 190 20 320 135" fill="none" stroke="#f59e0b" strokeWidth="4" strokeLinecap="round" />
          <line x1="140" y1="48" x2="240" y2="48" stroke="#34d399" strokeWidth="2.5" strokeDasharray="6 4" />
          <circle cx="190" cy="48" r={7 + 3 * peakGlow} fill="#f59e0b" stroke="#ffffff" strokeWidth="2" />
          <text x="190" y="32" fill="#f59e0b" fontSize="14" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            MAXIMUM TRANSFER: dP/dR = 0
          </text>
          <text x="190" y="165" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            MATCHED IMPEDANCE / ACTIVATION PEAK
          </text>
        </svg>
      );
    }
    // Card 3: 4-Node Mesh
    const flowDash = (frame * 2.5) % 30;
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <line x1="100" y1="55" x2="280" y2="55" stroke="#00f0ff" strokeWidth="3" strokeDasharray="6 4" strokeDashoffset={-flowDash} />
        <line x1="100" y1="125" x2="280" y2="125" stroke="#34d399" strokeWidth="3" strokeDasharray="6 4" strokeDashoffset={-flowDash} />
        <line x1="100" y1="55" x2="100" y2="125" stroke="#f59e0b" strokeWidth="3" />
        <line x1="280" y1="55" x2="280" y2="125" stroke="#f59e0b" strokeWidth="3" />
        <line x1="100" y1="55" x2="280" y2="125" stroke="#a855f7" strokeWidth="2" strokeDasharray="4 4" />
        <circle cx="100" cy="55" r="16" fill="#0f172a" stroke="#00f0ff" strokeWidth="2.5" />
        <text x="100" y="60" fill="#00f0ff" fontSize="11" fontWeight="bold" textAnchor="middle">B1</text>
        <circle cx="280" cy="55" r="16" fill="#0f172a" stroke="#00f0ff" strokeWidth="2.5" />
        <text x="280" y="60" fill="#00f0ff" fontSize="11" fontWeight="bold" textAnchor="middle">B2</text>
        <circle cx="100" cy="125" r="16" fill="#0f172a" stroke="#34d399" strokeWidth="2.5" />
        <text x="100" y="130" fill="#34d399" fontSize="11" fontWeight="bold" textAnchor="middle">B3</text>
        <circle cx="280" cy="125" r="16" fill="#0f172a" stroke="#34d399" strokeWidth="2.5" />
        <text x="280" y="130" fill="#34d399" fontSize="11" fontWeight="bold" textAnchor="middle">B4</text>
        <text x="190" y="165" fill="#00f0ff" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          4-NODE MESH TOPOLOGY &amp; OPF FLOW
        </text>
      </svg>
    );
  }

  // 5. SOFTWARE & DEVTOOL BENCHMARK MINI-SVGS
  if (isCodeDomain) {
    if (slot === 0 || normType.includes('latency')) {
      const barH = 30 + 10 * Math.sin(frame * 0.1);
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <line x1="40" y1="140" x2="340" y2="140" stroke="#334155" strokeWidth="2" />
          {/* Legacy Bar */}
          <rect x="90" y="45" width="55" height="95" rx="6" fill="rgba(239, 68, 68, 0.25)" stroke="#ef4444" strokeWidth="2" />
          <text x="117" y="35" fill="#ef4444" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">500ms</text>
          <text x="117" y="158" fill="#94a3b8" fontSize="12" fontFamily="monospace" textAnchor="middle">v1 (OLD)</text>
          {/* v2 Bar */}
          <rect x="235" y={140 - barH} width="55" height={barH} rx="6" fill="rgba(52, 211, 153, 0.35)" stroke="#34d399" strokeWidth="2" />
          <text x="262" y={128 - barH} fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">14ms</text>
          <text x="262" y="158" fill="#34d399" fontSize="12" fontWeight="bold" fontFamily="monospace" textAnchor="middle">v2 (-80%)</text>
          <text x="190" y="22" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            COLD-START LATENCY COMPARISON
          </text>
        </svg>
      );
    }
    if (slot === 1 || normType.includes('line')) {
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <rect x="50" y="38" width="125" height="95" rx="8" fill="#0f172a" stroke="#ef4444" strokeWidth="2" />
          <text x="112" y="60" fill="#ef4444" fontSize="12" fontWeight="bold" fontFamily="monospace" textAnchor="middle">BEFORE: 28 LINES</text>
          <line x1="65" y1="75" x2="160" y2="75" stroke="#ef4444" strokeWidth="2" strokeDasharray="3 3" />
          <line x1="65" y1="90" x2="145" y2="90" stroke="#ef4444" strokeWidth="2" strokeDasharray="3 3" />
          <line x1="65" y1="105" x2="155" y2="105" stroke="#ef4444" strokeWidth="2" strokeDasharray="3 3" />
          <line x1="65" y1="120" x2="130" y2="120" stroke="#ef4444" strokeWidth="2" strokeDasharray="3 3" />

          <text x="190" y="92" fill="#38bdf8" fontSize="22" fontWeight="bold" textAnchor="middle">→</text>

          <rect x="205" y="38" width="125" height="95" rx="8" fill="#0f172a" stroke="#34d399" strokeWidth="2" />
          <text x="267" y="60" fill="#34d399" fontSize="12" fontWeight="bold" fontFamily="monospace" textAnchor="middle">AFTER: 4 LINES</text>
          <line x1="220" y1="85" x2="315" y2="85" stroke="#34d399" strokeWidth="3" />
          <line x1="220" y1="105" x2="285" y2="105" stroke="#34d399" strokeWidth="3" />

          <text x="190" y="24" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            BOILERPLATE REDUCTION: 90%
          </text>
          <text x="190" y="162" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            STREAMING ASYNC ITERATOR
          </text>
        </svg>
      );
    }
    if (slot === 2 || normType.includes('cache')) {
      const pulseR = 40 + 3 * Math.sin(frame * 0.12);
      return (
        <svg width="100%" height="180" viewBox="0 0 380 180">
          <circle cx="190" cy="85" r={pulseR} fill="rgba(56, 189, 248, 0.12)" stroke="#38bdf8" strokeWidth="2.5" />
          <circle cx="190" cy="85" r="28" fill="#0f172a" stroke="#34d399" strokeWidth="3" />
          <text x="190" y="90" fill="#ffffff" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">99.9%</text>
          <circle cx="130" cy="55" r="5" fill="#38bdf8" />
          <circle cx="250" cy="55" r="5" fill="#38bdf8" />
          <circle cx="120" cy="115" r="5" fill="#34d399" />
          <circle cx="260" cy="115" r="5" fill="#34d399" />
          <line x1="135" y1="58" x2="165" y2="72" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="3 3" />
          <line x1="245" y1="58" x2="215" y2="72" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="3 3" />
          <text x="190" y="24" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            GLOBAL EDGE HIT RATE
          </text>
          <text x="190" y="162" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            40+ POPS • ZERO ORIGIN SPIKES
          </text>
        </svg>
      );
    }
    // Slot 3: Concurrency / Zero locks
    const dashX = (frame * 3) % 40;
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <line x1="60" y1="65" x2="320" y2="65" stroke="#38bdf8" strokeWidth="3" strokeDasharray="8 6" strokeDashoffset={-dashX} />
        <line x1="60" y1="105" x2="320" y2="105" stroke="#a855f7" strokeWidth="3" strokeDasharray="8 6" strokeDashoffset={-dashX} />
        <circle cx="190" cy="65" r="14" fill="#0f172a" stroke="#38bdf8" strokeWidth="2" />
        <text x="190" y="70" fill="#38bdf8" fontSize="11" fontWeight="bold" fontFamily="monospace" textAnchor="middle">CH-1</text>
        <circle cx="190" cy="105" r="14" fill="#0f172a" stroke="#a855f7" strokeWidth="2" />
        <text x="190" y="110" fill="#a855f7" fontSize="11" fontWeight="bold" fontFamily="monospace" textAnchor="middle">CH-2</text>
        <text x="190" y="24" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          LOCK-FREE PIPELINE CONCURRENCY
        </text>
        <text x="190" y="162" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          ZERO LOCK CONTENTION • mTLS
        </text>
      </svg>
    );
  }

  // 6. CLEAN DOMAIN-NEUTRAL / GENERIC MINI-SVGS (ZERO LEAKS)
  if (slot === 0) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <circle cx="190" cy="85" r="42" fill="none" stroke="#38bdf8" strokeWidth="3" strokeDasharray="8 6" />
        <circle cx="190" cy="85" r="14" fill="#38bdf8" />
        <text x="190" y="24" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          SYSTEM INVARIANT
        </text>
        <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          CONSERVED PARAMETER STATE
        </text>
      </svg>
    );
  }
  if (slot === 1) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <line x1="80" y1="85" x2="300" y2="85" stroke="#34d399" strokeWidth="3" />
        <circle cx="190" cy="85" r="12" fill="#f59e0b" />
        <text x="190" y="24" fill="#34d399" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          EQUILIBRIUM BALANCE
        </text>
        <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          STABLE POTENTIAL MINIMUM
        </text>
      </svg>
    );
  }
  if (slot === 2) {
    return (
      <svg width="100%" height="180" viewBox="0 0 380 180">
        <path d="M 70 130 Q 190 35 310 130" fill="none" stroke="#f59e0b" strokeWidth="3.5" />
        <circle cx="190" cy="35" r="6" fill="#ffffff" />
        <text x="190" y="24" fill="#f59e0b" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          OPTIMAL BOUNDARY
        </text>
        <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          CRITICAL TRANSITION THRESHOLD
        </text>
      </svg>
    );
  }
  return (
    <svg width="100%" height="180" viewBox="0 0 380 180">
      <circle cx="120" cy="85" r="16" fill="#0f172a" stroke="#a855f7" strokeWidth="2.5" />
      <circle cx="260" cy="85" r="16" fill="#0f172a" stroke="#a855f7" strokeWidth="2.5" />
      <line x1="136" y1="85" x2="244" y2="85" stroke="#a855f7" strokeWidth="2.5" strokeDasharray="6 4" />
      <text x="190" y="24" fill="#a855f7" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
        TOPOLOGICAL CONVERGENCE
      </text>
      <text x="190" y="166" fill="#cbd5e1" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
        DYNAMIC MULTI-NODE ATTRACTOR
      </text>
    </svg>
  );
};

/**
 * BentoGridScene
 * Full-Screen 3-Tier Editorial Bento (1540px Stage Height, 960px Width)
 * Automatically adapts to active domain with 4-card 2x2 grid or 5-card ML layout.
 */
export const BentoGridScene = ({
  scene,
  words = [],
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const choreography = scene?.choreography || {};

  const bentoData = scene?.bento_data || {};
  const domain = (
    bentoData.domain ||
    scene?.domain ||
    scene?.subject ||
    scene?.choreography?.domain ||
    ''
  ).toLowerCase();

  const isChemistry = domain.includes('chem') || (scene?.cards && scene.cards.some(c => ['substrate', 'nucleophile', 'solvent', 'stereochem'].includes(c.algo_type)));
  const isElectrical = domain.includes('electr') || (scene?.cards && scene.cards.some(c => ['kcl_kvl', 'thevenin_norton', 'economic_dispatch', 'opf_grid'].includes(c.algo_type)));
  const isMechanics = domain.includes('mechanic') || (scene?.cards && scene.cards.some(c => ['force_equilibrium', 'torque_balance', 'shear_bending', 'axle_transfer'].includes(c.algo_type)));
  const isQuantum = domain.includes('quantum') || (scene?.cards && scene.cards.some(c => ['schrodinger', 'tunneling', 'heisenberg', 'dirac_orbitals'].includes(c.algo_type)));
  const isMath = domain.includes('math');
  const isCode = domain.includes('code') || domain.includes('devtool') || domain.includes('system') || domain.includes('software');
  const isML = domain.includes('ml');

  let eyebrow = isCode ? 'DEVELOPER PLATFORM & BENCHMARKS' : (isML ? 'MACHINE LEARNING ARCHITECTURES' : 'SYSTEM SPECIFICATIONS & BENCHMARKS');
  let eyebrowColor = isCode ? '#38bdf8' : (isML ? '#f59e0b' : '#38bdf8');
  if (isChemistry) {
    eyebrow = 'ORGANIC CHEMISTRY • REACTION MECHANISMS';
    eyebrowColor = '#38bdf8';
  } else if (isElectrical) {
    eyebrow = 'POWER SYSTEMS & NETWORK THEOREMS';
    eyebrowColor = '#00f0ff';
  } else if (isMechanics) {
    eyebrow = 'STRUCTURAL MECHANICS & STATICS';
    eyebrowColor = '#f59e0b';
  } else if (isQuantum) {
    eyebrow = 'QUANTUM MECHANICS • WAVE DYNAMICS';
    eyebrowColor = '#c084fc';
  } else if (isMath) {
    eyebrow = 'PURE MATHEMATICS • CALCULUS & ANALYSIS';
    eyebrowColor = '#34d399';
  } else if (isCode) {
    eyebrow = 'PRODUCTION SCALE & BENCHMARKS';
    eyebrowColor = '#38bdf8';
  }

  const sectionTitle = bentoData.section_title || scene?.section_title || (
    isElectrical ? 'GRID & CIRCUIT MASTER MATRIX' :
    isMechanics ? 'EQUILIBRIUM & LOAD MATRIX' :
    isQuantum ? 'OPERATOR & STATE MATRIX' :
    isChemistry ? 'SN1 VS SN2 DECISION MATRIX' :
    isMath ? 'CALCULUS & INTEGRAL MATRIX' :
    isCode ? 'PRODUCTION SCALE & BENCHMARKS' :
    isML ? 'UNSUPERVISED ML ARCHITECTURES' :
    'SYSTEM SPECIFICATIONS & ARCHITECTURE'
  );

  const subtitle = bentoData.subtitle || scene?.subtitle || (
    isElectrical ? '4 Foundational Principles of Power Engineering' :
    isMechanics ? 'Static Equilibrium & Force Decomposition' :
    isQuantum ? 'Fundamental Postulates of Quantum Mechanics' :
    isChemistry ? 'The 4 Decisive Reaction Factors' :
    isMath ? '4 Core Cornerstones of Modern Calculus' :
    isCode ? 'Measured Performance Across 40 Global Edge Regions' :
    isML ? 'Algorithms You Need To Know' :
    'Verified Operational Invariants & Metrics'
  );

  const cards = bentoData.cards || scene?.cards || [];

  // Render 4-Card 2x2 Grid for all specialized subjects or 4-card matrices
  if (cards.length === 4 || !isML) {
    const displayCards = cards.length >= 4 ? cards.slice(0, 4) : (
      isCode ? [
        { title: 'COLD-START LATENCY', algo_type: 'latency', category: 'PERFORMANCE', description: '-80% cold-start execution latency (14ms vs 500ms)' },
        { title: 'CODE REDUCTION', algo_type: 'lines', category: 'DEVELOPER VELOCITY', description: '90% fewer lines of code (reduced from 28 lines to 4)' },
        { title: 'CACHE HIT RATE', algo_type: 'cache', category: 'GLOBAL EDGE', description: '99.9% cache hit rate across 40 global edge regions' },
        { title: 'ZERO CONFLICTS', algo_type: 'conflict', category: 'RELIABILITY', description: 'Lock-free atomic writes with native async streaming' },
      ] : isChemistry ? [
        { title: 'SUBSTRATE', algo_type: 'substrate', category: 'BULKINESS', description: 'SN2 prefers Methyl/1° • SN1 prefers bulky 3°' },
        { title: 'NUCLEOPHILE', algo_type: 'nucleophile', category: 'STRENGTH', description: 'SN2 requires strong Nu⁻ • SN1 works with weak neutral Nu' },
        { title: 'SOLVENT', algo_type: 'solvent', category: 'POLARITY', description: 'SN2 prefers polar aprotic • SN1 prefers polar protic' },
        { title: 'STEREOCHEMISTRY', algo_type: 'stereochem', category: 'OUTCOME', description: 'SN2 gives 100% inversion • SN1 gives 50/50 racemic' },
      ] : isElectrical ? [
        { title: 'KCL & KVL Laws', algo_type: 'kcl_kvl', category: 'CIRCUIT LAWS', description: 'Node conservation ΣI=0 • Mesh voltage balance ΣV=0' },
        { title: 'Thévenin & Norton', algo_type: 'thevenin_norton', category: 'EQUIVALENCE', description: 'Source reduction Vth=Voc, Rth=Voc/Isc • Maximum power transfer' },
        { title: 'Economic Dispatch', algo_type: 'economic_dispatch', category: 'OPTIMIZATION', description: 'Equal incremental cost rule λ = dC₁/dP₁ = dC₂/dP₂' },
        { title: 'Optimal Power Flow', algo_type: 'opf_grid', category: 'TRANSMISSION', description: 'Non-linear AC load flow • Thermal line limits & reactive VAR balance' },
      ] : isMechanics ? [
        { title: 'Force Equilibrium', algo_type: 'force_equilibrium', category: 'NEWTON I', description: 'Linear equilibrium ΣF_x = 0, ΣF_y = 0 guarantees zero acceleration' },
        { title: 'Torque Balance', algo_type: 'torque_balance', category: 'MOMENT OF FORCE', description: 'Rotational equilibrium Στ_A = 0 around any pin/pivot support' },
        { title: 'Shear & Bending', algo_type: 'shear_bending', category: 'BEAM STRESS', description: 'Internal shear step V(x) and parabolic bending moment M(x)' },
        { title: 'Axle Load Transfer', algo_type: 'axle_transfer', category: 'DYNAMIC SQUAT', description: 'Center of mass load shift ΔW = (h/L)·m·a acceleration' },
      ] : isQuantum ? [
        { title: 'Schrödinger Evolution', algo_type: 'schrodinger', category: 'WAVE EQUATION', description: 'Unitary wavepacket propagation iℏ∂Ψ/∂t = ĤΨ' },
        { title: 'Quantum Tunneling', algo_type: 'tunneling', category: 'BARRIER DYNAMICS', description: 'Evanescent decay T = exp(-2κL) barrier penetration' },
        { title: 'Heisenberg Uncertainty', algo_type: 'heisenberg', category: 'OBSERVABLES', description: 'Canonical commutator [x̂, p̂] = iℏ • Δx·Δp ≥ ℏ/2' },
        { title: 'Dirac Spinors & Orbitals', algo_type: 'dirac_orbitals', category: 'RELATIVISTIC QM', description: '4-component bi-spinor • Hydrogen spatial probability density' },
      ] : isMath ? [
        { title: 'Secant → Tangent', algo_type: 'derivative_limit', category: 'DIFFERENTIAL', description: 'Secant line slope converges to instantaneous rate df/dx' },
        { title: 'Riemann Integral', algo_type: 'riemann_sum', category: 'INTEGRAL', description: 'Accumulated rectangular partitions converge to continuous area ∫f(x)dx' },
        { title: 'Critical Extrema', algo_type: 'critical_points', category: 'OPTIMIZATION', description: 'Stationary points f\'(x)=0 reveal global maxima & minima bounds' },
        { title: 'Evaluation Theorem', algo_type: 'fundamental_thm', category: 'DUALITY', description: 'Antiderivative net evaluation: ∫_a^b f\'(x)dx = f(b) - f(a)' },
      ] : [
        { title: 'Principle 1', algo_type: 'p1', category: 'CORE', description: 'Primary invariant relationship' },
        { title: 'Principle 2', algo_type: 'p2', category: 'EQUILIBRIUM', description: 'Conservation and balance equations' },
        { title: 'Principle 3', algo_type: 'p3', category: 'OPTIMIZATION', description: 'Extrema and minimum potential' },
        { title: 'Principle 4', algo_type: 'p4', category: 'CONVERGENCE', description: 'Deterministic terminal outcome' },
      ]
    );

    return (
      <div
        style={{
          width: '960px',
          height: '1360px',
          maxHeight: '1380px',
          overflow: 'hidden',
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
        {/* TOP TIER: EDITORIAL HEADER */}
        <div
          style={{
            height: '160px',
            backgroundColor: '#111724',
            borderRadius: '20px',
            border: `1.5px solid ${eyebrowColor}55`,
            boxShadow: `0 24px 48px -12px rgba(0, 0, 0, 0.85), 0 0 28px ${eyebrowColor}22`,
            padding: '16px 28px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span
              style={{
                fontSize: '20px',
                fontWeight: 900,
                letterSpacing: '2.5px',
                color: eyebrowColor,
                textTransform: 'uppercase',
                fontFamily: 'monospace',
              }}
            >
              {eyebrow}
            </span>
            {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: '40px',
              fontWeight: 900,
              color: '#f8fafc',
              lineHeight: 1.15,
              letterSpacing: '-0.5px',
            }}
          >
            {sectionTitle}
          </h1>

          <div style={{ fontSize: '22px', color: '#94a3b8', fontWeight: 600 }}>
            {subtitle}
          </div>
        </div>

        {/* 4-CARD DECISION MATRIX GRID (2x2) */}
        <div
          style={{
            height: '1180px',
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '16px',
            boxSizing: 'border-box',
          }}
        >
          {displayCards.map((card, idx) => (
            <div
              key={idx}
              style={{
                height: '570px',
                backgroundColor: '#141824',
                borderRadius: '20px',
                border: `1.5px solid ${eyebrowColor}44`,
                padding: '18px 22px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxSizing: 'border-box',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '28px', fontWeight: 900, color: '#f8fafc' }}>{card.title}</span>
                  <span
                    style={{
                      fontSize: '15px',
                      color: eyebrowColor,
                      fontWeight: 800,
                      fontFamily: 'monospace',
                      backgroundColor: `${eyebrowColor}1a`,
                      padding: '4px 10px',
                      borderRadius: '8px',
                    }}
                  >
                    {card.category}
                  </span>
                </div>
                <div style={{ fontSize: '20px', color: '#cbd5e1', lineHeight: 1.3 }}>
                  {card.description}
                </div>
              </div>
              <MiniCanvas algoType={card.algo_type} cardIndex={idx} isHighlighted={true} frame={frame} domain={domain} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Strictly guard: non-ML domains must never render ML clustering layout
  if (!isML) {
    return null;
  }

  return (
    <div
      style={{
        width: '960px',
        height: '1360px',
        maxHeight: '1380px',
        overflow: 'hidden',
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
      {/* 1. TOP TIER: EDITORIAL HEADER (160px tall) */}
      <div
        style={{
          height: '160px',
          backgroundColor: '#111724',
          borderRadius: '20px',
          border: '1.5px solid rgba(245, 158, 11, 0.3)',
          boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.85), 0 0 28px rgba(245, 158, 11, 0.15)',
          padding: '16px 28px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span
            style={{
              fontSize: '24px',
              fontWeight: 900,
              letterSpacing: '3px',
              color: '#f59e0b',
              textTransform: 'uppercase',
              fontFamily: 'monospace',
            }}
          >
            MACHINE LEARNING ARCHITECTURES
          </span>
          {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
        </div>

        <h1
          style={{
            margin: 0,
            fontSize: '52px',
            fontWeight: 900,
            color: '#f8fafc',
            lineHeight: 1.15,
            letterSpacing: '-0.5px',
          }}
        >
          {sectionTitle}
        </h1>

        <div style={{ fontSize: '28px', color: '#94a3b8', fontWeight: 600 }}>
          You Need{' '}
          <span style={{ textDecoration: 'underline', textDecorationColor: '#f59e0b', textDecorationThickness: '4px', color: '#f8fafc' }}>
            To Know
          </span>
        </div>
      </div>

      {/* 2. MIDDLE TIER: CLUSTERING SECTION (540px tall) */}
      <div
        style={{
          height: '540px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxSizing: 'border-box',
        }}
      >
        {/* Section Header */}
        <div
          style={{
            fontSize: '22px',
            fontWeight: 900,
            color: '#f59e0b',
            letterSpacing: '3px',
            textTransform: 'uppercase',
            fontFamily: 'monospace',
            paddingLeft: '4px',
          }}
        >
          CLUSTERING ALGORITHMS
        </div>

        {/* 2 Tall Cards on Top (each 230px tall) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
          {/* Card 1: K-Means */}
          <div
            style={{
              height: '230px',
              backgroundColor: '#141824',
              borderRadius: '20px',
              border: '1.5px solid rgba(245, 158, 11, 0.35)',
              padding: '16px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
            }}
          >
            <div>
              <div style={{ fontSize: '28px', fontWeight: 900, color: '#f8fafc' }}>K-Means</div>
              <div style={{ fontSize: '19px', color: '#94a3b8' }}>Centroid-based spatial partitioning</div>
            </div>
            <MiniCanvas algoType="kmeans" isHighlighted={true} frame={frame} domain="ml" />
          </div>

          {/* Card 2: Hierarchical */}
          <div
            style={{
              height: '230px',
              backgroundColor: '#141824',
              borderRadius: '20px',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              padding: '16px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
            }}
          >
            <div>
              <div style={{ fontSize: '28px', fontWeight: 900, color: '#f8fafc' }}>Hierarchical</div>
              <div style={{ fontSize: '19px', color: '#94a3b8' }}>Tree-structured dendrogram linkage</div>
            </div>
            <MiniCanvas algoType="hierarchical" isHighlighted={false} frame={frame} domain="ml" />
          </div>
        </div>

        {/* 1 Wide Featured Card Below: DBSCAN (240px tall) */}
        <div
          style={{
            height: '240px',
            backgroundColor: '#141824',
            borderRadius: '20px',
            border: '1.5px solid #10b981',
            boxShadow: '0 0 24px rgba(16, 185, 129, 0.25)',
            padding: '16px 24px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '28px', fontWeight: 900, color: '#f8fafc' }}>DBSCAN</span>
              <span style={{ marginLeft: '16px', fontSize: '20px', color: '#10b981', fontWeight: 800, fontFamily: 'monospace' }}>
                DENSITY CORE &amp; NOISE HANDLING
              </span>
            </div>
            <span style={{ fontSize: '19px', color: '#94a3b8' }}>Robust to arbitrary cluster shapes</span>
          </div>
          <MiniCanvas algoType="dbscan" isHighlighted={true} frame={frame} domain="ml" />
        </div>
      </div>

      {/* 3. BOTTOM TIER: DIMENSIONALITY REDUCTION (580px tall) */}
      <div
        style={{
          height: '580px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxSizing: 'border-box',
        }}
      >
        {/* Section Header */}
        <div
          style={{
            fontSize: '22px',
            fontWeight: 900,
            color: '#f59e0b',
            letterSpacing: '3px',
            textTransform: 'uppercase',
            fontFamily: 'monospace',
            paddingLeft: '4px',
          }}
        >
          DIMENSIONALITY REDUCTION &amp; MANIFOLD
        </div>

        {/* 2 Tall Side-by-Side Cards (each 520px tall) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {/* Card 1: PCA */}
          <div
            style={{
              height: '520px',
              backgroundColor: '#141824',
              borderRadius: '20px',
              border: '1.5px solid rgba(245, 158, 11, 0.35)',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
            }}
          >
            <div>
              <div style={{ fontSize: '30px', fontWeight: 900, color: '#f8fafc', marginBottom: '6px' }}>PCA</div>
              <div style={{ fontSize: '21px', color: '#cbd5e1', lineHeight: 1.3 }}>
                Linear projection onto orthogonal principal component vectors
              </div>
            </div>
            <MiniCanvas algoType="pca" isHighlighted={true} frame={frame} domain="ml" />
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '12px', fontSize: '19px', color: '#94a3b8' }}>
              • Maximizes global variance<br />• Fast O(n · d²) covariance SVD
            </div>
          </div>

          {/* Card 2: t-SNE / UMAP */}
          <div
            style={{
              height: '520px',
              backgroundColor: '#141824',
              borderRadius: '20px',
              border: '1.5px solid rgba(56, 189, 248, 0.35)',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
            }}
          >
            <div>
              <div style={{ fontSize: '30px', fontWeight: 900, color: '#f8fafc', marginBottom: '6px' }}>t-SNE / UMAP</div>
              <div style={{ fontSize: '21px', color: '#cbd5e1', lineHeight: 1.3 }}>
                Non-linear manifold embedding for cluster separation
              </div>
            </div>
            <MiniCanvas algoType="tsne" isHighlighted={true} frame={frame} domain="ml" />
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '12px', fontSize: '19px', color: '#94a3b8' }}>
              • Preserves local topological rings<br />• Student-t probability divergence
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BentoGridScene;
