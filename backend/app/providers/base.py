from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, TypedDict


class ChatMessage(TypedDict, total=False):
    role: str
    content: str


class LLMProvider(Protocol):
    name: str

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        system: str = "",
        **kwargs: Any,
    ) -> AsyncIterator[str]: ...

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        system: str = "",
        **kwargs: Any,
    ) -> str: ...

    async def list_models(self) -> list[str]: ...
