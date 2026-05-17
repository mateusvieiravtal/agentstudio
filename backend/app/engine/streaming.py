from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass
class SSEEvent:
    event: str
    data: dict[str, Any]

    def to_payload(self) -> dict[str, str]:
        return {"event": self.event, "data": json.dumps(self.data, default=str)}


_END_SENTINEL: SSEEvent = SSEEvent(event="__end__", data={})


class SSEEmitter:
    """In-process pub/sub: one queue per run_id."""

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[SSEEvent]] = {}

    def _queue(self, run_id: str) -> asyncio.Queue[SSEEvent]:
        q = self._queues.get(run_id)
        if q is None:
            q = asyncio.Queue(maxsize=1024)
            self._queues[run_id] = q
        return q

    async def emit(self, run_id: str, event: str, data: dict[str, Any]) -> None:
        await self._queue(run_id).put(SSEEvent(event=event, data=data))

    async def close(self, run_id: str) -> None:
        await self._queue(run_id).put(_END_SENTINEL)

    def drop(self, run_id: str) -> None:
        self._queues.pop(run_id, None)

    async def stream(self, run_id: str) -> AsyncIterator[dict[str, str]]:
        queue = self._queue(run_id)
        try:
            while True:
                ev = await queue.get()
                if ev is _END_SENTINEL:
                    break
                yield ev.to_payload()
        finally:
            self.drop(run_id)


sse_emitter = SSEEmitter()
