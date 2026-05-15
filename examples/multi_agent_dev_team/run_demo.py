"""
Multi-agent dev team — end-to-end demo runner.

Run:
    PYTHONPATH=packages python examples/multi_agent_dev_team/run_demo.py

Requires: Memory Core API at MEMORY_CORE_URL (default 127.0.0.1:8001).
The 3 agents share that one Memory Core instance — different namespaces
(planner / coder / reviewer) so each role's writes are tagged, but reads
can cross namespaces by passing namespace= to search().

This is the demo's whole point: agents don't pass context via prompts.
Each agent's prompt is minimal. Context flows through Memory Core only.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

# Allow `from memory_core_sdk import ...` from the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages"))

from memory_core_sdk import MemoryClient  # noqa: E402

from agents import (  # noqa: E402
    Coder,
    Planner,
    Reviewer,
    get_coder_llm,
    get_planner_llm,
    get_reviewer_llm,
)


MEMORY_URL = os.getenv("MEMORY_CORE_URL", "http://127.0.0.1:8001")
PROJECT_SLICE = os.getenv("MEMORY_CORE_PROJECT_SLICE", "generic-project")


SANDBOX_DIR = Path(__file__).parent / "sandbox"
CODE_SUFFIXES = {".tsx", ".ts", ".jsx", ".js", ".py"}


def seed_project_context() -> None:
    """Walk sandbox/ and store each real file into Memory Core as project context."""
    if not SANDBOX_DIR.exists():
        return
    with MemoryClient(url=MEMORY_URL, namespace="bootstrap", project_slice=PROJECT_SLICE) as mem:
        for p in sorted(SANDBOX_DIR.rglob("*")):
            if not (p.is_file() and p.suffix in CODE_SUFFIXES):
                continue
            rel = p.relative_to(SANDBOX_DIR).as_posix()
            mem.store(
                f"file `{rel}`:\n```{p.suffix.lstrip('.')}\n{p.read_text()}\n```",
                type="context",
                tags=["project", "file", rel],
            )


def run(task: str) -> dict[str, str]:
    episode_id = f"ep-{uuid.uuid4().hex[:8]}"
    print(f"\n=== Episode {episode_id} ===")
    print(f"Task: {task}\n")

    seed_project_context()

    planner = Planner(get_planner_llm(), MEMORY_URL, PROJECT_SLICE)
    coder = Coder(get_coder_llm(), MEMORY_URL, PROJECT_SLICE)
    reviewer = Reviewer(get_reviewer_llm(), MEMORY_URL, PROJECT_SLICE)

    try:
        print("[planner / mimo] reading context, writing plan...")
        plan = planner.run(task, episode_id)
        print(plan, "\n")

        print("[coder / featherless qwen2.5-coder] reading plan, writing diff...")
        patch = coder.run(task, episode_id)
        print(patch, "\n")

        print("[reviewer / mimo] reading plan + diff, writing review...")
        review = reviewer.run(task, episode_id)
        print(review, "\n")

        return {"plan": plan, "patch": patch, "review": review, "episode_id": episode_id}
    finally:
        planner.close()
        coder.close()
        reviewer.close()


if __name__ == "__main__":
    task_file = Path(__file__).parent / "tasks" / "dark_mode_toggle.md"
    task = task_file.read_text().strip() if task_file.exists() else "Add a dark mode toggle to the settings page."
    run(task)
