"""
NextMove FastAPI application entry point.

Usage
-----
Start the development server from the ``backend/`` directory::

    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Environment
-----------
Copy ``.env.example`` to ``.env`` and adjust values before starting.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
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
    logger.info(
        "Swagger UI available at http://127.0.0.1:%s/docs", settings.backend_port
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=(
        "NextMove — AI-powered competitive intelligence platform.\n\n"
        "Phase 1: Repository foundation.  Subsequent phases will add "
        "the full intelligence pipeline."
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

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health_router)

# ── Global exception handlers ─────────────────────────────────────────────────


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Return a structured JSON error for any unhandled exception."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content=ErrorDetail(
            error="internal_server_error",
            detail=str(exc),
        ).model_dump(mode="json"),
    )



