from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.pipeline import Pipeline
from app.schemas.pipeline import PipelineCreate, PipelineRead, PipelineUpdate

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("", response_model=list[PipelineRead])
async def list_pipelines(session: AsyncSession = Depends(get_session)) -> list[Pipeline]:
    result = await session.execute(select(Pipeline).order_by(Pipeline.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=PipelineRead, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    payload: PipelineCreate,
    session: AsyncSession = Depends(get_session),
) -> Pipeline:
    pipeline = Pipeline(**payload.model_dump())
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)
    return pipeline


@router.get("/{pipeline_id}", response_model=PipelineRead)
async def get_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
) -> Pipeline:
    pipeline = await session.get(Pipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="pipeline not found")
    return pipeline


@router.patch("/{pipeline_id}", response_model=PipelineRead)
async def update_pipeline(
    pipeline_id: str,
    payload: PipelineUpdate,
    session: AsyncSession = Depends(get_session),
) -> Pipeline:
    pipeline = await session.get(Pipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="pipeline not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(pipeline, k, v)
    pipeline.updated_at = _now()
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)
    return pipeline


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    pipeline = await session.get(Pipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="pipeline not found")
    await session.delete(pipeline)
    await session.commit()
