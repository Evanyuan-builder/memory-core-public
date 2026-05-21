---
project: data-pipeline
type: decision
description: at-least-once delivery + idempotent sinks instead of exactly-once
---
The ingestion pipeline is at-least-once: every stage can retry, so a record
can be delivered more than once. Rather than chase exactly-once (expensive,
fragile), we made every sink idempotent — each record carries a deterministic
`event_id` and sinks upsert on it. Retries become free. Same principle the
checkout service uses for payment capture: push idempotency to the sink, don't
try to make the transport perfect.
