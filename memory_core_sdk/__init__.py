"""
Memory Core SDK

Quickstart:
    from memory_core_sdk import MemoryClient

    mem = MemoryClient(namespace="my-project")
    mem.store("We chose FalkorDB for lower operational overhead.")
    results = mem.search("database decision")
    for r in results:
        print(r.content)

Async:
    from memory_core_sdk import AsyncMemoryClient

    async with AsyncMemoryClient(namespace="my-project") as mem:
        await mem.store("async context preserved")
        results = await mem.search("context")
"""

from .client import (
    AsyncMemoryClient,
    Memory,
    MemoryClient,
    MemoryCoreError,
    SearchResult,
)
from .conversation import AsyncConversation, Conversation

__version__ = "0.1.0"

__all__ = [
    "MemoryClient",
    "AsyncMemoryClient",
    "Memory",
    "SearchResult",
    "MemoryCoreError",
    "Conversation",
    "AsyncConversation",
]
