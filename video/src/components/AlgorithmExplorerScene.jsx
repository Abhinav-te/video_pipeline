import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { GearIcon, TargetIcon, LayersIcon, BrainIcon, SparklesIcon, LightningIcon } from './SvgIcons';

/**
 * Phase 6 Dynamic Parameter & Telemetry Configurations
 * Distinct parameter dictionaries, legends, and complexity metrics for each algorithm mode.
 */
export const ALGORITHM_CONFIGS = {
  DBSCAN: {
    parameters: [
      { label: 'ε = 0.40', desc: '(Radius)' },
      { label: 'minPts = 4', desc: '(Core Cutoff)' },
      { label: 'Metric = Euclidean', desc: '(L2)' },
    ],
    legendTitle: 'POINT TYPES',
    legend: [
      { name: 'Core Point', desc: '≥ minPts within ε', color: '#10b981' },
      { name: 'Border Point', desc: 'in ε of core point', color: '#38bdf8' },
      { name: 'Noise Outlier (X)', desc: 'isolated outlier', color: '#ef4444' },
    ],
    rule: 'Discovers arbitrary manifold clusters with complete immunity to noise outliers.',
    ruleColor: '#34d399',
    scrubberLabel: 'Epsilon Radius (ε)',
    complexity: 'Complexity: O(n log n) • Outliers: 4',
  },
  'K-MEANS': {
    parameters: [
      { label: 'K = 2', desc: '(Cluster Centroids)' },
      { label: 'Metric = Euclidean', desc: '(L2)' },
      { label: 'Update = Mean Shift Iteration', desc: '(Inertia Convergence)' },
    ],
    legendTitle: 'CLUSTER TAXONOMY',
    legend: [
      { name: 'Centroid (Δ)', desc: 'Cluster center of mass', color: '#f59e0b' },
      { name: 'Cluster A', desc: 'Voronoi partition 1', color: '#f59e0b' },
      { name: 'Cluster B', desc: 'Voronoi partition 2', color: '#818cf8' },
      { name: 'Linear Voronoi Boundary', desc: 'Bisecting hyper-plane', color: 'rgba(255, 255, 255, 0.4)' },
    ],
    rule: 'Partitions space into linear Voronoi cells. Assumes convex spherical geometries.',
    ruleColor: '#fbbf24',
    scrubberLabel: 'Centroid Iteration',
    complexity: 'Complexity: O(k·n·i) • Inertia: 142.6',
  },
  PCA: {
    parameters: [
      { label: 'Components = 2', desc: '(PC1, PC2)' },
      { label: 'Variance Retained = 94.2%', desc: '(Optimal)' },
      { label: 'Solver = SVD', desc: '(Singular Value Decomposition)' },
    ],
    legendTitle: 'AXES & PROJECTIONS',
    legend: [
      { name: 'PC1 Primary Axis', desc: 'Maximal variance direction', color: '#f59e0b' },
      { name: 'PC2 Orthogonal Axis', desc: 'Orthogonal component', color: '#38bdf8' },
      { name: 'Projected Sample', desc: 'Projected vector coordinate', color: '#f8fafc' },
    ],
    rule: 'Orthogonal linear transformation maximizing variance along orthogonal eigenvectors.',
    ruleColor: '#38bdf8',
    scrubberLabel: 'Retained Variance',
    complexity: 'Complexity: O(d²·n + d³) • PCs: 2',
  },
};

export const getAlgorithmParameters = (mode = 'DBSCAN') => {
  const normalized = (mode || '').toUpperCase().trim();
  if (normalized.includes('K-MEAN') || normalized.includes('KMEAN')) {
    return ALGORITHM_CONFIGS['K-MEANS'];
  }
  if (normalized.includes('PCA')) {
    return ALGORITHM_CONFIGS['PCA'];
  }
  return ALGORITHM_CONFIGS['DBSCAN'];
};

/**
 * AlgorithmExplorerScene (Phase 5 - 1540px Vertical Stage Layout & Phase 6 Telemetry)
 * Full-screen 3-Tier Deep-Dive layout utilizing 85% of the 1080x1920 canvas:
 *   - Top Tier (220px): 5 thumbnail navigation cards with live mini-SVG icons + 48px gold title + subtitle badge.
 *     Dynamic Tab Switching: Automatically switches between DBSCAN, K-MEANS, and PCA based on narration keywords!
 *   - Center Tier (760px): Massive 920x740 interactive simulation canvas with 48 data points,
 *     sweeping ε=95 scanner circle, dynamic neighbor lines, and live Complexity & Telemetry HUD.
 *   - Bottom Tier (480px): Dynamic PARAMETERS card with Live Hyperparameter Scrubber Bar and POINT TYPES card.
 */
export const AlgorithmExplorerScene = ({
  scene,
  words = [],
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const choreography = scene?.choreography || {};
  const explorerChoreo = choreography.explorer || {};

  const scanStart = explorerChoreo.scan_start_frame || (sceneStartFrame + 4);
  const scanEnd = explorerChoreo.scan_end_frame || (sceneStartFrame + 50);

  // Dynamic Tab Switching based on narration context / keywords
  const spokenLower = (scene?.spoken_text || '').toLowerCase();
  const currentWord = (words || []).find(
    (w) => currentTime >= w.start && currentTime <= w.end
  )?.word?.toLowerCase() || '';

  // Detect active algorithm mode
  let activeMode = 'DBSCAN';
  if (
    currentWord.includes('k-mean') ||
    currentWord.includes('spherical') ||
    (spokenLower.includes('k-means') && !spokenLower.includes('dbscan'))
  ) {
    activeMode = 'K-MEANS';
  } else if (
    currentWord.includes('pca') ||
    currentWord.includes('variance') ||
    currentWord.includes('projection') ||
    (spokenLower.includes('pca') && !spokenLower.includes('dbscan'))
  ) {
    activeMode = 'PCA';
  } else if (spokenLower.includes('k-means') && spokenLower.includes('dbscan')) {
    // If both mentioned, switch dynamically if the word is in the first half
    const dbscanWord = (words || []).find((w) => w.word.toLowerCase().includes('dbscan'));
    if (dbscanWord && currentTime < dbscanWord.start) {
      activeMode = 'K-MEANS';
    } else {
      activeMode = 'DBSCAN';
    }
  }

  const conceptStrip = scene?.concept_strip || [
    'OVERVIEW', 'DBSCAN', 'K-MEANS', 'PCA', 'HIERARCHICAL'
  ];

  const conceptTabs = [
    { id: 'OVERVIEW', label: 'OVERVIEW', icon: 'layers' },
    { id: 'DBSCAN', label: 'DBSCAN', icon: 'target' },
    { id: 'K-MEANS', label: 'K-MEANS', icon: 'brain' },
    { id: 'PCA', label: 'PCA', icon: 'sparkles' },
    { id: 'HIERARCHICAL', label: 'HIERARCHICAL', icon: 'layers' },
  ];

  // Active tab index
  const activeTabIndex = conceptTabs.findIndex((t) => t.id === activeMode) >= 0
    ? conceptTabs.findIndex((t) => t.id === activeMode)
    : 1;

  // Center Simulation Dimensions (920px x 740px canvas)
  const width = 920;
  const canvasHeight = 740;

  // 48 synthetic 2D data points for rich non-linear crescent clusters
  const cluster1 = [
    { x: 180, y: 380 }, { x: 210, y: 340 }, { x: 250, y: 310 }, { x: 300, y: 290 },
    { x: 350, y: 280 }, { x: 400, y: 290 }, { x: 450, y: 310 }, { x: 490, y: 340 },
    { x: 520, y: 380 }, { x: 220, y: 410 }, { x: 270, y: 360 }, { x: 320, y: 340 },
    { x: 370, y: 340 }, { x: 420, y: 360 }, { x: 470, y: 410 }, { x: 260, y: 440 },
    { x: 310, y: 420 }, { x: 360, y: 410 }, { x: 410, y: 420 }, { x: 450, y: 450 },
    { x: 350, y: 470 }, { x: 380, y: 460 },
  ];

  const cluster2 = [
    { x: 440, y: 490 }, { x: 480, y: 530 }, { x: 530, y: 560 }, { x: 580, y: 570 },
    { x: 630, y: 570 }, { x: 680, y: 550 }, { x: 730, y: 520 }, { x: 770, y: 480 },
    { x: 500, y: 480 }, { x: 550, y: 510 }, { x: 600, y: 520 }, { x: 650, y: 510 },
    { x: 700, y: 480 }, { x: 740, y: 440 }, { x: 580, y: 460 }, { x: 630, y: 460 },
    { x: 680, y: 440 }, { x: 620, y: 410 },
  ];

  const noisePoints = [
    { x: 120, y: 220 }, { x: 160, y: 620 }, { x: 800, y: 240 }, { x: 840, y: 600 },
    { x: 240, y: 160 }, { x: 720, y: 180 }, { x: 140, y: 490 }, { x: 820, y: 380 },
  ];

  const corePoints = [...cluster1, ...cluster2];
  const allPoints = [...corePoints, ...noisePoints];

  // Scan progress across core path
  const scanProgress = interpolate(
    frame,
    [scanStart, scanEnd],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const scanPathPoints = [
    cluster1[0], cluster1[2], cluster1[4], cluster1[6], cluster1[8],
    cluster1[13], cluster1[17], cluster2[0], cluster2[4], cluster2[7],
  ];

  const scanIdx = Math.min(
    scanPathPoints.length - 1,
    Math.floor(scanProgress * (scanPathPoints.length - 1))
  );
  const nextScanIdx = Math.min(scanPathPoints.length - 1, scanIdx + 1);
  const localT = (scanProgress * (scanPathPoints.length - 1)) - scanIdx;

  const currentCenter = {
    x: scanPathPoints[scanIdx].x + (scanPathPoints[nextScanIdx].x - scanPathPoints[scanIdx].x) * localT,
    y: scanPathPoints[scanIdx].y + (scanPathPoints[nextScanIdx].y - scanPathPoints[scanIdx].y) * localT,
  };

  const epsilonRadius = 95;

  // Compute active neighbors inside the scanning circle
  const activeNeighbors = allPoints.filter((pt) => {
    const dx = pt.x - currentCenter.x;
    const dy = pt.y - currentCenter.y;
  });

  const currentConfig = getAlgorithmParameters(activeMode);

  // Dynamic scrubber calculations based on mode and frame
  let scrubberValue = '';
  let scrubberPercent = 50;
  let isOptimal = false;

  if (activeMode === 'K-MEANS') {
    isOptimal = frame >= scanStart + 22;
    scrubberPercent = Math.min(100, Math.max(25, Math.round(25 + 75 * scanProgress)));
    scrubberValue = isOptimal ? 'Iter 4 (Converged)' : (frame >= scanStart + 10 ? 'Iter 3' : 'Iter 2');
  } else if (activeMode === 'PCA') {
    isOptimal = frame >= scanStart + 18;
    scrubberPercent = Math.min(94, Math.max(45, Math.round(45 + 49 * scanProgress)));
    scrubberValue = isOptimal ? '94.2% (Optimal)' : `${scrubberPercent}% (Projecting)`;
  } else {
    // DBSCAN
    isOptimal = frame >= scanStart + 20;
    scrubberPercent = Math.min(100, Math.max(20, Math.round(20 + 75 * scanProgress)));
    scrubberValue = isOptimal ? '0.40 (Optimal)' : (scanProgress < 0.3 ? '0.15 (Under-clustered)' : '0.32 (Expanding)');
  }

  return (
    <div
      style={{
        backgroundColor: '#0a0e17',
        borderRadius: '28px',
        border: '1.5px solid rgba(245, 158, 11, 0.35)',
        boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 40px rgba(245, 158, 11, 0.16)',
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
      {/* TIER 1: TOP CONCEPT PROGRESS STRIP & HERO HEADER (220px) */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          height: '220px',
          boxSizing: 'border-box',
        }}
      >
        {/* Row of 5 Thumbnail Navigation Cards */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            width: '100%',
          }}
        >
          {conceptTabs.map((tab, idx) => {
            const isActive = idx === activeTabIndex;
            return (
              <div
                key={tab.id}
                style={{
                  flex: 1,
                  height: '76px',
                  borderRadius: '14px',
                  backgroundColor: isActive ? 'rgba(245, 158, 11, 0.18)' : '#121722',
                  border: isActive ? '2px solid #f59e0b' : '1px solid rgba(255, 255, 255, 0.08)',
                  boxShadow: isActive ? '0 0 20px rgba(245, 158, 11, 0.4)' : 'none',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  color: isActive ? '#f59e0b' : '#64748b',
                  fontSize: '15px',
                  fontWeight: 800,
                  fontFamily: 'monospace',
                  letterSpacing: '0.8px',
                  boxSizing: 'border-box',
                }}
              >
                {tab.icon === 'target' && <TargetIcon size={20} color={isActive ? '#f59e0b' : '#64748b'} />}
                {tab.icon === 'brain' && <BrainIcon size={20} color={isActive ? '#f59e0b' : '#64748b'} />}
                {tab.icon === 'sparkles' && <SparklesIcon size={20} color={isActive ? '#f59e0b' : '#64748b'} />}
                {tab.icon === 'layers' && <LayersIcon size={20} color={isActive ? '#f59e0b' : '#64748b'} />}
                <span>{tab.label}</span>
              </div>
            );
          })}
        </div>

        {/* Hero Title & Subtitle Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: '4px',
          }}
        >
          <div>
            <div
              style={{
                fontSize: '22px',
                fontWeight: 800,
                color: '#f59e0b',
                fontFamily: 'monospace',
                letterSpacing: '3px',
                textTransform: 'uppercase',
                marginBottom: '4px',
              }}
            >
              ALGORITHM ARCHITECTURE • DEEP DIVE
            </div>
            <div
              style={{
                fontSize: '48px',
                fontWeight: 900,
                color: '#ffffff',
                fontFamily: 'sans-serif',
                letterSpacing: '-0.5px',
                lineHeight: '1.1',
              }}
            >
              {activeMode === 'K-MEANS'
                ? 'K-Means Clustering'
                : (activeMode === 'PCA' ? 'Principal Component Analysis' : 'DBSCAN Clustering')}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(245, 158, 11, 0.16)',
                border: '1.5px solid #f59e0b',
                color: '#f59e0b',
                borderRadius: '8px',
                padding: '6px 16px',
                fontSize: '18px',
                fontWeight: 900,
                letterSpacing: '1px',
                fontFamily: 'monospace',
              }}
            >
              {activeMode === 'K-MEANS' ? 'CENTROID PARTITIONING' : (activeMode === 'PCA' ? 'VARIANCE MAXIMIZATION' : 'DENSITY SCANNER')}
            </span>
            {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
          </div>
        </div>
      </div>

      {/* TIER 2: CENTER SIMULATION CANVAS (760px) */}
      <div
        style={{
          backgroundColor: '#0d131f',
          borderRadius: '22px',
          border: '1.5px solid rgba(255, 255, 255, 0.1)',
          boxShadow: 'inset 0 0 36px rgba(0, 0, 0, 0.8), 0 0 24px rgba(245, 158, 11, 0.12)',
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: `${canvasHeight}px`,
          width: '100%',
          boxSizing: 'border-box',
        }}
      >
        <svg
          width={width}
          height={canvasHeight}
          viewBox={`0 0 ${width} ${canvasHeight}`}
          style={{ overflow: 'visible', width: '100%', height: '100%' }}
        >
          {/* Subtle 2D Grid Lines */}
          {[120, 240, 360, 480, 600, 720, 840].map((gx) => (
            <line
              key={`gx-${gx}`}
              x1={gx}
              y1="40"
              x2={gx}
              y2={canvasHeight - 40}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth="1.5"
            />
          ))}
          {[120, 240, 360, 480, 600].map((gy) => (
            <line
              key={`gy-${gy}`}
              x1="60"
              y1={gy}
              x2={width - 60}
              y2={gy}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth="1.5"
            />
          ))}

          {/* SIMULATION MODE: DBSCAN DENSITY SCANNER */}
          {activeMode === 'DBSCAN' && (
            <>
              {/* Dynamic Neighbor Connection Lines Lighting Up */}
              {activeNeighbors.map((nbr, idx) => (
                <line
                  key={`nbr-line-${idx}`}
                  x1={currentCenter.x}
                  y1={currentCenter.y}
                  x2={nbr.x}
                  y2={nbr.y}
                  stroke="#f59e0b"
                  strokeWidth="2.2"
                  strokeDasharray="4 3"
                  opacity="0.85"
                />
              ))}

              {/* Sweeping Dashed ε-radius Scanner Circle */}
              <circle
                cx={currentCenter.x}
                cy={currentCenter.y}
                r={epsilonRadius}
                fill="rgba(245, 158, 11, 0.14)"
                stroke="#f59e0b"
                strokeWidth="2.5"
                strokeDasharray="8 6"
              />
              {/* Epsilon Radius Line & Label */}
              <line
                x1={currentCenter.x}
                y1={currentCenter.y}
                x2={currentCenter.x + epsilonRadius}
                y2={currentCenter.y}
                stroke="#f59e0b"
                strokeWidth="2"
              />
              <text
                x={currentCenter.x + epsilonRadius / 2 - 8}
                y={currentCenter.y - 10}
                fill="#f59e0b"
                fontSize="22"
                fontWeight="900"
                fontFamily="monospace"
              >
                ε = 95px
              </text>

              {/* 1. Cluster 1 Core Points (Emerald Green) */}
              {cluster1.map((pt, idx) => (
                <circle
                  key={`c1-${idx}`}
                  cx={pt.x}
                  cy={pt.y}
                  r="11"
                  fill="#10b981"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              ))}

              {/* 2. Cluster 2 Core Points (Cyan Blue) */}
              {cluster2.map((pt, idx) => (
                <circle
                  key={`c2-${idx}`}
                  cx={pt.x}
                  cy={pt.y}
                  r="11"
                  fill="#38bdf8"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              ))}

              {/* 3. Noise Points (Slate Outliers with Crisp X) */}
              {noisePoints.map((pt, idx) => (
                <g key={`noise-${idx}`}>
                  <circle cx={pt.x} cy={pt.y} r="10" fill="#475569" opacity="0.75" />
                  <line x1={pt.x - 7} y1={pt.y - 7} x2={pt.x + 7} y2={pt.y + 7} stroke="#ef4444" strokeWidth="2.5" />
                  <line x1={pt.x + 7} y1={pt.y - 7} x2={pt.x - 7} y2={pt.y + 7} stroke="#ef4444" strokeWidth="2.5" />
                </g>
              ))}

              {/* Floating HUD Telemetry Pill (26px Font) */}
              <g transform="translate(60, 50)">
                <rect
                  x="0"
                  y="0"
                  width="420"
                  height="64"
                  rx="14"
                  fill="#141820"
                  stroke="rgba(245, 158, 11, 0.4)"
                  strokeWidth="1.5"
                />
                <text x="24" y="42" fill="#34d399" fontSize="26" fontWeight="bold" fontFamily="monospace">
                  Neighbors: {activeNeighbors.length} ≥ minPts (Core)
                </text>
              </g>
            </>
          )}

          {/* SIMULATION MODE: K-MEANS CENTROID PARTITIONING */}
          {activeMode === 'K-MEANS' && (
            <>
              {/* Voronoi Boundary Guide */}
              <line x1="100" y1="520" x2="820" y2="280" stroke="rgba(255,255,255,0.15)" strokeWidth="2" strokeDasharray="8 6" />

              {/* Moving Centroids */}
              {(() => {
                const c1 = { x: 340 + Math.sin(frame * 0.05) * 20, y: 360 + Math.cos(frame * 0.05) * 15 };
                const c2 = { x: 620 + Math.cos(frame * 0.05) * 20, y: 500 + Math.sin(frame * 0.05) * 15 };
                return (
                  <>
                    {/* Centroid 1 */}
                    <polygon
                      points={`${c1.x},${c1.y - 20} ${c1.x + 18},${c1.y + 14} ${c1.x - 18},${c1.y + 14}`}
                      fill="#f59e0b"
                      stroke="#ffffff"
                      strokeWidth="3"
                    />
                    {/* Centroid 2 */}
                    <polygon
                      points={`${c2.x},${c2.y - 20} ${c2.x + 18},${c2.y + 14} ${c2.x - 18},${c2.y + 14}`}
                      fill="#818cf8"
                      stroke="#ffffff"
                      strokeWidth="3"
                    />
                  </>
                );
              })()}

              {/* Points colored by nearest centroid */}
              {cluster1.map((pt, idx) => (
                <circle key={`km1-${idx}`} cx={pt.x} cy={pt.y} r="10" fill="#f59e0b" stroke="#ffffff" strokeWidth="1.5" />
              ))}
              {cluster2.map((pt, idx) => (
                <circle key={`km2-${idx}`} cx={pt.x} cy={pt.y} r="10" fill="#818cf8" stroke="#ffffff" strokeWidth="1.5" />
              ))}
              {noisePoints.map((pt, idx) => (
                <circle key={`kmn-${idx}`} cx={pt.x} cy={pt.y} r="10" fill="#f59e0b" stroke="#ffffff" strokeWidth="1.5" />
              ))}

              {/* Floating HUD Telemetry Pill (26px Font) */}
              <g transform="translate(60, 50)">
                <rect x="0" y="0" width="440" height="64" rx="14" fill="#141820" stroke="rgba(245, 158, 11, 0.4)" strokeWidth="1.5" />
                <text x="24" y="42" fill="#f59e0b" fontSize="26" fontWeight="bold" fontFamily="monospace">
                  Centroids: k=2 (Iteration 4 Converged)
                </text>
              </g>
            </>
          )}

          {/* SIMULATION MODE: PCA PROJECTION */}
          {activeMode === 'PCA' && (
            <>
              {/* Rotating Principal Component 1 Axis */}
              <line x1="160" y1="260" x2="780" y2="580" stroke="#f59e0b" strokeWidth="4" strokeLinecap="round" />
              {/* PC2 Axis */}
              <line x1="380" y1="620" x2="560" y2="220" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray="6 4" />

              {/* Data points & projections */}
              {allPoints.slice(0, 36).map((pt, idx) => {
                // Projection along PC1 line (y = 0.516 x + 177)
                const projX = (pt.x + 0.516 * pt.y - 91) / 1.266;
                const projY = 0.516 * projX + 177;
                return (
                  <g key={`pca-${idx}`}>
                    <line x1={pt.x} y1={pt.y} x2={projX} y2={projY} stroke="rgba(255,255,255,0.2)" strokeWidth="1" strokeDasharray="2 2" />
                    <circle cx={pt.x} cy={pt.y} r="8" fill="#e2e8f0" opacity="0.6" />
                    <circle cx={projX} cy={projY} r="7" fill="#f59e0b" />
                  </g>
                );
              })}

              {/* Floating HUD Telemetry Pill (26px Font) */}
              <g transform="translate(60, 50)">
                <rect x="0" y="0" width="420" height="64" rx="14" fill="#141820" stroke="rgba(245, 158, 11, 0.4)" strokeWidth="1.5" />
                <text x="24" y="42" fill="#f59e0b" fontSize="26" fontWeight="bold" fontFamily="monospace">
                  PC1 Explained Variance: 86.4%
                </text>
              </g>
            </>
          )}

          {/* Top-Right Complexity & Telemetry HUD Pill (Phase 6 Signature) */}
          <g transform="translate(480, 50)">
            <rect
              x="0"
              y="0"
              width="410"
              height="64"
              rx="14"
              fill="#141820"
              stroke="rgba(255, 255, 255, 0.16)"
              strokeWidth="1.5"
            />
            <text
              x="20"
              y="25"
              fill="#38bdf8"
              fontSize="12"
              fontWeight="800"
              fontFamily="monospace"
              letterSpacing="1"
            >
              {'ALGORITHM COMPLEXITY & TELEMETRY'}
            </text>
            <text
              x="20"
              y="48"
              fill="#f1f5f9"
              fontSize="16"
              fontWeight="bold"
              fontFamily="monospace"
            >
              {currentConfig.complexity}
            </text>
          </g>
        </svg>
      </div>

      {/* TIER 3: BOTTOM SPLIT INFO CARDS (480px) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '24px',
          height: '480px',
          boxSizing: 'border-box',
        }}
      >
        {/* Left Card: DYNAMIC PARAMETERS & LIVE SCRUBBER (445px x 460px) */}
        <div
          style={{
            backgroundColor: '#111726',
            borderRadius: '22px',
            border: '1.5px solid rgba(245, 158, 11, 0.28)',
            padding: '28px 30px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <GearIcon size={28} color="#f59e0b" />
              <span
                style={{
                  fontSize: '26px',
                  fontWeight: 900,
                  color: '#f59e0b',
                  fontFamily: 'monospace',
                  letterSpacing: '1.5px',
                }}
              >
                PARAMETERS
              </span>
            </div>
            <span
              style={{
                fontSize: '18px',
                fontWeight: 'bold',
                color: '#38bdf8',
                fontFamily: 'monospace',
                backgroundColor: 'rgba(56, 189, 248, 0.12)',
                padding: '4px 10px',
                borderRadius: '8px',
                border: '1px solid rgba(56, 189, 248, 0.3)',
              }}
            >
              {activeMode}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {currentConfig.parameters.map((param, pIdx) => (
              <div key={pIdx} style={{ fontSize: '24px', color: '#f8fafc', fontWeight: 'bold', fontFamily: 'monospace' }}>
                {param.label} {param.desc ? <span style={{ color: '#94a3b8', fontWeight: 'normal', fontSize: '22px' }}>{param.desc}</span> : null}
              </div>
            ))}
          </div>

          {/* Signature Feature: Live Hyperparameter Scrubber Bar */}
          <div
            style={{
              padding: '16px 20px',
              backgroundColor: '#0a0e17',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '20px', fontFamily: 'monospace' }}>
              <span style={{ color: '#cbd5e1', fontWeight: 600 }}>{currentConfig.scrubberLabel}</span>
              <span style={{ color: isOptimal ? '#10b981' : '#f59e0b', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '6px' }}>
                {isOptimal && <LightningIcon size={18} color="#10b981" />}
                {scrubberValue}
              </span>
            </div>

            {/* Animated Slider Track */}
            <div
              style={{
                width: '100%',
                height: '14px',
                backgroundColor: '#1e293b',
                borderRadius: '7px',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  left: '60%',
                  width: '35%',
                  height: '100%',
                  backgroundColor: 'rgba(16, 185, 129, 0.25)',
                  borderLeft: '1.5px dashed #10b981',
                  borderRight: '1.5px dashed #10b981',
                }}
              />
              <div
                style={{
                  width: `${scrubberPercent}%`,
                  height: '100%',
                  background: isOptimal
                    ? 'linear-gradient(90deg, #f59e0b 0%, #10b981 100%)'
                    : 'linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%)',
                  borderRadius: '7px',
                  boxShadow: '0 0 12px rgba(245, 158, 11, 0.5)',
                  transition: 'width 0.1s ease',
                }}
              />
            </div>
          </div>
        </div>

        {/* Right Card: DYNAMIC TAXONOMY & POINT TYPES (445px x 460px) */}
        <div
          style={{
            backgroundColor: '#111726',
            borderRadius: '22px',
            border: '1.5px solid rgba(16, 185, 129, 0.28)',
            padding: '28px 30px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <TargetIcon size={28} color="#10b981" />
            <span
              style={{
                fontSize: '26px',
                fontWeight: 900,
                color: '#10b981',
                fontFamily: 'monospace',
                letterSpacing: '1.5px',
              }}
            >
              {currentConfig.legendTitle}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {currentConfig.legend.map((item, lIdx) => (
              <div key={lIdx} style={{ fontSize: '23px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: item.name.includes('Boundary') ? '2px' : '50%',
                    backgroundColor: item.color,
                    display: 'inline-block',
                    boxShadow: `0 0 10px ${item.color}`,
                    flexShrink: 0,
                  }}
                />
                <span>
                  <b>{item.name}</b> {item.desc ? <span>{item.desc}</span> : null}
                </span>
              </div>
            ))}
          </div>

          {/* Key Rule Callout */}
          <div
            style={{
              padding: '14px 18px',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: `1px solid ${currentConfig.ruleColor}55`,
              borderRadius: '14px',
              fontSize: '21px',
              color: currentConfig.ruleColor,
              fontWeight: '600',
              lineHeight: '1.4',
            }}
          >
            {currentConfig.rule}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlgorithmExplorerScene;
