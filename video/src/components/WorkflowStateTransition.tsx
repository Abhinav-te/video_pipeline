import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { useBrand, useTheme, ThemeTokens } from '../context/BrandContext';
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
    visual?: {
      entities?: WorkflowEntity[];
      events?: WorkflowEvent[];
    };
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

// Crisp inline SVG vector icons (preventing headless Linux Chromium emoji tofu [▯])
const LockIcon: React.FC<{ size?: number; color?: string }> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const CheckIcon: React.FC<{ size?: number; color?: string }> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const AlertIcon: React.FC<{ size?: number; color?: string }> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

const RetryIcon: React.FC<{ size?: number; color?: string }> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <polyline points="1 4 1 10 7 10" />
    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
  </svg>
);

const ShieldCheckIcon: React.FC<{ size?: number; color?: string }> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <polyline points="9 12 11 14 15 10" />
  </svg>
);

const ArrowDownIcon: React.FC<{ size?: number; color?: string }> = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <line x1="12" y1="5" x2="12" y2="19" />
    <polyline points="19 12 12 19 5 12" />
  </svg>
);

const ArrowRightIcon: React.FC<{ size?: number; color?: string }> = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </svg>
);

export const WorkflowStateTransition: React.FC<WorkflowStateTransitionProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const brand = useBrand();
  const theme = useTheme();

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
  interface EntityRuntimeState {
    status: 'idle' | 'running' | 'succeeded' | 'failed' | 'retrying' | 'recovered';
    badgeText: string;
    activeActionLabel: string;
    color: string;
    bgColor: string;
    borderColor: string;
    isMemoized: boolean;
    isRetrying: boolean;
    progress: number;
    elapsedBadge?: string;
  }

  const stepStates: Record<string, EntityRuntimeState> = {};

  entities.forEach((ent) => {
    stepStates[ent.id] = {
      status: 'idle',
      badgeText: 'PENDING',
      activeActionLabel: 'Awaiting execution trigger',
      color: theme.text_muted,
      bgColor: 'rgba(255, 255, 255, 0.03)',
      borderColor: theme.border_subtle,
      isMemoized: false,
      isRetrying: false,
      progress: 0,
      elapsedBadge: undefined,
    };
  });

  // Track Stage 1 completion time for connector illumination
  let stage1DoneSec: number | null = null;
  const firstEntId = entities[0]?.id;

  // Replay events up to localSec strictly based on resolved timestamp_sec
  events.forEach((ev) => {
    const triggerSec = ev.timestamp_sec != null
      ? Math.max(0, ev.timestamp_sec - sceneStart)
      : 0;

    if (ev.target === firstEntId && (ev.action === 'succeed' || ev.action === 'saved_state')) {
      if (stage1DoneSec == null || triggerSec < stage1DoneSec) {
        stage1DoneSec = triggerSec;
      }
    }

    if (localSec >= triggerSec) {
      const state = stepStates[ev.target];
      if (!state) return;

      if (ev.elapsed != null && ev.evidence_id) {
        state.elapsedBadge = `${ev.elapsed}`;
      }

      state.activeActionLabel = ev.label || ev.action.toUpperCase();

      switch (ev.action) {
        case 'start':
          state.status = 'running';
          state.badgeText = ev.label || 'EXECUTING';
          state.color = theme.syntax_function;
          state.bgColor = 'rgba(147, 197, 253, 0.10)';
          state.borderColor = 'rgba(147, 197, 253, 0.35)';
          state.progress = 60;
          break;
        case 'succeed':
        case 'saved_state':
          state.status = 'succeeded';
          state.badgeText = ev.label || 'MEMOIZED & SAVED';
          state.color = theme.status_success;
          state.bgColor = 'rgba(54, 169, 130, 0.12)';
          state.borderColor = 'rgba(54, 169, 130, 0.40)';
          state.isMemoized = true;
          state.progress = 100;
          break;
        case 'fail':
          state.status = 'failed';
          state.badgeText = ev.label || 'FAULT DETECTED';
          state.color = theme.status_error;
          state.bgColor = 'rgba(225, 90, 90, 0.12)';
          state.borderColor = 'rgba(225, 90, 90, 0.45)';
          state.progress = 45;
          break;
        case 'retry':
          state.status = 'retrying';
          state.badgeText = ev.label || 'RETRYING (ISOLATED)';
          state.color = theme.status_warning;
          state.bgColor = 'rgba(229, 167, 67, 0.12)';
          state.borderColor = 'rgba(229, 167, 67, 0.45)';
          state.isRetrying = true;
          state.progress = 75;
          break;
        case 'recover':
          state.status = 'recovered';
          state.badgeText = ev.label || 'RECOVERED & REUSED';
          state.color = theme.status_success;
          state.bgColor = 'rgba(54, 169, 130, 0.12)';
          state.borderColor = 'rgba(54, 169, 130, 0.45)';
          state.progress = 100;
          break;
      }
    }
  });

  const isStage1Complete = stage1DoneSec != null && localSec >= stage1DoneSec;

  const proof = scene.proof_card || scene.callout || (scene.takeaway ? { title: scene.takeaway } : null);
  const showProofColumn = isWidescreen && Boolean(proof);

  // Smooth entrance interpolations
  const titleOpacity = interpolate(localFrame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const titleY = interpolate(localFrame, [0, 8], [8, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stageOpacity = interpolate(localFrame, [2, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stageY = interpolate(localFrame, [2, 10], [10, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Flow animation for connector track
  const connectorPulseOffset = stage1DoneSec != null
    ? interpolate(localSec - stage1DoneSec, [0, 0.8], [0, 100], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  // Active events count
  const completedEventsCount = events.filter((ev) => {
    const triggerSec = ev.timestamp_sec != null
      ? Math.max(0, ev.timestamp_sec - sceneStart)
      : 0;
    return localSec >= triggerSec;
  }).length;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: isWidescreen ? '12px 32px' : '16px 12px',
        boxSizing: 'border-box',
        fontFamily: brand?.font_sans || 'Inter, system-ui, sans-serif',
      }}
    >
      {/* Level 1 & 2: Restrained Scene Heading & Contextual Pill */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          marginBottom: isWidescreen ? '16px' : '18px',
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '5px 14px',
            borderRadius: '999px',
            backgroundColor: 'rgba(147, 197, 253, 0.08)',
            border: '1px solid rgba(147, 197, 253, 0.22)',
            color: '#93C5FD',
            fontSize: '12px',
            fontWeight: 700,
            fontFamily: brand?.font_mono || 'monospace',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: '8px',
          }}
        >
          <LayersIcon size={13} color="#93C5FD" />
          WORKFLOW TRANSITION
        </div>

        <h1
          style={{
            fontSize: isWidescreen ? '30px' : '32px',
            fontWeight: 800,
            color: theme.text_primary,
            lineHeight: 1.25,
            letterSpacing: '-0.02em',
            margin: 0,
            maxWidth: isWidescreen ? '1320px' : '920px',
            textShadow: '0 4px 16px rgba(0, 0, 0, 0.85)',
          }}
        >
          {scene.title || 'Workflow Execution Trace'}
        </h1>
        {scene.subtitle && (
          <div
            style={{
              fontSize: '13px',
              color: theme.text_secondary,
              fontFamily: brand?.font_mono || 'monospace',
              marginTop: '6px',
            }}
          >
            {scene.subtitle}
          </div>
        )}
      </div>

      {/* Main Visual Stage */}
      <div
        style={{
          width: '100%',
          maxWidth: isWidescreen ? (showProofColumn ? '1580px' : '1440px') : '960px',
          display: 'flex',
          flexDirection: isWidescreen ? 'row' : 'column',
          alignItems: isWidescreen ? 'stretch' : 'center',
          justifyContent: 'center',
          gap: isWidescreen ? '28px' : '14px',
          opacity: stageOpacity,
          transform: `translateY(${stageY}px)`,
          boxSizing: 'border-box',
        }}
      >
        {/* Left / Center Workflow Pipeline Area */}
        <div
          style={{
            flex: showProofColumn ? '0 0 68%' : '1 1 auto',
            maxWidth: showProofColumn ? '1080px' : (isWidescreen ? '1440px' : '960px'),
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: isWidescreen ? '16px' : '12px',
            boxSizing: 'border-box',
          }}
        >
          {/* Execution Stage Sequence */}
          <div
            style={{
              display: 'flex',
              flexDirection: isWidescreen ? 'row' : 'column',
              alignItems: 'stretch',
              justifyContent: 'space-between',
              gap: isWidescreen ? '14px' : '10px',
              width: '100%',
              boxSizing: 'border-box',
            }}
          >
            {entities.map((ent, idx) => {
              const st = stepStates[ent.id];
              const isFirst = idx === 0;
              const hasNext = idx < entities.length - 1;

              // Render appropriate stage status icon
              let statusIcon = null;
              if (st.status === 'idle') {
                statusIcon = (
                  <div
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: theme.text_disabled,
                    }}
                  />
                );
              } else if (st.status === 'running') {
                statusIcon = (
                  <div
                    style={{
                      width: '14px',
                      height: '14px',
                      borderRadius: '50%',
                      border: `2px solid ${theme.syntax_function}`,
                      borderTopColor: 'transparent',
                    }}
                  />
                );
              } else if (st.isMemoized || st.status === 'succeeded') {
                statusIcon = <LockIcon size={16} color={theme.status_success} />;
              } else if (st.status === 'failed') {
                statusIcon = <AlertIcon size={16} color={theme.status_error} />;
              } else if (st.isRetrying || st.status === 'retrying') {
                statusIcon = <RetryIcon size={16} color={theme.status_warning} />;
              } else if (st.status === 'recovered') {
                statusIcon = <ShieldCheckIcon size={16} color={theme.status_success} />;
              }

              return (
                <React.Fragment key={ent.id}>
                  {/* Stage Node Box */}
                  <div
                    style={{
                      flex: isWidescreen ? '1 1 0' : 'none',
                      width: '100%',
                      backgroundColor: theme.surface_elevated,
                      borderRadius: '16px',
                      border: `1.5px solid ${st.borderColor}`,
                      padding: isWidescreen ? '20px 24px' : '16px 20px',
                      boxSizing: 'border-box',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: '12px',
                      boxShadow: `0 16px 36px -10px rgba(0, 0, 0, 0.75), 0 0 20px ${st.bgColor}`,
                      transition: 'border 0.25s ease, background-color 0.25s ease',
                    }}
                  >
                    {/* Header Row: Stage Index + Title + Status Pill */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '12px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {/* Step index badge with icon */}
                        <div
                          style={{
                            height: '28px',
                            padding: '0 10px',
                            borderRadius: '8px',
                            backgroundColor: st.bgColor,
                            border: `1px solid ${st.borderColor}`,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            fontSize: '12px',
                            fontWeight: 700,
                            color: st.color,
                            fontFamily: brand?.font_mono || 'monospace',
                          }}
                        >
                          {statusIcon}
                          <span>STAGE 0{idx + 1}</span>
                        </div>

                        <div>
                          <div
                            style={{
                              fontFamily: brand?.font_mono || 'monospace',
                              fontSize: isWidescreen ? '18px' : '19px',
                              fontWeight: 700,
                              color: theme.text_primary,
                              lineHeight: 1.3,
                            }}
                          >
                            {ent.label}
                          </div>
                          {ent.sub_label && (
                            <div
                              style={{
                                fontSize: '13px',
                                color: theme.text_secondary,
                                marginTop: '2px',
                              }}
                            >
                              {ent.sub_label}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Live State Pill */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {st.elapsedBadge && (
                          <div
                            style={{
                              padding: '4px 8px',
                              borderRadius: '6px',
                              backgroundColor: 'rgba(255, 255, 255, 0.06)',
                              color: theme.text_secondary,
                              fontSize: '11px',
                              fontWeight: 700,
                              fontFamily: brand?.font_mono || 'monospace',
                            }}
                          >
                            {st.elapsedBadge}
                          </div>
                        )}

                        <div
                          style={{
                            display: 'inline-flex',
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
                            letterSpacing: '0.04em',
                            textTransform: 'uppercase',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {st.isMemoized && <LockIcon size={13} color={theme.status_success} />}
                          {st.badgeText}
                        </div>
                      </div>
                    </div>

                    {/* Middle Row: Active Event Action Trace */}
                    <div
                      style={{
                        padding: '8px 12px',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(0, 0, 0, 0.35)',
                        border: `1px solid ${theme.border_subtle}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div
                        style={{
                          fontSize: '12px',
                          fontFamily: brand?.font_mono || 'monospace',
                          color: st.status === 'idle' ? theme.text_disabled : theme.text_secondary,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <span style={{ color: st.color }}>●</span>
                        <span>{st.activeActionLabel}</span>
                      </div>

                      <div
                        style={{
                          fontSize: '11px',
                          fontFamily: brand?.font_mono || 'monospace',
                          color: theme.text_muted,
                        }}
                      >
                        {st.status === 'idle'
                          ? 'STANDBY'
                          : st.status === 'running'
                          ? 'ACTIVE'
                          : st.status === 'failed'
                          ? 'FAULT'
                          : st.status === 'retrying'
                          ? 'RETRY'
                          : 'PERSISTED'}
                      </div>
                    </div>

                    {/* Bottom Progress Bar */}
                    <div
                      style={{
                        width: '100%',
                        height: '6px',
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        borderRadius: '999px',
                        overflow: 'hidden',
                        position: 'relative',
                      }}
                    >
                      <div
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: `${st.progress}%`,
                          height: '100%',
                          backgroundColor: st.color,
                          borderRadius: '999px',
                          boxShadow: `0 0 10px ${st.color}`,
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                  </div>

                  {/* Inter-stage Connector Conduit */}
                  {hasNext && (
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: isWidescreen ? 'column' : 'row',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: isWidescreen ? '0 4px' : '4px 0',
                        flexShrink: 0,
                      }}
                    >
                      <div
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '5px 14px',
                          borderRadius: '999px',
                          backgroundColor: isStage1Complete
                            ? 'rgba(54, 169, 130, 0.12)'
                            : 'rgba(255, 255, 255, 0.03)',
                          border: `1px solid ${
                            isStage1Complete
                              ? 'rgba(54, 169, 130, 0.35)'
                              : theme.border_subtle
                          }`,
                          color: isStage1Complete
                            ? theme.status_success
                            : theme.text_muted,
                          fontSize: '11px',
                          fontWeight: 700,
                          fontFamily: brand?.font_mono || 'monospace',
                          letterSpacing: '0.05em',
                          textTransform: 'uppercase',
                        }}
                      >
                        {isStage1Complete ? (
                          <>
                            <LockIcon size={12} color={theme.status_success} />
                            <span>CHECKPOINT PERSISTED</span>
                            {isWidescreen ? (
                              <ArrowRightIcon size={12} color={theme.status_success} />
                            ) : (
                              <ArrowDownIcon size={12} color={theme.status_success} />
                            )}
                          </>
                        ) : (
                          <>
                            <span>STATE PROPAGATION</span>
                            {isWidescreen ? (
                              <ArrowRightIcon size={12} color={theme.text_muted} />
                            ) : (
                              <ArrowDownIcon size={12} color={theme.text_muted} />
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Chronological Runtime Event Stream (The Execution Log) */}
          <div
            style={{
              backgroundColor: theme.surface,
              borderRadius: '16px',
              border: `1px solid ${theme.border_subtle}`,
              padding: isWidescreen ? '16px 20px' : '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              boxSizing: 'border-box',
            }}
          >
            {/* Log Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: `1px solid ${theme.border_subtle}`,
                paddingBottom: '8px',
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  color: theme.text_muted,
                  fontFamily: brand?.font_mono || 'monospace',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>EXECUTION EVENT LOG</span>
                <span style={{ color: theme.text_disabled }}>•</span>
                <span>CAUSAL TIMELINE</span>
              </div>

              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  color: completedEventsCount === events.length
                    ? theme.status_success
                    : theme.syntax_function,
                  fontFamily: brand?.font_mono || 'monospace',
                }}
              >
                {completedEventsCount} / {events.length} RESOLVED
              </div>
            </div>

            {/* Events Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: isWidescreen ? 'repeat(3, 1fr)' : 'repeat(2, 1fr)',
                gap: '8px',
              }}
            >
              {events.map((ev, i) => {
                const triggerSec = ev.timestamp_sec != null
                  ? Math.max(0, ev.timestamp_sec - sceneStart)
                  : 0;
                const isTriggered = localSec >= triggerSec;

                // Color code action
                let actionColor = theme.text_disabled;
                let bgTint = 'rgba(255, 255, 255, 0.02)';
                let borderTint = theme.border_subtle;

                if (isTriggered) {
                  if (ev.action === 'succeed' || ev.action === 'saved_state' || ev.action === 'recover') {
                    actionColor = theme.status_success;
                    bgTint = 'rgba(54, 169, 130, 0.08)';
                    borderTint = 'rgba(54, 169, 130, 0.25)';
                  } else if (ev.action === 'fail') {
                    actionColor = theme.status_error;
                    bgTint = 'rgba(225, 90, 90, 0.08)';
                    borderTint = 'rgba(225, 90, 90, 0.3)';
                  } else if (ev.action === 'retry') {
                    actionColor = theme.status_warning;
                    bgTint = 'rgba(229, 167, 67, 0.08)';
                    borderTint = 'rgba(229, 167, 67, 0.3)';
                  } else {
                    actionColor = theme.syntax_function;
                    bgTint = 'rgba(147, 197, 253, 0.06)';
                    borderTint = 'rgba(147, 197, 253, 0.25)';
                  }
                }

                return (
                  <div
                    key={i}
                    style={{
                      padding: '8px 10px',
                      borderRadius: '8px',
                      backgroundColor: bgTint,
                      border: `1px solid ${borderTint}`,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      opacity: isTriggered ? 1 : 0.45,
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div
                        style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          color: actionColor,
                          fontFamily: brand?.font_mono || 'monospace',
                          textTransform: 'uppercase',
                        }}
                      >
                        {ev.action}
                      </div>

                      <div
                        style={{
                          fontSize: '10px',
                          color: theme.text_disabled,
                          fontFamily: brand?.font_mono || 'monospace',
                        }}
                      >
                        +{triggerSec.toFixed(1)}s
                      </div>
                    </div>

                    <div
                      style={{
                        fontSize: '12px',
                        color: isTriggered ? theme.text_primary : theme.text_disabled,
                        fontWeight: isTriggered ? 600 : 400,
                        fontFamily: brand?.font_mono || 'monospace',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                      title={ev.label || ev.action}
                    >
                      {ev.label || ev.action}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column (Widescreen) or Supporting Proof Card (if provided) */}
        {proof && (
          <div
            style={{
              flex: isWidescreen ? '0 0 30%' : 'none',
              width: isWidescreen ? 'auto' : '100%',
              maxWidth: isWidescreen ? '440px' : '960px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                backgroundColor: theme.surface_elevated,
                borderRadius: '16px',
                border: `1.5px solid ${theme.border_subtle}`,
                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.8)',
                padding: '24px 24px',
              }}
            >
              {proof.tag && (
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(54, 169, 130, 0.1)',
                    border: '1px solid rgba(54, 169, 130, 0.3)',
                    color: theme.status_success,
                    fontSize: '11px',
                    fontWeight: 800,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    fontFamily: brand?.font_mono || 'monospace',
                    marginBottom: '12px',
                  }}
                >
                  <LockIcon size={12} color={theme.status_success} />
                  <span>{proof.tag}</span>
                </div>
              )}

              {proof.title && (
                <div
                  style={{
                    fontSize: isWidescreen ? '17px' : '18px',
                    fontWeight: 700,
                    color: theme.text_primary,
                    lineHeight: 1.35,
                    marginBottom: '8px',
                  }}
                >
                  {proof.title}
                </div>
              )}

              {proof.body && (
                <div
                  style={{
                    fontSize: '13px',
                    color: theme.text_secondary,
                    lineHeight: 1.5,
                  }}
                >
                  {proof.body}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowStateTransition;
