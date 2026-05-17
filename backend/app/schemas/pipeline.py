from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PipelineBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)


class PipelineCreate(PipelineBase):
    pass


class PipelineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None


class PipelineRead(PipelineBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
