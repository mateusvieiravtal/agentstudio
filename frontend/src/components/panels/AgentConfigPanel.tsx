import { useEffect, useState } from "react";
import { useAgents, useCreateAgent, useUpdateAgent } from "@/api/agents";
import type { Agent, AgentType } from "@/types";

interface Props {
  selectedAgentId: string | null;
  onSelect: (agentId: string | null) => void;
}

const TYPES: AgentType[] = ["LLM", "TOOL", "ROUTER", "HUMAN"];
const PROVIDERS = ["anthropic", "openai", "ollama"];

export function AgentConfigPanel({ selectedAgentId, onSelect }: Props) {
  const { data: agents } = useAgents();
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent();

  const selected = agents?.find((a) => a.id === selectedAgentId) ?? null;
  const [draft, setDraft] = useState<Agent | null>(selected);

  useEffect(() => {
    setDraft(selected);
  }, [selected]);

  return (
    <aside className="h-full w-80 shrink-0 border-l border-slate-200 bg-white p-4 overflow-auto">
      <h2 className="font-semibold mb-3">Agents</h2>

      <button
        className="mb-3 w-full rounded bg-slate-900 text-white text-sm py-1.5"
        onClick={() =>
          createAgent.mutate({
            name: "New Agent",
            type: "LLM",
            provider: "anthropic",
            model: "claude-sonnet-4-6",
          })
        }
      >
        + New agent
      </button>

      <ul className="space-y-1 mb-4">
        {agents?.map((a) => (
          <li key={a.id}>
            <button
              className={`w-full text-left px-2 py-1 rounded text-sm hover:bg-slate-100 ${
                selectedAgentId === a.id ? "bg-slate-100 font-medium" : ""
              }`}
              onClick={() => onSelect(a.id)}
            >
              <span className="text-xs uppercase text-slate-400 mr-2">{a.type}</span>
              {a.name}
            </button>
          </li>
        ))}
      </ul>

      {draft && (
        <div className="space-y-3 border-t border-slate-200 pt-3">
          <h3 className="text-sm font-medium">Edit</h3>
          <label className="block text-xs text-slate-500">
            Name
            <input
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </label>
          <label className="block text-xs text-slate-500">
            Type
            <select
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
              value={draft.type}
              onChange={(e) =>
                setDraft({ ...draft, type: e.target.value as AgentType })
              }
            >
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-xs text-slate-500">
            Provider
            <select
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
              value={draft.provider}
              onChange={(e) => setDraft({ ...draft, provider: e.target.value })}
            >
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-xs text-slate-500">
            Model
            <input
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
              value={draft.model}
              onChange={(e) => setDraft({ ...draft, model: e.target.value })}
            />
          </label>
          <label className="block text-xs text-slate-500">
            System prompt
            <textarea
              rows={5}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm font-mono"
              value={draft.system_prompt}
              onChange={(e) =>
                setDraft({ ...draft, system_prompt: e.target.value })
              }
            />
          </label>
          <button
            className="w-full rounded bg-blue-600 text-white text-sm py-1.5"
            onClick={() =>
              updateAgent.mutate({
                id: draft.id,
                body: {
                  name: draft.name,
                  type: draft.type,
                  provider: draft.provider,
                  model: draft.model,
                  system_prompt: draft.system_prompt,
                },
              })
            }
          >
            Save
          </button>
        </div>
      )}
    </aside>
  );
}
