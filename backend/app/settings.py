from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="sqlite+aiosqlite:///./agentstudio.db",
        description="Async SQLAlchemy DB URL",
    )

    anthropic_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    ollama_base_url: str = Field(default="http://localhost:11434/v1")

    # LiteLLM gateway — set USE_LITELLM=true to route all LLM calls through LiteLLM.
    # Falls back to direct provider SDKs when false (default for local dev without keys).
    use_litellm: bool = Field(default=False)

    # L2 working memory — set REDIS_URL to use Redis; omit to use in-process dict.
    # In-process dict is fine for local single-process dev; Redis is required for
    # multi-process / multi-instance deployments.
    redis_url: str | None = Field(default=None)

    log_level: str = Field(default="INFO")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    api_prefix: str = Field(default="/api/v1")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
