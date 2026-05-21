---
project: checkout-service
type: learning
description: Stripe webhooks arrive out of order — never trust event sequence
---
Stripe webhook events are not ordered. We saw a `payment_intent.succeeded`
land before the `payment_intent.created` it belonged to, which broke a state
machine that assumed creation came first. Fix: treat every webhook as a
state assertion, not a transition — upsert the payment to the state the event
describes, guarded by the event's `created` timestamp so a stale event never
overwrites a newer one.
