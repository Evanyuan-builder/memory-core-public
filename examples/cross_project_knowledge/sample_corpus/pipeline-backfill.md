---
project: data-pipeline
type: learning
description: backfills must run through the same code path as live ingestion
---
We used to have a separate "backfill script" that wrote straight to the
warehouse, bypassing the live pipeline. It drifted: the backfill applied an
older schema and silently produced rows the live path would have rejected.
Lesson — backfills replay through the exact same ingestion code path as live
traffic, just with historical timestamps. One code path, one set of
invariants. No shadow writers.
