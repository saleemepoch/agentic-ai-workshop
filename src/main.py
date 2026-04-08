"""
FastAPI application entry point.

Configures CORS, lifespan (DB initialisation), and mounts all pillar routers.

Interview talking points:
- Why a lifespan context manager? FastAPI's lifespan replaces the older
  on_startup/on_shutdown hooks. It's cleaner — setup and teardown are co-located,
  and resources (like DB connections) can be shared via the lifespan state.
- Why permissive CORS in development? The Next.js frontend runs on a different
  port. In production, you'd lock this down to your domain.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database import init_db, engine
from src.errors import register_error_handlers
from src.observability.tracing import flush_traces, shutdown as shutdown_langfuse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialise DB on startup, dispose engine on shutdown."""
    logger.info("Starting Agentic AI Workshop API...")
    await init_db()
    logger.info("Database initialised.")
    yield
    flush_traces()
    shutdown_langfuse()
    await engine.dispose()
    logger.info("Database and Langfuse connections closed.")


app = FastAPI(
    title="Agentic AI Workshop",
    description="Teaching platform for agentic AI, RAG, and production AI engineering.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — permissive in development for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Translate upstream provider errors (Anthropic, Voyage AI) into structured
# HTTP responses the frontend can render. See src/errors.py.
register_error_handlers(app)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint. Returns 200 if the API is running."""
    return {"status": "healthy", "service": "agentic-ai-workshop"}


# Pillar routers
from src.documents.router import router as documents_router
from src.matching.router import router as matching_router
from src.agents.router import router as agents_router
from src.observability.router import router as observability_router
from src.evaluation.router import router as evaluation_router
from src.guardrails.router import router as guardrails_router
from src.prompts.router import router as prompts_router
from src.structured.router import router as structured_router
from src.resilience.router import router as resilience_router

app.include_router(documents_router, prefix="/documents", tags=["Documents"])
app.include_router(matching_router, prefix="/embeddings", tags=["Embeddings & Retrieval"])
app.include_router(agents_router, prefix="/agents", tags=["Agents"])
app.include_router(observability_router, prefix="/observability", tags=["Observability"])
app.include_router(evaluation_router, prefix="/evaluation", tags=["Evaluation"])
app.include_router(guardrails_router, prefix="/guardrails", tags=["Guardrails"])
app.include_router(prompts_router, prefix="/prompts", tags=["Prompts"])
app.include_router(structured_router, prefix="/structured", tags=["Structured Outputs"])
app.include_router(resilience_router, prefix="/resilience", tags=["Resilience"])
