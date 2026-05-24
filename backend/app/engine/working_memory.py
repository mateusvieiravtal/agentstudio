from __future__ import annotations

import json
from typing import Any


class WorkingMemory:
    """In-process L2 working memory — zero-config fallback for local dev.

    Stores per-run key/value pairs in a plain dict. Data is lost when the
    process restarts. Use RedisWorkingMemory for any multi-process setup.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def set(self, run_id: str, key: str, value: Any) -> None:
        self._store.setdefault(run_id, {})[key] = value

    async def get(self, run_id: str, key: str) -> Any | None:
        return self._store.get(run_id, {}).get(key)

    async def get_all(self, run_id: str) -> dict[str, Any]:
        return dict(self._store.get(run_id, {}))

    async def delete_run(self, run_id: str) -> None:
        self._store.pop(run_id, None)


class RedisWorkingMemory(WorkingMemory):
    """Redis-backed L2 working memory for multi-process / staging / production.

    Each run is stored as a Redis hash at key ``run:{run_id}`` with a TTL
    (default 24 hours) so stale data is cleaned up automatically.
    """

    def __init__(self, redis_url: str, ttl_seconds: int = 86_400) -> None:
        import redis.asyncio as aioredis

        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds

    def _key(self, run_id: str) -> str:
        return f"run:{run_id}"

    async def set(self, run_id: str, key: str, value: Any) -> None:
        k = self._key(run_id)
        await self._redis.hset(k, key, json.dumps(value))
        await self._redis.expire(k, self._ttl)

    async def get(self, run_id: str, key: str) -> Any | None:
        raw = await self._redis.hget(self._key(run_id), key)
        return json.loads(raw) if raw is not None else None

    async def get_all(self, run_id: str) -> dict[str, Any]:
        raw = await self._redis.hgetall(self._key(run_id))
        return {k: json.loads(v) for k, v in raw.items()}

    async def delete_run(self, run_id: str) -> None:
        await self._redis.delete(self._key(run_id))


def create_working_memory(redis_url: str | None = None) -> WorkingMemory:
    if redis_url:
        return RedisWorkingMemory(redis_url)
    return WorkingMemory()


# Module-level singleton — imported by executor and routers.
# Initialised from settings so it is available before the FastAPI lifespan runs.
from app.settings import settings as _settings  # noqa: E402

working_memory: WorkingMemory = create_working_memory(_settings.redis_url)
