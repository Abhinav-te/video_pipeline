# Resend: Webhook Signature Verification

Resend uses cryptographic HMAC webhook signatures to verify that incoming webhook events are genuinely dispatched by Resend and haven't been tampered with or replayed in transit.

## Core Concept
Verifying webhook signatures prevents man-in-the-middle attacks and replay attempts by malicious actors. Every incoming webhook payload includes a signature header computed using your endpoint's shared webhook secret.

## Developer Action
To verify a webhook event in Node.js, pass the raw request payload, the `svix-signature` header, and your signing secret to the official SDK or Svix verification helper.

```typescript
import { Webhook } from 'svix';

export async function handleWebhook(payload: string, headers: Record<string, string>) {
  const wh = new Webhook(process.env.RESEND_WEBHOOK_SECRET!);
  const event = wh.verify(payload, {
    'svix-id': headers['svix-id'],
    'svix-timestamp': headers['svix-timestamp'],
    'svix-signature': headers['svix-signature'],
  });
  return event;
}
```

## Runtime Behavior & Replay Protection
During verification, the helper checks both the cryptographic HMAC-SHA256 signature and the timestamp header. If the timestamp differs from the current time by more than 5 minutes, the request is rejected immediately as an expired replay attack.

```json
{
  "type": "email.delivered",
  "created_at": "2026-10-21T18:00:00.000Z",
  "data": {
    "email_id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794",
    "to": ["user@example.com"]
  }
}
```

## Important Limitations & Boundary Constraints
> [!WARNING]
> You must verify signatures using the raw unparsed request body string. Parsing JSON before verification modifies character serialization and causes signature verification to fail.

> [!NOTE]
> Webhook timestamps are rejected if older than 300 seconds to eliminate replay windows.

