# Stripe API: Idempotent Requests

The Stripe API supports idempotency for safely retrying requests without accidentally performing the same operation twice. This is particularly useful when an API call is disrupted in transit and you don't receive a response.

## Core Concept
Idempotent requests prevent accidentally performing the same mutating operation twice when retrying after a connection drop or timeout. If a network connection is dropped during a payment authorization, you can safely retry the request with the same idempotency key to guarantee that only a single charge is created.

## Developer Action
To perform an idempotent request, pass a unique `Idempotency-Key` HTTP header (UUID v4 or deterministic cart or order ID) on `POST /v1/payment_intents` requests, or provide the `idempotencyKey` option in the official SDK.

```typescript
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
```

Or pass the raw HTTP header:
```http
POST /v1/payment_intents HTTP/1.1
Host: api.stripe.com
Idempotency-Key: 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
Content-Type: application/x-www-form-urlencoded

amount=2000&currency=usd
```

## Runtime Behavior & Response Caching
If Stripe receives a retry with the same `Idempotency-Key`, it does not create a duplicate charge; it returns the cached response from the original completed request. The initial operation saves its response in Stripe's idempotency store, and all subsequent requests with that key reuse the saved response payload.

```json
{
  "id": "pi_3MtwBwLkdIwHu7ix28a3tqPa",
  "object": "payment_intent",
  "amount": 2000,
  "currency": "usd",
  "status": "succeeded"
}
```

## Important Limitations & Boundary Constraints
> [!WARNING]
> Sending the same `Idempotency-Key` with different request parameters returns a 400 parameter mismatch error. Keys are tied to the exact request payload and parameters.

> [!NOTE]
> The Stripe API retains idempotency keys for at least 24 hours. Keys are only needed on POST requests because GET and DELETE methods are idempotent by definition.

