from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class AgentType(str, Enum):
    LLM = "LLM"
    TOOL = "TOOL"
    ROUTER = "ROUTER"
    HUMAN = "HUMAN"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: str = Field(default_factory=_new_id, primary_key=True)
    name: str = Field(index=True, max_length=200)
    type: AgentType = Field(default=AgentType.LLM)
    provider: str = Field(default="anthropic")
    model: str = Field(default="claude-sonnet-4-6")
    system_prompt: str = Field(default="")
    tools: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
