from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.providers.base import ChatMessage
from app.settings import settings


class AnthropicProvider:
    name = "anthropic"
    default_models: list[str] = [
        "claude-opus-4-7",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ]

    def _client(self):  # type: ignore[no-untyped-def]
        from anthropic import AsyncAnthropic

        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        return AsyncAnthropic(api_key=settings.anthropic_api_key)

    @staticmethod
    def _split_system(messages: list[ChatMessage], system: str) -> tuple[str, list[dict[str, Any]]]:
        sys_parts = [system] if system else []
        msgs: list[dict[str, Any]] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                sys_parts.append(content)
                continue
            msgs.append({"role": role, "content": content})
        return ("\n\n".join(p for p in sys_parts if p), msgs)

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        system: str = "",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        client = self._client()
        sys_str, msgs = self._split_system(messages, system)
        max_tokens = int(kwargs.get("max_tokens", 1024))
        async with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=sys_str,
            messages=msgs,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        system: str = "",
        **kwargs: Any,
    ) -> str:
        client = self._client()
        sys_str, msgs = self._split_system(messages, system)
        max_tokens = int(kwargs.get("max_tokens", 1024))
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=sys_str,
            messages=msgs,
        )
        parts: list[str] = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "".join(parts)

    async def list_models(self) -> list[str]:
        return list(self.default_models)
