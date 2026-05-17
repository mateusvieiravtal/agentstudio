import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Background,
  Controls,
  ReactFlow,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
} from "@xyflow/react";

import { useAgents } from "@/api/agents";
import { usePipeline, useUpdatePipeline } from "@/api/pipelines";
import { useResumeRun, useStartRun } from "@/api/runs";
import { AgentNode } from "@/components/canvas/AgentNode";
import { HumanNode } from "@/components/canvas/HumanNode";
import { RouterNode } from "@/components/canvas/RouterNode";
import { RunStream } from "@/components/run/RunStream";
import { StepCard } from "@/components/run/StepCard";
import { AgentConfigPanel } from "@/components/panels/AgentConfigPanel";
import { useRunStore } from "@/stores/runStore";
import { usePipelineStore, type CanvasNodeData } from "@/stores/pipelineStore";
import type { Agent } from "@/types";

const nodeTypes = {
  agent: AgentNode,
  router: RouterNode,
  human: HumanNode,
};

function agentNodeType(a: Agent): keyof typeof nodeTypes {
  if (a.type === "ROUTER") return "router";
  if (a.type === "HUMAN") return "human";
  return "agent";
}

function makeData(a: Agent): CanvasNodeData {
  return {
    agent_id: a.id,
    name: a.name,
    type: a.type,
    provider: a.provider,
    model: a.model,
    runStatus: "idle",
    streamingToken: "",
  };
}

export function PipelineEditorPage() {
  const { id } = useParams<{ id: string }>();
  const { data: pipeline } = usePipeline(id);
  const { data: agents } = useAgents();
  const updatePipeline = useUpdatePipeline();
  const startRun = useStartRun();
  const resumeRun = useResumeRun();

  const [nodes, setNodes, onNodesChange] = useNodesState<Node<CanvasNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const setNodesStore = usePipelineStore((s) => s.setNodes);
  const setEdgesStore = usePipelineStore((s) => s.setEdges);
  const resetRunState = usePipelineStore((s) => s.resetRunState);
  const selectedNodeId = usePipelineStore((s) => s.selectedNodeId);
  const setSelectedNodeId = usePipelineStore((s) => s.setSelectedNodeId);

  const run = useRunStore((s) => ({
    runId: s.runId,
    status: s.status,
    output: s.output,
    error: s.error,
    steps: s.steps,
    stepOrder: s.stepOrder,
    humanPrompt: s.humanPrompt,
  }));
  const startRunStore = useRunStore((s) => s.startRun);
  const resetRunStore = useRunStore((s) => s.reset);
  const clearHuman = useRunStore((s) => s.clearHuman);

  useEffect(() => {
    if (!pipeline || !agents) return;
    const byId = new Map(agents.map((a) => [a.id, a]));
    const ns: Node<CanvasNodeData>[] = [];
    for (const n of pipeline.nodes) {
      const a = byId.get(n.agent_id);
      if (!a) continue;
      ns.push({
        id: n.id,
        type: agentNodeType(a),
        position: n.position ?? { x: 0, y: 0 },
        data: makeData(a),
      });
    }
    const es: Edge[] = pipeline.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.condition,
    }));
    setNodes(ns);
    setEdges(es);
    setNodesStore(ns);
    setEdgesStore(es);
  }, [pipeline, agents, setNodes, setEdges, setNodesStore, setEdgesStore]);

  const onConnect = useCallback(
    (conn: Connection) => setEdges((eds) => addEdge(conn, eds)),
    [setEdges],
  );

  const onPaneClick = useCallback(() => setSelectedNodeId(null), [setSelectedNodeId]);

  const addAgentToCanvas = useCallback(
    (agent: Agent) => {
      const nodeId = `n_${Math.random().toString(36).slice(2, 9)}`;
      const newNode: Node<CanvasNodeData> = {
        id: nodeId,
        type: agentNodeType(agent),
        position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
        data: makeData(agent),
      };
      setNodes((curr) => [...curr, newNode]);
    },
    [setNodes],
  );

  const onSave = () => {
    if (!pipeline) return;
    updatePipeline.mutate({
      id: pipeline.id,
      body: {
        nodes: nodes.map((n) => ({
          id: n.id,
          agent_id: (n.data as unknown as CanvasNodeData).agent_id,
          position: n.position,
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          condition: typeof e.label === "string" ? e.label : undefined,
        })),
      },
    });
  };

  const [runInput, setRunInput] = useState("");
  const [showRunModal, setShowRunModal] = useState(false);
  const onRun = () => {
    if (!pipeline) return;
    resetRunStore();
    resetRunState();
    startRun.mutate(
      { pipeline_id: pipeline.id, input: runInput },
      {
        onSuccess: (created) => {
          startRunStore(created.id);
          setShowRunModal(false);
        },
      },
    );
  };

  const [humanInput, setHumanInput] = useState("");
  const onResume = () => {
    if (!run.runId) return;
    resumeRun.mutate(
      { id: run.runId, input: humanInput },
      {
        onSuccess: () => {
          clearHuman();
          setHumanInput("");
        },
      },
    );
  };

  const orderedSteps = useMemo(
    () => run.stepOrder.map((sid) => run.steps[sid]).filter(Boolean),
    [run.stepOrder, run.steps],
  );

  return (
    <div className="h-full w-full flex flex-col">
      <header className="flex items-center justify-between px-4 py-2 border-b border-slate-200 bg-white">
        <div className="flex items-center gap-3">
          <Link to="/pipelines" className="text-sm text-slate-500 hover:underline">
            ← Pipelines
          </Link>
          <h1 className="font-medium">{pipeline?.name ?? "Loading…"}</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="rounded bg-slate-900 text-white text-sm px-3 py-1.5"
            onClick={onSave}
          >
            Save
          </button>
          <button
            className="rounded bg-emerald-600 text-white text-sm px-3 py-1.5"
            onClick={() => setShowRunModal(true)}
            disabled={!pipeline || nodes.length === 0}
          >
            Run
          </button>
        </div>
      </header>

      <div className="flex-1 flex">
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, n) => setSelectedNodeId(n.id)}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
          </ReactFlow>

          {agents && agents.length > 0 && (
            <div className="absolute top-2 left-2 z-10 bg-white shadow rounded p-2 text-xs space-y-1 max-h-72 overflow-auto">
              <div className="font-medium mb-1">Drag agent to canvas</div>
              {agents.map((a) => (
                <button
                  key={a.id}
                  className="block w-full text-left px-2 py-1 rounded hover:bg-slate-100"
                  onClick={() => addAgentToCanvas(a)}
                >
                  <span className="text-[10px] uppercase text-slate-400 mr-1">{a.type}</span>
                  {a.name}
                </button>
              ))}
            </div>
          )}

          {orderedSteps.length > 0 && (
            <div className="absolute right-2 top-2 bottom-2 z-10 w-80 bg-white shadow rounded p-3 overflow-auto space-y-2">
              <div className="text-xs font-medium text-slate-500">
                Run {run.runId?.slice(0, 8)} · {run.status}
              </div>
              {orderedSteps.map((s) => (
                <StepCard key={s.id} step={s} />
              ))}
              {run.error && (
                <div className="text-xs text-rose-700 bg-rose-50 rounded p-2">
                  {run.error}
                </div>
              )}
            </div>
          )}
        </div>

        <AgentConfigPanel
          selectedAgentId={
            selectedNodeId
              ? ((nodes.find((n) => n.id === selectedNodeId)?.data as
                  | CanvasNodeData
                  | undefined)?.agent_id ?? null)
              : null
          }
          onSelect={() => undefined}
        />
      </div>

      <RunStream runId={run.runId} />

      {showRunModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
          <div className="bg-white rounded-md p-4 w-[500px] space-y-3">
            <h3 className="font-medium">Run pipeline</h3>
            <textarea
              rows={4}
              className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
              placeholder="Initial input"
              value={runInput}
              onChange={(e) => setRunInput(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <button
                className="rounded px-3 py-1.5 text-sm"
                onClick={() => setShowRunModal(false)}
              >
                Cancel
              </button>
              <button
                className="rounded bg-emerald-600 text-white text-sm px-3 py-1.5"
                onClick={onRun}
              >
                Start
              </button>
            </div>
          </div>
        </div>
      )}

      {run.humanPrompt && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
          <div className="bg-white rounded-md p-4 w-[500px] space-y-3">
            <h3 className="font-medium">Human input required</h3>
            <p className="text-sm text-slate-700 whitespace-pre-wrap">
              {run.humanPrompt.prompt}
            </p>
            <textarea
              rows={4}
              className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
              value={humanInput}
              onChange={(e) => setHumanInput(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <button className="rounded px-3 py-1.5 text-sm" onClick={clearHuman}>
                Cancel
              </button>
              <button
                className="rounded bg-amber-600 text-white text-sm px-3 py-1.5"
                onClick={onResume}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
