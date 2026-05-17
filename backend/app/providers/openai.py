from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.providers.base import ChatMessage
from app.settings import settings


class OpenAIProvider:
    name = "openai"
    default_models: list[str] = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
    ]

    def _client(self):  # type: ignore[no-untyped-def]
        from openai import AsyncOpenAI

        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        return AsyncOpenAI(api_key=settings.openai_api_key)

    @staticmethod
    def _prepare(messages: list[ChatMessage], system: str) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        if system:
            out.append({"role": "system", "content": system})
        for m in messages:
            out.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        return out

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        system: str = "",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        client = self._client()
        msgs = self._prepare(messages, system)
        stream = await client.chat.completions.create(
            model=model,
            messages=msgs,  # type: ignore[arg-type]
            stream=True,
            max_tokens=int(kwargs.get("max_tokens", 1024)),
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        system: str = "",
        **kwargs: Any,
    ) -> str:
        client = self._client()
        msgs = self._prepare(messages, system)
        resp = await client.chat.completions.create(
            model=model,
            messages=msgs,  # type: ignore[arg-type]
            max_tokens=int(kwargs.get("max_tokens", 1024)),
        )
        return resp.choices[0].message.content or ""

    async def list_models(self) -> list[str]:
        return list(self.default_models)
