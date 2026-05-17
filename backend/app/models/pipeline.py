from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class Pipeline(SQLModel, table=True):
    __tablename__ = "pipelines"

    id: str = Field(default_factory=_new_id, primary_key=True)
    name: str = Field(index=True, max_length=200)
    description: str = Field(default="")
    # nodes: [{ id: str, agent_id: str, position: {x, y} }]
    nodes: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    # edges: [{ id: str, source: str (node id), target: str, condition?: str }]
    edges: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
