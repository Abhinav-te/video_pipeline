import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { LayersIcon, SparklesIcon } from './SvgIcons';

/**
 * Animated SVG Flow Arrow connecting diagram nodes.
 */
const FlowArrow = ({ isActive }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '60px',
      }}
    >
      <svg width="40" height="60" viewBox="0 0 40 60" fill="none">
        <line
          x1="20"
          y1="4"
          x2="20"
          y2="44"
          stroke={isActive ? '#58a6ff' : '#30363d'}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={isActive ? 'none' : '8 5'}
          style={{ transition: 'stroke 0.15s ease' }}
        />
        <polygon
          points="10,40 20,56 30,40"
          fill={isActive ? '#58a6ff' : '#30363d'}
          style={{
            transition: 'fill 0.15s ease',
          }}
        />
      </svg>
    </div>
  );
};

/**
 * DiagramScene (Phase 5 - 1540px Vertical Stage Layout)
 * Full-height 1540px layout filling 85% of the 1080x1920 canvas:
 *   - Top Editorial Header (160px): LayersIcon, 50px bold title, SceneBadge.
 *   - Center Sequential Flow Nodes (980px): Spacious animated step cards with 32px font.
 *   - Bottom Architecture Invariants Card (340px): System invariants & data contract verification.
 */
export const DiagramScene = ({
  scene,
  sceneStartFrame = 0,
  nextSceneStartTime = null,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const rawNodes = scene?.nodes || [];
  const defaultNodes = [
    { label: 'Client Ingestion & Validation' },
    { label: 'Distributed Queue & Worker Pools' },
    { label: 'Consensus & State Replication' },
  ];
  const nodes = rawNodes.length > 0 ? rawNodes : defaultNodes;
  const nodeCount = Math.max(1, nodes.length);

  const sceneStart = scene?.start_time || 0;
  const sceneDurationFrames = nextSceneStartTime
    ? Math.max(60, Math.round((nextSceneStartTime - sceneStart) * fps))
    : 90;

  const stepInterval = Math.max(12, Math.floor(sceneDurationFrames / (nodeCount + 0.5)));

  return (
    <div
      style={{
        backgroundColor: '#0d1117',
        borderRadius: '28px',
        border: '1.5px solid rgba(88, 166, 255, 0.35)',
        boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 36px rgba(88, 166, 255, 0.15)',
        width: '960px',
        height: '1540px',
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
          flexDirection: 'column',
          gap: '10px',
          height: '140px',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <LayersIcon size={28} color="#58a6ff" />
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
              SYSTEM PIPELINE ARCHITECTURE
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                backgroundColor: 'rgba(88, 166, 255, 0.15)',
                border: '1.5px solid #58a6ff',
                color: '#58a6ff',
                borderRadius: '8px',
                padding: '4px 14px',
                fontSize: '17px',
                fontFamily: 'monospace',
                fontWeight: 900,
              }}
            >
              DATA FLOW
            </span>
            {scene?.badge ? <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} /> : null}
          </div>
        </div>

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
          {scene?.title || 'Execution Flow Pipeline'}
        </div>
      </div>

      {/* 2. CENTER SEQUENTIAL FLOW NODES (980px) */}
      <div
        style={{
          height: '980px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px',
          boxSizing: 'border-box',
        }}
      >
        {nodes.map((node, i) => {
          const nodeStart = sceneStartFrame + i * stepInterval;
          const elapsed = frame - nodeStart;
          const isStarted = elapsed >= 0;

          let nodeOpacity = 0;
          if (isStarted) {
            nodeOpacity = elapsed < 8 ? Math.round((elapsed / 8) * 100) / 100 : 1;
          }

          const nextNodeStart = sceneStartFrame + (i + 1) * stepInterval;
          const isArrowActive = frame >= nextNodeStart - 4;
          const labelText = typeof node === 'string' ? node : (node?.label || JSON.stringify(node));

          return (
            <React.Fragment key={i}>
              {/* Step Node Card */}
              <div
                style={{
                  backgroundColor: isStarted ? '#161b22' : '#0d1117',
                  border: isStarted ? '2px solid #58a6ff' : '2px solid #30363d',
                  borderRadius: '22px',
                  padding: '28px 36px',
                  width: '95%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '24px',
                  boxShadow: isStarted
                    ? '0 20px 40px -8px rgba(0,0,0,0.65), 0 0 24px rgba(88, 166, 255, 0.25)'
                    : 'none',
                  opacity: nodeOpacity,
                  boxSizing: 'border-box',
                  transition: 'border-color 0.15s ease, background-color 0.15s ease',
                }}
              >
                <div
                  style={{
                    backgroundColor: isStarted ? 'rgba(88, 166, 255, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                    border: isStarted ? '1.5px solid #58a6ff' : '1px solid #30363d',
                    color: isStarted ? '#58a6ff' : '#8b949e',
                    borderRadius: '12px',
                    padding: '8px 18px',
                    fontSize: '22px',
                    fontWeight: 900,
                    letterSpacing: '1px',
                    textTransform: 'uppercase',
                    flexShrink: 0,
                  }}
                >
                  Step {i + 1}
                </div>
                <div
                  style={{
                    fontSize: '32px',
                    fontWeight: 'bold',
                    color: '#e6edf3',
                    textAlign: 'left',
                    flex: 1,
                  }}
                >
                  {labelText}
                </div>
              </div>

              {/* Connecting Flow Arrow */}
              {i < nodes.length - 1 && (
                <FlowArrow isActive={isArrowActive} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* 3. BOTTOM CARD: API FLOW PAYLOADS (DevTools) OR ARCHITECTURE INVARIANTS */}
      {(scene?.request_payload || scene?.response_payload || scene?.request_method || scene?.response_status) ? (
        <div
          style={{
            height: '420px',
            backgroundColor: '#0c1017',
            borderRadius: '22px',
            border: '1.5px solid rgba(56, 189, 248, 0.35)',
            boxShadow: '0 16px 32px rgba(0, 0, 0, 0.7)',
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          }}
        >
          {/* Method and Status Headers */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  backgroundColor: 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid #38bdf8',
                  color: '#38bdf8',
                  borderRadius: '6px',
                  padding: '4px 12px',
                  fontSize: '16px',
                  fontWeight: 800,
                  letterSpacing: '0.5px',
                }}
              >
                {scene.request_method || 'POST /v2/agents/stream'}
              </span>
            </div>
            <span
              style={{
                backgroundColor: 'rgba(52, 211, 153, 0.15)',
                border: '1px solid #34d399',
                color: '#34d399',
                borderRadius: '6px',
                padding: '4px 12px',
                fontSize: '16px',
                fontWeight: 800,
              }}
            >
              {scene.response_status || '200 OK • 14ms'}
            </span>
          </div>

          {/* JSON Payload Split Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', margin: '10px 0', flex: 1 }}>
            {/* Request Payload */}
            <div
              style={{
                backgroundColor: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '12px',
                padding: '12px 14px',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
              }}
            >
              <div style={{ fontSize: '13px', color: '#94a3b8', fontWeight: 700, marginBottom: '6px', letterSpacing: '0.5px' }}>
                REQUEST BODY
              </div>
              <pre style={{ margin: 0, fontSize: '17px', color: '#cbd5e1', lineHeight: 1.4, whiteSpace: 'pre-wrap', wordBreak: 'break-all', overflow: 'hidden' }}>
                {scene.request_payload || '{\n  "stream": true\n}'}
              </pre>
            </div>

            {/* Response Payload */}
            <div
              style={{
                backgroundColor: 'rgba(6, 40, 24, 0.4)',
                border: '1px solid rgba(52, 211, 153, 0.25)',
                borderRadius: '12px',
                padding: '12px 14px',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
              }}
            >
              <div style={{ fontSize: '13px', color: '#34d399', fontWeight: 700, marginBottom: '6px', letterSpacing: '0.5px' }}>
                RESPONSE STREAM
              </div>
              <pre style={{ margin: 0, fontSize: '17px', color: '#86efac', lineHeight: 1.4, whiteSpace: 'pre-wrap', wordBreak: 'break-all', overflow: 'hidden' }}>
                {scene.response_payload || '{\n  "status": 200\n}'}
              </pre>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '15px', color: '#64748b', fontFamily: 'monospace', marginTop: '4px' }}>
            <span>PROTOCOL: HTTP/2 • TLS 1.3</span>
            <span style={{ color: '#34d399' }}>✓ mTLS VERIFIED</span>
          </div>
        </div>
      ) : (
        <div
          style={{
            height: '340px',
            backgroundColor: '#161b22',
            borderRadius: '22px',
            border: '1.5px solid rgba(88, 166, 255, 0.3)',
            boxShadow: '0 16px 32px rgba(0, 0, 0, 0.6)',
            padding: '28px 32px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <SparklesIcon size={26} color="#58a6ff" />
            <span
              style={{
                fontSize: '24px',
                fontWeight: 900,
                color: '#58a6ff',
                fontFamily: 'monospace',
                letterSpacing: '1.5px',
              }}
            >
              PIPELINE INVARIANTS & CONSTRAINTS
            </span>
          </div>

          <div style={{ fontSize: '20px', color: '#cbd5e1', lineHeight: '1.4', fontFamily: 'monospace' }}>
            <span>DETERMINISTIC PIPELINE: ZERO REDUNDANT TRANSITIONS • SUB-MS LATENCY</span>
          </div>

          <div
            style={{
              padding: '14px 20px',
              backgroundColor: 'rgba(88, 166, 255, 0.12)',
              borderRadius: '12px',
              border: '1px solid rgba(88, 166, 255, 0.28)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontSize: '22px', color: '#58a6ff', fontFamily: 'monospace', fontWeight: 'bold' }}>
              Throughput: 50,000 req/sec • p99 &lt; 5ms
            </span>
            <span style={{ fontSize: '18px', color: '#56d364', fontFamily: 'monospace', fontWeight: 800 }}>
              OPTIMAL
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiagramScene;
