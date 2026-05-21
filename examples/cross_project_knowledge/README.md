# Reference app: cross-project engineering memory

> The other example in this repo (`multi_agent_dev_team/`) shows Memory Core as
> the shared substrate for a **team of agents**. This one shows the other half
> of the story: Memory Core as **one developer's long-lived engineering brain**
> — the decisions and hard-won lessons from every project you've worked on,
> recallable by meaning, across machines and across months.

You write notes as you work — why you made a call, what bit you, what not to do
again. Scattered across repos and machines they rot. Pointed at Memory Core they
become a memory you can *ask*: a question asked while working on one project
surfaces the relevant decision you made on another.

## The real story behind this demo

This isn't a toy pattern we invented for a README. The author runs exactly this
against a real ~88-file engineering-memory corpus, kept in markdown and synced
across two machines (a desktop and a laptop). That corpus is private, so the
`sample_corpus/` here is a small synthetic stand-in — six notes across three
projects — so you can run the demo end-to-end without anyone's private notes.
The code is the same code; only the corpus is swapped.

## Run it

```bash
# 1. Start a Memory Core API (from the engine repo): `make api`  → 127.0.0.1:8001
#    or point MEMORY_CORE_URL at your own deployment.
cp .env.example .env        # optional; defaults to 127.0.0.1:8001

# 2. Ingest the corpus — one memory per note, tagged by project.
python ingest.py
#   → ingested 6 notes into 'refapp.knowledge' across 3 projects:
#     checkout-service, data-pipeline, infra

# 3. Ask across every project at once …
python ask.py "how do we handle retries and avoid double-processing?"

# 4. … or scope the same question to one project.
python ask.py "how do we handle retries and avoid double-processing?" data-pipeline
```

## What you actually see

Ask about retries with no project scope — and Memory Core surfaces the relevant
decision from **two** projects, because the idea (push idempotency to the sink)
was written down once in the pipeline and once in checkout:

```
Q: how do we handle retries and avoid double-processing?   (all projects)

1. [data-pipeline]   The ingestion pipeline is at-least-once: every stage can retry…
2. [checkout-service] The payment-capture endpoint is idempotent: the client sends an…
3. [infra]            We never rebuild between environments. CI builds one image…
```

Add a project and the same query narrows to that codebase:

```
Q: how do we handle retries and avoid double-processing?   (project=data-pipeline)

1. [data-pipeline]   The ingestion pipeline is at-least-once: every stage can retry…
2. [data-pipeline]   We used to have a separate "backfill script" that wrote straight…
```

Different questions land on the right note regardless of which project wrote it:

```
Q: how do we keep staging and prod from drifting?
1. [infra]            We never rebuild between environments. CI builds one image…

Q: what do we do when a secret leaks?
1. [infra]            Someone pasted a cloud token into a chat log. Removing it…
```

(`ask.py` also prints a relevance score per hit — the cross-encoder logit,
higher = more relevant. The ranking is the point; the raw number is just there
to show it's real retrieval, not keyword grep.)

## What this exercises in the engine

| Capability | Where it shows up here |
|---|---|
| Hybrid retrieval (BM25 + dense + RRF) | "retries" matches by meaning, not the literal word |
| One namespace, project-tagged | cross-project recall by default; `tag_filter` to scope |
| Deterministic ranking | same corpus → same order, every run (verified property) |
| Structured markdown ingest | frontmatter `project:` / `type:` become tags |

It's a deliberately small slice. The same `MemoryClient` calls — `store_batch`
and `search` — are what a coding agent makes when it writes a decision to memory
mid-task and recalls it three sessions later.

## Files

| File | What it is |
|---|---|
| `ingest.py` | Walk a markdown dir → one memory per note, tagged by project |
| `ask.py` | Semantic recall, optionally scoped to a project tag |
| `sample_corpus/` | Six synthetic notes across three projects (stand-in for a private corpus) |

## Links

- Engine + benchmarks: see the [repo root README](../../README.md) — LoCoMo / LongMemEval scores, reproducible from the public [memory-core-eval](https://github.com/Evanyuan-builder/memory-core-eval) harness.
- Point `ingest.py` at your own notes directory: `python ingest.py /path/to/your/notes`.
