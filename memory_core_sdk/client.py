"""
Memory Core SDK — Python client for the unified Memory Core REST API.

Quickstart:
    from memory_core_sdk import MemoryClient

    mem = MemoryClient(namespace="my-project")
    mem.store("We decided to use FalkorDB over Neo4j.")
    results = mem.search("database decision")

Async:
    async with AsyncMemoryClient(namespace="my-project") as mem:
        await mem.store("async fact")
        results = await mem.search("async")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from .conversation import AsyncConversation, Conversation

# ── Value objects ─────────────────────────────────────────────────────────────

@dataclass
class Memory:
    """A single memory returned from the API."""
    id: str
    content: str
    namespace: str
    type: str = "observation"
    tags: list[str] = field(default_factory=list)
    score: float | None = None
    episode_id: str | None = None
    source_ref: str | None = None
    ttl_seconds: int | None = None
    created_at: str | None = None
    valid_at: str | None = None
    invalid_at: str | None = None
    # Three-layer routing fields
    layer: str = "brain"          # brain | ops | session
    is_entity_page: bool = False  # Compiled Truth + Timeline format

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Memory":
        temporal = d.get("temporal") or {}
        return cls(
            id=str(d.get("id", "")),
            content=d.get("content", ""),
            namespace=d.get("namespace", ""),
            type=d.get("type", "observation"),
            tags=d.get("tags", []),
            score=d.get("relevance_score"),
            episode_id=d.get("episode_id"),
            source_ref=d.get("source_ref"),
            ttl_seconds=d.get("ttl_seconds"),
            created_at=d.get("created_at"),
            valid_at=temporal.get("valid_at"),
            invalid_at=temporal.get("invalid_at"),
            layer=d.get("layer", "brain"),
            is_entity_page=bool(d.get("is_entity_page", False)),
        )

    def __repr__(self) -> str:
        score_str = f" score={self.score:.3f}" if self.score is not None else ""
        return f"Memory(ns={self.namespace!r}{score_str}, content={self.content[:60]!r})"


@dataclass
class SearchResult:
    memories: list[Memory]
    total: int
    query: str
    backend: str
    latency_ms: float | None = None

    def __repr__(self) -> str:
        return f"SearchResult(total={self.total}, backend={self.backend!r}, latency={self.latency_ms}ms)"


class MemoryCoreError(Exception):
    pass


# ── Shared request logic ──────────────────────────────────────────────────────

def _build_store_payload(
    content: str,
    namespace: str | None,
    type: str,
    tags: list[str],
    episode_id: str | None,
    source_ref: str | None,
    ttl_seconds: int | None,
    project_slice: str | None,
) -> dict:
    payload: dict[str, Any] = {
        "content": content,
        "type": type,
        "tags": tags,
    }
    if namespace:
        payload["namespace"] = namespace
    if episode_id:
        payload["episode_id"] = episode_id
    if source_ref:
        payload["source_ref"] = source_ref
    if ttl_seconds is not None:
        payload["ttl_seconds"] = ttl_seconds
    if project_slice:
        payload["project_slice"] = project_slice
    return payload


def _build_search_payload(
    query: str,
    namespace: str | None,
    top_k: int,
    include_temporal: bool,
    tag_filter: list[str] | None,
    min_score: float,
    project_slice: str | None,
    *,
    ranker: str | None = None,
    explain: bool = False,
    min_credibility: float | None = None,
    include_superseded: bool = False,
    as_of_date: Any = None,
    role: str | None = None,
    role_scope: str | None = None,
    roles: list[str] | None = None,
) -> dict:
    payload: dict[str, Any] = {
        "query": query,
        "top_k": top_k,
        "include_temporal": include_temporal,
        "min_score": min_score,
    }
    if namespace:
        payload["namespace"] = namespace
    if tag_filter:
        payload["tag_filter"] = tag_filter
    if project_slice:
        payload["project_slice"] = project_slice
    if ranker:
        payload["ranker"] = ranker
    if explain:
        payload["explain"] = True
    if min_credibility is not None:
        payload["min_credibility"] = float(min_credibility)
    if include_superseded:
        payload["include_superseded"] = True
    if as_of_date is not None:
        # httpx serialises datetimes fine; tolerate strings too.
        if hasattr(as_of_date, "isoformat"):
            payload["as_of_date"] = as_of_date.isoformat()
        else:
            payload["as_of_date"] = str(as_of_date)
    if role:
        payload["role"] = role
    if role_scope:
        payload["role_scope"] = role_scope
    if roles:
        payload["roles"] = list(roles)
    return payload


def _parse_search_response(data: dict, query: str) -> SearchResult:
    memories = [Memory.from_dict(m) for m in data.get("memories", [])]
    return SearchResult(
        memories=memories,
        total=data.get("total", len(memories)),
        query=query,
        backend=data.get("backend_used", ""),
        latency_ms=data.get("latency_ms"),
    )


# ── Synchronous client ────────────────────────────────────────────────────────

class MemoryClient:
    """
    Synchronous Memory Core client.

    Args:
        url:       Memory Core API base URL (default http://127.0.0.1:8001)
        namespace: Default namespace for all operations
        timeout:   HTTP timeout in seconds

    Example:
        mem = MemoryClient(namespace="yunzhou")
        mem.store("用户选择了月付方案")
        results = mem.search("用户付款偏好")
        for r in results:
            print(r.content, r.score)
    """

    def __init__(
        self,
        url: str = "http://127.0.0.1:8001",
        namespace: str | None = "default",
        project_slice: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._url = url.rstrip("/")
        self.namespace = namespace
        self.project_slice = project_slice
        self._client = httpx.Client(
            base_url=self._url,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
            transport=httpx.HTTPTransport(),  # bypass system proxy for local API
        )

    # ── Layer routing helper ──────────────────────────────────────────────────

    @staticmethod
    def route_layer(info: str) -> str:
        """Classify *info* into a routing layer: "brain" | "ops" | "session".

        Uses keyword heuristics matching GBrain's three-layer taxonomy:
          brain   — facts about the world (people, companies, events, ideas)
          ops     — how the agent should behave (preferences, config, rules)
          session — current conversation context (ephemeral, already in window)

        This is intentionally simple — use it as a starting point, not gospel.
        """
        text = info.lower()
        session_signals = {
            "just said", "current task", "this conversation", "we were just",
            "you asked me to", "the file i just", "right now", "at the moment",
        }
        ops_signals = {
            "prefer ", "preference", "always use", "never use", "format ",
            "formatting", "style ", "config ", "config:", "setting ", "setting:",
            "behavior ", "rule:", "do not ", "don't ", "please always", "please never",
        }
        if any(s in text for s in session_signals):
            return "session"
        if any(s in text for s in ops_signals):
            return "ops"
        return "brain"

    # ── Core CRUD ─────────────────────────────────────────────────────────────

    def store(
        self,
        content: str,
        *,
        namespace: str | None = None,
        type: str = "observation",
        tags: list[str] | None = None,
        episode_id: str | None = None,
        source_ref: str | None = None,
        ttl_seconds: int | None = None,
        layer: str | None = None,
        is_entity_page: bool = False,
        project_slice: str | None = None,
    ) -> Memory:
        """Store a memory. Returns the stored Memory object."""
        payload = _build_store_payload(
            content=content,
            namespace=namespace or self.namespace,
            type=type,
            tags=tags or [],
            episode_id=episode_id,
            source_ref=source_ref,
            ttl_seconds=ttl_seconds,
            project_slice=project_slice or self.project_slice,
        )
        if layer:
            payload["layer"] = layer
        payload["is_entity_page"] = is_entity_page
        try:
            r = self._client.post("/api/v1/memories/", json=payload)
            r.raise_for_status()
            return Memory.from_dict(r.json())
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(f"store failed [{e.response.status_code}]: {e.response.text}") from e

    # ── Entity page helpers ────────────────────────────────────────────────────

    def store_entity(
        self,
        compiled_truth: str,
        *,
        namespace: str | None = None,
        tags: list[str] | None = None,
        source_ref: str | None = None,
    ) -> Memory:
        """Store a new entity page with compiled truth (no timeline yet)."""
        return self.store(
            content=compiled_truth,
            namespace=namespace,
            tags=tags,
            source_ref=source_ref,
            layer="brain",
            is_entity_page=True,
        )

    def append_timeline(
        self,
        memory_id: str,
        summary: str,
        *,
        namespace: str | None = None,
        date: str | None = None,
        source: str | None = None,
    ) -> Memory:
        """Append an immutable timeline entry to an entity page."""
        ns = namespace or self.namespace
        payload: dict[str, Any] = {"namespace": ns, "summary": summary}
        if date:
            payload["date"] = date
        if source:
            payload["source"] = source
        try:
            r = self._client.post(f"/api/v1/memories/{memory_id}/timeline", json=payload)
            r.raise_for_status()
            return Memory.from_dict(r.json())
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(f"append_timeline failed [{e.response.status_code}]: {e.response.text}") from e

    def rewrite_compiled_truth(
        self,
        memory_id: str,
        compiled_truth: str,
        *,
        namespace: str | None = None,
    ) -> Memory:
        """Rewrite the compiled truth zone; timeline is left unchanged."""
        ns = namespace or self.namespace
        try:
            r = self._client.put(
                f"/api/v1/memories/{memory_id}/compiled-truth",
                json={"namespace": ns, "compiled_truth": compiled_truth},
            )
            r.raise_for_status()
            return Memory.from_dict(r.json())
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(f"rewrite_compiled_truth failed [{e.response.status_code}]: {e.response.text}") from e

    def search(
        self,
        query: str,
        *,
        namespace: str | None = None,
        top_k: int = 5,
        include_temporal: bool = False,
        tag_filter: list[str] | None = None,
        min_score: float = 0.0,
        layer: str | None = None,
        project_slice: str | None = None,
        ranker: str | None = None,
        explain: bool = False,
        min_credibility: float | None = None,
        include_superseded: bool = False,
        as_of_date: Any = None,
        role: str | None = None,
        role_scope: str | None = None,
        roles: list[str] | None = None,
    ) -> SearchResult:
        """Search memories. Returns a SearchResult with .memories list.

        ``ranker`` selects a named preset (hybrid / conversation / knowledge /
        preference). ``explain`` attaches per-memory signal traces. Remaining
        flags wrap the matching SearchRequest fields documented in the API.

        Role-aware routing: ``role_scope="agent"`` + ``role="csa"`` restricts
        to the caller's role; ``"cross-role"`` + ``roles=[…]`` returns the
        union; ``"organizational"`` is the team-shared pool. Default (None)
        keeps the pre-role behaviour.
        """
        payload = _build_search_payload(
            query=query,
            namespace=namespace or self.namespace,
            top_k=top_k,
            include_temporal=include_temporal,
            tag_filter=tag_filter,
            min_score=min_score,
            project_slice=project_slice or self.project_slice,
            ranker=ranker,
            explain=explain,
            min_credibility=min_credibility,
            include_superseded=include_superseded,
            as_of_date=as_of_date,
            role=role,
            role_scope=role_scope,
            roles=roles,
        )
        if layer:
            payload["layer"] = layer
        try:
            r = self._client.post("/api/v1/memories/search", json=payload)
            r.raise_for_status()
            return _parse_search_response(r.json(), query)
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(f"search failed [{e.response.status_code}]: {e.response.text}") from e

    def list_by_namespace(
        self,
        *,
        namespace: str | None = None,
        top_k: int = 50,
        tags: list[str] | None = None,
        match_all: bool = True,
    ) -> SearchResult:
        """List memories in a namespace, newest-first, with optional tag filter.

        No query string, no semantic ranking — use for chronological replay,
        audit/list views, or "everything on project X most-recent first".
        Pair with role-aware /search when relevance matters.
        """
        ns = namespace or self.namespace
        if not ns:
            raise MemoryCoreError("list_by_namespace: namespace is required")
        params: dict[str, Any] = {"namespace": ns, "top_k": top_k}
        if tags:
            params["tag"] = list(tags)
            params["match_all"] = "true" if match_all else "false"
        try:
            r = self._client.get("/api/v1/memories/list", params=params)
            r.raise_for_status()
            return _parse_search_response(r.json(), query="")
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(
                f"list failed [{e.response.status_code}]: {e.response.text}"
            ) from e

    def store_batch(
        self,
        memories: list[dict],
        *,
        max_parallelism: int = 8,
    ) -> dict[str, Any]:
        """Bulk-store up to the configured batch limit in one call.

        ``memories`` is a list of dicts shaped like StoreRequest — at minimum
        ``content`` and ``namespace`` (or project_slice). The server returns
        a partial-success envelope: ``{stored, errors, n_stored, n_errors}``.
        """
        payload = {
            "memories": memories,
            "max_parallelism": max_parallelism,
        }
        try:
            r = self._client.post("/api/v1/memories/batch", json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(
                f"batch store failed [{e.response.status_code}]: {e.response.text}"
            ) from e

    def config(self) -> dict[str, Any]:
        """Fetch the runtime ranker / feature configuration snapshot.

        Handy for debugging "is preset X live?" without grepping env. Same
        shape as GET /api/v1/config (no secrets).
        """
        try:
            r = self._client.get("/api/v1/config")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(
                f"config fetch failed [{e.response.status_code}]: {e.response.text}"
            ) from e

    def conversation(
        self,
        session_id: str,
        *,
        namespace: str | None = None,
        auto_flush_every: int = 50,
    ) -> "Conversation":
        """Return a buffered per-conversation ingest + scoped-search helper.

        See :class:`memory_core_sdk.conversation.Conversation` for the
        agent-ingest pattern. Use as a context manager so buffered turns
        flush on exit.
        """
        from .conversation import Conversation  # late import breaks cycle
        return Conversation(
            client=self,
            session_id=session_id,
            namespace=namespace,
            auto_flush_every=auto_flush_every,
        )

    def get(self, memory_id: str, *, namespace: str | None = None) -> Memory | None:
        """Retrieve a memory by ID. Returns None if not found."""
        ns = namespace or self.namespace
        try:
            r = self._client.get(f"/api/v1/memories/{memory_id}", params={"namespace": ns})
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return Memory.from_dict(r.json())
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(f"get failed [{e.response.status_code}]: {e.response.text}") from e

    def delete(self, memory_id: str, *, namespace: str | None = None) -> bool:
        """Delete a memory by ID. Returns True if deleted."""
        ns = namespace or self.namespace
        try:
            r = self._client.delete(f"/api/v1/memories/{memory_id}", params={"namespace": ns})
            return r.status_code in (200, 204)
        except httpx.HTTPStatusError:
            return False

    def health(self) -> dict[str, Any]:
        """Check health of all backends."""
        try:
            r = self._client.get("/health")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise MemoryCoreError(f"health check failed: {e}") from e

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MemoryClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()


# ── Async client ──────────────────────────────────────────────────────────────

class AsyncMemoryClient:
    """
    Async Memory Core client (use with async/await).

    Example:
        async with AsyncMemoryClient(namespace="evan_core") as mem:
            await mem.store("Agent decided to retry with backoff")
            results = await mem.search("retry strategy")
    """

    def __init__(
        self,
        url: str = "http://127.0.0.1:8001",
        namespace: str | None = "default",
        project_slice: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._url = url.rstrip("/")
        self.namespace = namespace
        self.project_slice = project_slice
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._url,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
                transport=httpx.AsyncHTTPTransport(),  # bypass system proxy for local API
            )
        return self._client

    async def store(
        self,
        content: str,
        *,
        namespace: str | None = None,
        type: str = "observation",
        tags: list[str] | None = None,
        episode_id: str | None = None,
        source_ref: str | None = None,
        ttl_seconds: int | None = None,
        layer: str | None = None,
        is_entity_page: bool = False,
        project_slice: str | None = None,
    ) -> Memory:
        payload = _build_store_payload(
            content=content,
            namespace=namespace or self.namespace,
            type=type,
            tags=tags or [],
            episode_id=episode_id,
            source_ref=source_ref,
            ttl_seconds=ttl_seconds,
            project_slice=project_slice or self.project_slice,
        )
        if layer:
            payload["layer"] = layer
        payload["is_entity_page"] = is_entity_page
        try:
            c = await self._http()
            r = await c.post("/api/v1/memories/", json=payload)
            r.raise_for_status()
            return Memory.from_dict(r.json())
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(f"store failed [{e.response.status_code}]: {e.response.text}") from e

    async def search(
        self,
        query: str,
        *,
        namespace: str | None = None,
        top_k: int = 5,
        include_temporal: bool = False,
        tag_filter: list[str] | None = None,
        min_score: float = 0.0,
        layer: str | None = None,
        project_slice: str | None = None,
        ranker: str | None = None,
        explain: bool = False,
        min_credibility: float | None = None,
        include_superseded: bool = False,
        as_of_date: Any = None,
        role: str | None = None,
        role_scope: str | None = None,
        roles: list[str] | None = None,
    ) -> SearchResult:
        payload = _build_search_payload(
            query=query,
            namespace=namespace or self.namespace,
            top_k=top_k,
            include_temporal=include_temporal,
            tag_filter=tag_filter,
            min_score=min_score,
            project_slice=project_slice or self.project_slice,
            ranker=ranker,
            explain=explain,
            min_credibility=min_credibility,
            include_superseded=include_superseded,
            as_of_date=as_of_date,
            role=role,
            role_scope=role_scope,
            roles=roles,
        )
        if layer:
            payload["layer"] = layer
        try:
            c = await self._http()
            r = await c.post("/api/v1/memories/search", json=payload)
            r.raise_for_status()
            return _parse_search_response(r.json(), query)
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(f"search failed [{e.response.status_code}]: {e.response.text}") from e

    async def store_batch(
        self,
        memories: list[dict],
        *,
        max_parallelism: int = 8,
    ) -> dict[str, Any]:
        """Bulk-store up to the configured batch limit in one call."""
        payload = {"memories": memories, "max_parallelism": max_parallelism}
        try:
            c = await self._http()
            r = await c.post("/api/v1/memories/batch", json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(
                f"batch store failed [{e.response.status_code}]: {e.response.text}"
            ) from e

    async def config(self) -> dict[str, Any]:
        """Fetch the runtime ranker / feature configuration snapshot."""
        try:
            c = await self._http()
            r = await c.get("/api/v1/config")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(
                f"config fetch failed [{e.response.status_code}]: {e.response.text}"
            ) from e

    def conversation(
        self,
        session_id: str,
        *,
        namespace: str | None = None,
        auto_flush_every: int = 50,
    ) -> "AsyncConversation":
        """Return an async buffered per-conversation ingest helper.

        Use with ``async with`` so buffered turns flush on exit. See
        :class:`memory_core_sdk.conversation.AsyncConversation`.
        """
        from .conversation import AsyncConversation  # late import breaks cycle
        return AsyncConversation(
            client=self,
            session_id=session_id,
            namespace=namespace,
            auto_flush_every=auto_flush_every,
        )

    async def get(self, memory_id: str, *, namespace: str | None = None) -> Memory | None:
        ns = namespace or self.namespace
        try:
            c = await self._http()
            r = await c.get(f"/api/v1/memories/{memory_id}", params={"namespace": ns})
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return Memory.from_dict(r.json())
        except httpx.HTTPStatusError as e:
            raise MemoryCoreError(f"get failed [{e.response.status_code}]: {e.response.text}") from e

    async def delete(self, memory_id: str, *, namespace: str | None = None) -> bool:
        ns = namespace or self.namespace
        try:
            c = await self._http()
            r = await c.delete(f"/api/v1/memories/{memory_id}", params={"namespace": ns})
            return r.status_code in (200, 204)
        except httpx.HTTPStatusError:
            return False

    async def health(self) -> dict[str, Any]:
        try:
            c = await self._http()
            r = await c.get("/health")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise MemoryCoreError(f"health check failed: {e}") from e

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncMemoryClient":
        await self._http()  # warm up connection
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
