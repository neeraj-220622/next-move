"""
NextMove FastAPI application entry point.

Usage
-----
Start the development server from the ``backend/`` directory::

    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Environment
-----------
Copy ``.env.example`` to ``.env`` and adjust values before starting.
All sensitive values (``LLM_API_KEY``) must be supplied via environment
variables and are never echoed or logged.
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.v1.competitors import router as competitors_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.behaviour import router as behaviour_router
from app.api.v1.outcomes import router as outcomes_router
from app.api.v1.timemachine import router as timemachine_router
from app.core.config import get_settings
from app.schemas.common import ErrorDetail

# ── Logging setup ─────────────────────────────────────────────────────────────

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

# ── FastAPI application ───────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup and shutdown logic."""
    logger.info(
        "Starting %s (env=%s, port=%s)",
        settings.app_name,
        settings.app_env,
        settings.backend_port,
    )
    logger.info("Configuration: %s", settings.safe_summary())
    logger.info(
        "Swagger UI available at http://127.0.0.1:%s/docs", settings.backend_port
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=(
        "NextMove — AI-powered competitive intelligence platform.\n\n"
        "Phases 1–5 implemented: Hindsight memory integration, "
        "Groq LLM inference, and scikit-learn forecasting pipeline."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware ────────────────────────────────────────────────


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log method, path, status code, duration, and correlation ID for every request."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request_id=%s %s %s -> %s (%.1fms)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(competitors_router, prefix="/api/v1/competitors", tags=["Competitors"])
app.include_router(predictions_router, prefix="/api/v1/predict", tags=["Predictions"])
app.include_router(evidence_router, prefix="/api/v1/evidence", tags=["Evidence"])
app.include_router(behaviour_router, prefix="/api/v1/behaviour", tags=["Behaviour"])
app.include_router(outcomes_router, prefix="/api/v1/outcomes", tags=["Outcomes"])
app.include_router(timemachine_router, prefix="/api/v1/timemachine", tags=["Strategic Time Machine"])

# ── Global exception handlers ─────────────────────────────────────────────────


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Return a structured JSON error for any unhandled exception.

    The ``detail`` field is intentionally generic to avoid leaking
    internal paths, secrets, or stack traces to API clients.
    Full details are logged server-side.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(
        "Unhandled exception request_id=%s %s %s",
        request_id,
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content=ErrorDetail(
            error="internal_server_error",
            detail="An unexpected error occurred. Please try again or contact support.",
        ).model_dump(mode="json"),
        headers={"X-Request-ID": request_id},
    )
