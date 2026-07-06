"""Redis implementation of the CachePort application interface."""

from __future__ import annotations

from redis import asyncio as aioredis

from src.application.ports.cache_port import CachePort
from src.infrastructure.config import settings


class RedisCache(CachePort):
    """A thin adapter over the async Redis client."""

    def __init__(self, redis_url: str | None = None) -> None:
        self._client = aioredis.from_url(
            redis_url or settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(
        self, key: str, value: str, ttl_seconds: int | None = None
    ) -> None:
        await self._client.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def close(self) -> None:
        await self._client.aclose()
