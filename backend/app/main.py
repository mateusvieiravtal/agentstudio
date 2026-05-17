from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import agents, pipelines, providers, runs
from app.settings import settings


def _configure_logging() -> None:
    logging.basicConfig(level=settings.log_level.upper(), format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )


_configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_db()
    logger.info("startup_complete", database_url=settings.database_url)
    yield
    logger.info("shutdown_complete")


app = FastAPI(
    title="AgentStudio",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix=settings.api_prefix)
app.include_router(pipelines.router, prefix=settings.api_prefix)
app.include_router(runs.router, prefix=settings.api_prefix)
app.include_router(providers.router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
