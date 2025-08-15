from __future__ import annotations
import json
from typing import Any
from redis.asyncio import Redis

class Cache:
    def __init__(self, url: str, *, namespace: str = "app") -> None:
        self._r = Redis.from_url(url, decode_responses=True)
        self._ns = namespace

    def _k(self, key: str) -> str:
        return f"{self._ns}:{key}"

    async def get(self, key: str) -> str | None:
        return await self._r.get(self._k(key))

    async def set(self, key: str, value: str, ttl: int | float | None = None) -> None:
        await self._r.set(self._k(key), value, ex=ttl if ttl else None)

    async def delete(self, key: str) -> None:
        await self._r.delete(self._k(key))

    async def get_json(self, key: str) -> Any:
        raw = await self.get(key)
        return None if raw is None else json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl: int | float | None = None) -> None:
        await self.set(key, json.dumps(value, ensure_ascii=False), ttl)

    async def close(self) -> None:
        await self._r.close()
