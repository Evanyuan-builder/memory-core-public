# Lablab.ai submission · Milan AI Week (AI Agent Olympics)

Application ID: **#1311**  ·  Submitter: Evan / longtide1230@gmail.com  ·  Deadline: **2026-05-19 23:00 CST**

This file contains the exact text to paste into each lablab submission field.

---

## 1 · Project Title

```
Memory Core — The Memory Layer for Multi-Agent Dev Teams
```

(67 chars; lablab title caps vary, keep alternate ready: `Memory Core: Role-Aware Memory for Agent Teams`.)

---

## 2 · Short Description (one-liner)

```
An MIT-licensed role-aware memory layer that lets planner, coder, and reviewer agents share context through namespaces — not prompt-stuffing. SOTA: 99.4 R@10 on LongMemEval-S.
```

(195 chars, under any reasonable 240 cap.)

---

## 3 · Tags

```
memory, multi-agent, agent-teams, llm, retrieval, namespace, role-aware, mcp, featherless, qwen, mit, open-source
```

---

## 4 · Long Description (paste as markdown)

### The problem we ship a fix for

Multi-agent dev teams have a coordination problem disguised as a memory
problem. When a planner, coder, and reviewer collaborate on a single task
today, they pass context through **prompts** — concatenating each other's
outputs into the next agent's system message, paying for every token
re-injected, and losing the whole thread on the next session reset.

Most framework benchmarks (LangGraph, CrewAI, AutoGen) assume the model
is the substrate. We disagree: **the memory layer is**. Memory Core
makes context a first-class shared resource — every agent reads exactly
the role-scoped slice it needs, nothing else.

### What we built for Milan AI Week

A three-agent dev team — `planner`, `coder`, `reviewer` — collaborating
on a real coding task (*"add a dark-mode toggle to a Next.js settings
page"*) through Memory Core's namespaces.

- The **planner** (`mimo-v2.5`) reads the project files from a
  `bootstrap` namespace and writes a multi-step plan into the `planner`
  namespace.
- The **coder** (`Qwen2.5-Coder-32B-Instruct` via Featherless) reads
  `planner` + `bootstrap`, emits `[FILE: path]…[/FILE]` blocks, and
  stores each one as a separate artifact in the `coder` namespace.
- The **reviewer** (`mimo-v2.5`) reads `planner` + `coder` and writes a
  critique into the `reviewer` namespace.

Each agent's prompt mentions only its own task — none of them sees the
other agents' raw outputs through prompt concatenation. The shared
substrate is the memory layer.

The web UI animates the data flow in real time: every memory write shows
`◆ ns writes type=X · ◇ reads namespace+…`, and coder artifacts render
as discrete file cards instead of one opaque blob.

**Live:** https://memory-core.chinasourcingbridge.com

### Why this fits the Featherless track exactly

The Featherless brief asks for *domain-specialized + async-first +
permissively-licensed + production-shaped* — those four points are
literally Memory Core's design pillars:

- **Domain-specialized**: the demo targets software dev teams. The
  namespace scoping primitives encode roles for an org, not a chat user.
- **Async-first**: agents communicate through namespaces, not chat turns.
  No agent is blocked on another agent's prompt being read.
- **Permissive**: MIT core + Apache-2.0 evaluation harness. Real open
  source, not source-available.
- **Production-shaped**: REST API, Python SDK, 10+ pluggable backends,
  CI 7/7 green, 369 unit + 99 e2e tests on v1.0.0.

The coder calls `Qwen2.5-Coder-32B-Instruct` from Featherless's open
catalog, satisfying the track's "use models from the catalog" requirement.

We are also submitting to **Collaborative Systems** (this *is* a
collaborative system) and **Agentic Workflows** (planner → coder →
reviewer with persistent state is a workflow).

### Benchmarks — not a toy

Memory Core's published numbers on two long-memory benchmarks (full
methodology, ablations and reproduction in the public
[memory-core-eval](https://github.com/Evanyuan-builder/memory-core-eval)
harness, Apache-2.0):

| Benchmark | Memory Core R@10 | Published anchor R@10 |
|---|---:|---:|
| LongMemEval-S (n=500) | **99.4** | 97.9 (Hybrid-RRF) |
| LoCoMo (n=500) | **88.8** | 85.0 (Hybrid-RRF) |

Cross-restart determinism is a verified property at the same revision —
zero question flips across runs.

### Tech stack

- **Backend**: FastAPI + LanceDB (vector + full-text in one store) +
  optional MCP server adapter.
- **Retrieval**: hybrid dense + sparse with RRF fusion and a
  cross-encoder rerank head; the `role_scope` filter is pushed down
  into LanceDB SQL (`array_has_any`) so it runs *before* RRF samples
  candidates — no recall depth lost.
- **Demo**: Python + FastAPI + Server-Sent Events + a single-file
  Tailwind UI.
- **LLMs**: heterogeneous on purpose — coder is `Qwen2.5-Coder-32B` on
  Featherless; planner and reviewer are Xiaomi's `mimo-v2.5`. Each
  agent uses the right model for its role; the memory layer is the
  invariant.

### Founder

Built solo by Evan (16) out of Shanxi, China. Memory Core is the
flagship of an open-source substrate stack — alongside
[temporal-core](https://github.com/Evanyuan-builder/temporal-core),
[RoleCore](https://github.com/Evanyuan-builder/rolecore), and
[EvanCore](https://github.com/Evanyuan-builder/evancore) — that aims to
make role-aware, time-aware agent infrastructure the boring default.
A Chinese software-copyright filing for Memory Core is currently under
CPCC review (filed 2026-05-07).

### Links

- **Live demo (public):** https://memory-core.chinasourcingbridge.com
- **3-minute storyboard:** https://memory-core.chinasourcingbridge.com/video
- **GitHub (MIT):** https://github.com/Evanyuan-builder/memory-core
- **Eval harness (Apache-2.0):** https://github.com/Evanyuan-builder/memory-core-eval
- **v1.0.0 release notes:** https://github.com/Evanyuan-builder/memory-core/releases/tag/v1.0.0

---

## 5 · Cover Image

`submission/cover.png` — 1200×675, 233 KB. Rendered from `submission/cover.html` via headless Chrome.

## 6 · Video Presentation

See `video/` (TODO — task B, recording in progress). Upload to YouTube
(unlisted) once exported.

## 7 · Slide Presentation

`submission/slides.pdf` — 5 pages, 1920×1080 each, 2.6 MB. Rendered from `submission/slides.html` via headless Chrome.

## 8 · Public GitHub Repository URL

```
https://github.com/Evanyuan-builder/memory-core
```

## 9 · Demo URL

```
https://memory-core.chinasourcingbridge.com
```

---

## Pre-submit checklist

- [ ] Title pasted exactly
- [ ] Short description ≤ form cap (check live form)
- [ ] Tags comma-separated, no spaces issues
- [ ] Long description markdown renders correctly in lablab preview
- [ ] Cover image 1200×675 minimum, < 5 MB
- [ ] Video uploaded to YouTube unlisted, link in submission AND uploaded direct as backup
- [ ] Slides exported as PDF
- [ ] GitHub repo is public + README has Live demo section linking back
- [ ] Demo URL responds 200 from a non-CN IP (test via incognito or VPN)
- [ ] Tracks selected: Featherless (primary) + Collaborative Systems + Agentic Workflows
- [ ] Submission time: before 2026-05-19 23:00 CST (China standard time)
