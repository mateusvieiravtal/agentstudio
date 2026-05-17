from __future__ import annotations

from app.providers.anthropic import AnthropicProvider
from app.providers.base import ChatMessage, LLMProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider


def get_provider(name: str) -> LLMProvider:
    key = name.lower()
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
    "LLMProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "get_provider",
]
