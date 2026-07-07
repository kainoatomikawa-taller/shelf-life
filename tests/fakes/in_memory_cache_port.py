"""In-memory CachePort for fast, isolated tests. Ignores TTLs — tests that
care about expiry should assert on `set` calls instead."""

from __future__ import annotations

from src.application.ports.cache_port import CachePort


class InMemoryCachePort(CachePort):
    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._values.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        self._values[key] = value

    async def delete(self, key: str) -> None:
        self._values.pop(key, None)
