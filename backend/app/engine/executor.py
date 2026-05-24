from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.engine.graph import PipelineGraph
from app.engine.memory import MessageMemory
from app.engine.runner import AgentRunner, HumanInputRequired
from app.engine.streaming import SSEEmitter, sse_emitter
from app.engine.working_memory import WorkingMemory, working_memory as _default_working_memory
from app.models.agent import Agent
from app.models.pipeline import Pipeline
from app.models.run import Run, RunStatus, RunStep, StepStatus

logger = structlog.get_logger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineExecutor:
    """Orchestrates a single run across a pipeline graph, with SSE emission."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        emitter: SSEEmitter | None = None,
        runner_factory=None,
        working_memory: WorkingMemory | None = None,
    ) -> None:
        self.session = session
        self.emitter = emitter or sse_emitter
        self._runner_factory = runner_factory
        self.working_memory = working_memory or _default_working_memory

    async def execute(self, run: Run) -> None:
        pipeline = await self._load_pipeline(run.pipeline_id)
        agents_by_id = await self._load_agents(pipeline)

        graph = PipelineGraph(pipeline.nodes, pipeline.edges)
        order = graph.topological_sort()

        memory = MessageMemory()
        runner = (self._runner_factory or self._default_runner)(
            run_id=run.id, emitter=self.emitter, memory=memory
        )
        # Inject working memory after construction so custom runner factories
        # used in tests don't need to declare the kwarg.
        runner.working_memory = self.working_memory

        run.status = RunStatus.RUNNING
        run.started_at = _now()
        await self._save(run)
        await self.emitter.emit(run.id, "run.started", {"run_id": run.id})
        await self.working_memory.set(run.id, "run_input", run.input)

        current_input = run.input
        try:
            executed_outputs: dict[str, str] = {}
            for node_id in order:
                node = graph.nodes[node_id]
                agent_id = node.get("agent_id") or node.get("data", {}).get("agent_id")
                if not agent_id or agent_id not in agents_by_id:
                    continue
                agent = agents_by_id[agent_id]

                node_input = _resolve_input(graph, node_id, executed_outputs, current_input)

                step = RunStep(
                    run_id=run.id,
                    agent_id=agent.id,
                    node_id=node_id,
                    status=StepStatus.RUNNING,
                    input=node_input,
                    started_at=_now(),
                )
                self.session.add(step)
                await self.session.commit()
                await self.session.refresh(step)
                await self.emitter.emit(
                    run.id,
                    "step.started",
                    {"step_id": step.id, "agent_id": agent.id, "node_id": node_id},
                )

                try:
                    result = await runner.run(
                        agent=agent, step_id=step.id, user_input=node_input
                    )
                except HumanInputRequired as exc:
                    step.status = StepStatus.PAUSED
                    step.ended_at = _now()
                    run.status = RunStatus.PAUSED
                    run.paused_step_id = step.id
                    await self._save_all(step, run)
                    await self.emitter.close(run.id)
                    logger.info("run_paused", run_id=run.id, step_id=exc.step_id)
                    return

                step.status = StepStatus.COMPLETED
                step.output = result.output
                step.ended_at = _now()
                await self._save(step)
                await self.emitter.emit(
                    run.id,
                    "step.completed",
                    {"step_id": step.id, "output": result.output},
                )

                executed_outputs[node_id] = result.output
                current_input = result.output
                await self.working_memory.set(run.id, f"step:{node_id}:output", result.output)

            run.status = RunStatus.COMPLETED
            run.output = current_input
            run.ended_at = _now()
            await self._save(run)
            await self.emitter.emit(
                run.id, "run.completed", {"run_id": run.id, "output": run.output}
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("run_failed", run_id=run.id)
            run.status = RunStatus.FAILED
            run.error = str(exc)
            run.ended_at = _now()
            await self._save(run)
            await self.emitter.emit(
                run.id, "run.failed", {"run_id": run.id, "error": str(exc)}
            )
        finally:
            await self.emitter.close(run.id)

    @staticmethod
    def _default_runner(*, run_id: str, emitter: SSEEmitter, memory: MessageMemory) -> AgentRunner:
        return AgentRunner(run_id=run_id, emitter=emitter, memory=memory)

    async def _load_pipeline(self, pipeline_id: str) -> Pipeline:
        stmt = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await self.session.execute(stmt)
        pipeline = result.scalar_one_or_none()
        if pipeline is None:
            raise ValueError(f"pipeline not found: {pipeline_id}")
        return pipeline

    async def _load_agents(self, pipeline: Pipeline) -> dict[str, Agent]:
        ids = {
            (n.get("agent_id") or n.get("data", {}).get("agent_id"))
            for n in pipeline.nodes
        }
        ids.discard(None)
        if not ids:
            return {}
        stmt = select(Agent).where(Agent.id.in_(ids))  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return {a.id: a for a in result.scalars().all()}

    async def _save(self, obj: Any) -> None:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

    async def _save_all(self, *objs: Any) -> None:
        for obj in objs:
            self.session.add(obj)
        await self.session.commit()
        for obj in objs:
            await self.session.refresh(obj)


def _resolve_input(
    graph: PipelineGraph,
    node_id: str,
    outputs: dict[str, str],
    initial_input: str,
) -> str:
    incoming = [e for e in graph.edges if e["target"] == node_id]
    if not incoming:
        return initial_input
    parts = [outputs.get(e["source"], "") for e in incoming]
    return "\n".join(p for p in parts if p)


async def load_run_for_execution(session: AsyncSession, run_id: str) -> Run | None:
    stmt = (
        select(Run)
        .options(selectinload(Run.steps))
        .where(Run.id == run_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
