FROM python:3.11-slim

WORKDIR /app

# Install uv from official image (fast, reproducible)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Layer cache: copy lockfile first so deps only rebuild when they change
COPY pyproject.toml uv.lock ./

# Install production deps only, honour the lockfile exactly
RUN uv sync --no-dev --frozen

# Copy application source
COPY app/ ./app/

# Cloud Run injects PORT=8080; default to 8080 if not set
ENV PORT=8080

CMD uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
