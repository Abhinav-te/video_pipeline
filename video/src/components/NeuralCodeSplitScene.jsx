import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { BrainIcon, LayersIcon } from './SvgIcons';

/**
 * NeuralCodeSplitScene (Phase 5 - 1540px Vertical Stage Layout)
 * Full-screen Top Visualizer + Bottom Code layout utilizing 88% of the 1080x1920 canvas:
 *   - Top Header (160px): ML IN PYTHON eyebrow, 52px editorial title, FROM SCRATCH badge.
 *   - Upper Visualizer Card (640px):
 *       • Left: 220x220 8x8 handwriting pixel grid (digit #5) + 16 digit thumbnail strip
 *       • Center: Tall 3-layer neural net (12 -> 10 -> 10 nodes spanning 460px height) with animated pulses
 *       • Right: 28px mono Loss & Epoch telemetry + 10 horizontal probability bars (0–9)
 *   - Lower Code Editor Card (680px):
 *       • 15 lines of Python code (22px monospace font, 36px line height) with sweeping glowing active-line bar
 */
export const NeuralCodeSplitScene = ({
  scene,
  words = [],
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const choreography = scene?.choreography || {};
  const neuralChoreo = choreography.neural || {};

  const startF = sceneStartFrame;
  const endF = choreography.scene_end_frame || (sceneStartFrame + 60);

  // Training Telemetries (Live Counters)
  const trainProgress = interpolate(
    frame,
    [startF, endF],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const currentLoss = (0.842 - (0.842 - 0.184) * trainProgress).toFixed(3);
  const currentEpoch = Math.min(300, Math.floor(1 + 299 * trainProgress));
  const prob5 = Math.min(96, Math.floor(40 + 56 * trainProgress));

  // Active Line Sweeper for Code Window (Auto-enriched to at least 8-10 lines if snippet is short)
  const rawCodeSnippet = scene?.code_snippet || '';
  let rawLines = rawCodeSnippet ? rawCodeSnippet.split('\n').filter(Boolean) : [];

  if (rawLines.length > 0 && rawLines.length < 8) {
    const enrichedPrefix = [
      'class NeuralManifold(nn.Module):',
      '    def __init__(self, in_features=784, latent_dim=32):',
      '        super().__init__()',
      '        self.encoder = nn.Linear(in_features, latent_dim)',
    ];
    const enrichedSuffix = [
      '        loss = F.mse_loss(recon, target)',
      '        return loss, z',
    ];
    rawLines = [...enrichedPrefix, ...rawLines, ...enrichedSuffix];
  }

  const defaultCodeLines = [
    'def forward(x, W1, b1, W2, b2):',
    '    z1 = x @ W1 + b1',
    '    a1 = np.maximum(0, z1)  # ReLU activation',
    '    z2 = a1 @ W2 + b2',
    '    probs = softmax(z2)',
    '    return probs',
    '',
    'def backward(x, y, probs, a1, W2):',
    '    dz2 = probs - y  # Cross-entropy loss grad',
    '    dW2 = a1.T @ dz2',
    '    da1 = dz2 @ W2.T',
    '    dz1 = da1 * (a1 > 0)  # ReLU derivative',
    '    return dW2, dz1',
    '',
    'def train_step(x, y, lr=0.01):',
    '    probs = forward(x, W1, b1, W2, b2)',
    '    return -np.sum(y * np.log(probs + 1e-8))',
  ];

  const codeLines = rawLines.length >= 8 ? rawLines : defaultCodeLines;

  const highlightFrames = neuralChoreo.line_highlight_frames || [];
  let activeLineIdx = 0;
  if (highlightFrames.length > 0) {
    for (let idx = 0; idx < highlightFrames.length; idx++) {
      if (frame >= highlightFrames[idx]) {
        activeLineIdx = idx;
      }
    }
  } else {
    activeLineIdx = Math.min(
      codeLines.length - 1,
      Math.floor(trainProgress * codeLines.length)
    );
  }

  // 8x8 bitmap for digit 5
  const digit5Bitmap = [
    1, 1, 1, 1, 1, 1, 1, 0,
    1, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 0, 0,
    0, 0, 0, 0, 0, 0, 1, 0,
    0, 0, 0, 0, 0, 0, 1, 0,
    1, 0, 0, 0, 0, 0, 1, 0,
    0, 1, 1, 1, 1, 1, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
  ];

  // Neural network node positions spanning 460px height
  const inputY = [30, 70, 110, 150, 190, 230, 270, 310, 350, 390, 430, 470];
  const hiddenY = [45, 90, 135, 180, 225, 270, 315, 360, 405, 450];
  const outputY = [45, 90, 135, 180, 225, 270, 315, 360, 405, 450]; // 10 classes (0-9)

  // Animated traveling signal pulses
  const pulseT = (frame * 0.08) % 1;

  return (
    <div
      style={{
        backgroundColor: '#070b12',
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
      {/* 1. TOP EDITORIAL HEADER (160px) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '130px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          paddingBottom: '16px',
          boxSizing: 'border-box',
        }}
      >
        <div>
          <div
            style={{
              fontSize: '22px',
              fontWeight: 800,
              letterSpacing: '2.5px',
              color: '#f59e0b',
              textTransform: 'uppercase',
              fontFamily: 'monospace',
              marginBottom: '6px',
            }}
          >
            ML IN PYTHON • DEEP LEARNING
          </div>
          <div
            style={{
              fontSize: '52px',
              fontWeight: 900,
              color: '#f8fafc',
              letterSpacing: '-0.5px',
              fontFamily: 'sans-serif',
              lineHeight: '1.1',
            }}
          >
            Neural Network
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span
            style={{
              backgroundColor: 'rgba(245, 158, 11, 0.18)',
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
            FROM SCRATCH
          </span>
          {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
        </div>
      </div>

      {/* 2. UPPER LIVE SIMULATION PANEL (640px) */}
      <div
        style={{
          height: '640px',
          backgroundColor: '#0b101b',
          borderRadius: '22px',
          border: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxShadow: 'inset 0 0 32px rgba(0, 0, 0, 0.7)',
          padding: '24px 28px',
          display: 'grid',
          gridTemplateColumns: '240px 1fr 260px',
          gap: '24px',
          alignItems: 'center',
          boxSizing: 'border-box',
        }}
      >
        {/* Left Column: 220x220 8x8 Handwriting Pixel Grid + 16 Thumbnails */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
          <div style={{ fontSize: '20px', color: '#f59e0b', fontFamily: 'monospace', fontWeight: 800 }}>
            INPUT: digit #5
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(8, 1fr)',
              gap: '4px',
              width: '220px',
              height: '220px',
              padding: '10px',
              backgroundColor: '#141a28',
              borderRadius: '14px',
              border: '1.5px solid rgba(245, 158, 11, 0.3)',
              boxShadow: '0 0 20px rgba(245, 158, 11, 0.15)',
              boxSizing: 'border-box',
            }}
          >
            {digit5Bitmap.map((val, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: val ? '#f59e0b' : '#090d15',
                  borderRadius: '3px',
                  boxShadow: val ? '0 0 8px #f59e0b' : 'none',
                }}
              />
            ))}
          </div>

          {/* Strip of 16 Digit Thumbnails */}
          <div style={{ width: '220px' }}>
            <div style={{ fontSize: '15px', color: '#64748b', fontFamily: 'monospace', marginBottom: '6px', textAlign: 'center' }}>
              BATCH SAMPLES [0..15]
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(8, 1fr)',
                gap: '4px',
              }}
            >
              {Array.from({ length: 16 }).map((_, i) => (
                <div
                  key={i}
                  style={{
                    height: '22px',
                    borderRadius: '4px',
                    backgroundColor: i === 5 ? 'rgba(245, 158, 11, 0.35)' : '#161d2d',
                    border: i === 5 ? '1px solid #f59e0b' : '1px solid rgba(255, 255, 255, 0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                    color: i === 5 ? '#f59e0b' : '#64748b',
                    fontWeight: 'bold',
                  }}
                >
                  {i}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Center Column: Tall 3-Layer Neural Network Graph (460px height) */}
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <svg width="340" height="520" viewBox="0 0 340 520" style={{ overflow: 'visible' }}>
            {/* Input layer to Hidden layer edges */}
            {inputY.map((y1, i) =>
              hiddenY.map((y2, j) => (
                <line
                  key={`in-${i}-${j}`}
                  x1="50"
                  y1={y1}
                  x2="170"
                  y2={y2}
                  stroke="#38bdf8"
                  strokeWidth="1.2"
                  strokeOpacity={0.15 + 0.25 * Math.sin(frame * 0.1 + i + j)}
                />
              ))
            )}

            {/* Hidden layer to Output layer edges */}
            {hiddenY.map((y1, i) =>
              outputY.map((y2, j) => (
                <line
                  key={`out-${i}-${j}`}
                  x1="170"
                  y1={y1}
                  x2="290"
                  y2={y2}
                  stroke={j === 5 ? '#10b981' : '#f59e0b'}
                  strokeWidth={j === 5 ? '2.5' : '1.2'}
                  strokeOpacity={j === 5 ? '0.85' : '0.15'}
                />
              ))
            )}

            {/* Traveling Forward Signal Pulses */}
            {hiddenY.map((y, idx) => {
              const px = 50 + (170 - 50) * pulseT;
              const py = inputY[idx % inputY.length] + (y - inputY[idx % inputY.length]) * pulseT;
              return (
                <circle
                  key={`pulse-${idx}`}
                  cx={px}
                  cy={py}
                  r="3.5"
                  fill="#f59e0b"
                />
              );
            })}

            {/* Layer 1 Nodes (12 nodes) */}
            {inputY.map((y, i) => (
              <circle key={`l1-${i}`} cx="50" cy={y} r="8" fill="#38bdf8" stroke="#ffffff" strokeWidth="1.5" />
            ))}

            {/* Layer 2 Nodes (10 nodes) */}
            {hiddenY.map((y, i) => (
              <circle key={`l2-${i}`} cx="170" cy={y} r="8" fill="#818cf8" stroke="#ffffff" strokeWidth="1.5" />
            ))}

            {/* Layer 3 Output Nodes (10 nodes, 0–9) */}
            {outputY.map((y, i) => (
              <g key={`l3-${i}`}>
                <circle
                  cx="290"
                  cy={y}
                  r={i === 5 ? 10 : 8}
                  fill={i === 5 ? '#10b981' : '#f59e0b'}
                  stroke="#ffffff"
                  strokeWidth="2"
                />
                <text x="312" y={y + 5} fill={i === 5 ? '#10b981' : '#64748b'} fontSize="16" fontWeight="bold" fontFamily="monospace">
                  {i}
                </text>
              </g>
            ))}
          </svg>
        </div>

        {/* Right Column: 28px Mono Loss/Epoch Telemetry + 10 Probability Bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', justifyContent: 'center' }}>
          {/* Live Telemetry Card */}
          <div
            style={{
              padding: '16px 20px',
              backgroundColor: '#141a28',
              borderRadius: '14px',
              border: '1.5px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'monospace', fontSize: '26px' }}>
              <span style={{ color: '#94a3b8' }}>Loss:</span>
              <span style={{ color: '#f59e0b', fontWeight: 900 }}>{currentLoss}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'monospace', fontSize: '26px' }}>
              <span style={{ color: '#94a3b8' }}>Epoch:</span>
              <span style={{ color: '#38bdf8', fontWeight: 900 }}>{currentEpoch}/300</span>
            </div>
          </div>

          {/* 10 Horizontal Probability Bars (0-9) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {Array.from({ length: 10 }).map((_, digit) => {
              const isTarget = digit === 5;
              const barWidth = isTarget ? prob5 : Math.max(3, (digit * 3) % 9);
              return (
                <div key={digit} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      width: '18px',
                      fontSize: '15px',
                      fontFamily: 'monospace',
                      fontWeight: isTarget ? 'bold' : 'normal',
                      color: isTarget ? '#10b981' : '#64748b',
                    }}
                  >
                    #{digit}
                  </span>
                  <div
                    style={{
                      flex: 1,
                      height: '14px',
                      backgroundColor: '#161d2d',
                      borderRadius: '4px',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${barWidth}%`,
                        height: '100%',
                        backgroundColor: isTarget ? '#10b981' : '#475569',
                        borderRadius: '4px',
                        boxShadow: isTarget ? '0 0 10px rgba(16, 185, 129, 0.7)' : 'none',
                        transition: 'width 0.1s ease',
                      }}
                    />
                  </div>
                  <span
                    style={{
                      width: '42px',
                      fontSize: '14px',
                      fontFamily: 'monospace',
                      fontWeight: isTarget ? 'bold' : 'normal',
                      color: isTarget ? '#10b981' : '#64748b',
                      textAlign: 'right',
                    }}
                  >
                    {barWidth}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. LOWER CODE EDITOR CARD (680px) */}
      <div
        style={{
          height: '680px',
          backgroundColor: '#080d17',
          borderRadius: '22px',
          border: '1.5px solid rgba(255, 255, 255, 0.1)',
          padding: '24px 28px',
          display: 'flex',
          flexDirection: 'column',
          boxSizing: 'border-box',
          position: 'relative',
        }}
      >
        {/* Terminal Header Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '16px',
            paddingBottom: '12px',
            borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#ff5f56', display: 'inline-block' }} />
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#ffbd2e', display: 'inline-block' }} />
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#27c93f', display: 'inline-block' }} />
          <span style={{ marginLeft: '12px', fontSize: '20px', color: '#cbd5e1', fontFamily: 'monospace', fontWeight: 'bold' }}>
            neural_network.py
          </span>
        </div>

        {/* Syntax-Highlighted Python Code with consistent 38px line height */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            fontFamily: 'monospace',
            fontSize: '20px',
            lineHeight: '38px',
            justifyContent: 'flex-start',
            gap: '2px',
            overflow: 'hidden',
            flex: 1,
          }}
        >
          {codeLines.slice(0, 10).map((line, idx) => {
            const isLineActive = idx === activeLineIdx;
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  lineHeight: '38px',
                  height: '38px',
                  backgroundColor: isLineActive ? 'rgba(245, 158, 11, 0.22)' : 'transparent',
                  borderLeft: isLineActive ? '4px solid #f59e0b' : '4px solid transparent',
                  paddingLeft: '12px',
                  boxShadow: isLineActive ? '0 0 20px rgba(245, 158, 11, 0.35)' : 'none',
                  borderRadius: '3px',
                }}
              >
                {/* Line Number */}
                <span
                  style={{
                    width: '38px',
                    color: isLineActive ? '#f59e0b' : '#475569',
                    userSelect: 'none',
                    fontWeight: isLineActive ? 'bold' : 'normal',
                  }}
                >
                  {idx + 1}
                </span>
                {/* Line Text */}
                <span style={{ color: isLineActive ? '#ffffff' : '#cbd5e1', whiteSpace: 'pre' }}>
                  {line}
                </span>
              </div>
            );
          })}
        </div>

        {/* Live Tensor Shape & Hardware Telemetry Panel */}
        <div
          style={{
            marginTop: '12px',
            padding: '12px 16px',
            backgroundColor: '#0c1322',
            borderRadius: '12px',
            border: '1.5px solid rgba(56, 189, 248, 0.25)',
            boxShadow: '0 8px 20px rgba(0, 0, 0, 0.4)',
            fontFamily: 'monospace',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span style={{ fontSize: '13px', fontWeight: 800, color: '#38bdf8', letterSpacing: '1px' }}>
              LIVE TENSOR SHAPE & HARDWARE TELEMETRY
            </span>
            <span style={{ fontSize: '12px', color: '#10b981', fontWeight: 700, backgroundColor: 'rgba(16, 185, 129, 0.15)', padding: '2px 8px', borderRadius: '4px' }}>
              CUDA ACTIVE
            </span>
          </div>
          <div style={{ fontSize: '14px', color: '#f1f5f9', fontWeight: 600, letterSpacing: '0.2px', marginBottom: '6px' }}>
            {'Input: [B, 784] -> Encoder: [B, 128] -> Latent Z: [B, 32] -> Recon: [B, 784]'}
          </div>
          <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: '#94a3b8' }}>
            <span>VRAM: <strong style={{ color: '#f59e0b' }}>42 MB</strong></span>
            <span>•</span>
            <span>Throughput: <strong style={{ color: '#10b981' }}>1,420 samples/s</strong></span>
            <span>•</span>
            <span>Latency: <strong style={{ color: '#38bdf8' }}>1.8 ms/step</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NeuralCodeSplitScene;
