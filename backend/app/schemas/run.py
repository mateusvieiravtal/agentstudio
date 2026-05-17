from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.run import RunStatus, StepStatus


class RunCreate(BaseModel):
    pipeline_id: str
    input: str = ""


class RunResume(BaseModel):
    input: str


class RunStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    agent_id: str
    node_id: str
    status: StepStatus
    input: str
    output: str
    error: str | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pipeline_id: str
    status: RunStatus
    input: str
    output: str
    error: str | None
    paused_step_id: str | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    steps: list[RunStepRead] = []
