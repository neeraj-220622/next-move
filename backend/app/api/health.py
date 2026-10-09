"""
Health and status API routes.

Endpoints
---------
GET /health         — lightweight liveness probe (no dependency checks).
GET /api/v1/status  — full application and dependency status.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import DependencyInfo, HealthResponse, ServiceStatus, StatusResponse
from app.services.forecasting_service import ForecastingService
from app.services.hindsight_service import HindsightService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    tags=["health"],
)
async def health() -> HealthResponse:
    """
    Lightweight liveness endpoint — always returns 200 if the server is up.

    Does **not** check external dependencies; use ``/api/v1/status`` for that.
    """
    settings = get_settings()
    return HealthResponse(app_name=settings.app_name)


@router.get(
    "/api/v1/status",
    response_model=StatusResponse,
    summary="Application and dependency status",
    tags=["health"],
)
async def status() -> StatusResponse:
    """
    Full status check.

    Probes each external dependency (Hindsight, LLM, forecasting) and
    reports their availability honestly.  A dependency being unavailable
    does **not** cause this endpoint to return a non-200 status; the
    dependency list in the response body conveys the full picture.
    """
    settings = get_settings()

    # Run all dependency checks.
    hindsight_info = await HindsightService(settings).check_connectivity()
    llm_info = await LLMService(settings).check_connectivity()
    forecasting_info = ForecastingService(settings).check_availability()

    dependencies: list[DependencyInfo] = [
        hindsight_info,
        llm_info,
        forecasting_info,
    ]

    # Overall status: "ok" only when every dependency that *should* be up is.
    # Disabled / unavailable optional deps degrade to "degraded", not "error".
    statuses = {d.status for d in dependencies}
    if statuses == {ServiceStatus.OK}:
        overall = "ok"
    elif ServiceStatus.UNKNOWN in statuses:
        overall = "error"
    else:
        overall = "degraded"

    logger.info("Status check — overall: %s", overall)

    return StatusResponse(
        status=overall,
        app_name=settings.app_name,
        app_env=settings.app_env,
        dependencies=dependencies,
    )
