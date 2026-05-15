"""Conversation session helper — the common agent-ingest pattern.

Agents rarely store a single turn in isolation; they accumulate a chat
transcript and want to search over it. Doing this with raw ``store`` +
``search`` works but burns one HTTP call per turn and leaves the caller to
manage turn_idx / session tags / scoping filters by hand. This module is a
small class that wraps that pattern.

Usage
-----
    from memory_core_sdk import MemoryClient

    mem = MemoryClient(namespace="agent-007")

    with mem.conversation("chat-2026-04-24") as conv:
        conv.add("user", "What was the last release date?")
        conv.add("assistant", "v1.1.0 on 2026-04-12.")
        conv.add("user", "And what changed from 1.0?")
        # ... 30 more turns
        # context exit → auto-flush via store_batch

    # Later — search scoped to this conversation
    hits = mem.conversation("chat-2026-04-24").search("release date")
    for h in hits.memories:
        print(h.role, h.content)

Design notes
------------
- Turn storage is **buffered**, flushed via ``store_batch`` on context exit
  or explicit ``flush()``. One HTTP call per N turns is the point.
- ``session_id`` is stamped as a tag ``session:<session_id>`` and mirrored
  to ``source_ref`` so downstream ranker signals (session diversity, etc.)
  can see it.
- ``turn_idx`` auto-increments from 0 within the conversation lifetime.
- ``search()`` does not filter to the conversation by default — most agent
  queries search across conversations. Pass ``only_this=True`` to scope.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import AsyncMemoryClient, MemoryClient, SearchResult


class Conversation:
    """Buffered per-conversation ingest + scoped search over ``MemoryClient``.

    Don't instantiate directly — call ``MemoryClient.conversation(id)`` which
    wires the parent client in.
    """

    def __init__(
        self,
        client: "MemoryClient",
        session_id: str,
        namespace: str | None = None,
        auto_flush_every: int = 50,
    ) -> None:
        self._client = client
        self.session_id = session_id
        self.namespace = namespace or client.namespace
        self._buffer: list[dict[str, Any]] = []
        self._turn_idx = 0
        self._auto_flush_every = auto_flush_every

    # ── Ingest ────────────────────────────────────────────────────────────

    def add(self, role: str, content: str, **extra: Any) -> None:
        """Buffer one turn. Auto-flushes when the buffer reaches the trigger."""
        turn = {
            "content": content,
            "namespace": self.namespace,
            "tags": [f"session:{self.session_id}", f"role:{role}", f"turn:{self._turn_idx}"],
            "source_ref": f"session/{self.session_id}/turn/{self._turn_idx}",
            "episode_id": self.session_id,
        }
        turn.update(extra)
        self._buffer.append(turn)
        self._turn_idx += 1
        if len(self._buffer) >= self._auto_flush_every:
            self.flush()

    def add_user(self, content: str, **extra: Any) -> None:
        self.add("user", content, **extra)

    def add_assistant(self, content: str, **extra: Any) -> None:
        self.add("assistant", content, **extra)

    def add_system(self, content: str, **extra: Any) -> None:
        self.add("system", content, **extra)

    def flush(self) -> dict[str, Any] | None:
        """Push buffered turns via ``store_batch``. Returns the batch envelope
        or None when the buffer is empty.
        """
        if not self._buffer:
            return None
        memories, self._buffer = self._buffer, []
        return self._client.store_batch(memories)

    # ── Search ────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        only_this: bool = False,
        **kwargs: Any,
    ) -> "SearchResult":
        """Search. ``only_this=True`` scopes to this conversation's session
        tag; default is namespace-wide (what agents usually want).
        """
        if only_this:
            tag_filter = list(kwargs.pop("tag_filter", []) or [])
            tag_filter.append(f"session:{self.session_id}")
            kwargs["tag_filter"] = tag_filter
        return self._client.search(query, namespace=self.namespace, **kwargs)

    # ── Context manager ──────────────────────────────────────────────────

    def __enter__(self) -> "Conversation":
        return self

    def __exit__(self, *_) -> None:
        self.flush()

    # ── Diagnostics ──────────────────────────────────────────────────────

    @property
    def pending(self) -> int:
        """Count of buffered-but-unflushed turns."""
        return len(self._buffer)

    @property
    def turn_count(self) -> int:
        """Total turns added this session (including flushed ones)."""
        return self._turn_idx


class AsyncConversation:
    """Async mirror of :class:`Conversation`. Use with ``AsyncMemoryClient``.

    Don't instantiate directly — call ``AsyncMemoryClient.conversation(id)``.

    Usage::

        async with AsyncMemoryClient(namespace="agent") as mem:
            async with mem.conversation("chat-1") as conv:
                await conv.add_user("Hello")
                await conv.add_assistant("Hi!")
                # ... exit → await-ed auto-flush via store_batch
    """

    def __init__(
        self,
        client: "AsyncMemoryClient",
        session_id: str,
        namespace: str | None = None,
        auto_flush_every: int = 50,
    ) -> None:
        self._client = client
        self.session_id = session_id
        self.namespace = namespace or client.namespace
        self._buffer: list[dict[str, Any]] = []
        self._turn_idx = 0
        self._auto_flush_every = auto_flush_every

    # ── Ingest ────────────────────────────────────────────────────────────

    async def add(self, role: str, content: str, **extra: Any) -> None:
        turn = {
            "content": content,
            "namespace": self.namespace,
            "tags": [f"session:{self.session_id}", f"role:{role}", f"turn:{self._turn_idx}"],
            "source_ref": f"session/{self.session_id}/turn/{self._turn_idx}",
            "episode_id": self.session_id,
        }
        turn.update(extra)
        self._buffer.append(turn)
        self._turn_idx += 1
        if len(self._buffer) >= self._auto_flush_every:
            await self.flush()

    async def add_user(self, content: str, **extra: Any) -> None:
        await self.add("user", content, **extra)

    async def add_assistant(self, content: str, **extra: Any) -> None:
        await self.add("assistant", content, **extra)

    async def add_system(self, content: str, **extra: Any) -> None:
        await self.add("system", content, **extra)

    async def flush(self) -> dict[str, Any] | None:
        if not self._buffer:
            return None
        memories, self._buffer = self._buffer, []
        return await self._client.store_batch(memories)

    # ── Search ────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        *,
        only_this: bool = False,
        **kwargs: Any,
    ) -> "SearchResult":
        if only_this:
            tag_filter = list(kwargs.pop("tag_filter", []) or [])
            tag_filter.append(f"session:{self.session_id}")
            kwargs["tag_filter"] = tag_filter
        return await self._client.search(query, namespace=self.namespace, **kwargs)

    # ── Context manager ──────────────────────────────────────────────────

    async def __aenter__(self) -> "AsyncConversation":
        return self

    async def __aexit__(self, *_) -> None:
        await self.flush()

    # ── Diagnostics ──────────────────────────────────────────────────────

    @property
    def pending(self) -> int:
        return len(self._buffer)

    @property
    def turn_count(self) -> int:
        return self._turn_idx
