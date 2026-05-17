from __future__ import annotations

from fastapi import APIRouter

from app.providers import AnthropicProvider, OllamaProvider, OpenAIProvider

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def list_providers() -> list[dict[str, list[str] | str]]:
    return [
        {"name": "anthropic", "models": AnthropicProvider().default_models},
        {"name": "openai", "models": OpenAIProvider().default_models},
        {"name": "ollama", "models": OllamaProvider().default_models},
    ]
