"""
Demo web server — wraps run_demo.run() in HTTP + SSE.

Run:
    set -a && source examples/multi_agent_dev_team/.env && set +a
    PYTHONPATH=packages uvicorn examples.multi_agent_dev_team.server:app --port 8765

Visit http://127.0.0.1:8765/
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "packages"))
sys.path.insert(0, str(HERE))

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

WEB_DIR = Path(__file__).parent / "web"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    task: str


SANDBOX_DIR = Path(__file__).parent / "sandbox"
CODE_SUFFIXES = {".tsx", ".ts", ".jsx", ".js", ".py"}


def _seed_context() -> None:
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


async def _stream_episode(task: str):
    """SSE generator. Each yield is one event the UI animates on."""
    episode_id = f"ep-{uuid.uuid4().hex[:8]}"

    def evt(kind: str, payload: dict) -> str:
        return f"data: {json.dumps({'kind': kind, **payload})}\n\n"

    yield evt("episode", {"episode_id": episode_id, "task": task})

    # seed
    yield evt("status", {"agent": "bootstrap", "state": "running"})
    await asyncio.to_thread(_seed_context)
    yield evt("status", {"agent": "bootstrap", "state": "done"})

    # planner
    yield evt("status", {"agent": "planner", "state": "running"})
    planner = Planner(get_planner_llm(), MEMORY_URL, PROJECT_SLICE)
    try:
        plan = await asyncio.to_thread(planner.run, task, episode_id)
    finally:
        planner.close()
    yield evt("status", {"agent": "planner", "state": "done"})
    yield evt("output", {"agent": "planner", "content": plan})

    # coder
    yield evt("status", {"agent": "coder", "state": "running"})
    coder = Coder(get_coder_llm(), MEMORY_URL, PROJECT_SLICE)
    try:
        patch = await asyncio.to_thread(coder.run, task, episode_id)
    finally:
        coder.close()
    yield evt("status", {"agent": "coder", "state": "done"})
    yield evt("output", {"agent": "coder", "content": patch})

    # reviewer
    yield evt("status", {"agent": "reviewer", "state": "running"})
    reviewer = Reviewer(get_reviewer_llm(), MEMORY_URL, PROJECT_SLICE)
    try:
        review = await asyncio.to_thread(reviewer.run, task, episode_id)
    finally:
        reviewer.close()
    yield evt("status", {"agent": "reviewer", "state": "done"})
    yield evt("output", {"agent": "reviewer", "content": review})

    yield evt("episode_done", {"episode_id": episode_id})


@app.post("/api/run")
async def run_episode(req: RunRequest):
    return StreamingResponse(_stream_episode(req.task), media_type="text/event-stream")


@app.get("/api/memories")
def list_memories(q: str = "", namespace: str | None = None, top_k: int = 20):
    """Frontend polls this for the Memory Core timeline."""
    with MemoryClient(url=MEMORY_URL, namespace=namespace or "viewer", project_slice=PROJECT_SLICE) as mem:
        if namespace:
            r = mem.search(q or "*", top_k=top_k, namespace=namespace)
        else:
            r = mem.search(q or "*", top_k=top_k)
    return {
        "memories": [
            {"id": m.id, "namespace": getattr(m, "namespace", None), "type": m.type, "content": m.content, "tags": getattr(m, "tags", [])}
            for m in r.memories
        ]
    }


@app.get("/")
def root():
    return FileResponse(WEB_DIR / "index.html")


VIDEO_DIR = Path(__file__).parent / "video"


@app.get("/video")
def video_storyboard():
    return FileResponse(VIDEO_DIR / "storyboard.html")
