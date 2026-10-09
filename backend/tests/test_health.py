"""
Tests for health and status endpoints.

These tests run entirely without a live Hindsight server, Qwen, or any
ML dependencies.  External HTTP calls are mocked.

Run::

    cd backend
    pytest tests/ -v
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ConnectError, TimeoutException

from app.main import app
from app.schemas.common import DependencyInfo, ServiceStatus


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Synchronous test client — suitable for sync and async endpoint tests."""
    with TestClient(app) as c:
        yield c


# ── GET /health ───────────────────────────────────────────────────────────────


class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_contains_status_ok(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_response_contains_app_name(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "app_name" in data
        assert isinstance(data["app_name"], str)
        assert len(data["app_name"]) > 0

    def test_response_contains_timestamp(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "timestamp" in data


# ── GET /api/v1/status ────────────────────────────────────────────────────────


class TestStatusEndpoint:
    def _mocked_dependency(self, status: ServiceStatus, name: str) -> DependencyInfo:
        return DependencyInfo(
            name=name,
            status=status,
            message=f"Mocked {name} — {status}",
        )

    @patch(
        "app.api.health.HindsightService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="hindsight",
            status=ServiceStatus.UNAVAILABLE,
            message="Mocked — server not running",
        ),
    )
    @patch(
        "app.api.health.LLMService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="llm",
            status=ServiceStatus.UNAVAILABLE,
            message="Mocked — server not running",
        ),
    )
    @patch(
        "app.api.health.ForecastingService.check_availability",
        return_value=DependencyInfo(
            name="forecasting",
            status=ServiceStatus.OK,
            message="Baseline mode",
        ),
    )
    def test_returns_200_when_deps_unavailable(
        self, mock_fc, mock_llm, mock_hs, client: TestClient
    ) -> None:
        """Status endpoint must return 200 even when optional deps are down."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200

    @patch(
        "app.api.health.HindsightService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="hindsight",
            status=ServiceStatus.UNAVAILABLE,
            message="Mocked — server not running",
        ),
    )
    @patch(
        "app.api.health.LLMService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="llm",
            status=ServiceStatus.UNAVAILABLE,
            message="Mocked — server not running",
        ),
    )
    @patch(
        "app.api.health.ForecastingService.check_availability",
        return_value=DependencyInfo(
            name="forecasting",
            status=ServiceStatus.OK,
            message="Baseline mode",
        ),
    )
    def test_reports_degraded_when_deps_unavailable(
        self, mock_fc, mock_llm, mock_hs, client: TestClient
    ) -> None:
        data = client.get("/api/v1/status").json()
        assert data["status"] == "degraded"

    @patch(
        "app.api.health.HindsightService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="hindsight", status=ServiceStatus.OK, message="ok"
        ),
    )
    @patch(
        "app.api.health.LLMService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="llm", status=ServiceStatus.OK, message="ok"
        ),
    )
    @patch(
        "app.api.health.ForecastingService.check_availability",
        return_value=DependencyInfo(
            name="forecasting", status=ServiceStatus.OK, message="ok"
        ),
    )
    def test_reports_ok_when_all_deps_healthy(
        self, mock_fc, mock_llm, mock_hs, client: TestClient
    ) -> None:
        data = client.get("/api/v1/status").json()
        assert data["status"] == "ok"

    @patch(
        "app.api.health.HindsightService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="hindsight",
            status=ServiceStatus.UNAVAILABLE,
            message="Mocked",
        ),
    )
    @patch(
        "app.api.health.LLMService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="llm", status=ServiceStatus.UNAVAILABLE, message="Mocked"
        ),
    )
    @patch(
        "app.api.health.ForecastingService.check_availability",
        return_value=DependencyInfo(
            name="forecasting", status=ServiceStatus.OK, message="ok"
        ),
    )
    def test_response_contains_dependency_list(
        self, mock_fc, mock_llm, mock_hs, client: TestClient
    ) -> None:
        data = client.get("/api/v1/status").json()
        assert "dependencies" in data
        assert isinstance(data["dependencies"], list)
        dep_names = {d["name"] for d in data["dependencies"]}
        assert {"hindsight", "llm", "forecasting"} == dep_names

    @patch(
        "app.api.health.HindsightService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="hindsight",
            status=ServiceStatus.UNAVAILABLE,
            message="Mocked",
        ),
    )
    @patch(
        "app.api.health.LLMService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(
            name="llm", status=ServiceStatus.UNAVAILABLE, message="Mocked"
        ),
    )
    @patch(
        "app.api.health.ForecastingService.check_availability",
        return_value=DependencyInfo(
            name="forecasting", status=ServiceStatus.OK, message="ok"
        ),
    )
    def test_hindsight_unavailable_reported_correctly(
        self, mock_fc, mock_llm, mock_hs, client: TestClient
    ) -> None:
        data = client.get("/api/v1/status").json()
        hs = next(d for d in data["dependencies"] if d["name"] == "hindsight")
        assert hs["status"] == "unavailable"


# ── HindsightService unit tests ───────────────────────────────────────────────


class TestHindsightServiceConnectivity:
    @pytest.mark.asyncio
    async def test_returns_unavailable_on_connect_error(self) -> None:
        from app.services.hindsight_service import HindsightService

        with patch("httpx.AsyncClient.get", side_effect=ConnectError("refused")):
            svc = HindsightService()
            result = await svc.check_connectivity()
        assert result.status == ServiceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_returns_unavailable_on_timeout(self) -> None:
        from app.services.hindsight_service import HindsightService

        with patch(
            "httpx.AsyncClient.get",
            side_effect=TimeoutException("timeout"),
        ):
            svc = HindsightService()
            result = await svc.check_connectivity()
        assert result.status == ServiceStatus.UNAVAILABLE


# ── ForecastingService unit tests ─────────────────────────────────────────────


class TestForecastingServiceAvailability:
    def test_baseline_always_ok(self) -> None:
        from app.core.config import Settings
        from app.services.forecasting_service import ForecastingService

        settings = Settings(FORECASTING_MODEL="baseline")
        result = ForecastingService(settings).check_availability()
        assert result.status == ServiceStatus.OK

    def test_sklearn_unavailable_when_not_installed(self) -> None:
        """Simulate sklearn not installed by patching builtins.__import__."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):  # type: ignore[override]
            if name == "sklearn":
                raise ImportError("No module named 'sklearn'")
            return real_import(name, *args, **kwargs)

        from app.core.config import Settings
        from app.services.forecasting_service import ForecastingService

        settings = Settings(FORECASTING_MODEL="sklearn")
        with patch("builtins.__import__", side_effect=mock_import):
            result = ForecastingService(settings).check_availability()
        assert result.status == ServiceStatus.UNAVAILABLE
