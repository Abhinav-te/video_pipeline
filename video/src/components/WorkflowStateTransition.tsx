import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { useBrand } from '../context/BrandContext';
import { LayersIcon } from './SvgIcons';

export interface WorkflowEntity {
  id: string;
  label: string;
  sub_label?: string;
}

export interface WorkflowEvent {
  target: string;
  action: 'start' | 'succeed' | 'saved_state' | 'fail' | 'retry' | 'recover';
  label?: string;
  at_word?: string;
  timestamp_sec?: number;
  elapsed?: string | number;
  evidence_id?: string;
}

export interface WorkflowStateTransitionProps {
  scene: {
    title?: string;
    subtitle?: string;
    entities?: WorkflowEntity[];
    events?: WorkflowEvent[];
    start_time?: number;
    end_time?: number;
    badge?: any;
    emphasis_word?: string;
    proof_card?: {
      title?: string;
      body?: string;
      tag?: string;
    };
    callout?: {
      title?: string;
      body?: string;
      tag?: string;
    };
    takeaway?: string;
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

export const WorkflowStateTransition: React.FC<WorkflowStateTransitionProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const brand = useBrand();

  const entities = scene?.entities || scene?.visual?.entities || [];
  const events = scene?.events || scene?.visual?.events || [];

  // Strict validation: No built-in fallbacks
  if (entities.length === 0) {
    throw new Error(
      `[WorkflowStateTransition] Validation Error: 'entities' array is required and must not be empty. Scene: "${scene?.title || 'untitled'}"`
    );
  }
  if (events.length === 0) {
    throw new Error(
      `[WorkflowStateTransition] Validation Error: 'events' array is required and must not be empty. Scene: "${scene?.title || 'untitled'}"`
    );
  }

  const sceneStart = scene.start_time || 0;
  const localFrame = Math.max(0, frame - sceneStartFrame);
  const localSec = localFrame / fps;

  // Track runtime state of each entity
  const stepStates: Record<
    string,
    {
      status: string;
      badgeText: string;
      color: string;
      bgColor: string;
      borderColor: string;
      isMemoized: boolean;
      isRetrying: boolean;
      progress: number;
      elapsedBadge?: string;
    }
  > = {};

  entities.forEach((ent) => {
    stepStates[ent.id] = {
      status: 'idle',
      badgeText: 'PENDING',
      color: '#64748b',
      bgColor: 'rgba(255, 255, 255, 0.04)',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      isMemoized: false,
      isRetrying: false,
      progress: 0,
      elapsedBadge: undefined,
    };
  });

  // Replay events up to localSec strictly based on resolved timestamp_sec
  events.forEach((ev) => {
    // Resolved timestamp relative to scene start
    const triggerSec = ev.timestamp_sec != null
      ? Math.max(0, ev.timestamp_sec - sceneStart)
      : 0;

    if (localSec >= triggerSec) {
      const state = stepStates[ev.target];
      if (!state) return;

      // Elapsed duration badge strictly if evidence backed
      if (ev.elapsed != null && ev.evidence_id) {
        state.elapsedBadge = `${ev.elapsed}`;
      }

      switch (ev.action) {
        case 'start':
          state.status = 'running';
          state.badgeText = ev.label || 'EXECUTING';
          state.color = '#38bdf8';
          state.bgColor = 'rgba(56, 189, 248, 0.12)';
          state.borderColor = 'rgba(56, 189, 248, 0.4)';
          state.progress = 60;
          break;
        case 'succeed':
        case 'saved_state':
          state.status = 'succeeded';
          state.badgeText = ev.label || 'COMPLETED & MEMOIZED';
          state.color = '#34d399';
          state.bgColor = 'rgba(52, 211, 153, 0.14)';
          state.borderColor = 'rgba(52, 211, 153, 0.5)';
          state.isMemoized = true;
          state.progress = 100;
          break;
        case 'fail':
          state.status = 'failed';
          state.badgeText = ev.label || 'HTTP ERROR';
          state.color = '#f87171';
          state.bgColor = 'rgba(248, 113, 113, 0.16)';
          state.borderColor = 'rgba(248, 113, 113, 0.55)';
          state.progress = 40;
          break;
        case 'retry':
          state.status = 'retrying';
          state.badgeText = ev.label || 'RETRYING';
          state.color = '#fbbf24';
          state.bgColor = 'rgba(251, 191, 36, 0.16)';
          state.borderColor = 'rgba(251, 191, 36, 0.6)';
          state.isRetrying = true;
          state.progress = 75;
          break;
        case 'recover':
          state.status = 'recovered';
          state.badgeText = ev.label || 'RECOVERED';
          state.color = '#34d399';
          state.bgColor = 'rgba(52, 211, 153, 0.16)';
          state.borderColor = 'rgba(52, 211, 153, 0.6)';
          state.progress = 100;
          break;
      }
    }
  });

  const proof = scene.proof_card || scene.callout || (scene.takeaway ? { title: scene.takeaway } : null);
  const showProofColumn = isWidescreen && Boolean(proof);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: isWidescreen ? 'row' : 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: isWidescreen ? '36px' : '24px',
        padding: isWidescreen ? '20px 40px' : '16px 8px',
        boxSizing: 'border-box',
        fontFamily: brand?.font_sans || 'Inter, system-ui, sans-serif',
      }}
    >
      {/* Main Execution Waterfall Stage */}
      <div
        style={{
          flex: showProofColumn ? '0 0 68%' : '1 1 auto',
          maxWidth: showProofColumn ? '1140px' : (isWidescreen ? '1400px' : '960px'),
          width: '100%',
          backgroundColor: brand?.bg_surface || '#0c0e17',
          borderRadius: '24px',
          border: `1.5px solid ${brand?.primary_color ? `${brand.primary_color}55` : 'rgba(99, 102, 241, 0.35)'}`,
          boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95)',
          padding: isWidescreen ? '28px 32px' : '24px 20px',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          backdropFilter: 'blur(16px)',
        }}
      >
        {/* Waterfall Header: strictly from scene.title & optional scene.subtitle */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            paddingBottom: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                border: '1px solid #6366F1',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <LayersIcon size={18} color="#818cf8" />
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc' }}>
                {scene.title || 'Workflow Execution Trace'}
              </div>
              {scene.subtitle && (
                <div style={{ fontSize: '12px', color: '#94a3b8', fontFamily: brand?.font_mono || 'monospace' }}>
                  {scene.subtitle}
                </div>
              )}
            </div>
          </div>

          <div
            style={{
              padding: '6px 14px',
              borderRadius: '999px',
              backgroundColor: 'rgba(52, 211, 153, 0.12)',
              border: '1px solid rgba(52, 211, 153, 0.3)',
              color: '#34d399',
              fontSize: '12px',
              fontWeight: 800,
              fontFamily: brand?.font_mono || 'monospace',
              letterSpacing: '0.05em',
            }}
          >
            ACTIVE RUNTIME TRACE
          </div>
        </div>

        {/* Steps Waterfall List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {entities.map((ent, idx) => {
            const st = stepStates[ent.id];
            const isFirst = idx === 0;

            return (
              <div
                key={ent.id}
                style={{
                  backgroundColor: 'rgba(17, 19, 28, 0.8)',
                  borderRadius: '16px',
                  border: `1.5px solid ${st.borderColor}`,
                  padding: '18px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  boxShadow: `0 8px 24px rgba(0, 0, 0, 0.5), 0 0 16px ${st.bgColor}`,
                  transition: 'all 0.2s ease',
                }}
              >
                {/* Step Title & Status Badge */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {isFirst && st.isMemoized ? (
                      <div
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(52, 211, 153, 0.2)',
                          border: '1px solid #34d399',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '14px',
                        }}
                      >
                        🔒
                      </div>
                    ) : (
                      <div
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(255, 255, 255, 0.06)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '12px',
                          fontWeight: 700,
                          color: '#94a3b8',
                          fontFamily: brand?.font_mono || 'monospace',
                        }}
                      >
                        0{idx + 1}
                      </div>
                    )}

                    <div>
                      <div
                        style={{
                          fontFamily: brand?.font_mono || 'monospace',
                          fontSize: '15px',
                          fontWeight: 700,
                          color: '#f1f5f9',
                        }}
                      >
                        {ent.label}
                      </div>
                      {ent.sub_label && (
                        <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                          {ent.sub_label}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {/* Duration / elapsed badge strictly if provided & cited */}
                    {st.elapsedBadge && (
                      <div
                        style={{
                          padding: '4px 10px',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(255, 255, 255, 0.08)',
                          color: '#94a3b8',
                          fontSize: '11px',
                          fontWeight: 700,
                          fontFamily: brand?.font_mono || 'monospace',
                        }}
                      >
                        {st.elapsedBadge}
                      </div>
                    )}

                    {/* Live Status Badge */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '6px 12px',
                        borderRadius: '8px',
                        backgroundColor: st.bgColor,
                        border: `1px solid ${st.borderColor}`,
                        color: st.color,
                        fontSize: '12px',
                        fontWeight: 800,
                        fontFamily: brand?.font_mono || 'monospace',
                        textTransform: 'uppercase',
                      }}
                    >
                      {st.isMemoized && '🔒 '}
                      {st.badgeText}
                    </div>
                  </div>
                </div>

                {/* Live Execution Timeline Span Bar */}
                <div
                  style={{
                    width: '100%',
                    height: '10px',
                    backgroundColor: 'rgba(255, 255, 255, 0.06)',
                    borderRadius: '999px',
                    overflow: 'hidden',
                    position: 'relative',
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: isFirst ? '0%' : '20%',
                      width: `${st.progress * (isFirst ? 0.35 : 0.65)}%`,
                      height: '100%',
                      backgroundColor: st.color,
                      borderRadius: '999px',
                      boxShadow: `0 0 12px ${st.color}`,
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Column (Widescreen) or Bottom Proof Card (Only if proof prop provided) */}
      {proof && (
        <div
          style={{
            flex: isWidescreen ? '0 0 28%' : 'none',
            width: isWidescreen ? 'auto' : '100%',
            maxWidth: isWidescreen ? '400px' : '960px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(17, 19, 28, 0.9)',
              borderRadius: '20px',
              border: '1.5px solid rgba(52, 211, 153, 0.4)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.8), 0 0 24px rgba(52, 211, 153, 0.15)',
              padding: '24px 24px',
              backdropFilter: 'blur(16px)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <span style={{ fontSize: '20px' }}>🔒</span>
              <span
                style={{
                  fontSize: '13px',
                  fontWeight: 800,
                  color: '#34d399',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  fontFamily: brand?.font_mono || 'monospace',
                }}
              >
                {proof.tag || 'VERIFIED GUARANTEE'}
              </span>
            </div>

            {proof.title && (
              <div
                style={{
                  fontSize: isWidescreen ? '18px' : '20px',
                  fontWeight: 700,
                  color: '#ffffff',
                  lineHeight: 1.35,
                  marginBottom: '12px',
                }}
              >
                {proof.title}
              </div>
            )}

            {proof.body && (
              <div style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
                {proof.body}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowStateTransition;
