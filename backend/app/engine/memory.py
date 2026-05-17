from __future__ import annotations

from collections import deque

from app.providers.base import ChatMessage


class MessageMemory:
    """Sliding-window message memory shared across steps of a run."""

    def __init__(self, max_messages: int = 50) -> None:
        self._buf: deque[ChatMessage] = deque(maxlen=max_messages)

    def append(self, role: str, content: str) -> None:
        self._buf.append({"role": role, "content": content})

    def extend(self, messages: list[ChatMessage]) -> None:
        for m in messages:
            self._buf.append(m)

    def as_list(self) -> list[ChatMessage]:
        return list(self._buf)

    def clear(self) -> None:
        self._buf.clear()

    def __len__(self) -> int:
        return len(self._buf)
