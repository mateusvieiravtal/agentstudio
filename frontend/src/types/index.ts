export type AgentType = "LLM" | "TOOL" | "ROUTER" | "HUMAN";

export type RunStatus =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed";

export type StepStatus = RunStatus;

export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  provider: string;
  model: string;
  system_prompt: string;
  tools: string[];
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  type?: AgentType;
  provider?: string;
  model?: string;
  system_prompt?: string;
  tools?: string[];
  config?: Record<string, unknown>;
}

export interface PipelineNode {
  id: string;
  agent_id: string;
  position: { x: number; y: number };
}

export interface PipelineEdge {
  id: string;
  source: string;
  target: string;
  condition?: string;
}

export interface Pipeline {
  id: string;
  name: string;
  description: string;
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  created_at: string;
  updated_at: string;
}

export interface PipelineCreate {
  name: string;
  description?: string;
  nodes?: PipelineNode[];
  edges?: PipelineEdge[];
}

export interface RunStep {
  id: string;
  run_id: string;
  agent_id: string;
  node_id: string;
  status: StepStatus;
  input: string;
  output: string;
  error: string | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
}

export interface Run {
  id: string;
  pipeline_id: string;
  status: RunStatus;
  input: string;
  output: string;
  error: string | null;
  paused_step_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  steps: RunStep[];
}

export type SSEEventName =
  | "run.started"
  | "step.started"
  | "token"
  | "tool.called"
  | "tool.result"
  | "step.completed"
  | "human.required"
  | "run.completed"
  | "run.failed";

export interface ProviderInfo {
  name: string;
  models: string[];
}
