import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { KineticCallout } from './KineticCallout';
import { WarningIcon, SparklesIcon, ScaleIcon } from './SvgIcons';
import { splitCodeByToken, resolveCalloutTiming } from '../calloutUtils';
import { SPRING_CALLOUT_CONFIG } from '../calloutUtils';

const ComparisonSnippet = ({
  code,
  scene,
  words,
  fps,
  nextSceneStartTime,
  styleVariant = 'box_glow',
}) => {
  const target = scene?.focus_phrase || scene?.emphasis_word;
  const tokenData = code ? splitCodeByToken(code, target) : null;

  if (!tokenData || !tokenData.match) {
    return (
      <code style={{ fontFamily: 'monospace', lineHeight: 1.5, transform: 'none', display: 'block' }}>
        {code}
      </code>
    );
  }

  const { before, match, after } = tokenData;
  const { startFrame, endFrame } = resolveCalloutTiming({
    scene,
    words,
    fps,
    nextSceneStartTime,
  });

  return (
    <code style={{ fontFamily: 'monospace', lineHeight: 1.5, transform: 'none', display: 'block' }}>
      {before}
      <KineticCallout
        startFrame={startFrame}
        endFrame={endFrame}
        styleVariant={styleVariant}
      >
        {match}
      </KineticCallout>
      {after}
    </code>
  );
};

/**
 * ComparisonScene (Phase 5 - 1540px Vertical Stage Layout)
 * Full-height 1540px layout filling 85% of the 1080x1920 canvas:
 *   - Top Editorial Header (160px): ScaleIcon, 50px bold title, SceneBadge.
 *   - Staggered Problem vs Solution Cards (920px): Two tall 440px cards with 26px–30px code.
 *   - Bottom Benchmark Summary Card (380px): O(n^2) vs O(n) complexity and throughput metrics.
 *   - Zero Unicode emojis (clean inline SVG icons). Legacy tag: WINNER 🏆
 */
export const ComparisonScene = ({
  scene,
  subject,
  words = [],
  sceneStartFrame = 0,
  nextSceneStartTime = null,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sides = scene?.comparison_sides;
  const leftSide = sides?.left || (Array.isArray(sides) ? sides[0] : null);
  const rightSide = sides?.right || (Array.isArray(sides) ? sides[1] : null);

  const problemCode = scene?.problem_code || scene?.code_snippet || leftSide?.detail || leftSide?.metric || '';
  const solutionCode = scene?.solution_code || rightSide?.detail || rightSide?.metric || '';
  const problemLabel = leftSide?.tag || leftSide?.title || scene?.problem_label || 'Slow Naive Approach';
  const solutionLabel = rightSide?.tag || rightSide?.title || scene?.solution_label || 'Optimized / Invariant';

  const emphasisTime = typeof scene?.emphasis_time === 'number'
    ? scene.emphasis_time
    : (scene?.start_time || 0) + 1.0;
  const emphasisFrame = Math.round(emphasisTime * fps);

  // Staggered entrance animations
  const card1Start = sceneStartFrame;
  const card1Elapsed = frame - card1Start;
  let card1Opacity = 0;
  if (card1Elapsed >= 0) {
    card1Opacity = card1Elapsed < 8 ? Math.round((card1Elapsed / 8) * 100) / 100 : 1;
  }

  const card2Start = sceneStartFrame + 6;
  const card2Elapsed = frame - card2Start;
  let card2Opacity = 0;
  if (card2Elapsed >= 0) {
    card2Opacity = card2Elapsed < 8 ? Math.round((card2Elapsed / 8) * 100) / 100 : 1;
  }

  // Emphasis illumination
  const isPostEmphasis = frame >= emphasisFrame;
  let winnerGlow = 0;
  if (isPostEmphasis) {
    const rawSpring = spring({
      frame: frame - emphasisFrame,
      fps,
      config: SPRING_CALLOUT_CONFIG,
    });
    winnerGlow = Math.round(interpolate(rawSpring, [0, 1], [0, 36]));
  }

  return (
    <div
      style={{
        backgroundColor: '#0d1117',
        borderRadius: '28px',
        border: '1.5px solid rgba(255, 255, 255, 0.12)',
        boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95)',
        width: '960px',
        height: '1360px',
        maxHeight: '1360px',
        overflow: 'hidden',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        position: 'relative',
        padding: '24px 28px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      {/* 1. TOP EDITORIAL HEADER (140px) */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          height: '130px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <ScaleIcon size={28} color="#58a6ff" />
            <span
              style={{
                fontSize: '22px',
                fontWeight: 800,
                color: '#58a6ff',
                fontFamily: 'monospace',
                letterSpacing: '2.5px',
                textTransform: 'uppercase',
              }}
            >
              ALGORITHM ARCHITECTURE • BENCHMARK
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
          </div>
        </div>

        <div
          style={{
            fontSize: '44px',
            fontWeight: 900,
            color: '#ffffff',
            fontFamily: 'sans-serif',
            letterSpacing: '-0.5px',
            lineHeight: '1.15',
          }}
        >
          {scene?.title || 'Algorithmic Comparison'}
        </div>
      </div>

      {/* 2. STAGGERED PROBLEM VS SOLUTION CARDS (760px) */}
      <div
        style={{
          height: '760px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '18px',
          boxSizing: 'border-box',
        }}
      >
        {/* CARD 1: PROBLEM CARD (Red Accent) */}
        <div
          style={{
            flex: 1,
            backgroundColor: '#220b12',
            padding: '28px 32px',
            borderRadius: '22px',
            border: '2px solid rgba(255, 123, 114, 0.8)',
            boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.6)',
            opacity: card1Opacity,
            overflow: 'hidden',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <WarningIcon size={26} color="#ff7b72" />
            <h2 style={{ color: '#ff7b72', margin: 0, fontSize: '30px', fontWeight: 800 }}>
              {problemLabel}
            </h2>
          </div>
          <pre
            style={{
              fontSize: '26px',
              lineHeight: '1.5',
              color: '#c9d1d9',
              margin: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'monospace',
            }}
          >
            <ComparisonSnippet
              code={problemCode}
              scene={scene}
              words={words}
              fps={fps}
              nextSceneStartTime={nextSceneStartTime}
              styleVariant="box_glow"
            />
          </pre>
        </div>

        {/* CARD 2: SOLUTION / WINNING CARD (Green Accent + Emerald Glow) */}
        <div
          style={{
            flex: 1,
            backgroundColor: '#0a2213',
            padding: '28px 32px',
            borderRadius: '22px',
            border: isPostEmphasis
              ? '2px solid #3fb950'
              : '2px solid rgba(63, 185, 80, 0.8)',
            boxShadow: isPostEmphasis
              ? `0 0 ${winnerGlow}px rgba(63, 185, 80, 0.65), 0 20px 40px -10px rgba(0, 0, 0, 0.6)`
              : '0 20px 40px -10px rgba(0, 0, 0, 0.6)',
            opacity: card2Opacity,
            overflow: 'hidden',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            transition: 'border-color 0.15s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <SparklesIcon size={26} color="#3fb950" />
              <h2 style={{ color: '#3fb950', margin: 0, fontSize: '30px', fontWeight: 800 }}>
                {solutionLabel}
              </h2>
            </div>
            {isPostEmphasis && (
              <span
                style={{
                  backgroundColor: 'rgba(63, 185, 80, 0.2)',
                  border: '1.5px solid #3fb950',
                  color: '#3fb950',
                  borderRadius: '8px',
                  padding: '4px 14px',
                  fontSize: '18px',
                  fontWeight: 'bold',
                  fontFamily: 'monospace',
                  letterSpacing: '0.8px',
                }}
              >
                OPTIMAL WINNER
              </span>
            )}
          </div>
          <pre
            style={{
              fontSize: '26px',
              lineHeight: '1.5',
              color: '#e6edf3',
              margin: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'monospace',
            }}
          >
            <ComparisonSnippet
              code={solutionCode}
              scene={scene}
              words={words}
              fps={fps}
              nextSceneStartTime={nextSceneStartTime}
              styleVariant="box_glow"
            />
          </pre>
        </div>
      </div>

      {/* 3. BOTTOM BENCHMARK / DOMAIN SUMMARY CARD (380px) */}
      {(() => {
        const domain = (
          subject ||
          scene?.subject ||
          scene?.domain ||
          scene?.choreography?.domain ||
          scene?.choreography?.theme?.badge_tag ||
          ''
        ).toLowerCase();

        const textLower = `${scene?.title || ''} ${scene?.display_text || ''} ${scene?.spoken_text || ''} ${problemLabel} ${solutionLabel}`.toLowerCase();

        const isCode = domain.includes('code') || domain.includes('algo') || domain.includes('soft') || textLower.includes('complexity') || textLower.includes('hash table');
        const isMath = domain.includes('math') || domain.includes('calc') || textLower.includes('calculus') || textLower.includes('integral') || textLower.includes('derivative') || textLower.includes('riemann') || textLower.includes('euler') || textLower.includes('partition');
        const isChemistry = domain.includes('chem') || textLower.includes('sn1') || textLower.includes('sn2') || textLower.includes('reaction');
        const isQuantum = domain.includes('quantum') || textLower.includes('schrodinger') || textLower.includes('tunneling') || textLower.includes('heisenberg') || textLower.includes('wavepacket');
        const isPhysicsOrMechanics = domain.includes('mechanic') || domain.includes('physics') || textLower.includes('beam') || textLower.includes('equilibrium') || textLower.includes('inclined plane') || textLower.includes('axle') || textLower.includes('newton');
        const isElectrical = domain.includes('electr') || textLower.includes('thevenin') || textLower.includes('kvl') || textLower.includes('smart grid') || textLower.includes('circuit');
        const isML = domain.includes('ml') || textLower.includes('cluster') || textLower.includes('centroid') || textLower.includes('dbscan') || textLower.includes('kmeans');
        const isDevTools = domain.includes('devtools') || textLower.includes('sdk') || textLower.includes('migration') || textLower.includes('latency');

        // Derive labels dynamically from leftSide / rightSide cards if provided
        const leftTag = leftSide?.tag ? `${leftSide.tag.toUpperCase()}` : '';
        const rightTag = rightSide?.tag ? `${rightSide.tag.toUpperCase()}` : '';

        let footerTitle = 'MATHEMATICAL DUALITY & BOUNDS';
        let defaultLeftLabel = leftTag || 'DISCRETE FORMULATION';
        let defaultLeftMetric = leftSide?.metric || 'Σ f(x_i) Δx (Partition)';
        let defaultRightLabel = rightTag || 'CONTINUOUS LIMIT';
        let defaultRightMetric = rightSide?.metric || '∫ f(x) dx (Antiderivative)';
        let defaultSummary = 'KEY TAKEAWAY: Infinite refinement transforms discrete sums into exact continuous antiderivatives';
        let defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'FUNDAMENTAL THEOREM';

        if (isCode) {
          footerTitle = 'ASYMPTOTIC COMPLEXITY ANALYSIS';
          defaultLeftLabel = leftTag || 'TIME COMPLEXITY';
          defaultLeftMetric = leftSide?.metric || 'O(n²) Quadratic';
          defaultRightLabel = rightTag || 'OPTIMIZED RUNTIME';
          defaultRightMetric = rightSide?.metric || 'O(n) Linear';
          defaultSummary = scene?.speedup || (rightSide?.metric ? `Outcome: ${rightSide.metric}` : 'Speedup: 1,000x on 100,000 elements');
          defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'SPACE: O(n)';
        } else if (isChemistry) {
          footerTitle = 'RATE LAW CONTRAST & STEREOCHEMISTRY';
          defaultLeftLabel = leftTag || '2ND ORDER (CONCERTED)';
          defaultLeftMetric = leftSide?.metric || 'Rate = k[R-X][Nu⁻]';
          defaultRightLabel = rightTag || '1ST ORDER (IONIZATION)';
          defaultRightMetric = rightSide?.metric || 'Rate = k[R-X]';
          defaultSummary = 'KEY TAKEAWAY: Substrate hindrance determines whether concerted SN2 or carbocation SN1 dominates';
          defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'STEREO: INVERSION VS RACEMIC';
        } else if (isQuantum) {
          footerTitle = 'CANONICAL COMMUTATION & UNCERTAINTY';
          defaultLeftLabel = leftTag || 'COMMUTATION RELATION';
          defaultLeftMetric = leftSide?.metric || '[x̂, p̂] = iℏ';
          defaultRightLabel = rightTag || 'UNCERTAINTY BOUND';
          defaultRightMetric = rightSide?.metric || 'Δx·Δp ≥ ℏ/2';
          defaultSummary = 'KEY TAKEAWAY: Wavefunction superposition enables quantum tunneling through classical barriers';
          defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'UNCERTAINTY BOUND: Δx·Δp ≥ ℏ/2';
        } else if (isPhysicsOrMechanics) {
          footerTitle = 'EQUILIBRIUM & CONSERVATION LAWS';
          defaultLeftLabel = leftTag || 'EQUILIBRIUM CONDITION';
          defaultLeftMetric = leftSide?.metric || 'ΣF_x = 0, ΣF_y = 0, Στ = 0';
          defaultRightLabel = rightTag || 'CONSERVATION PRINCIPLE';
          defaultRightMetric = rightSide?.metric || 'E_mech = K + U = const';
          defaultSummary = 'KEY TAKEAWAY: Resolving equilibrium reactions eliminates structural collapse risks';
          defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'CONSERVATION: MECHANICAL ENERGY';
        } else if (isElectrical) {
          footerTitle = 'NETWORK EQUIVALENCE & POWER FLOW';
          defaultLeftLabel = leftTag || 'THÉVENIN EQUIVALENCE';
          defaultLeftMetric = leftSide?.metric || 'V_th = V_oc, R_th = V_oc / I_sc';
          defaultRightLabel = rightTag || 'POWER CONSERVATION';
          defaultRightMetric = rightSide?.metric || 'ΣP_gen = ΣP_load + P_loss';
          defaultSummary = 'KEY TAKEAWAY: Linear network reduction simplifies multi-bus OPF solver complexity by 100x';
          defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'POWER FLOW: ΣP_gen = ΣP_load + P_loss';
        } else if (isML) {
          footerTitle = 'LATENT MANIFOLD & GEOMETRY';
          defaultLeftLabel = leftTag || 'HIGH-DIM RAW SPACE';
          defaultLeftMetric = leftSide?.metric || 'd = 512 (Euclidean)';
          defaultRightLabel = rightTag || 'LATENT EMBEDDING';
          defaultRightMetric = rightSide?.metric || 'd = 2 (Non-linear)';
          defaultSummary = 'KEY TAKEAWAY: Manifold learning preserves topological neighborhoods across complex distributions';
          defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'TOPOLOGY: NEIGHBORHOOD';
        } else if (isDevTools) {
          footerTitle = 'PERFORMANCE & DEVELOPER EXPERIENCE BENCHMARK';
          defaultLeftLabel = leftTag || 'LEGACY SDK (V1)';
          defaultLeftMetric = leftSide?.metric || '840ms Latency';
          defaultRightLabel = rightTag || 'NEW SDK (V2)';
          defaultRightMetric = rightSide?.metric || '140ms Latency (6x Faster)';
          defaultSummary = scene?.comparison_footer || 'KEY TAKEAWAY: v2 SDK reduces cold-start latency by 6x with 90% less boilerplate';
          defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'BENCHMARK: 6x SPEEDUP';
        } else if (!isMath) {
          footerTitle = 'COMPARATIVE REGIME ANALYSIS';
          defaultLeftLabel = leftTag || (leftSide?.title ? `${leftSide.title.toUpperCase()}` : 'BASELINE APPROACH');
          defaultLeftMetric = leftSide?.metric || 'Standard Model';
          defaultRightLabel = rightTag || (rightSide?.title ? `${rightSide.title.toUpperCase()}` : 'OPTIMIZED APPROACH');
          defaultRightMetric = rightSide?.metric || 'Refined Model';
          defaultSummary = `KEY TAKEAWAY: Evaluating trade-offs between ${leftSide?.tag || 'baseline'} and ${rightSide?.tag || 'optimized'}`;
          defaultTag = leftTag && rightTag ? `${leftTag} VS ${rightTag}` : 'ANALYSIS';
        }

        let rawSummary = typeof scene?.comparison_footer === 'string'
          ? scene.comparison_footer
          : (scene?.takeaway || scene?.summary || defaultSummary);

        // Strip any pipe-separated duplicate suffixes (| NETWORK EQUIVALENCE: ..., | POWER FLOW: ...)
        if (rawSummary.includes('|')) {
          rawSummary = rawSummary.split('|')[0].trim();
        }
        // Normalize to clean KEY TAKEAWAY prefix
        const cleanSummary = rawSummary.startsWith('KEY TAKEAWAY:')
          ? rawSummary
          : `KEY TAKEAWAY: ${rawSummary.replace(/^[A-Z\s_]+:\s*/, '')}`;

        return (
          <div
            style={{
              height: '380px',
              backgroundColor: '#161b22',
              borderRadius: '22px',
              border: '1.5px solid rgba(255, 255, 255, 0.1)',
              padding: '28px 32px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              transform: 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <SparklesIcon size={26} color="#3fb950" />
              <span
                style={{
                  fontSize: '24px',
                  fontWeight: 900,
                  color: '#3fb950',
                  fontFamily: 'monospace',
                  letterSpacing: '1.5px',
                }}
              >
                {footerTitle}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div
                style={{
                  padding: '18px 22px',
                  backgroundColor: '#0d1117',
                  borderRadius: '14px',
                  border: '1px solid rgba(255, 123, 114, 0.3)',
                }}
              >
                <div style={{ fontSize: '18px', color: '#ff7b72', fontFamily: 'monospace', marginBottom: '6px' }}>
                  {defaultLeftLabel}
                </div>
                <div style={{ fontSize: '30px', color: '#ff7b72', fontWeight: 'bold', fontFamily: 'monospace' }}>
                  {defaultLeftMetric}
                </div>
              </div>

              <div
                style={{
                  padding: '18px 22px',
                  backgroundColor: '#0d1117',
                  borderRadius: '14px',
                  border: '1px solid rgba(63, 185, 80, 0.3)',
                }}
              >
                <div style={{ fontSize: '18px', color: '#3fb950', fontFamily: 'monospace', marginBottom: '6px' }}>
                  {defaultRightLabel}
                </div>
                <div style={{ fontSize: '30px', color: '#3fb950', fontWeight: 'bold', fontFamily: 'monospace' }}>
                  {defaultRightMetric}
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '14px 20px',
                backgroundColor: 'rgba(63, 185, 80, 0.12)',
                borderRadius: '12px',
                border: '1px solid rgba(63, 185, 80, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: '20px', color: '#3fb950', fontFamily: 'monospace', fontWeight: 'bold' }}>
                {cleanSummary}
              </span>
              <span style={{ fontSize: '18px', color: '#56d364', fontFamily: 'monospace', fontWeight: 800, whiteSpace: 'nowrap', marginLeft: '16px' }}>
                OPTIMAL
              </span>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default ComparisonScene;
