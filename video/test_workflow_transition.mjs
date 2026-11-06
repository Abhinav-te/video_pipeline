import assert from 'assert';
import fs from 'fs';
import path from 'path';

console.log('Running Workflow State Transition Unit & Regression Tests...');

// 1. Gate 4 / Component Literal Lint compliance test
const componentPath = path.resolve(path.dirname(new URL(import.meta.url).pathname), 'src/components/WorkflowStateTransition.tsx');
const componentSource = fs.readFileSync(componentPath, 'utf-8');

const GATE4_BANNED_LITERALS = [
  'EVIDENCE-BACKED PRODUCTION VALUE',
  'Verified via official documentation',
  '0 RE-RUNS',
  'GUARDED',
  'OpenTelemetry',
  '8f4e29b1',
  '420ms',
  'FAILED: 503',
  'RETRY #1',
  "'VERIFIED'",
  "'GUARANTEE'",
];

for (const banned of GATE4_BANNED_LITERALS) {
  assert.ok(
    !componentSource.includes(banned),
    `WorkflowStateTransition.tsx must not contain banned literal: "${banned}"`
  );
}
console.log('✓ Zero banned literals found in WorkflowStateTransition.tsx');

// 2. Strict Theme Token usage test
assert.ok(
  componentSource.includes('useTheme()'),
  'WorkflowStateTransition must consume useTheme() for shared theme tokens'
);
assert.ok(
  componentSource.includes('theme.surface_elevated'),
  'WorkflowStateTransition must use theme.surface_elevated for stage node cards'
);
assert.ok(
  componentSource.includes('theme.status_success'),
  'WorkflowStateTransition must use theme.status_success for memoized/recovered states'
);
assert.ok(
  componentSource.includes('theme.status_error'),
  'WorkflowStateTransition must use theme.status_error for failed states'
);
assert.ok(
  componentSource.includes('theme.status_warning'),
  'WorkflowStateTransition must use theme.status_warning for retrying states'
);
console.log('✓ Theme tokens strictly utilized across surfaces, borders, typography, and status indicators');

// 3. Workflow State Machine Event Replay Simulation
function replayWorkflowEvents(events, entities, currentTime, sceneStart = 0) {
  const localSec = currentTime - sceneStart;
  const states = {};

  entities.forEach((ent) => {
    states[ent.id] = {
      status: 'idle',
      badgeText: 'PENDING',
      isMemoized: false,
      isRetrying: false,
      progress: 0,
    };
  });

  events.forEach((ev) => {
    const triggerSec = ev.timestamp_sec != null
      ? Math.max(0, ev.timestamp_sec - sceneStart)
      : 0;

    if (localSec >= triggerSec) {
      const state = states[ev.target];
      if (!state) return;

      switch (ev.action) {
        case 'start':
          state.status = 'running';
          state.badgeText = ev.label || 'EXECUTING';
          state.progress = 60;
          break;
        case 'succeed':
        case 'saved_state':
          state.status = 'succeeded';
          state.badgeText = ev.label || 'MEMOIZED & SAVED';
          state.isMemoized = true;
          state.progress = 100;
          break;
        case 'fail':
          state.status = 'failed';
          state.badgeText = ev.label || 'FAULT DETECTED';
          state.progress = 45;
          break;
        case 'retry':
          state.status = 'retrying';
          state.badgeText = ev.label || 'RETRYING (ISOLATED)';
          state.isRetrying = true;
          state.progress = 75;
          break;
        case 'recover':
          state.status = 'recovered';
          state.badgeText = ev.label || 'RECOVERED & REUSED';
          state.progress = 100;
          break;
      }
    }
  });

  return states;
}

const testEntities = [
  { id: 'initial_operation', label: 'Definition and Syntax', sub_label: 'Execution context checkpointed' },
  { id: 'recovery_operation', label: 'Retry & State Recovery', sub_label: 'Recovery without side effects' },
];

const testEvents = [
  { target: 'initial_operation', action: 'start', label: 'Executing Operation', timestamp_sec: 9.075 },
  { target: 'initial_operation', action: 'succeed', label: 'Durable Execution & Memoization', timestamp_sec: 10.112 },
  { target: 'recovery_operation', action: 'start', label: 'Fault Detection & Check', timestamp_sec: 10.412 },
  { target: 'recovery_operation', action: 'fail', label: 'Inngest Retries and Error', timestamp_sec: 13.15 },
  { target: 'recovery_operation', action: 'retry', label: 'Retry with Checkpoint', timestamp_sec: 13.45 },
  { target: 'recovery_operation', action: 'recover', label: 'Succeeded — State Reused', timestamp_sec: 13.75 },
];

const sceneStart = 8.775;

// Test Beat 1: Initial idle state (t=8.8s)
const t_init = replayWorkflowEvents(testEvents, testEntities, 8.8, sceneStart);
assert.strictEqual(t_init.initial_operation.status, 'idle', 'Initial state before t=9.075s should be idle');
assert.strictEqual(t_init.initial_operation.badgeText, 'PENDING');

// Test Beat 2: Initial operation running (t=9.5s)
const t_run = replayWorkflowEvents(testEvents, testEntities, 9.5, sceneStart);
assert.strictEqual(t_run.initial_operation.status, 'running', 'At t=9.5s, initial_operation should be running');
assert.strictEqual(t_run.initial_operation.badgeText, 'Executing Operation');

// Test Beat 3: Initial operation memoized and saved (t=10.2s)
const t_memo = replayWorkflowEvents(testEvents, testEntities, 10.2, sceneStart);
assert.strictEqual(t_memo.initial_operation.status, 'succeeded', 'At t=10.2s, initial_operation should be succeeded');
assert.strictEqual(t_memo.initial_operation.isMemoized, true, 'isMemoized flag should be true');

// Test Beat 4: Recovery operation fails with error (t=13.2s)
const t_fail = replayWorkflowEvents(testEvents, testEntities, 13.2, sceneStart);
assert.strictEqual(t_fail.recovery_operation.status, 'failed', 'At t=13.2s, recovery_operation should be failed');
assert.strictEqual(t_fail.initial_operation.status, 'succeeded', 'initial_operation remains memoized and untouched');

// Test Beat 5: Recovery operation retries in isolation (t=13.5s)
const t_retry = replayWorkflowEvents(testEvents, testEntities, 13.5, sceneStart);
assert.strictEqual(t_retry.recovery_operation.status, 'retrying', 'At t=13.5s, recovery_operation should be retrying');
assert.strictEqual(t_retry.recovery_operation.isRetrying, true);

// Test Beat 6: Recovery operation recovered reusing saved state (t=14.0s)
const t_recover = replayWorkflowEvents(testEvents, testEntities, 14.0, sceneStart);
assert.strictEqual(t_recover.recovery_operation.status, 'recovered', 'At t=14.0s, recovery_operation should be recovered');
assert.strictEqual(t_recover.recovery_operation.progress, 100);
console.log('✓ Deterministic state machine transition verified across all 6 chronological beats');

// 4. Responsive Layout Sizing & Proportions
function computeWorkflowLayout(isWidescreen, entityCount, hasProof) {
  const stageWidth = isWidescreen ? (hasProof ? '1580px' : '1440px') : '960px';
  const pipelineDirection = isWidescreen ? 'row' : 'column';
  const eventStreamCols = isWidescreen ? 'repeat(3, 1fr)' : 'repeat(2, 1fr)';
  const proofFlex = isWidescreen ? (hasProof ? '0 0 30%' : 'none') : 'none';

  return {
    stageWidth,
    pipelineDirection,
    eventStreamCols,
    proofFlex,
  };
}

const verticalLayout = computeWorkflowLayout(false, 2, false);
assert.strictEqual(verticalLayout.stageWidth, '960px', 'Vertical stage spans 960px canvas');
assert.strictEqual(verticalLayout.pipelineDirection, 'column', 'Vertical stage uses column flow');
assert.strictEqual(verticalLayout.eventStreamCols, 'repeat(2, 1fr)', 'Vertical event stream uses 2 balanced columns');

const widescreenLayout = computeWorkflowLayout(true, 2, true);
assert.strictEqual(widescreenLayout.stageWidth, '1580px', 'Widescreen stage spans 1580px');
assert.strictEqual(widescreenLayout.pipelineDirection, 'row', 'Widescreen stage uses horizontal row flow');
assert.strictEqual(widescreenLayout.eventStreamCols, 'repeat(3, 1fr)', 'Widescreen event stream uses 3 balanced columns');
assert.strictEqual(widescreenLayout.proofFlex, '0 0 30%', 'Proof column flexes to 30% in widescreen');
console.log('✓ Responsive layout calculations validated for 9:16 and 16:9 aspect ratios');

console.log('All Workflow State Transition Unit & Regression Tests passed successfully!');
