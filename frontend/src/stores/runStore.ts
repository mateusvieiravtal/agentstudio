import { create } from "zustand";
import type { RunStatus } from "@/types";

export interface RunStepView {
  id: string;
  agent_id: string;
  node_id: string;
  status: "running" | "completed" | "failed" | "paused";
  tokens: string;
  toolCalls: { tool: string; args: unknown; result?: unknown }[];
}

interface RunState {
  runId: string | null;
  status: RunStatus;
  output: string;
  error: string | null;
  steps: Record<string, RunStepView>;
  stepOrder: string[];
  humanPrompt: { stepId: string; prompt: string } | null;

  startRun: (runId: string) => void;
  setStatus: (s: RunStatus) => void;
  beginStep: (stepId: string, agentId: string, nodeId: string) => void;
  appendToken: (stepId: string, token: string) => void;
  completeStep: (stepId: string, output: string) => void;
  recordToolCall: (stepId: string, tool: string, args: unknown) => void;
  recordToolResult: (stepId: string, tool: string, result: unknown) => void;
  requireHuman: (stepId: string, prompt: string) => void;
  clearHuman: () => void;
  completeRun: (output: string) => void;
  failRun: (error: string) => void;
  reset: () => void;
}

export const useRunStore = create<RunState>((set) => ({
  runId: null,
  status: "pending",
  output: "",
  error: null,
  steps: {},
  stepOrder: [],
  humanPrompt: null,

  startRun: (runId) =>
    set({ runId, status: "running", output: "", error: null, steps: {}, stepOrder: [], humanPrompt: null }),
  setStatus: (status) => set({ status }),

  beginStep: (stepId, agentId, nodeId) =>
    set((state) => ({
      steps: {
        ...state.steps,
        [stepId]: {
          id: stepId,
          agent_id: agentId,
          node_id: nodeId,
          status: "running",
          tokens: "",
          toolCalls: [],
        },
      },
      stepOrder: state.stepOrder.includes(stepId)
        ? state.stepOrder
        : [...state.stepOrder, stepId],
    })),
  appendToken: (stepId, token) =>
    set((state) => {
      const step = state.steps[stepId];
      if (!step) return state;
      return {
        steps: { ...state.steps, [stepId]: { ...step, tokens: step.tokens + token } },
      };
    }),
  completeStep: (stepId, output) =>
    set((state) => {
      const step = state.steps[stepId];
      if (!step) return state;
      return {
        steps: {
          ...state.steps,
          [stepId]: { ...step, status: "completed", tokens: output || step.tokens },
        },
      };
    }),
  recordToolCall: (stepId, tool, args) =>
    set((state) => {
      const step = state.steps[stepId];
      if (!step) return state;
      return {
        steps: {
          ...state.steps,
          [stepId]: { ...step, toolCalls: [...step.toolCalls, { tool, args }] },
        },
      };
    }),
  recordToolResult: (stepId, tool, result) =>
    set((state) => {
      const step = state.steps[stepId];
      if (!step) return state;
      const calls = [...step.toolCalls];
      for (let i = calls.length - 1; i >= 0; i--) {
        if (calls[i].tool === tool && calls[i].result === undefined) {
          calls[i] = { ...calls[i], result };
          break;
        }
      }
      return { steps: { ...state.steps, [stepId]: { ...step, toolCalls: calls } } };
    }),
  requireHuman: (stepId, prompt) =>
    set({ status: "paused", humanPrompt: { stepId, prompt } }),
  clearHuman: () => set({ humanPrompt: null }),
  completeRun: (output) => set({ status: "completed", output }),
  failRun: (error) => set({ status: "failed", error }),
  reset: () =>
    set({
      runId: null,
      status: "pending",
      output: "",
      error: null,
      steps: {},
      stepOrder: [],
      humanPrompt: null,
    }),
}));
