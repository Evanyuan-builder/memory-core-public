"""
Reviewer agent — reviews the coder's patch against the plan.

Reads from Memory Core: plan (planner namespace), patch (coder namespace).
Writes to Memory Core: namespace=reviewer, type=review.

Notice: the reviewer never sees the planner's or coder's prompts directly.
Context flows through Memory Core only — that's the demo.
"""

from __future__ import annotations

from memory_core_sdk import MemoryClient

from .llm import LLM


SYSTEM = """You are the reviewer in a 3-agent dev team.
Given a plan and a code diff, write a 2-3 sentence review.
Flag any step from the plan that the diff missed."""


class Reviewer:
    def __init__(self, llm: LLM, memory_url: str, project_slice: str) -> None:
        self.llm = llm
        self._client = MemoryClient(
            url=memory_url, namespace="reviewer", project_slice=project_slice
        )

    def run(self, task: str, episode_id: str) -> str:
        plan = self._client.search(task, top_k=3, namespace="planner")
        patch = self._client.search(task, top_k=3, namespace="coder")

        plan_blob = "\n".join(m.content for m in plan.memories) or "(no plan)"
        patch_blob = "\n".join(m.content for m in patch.memories) or "(no patch)"

        review = self.llm.chat([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Plan:\n{plan_blob}\n\nDiff:\n{patch_blob}"},
        ])

        self._client.store(
            review,
            type="review",
            tags=["reviewer-output"],
            episode_id=episode_id,
        )
        return review

    def close(self) -> None:
        self._client.close()
