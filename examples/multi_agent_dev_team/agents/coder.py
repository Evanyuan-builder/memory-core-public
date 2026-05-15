"""
Coder agent — produces full file rewrites from the plan + project context.

Reads from Memory Core: plan (planner namespace), project files (bootstrap namespace).
Writes to Memory Core: namespace=coder, type=artifact — one entry per file edited.

Output format the LLM is asked to produce:

    [FILE: path/relative/to/sandbox.tsx]
    <entire new file content>
    [/FILE]

    [FILE: another.ts]
    ...
    [/FILE]

We parse those blocks and store each file as a separate memory so the reviewer
(and the UI) can compare bootstrap (before) against coder (after) per file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from memory_core_sdk import MemoryClient

from .llm import LLM


SYSTEM = """You are the coder in a 3-agent dev team.
Given a plan and the current project files, output the COMPLETE rewritten content
of each file you change. Use this exact format, nothing else:

[FILE: path/relative/to/sandbox.tsx]
<entire new file content>
[/FILE]

[FILE: another.ts]
<entire new file content>
[/FILE]

Rules:
- One [FILE]…[/FILE] block per file you change or create.
- Output the FULL file body, not a diff or excerpt.
- Use the exact relative path the user shows you. If you create a new file,
  pick a reasonable path under the same tree.
- No prose outside the blocks."""


_FILE_BLOCK = re.compile(
    r"\[FILE:\s*(?P<path>[^\]]+)\]\s*\n(?P<body>.*?)\n\[/FILE\]",
    re.DOTALL,
)


@dataclass
class FileEdit:
    path: str
    content: str


class Coder:
    def __init__(self, llm: LLM, memory_url: str, project_slice: str) -> None:
        self.llm = llm
        self._client = MemoryClient(
            url=memory_url, namespace="coder", project_slice=project_slice
        )

    def run(self, task: str, episode_id: str) -> str:
        plan = self._client.search(task, top_k=3, namespace="planner")
        plan_blob = "\n".join(m.content for m in plan.memories) or "(no plan)"

        files = self._client.search(task, top_k=10, namespace="bootstrap")
        files_blob = "\n\n".join(m.content for m in files.memories) or "(no project files)"

        raw = self.llm.chat([
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": f"Task: {task}\n\nPlan:\n{plan_blob}\n\nProject files:\n{files_blob}\n\nNow output the file blocks.",
            },
        ])

        edits = self._parse(raw)
        for edit in edits:
            self._client.store(
                f"file `{edit.path}`:\n```\n{edit.content}\n```",
                type="artifact",
                tags=["file", edit.path, "coder-output"],
                episode_id=episode_id,
            )

        if not edits:
            # Mock-mode or LLM ignored format — store the raw blob so the
            # timeline still has something visible.
            self._client.store(
                raw, type="artifact", tags=["raw", "coder-output"], episode_id=episode_id
            )
        return raw

    @staticmethod
    def _parse(raw: str) -> list[FileEdit]:
        return [
            FileEdit(path=m.group("path").strip(), content=m.group("body"))
            for m in _FILE_BLOCK.finditer(raw)
        ]

    def close(self) -> None:
        self._client.close()
