"""tests/test_code_sanitize_and_slice.py

Behavioral Test Suite for Code Sanitization, Delimiter Balancing,
Zero 12-Line Cap (Complete Blocks), and Dynamic Highlight Derivation.
"""

import pytest
from engine.ingestion.code_sanitizer import (
    sanitize_code,
    is_delimiter_balanced,
    derive_highlight_lines,
)


INNGEST_RAW_DOC_SNIPPET = """```typescript
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
```"""


STRIPE_RAW_DOC_SNIPPET = """```typescript
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function authorizePayment(order: { id: string; amount: number }) {
  const paymentIntent = await stripe.paymentIntents.create(
    {
      amount: 2000,
      currency: 'usd',
      payment_method_types: ['card'],
    },
    {
      idempotencyKey: order.id,
    }
  );
  return paymentIntent;
}
```"""


def test_sanitize_code_strips_fences_and_line_one_clean():
    """Verify markdown fences are stripped and Line 1 on screen is never ```typescript."""
    sanitized = sanitize_code(INNGEST_RAW_DOC_SNIPPET)
    lines = sanitized.splitlines()

    assert not lines[0].strip().startswith("```")
    assert not sanitized.endswith("```")
    assert "```" not in sanitized
    assert lines[0].startswith("export const processOrder")


def test_sanitize_code_normalizes_tabs_and_dedents():
    """Verify tabs are normalized to 2 spaces and leading indentation is dedented."""
    raw = "\t\tconst foo = 42;\n\t\tconst bar = foo + 1;"
    sanitized = sanitize_code(raw)

    assert "\t" not in sanitized
    assert sanitized.startswith("const foo = 42;")
    assert "  const bar = foo + 1;" in sanitized or "const bar = foo + 1;" in sanitized


def test_no_12_line_cap_preserves_syntactically_balanced_block():
    """Verify 12-line cap is removed so processOrder includes closing } and );."""
    sanitized = sanitize_code(INNGEST_RAW_DOC_SNIPPET)
    lines = sanitized.splitlines()

    # The full processOrder function is 13 lines (greater than the previous 12-line truncation)
    assert len(lines) == 13
    assert lines[-2].strip() == "}"
    assert lines[-1].strip() == ");"
    assert is_delimiter_balanced(sanitized)


def test_is_delimiter_balanced_handles_strings_and_comments():
    """Verify delimiter balancing ignores brackets inside strings and comments."""
    valid_code = 'const s = "{[( unclosed inside string"; // unclosed in comment {(\nreturn { ok: true };'
    assert is_delimiter_balanced(valid_code)

    unbalanced_code = 'function bad() { return (1 + 2; }'
    assert not is_delimiter_balanced(unbalanced_code)

    missing_brace = 'export const fn = () => {\n  console.log("missing closing");\n'
    assert not is_delimiter_balanced(missing_brace)


def test_derive_highlight_lines_for_inngest_step_run():
    """Verify highlight lines are derived dynamically from 'step.run(' focus token."""
    sanitized = sanitize_code(INNGEST_RAW_DOC_SNIPPET)
    highlights = derive_highlight_lines(sanitized, focus_token="step.run(")

    # Lines 5-7 and 8-10 are the step.run calls in the 14-line snippet
    assert 5 in highlights
    assert 6 in highlights
    assert 7 in highlights
    assert len(highlights) >= 3


def test_derive_highlight_lines_for_stripe_idempotency():
    """Verify highlight lines are derived dynamically from 'idempotencyKey' focus token."""
    sanitized = sanitize_code(STRIPE_RAW_DOC_SNIPPET)
    highlights = derive_highlight_lines(sanitized, focus_token="idempotencyKey")

    lines = sanitized.splitlines()
    matching_line_idx = next(i + 1 for i, l in enumerate(lines) if "idempotencyKey" in l)

    assert matching_line_idx in highlights
