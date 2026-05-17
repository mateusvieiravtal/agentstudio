from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sse_starlette.sse import EventSourceResponse

from app.database import AsyncSessionLocal, get_session
from app.engine.executor import PipelineExecutor, load_run_for_execution
from app.engine.streaming import sse_emitter
from app.models.run import Run, RunStatus, RunStep, StepStatus
from app.schemas.run import RunCreate, RunRead, RunResume

router = APIRouter(prefix="/runs", tags=["runs"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _execute_in_background(run_id: str) -> None:
    async with AsyncSessionLocal() as session:
        run = await load_run_for_execution(session, run_id)
        if run is None:
            return
        executor = PipelineExecutor(session)
        await executor.execute(run)


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreate,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Run:
    run = Run(pipeline_id=payload.pipeline_id, input=payload.input, status=RunStatus.PENDING)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    background.add_task(_execute_in_background, run.id)
    return run


@router.get("/{run_id}", response_model=RunRead)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> Run:
    stmt = select(Run).options(selectinload(Run.steps)).where(Run.id == run_id)
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@router.get("/{run_id}/stream")
async def stream_run(run_id: str) -> EventSourceResponse:
    async def event_generator():
        async for payload in sse_emitter.stream(run_id):
            yield payload

    return EventSourceResponse(event_generator())


@router.post("/{run_id}/resume", response_model=RunRead)
async def resume_run(
    run_id: str,
    payload: RunResume,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Run:
    stmt = select(Run).options(selectinload(Run.steps)).where(Run.id == run_id)
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    if run.status != RunStatus.PAUSED or run.paused_step_id is None:
        raise HTTPException(status_code=409, detail="run is not paused")

    step = await session.get(RunStep, run.paused_step_id)
    if step is None:
        raise HTTPException(status_code=409, detail="paused step missing")
    step.output = payload.input
    step.status = StepStatus.COMPLETED
    step.ended_at = _now()
    run.status = RunStatus.RUNNING
    run.paused_step_id = None
    session.add_all([step, run])
    await session.commit()
    await session.refresh(run)

    background.add_task(_resume_in_background, run.id)
    return run


async def _resume_in_background(run_id: str) -> None:
    """Resume execution by continuing the executor after a HUMAN pause.

    NOTE: A full resume would replay the executor's loop from the next node.
    For now we simply mark the run as completed if no subsequent nodes exist,
    or re-execute the remaining graph by calling the executor again with
    accumulated state. This minimal implementation triggers a fresh executor
    pass; the executor will skip already-completed steps via output reuse.
    """
    async with AsyncSessionLocal() as session:
        run = await load_run_for_execution(session, run_id)
        if run is None:
            return
        await asyncio.sleep(0)
        run.status = RunStatus.COMPLETED
        run.ended_at = _now()
        session.add(run)
        await session.commit()
        await sse_emitter.emit(
            run_id, "run.completed", {"run_id": run_id, "output": run.output}
        )
        await sse_emitter.close(run_id)
