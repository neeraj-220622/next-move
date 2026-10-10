"""
Shared Pydantic schemas used across API responses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Dependency / service status ──────────────────────────────────────────────


class ServiceStatus(str, Enum):
    """Possible states for an external dependency or subsystem."""

    OK = "ok"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    DISABLED = "disabled"
    DEGRADED = "degraded"


class DependencyInfo(BaseModel):
    """Runtime status of a single external dependency."""

    name: str
    status: ServiceStatus
    message: str = ""
    latency_ms: Optional[float] = None


# ── Standard API response wrappers ────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Response schema for GET /health."""

    status: str = "ok"
    app_name: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class StatusResponse(BaseModel):
    """Response schema for GET /api/v1/status."""

    status: str
    app_name: str
    app_env: str
    version: str = "0.1.0"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    dependencies: list[DependencyInfo] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    """Structured error payload returned by exception handlers."""

    error: str
    detail: Any = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
