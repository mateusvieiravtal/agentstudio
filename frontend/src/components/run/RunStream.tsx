import { useEffect } from "react";
import { runStreamUrl } from "@/api/runs";
import { useRunStore } from "@/stores/runStore";
import { usePipelineStore } from "@/stores/pipelineStore";

interface Props {
  runId: string | null;
}

export function RunStream({ runId }: Props) {
  const beginStep = useRunStore((s) => s.beginStep);
  const appendToken = useRunStore((s) => s.appendToken);
  const completeStep = useRunStore((s) => s.completeStep);
  const recordToolCall = useRunStore((s) => s.recordToolCall);
  const recordToolResult = useRunStore((s) => s.recordToolResult);
  const requireHuman = useRunStore((s) => s.requireHuman);
  const completeRun = useRunStore((s) => s.completeRun);
  const failRun = useRunStore((s) => s.failRun);

  const setNodeRunStatus = usePipelineStore((s) => s.setNodeRunStatus);
  const setNodeStreaming = usePipelineStore((s) => s.setNodeStreaming);

  useEffect(() => {
    if (!runId) return;

    const stepToNode = new Map<string, string>();
    const es = new EventSource(runStreamUrl(runId));

    const safeJson = <T,>(raw: string): T | null => {
      try {
        return JSON.parse(raw) as T;
      } catch {
        return null;
      }
    };

    es.addEventListener("step.started", (ev) => {
      const data = safeJson<{ step_id: string; agent_id: string; node_id: string }>(
        (ev as MessageEvent).data,
      );
      if (!data) return;
      stepToNode.set(data.step_id, data.node_id);
      beginStep(data.step_id, data.agent_id, data.node_id);
      if (data.node_id) setNodeRunStatus(data.node_id, "running");
    });

    es.addEventListener("token", (ev) => {
      const data = safeJson<{ step_id: string; token: string }>((ev as MessageEvent).data);
      if (!data) return;
      appendToken(data.step_id, data.token);
      const nodeId = stepToNode.get(data.step_id);
      if (nodeId) setNodeStreaming(nodeId, data.token);
    });

    es.addEventListener("tool.called", (ev) => {
      const data = safeJson<{ step_id: string; tool: string; args: unknown }>(
        (ev as MessageEvent).data,
      );
      if (!data) return;
      recordToolCall(data.step_id, data.tool, data.args);
    });

    es.addEventListener("tool.result", (ev) => {
      const data = safeJson<{ step_id: string; tool: string; result: unknown }>(
        (ev as MessageEvent).data,
      );
      if (!data) return;
      recordToolResult(data.step_id, data.tool, data.result);
    });

    es.addEventListener("step.completed", (ev) => {
      const data = safeJson<{ step_id: string; output: string }>((ev as MessageEvent).data);
      if (!data) return;
      completeStep(data.step_id, data.output);
      const nodeId = stepToNode.get(data.step_id);
      if (nodeId) setNodeRunStatus(nodeId, "done");
    });

    es.addEventListener("human.required", (ev) => {
      const data = safeJson<{ step_id: string; prompt: string }>((ev as MessageEvent).data);
      if (!data) return;
      requireHuman(data.step_id, data.prompt);
      const nodeId = stepToNode.get(data.step_id);
      if (nodeId) setNodeRunStatus(nodeId, "paused");
    });

    es.addEventListener("run.completed", (ev) => {
      const data = safeJson<{ output: string }>((ev as MessageEvent).data);
      completeRun(data?.output ?? "");
      es.close();
    });

    es.addEventListener("run.failed", (ev) => {
      const data = safeJson<{ error: string }>((ev as MessageEvent).data);
      failRun(data?.error ?? "unknown error");
      es.close();
    });

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [
    runId,
    beginStep,
    appendToken,
    completeStep,
    recordToolCall,
    recordToolResult,
    requireHuman,
    completeRun,
    failRun,
    setNodeRunStatus,
    setNodeStreaming,
  ]);

  return null;
}
