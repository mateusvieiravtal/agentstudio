import { useState } from "react";
import { Link } from "react-router-dom";
import {
  useCreatePipeline,
  useDeletePipeline,
  usePipelines,
} from "@/api/pipelines";

export function PipelineListPage() {
  const { data, isLoading } = usePipelines();
  const create = useCreatePipeline();
  const remove = useDeletePipeline();
  const [name, setName] = useState("");

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-semibold mb-4">AgentStudio</h1>
      <div className="mb-6 flex gap-2">
        <input
          className="flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm"
          placeholder="New pipeline name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="rounded bg-slate-900 text-white text-sm px-3 py-1.5"
          onClick={() => {
            if (!name.trim()) return;
            create.mutate(
              { name: name.trim() },
              { onSuccess: () => setName("") },
            );
          }}
          disabled={create.isPending}
        >
          Create
        </button>
      </div>

      {isLoading && <div className="text-slate-500">Loading…</div>}
      <ul className="divide-y divide-slate-200 rounded border border-slate-200 bg-white">
        {data?.map((p) => (
          <li key={p.id} className="flex items-center justify-between px-3 py-2">
            <Link to={`/pipelines/${p.id}`} className="text-sm hover:underline">
              <span className="font-medium">{p.name}</span>
              <span className="text-slate-500 ml-2">
                {p.nodes.length} nodes · {p.edges.length} edges
              </span>
            </Link>
            <button
              className="text-xs text-rose-600 hover:underline"
              onClick={() => remove.mutate(p.id)}
            >
              Delete
            </button>
          </li>
        ))}
        {data && data.length === 0 && (
          <li className="px-3 py-4 text-sm text-slate-500">No pipelines yet.</li>
        )}
      </ul>
    </div>
  );
}
