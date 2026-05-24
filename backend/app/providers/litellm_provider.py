from __future__ import annotations

from typing import AsyncIterator

import litellm

from app.providers.base import ChatMessage

litellm.drop_params = True  # silently ignore unsupported kwargs per provider


_PROVIDER_PREFIX: dict[str, str] = {
    "anthropic": "anthropic",
    "openai": "openai",
    "ollama": "ollama",
    "gemini": "gemini",
    "vertex_ai": "vertex_ai",
}


class LiteLLMProvider:
    """LLM provider backed by LiteLLM — routes to any configured backend.

    Each instance is bound to a provider name (e.g. "anthropic") so it can
    construct the correct model string for LiteLLM (e.g. "anthropic/claude-sonnet-4-6").
    """

    def __init__(self, provider_name: str) -> None:
        self.name = provider_name
        self._prefix = _PROVIDER_PREFIX.get(provider_name.lower(), provider_name.lower())

    def _model(self, model: str) -> str:
        """Return the fully-qualified LiteLLM model string."""
        if "/" in model:
            return model  # already prefixed
        return f"{self._prefix}/{model}"

    @staticmethod
    def _build_messages(
        messages: list[ChatMessage], system: str
    ) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend({"role": m.role, "content": m.content} for m in messages)
        return msgs

    async def stream(
        self,
        messages: list[ChatMessage],
        model: str,
        system: str = "",
        **kwargs,
    ) -> AsyncIterator[str]:
        response = await litellm.acompletion(
            model=self._model(model),
            messages=self._build_messages(messages, system),
            stream=True,
            **kwargs,
        )
        async for chunk in response:
            token: str = chunk.choices[0].delta.content or ""
            if token:
                yield token

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str,
        system: str = "",
        **kwargs,
    ) -> str:
        response = await litellm.acompletion(
            model=self._model(model),
            messages=self._build_messages(messages, system),
            **kwargs,
        )
        return response.choices[0].message.content or ""

    async def list_models(self) -> list[str]:
        model_map: dict[str, list[str]] = {
            "anthropic": [
                "claude-opus-4-7",
                "claude-sonnet-4-6",
                "claude-haiku-4-5-20251001",
            ],
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "ollama": ["llama3.2", "qwen2.5", "mistral"],
            "gemini": ["gemini-2.0-flash", "gemini-2.0-pro"],
        }
        return model_map.get(self.name, [])
