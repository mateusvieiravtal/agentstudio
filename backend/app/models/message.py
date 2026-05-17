from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(default_factory=_new_id, primary_key=True)
    step_id: str = Field(foreign_key="run_steps.id", index=True)
    role: MessageRole
    content: str = Field(default="")
    tool_calls: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))
    tool_results: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_now)
