# Memory Core — Public Showcase

> Multi-agent dev teams burn tokens passing context through prompts — and lose it every session reset.
> Memory Core fixes that with role-scoped namespaces.

This repository is the **public showcase** for [Memory Core](https://memory-core.chinasourcingbridge.com), a role-aware memory layer for multi-agent systems. It is the **AI Agent Olympics 2026 / Milan AI Week** hackathon submission for the **Featherless** track (also Collaborative Systems and Agentic Workflows).

## What's in here

| Path | What it is |
|---|---|
| `examples/multi_agent_dev_team/` | The hackathon demo — three agents (planner, coder, reviewer) collaborating through Memory Core's namespaces |
| `examples/multi_agent_dev_team/submission/` | Cover image, slide deck (1920×1080 × 5 pages), and full lablab.ai submission text |
| `examples/multi_agent_dev_team/video/` | HTML composition for the demo video, rendered to MP4 via [HyperFrames](https://github.com/heygen-com/hyperframes) |
| `memory_core_sdk/` | Python REST client for the Memory Core API |

## Benchmarks (verified externally)

Reproducible from the public [memory-core-eval](https://github.com/Evanyuan-builder/memory-core-eval) harness (Apache-2.0):

| Benchmark | Memory Core R@10 | Published anchor R@10 |
|---|---:|---:|
| LongMemEval-S (n=500) | **99.4** | 97.9 (Hybrid-RRF) |
| LoCoMo (n=500) | **88.8** | 85.0 (Hybrid-RRF) |

Cross-restart determinism is a verified property at the same revision — zero question flips across runs.

## Live demo

[**memory-core.chinasourcingbridge.com**](https://memory-core.chinasourcingbridge.com)

Click *Run episode* and watch three real LLM agents (planner: `mimo-v2.5`, coder: `Qwen2.5-Coder-32B-Instruct` via Featherless, reviewer: `mimo-v2.5`) collaborate on a real coding task ("add a dark-mode toggle to a Next.js settings page"). Each agent reads only its own role's prompt — the shared substrate is the memory layer.

## Open ecosystem, closed core

This repository follows the same publishing pattern as the rest of our [substrate stack](https://github.com/Evanyuan-builder) — open verification, open interface, closed core:

| Component | Visibility | License |
|---|---|---|
| Memory Core retrieval engine + REST API server | private | proprietary |
| Memory Core SDK *(this repo)* | public | Apache-2.0 |
| Hackathon showcase example *(this repo)* | public | Apache-2.0 |
| Evaluation harness ([memory-core-eval](https://github.com/Evanyuan-builder/memory-core-eval)) | public | Apache-2.0 |

Everything required to **verify the benchmarks**, **understand the API surface**, and **see how Memory Core is used in a real multi-agent system** is open. The retrieval engine itself is privately licensed.

## Substrate stack siblings

- [memory-core-eval](https://github.com/Evanyuan-builder/memory-core-eval) — reproducible eval harness for agent memory systems
- [temporal-core](https://github.com/Evanyuan-builder/temporal-core) — temporal awareness skill for Claude Code
- [rolecore](https://github.com/Evanyuan-builder/rolecore) — role-aware permission layer for LLM agents (public showcase)
- [evancore](https://github.com/Evanyuan-builder/evancore) — CLI-first harness engineering for AI agents (public showcase)

## Quick start (showcase example)

The hackathon example talks to a Memory Core REST API. Point it at the hosted demo or your own instance:

```bash
git clone https://github.com/Evanyuan-builder/memory-core-public.git
cd memory-core-public

# Install the SDK
pip install -e .

# Run the demo
cd examples/multi_agent_dev_team
cp .env.example .env  # add your Featherless + Xiaomi MiMo API keys
export MC_API_URL=https://memory-core.chinasourcingbridge.com  # or your own
python run_demo.py
```

For end-to-end interactive runs with the live UI, see the [live demo](https://memory-core.chinasourcingbridge.com) — no setup required.

## Featherless track fit

The Featherless brief asks for **domain-specialized + async-first + permissively-licensed + production-shaped** — those four points are literally Memory Core's design pillars:

- **Domain-specialized**: the demo targets software dev teams. Namespace primitives encode roles for an org, not chat users.
- **Async-first**: agents communicate through namespaces, not chat turns. No agent is blocked on another agent's prompt being read.
- **Permissive**: Apache-2.0 SDK + Apache-2.0 evaluation harness. Real open ecosystem.
- **Production-shaped**: REST API, Python SDK, 10+ pluggable backends, 369 unit + 99 e2e tests on v1.0.0.

The coder calls `Qwen2.5-Coder-32B-Instruct` from Featherless's open catalog, satisfying the track's "use models from the catalog" requirement.

## Founder

Built solo by **Evan**, age 16, out of Shanxi, China. Memory Core's Chinese software copyright filing is under CPCC review (filed 2026-05-07).

## License

Apache-2.0 — see [LICENSE](LICENSE).
