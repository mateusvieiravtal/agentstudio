from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent import AgentType


class AgentBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: AgentType = AgentType.LLM
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    system_prompt: str = ""
    tools: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: str | None = None
    type: AgentType | None = None
    provider: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    tools: list[str] | None = None
    config: dict[str, Any] | None = None


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
