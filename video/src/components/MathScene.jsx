import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { MathIcon, SparklesIcon } from './SvgIcons';

/**
 * MathScene (Phase 5 - 1540px Vertical Stage Layout)
 * Full-height 1540px layout filling 85% of the 1080x1920 canvas:
 *   - Top Editorial Header (220px): 52px bold title, MathIcon, category eyebrow, active badge.
 *   - Center Derivation Steps (860px): Sequential formula reveals with 38px monospace font and 24px explanation.
 *   - Bottom Theorem Intuition Card (380px): Key mathematical takeaway with 24px font and glowing accents.
 */
export const MathScene = ({
  scene,
  words = [],
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const choreography = scene?.choreography || {};
  const stepsData = choreography.steps || [];

  // Fallback if raw steps were provided without choreographer
  const rawSteps = scene?.steps || scene?.equations || [];
  const fallbackSteps = rawSteps.map((step, idx) => ({
    step_index: idx,
    formula: typeof step === 'string' ? step : (step?.formula || step?.latex || ''),
    explanation: typeof step === 'string' ? '' : (step?.explanation || ''),
    reveal_frame: sceneStartFrame + idx * 12,
    highlight_frame: sceneStartFrame + idx * 12 + 6,
    highlight_term: null,
  }));

  const domain = (
    scene?.domain ||
    scene?.subject ||
    scene?.choreography?.domain ||
    'math'
  ).toLowerCase();

  const DOMAIN_FALLBACK_STEPS = {
    electrical: [
      {
        step_index: 0,
        formula: '\\sum_{i} P_{Gi} = P_{\\text{load}} + P_{\\text{loss}}',
        explanation: 'Active Power Balance Constraint',
        reveal_frame: sceneStartFrame,
        highlight_frame: sceneStartFrame + 6,
        highlight_term: null,
      },
      {
        step_index: 1,
        formula: '\\frac{\\partial C_i}{\\partial P_{Gi}} = \\lambda \\quad \\text{subject to } |S_{ij}| \\le S_{ij,\\max}',
        explanation: 'Thermal Line Limit & Economic Dispatch',
        reveal_frame: sceneStartFrame + 18,
        highlight_frame: sceneStartFrame + 24,
        highlight_term: null,
      },
    ],
    mechanics: [
      {
        step_index: 0,
        formula: '\\sum F_x = 0, \\quad \\sum F_y = R_A + R_B - \\sum W_i = 0',
        explanation: 'Translational Static Equilibrium',
        reveal_frame: sceneStartFrame,
        highlight_frame: sceneStartFrame + 6,
        highlight_term: null,
      },
      {
        step_index: 1,
        formula: '\\sum \\tau_A = R_B \\cdot L - \\sum (W_i \\cdot x_i) = 0 \\implies M(x) = \\int V(x) dx',
        explanation: 'Rotational Moment Balance',
        reveal_frame: sceneStartFrame + 18,
        highlight_frame: sceneStartFrame + 24,
        highlight_term: null,
      },
    ],
    quantum_physics: [
      {
        step_index: 0,
        formula: '\\hat{H}\\Psi = E\\Psi \\implies \\kappa = \\frac{\\sqrt{2m(V_0 - E)}}{\\hbar}',
        explanation: 'Wavefunction Attenuation Constant',
        reveal_frame: sceneStartFrame,
        highlight_frame: sceneStartFrame + 6,
        highlight_term: null,
      },
      {
        step_index: 1,
        formula: 'T \\approx e^{-2\\kappa L}, \\quad \\sigma_x \\sigma_p \\ge \\frac{\\hbar}{2}',
        explanation: 'Barrier Transmission & Phase-Space Bound',
        reveal_frame: sceneStartFrame + 18,
        highlight_frame: sceneStartFrame + 24,
        highlight_term: null,
      },
    ],
    chemistry: [
      {
        step_index: 0,
        formula: '\\text{Rate}_{S_N2} = k[\\text{R-X}][\\text{Nu}^-], \\quad \\text{Rate}_{S_N1} = k[\\text{R-X}]',
        explanation: 'Kinetic Order Law',
        reveal_frame: sceneStartFrame,
        highlight_frame: sceneStartFrame + 6,
        highlight_term: null,
      },
      {
        step_index: 1,
        formula: 'k = A e^{-E_a / RT}, \\quad \\Delta G^\\ddagger = \\Delta H^\\ddagger - T\\Delta S^\\ddagger',
        explanation: 'Eyring-Arrhenius Activation Barrier',
        reveal_frame: sceneStartFrame + 18,
        highlight_frame: sceneStartFrame + 24,
        highlight_term: null,
      },
    ],
    math: [
      {
        step_index: 0,
        formula: '\\frac{df}{dx} = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}',
        explanation: 'First-Principles Derivative Limit',
        reveal_frame: sceneStartFrame,
        highlight_frame: sceneStartFrame + 6,
        highlight_term: null,
      },
      {
        step_index: 1,
        formula: '\\int_a^b f\'(x)\\,dx = f(b) - f(a)',
        explanation: 'Fundamental Theorem of Calculus',
        reveal_frame: sceneStartFrame + 18,
        highlight_frame: sceneStartFrame + 24,
        highlight_term: null,
      },
    ],
  };

  const stepsToUse = (stepsData.length > 0 ? stepsData : fallbackSteps);
  const fallbackDefault = DOMAIN_FALLBACK_STEPS[domain] || DOMAIN_FALLBACK_STEPS.math;
  const normalizedSteps = stepsToUse.length > 0 ? stepsToUse : fallbackDefault;

  const palette = choreography.palette || {
    primary: '#79c0ff',
    secondary: '#d2a8ff',
    accent: '#56d364',
    background: '#121d2f',
    border: 'rgba(121, 192, 255, 0.35)',
    glow: 'rgba(121, 192, 255, 0.2)',
  };

  const defaultTitle = `${domain.replace('_', ' ').toUpperCase()} MATHEMATICAL FORMULATION`;
  const title = scene?.title && scene.title !== "Euler's Identity" ? scene.title : defaultTitle;

  const eyebrowText = `${domain.toUpperCase()} • MATHEMATICAL FORMULATION`;

  const DOMAIN_FALLBACK_INTUITION = {
    electrical: {
      text: 'Lagrangian optimization dispatches lowest-cost generators while clamping branch currents below thermal sag thresholds.',
      footer_label: 'Optimal Power Flow (OPF)',
      status: 'CONVERGED',
    },
    mechanics: {
      text: 'Internal shear and bending moments peak where reaction forces balance concentrated structural loads.',
      footer_label: 'Static Determinacy',
      status: 'EQUILIBRIUM',
    },
    quantum_physics: {
      text: 'Non-zero probability amplitude inside classically forbidden barriers enables quantum tunneling.',
      footer_label: 'Unitary Evolution',
      status: 'PROVEN',
    },
    chemistry: {
      text: 'Activation energy height dictates reaction rate; steric hindrance raises the concerted transition state barrier.',
      footer_label: 'Eyring Transition State',
      status: 'VERIFIED',
    },
    physics: {
      text: 'Net external force dictates momentum transfer; conserved quantities remain invariant under continuous symmetry.',
      footer_label: 'Dynamical Conservation',
      status: 'CONSERVED',
    },
    ml: {
      text: 'Backpropagation computes directional gradients along the loss surface toward local empirical risk minima.',
      footer_label: 'Optimization Convergence',
      status: 'OPTIMAL',
    },
    code: {
      text: 'Logarithmic branch partitioning bounds worst-case recursive call depth within deterministic stack limits.',
      footer_label: 'Asymptotic Complexity',
      status: 'BOUNDED',
    },
    math: {
      text: 'Infinitesimal differential limits bridge localized rates of change with global accumulated continuous area.',
      footer_label: 'Analytical Rigor',
      status: 'Q.E.D.',
    },
  };

  const domainIntuition = DOMAIN_FALLBACK_INTUITION[domain] || DOMAIN_FALLBACK_INTUITION.math;
  const rawIntuition = scene?.intuition;
  const intuitionText = (typeof rawIntuition === 'object' && rawIntuition?.text)
    ? rawIntuition.text
    : (typeof rawIntuition === 'string' && rawIntuition.length > 10 ? rawIntuition : domainIntuition.text);
  const footerLabel = (typeof rawIntuition === 'object' && rawIntuition?.footer_label)
    ? rawIntuition.footer_label
    : domainIntuition.footer_label;
  const statusBadge = (typeof rawIntuition === 'object' && rawIntuition?.status)
    ? rawIntuition.status
    : domainIntuition.status;

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
            <MathIcon size={28} color={palette.primary} />
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
              {eyebrowText}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(121, 192, 255, 0.15)',
                border: `1.5px solid ${palette.primary}`,
                color: palette.primary,
                borderRadius: '8px',
                padding: '4px 14px',
                fontSize: '17px',
                fontFamily: 'monospace',
                fontWeight: 900,
              }}
            >
              EXACT PROOF
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
            {scene?.spoken_text || 'Step-by-step rigorous algebraic transition.'}
          </div>
        </div>
      </div>

      {/* 2. CENTER DERIVATION STEPS (860px) */}
      <div
        style={{
          height: '860px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-around',
          gap: '18px',
          boxSizing: 'border-box',
        }}
      >
        {normalizedSteps.map((step, idx) => {
          const isRevealed = frame >= step.reveal_frame;
          const isHighlighted = frame >= step.highlight_frame;

          let opacity = 0;
          if (isRevealed) {
            const elapsed = frame - step.reveal_frame;
            opacity = elapsed < 6 ? Math.round((elapsed / 6) * 100) / 100 : 1;
          }

          return (
            <div
              key={idx}
              style={{
                opacity,
                visibility: isRevealed ? 'visible' : 'hidden',
                backgroundColor: isHighlighted ? 'rgba(121, 192, 255, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                border: isHighlighted
                  ? `2px solid ${palette.primary}`
                  : '1.5px solid rgba(255, 255, 255, 0.08)',
                boxShadow: isHighlighted ? `0 0 24px ${palette.glow}` : 'none',
                borderRadius: '20px',
                padding: '24px 28px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                transition: 'border-color 0.15s ease, background-color 0.15s ease',
                boxSizing: 'border-box',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span
                  style={{
                    fontSize: '20px',
                    fontWeight: 800,
                    color: isHighlighted ? palette.primary : '#8b949e',
                    fontFamily: 'monospace',
                    letterSpacing: '1.5px',
                    textTransform: 'uppercase',
                  }}
                >
                  Step {idx + 1}
                </span>

                {isHighlighted && (
                  <span
                    style={{
                      backgroundColor: 'rgba(86, 211, 100, 0.2)',
                      border: '1px solid #56d364',
                      color: '#56d364',
                      borderRadius: '6px',
                      padding: '3px 12px',
                      fontSize: '15px',
                      fontWeight: 800,
                      fontFamily: 'monospace',
                    }}
                  >
                    ACTIVE FOCUS
                  </span>
                )}
              </div>

              {/* Formatted Formula Line (38px font) */}
              <div
                style={{
                  fontSize: '38px',
                  fontWeight: 'bold',
                  color: '#ffffff',
                  fontFamily: 'monospace',
                  letterSpacing: '1.5px',
                  lineHeight: '1.3',
                  boxSizing: 'border-box',
                }}
              >
                {step.formula}
              </div>

              {/* Explanation Subtext (23px font) */}
              {step.explanation ? (
                <div
                  style={{
                    fontSize: '23px',
                    color: '#94a3b8',
                    fontStyle: 'italic',
                  }}
                >
                  {step.explanation}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>

      {/* 3. BOTTOM THEOREM INTUITION CARD (380px) */}
      <div
        style={{
          height: '380px',
          backgroundColor: '#0b121e',
          borderRadius: '22px',
          border: '1.5px solid rgba(121, 192, 255, 0.3)',
          boxShadow: '0 16px 32px rgba(0, 0, 0, 0.6)',
          padding: '28px 30px',
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
              fontSize: '24px',
              fontWeight: 900,
              color: palette.primary,
              fontFamily: 'monospace',
              letterSpacing: '1.5px',
            }}
          >
            MATHEMATICAL INTUITION
          </span>
        </div>

        <div style={{ fontSize: '24px', color: '#e2e8f0', lineHeight: '1.5' }}>
          {intuitionText}
        </div>

        <div
          style={{
            padding: '14px 20px',
            backgroundColor: 'rgba(121, 192, 255, 0.12)',
            borderRadius: '12px',
            border: '1px solid rgba(121, 192, 255, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span style={{ fontSize: '22px', color: '#79c0ff', fontFamily: 'monospace', fontWeight: 'bold' }}>
            {footerLabel}
          </span>
          <span style={{ fontSize: '18px', color: '#56d364', fontFamily: 'monospace', fontWeight: 800 }}>
            {statusBadge}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MathScene;
