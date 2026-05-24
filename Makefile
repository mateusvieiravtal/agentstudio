.PHONY: help dev backend frontend infra infra-down install test lint

# ── Colours ───────────────────────────────────────────────────────────────────
CYAN  := \033[0;36m
RESET := \033[0m

help:
	@echo ""
	@echo "  $(CYAN)make install$(RESET)     Install all dependencies (backend + frontend)"
	@echo "  $(CYAN)make infra$(RESET)       Start local infrastructure (Redis) via Docker"
	@echo "  $(CYAN)make infra-down$(RESET)  Stop local infrastructure"
	@echo "  $(CYAN)make backend$(RESET)     Run FastAPI backend with hot-reload"
	@echo "  $(CYAN)make frontend$(RESET)    Run Vite dev server"
	@echo "  $(CYAN)make dev$(RESET)         Start infra + backend + frontend (requires tmux or run manually)"
	@echo "  $(CYAN)make test$(RESET)        Run backend test suite"
	@echo "  $(CYAN)make lint$(RESET)        Lint + type-check backend"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	cd backend && uv sync
	cd frontend && npm install

# ── Infrastructure ────────────────────────────────────────────────────────────
infra:
	docker compose up -d redis
	@echo "$(CYAN)Redis running on localhost:6379$(RESET)"

infra-down:
	docker compose down

# ── Backend ───────────────────────────────────────────────────────────────────
backend:
	@test -f backend/.env || cp backend/.env.example backend/.env
	cd backend && uv run uvicorn app.main:app --reload --port 8000

# ── Frontend ──────────────────────────────────────────────────────────────────
frontend:
	cd frontend && npm run dev

# ── Combined dev (requires two terminals or a multiplexer) ───────────────────
dev: infra
	@echo ""
	@echo "$(CYAN)Infrastructure started. Now run in separate terminals:$(RESET)"
	@echo "  Terminal 1: make backend"
	@echo "  Terminal 2: make frontend"
	@echo ""

# ── Quality ───────────────────────────────────────────────────────────────────
test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check . && uv run mypy app
