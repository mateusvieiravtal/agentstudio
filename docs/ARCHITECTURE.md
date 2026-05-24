# AgentStudio — Technical Architecture Document

| Field       | Value                                      |
|-------------|--------------------------------------------|
| Version     | 0.2 — ADRs resolved                       |
| Status      | **PENDING APPROVAL**                       |
| Date        | 2026-05-24                                 |
| Owner       | VTAL Engineering                          |
| Repository  | `mateusvieiravtal/agentstudio`             |
| Branch      | `claude/sleepy-ramanujan-orXJu`            |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Context & Problem Statement](#2-context--problem-statement)
3. [Goals & Non-Goals](#3-goals--non-goals)
4. [Architecture Principles](#4-architecture-principles)
5. [System Overview](#5-system-overview)
6. [Layer Specifications](#6-layer-specifications)
   - [L0 — Agent Identity & Registry](#l0--agent-identity--registry)
   - [L1 — LLM Gateway](#l1--llm-gateway)
   - [L2 — Memory Subsystem](#l2--memory-subsystem)
   - [L3 — Tools (MCP Layer)](#l3--tools-mcp-layer)
   - [L4 — Skills (Native Capabilities)](#l4--skills-native-capabilities)
   - [L5 — A2A Communication Bus](#l5--a2a-communication-bus)
   - [L6 — Digital Squad — Software Factory](#l6--digital-squad--software-factory)
   - [L7 — Orchestration](#l7--orchestration)
   - [L8 — Guardrails & Safety](#l8--guardrails--safety)
   - [L9 — Observability & LLMOps](#l9--observability--llmops)
7. [Technology Stack Summary](#7-technology-stack-summary)
8. [Infrastructure — GCP Services Map](#8-infrastructure--gcp-services-map)
9. [Data Architecture](#9-data-architecture)
10. [Security & Compliance](#10-security--compliance)
11. [CI/CD & DevOps](#11-cicd--devops)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [Cost Model](#13-cost-model)
14. [Open Decisions & ADRs](#14-open-decisions--adrs)
15. [Appendix — Current Codebase (Phase 1–3)](#15-appendix--current-codebase-phase-13)

---

## 1. Executive Summary

AgentStudio is a visual, no-code/low-code platform for designing, deploying, and operating **Digital Squads** — coordinated teams of AI agents that execute business workflows autonomously. Rather than single-agent chatbots, Digital Squads are purpose-built ensembles of specialized agents that collaborate through a defined communication protocol, share memory, invoke external tools, and escalate to humans only when required.

The first squad to be deployed is the **Digital Software Factory**: a squad capable of taking a product requirement from specification to working, tested, and reviewed code — functioning as a force multiplier for VTAL's engineering capacity.

This document specifies the full technical architecture for AgentStudio and the agent runtime that powers all squads. It covers technology choices, GCP infrastructure, data design, security, observability, and a phased implementation roadmap. It is written for technical approval prior to development investment.

---

## 2. Context & Problem Statement

VTAL's engineering teams face growing demand for software delivery that outpaces headcount growth. AI-assisted coding tools (Copilot, Claude Code) provide individual productivity gains, but they are **ad-hoc and single-agent** — they do not coordinate, do not remember past decisions, and do not enforce company conventions autonomously.

What is needed is a system where:

- Multiple AI agents with complementary specializations work together on a shared codebase
- Each agent has persistent memory of the project, its decisions, and its outcomes
- Agents communicate asynchronously without requiring a human to relay information
- Humans retain control at defined checkpoints (approval gates, code reviews)
- The system is auditable, cost-controlled, and observable from day one

The existing AgentStudio codebase (Phases 1–3) provides a working foundation: a visual pipeline editor, a DAG-based execution engine, SSE streaming, and multi-provider LLM support. This architecture document defines the production-grade extensions required to support real Digital Squads.

---

## 3. Goals & Non-Goals

### Goals

- Define a production-ready agent runtime architecture for GCP
- Specify concrete vendor/technology choices per layer (no ambiguity)
- Enable the Digital Software Factory squad as the first live squad
- Ensure cost observability and budget controls from day one
- Maintain a clean extension path: new squads require only new skill/agent definitions, not new infrastructure
- Preserve existing AgentStudio UX and pipeline model as the authoring surface

### Non-Goals

- Building a general-purpose AI research platform
- Supporting non-GCP primary deployments (edge, on-premises) in v1
- Fine-tuning or training custom models
- Replacing GitHub as the source of truth for code
- Real-time voice/audio interfaces (not in scope for v1)

---

## 4. Architecture Principles

**1. Contracts first, infrastructure second.**
Each layer is defined by the interface it exposes — not the underlying technology. This allows component replacement without cascading rewrites.

**2. Skills ≠ Tools.**
Native capabilities (how an agent reasons, generates code, or decomposes a plan) are distinct from external integrations (GitHub, Cloud Build, web search). This distinction drives composability: skills are bundled with the agent; tools are discovered at runtime from the registry.

**3. Every agent has an identity, a scope, and a budget.**
No agent runs anonymously. Every invocation is bound to a service account, a memory scope, and a token budget. This is the foundation for both security and cost control.

**4. Memory is tiered, not flat.**
Working scratchpad, past decisions, and organizational knowledge have different access patterns, lifetimes, and storage requirements. A single "memory" blob collapses these distinctions and creates scaling problems.

**5. The A2A bus is the single nervous system.**
Agent-to-agent communication flows exclusively through the A2A bus (Pub/Sub + Cloud Tasks). No direct agent-to-agent HTTP calls outside of within a single pipeline step. This ensures auditability and enables async, distributed operation.

**6. Humans are first-class actors.**
Human-in-the-loop is not an exception path. Approval gates, review requests, and escalations are defined workflow nodes, not workarounds.

**7. Optimize for GCP, do not vendor-lock blindly.**
Where GCP-native services provide meaningful operational advantage (AlloyDB, Memorystore, Vertex AI, Pub/Sub), use them. Where OSS tooling is significantly better (LiteLLM, OpenTelemetry, MCP), use OSS and run it on GCP infrastructure.

---

## 5. System Overview

AgentStudio has two surfaces:

- **Authoring Surface**: The visual canvas where humans design squad compositions, agent configurations, and pipeline graphs. This is the existing React + @xyflow/react frontend.
- **Agent Runtime**: The backend infrastructure that executes squads, manages memory, routes LLM calls, invokes tools, and handles communication between agents.

The runtime is structured in 10 layers. Layers 0–5 are infrastructure shared by all squads. Layers 6–9 are squad-specific or cross-cutting operational concerns.

```
┌─────────────────────────────────────────────────────────────┐
│  HUMAN INTERFACE                                            │
│  AgentStudio Canvas · HITL Gates · Observability UI        │
├─────────────────────────────────────────────────────────────┤
│  L7  ORCHESTRATION                                          │
│  Squad Manager · Planner Agent · Task Router               │
├─────────────────────────────────────────────────────────────┤
│  L6  DIGITAL SQUAD                                          │
│  PM · Architect · BE · FE · QA · Security · DevOps · TW    │
├─────────────────────────────────────────────────────────────┤
│  L5  A2A COMMUNICATION BUS                                  │
│  Pub/Sub · Cloud Tasks · Direct HTTP                        │
├──────────────────┬──────────────────┬───────────────────────┤
│  L2  MEMORY      │  L3 TOOLS        │  L8  GUARDRAILS       │
│  L1 In-Context   │  MCP Registry    │  Cost · Security      │
│  L2 Working      │  GitHub · Code   │  Scope · Output       │
│  L3 Episodic     │  Executor · Web  │                       │
│  L4 Semantic     │  L4 SKILLS       │  L9  OBSERVABILITY    │
│  L5 Org Context  │  Native Caps     │  Trace · Monitor      │
│                  │  Skill Registry  │  Logging · LLMOps     │
├──────────────────┴──────────────────┴───────────────────────┤
│  L1  LLM GATEWAY                                            │
│  LiteLLM · Vertex AI Model Garden · OpenAI · Ollama        │
├─────────────────────────────────────────────────────────────┤
│  L0  AGENT IDENTITY & REGISTRY                              │
│  GCP Agent Platform · IAM · Workload Identity              │
├─────────────────────────────────────────────────────────────┤
│  GCP FOUNDATION                                             │
│  Cloud Run · GKE · AlloyDB · Memorystore · Pub/Sub · etc.  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Layer Specifications

---

### L0 — Agent Identity & Registry

**Purpose:** Every agent in the system has a machine-readable identity that declares what it is, what it can do, and what it is allowed to access. The registry is the single source of truth for agent discovery.

#### Components

| Component | Product | Vendor |
|-----------|---------|--------|
| Agent Registry | Vertex AI Agent Builder (GCP Agent Platform) | Google Cloud |
| Agent Identity Card | A2A Protocol `AgentCard` spec | Google OSS |
| Service Identity | Workload Identity Federation + Service Account per agent | Google Cloud |
| Secrets & Credentials | Secret Manager | Google Cloud |
| IAM Scoping | IAM roles with least-privilege per agent | Google Cloud |

#### Agent Card Structure

Each registered agent exposes a capability manifest conforming to the Google A2A spec:

```json
{
  "id": "backend-engineer-v1",
  "name": "Backend Engineer",
  "version": "1.0.0",
  "skills": ["code_generation", "test_generation", "code_review"],
  "tools_allowed": ["github_tool", "code_executor_tool", "search_tool"],
  "model_preference": "claude-sonnet",
  "memory_read_scope": ["project_context", "episodic", "semantic"],
  "memory_write_scope": ["working", "episodic"],
  "cost_budget_tokens": 100000,
  "guardrail_profile": "code_safety_strict"
}
```

#### Rationale

GCP Agent Platform provides native integration with Vertex AI and the A2A protocol, avoiding the need to build and operate a custom registry service. Workload Identity eliminates static service account key management — agents authenticate as their GCP service account without any credentials in environment variables.

---

### L1 — LLM Gateway

**Purpose:** A single, model-agnostic entry point for all LLM calls in the system. Routes requests to the optimal model based on task type, cost budget, latency SLA, and provider availability. All agents call the gateway — never a provider directly.

#### Components

| Component | Product | Vendor |
|-----------|---------|--------|
| LLM Router / Proxy | LiteLLM (self-hosted on Cloud Run) | OSS |
| Primary Platform | Vertex AI Model Garden | Google Cloud |
| Primary Model (reasoning/code) | Claude Sonnet via Vertex AI partner model | Anthropic via GCP |
| Primary Model (fast/cheap) | Gemini 2.0 Flash | Google |
| Primary Model (heavy reasoning) | Claude Opus via Vertex AI | Anthropic via GCP |
| Fallback | OpenAI GPT-4o | OpenAI |
| Private/Local | Ollama (internal network) | Meta / OSS |

#### Routing Policy

LiteLLM evaluates per-request routing using a policy defined in configuration (not in agent code):

```yaml
model_list:
  - model_name: "fast"
    litellm_params:
      model: vertex_ai/gemini-2.0-flash
      budget_limit: 0.01    # USD per request
  - model_name: "standard"
    litellm_params:
      model: vertex_ai/claude-sonnet-4-6
      budget_limit: 0.10
  - model_name: "reasoning"
    litellm_params:
      model: vertex_ai/claude-opus-4-7
      budget_limit: 1.00
  - model_name: "fallback"
    litellm_params:
      model: gpt-4o
      fallback_models: ["ollama/llama3.2"]
```

Routing signals (evaluated in order):
1. Agent's `model_preference` from Agent Card
2. Remaining `cost_budget_tokens` for the current run
3. Current provider rate-limit status (tracked in Redis)
4. Latency SLA of the current task (`realtime` vs `batch`)

#### Rationale

Calling providers directly (current Phase 1–3 approach) creates coupling: model changes, key rotation, and cost monitoring all require touching agent code. LiteLLM solves this at the infrastructure level with zero agent-code changes. Running it on GCP Cloud Run keeps all API egress within GCP's billing perimeter. Using Vertex AI as the primary platform means Claude and Gemini calls are billed and audited through a single GCP invoice.

---

### L2 — Memory Subsystem

**Purpose:** Provide agents with the right type of memory for each use case: fast ephemeral scratch space, structured history, vector-searchable knowledge, and shared project context.

#### Memory Tiers

| Tier | Name | Storage | TTL | Scope | Use Case |
|------|------|---------|-----|-------|----------|
| L1 | In-Context | LLM context window | Request | Per-agent | Active conversation, immediate reasoning |
| L2 | Working Memory | Cloud Memorystore (Redis 7) | Run lifetime | Per-run | Shared scratchpad between agents in a squad session |
| L3 | Episodic Memory | AlloyDB | Indefinite | Per-project | Past runs, decisions made, outcomes, errors |
| L4 | Semantic Memory | AlloyDB pgvector + Vertex AI Vector Search | Indefinite | Per-project | Embeddings of code, docs, architecture patterns |
| L5 | Org/Project Context | AlloyDB | Indefinite | Per-org / Per-project | Tech stack conventions, team standards, open tasks, decision log |

#### Technology Choices

| Component | Product | Vendor | Justification |
|-----------|---------|--------|---------------|
| Working Memory (L2) | Cloud Memorystore for Redis 7 | Google Cloud | Sub-millisecond reads, TTL native, Redis data structures (lists, hashes, sorted sets) map cleanly to conversation buffers and run state |
| Episodic + Semantic (L3/L4/L5) | AlloyDB for PostgreSQL | Google Cloud | PostgreSQL-compatible (uses existing SQLModel/Alembic), built-in pgvector extension for vector similarity, Cloud SQL Auth Proxy for IAM auth, no separate vector DB to operate |
| Embedding Model | `text-embedding-004` via Vertex AI | Google Cloud | Native GCP, 768-dim embeddings, optimized for code + text |

#### AlloyDB Schema (Memory Tables)

```sql
-- Episodic: structured run history
CREATE TABLE run_memory (
  id UUID PRIMARY KEY,
  project_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  action TEXT NOT NULL,           -- "code_written", "decision_made", "error_encountered"
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Semantic: vectorized knowledge
CREATE TABLE knowledge_chunks (
  id UUID PRIMARY KEY,
  project_id TEXT NOT NULL,
  source TEXT NOT NULL,           -- "codebase", "docs", "decision_log"
  content TEXT NOT NULL,
  embedding vector(768),          -- pgvector
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops);

-- Org/Project Context (L5)
CREATE TABLE project_context (
  id UUID PRIMARY KEY,
  project_id TEXT NOT NULL UNIQUE,
  org_id TEXT NOT NULL,
  tech_stack JSONB,              -- {"language": "Python", "framework": "FastAPI", ...}
  conventions JSONB,             -- coding standards, naming rules
  open_tasks JSONB,              -- current sprint tasks
  decision_log JSONB[],          -- ADRs, key decisions
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### Rationale: AlloyDB over Vertex AI Vector Search

Vertex AI Vector Search (Matching Engine) is purpose-built for billion-scale ANN search with very low latency. For the Software Factory use case, however, queries frequently combine structured filters with vector similarity (`find similar past bugs WHERE resolved = true AND component = 'payments'`). AlloyDB with pgvector handles this natively in SQL. We should migrate to Vertex Vector Search only when pgvector index rebuild times or query latency become bottlenecks (typically >50M vectors).

---

### L3 — Tools (MCP Layer)

**Purpose:** Provide agents with access to external capabilities (APIs, services, systems) through a standardized, audited, and permission-scoped interface.

#### Protocol

All tools use the **Model Context Protocol (MCP)** by Anthropic as the wire standard. MCP defines tool manifests (name, description, input/output schema) in a format that Claude natively understands, and is becoming the industry standard for agent tool interfaces.

#### Components

| Component | Product | Vendor |
|-----------|---------|--------|
| Tool Protocol | MCP (Model Context Protocol) | Anthropic OSS |
| Tool Runtime | Cloud Run (one service per tool group) | Google Cloud |
| Tool Auth | Workload Identity + Secret Manager | Google Cloud |
| Tool Registry | Custom Cloud Run service (Firestore-backed catalog) | Internal / GCP |
| Tool Invocation Logging | Cloud Logging + BigQuery export | Google Cloud |

#### Core Tools — Software Factory

| Tool | Implementation | Access |
|------|---------------|--------|
| `github_tool` | Cloud Run → GitHub API (REST + GraphQL) | Read/write repos, PRs, issues, branches |
| `code_executor_tool` | Cloud Run → Cloud Run Jobs (ephemeral sandbox) | Run code, return stdout/stderr, resource-capped |
| `web_search_tool` | Cloud Run → Vertex AI Search or Tavily API | External search, internal docs search |
| `cloud_build_tool` | Cloud Run → Cloud Build API | Trigger builds, fetch logs, check status |
| `test_runner_tool` | Cloud Run → Cloud Run Jobs | Run test suites, return results |
| `diagram_tool` | Cloud Run → Mermaid/PlantUML renderer | Generate architecture diagrams |
| `secret_reader_tool` | Cloud Run → Secret Manager (read-only, scoped) | Fetch non-sensitive config values |

#### Tool Registry Contract

The Tool Registry is a lightweight Cloud Run service that agents query at startup:

```
GET /tools?agent_id=backend-engineer-v1
→ Returns list of tool manifests this agent is permitted to call

POST /tools/{tool_name}/invoke
  Body: { "args": {...}, "agent_id": "...", "run_id": "...", "step_id": "..." }
→ Routes to tool, logs invocation, returns result
```

All tool invocations are logged with: `agent_id`, `run_id`, `tool_name`, `args` (redacted if sensitive), `result_summary`, `latency_ms`, `timestamp`.

#### Rationale

MCP is the right protocol because Claude natively generates MCP-formatted tool calls — no adapter layer needed. Running tools as independent Cloud Run services means: independent deployment, independent scaling, fault isolation, and clean IAM boundaries. The centralized Tool Registry prevents tool sprawl and gives security teams a single audit surface.

---

### L4 — Skills (Native Capabilities)

**Purpose:** Define the innate, built-in capabilities of an agent — what it can do through reasoning alone, without external tool calls. Skills are part of the agent's identity; tools are external integrations it can invoke.

#### Skill vs. Tool Distinction

| Aspect | Skill | Tool |
|--------|-------|------|
| Where it runs | Inside the agent's LLM call | External Cloud Run service |
| How it's invoked | Via system prompt + prompt engineering | Via MCP tool call |
| Examples | Decompose a task into subtasks, generate a test suite, review code for bugs | Call GitHub API, run code in sandbox, search the web |
| Versioning | Via Skill Registry (system prompt templates) | Via tool service deployment |

#### Core Skills — Software Factory

| Skill ID | Description |
|----------|-------------|
| `deep_reasoning` | Chain-of-Thought and ReAct loops for multi-step problems |
| `code_generation` | Write production-quality code in target language/framework |
| `code_review` | Identify bugs, security issues, style violations in a diff |
| `test_generation` | Write unit, integration, and e2e tests from code or spec |
| `plan_decomposition` | Break a high-level goal into ordered, assignable subtasks |
| `doc_writing` | Write technical documentation, ADRs, API docs, READMEs |
| `data_analysis` | Interpret logs, metrics, test results, and coverage reports |
| `security_audit` | Review code and infrastructure for OWASP Top 10, secrets, misconfigurations |
| `multimodal_read` | Interpret diagrams, screenshots, and UI mockups (vision) |
| `computer_use` | Interact with web UIs and desktop apps via screenshot + action loops |

#### Skill Registry

Skills are stored in **Firestore** as versioned documents:

```json
{
  "skill_id": "code_generation",
  "version": "1.2.0",
  "system_prompt_template": "You are a senior software engineer at VTAL...\n{{context}}",
  "required_context_keys": ["project_context", "tech_stack"],
  "model_preference": "claude-sonnet",
  "max_tokens": 8192,
  "temperature": 0.2
}
```

Agents load their skill configurations at startup from the registry. A squad leader can pin agents to specific skill versions to ensure reproducibility across a project.

#### Execution Sandbox

When a skill requires executing code (e.g., `code_generation` followed by verification):

- **Runtime**: Cloud Run Jobs
- **Isolation**: Each job runs in a dedicated container with no persistent state
- **Network**: No egress by default; explicit allowlist for test dependencies
- **Resources**: CPU 1–2 vCPU, memory 512MB–2GB, timeout 5 min
- **Artifacts**: Output written to a dedicated GCS bucket, path returned to agent

---

### L5 — A2A Communication Bus

**Purpose:** Enable asynchronous, reliable, audited communication between agents in a squad. No agent calls another agent directly over HTTP in production — all delegation flows through the bus.

#### Protocol

**Google A2A Protocol** is used as the message envelope standard. It defines:
- How agents advertise tasks to other agents
- How long-running tasks stream partial results back
- How task delegation chains are tracked

#### Components

| Component | Product | Use Case |
|-----------|---------|----------|
| Async broadcast | Cloud Pub/Sub | Squad-wide events, fan-out notifications |
| Guaranteed delivery | Cloud Tasks | Critical work items (code commits, deploy triggers) with retry + DLQ |
| Sync sub-calls | Cloud Run HTTP / gRPC | Tight-loop calls within a single pipeline step |
| Event-driven triggers | Eventarc | React to external events (GitHub webhook, CI result) |

#### Message Schema

```json
{
  "message_id": "uuid",
  "type": "task.delegated",
  "from_agent": "planner-v1",
  "to_agent": "backend-engineer-v1",
  "run_id": "run-uuid",
  "task": {
    "skill": "code_generation",
    "input": "Implement the payment service endpoint...",
    "context_keys": ["project_context", "run_memory:run-uuid"],
    "deadline": "2026-05-24T18:00:00Z",
    "priority": "normal"
  },
  "reply_to_topic": "projects/vtal/topics/squad-results",
  "created_at": "2026-05-24T12:00:00Z"
}
```

#### Routing Topology

```
Pub/Sub Topic: squad-tasks-{squad_id}
  → Subscription per agent type (pull, filtered by "to_agent")

Pub/Sub Topic: squad-results-{squad_id}
  → Subscription for Orchestration layer (Squad Manager aggregates)

Cloud Tasks Queue: critical-actions-{squad_id}
  → Code commits, PR creations, deploy triggers
  → Retry: exponential backoff, max 5 retries
  → DLQ: dead-letter topic → PagerDuty alert
```

---

### L6 — Digital Squad — Software Factory

**Purpose:** Define the composition and responsibilities of the first Digital Squad: an autonomous software factory that takes requirements to production-ready code.

#### Squad Composition

| Agent Role | Primary Skill | Key Tools | Output |
|------------|--------------|-----------|--------|
| **PM** | `plan_decomposition` | `web_search_tool`, `github_tool` (issues) | User stories, acceptance criteria, task breakdown |
| **Architect** | `deep_reasoning` + `doc_writing` | `diagram_tool`, `search_tool` | Architecture Decision Records, system design |
| **Backend Engineer** | `code_generation` + `test_generation` | `github_tool`, `code_executor_tool`, `test_runner_tool` | Server-side code, unit tests |
| **Frontend Engineer** | `code_generation` + `multimodal_read` | `github_tool`, `code_executor_tool` | UI components, frontend logic |
| **QA Engineer** | `test_generation` + `data_analysis` | `test_runner_tool`, `github_tool` | Integration tests, test reports, coverage |
| **Security Reviewer** | `security_audit` + `code_review` | `github_tool`, `secret_reader_tool` | Security findings, SAST results, mitigations |
| **DevOps Engineer** | `code_generation` | `github_tool`, `cloud_build_tool` | CI/CD pipelines, IaC, deploy scripts |
| **Technical Writer** | `doc_writing` + `multimodal_read` | `github_tool`, `diagram_tool` | API docs, READMEs, runbooks |

#### Workflow (Simplified)

```
Human → "Build feature X"
  ↓
PM: Decompose into tasks, create GitHub issues
  ↓
Architect: Design system, write ADR
  ↓ (parallel)
  ├─ Backend Engineer: Implement server code
  └─ Frontend Engineer: Implement UI
  ↓ (join)
QA Engineer: Write and run tests
  ↓
Security Reviewer: Audit the diff
  ↓ (parallel)
  ├─ DevOps Engineer: Update CI/CD if needed
  └─ Technical Writer: Update docs
  ↓
Human Gate: Review PR, approve merge
  ↓
DevOps: Deploy to staging
```

#### Conflict Resolution

When two agents attempt to modify the same file, the Squad Manager detects the conflict via the A2A bus and:
1. Serializes the writes (second agent waits for first to complete)
2. Notifies both agents of the conflict context
3. Escalates to human if three consecutive conflict cycles occur on the same file

---

### L7 — Orchestration

**Purpose:** Decompose high-level human goals into agent tasks, assign tasks to the right agents, monitor progress, and handle coordination failures.

#### Components

| Component | Description |
|-----------|-------------|
| **Squad Manager** | Stateful coordinator: maintains the overall task graph, tracks what's done, what's blocked, and what needs human attention. Uses `claude-opus` (heavy reasoning). |
| **Planner Agent** | Stateless decomposer: takes a goal and produces an ordered dependency graph of subtasks. Uses `claude-sonnet` (fast planning). |
| **Task Router** | Matches subtasks to agents by skill requirements. Reads Agent Cards from the registry. |

The Squad Manager is the **only agent** that writes to the `run_memory` table and updates `project_context`. All other agents read context but delegate writes back through the Squad Manager.

#### HITL (Human-in-the-Loop) Gates

Human approval is required at:

| Gate | Trigger | Action Required |
|------|---------|----------------|
| Task approval | PM produces task breakdown | Human reviews scope |
| Architecture review | Architect produces ADR | Human reviews design |
| PR merge | All agents complete their work | Human reviews and merges PR |
| Production deploy | Staging tests pass | Human approves deploy |
| Cost overrun | Run exceeds 80% of token budget | Human decides to continue or abort |

HITL gates are modeled as `HUMAN` nodes in the AgentStudio pipeline graph — the existing mechanism is promoted to a first-class workflow concept.

---

### L8 — Guardrails & Safety

**Purpose:** Prevent runaway costs, security incidents, and low-quality output from reaching production.

#### Cost Guardrails

| Control | Implementation |
|---------|---------------|
| Per-run token budget | LiteLLM budget tracking per `run_id`, backed by Redis counter |
| Per-squad daily budget | LiteLLM global budget with Pub/Sub alert at 80% |
| Hard abort | LiteLLM returns 429 when budget exceeded; run marked `failed` with reason |
| Cost visibility | All LiteLLM calls tagged with `project_id`, `squad_id`, `agent_id`; exported to BigQuery |

#### Security Guardrails

| Control | Tool | When |
|---------|------|------|
| Static analysis (Python) | Bandit | On every code_generation output, before commit |
| Static analysis (JS/TS) | ESLint + `@typescript-eslint/no-unsafe-*` | On every frontend code output |
| SAST | Semgrep (OWASP ruleset) | On every diff before PR creation |
| Secret detection | TruffleHog + GitHub Advanced Security | On every commit and PR |
| Dependency audit | `pip audit` + `npm audit` | On every dependency change |
| Scope enforcement | Tool Registry: agent can only call tools in its `tools_allowed` list | At invocation time |

#### Output Validation

Before any agent output is committed to GitHub:
1. Syntax check (parse the generated code)
2. Security scan (Semgrep, Bandit/ESLint)
3. Secret scan (TruffleHog)
4. If any check fails: agent receives the failure, retries up to 3 times, then escalates to human

---

### L9 — Observability & LLMOps

**Purpose:** Provide full visibility into what the system is doing, how much it costs, and where it is failing — from infrastructure metrics down to individual token streams.

#### Components

| Component | Product | What It Covers |
|-----------|---------|---------------|
| Agent Dashboard | Gemini Enterprise Agent Platform (native) | Token usage, latency, error rates, tool call counts per agent — built-in, no config needed |
| Unified Trace Viewer | Agent Platform native | Visualize full sequence of agent actions, tool calls, and routing decisions per run |
| Distributed Tracing | Cloud Trace + OpenTelemetry SDK | Cross-service spans: FastAPI → LiteLLM → Vertex AI → Tools |
| LiteLLM Metrics | LiteLLM OTEL exporter → Cloud Trace | Per-model token cost, latency, error rate from the gateway layer |
| Infrastructure Metrics | Cloud Monitoring + custom metrics | CPU, memory, latency for Cloud Run / GKE / AlloyDB / Redis |
| Logging | Cloud Logging (structured JSON) | All agent actions, tool calls, A2A messages — already structured in codebase |
| Cost Analytics | BigQuery (Log Sink) + Looker Studio | Long-term cost attribution per squad/project; custom exec dashboards |
| Alerting | Cloud Monitoring Alert Policies → PagerDuty | Cost overruns, error rate spikes, DLQ messages, failed runs |
| Eval | Offline eval pipeline (Cloud Run Jobs) | Periodic quality scoring of agent outputs against golden dataset |

> **ADR-007 — Decided:** The Gemini Enterprise Agent Platform provides a native observability dashboard (token usage, latency, error rates, tool calls, Unified Trace Viewer) that covers agent-level LLMOps out of the box. LiteLLM exports to Cloud Trace via OTEL. Combined with Cloud Monitoring for infrastructure and Looker Studio for cost analytics, this eliminates the need for self-hosted Grafana. Decision: **native GCP observability stack only**.

#### Key Custom Metrics

```
agentstudio/run/duration_ms         (run_id, squad_id, status)
agentstudio/run/token_cost_usd      (run_id, agent_id, model)
agentstudio/agent/step_duration_ms  (agent_id, skill, model)
agentstudio/tool/call_count         (tool_name, agent_id, status)
agentstudio/tool/latency_ms         (tool_name)
agentstudio/a2a/message_count       (from_agent, to_agent, type)
agentstudio/budget/utilization_pct  (run_id, squad_id)
```

#### OpenTelemetry Integration

Every agent request and tool call is wrapped in an OTEL span:

```python
with tracer.start_as_current_span("agent.step", attributes={
    "agent.id": agent_id,
    "agent.skill": skill,
    "run.id": run_id,
    "model": model_name,
}) as span:
    result = await litellm_gateway.complete(...)
    span.set_attribute("tokens.input", result.usage.input_tokens)
    span.set_attribute("tokens.output", result.usage.output_tokens)
    span.set_attribute("cost.usd", result.usage.cost)
```

---

## 7. Technology Stack Summary

| Layer | Component | Product | Vendor | Notes |
|-------|-----------|---------|--------|-------|
| L0 | Agent Registry | Gemini Enterprise Agent Platform (Vertex AI Agent Builder) | Google Cloud | Native A2A support, built-in observability |
| L0 | Agent Identity | Workload Identity Federation | Google Cloud | No static keys |
| L0 | Secrets | Secret Manager | Google Cloud | Versioned, audited |
| L1 | LLM Router | LiteLLM (self-hosted) | OSS on Cloud Run | Model-agnostic, budget tracking |
| L1 | Primary Model (standard) | Claude Sonnet 4.6 via Vertex AI | Anthropic via GCP | Code + reasoning |
| L1 | Primary Model (fast) | Gemini 2.0 Flash | Google | Classification, routing |
| L1 | Primary Model (heavy) | Claude Opus 4.7 via Vertex AI | Anthropic via GCP | Planning, architecture |
| L1 | Fallback | OpenAI GPT-4o | OpenAI | Provider redundancy |
| L1 | Local/Private | Ollama | Meta / OSS | Air-gapped use cases |
| L2 | Working Memory | Cloud Memorystore for Redis 7 | Google Cloud | <1ms reads, TTL native |
| L2 | Episodic Memory | AlloyDB for PostgreSQL | Google Cloud | SQL + pgvector unified |
| L2 | Semantic Memory | AlloyDB pgvector | Google Cloud | Same DB, vector index |
| L2 | Org Context | AlloyDB for PostgreSQL | Google Cloud | Structured project state |
| L2 | Embedding Model | text-embedding-004 (Vertex AI) | Google Cloud | 768-dim, code-optimized |
| L3 | Tool Protocol | MCP (Model Context Protocol) | Anthropic OSS | Claude-native standard |
| L3 | Tool Runtime | Cloud Run | Google Cloud | Per-tool containerized service |
| L3 | Tool Registry | Custom service (Firestore-backed) | Internal / GCP | Manifest + invocation routing |
| L3 | Code Execution Sandbox | Cloud Run Jobs | Google Cloud | Ephemeral, resource-capped |
| L3 | Code Search | GitHub API + Vertex AI Search | GitHub / Google | Repository traversal |
| L4 | Skill Registry | Firestore | Google Cloud | Versioned prompt configs |
| L5 | Async Bus | Cloud Pub/Sub | Google Cloud | Fan-out, filtering |
| L5 | Guaranteed Queue | Cloud Tasks | Google Cloud | Retry, DLQ |
| L5 | Protocol | Google A2A Protocol | Google OSS | Agent discovery + delegation |
| L6–L7 | Squad Agents | Custom (FastAPI services on Cloud Run) | Internal | Extends existing codebase |
| L7 | Orchestration DB | AlloyDB (run state) | Google Cloud | Shared with L2 |
| L8 | SAST | Semgrep | OSS / Semgrep Inc. | OWASP ruleset |
| L8 | Python Security | Bandit | OSS | Python-specific |
| L8 | JS/TS Security | ESLint + security rules | OSS | Frontend |
| L8 | Secret Scanning | TruffleHog + GitHub Advanced Security | OSS / GitHub | Pre-commit + PR |
| L9 | Distributed Tracing | Cloud Trace + OpenTelemetry SDK | Google / CNCF | Spans across all layers |
| L9 | Metrics | Cloud Monitoring | Google Cloud | Infrastructure + custom |
| L9 | Logging | Cloud Logging (structured JSON) | Google Cloud | Already in codebase |
| L9 | Log Analytics | BigQuery (Log Sink) | Google Cloud | Cost attribution |
| L9 | Agent Dashboard | Gemini Enterprise Agent Platform (native) | Google Cloud | Token, latency, error rate, tool calls |
| L9 | Cost Analytics | BigQuery + Looker Studio | Google Cloud | Per-squad/project cost attribution |
| L9 | Alerting | Cloud Monitoring → PagerDuty | Google / PagerDuty | On-call escalation |
| Infra | Container Serverless | Cloud Run | Google Cloud | Tools, agents, gateway |
| Infra | Container Persistent | GKE Autopilot | Google Cloud | Squad Manager, bus consumers |
| Infra | Database | AlloyDB for PostgreSQL | Google Cloud | All structured + vector data |
| Infra | Cache | Cloud Memorystore Redis 7 | Google Cloud | Working memory, budget counters |
| Infra | Object Storage | Cloud Storage (GCS) | Google Cloud | Execution artifacts, snapshots |
| Infra | CI/CD | GitHub Actions + Cloud Build | GitHub / Google | Build, test, deploy pipeline |
| Infra | IaC | Terraform (GCP provider) | HashiCorp | All GCP resources |
| Backend | API Framework | FastAPI 0.115 | OSS | Existing codebase |
| Backend | ORM | SQLModel + Alembic | OSS | Existing codebase |
| Backend | Async DB Driver | asyncpg (PostgreSQL) | OSS | Replacing aiosqlite for prod |
| Backend | Streaming | sse-starlette | OSS | SSE to frontend |
| Backend | Logging | structlog (JSON) | OSS | Existing codebase |
| Backend | Python Version | 3.12 | PSF | Upgrade from 3.11 |
| Frontend | Framework | React 19 + TypeScript 5.6 | Meta / OSS | Existing codebase |
| Frontend | Build | Vite 5 | OSS | Existing codebase |
| Frontend | State | Zustand 5 | OSS | Existing codebase |
| Frontend | Data Fetching | TanStack Query v5 | OSS | Existing codebase |
| Frontend | Canvas | @xyflow/react 12 | OSS | Existing codebase |
| Frontend | Styling | Tailwind CSS 3 | OSS | Existing codebase |

---

## 8. Infrastructure — GCP Services Map

```
GCP Project: vtal-agentstudio-prod
│
├── Compute
│   ├── Cloud Run (us-east1)
│   │   ├── agentstudio-backend       ← FastAPI API + SSE
│   │   ├── litellm-gateway           ← LLM proxy/router
│   │   ├── tool-registry             ← Tool manifest catalog
│   │   ├── tool-github               ← GitHub MCP tool
│   │   ├── tool-search               ← Web/docs search tool
│   │   ├── tool-build                ← Cloud Build trigger tool
│   │   └── agentstudio-frontend      ← React SPA (Nginx container, Cloud Run)
│   │
│   ├── Cloud Run Jobs
│   │   ├── code-executor-sandbox     ← Ephemeral code execution
│   │   └── test-runner-sandbox       ← Ephemeral test execution
│   │
│   └── GKE Autopilot (us-east1)
│       ├── squad-manager             ← Stateful orchestrator
│       ├── pub-sub-consumers         ← A2A bus workers (per agent type)
│       └── eval-pipeline             ← Periodic quality evaluation
│
├── Data
│   ├── AlloyDB Cluster (us-east1)
│   │   ├── Primary instance          ← Read/write
│   │   └── Read replica              ← Analytics / eval queries
│   │
│   ├── Cloud Memorystore             ← Redis 7, 2GB (working memory + budget counters)
│   │
│   └── Cloud Storage
│       ├── gs://agentstudio-artifacts ← Code execution outputs
│       ├── gs://agentstudio-backups   ← AlloyDB backups
│       └── gs://agentstudio-frontend  ← Frontend build cache / CDN assets
│
├── Messaging
│   ├── Pub/Sub Topics
│   │   ├── squad-tasks-{squad_id}    ← Inbound tasks per squad
│   │   ├── squad-results-{squad_id} ← Results back to orchestrator
│   │   └── squad-dlq                 ← Dead letter queue
│   │
│   └── Cloud Tasks Queues
│       └── critical-actions          ← Commits, PRs, deploy triggers
│
├── ML / AI
│   ├── Vertex AI Model Garden        ← Gemini + Claude (partner)
│   ├── Vertex AI Vector Search       ← Future: scale beyond pgvector
│   └── Gemini Enterprise Agent Platform  ← Agent registry + native observability
│
├── Security
│   ├── Secret Manager                ← API keys, DB passwords
│   ├── Workload Identity Pool        ← Service-to-service auth
│   ├── Cloud Armor                   ← API rate limiting / WAF
│   └── VPC Service Controls          ← Data perimeter
│
└── Observability
    ├── Gemini Enterprise Agent Platform  ← Native LLMOps dashboard (token, latency, tools, traces)
    ├── Cloud Trace                       ← Distributed tracing (OTEL + LiteLLM export)
    ├── Cloud Monitoring                  ← Infrastructure metrics + alert policies
    ├── Cloud Logging                     ← Structured logs (JSON, all services)
    ├── BigQuery (Log Sink)               ← Long-term log analytics + cost attribution
    └── Looker Studio                     ← Exec-facing cost + quality reports
```

**Regions:** Primary `us-east1`. Disaster recovery: `us-central1` (AlloyDB cross-region replica only in v1).

**Networking:** All services within a private VPC. Cloud Run services use VPC connector. AlloyDB and Memorystore are VPC-private only. External access through Cloud Load Balancing + Cloud Armor.

---

## 9. Data Architecture

### Entities & Storage

| Entity | Storage | Why |
|--------|---------|-----|
| Agent definitions | AlloyDB `agents` table | Structured, CRUD, existing schema |
| Pipeline graphs | AlloyDB `pipelines` table | JSON nodes/edges, existing schema |
| Run records + steps | AlloyDB `runs` / `run_steps` | Structured, queryable, FK relations |
| Working memory | Redis (per run key prefix) | Fast, ephemeral, TTL-scoped |
| Episodic memory | AlloyDB `run_memory` | Queryable history |
| Knowledge embeddings | AlloyDB `knowledge_chunks` (pgvector) | SQL + vector combined queries |
| Project context | AlloyDB `project_context` | Structured JSON per project |
| Skill configs | Firestore `skills/{skill_id}/versions/{v}` | Document store, fast reads, version history |
| Agent cards | Firestore `agents/{agent_id}` | A2A discovery, fast reads |
| Execution artifacts | GCS `agentstudio-artifacts/{run_id}/` | Binary/large outputs |
| LLM call logs | Cloud Logging → BigQuery | Analytics, cost attribution |
| Tool invocation logs | Cloud Logging → BigQuery | Audit trail |

### Data Flows

**Execution path (hot):** API → AlloyDB (run create) → Redis (context write) → LiteLLM → AlloyDB (step update) → SSE → Frontend

**Memory retrieval (hot):** Agent → AlloyDB pgvector similarity search → Top-K chunks → Injected into LLM context

**Audit path (cold):** Cloud Logging → BigQuery daily export → Looker Studio (cost attribution + exec reports)

---

## 10. Security & Compliance

### Authentication & Authorization

| Boundary | Mechanism |
|----------|-----------|
| User → AgentStudio API | Google Identity Platform (OAuth 2.0 / OIDC) + JWT |
| Agent → LiteLLM Gateway | Workload Identity (service account token) |
| Agent → Tool Registry | Workload Identity |
| Tool → External APIs | Secret Manager (API keys, no static env vars) |
| Service → AlloyDB | Cloud SQL Auth Proxy + IAM database auth |
| Service → Memorystore | VPC-private, no public endpoint |
| Service → Pub/Sub | Workload Identity + topic-level IAM |

### Threat Model (Key Risks)

| Risk | Mitigation |
|------|-----------|
| Prompt injection via external tool results | Tool results are treated as untrusted input; injected into context with role `tool`, never `system` |
| Agent writes malicious code | Execution sandbox (Cloud Run Jobs, no egress) + Semgrep/Bandit before commit |
| Runaway token spend | LiteLLM per-run budget + Redis counter + hard abort at 100% |
| Secret leakage in generated code | TruffleHog on every output before commit |
| Agent scope creep (accessing files outside its domain) | Tool Registry enforces `tools_allowed` per Agent Card; GitHub tool enforces path-level permissions |
| Unauthorized A2A messages | Pub/Sub IAM: only authorized service accounts can publish to squad topics |

### Compliance Notes

- All LLM calls via Vertex AI remain within GCP's data processing boundary
- PII must not be included in agent prompts without data classification review (v1 constraint)
- AlloyDB encryption at rest (Google-managed keys; CMEK available if required)
- Audit logs exported to BigQuery with 1-year retention

---

## 11. CI/CD & DevOps

### Pipeline

```
Developer pushes to feature branch
  ↓
GitHub Actions: lint (ruff, eslint) + type-check (mypy, tsc) + unit tests
  ↓
GitHub Actions: Semgrep SAST + TruffleHog secret scan
  ↓
PR created → Code Review Agent (optional automated review)
  ↓
PR merged to main
  ↓
Cloud Build: Docker image build + push to Artifact Registry
  ↓
Cloud Build: Deploy to Cloud Run (staging environment)
  ↓
Integration tests run against staging
  ↓
Manual approval gate (human)
  ↓
Cloud Build: Deploy to Cloud Run (production)
```

### Environments

| Environment | Purpose | Database | Branch |
|-------------|---------|----------|--------|
| `local` | Developer workstation | SQLite | Any feature branch |
| `staging` | Integration testing | AlloyDB (staging cluster) | `main` |
| `production` | Live system | AlloyDB (prod cluster) | Tagged releases |

### Terraform Modules

IaC is organized as Terraform modules:
- `modules/alloydb` — AlloyDB cluster + replica
- `modules/memorystore` — Redis instance
- `modules/cloud-run-service` — Reusable Cloud Run service template
- `modules/pubsub-squad` — Topics + subscriptions per squad
- `modules/iam-agent` — Service account + workload identity per agent role

---

## 12. Implementation Roadmap

### Phase 1 — Foundation (Weeks 1–4)

**Goal:** Replace current direct-provider calls with the LLM gateway and upgrade the database layer to AlloyDB.

| Deliverable | Details |
|-------------|---------|
| LiteLLM Gateway | Deploy on Cloud Run; wire all existing providers through it; add budget tracking |
| AlloyDB | Migrate from SQLite/PostgreSQL to AlloyDB; run Alembic migrations; validate existing tests |
| Cloud Memorystore | Deploy Redis instance; wire as L2 working memory in executor |
| Terraform baseline | IaC for all Phase 1 infrastructure |
| OTEL tracing | Instrument FastAPI backend + LiteLLM with OpenTelemetry → Cloud Trace |

**Exit criteria:** All existing pipeline runs work end-to-end through LiteLLM + AlloyDB with traces visible in Cloud Trace.

### Phase 2 — Agent Runtime (Weeks 5–10)

**Goal:** Build the MCP tool layer, skill registry, A2A bus, and execution sandbox.

| Deliverable | Details |
|-------------|---------|
| MCP Tool Registry | Cloud Run service with Firestore-backed catalog |
| Core Tools | `github_tool`, `code_executor_tool`, `web_search_tool` (first three) |
| Execution Sandbox | Cloud Run Jobs for safe code execution |
| Skill Registry | Firestore documents for all 10 core skills |
| A2A Bus | Pub/Sub topics + Cloud Tasks queue + A2A message schema |
| Agent Card Spec | Implement Agent Card generation for all existing agents |
| Memory tiers L3–L5 | AlloyDB schema migrations for `run_memory`, `knowledge_chunks`, `project_context` |
| Guardrails baseline | Semgrep + Bandit in CI; cost abort in LiteLLM |

**Exit criteria:** A single TOOL agent can use `github_tool` to read a repo and `code_executor_tool` to run the tests, via MCP, with full trace.

### Phase 3 — Software Factory Squad (Weeks 11–18)

**Goal:** Deploy the Digital Software Factory squad with all 8 agent roles.

| Deliverable | Details |
|-------------|---------|
| Squad Manager | Stateful orchestrator on GKE; reads Agent Cards; manages task graph |
| Planner Agent | Task decomposition using Claude Opus |
| All 8 squad agents | Deploy with role-specific skill configs and tool permissions |
| HITL gates | Human approval nodes wired for task approval, PR review, and deploy |
| Remaining tools | `cloud_build_tool`, `test_runner_tool`, `diagram_tool` |
| LLMOps Dashboard | Activate Agent Platform native dashboard; wire LiteLLM OTEL → Cloud Trace; Looker Studio cost report |
| End-to-end test | Full squad run: "implement a new REST endpoint" from requirement to PR |

**Exit criteria:** Squad autonomously takes a GitHub issue from "To Do" to "PR Ready" with human review only at the HITL gates.

### Phase 4 — Production Hardening (Weeks 19–24)

**Goal:** Production-ready reliability, security, and multi-squad support.

| Deliverable | Details |
|-------------|---------|
| GKE Autopilot migration | Move squad-manager + bus consumers to GKE for auto-scaling |
| VPC Service Controls | Data perimeter around AlloyDB + Memorystore |
| AlloyDB read replica | Offload analytics/eval queries |
| Multi-squad support | AgentStudio supports multiple concurrent squads |
| Eval pipeline | Automated quality scoring of agent outputs |
| DR plan | AlloyDB cross-region replica + runbook for failover |
| Load testing | Simulate 10 concurrent squad runs; validate cost and latency |
| Security audit | External penetration test |

---

## 13. Cost Model

Estimates assume moderate usage (5 squad runs/day, average 50 steps/run, mixed models).

| Component | GCP Service | Estimated Monthly Cost |
|-----------|------------|----------------------|
| LLM calls (Vertex AI — Claude Sonnet) | Vertex AI | ~$800–2,000 |
| LLM calls (Vertex AI — Gemini Flash) | Vertex AI | ~$50–150 |
| AlloyDB (2 vCPU, 16GB, 1 replica) | AlloyDB | ~$400–600 |
| Cloud Memorystore Redis (2GB) | Memorystore | ~$80–120 |
| Cloud Run (all services, min-instances=1) | Cloud Run | ~$150–300 |
| GKE Autopilot (squad-manager + consumers) | GKE | ~$200–400 |
| Pub/Sub + Cloud Tasks | Messaging | ~$10–30 |
| Cloud Build (CI minutes) | Cloud Build | ~$30–80 |
| Cloud Storage | GCS | ~$10–20 |
| Observability (Logging, Monitoring, Trace) | Ops Suite | ~$50–100 |
| **Total (moderate usage)** | | **~$1,780–3,800/month** |

**Cost Controls in Place:**
- LiteLLM per-run budget caps (hard abort)
- Cloud Run min-instances=0 for non-critical services
- Gemini Flash for classification/routing tasks (10–20x cheaper than Sonnet)
- BigQuery cost attribution reports for per-squad, per-project billing

---

## 14. Open Decisions & ADRs

These are architectural questions that need a decision before or during implementation.

| # | Question | Options | Recommendation | Status |
|---|----------|---------|----------------|--------|
| ADR-001 | GCP Agent Platform maturity vs. custom registry | (A) GCP Agent Platform, (B) custom Firestore service | **(A) — follow recommendation.** Avoids registry maintenance; Agent Platform now rebranded as Gemini Enterprise Agent Platform (Cloud Next 2026) with stable APIs | **Decided** |
| ADR-002 | AlloyDB pgvector vs. Vertex AI Vector Search for L4 | (A) pgvector (same DB), (B) Vertex Vector Search (dedicated) | (A) until >10M vectors or pgvector query P95 >100ms | **Decided** |
| ADR-003 | Squad-per-GKE-namespace vs. squad-per-Cloud-Run-service | (A) GKE namespaces, (B) Cloud Run per agent type | (A) for stateful squad manager; (B) for stateless tools | **Decided** |
| ADR-004 | LiteLLM self-hosted vs. LiteLLM Proxy managed service | (A) Self-hosted on Cloud Run, (B) LiteLLM Cloud | (A) — data residency control, no vendor lock for gateway | **Decided** |
| ADR-005 | Frontend hosting: Cloud Run vs. Firebase Hosting vs. GCS+CDN | (A) Cloud Run, (B) Firebase Hosting, (C) GCS + Cloud CDN | **(A) Cloud Run** — consistent with all other services; Nginx container serving Vite build; same VPC + IAP boundary | **Decided** |
| ADR-006 | Human authentication provider | (A) Google Identity Platform, (B) Auth0, (C) custom | **(A) — follow recommendation.** Google Identity Platform: GCP-native, IAP integration, no extra vendor, SSO with VTAL Google Workspace | **Decided** |
| ADR-007 | LLMOps dashboard: Grafana self-hosted vs. native GCP | (A) Grafana on Cloud Run, (B) native GCP stack | **(B) native GCP stack.** Gemini Enterprise Agent Platform has a built-in observability dashboard (token usage, latency, error rates, tool calls, Unified Trace Viewer). LiteLLM exports to Cloud Trace via OTEL. Looker Studio covers cost attribution. No Grafana needed — eliminates one operational dependency | **Decided** |
| ADR-008 | When to enable Vertex AI Vector Search (scale threshold) | Trigger: pgvector index rebuild >5min OR query P95 >100ms | Documented threshold; no change needed in v1 | **Decided** |

---

## 15. Appendix — Current Codebase (Phase 1–3)

The following describes what has already been implemented and will serve as the foundation for the architecture above.

### What's Built

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI backend | ✅ Complete | `backend/app/main.py`, CORS, lifespan |
| Agent CRUD | ✅ Complete | `/api/v1/agents` — LLM, TOOL, ROUTER, HUMAN types |
| Pipeline CRUD | ✅ Complete | `/api/v1/pipelines` — ReactFlow nodes/edges as JSON |
| Run execution (DAG) | ✅ Complete | `engine/executor.py` — topological sort, background tasks |
| SSE streaming | ✅ Complete | `engine/streaming.py` — per-run asyncio queues |
| In-context memory | ✅ Complete | `engine/memory.py` — 50-message sliding window |
| Anthropic provider | ✅ Complete | `providers/anthropic.py` — stream + complete |
| OpenAI provider | ✅ Complete | `providers/openai.py` |
| Ollama provider | ✅ Complete | `providers/ollama.py` |
| SQLite/PostgreSQL DB | ✅ Complete | SQLModel ORM + Alembic |
| React frontend | ✅ Complete | Pipeline canvas, agent config, run stream |
| Basic test suite | ✅ Complete | `tests/` — engine, agents, pipelines |
| Human-in-the-loop | ✅ Complete | HUMAN node type + `/resume` endpoint |

### Known Gaps (to be addressed in Phases 1–4)

| Gap | Phase |
|-----|-------|
| No LLM gateway (direct provider calls) | Phase 1 |
| SQLite in dev, no AlloyDB | Phase 1 |
| No distributed working memory | Phase 1 |
| No MCP tool layer (only `echo`, `add` stubs) | Phase 2 |
| Router agent doesn't affect edge traversal | Phase 2 |
| Resume logic doesn't replay remaining nodes | Phase 2 |
| No A2A bus (single-process only) | Phase 2 |
| No authentication | Phase 3/4 |
| No production observability | Phase 1 (OTEL) |
| Frontend: no run history, no agent templates | Phase 3 |

---

*End of document. Version 0.1 — PENDING APPROVAL.*
