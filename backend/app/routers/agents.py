from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("", response_model=list[AgentRead])
async def list_agents(session: AsyncSession = Depends(get_session)) -> list[Agent]:
    result = await session.execute(select(Agent).order_by(Agent.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    session: AsyncSession = Depends(get_session),
) -> Agent:
    agent = Agent(**payload.model_dump())
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
) -> Agent:
    agent = await session.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    session: AsyncSession = Depends(get_session),
) -> Agent:
    agent = await session.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(agent, k, v)
    agent.updated_at = _now()
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    agent = await session.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    await session.delete(agent)
    await session.commit()
