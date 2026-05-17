import { Handle, Position, type NodeProps } from "@xyflow/react";
import clsx from "clsx";
import type { CanvasNodeData } from "@/stores/pipelineStore";

interface RouterData extends CanvasNodeData {
  labels?: string[];
}

const STATUS_COLORS: Record<string, string> = {
  idle: "border-slate-300",
  running: "border-agent-running ring-2 ring-agent-running/30",
  done: "border-agent-done",
  failed: "border-agent-failed",
  paused: "border-agent-paused",
};

export function RouterNode({ data, selected }: NodeProps) {
  const d = data as unknown as RouterData;
  const labels = d.labels ?? [];
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
      <div className="text-xs uppercase tracking-wide text-violet-600">ROUTER</div>
      <div className="font-medium text-sm">{d.name}</div>
      <div className="text-[11px] text-slate-500">{labels.length} routes</div>
      {labels.length === 0 ? (
        <Handle type="source" position={Position.Bottom} />
      ) : (
        labels.map((label, idx) => (
          <Handle
            key={label}
            id={label}
            type="source"
            position={Position.Bottom}
            style={{ left: `${((idx + 1) * 100) / (labels.length + 1)}%` }}
          />
        ))
      )}
    </div>
  );
}
