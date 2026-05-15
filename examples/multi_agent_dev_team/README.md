# multi_agent_dev_team

A 3-agent dev team — **planner**, **coder**, **reviewer** — that shares
Memory Core as its context layer. Agents don't pass context through prompts.
Each agent's prompt is minimal; everything else flows through Memory Core,
namespaced by role.

Built for [AI Agent Olympics 2026](https://lablab.ai/ai-hackathons/milan-ai-week-hackathon)
(Milan AI Week).

## Why this shape

Most multi-agent systems waste tokens stuffing the full repo context into
every agent's prompt. They also leak context across roles — the reviewer
sees the planner's deliberation, the coder sees the reviewer's nitpicks,
and so on.

Memory Core's role-aware memory layer fixes both:

- Each agent writes to its own namespace (`planner` / `coder` / `reviewer`)
- Each agent reads only what it needs, by namespace + tag + type
- Prompts stay minimal — context flows through memory

## Architecture

```
        ┌──────────┐
   task │ planner  │  writes:  type=plan,    namespace=planner
   ───▶ │  (mimo)  │ ─────────────────────────┐
        └──────────┘                          │
                                              ▼
                                         ┌─────────────┐
                                         │ Memory Core │
                                         │  (LanceDB)  │
                                         └─────────────┘
                                              ▲ ▲ ▲
        ┌──────────────────────────┐          │ │ │
        │ coder                    │  reads:  │ │ │
        │ (featherless qwen-coder) │ ─────────┘ │ │
        │                          │  writes:   │ │
        │                          │ ───────────┘ │
        └──────────────────────────┘              │
                                                  │
        ┌──────────┐                              │
        │ reviewer │  reads + writes:             │
        │  (mimo)  │ ─────────────────────────────┘
        └──────────┘
```

## LLM choice (heterogeneous by design)

| Agent     | LLM                                   | Why                          |
|-----------|---------------------------------------|------------------------------|
| planner   | Xiaomi MiMo (`mimo-v2.5`)             | Fast reasoning, cheap        |
| coder     | Featherless `Qwen2.5-Coder-32B`       | Code-specialized model       |
| reviewer  | Xiaomi MiMo (`mimo-v2.5`)             | Different role, same model   |

Each agent picks the LLM that fits its role — a real dev team isn't going
to run a 32B coder model for a 3-bullet plan.

## Run

```bash
# 1. Start Memory Core API (in repo root)
make api

# 2. Configure keys
cp .env.example .env
# fill in MIMO_API_KEY and FEATHERLESS_API_KEY

# 3. Run the demo
PYTHONPATH=packages python examples/multi_agent_dev_team/run_demo.py
```

Without API keys the agents return mock outputs so you can verify the
Memory Core wiring end-to-end before paying for tokens.

## Sample task

`tasks/dark_mode_toggle.md` — a tiny Next.js feature request. Swap in your
own task file or pass a string to `run_demo.run()`.

## What you'll see

```
[planner / mimo] reading context, writing plan...
1. Read settings page
2. Add toggle component
3. Wire theme state

[coder / featherless qwen2.5-coder] reading plan, writing diff...
diff --git a/Settings.tsx b/Settings.tsx
+<DarkModeToggle />

[reviewer / mimo] reading plan + diff, writing review...
LGTM. Consider extracting useTheme() hook.
```

The interesting part isn't the output — it's that **none of the three
agents share a prompt**. They share Memory Core, and that's it.
