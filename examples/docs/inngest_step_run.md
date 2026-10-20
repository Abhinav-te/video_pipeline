# Inngest step.run()

`step.run()` is a core durable execution primitive in Inngest that enables developers to break workflows into isolated, retried, and memoized steps.

## Definition and Syntax

To execute synchronous or asynchronous operations durably, wrap your operation in `await step.run("step-id", async () => { ... })`.

```typescript
export const processOrder = inngest.createFunction(
  { id: "process-order" },
  { event: "order.created" },
  async ({ event, step }) => {
    const billing = await step.run("fetch-billing-data", async () => {
      return await getBillingAccount(event.data.customerId);
    });
    const receipt = await step.run("charge-customer", async () => {
      return await paymentGateway.charge({ customerId: billing.id, amount: event.data.amount });
    });
    return { status: "completed", receiptId: receipt.id };
  }
);
```

## Durable Execution & Memoization Behavior

When a function executes:
1. Each step executes in its own isolated execution context.
2. When `step.run()` completes successfully, its return value is serialized and saved in durable workflow state.
3. If a subsequent step throws an error or fails, the function execution pauses and schedules an automatic retry.
4. On retry, Inngest does not re-execute previously completed steps. Instead, it reuses the memoized return value from workflow state and resumes execution at the failed step.

## Failure Behavior and Step Isolation

If step 2 (`"charge-customer"`) encounters a transient error such as a network timeout or HTTP 503 from an external API:
- Inngest retries only the failed step (`"charge-customer"`).
- Step 1 (`"fetch-billing-data"`) is not re-executed, preventing redundant external API calls and database loads.
- This guarantees reliable recovery while minimizing duplicate operations across distributed services.

## Important Limitations

> [!WARNING]
> External side effects inside a retried step must be idempotent or handled safely.
> Because Inngest retries the entire callback inside a failed `step.run()` until it succeeds or exhausts retries, non-idempotent side effects inside an uncommitted step can execute more than once if failure occurs mid-step.

