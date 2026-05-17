import clsx from "clsx";
import type { RunStepView } from "@/stores/runStore";

const STATUS_BADGE: Record<string, string> = {
  running: "bg-blue-100 text-blue-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-rose-100 text-rose-700",
  paused: "bg-amber-100 text-amber-700",
};

export function StepCard({ step }: { step: RunStepView }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3 text-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-xs text-slate-500">step {step.id.slice(0, 8)}</span>
        <span
          className={clsx(
            "rounded px-2 py-0.5 text-xs font-medium",
            STATUS_BADGE[step.status] ?? "bg-slate-100 text-slate-700",
          )}
        >
          {step.status}
        </span>
      </div>
      {step.tokens && (
        <pre className="whitespace-pre-wrap break-words text-xs text-slate-700">
          {step.tokens}
        </pre>
      )}
      {step.toolCalls.length > 0 && (
        <div className="mt-2 space-y-1">
          {step.toolCalls.map((tc, idx) => (
            <div key={idx} className="text-xs">
              <span className="font-mono text-violet-700">→ {tc.tool}</span>
              <span className="text-slate-500"> {JSON.stringify(tc.args)}</span>
              {tc.result !== undefined && (
                <div className="ml-3 text-emerald-700 font-mono">
                  {JSON.stringify(tc.result)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
