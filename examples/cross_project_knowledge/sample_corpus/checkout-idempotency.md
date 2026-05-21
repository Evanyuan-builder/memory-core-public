---
project: checkout-service
type: decision
description: why payment capture is keyed on a client idempotency-key
---
The payment-capture endpoint is idempotent: the client sends an
`Idempotency-Key` header, and we persist the first response under that key for
24h. A retried POST with the same key replays the stored response instead of
charging the card twice. We chose client-supplied keys over server-derived
hashes because the same logical charge can arrive with different request bodies
(amount rounding, currency normalisation) and we still want them collapsed.
