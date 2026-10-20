import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { LayersIcon, SparklesIcon, CheckIcon, WarningIcon, LightningIcon } from './SvgIcons';

export interface WorkflowEntity {
  id: string;
  label: string;
  sub_label?: string;
  status?: string;
}

export interface WorkflowEvent {
  target: string;
  action: 'start' | 'succeed' | 'saved_state' | 'fail' | 'retry' | 'recover';
  label?: string;
  time_offset?: number;
}

export interface WorkflowStateTransitionProps {
  scene: {
    title?: string;
    entities?: WorkflowEntity[];
    events?: WorkflowEvent[];
    start_time?: number;
    end_time?: number;
    badge?: any;
    emphasis_word?: string;
  };
  words?: any[];
  sceneStartFrame?: number;
  nextSceneStartTime?: number | null;
}

/**
 * Universal WorkflowStateTransition Scene Primitive.
 * Animates developer state machine transitions with zero company hardcoding.
 */
export const WorkflowStateTransition: React.FC<WorkflowStateTransitionProps> = ({
  scene,
  sceneStartFrame = 0,
  nextSceneStartTime = null,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sceneStart = scene?.start_time || 0;
  const sceneEnd = nextSceneStartTime || scene?.end_time || (sceneStart + 5);
  const sceneDurationFrames = Math.max(90, Math.round((sceneEnd - sceneStart) * fps));
  const localFrame = Math.max(0, frame - sceneStartFrame);

  // Default entities if not provided
  const rawEntities: WorkflowEntity[] = scene?.entities && scene.entities.length > 0
    ? scene.entities
    : [
        { id: 'op_1', label: "Initial Operation", sub_label: "Operation 1: Primary Execution" },
        { id: 'op_2', label: "Subsequent Operation", sub_label: "Operation 2: Downstream Verification" },
      ];

  // Default event sequence demonstrating memoized step recovery
  const defaultEvents: WorkflowEvent[] = [
    { target: 'step_1', action: 'start', label: 'Executing Step 1' },
    { target: 'step_1', action: 'succeed', label: 'RESULT SAVED / MEMOIZED' },
    { target: 'step_2', action: 'start', label: 'Executing Step 2' },
    { target: 'step_2', action: 'fail', label: 'FAILED: 503' },
    { target: 'step_2', action: 'retry', label: 'RETRY #1 — Reusing Step 1 State' },
    { target: 'step_2', action: 'recover', label: 'RECOVERED' },
  ];

  const events: WorkflowEvent[] = scene?.events && scene.events.length > 0 ? scene.events : defaultEvents;
  const numEvents = events.length;

  // Compute active state for each entity based on elapsed localFrame
  const entityStates: Record<string, {
    status: string;
    badgeText: string;
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
    isPulsing: boolean;
    isMemoized: boolean;
  }> = {};

  // Initialize
  rawEntities.forEach((ent) => {
    entityStates[ent.id] = {
      status: 'idle',
      badgeText: 'QUEUED',
      label: 'Waiting in workflow queue',
      color: '#8b949e',
      bgColor: 'rgba(22, 27, 34, 0.8)',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      isPulsing: false,
      isMemoized: false,
    };
  });

  // Replay events up to localFrame
  events.forEach((ev, idx) => {
    const triggerFrame = Math.floor((idx / numEvents) * sceneDurationFrames);
    if (localFrame >= triggerFrame) {
      const targetState = entityStates[ev.target];
      if (!targetState) return;

      switch (ev.action) {
        case 'start':
          targetState.status = 'running';
          targetState.badgeText = 'EXECUTING';
          targetState.label = ev.label || 'Step execution in progress...';
          targetState.color = '#58a6ff';
          targetState.bgColor = 'rgba(88, 166, 255, 0.1)';
          targetState.borderColor = 'rgba(88, 166, 255, 0.45)';
          targetState.isPulsing = false;
          break;
        case 'succeed':
        case 'saved_state':
          targetState.status = 'succeeded';
          targetState.badgeText = 'RESULT SAVED / MEMOIZED';
          targetState.label = ev.label || 'Output saved in workflow state';
          targetState.color = '#3fb950';
          targetState.bgColor = 'rgba(63, 185, 80, 0.12)';
          targetState.borderColor = 'rgba(63, 185, 80, 0.5)';
          targetState.isPulsing = false;
          targetState.isMemoized = true;
          break;
        case 'fail':
          targetState.status = 'failed';
          targetState.badgeText = 'FAILED: 503';
          targetState.label = ev.label || 'Transient error: HTTP 503 timeout';
          targetState.color = '#f85149';
          targetState.bgColor = 'rgba(248, 81, 73, 0.12)';
          targetState.borderColor = 'rgba(248, 81, 73, 0.55)';
          targetState.isPulsing = false;
          break;
        case 'retry':
          targetState.status = 'retrying';
          targetState.badgeText = 'RETRY #1 — Reusing Step 1 State';
          targetState.label = ev.label || 'Retrying step without re-executing step 1';
          targetState.color = '#d29922';
          targetState.bgColor = 'rgba(210, 153, 34, 0.15)';
          targetState.borderColor = 'rgba(210, 153, 34, 0.65)';
          targetState.isPulsing = true;
          break;
        case 'recover':
          targetState.status = 'recovered';
          targetState.badgeText = 'RECOVERED';
          targetState.label = ev.label || 'Step executed successfully';
          targetState.color = '#3fb950';
          targetState.bgColor = 'rgba(63, 185, 80, 0.16)';
          targetState.borderColor = 'rgba(63, 185, 80, 0.6)';
          targetState.isPulsing = false;
          break;
      }
    }
  });

  // Pulse animation for retry
  const pulseOpacity = interpolate(
    Math.sin((localFrame / 10) * Math.PI),
    [-1, 1],
    [0.4, 0.95]
  );

  return (
    <div
      style={{
        backgroundColor: '#0d1117',
        borderRadius: '28px',
        border: '1.5px solid rgba(88, 166, 255, 0.3)',
        boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 32px rgba(88, 166, 255, 0.1)',
        width: '960px',
        height: 'fit-content',
        maxHeight: '1380px',
        overflow: 'hidden',
        boxSizing: 'border-box',
        padding: '36px 36px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        gap: '24px',
        margin: 'auto 0',
      }}
    >
      {/* 1. EDITORIAL HEADER */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
          paddingBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <LayersIcon size={30} color="#58a6ff" />
          <span
            style={{
              fontSize: '28px',
              fontWeight: 800,
              color: '#f0f6fc',
              fontFamily: "'Inter', sans-serif",
              letterSpacing: '-0.5px',
            }}
          >
            {scene.title || 'Durable State Machine'}
          </span>
        </div>
        <SceneBadge badge={scene.badge} defaultText="DURABLE FLOW" />
      </div>

      {/* 2. SEQUENTIAL WORKFLOW ENTITIES */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px',
        }}
      >
        {rawEntities.map((entity, index) => {
          const state = entityStates[entity.id] || {
            badgeText: 'PENDING',
            color: '#8b949e',
            bgColor: '#161b22',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            label: '',
            isPulsing: false,
            isMemoized: false,
          };

          const cardBorder = state.isPulsing
            ? `2px solid rgba(210, 153, 34, ${pulseOpacity})`
            : `1.5px solid ${state.borderColor}`;

          const cardShadow = state.isPulsing
            ? `0 0 24px rgba(210, 153, 34, ${pulseOpacity * 0.5})`
            : '0 8px 24px rgba(0, 0, 0, 0.5)';

          return (
            <React.Fragment key={entity.id}>
              {/* Connector Arrow between steps */}
              {index > 0 && (() => {
                const prevEntity = rawEntities[index - 1];
                const prevMemoized = prevEntity ? entityStates[prevEntity.id]?.isMemoized : false;
                return (
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '4px',
                      margin: '-4px 0',
                    }}
                  >
                    <svg width="24" height="38" viewBox="0 0 24 38" fill="none">
                      <line
                        x1="12"
                        y1="0"
                        x2="12"
                        y2="26"
                        stroke={prevMemoized ? '#3fb950' : '#58a6ff'}
                        strokeWidth="3.5"
                        strokeDasharray={prevMemoized ? 'none' : '4 3'}
                      />
                      <polygon
                        points="6,24 12,36 18,24"
                        fill={prevMemoized ? '#3fb950' : '#58a6ff'}
                      />
                    </svg>
                    {prevMemoized && (
                      <span
                        style={{
                          fontSize: '13px',
                          fontWeight: 700,
                          color: '#3fb950',
                          fontFamily: 'monospace',
                          letterSpacing: '1px',
                          backgroundColor: 'rgba(63, 185, 80, 0.1)',
                          padding: '2px 10px',
                          borderRadius: '10px',
                          border: '1px solid rgba(63, 185, 80, 0.3)',
                        }}
                      >
                        CACHED STATE REUSED
                      </span>
                    )}
                  </div>
                );
              })()}

              {/* Entity Step Card */}
              <div
                style={{
                  width: '100%',
                  backgroundColor: state.bgColor,
                  border: cardBorder,
                  borderRadius: '20px',
                  padding: '22px 26px',
                  boxShadow: cardShadow,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  boxSizing: 'border-box',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span
                      style={{
                        fontFamily: 'monospace',
                        fontSize: '22px',
                        fontWeight: 800,
                        color: '#f0f6fc',
                      }}
                    >
                      {entity.label}
                    </span>
                  </div>

                  {/* Dynamic Status Pill */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      backgroundColor: 'rgba(0, 0, 0, 0.45)',
                      border: `1.5px solid ${state.color}`,
                      borderRadius: '100px',
                      padding: '6px 14px',
                    }}
                  >
                    {state.status === 'succeeded' || state.status === 'recovered' ? (
                      <CheckIcon size={16} color={state.color} />
                    ) : state.status === 'failed' ? (
                      <WarningIcon size={16} color={state.color} />
                    ) : (
                      <LightningIcon size={16} color={state.color} />
                    )}
                    <span
                      style={{
                        fontSize: '14px',
                        fontWeight: 800,
                        color: state.color,
                        fontFamily: 'monospace',
                        letterSpacing: '0.8px',
                      }}
                    >
                      {state.badgeText}
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    fontSize: '16px',
                    color: '#c9d1d9',
                    fontFamily: "'Inter', sans-serif",
                    lineHeight: 1.4,
                  }}
                >
                  {state.label}
                </div>

                {state.isMemoized && (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      backgroundColor: 'rgba(63, 185, 80, 0.15)',
                      border: '1px solid rgba(63, 185, 80, 0.35)',
                      borderRadius: '10px',
                      padding: '8px 14px',
                      fontSize: '14px',
                      color: '#86efac',
                      fontFamily: 'monospace',
                    }}
                  >
                    <SparklesIcon size={16} color="#3fb950" />
                    <span>{(entity as any).memoized_detail || 'Cached Result: Output serialized & saved • 0 redundant operations'}</span>
                  </div>
                )}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default WorkflowStateTransition;

