# AgentStudio

Plataforma visual no-code/low-code para montar e executar pipelines de agentes
de IA. Inspirada em AgentScope (Alibaba), suporta múltiplos providers (Anthropic
Claude, OpenAI, Ollama) e execução com streaming em tempo real via SSE.

## Estrutura

```
agentstudio/
├── backend/        FastAPI + SQLModel + engine de execução
└── frontend/       Vite + React 19 + TypeScript + ReactFlow
```

## Backend

Stack: FastAPI, SQLModel, Alembic, pydantic-settings, structlog, providers
oficiais Anthropic/OpenAI, Ollama via OpenAI-compat.

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Testes:

```bash
cd backend
uv run pytest -q
```

Variáveis de ambiente (ver `.env.example`):

```
DATABASE_URL=sqlite+aiosqlite:///./agentstudio.db
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434/v1
```

## Frontend

Stack: Vite, React 19, TypeScript, Tailwind v3, @xyflow/react v12, Zustand,
TanStack Query v5.

```bash
cd frontend
npm install
npm run dev       # dev server proxiado para o backend
npm run build     # build de produção
```

## API (resumo)

| Método | Path | Descrição |
|--------|------|-----------|
| GET    | `/api/v1/providers` | Lista providers + modelos |
| GET    | `/api/v1/agents` | Lista agentes |
| POST   | `/api/v1/agents` | Cria agente |
| GET    | `/api/v1/agents/{id}` | Detalhe |
| PATCH  | `/api/v1/agents/{id}` | Atualiza |
| DELETE | `/api/v1/agents/{id}` | Remove |
| GET    | `/api/v1/pipelines` | Lista pipelines |
| POST   | `/api/v1/pipelines` | Cria pipeline |
| GET    | `/api/v1/pipelines/{id}` | Detalhe |
| PATCH  | `/api/v1/pipelines/{id}` | Atualiza |
| DELETE | `/api/v1/pipelines/{id}` | Remove |
| POST   | `/api/v1/runs` | Dispara execução |
| GET    | `/api/v1/runs/{id}` | Detalhe |
| GET    | `/api/v1/runs/{id}/stream` | SSE em tempo real |
| POST   | `/api/v1/runs/{id}/resume` | Retoma após HUMAN |

## Tipos de agente

- `LLM` — chamada simples de LLM com streaming.
- `TOOL` — loop ReAct (até 10 iterações) com tools registradas.
- `ROUTER` — LLM classifica o input e escolhe a próxima aresta (label).
- `HUMAN` — pausa o pipeline e aguarda input humano via `/resume`.

## Eventos SSE

```
run.started      { run_id }
step.started     { step_id, agent_id }
token            { step_id, token }
tool.called      { step_id, tool, args }
tool.result      { step_id, tool, result }
step.completed   { step_id, output }
human.required   { step_id, prompt }
run.completed    { run_id, output }
run.failed       { run_id, error }
```
