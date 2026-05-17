import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: str = Field(default_factory=_new_id, primary_key=True)
    pipeline_id: str = Field(foreign_key="pipelines.id", index=True)
    status: RunStatus = Field(default=RunStatus.PENDING)
    input: str = Field(default="")
    output: str = Field(default="")
    error: Optional[str] = Field(default=None)
    paused_step_id: Optional[str] = Field(default=None)
    context: dict = Field(default_factory=dict, sa_column=Column(JSON))
    started_at: Optional[datetime] = Field(default=None)
    ended_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)

    steps: List["RunStep"] = Relationship(
        back_populates="run",
        sa_relationship_kwargs={"order_by": "RunStep.created_at"},
    )


class RunStep(SQLModel, table=True):
    __tablename__ = "run_steps"

    id: str = Field(default_factory=_new_id, primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    agent_id: str = Field(index=True)
    node_id: str = Field(default="")
    status: StepStatus = Field(default=StepStatus.PENDING)
    input: str = Field(default="")
    output: str = Field(default="")
    error: Optional[str] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    ended_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)

    run: Optional["Run"] = Relationship(back_populates="steps")


# Re-export for static typing; needed for Pydantic/SQLModel string-forward-refs.
Any  # noqa: B018
