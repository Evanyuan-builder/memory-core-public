#!/usr/bin/env python3
"""Ingest a directory of markdown notes into Memory Core as a single
developer's cross-project engineering knowledge base.

Each note becomes one memory in the ``refapp.knowledge`` namespace, tagged
``project:<name>`` and ``type:<kind>`` from its frontmatter — so the same
corpus can be recalled across every project at once, or scoped to one.

Usage:
    python ingest.py [CORPUS_DIR]      # default: ./sample_corpus

Requires a Memory Core API at MEMORY_CORE_URL (default 127.0.0.1:8001).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow `from memory_core_sdk import ...` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from memory_core_sdk import MemoryClient  # noqa: E402

NAMESPACE = "refapp.knowledge"
MEMORY_URL = os.getenv("MEMORY_CORE_URL", "http://127.0.0.1:8001")


def parse_note(path: Path) -> tuple[dict[str, str], str]:
    """Split a `--- key: value ---` frontmatter block from the note body."""
    text = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        _, frontmatter, body = text.split("---", 2)
        for line in frontmatter.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body.strip()


def main() -> int:
    corpus = (
        Path(sys.argv[1]) if len(sys.argv) > 1
        else Path(__file__).parent / "sample_corpus"
    )
    notes = sorted(corpus.glob("*.md"))
    if not notes:
        print(f"no .md files in {corpus}")
        return 1

    memories: list[dict] = []
    for p in notes:
        meta, body = parse_note(p)
        project = meta.get("project", "misc")
        kind = meta.get("type", "note")
        memories.append({
            "content": body,
            "namespace": NAMESPACE,
            "tags": [f"project:{project}", f"type:{kind}"],
            "source_ref": p.name,   # stable id so re-ingest upserts, not duplicates
        })

    with MemoryClient(url=MEMORY_URL, namespace=NAMESPACE) as mem:
        res = mem.store_batch(memories)

    n_stored = res.get("n_stored", len(memories))
    projects = sorted({m["tags"][0].split(":", 1)[1] for m in memories})
    print(
        f"ingested {n_stored} notes into '{NAMESPACE}' "
        f"across {len(projects)} projects: {', '.join(projects)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
