from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.engine.executor import PipelineExecutor
from app.engine.graph import CycleError, PipelineGraph
from app.engine.memory import MessageMemory
from app.engine.runner import AgentRunner
from app.engine.streaming import SSEEmitter
from app.models.agent import Agent, AgentType
from app.models.pipeline import Pipeline
from app.models.run import Run, RunStatus


def test_graph_topological_sort_linear() -> None:
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
    ]
    g = PipelineGraph(nodes, edges)
    assert g.topological_sort() == ["a", "b", "c"]


def test_graph_cycle_detection() -> None:
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [
        {"source": "a", "target": "b"},
        {"source": "b", "target": "a"},
    ]
    g = PipelineGraph(nodes, edges)
    with pytest.raises(CycleError):
        g.topological_sort()


class _FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.last_messages: list[dict[str, Any]] | None = None

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        system: str = "",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self.last_messages = messages
        for tok in ["hello", " ", "world"]:
            yield tok

    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        system: str = "",
        **kwargs: Any,
    ) -> str:
        return "ok"

    async def list_models(self) -> list[str]:
        return ["fake-1"]


def _fake_factory(_name: str) -> _FakeProvider:
    return _FakeProvider()


@pytest.mark.asyncio
async def test_runner_llm_emits_tokens() -> None:
    emitter = SSEEmitter()
    memory = MessageMemory()
    runner = AgentRunner(
        run_id="run1",
        emitter=emitter,
        memory=memory,
        provider_factory=_fake_factory,
    )
    agent = Agent(name="x", type=AgentType.LLM, provider="fake", model="fake-1")
    result = await runner.run(agent=agent, step_id="step1", user_input="hi")
    assert result.output == "hello world"

    received: list[str] = []
    await emitter.close("run1")
    async for payload in emitter.stream("run1"):
        received.append(payload["event"])
    assert received.count("token") == 3


@pytest.mark.asyncio
async def test_executor_runs_two_agent_pipeline(session) -> None:
    a1 = Agent(name="A1", type=AgentType.LLM, provider="fake", model="fake-1")
    a2 = Agent(name="A2", type=AgentType.LLM, provider="fake", model="fake-1")
    session.add_all([a1, a2])
    await session.commit()
    await session.refresh(a1)
    await session.refresh(a2)

    pipeline = Pipeline(
        name="P",
        nodes=[
            {"id": "n1", "agent_id": a1.id},
            {"id": "n2", "agent_id": a2.id},
        ],
        edges=[{"id": "e1", "source": "n1", "target": "n2"}],
    )
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)

    run = Run(pipeline_id=pipeline.id, input="hi")
    session.add(run)
    await session.commit()
    await session.refresh(run)

    emitter = SSEEmitter()

    def runner_factory(*, run_id: str, emitter: SSEEmitter, memory: MessageMemory) -> AgentRunner:
        return AgentRunner(
            run_id=run_id,
            emitter=emitter,
            memory=memory,
            provider_factory=_fake_factory,
        )

    executor = PipelineExecutor(session, emitter=emitter, runner_factory=runner_factory)
    await executor.execute(run)

    await session.refresh(run)
    assert run.status == RunStatus.COMPLETED
    assert run.output == "hello world"


@pytest.mark.asyncio
async def test_memory_append_and_window() -> None:
    mem = MessageMemory(max_messages=3)
    mem.append("user", "a")
    mem.append("assistant", "b")
    mem.append("user", "c")
    mem.append("assistant", "d")
    items = mem.as_list()
    assert len(items) == 3
    assert items[0]["content"] == "b"


@pytest.mark.asyncio
async def test_sse_emitter_round_trip() -> None:
    emitter = SSEEmitter()
    await emitter.emit("r1", "ping", {"v": 1})
    await emitter.emit("r1", "pong", {"v": 2})
    await emitter.close("r1")
    events = []
    async for payload in emitter.stream("r1"):
        events.append(payload["event"])
    assert events == ["ping", "pong"]
