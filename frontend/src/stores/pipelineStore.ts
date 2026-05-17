import { create } from "zustand";
import type { Edge, Node } from "@xyflow/react";

type AgentRunStatus = "idle" | "running" | "done" | "failed" | "paused";

export interface CanvasNodeData {
  agent_id: string;
  name: string;
  type: string;
  provider: string;
  model: string;
  runStatus: AgentRunStatus;
  streamingToken: string;
  [key: string]: unknown;
}

interface PipelineState {
  nodes: Node<CanvasNodeData>[];
  edges: Edge[];
  selectedNodeId: string | null;
  isDirty: boolean;
  setNodes: (nodes: Node<CanvasNodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  markClean: () => void;
  markDirty: () => void;
  setNodeRunStatus: (nodeId: string, status: AgentRunStatus) => void;
  setNodeStreaming: (nodeId: string, token: string) => void;
  resetRunState: () => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  isDirty: false,
  setNodes: (nodes) => set({ nodes, isDirty: true }),
  setEdges: (edges) => set({ edges, isDirty: true }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  markClean: () => set({ isDirty: false }),
  markDirty: () => set({ isDirty: true }),
  setNodeRunStatus: (nodeId, status) =>
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...n.data, runStatus: status } }
          : n,
      ),
    })),
  setNodeStreaming: (nodeId, token) =>
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.id === nodeId
          ? {
              ...n,
              data: {
                ...n.data,
                streamingToken: (n.data.streamingToken + token).slice(-50),
                runStatus: "running",
              },
            }
          : n,
      ),
    })),
  resetRunState: () =>
    set((state) => ({
      nodes: state.nodes.map((n) => ({
        ...n,
        data: { ...n.data, runStatus: "idle", streamingToken: "" },
      })),
    })),
}));
