# Inngest Retries and Error Handling

Inngest provides built-in automatic retries with configurable exponential backoff for all workflow steps.

## Automatic Step-Level Retries

When code inside `step.run()` throws an unhandled error:
- Inngest intercepts the failure and captures the error stack trace.
- The step enters a retry queue with exponential backoff and jitter.
- Only the specific step that threw the exception is scheduled for retry.
- Completed steps prior to the failure remain memoized and are never re-run upon step retry.

## Retry Guarantees and Idempotency

Step execution guarantees at-least-once delivery:
- Steps that complete successfully have their return values persisted permanently in workflow state.
- Upon retry, previous step results are loaded directly from cache.
- Side effects within a step must be designed to tolerate retries safely.

