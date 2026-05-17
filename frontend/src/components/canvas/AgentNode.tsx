import { Handle, Position, type NodeProps } from "@xyflow/react";
import clsx from "clsx";
import type { CanvasNodeData } from "@/stores/pipelineStore";

const STATUS_COLORS: Record<string, string> = {
  idle: "border-slate-300",
  running: "border-agent-running ring-2 ring-agent-running/30",
  done: "border-agent-done",
  failed: "border-agent-failed",
  paused: "border-agent-paused",
};

export function AgentNode({ data, selected }: NodeProps) {
  const d = data as unknown as CanvasNodeData;
  const status = d.runStatus ?? "idle";

  return (
    <div
      className={clsx(
        "rounded-md bg-white px-3 py-2 shadow-sm border-2 min-w-[180px]",
        STATUS_COLORS[status] ?? STATUS_COLORS.idle,
        selected && "ring-2 ring-blue-400",
      )}
    >
      <Handle type="target" position={Position.Top} />
      <div className="text-xs uppercase tracking-wide text-slate-500">{d.type}</div>
      <div className="font-medium text-sm">{d.name}</div>
      <div className="text-[11px] text-slate-500">
        {d.provider} / {d.model}
      </div>
      {status === "running" && d.streamingToken && (
        <div className="mt-1 text-[11px] text-slate-700 font-mono">
          <span>{d.streamingToken}</span>
          <span className="cursor-blink" />
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
