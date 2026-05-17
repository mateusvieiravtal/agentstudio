from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.engine.memory import MessageMemory
from app.engine.streaming import SSEEmitter
from app.models.agent import Agent, AgentType
from app.providers import get_provider
from app.providers.base import LLMProvider


class HumanInputRequired(Exception):
    def __init__(self, step_id: str, prompt: str) -> None:
        self.step_id = step_id
        self.prompt = prompt
        super().__init__(prompt)


@dataclass
class RunnerResult:
    output: str
    route_label: str | None = None


class AgentRunner:
    """Dispatches per-agent execution logic by AgentType."""

    def __init__(
        self,
        *,
        run_id: str,
        emitter: SSEEmitter,
        memory: MessageMemory,
        provider_factory=get_provider,
    ) -> None:
        self.run_id = run_id
        self.emitter = emitter
        self.memory = memory
        self.provider_factory = provider_factory

    async def run(
        self,
        *,
        agent: Agent,
        step_id: str,
        user_input: str,
    ) -> RunnerResult:
        if agent.type == AgentType.HUMAN:
            return await self._run_human(agent=agent, step_id=step_id, prompt=user_input)
        if agent.type == AgentType.ROUTER:
            return await self._run_router(agent=agent, step_id=step_id, user_input=user_input)
        if agent.type == AgentType.TOOL:
            return await self._run_tool(agent=agent, step_id=step_id, user_input=user_input)
        return await self._run_llm(agent=agent, step_id=step_id, user_input=user_input)

    def _provider(self, agent: Agent) -> LLMProvider:
        return self.provider_factory(agent.provider)

    async def _run_llm(self, *, agent: Agent, step_id: str, user_input: str) -> RunnerResult:
        provider = self._provider(agent)
        self.memory.append("user", user_input)
        messages = self.memory.as_list()
        chunks: list[str] = []
        async for token in provider.stream(
            messages,
            model=agent.model,
            system=agent.system_prompt,
            **agent.config,
        ):
            chunks.append(token)
            await self.emitter.emit(
                self.run_id,
                "token",
                {"step_id": step_id, "token": token},
            )
        output = "".join(chunks)
        self.memory.append("assistant", output)
        return RunnerResult(output=output)

    async def _run_router(self, *, agent: Agent, step_id: str, user_input: str) -> RunnerResult:
        provider = self._provider(agent)
        labels: list[str] = list(agent.config.get("labels", []))
        sys_prompt = agent.system_prompt or (
            "You are a router. Pick exactly one label from this list that best "
            f"matches the user's input: {labels}. Reply with only the label."
        )
        messages = [{"role": "user", "content": user_input}]
        text = await provider.complete(
            messages,
            model=agent.model,
            system=sys_prompt,
        )
        label = text.strip().splitlines()[0].strip() if text else ""
        await self.emitter.emit(
            self.run_id,
            "token",
            {"step_id": step_id, "token": label},
        )
        return RunnerResult(output=label, route_label=label)

    async def _run_tool(self, *, agent: Agent, step_id: str, user_input: str) -> RunnerResult:
        provider = self._provider(agent)
        self.memory.append("user", user_input)
        max_iters = int(agent.config.get("max_iterations", 10))
        sys = (
            agent.system_prompt
            + "\n\nYou can call tools by emitting a JSON line of the form "
            '{"tool":"<name>","args":{...}}. When done, output a final answer.'
        )
        final_output = ""
        for _ in range(max_iters):
            text = await provider.complete(
                self.memory.as_list(),
                model=agent.model,
                system=sys,
            )
            await self.emitter.emit(
                self.run_id,
                "token",
                {"step_id": step_id, "token": text},
            )
            self.memory.append("assistant", text)
            tool_call = _try_parse_tool_call(text)
            if tool_call is None:
                final_output = text
                break
            tool_name, args = tool_call
            await self.emitter.emit(
                self.run_id,
                "tool.called",
                {"step_id": step_id, "tool": tool_name, "args": args},
            )
            result = _invoke_tool(tool_name, args, allowed=agent.tools)
            await self.emitter.emit(
                self.run_id,
                "tool.result",
                {"step_id": step_id, "tool": tool_name, "result": result},
            )
            self.memory.append("tool", f"{tool_name}: {result}")
        return RunnerResult(output=final_output)

    async def _run_human(self, *, agent: Agent, step_id: str, prompt: str) -> RunnerResult:
        message = agent.system_prompt or prompt or "Please provide input."
        await self.emitter.emit(
            self.run_id,
            "human.required",
            {"step_id": step_id, "prompt": message},
        )
        raise HumanInputRequired(step_id=step_id, prompt=message)


def _try_parse_tool_call(text: str) -> tuple[str, dict[str, Any]] | None:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or "tool" not in obj:
        return None
    return str(obj["tool"]), dict(obj.get("args", {}))


def _invoke_tool(name: str, args: dict[str, Any], *, allowed: list[str]) -> str:
    if name not in allowed:
        return f"error: tool '{name}' not allowed"
    if name == "echo":
        return str(args.get("text", ""))
    if name == "add":
        try:
            return str(float(args.get("a", 0)) + float(args.get("b", 0)))
        except (TypeError, ValueError) as exc:
            return f"error: {exc}"
    return f"error: tool '{name}' not implemented"
