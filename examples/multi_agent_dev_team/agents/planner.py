"""
Planner agent — decomposes a user task into ordered steps.

Reads from Memory Core: project context (layer=context, any namespace).
Writes to Memory Core: namespace=planner, type=plan.
"""

from __future__ import annotations

from memory_core_sdk import MemoryClient

from .llm import LLM


SYSTEM = """You are the planner in a 3-agent dev team.
Decompose the task into 2-5 ordered steps, each one short and actionable.
Output: a numbered list. No prose."""


class Planner:
    def __init__(self, llm: LLM, memory_url: str, project_slice: str) -> None:
        self.llm = llm
        self._client = MemoryClient(
            url=memory_url, namespace="planner", project_slice=project_slice
        )

    def run(self, task: str, episode_id: str) -> str:
        # Pull project context (any role can have written it; we read across)
        ctx = self._client.search(task, top_k=5)
        context_blob = "\n".join(f"- {m.content}" for m in ctx.memories) or "(no prior context)"

        plan = self.llm.chat([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Project context:\n{context_blob}\n\nTask: {task}"},
        ])

        self._client.store(
            plan,
            type="plan",
            tags=["planner-output"],
            episode_id=episode_id,
        )
        return plan

    def close(self) -> None:
        self._client.close()
