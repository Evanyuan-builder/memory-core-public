#!/usr/bin/env python3
"""Recall from the cross-project knowledge base.

    python ask.py "how do we handle retries?"          # across all projects
    python ask.py "how do we handle retries?" infra    # scoped to one project

Demonstrates that one question surfaces the relevant decisions and learnings
regardless of which project they were written in — and that a project tag
narrows the same query to a single codebase.

Requires a Memory Core API at MEMORY_CORE_URL (default 127.0.0.1:8001).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from memory_core_sdk import MemoryClient  # noqa: E402

NAMESPACE = "refapp.knowledge"
MEMORY_URL = os.getenv("MEMORY_CORE_URL", "http://127.0.0.1:8001")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    query = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else None
    tag_filter = [f"project:{project}"] if project else None
    scope = f"project={project}" if project else "all projects"

    with MemoryClient(url=MEMORY_URL, namespace=NAMESPACE) as mem:
        res = mem.search(query, top_k=3, tag_filter=tag_filter)

    print(f"Q: {query}   ({scope})\n")
    if not res.memories:
        print("  (no matches — did you run `python ingest.py` first?)")
        return 0
    for i, m in enumerate(res.memories, 1):
        proj = next(
            (t.split(":", 1)[1] for t in m.tags if t.startswith("project:")),
            "?",
        )
        score = f"{m.score:.3f}" if m.score is not None else "-"
        first_line = m.content.strip().splitlines()[0]
        print(f"{i}. [{proj}]  score={score}\n   {first_line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
