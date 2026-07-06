"""CachePort interface.

Abstraction for a key/value cache (e.g. Redis). The application layer depends
on this port; the concrete implementation lives in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class CachePort(ABC):
    """A minimal key/value caching contract."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Return the cached value for a key, or None if absent."""

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """Store a value under a key with an optional TTL in seconds."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a key from the cache."""
