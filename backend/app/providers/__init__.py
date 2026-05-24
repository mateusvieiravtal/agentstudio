from __future__ import annotations

from app.providers.anthropic import AnthropicProvider
from app.providers.base import ChatMessage, LLMProvider
from app.providers.litellm_provider import LiteLLMProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider


def get_provider(name: str) -> LLMProvider:
    """Return the LLM provider for *name*.

    When ``settings.use_litellm`` is True every provider is routed through
    LiteLLM so callers get unified cost-tracking, fallbacks, and budget caps.
    Direct SDK providers are used otherwise (simpler local dev without extras).
    """
    from app.settings import settings  # local import avoids circular dependency

    key = name.lower()
    if settings.use_litellm:
        return LiteLLMProvider(provider_name=key)

    if key == "anthropic":
        return AnthropicProvider()
    if key == "openai":
        return OpenAIProvider()
    if key == "ollama":
        return OllamaProvider()
    raise ValueError(f"unknown provider: {name}")


__all__ = [
    "AnthropicProvider",
    "ChatMessage",
    "LiteLLMProvider",
    "LLMProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "get_provider",
]
