"""
Phase 6 tests — configuration, error handling, logging, and resilience.

All external services (Groq, Hindsight) are mocked.
"""

from __future__ import annotations

import builtins
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from app.schemas.common import DependencyInfo, ServiceStatus


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


# ── Task 1 — Configuration validation ─────────────────────────────────────────


class TestConfigValidation:
    def test_valid_settings_load(self):
        s = Settings(
            LLM_PROVIDER="openai-compatible",
            LLM_BASE_URL="https://api.groq.com/openai/v1",
            LLM_MODEL="openai/gpt-oss-120b",
            FORECASTING_MODEL="baseline",
        )
        assert s.llm_provider == "openai-compatible"
        assert s.forecasting_model == "baseline"

    def test_invalid_llm_provider_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(LLM_PROVIDER="ollama-invalid")

    def test_invalid_forecasting_model_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(FORECASTING_MODEL="tensorflow")

    def test_invalid_timeout_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(LLM_TIMEOUT=-1)

    def test_safe_summary_does_not_contain_api_key(self):
        s = Settings(LLM_API_KEY="super-secret-key", LLM_PROVIDER="disabled")
        summary = s.safe_summary()
        assert "super-secret-key" not in summary
        assert "[SET]" in summary

    def test_safe_summary_reports_not_set_when_no_key(self):
        s = Settings(LLM_API_KEY="", LLM_PROVIDER="disabled")
        summary = s.safe_summary()
        assert "[NOT SET]" in summary

    def test_disabled_provider_accepted(self):
        s = Settings(LLM_PROVIDER="disabled")
        assert s.llm_provider == "disabled"

    def test_local_provider_accepted(self):
        s = Settings(LLM_PROVIDER="local")
        assert s.llm_provider == "local"


# ── Task 2 — Status / health reporting ────────────────────────────────────────


class TestHealthStatus:
    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_has_status_ok(self, client):
        assert client.get("/health").json()["status"] == "ok"

    @patch(
        "app.api.health.HindsightService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(name="hindsight", status=ServiceStatus.OK, message="ok"),
    )
    @patch(
        "app.api.health.LLMService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(name="llm", status=ServiceStatus.OK, message="ok"),
    )
    @patch(
        "app.api.health.ForecastingService.check_availability",
        return_value=DependencyInfo(name="forecasting", status=ServiceStatus.OK, message="ok"),
    )
    def test_status_ok_when_all_deps_healthy(self, mock_fc, mock_llm, mock_hs, client):
        data = client.get("/api/v1/status").json()
        assert data["status"] == "ok"

    @patch(
        "app.api.health.HindsightService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(name="hindsight", status=ServiceStatus.DEGRADED, message="model missing"),
    )
    @patch(
        "app.api.health.LLMService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(name="llm", status=ServiceStatus.OK, message="ok"),
    )
    @patch(
        "app.api.health.ForecastingService.check_availability",
        return_value=DependencyInfo(name="forecasting", status=ServiceStatus.DEGRADED, message="model missing"),
    )
    def test_status_degraded_when_one_dep_degraded(self, mock_fc, mock_llm, mock_hs, client):
        data = client.get("/api/v1/status").json()
        assert data["status"] == "degraded"

    @patch(
        "app.api.health.HindsightService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(name="hindsight", status=ServiceStatus.OK, message="ok"),
    )
    @patch(
        "app.api.health.LLMService.check_connectivity",
        new_callable=AsyncMock,
        return_value=DependencyInfo(name="llm", status=ServiceStatus.UNKNOWN, message="mystery"),
    )
    @patch(
        "app.api.health.ForecastingService.check_availability",
        return_value=DependencyInfo(name="forecasting", status=ServiceStatus.OK, message="ok"),
    )
    def test_status_error_when_dep_unknown(self, mock_fc, mock_llm, mock_hs, client):
        data = client.get("/api/v1/status").json()
        assert data["status"] == "error"

    def test_status_returns_200_even_when_all_degraded(self, client):
        with (
            patch(
                "app.api.health.HindsightService.check_connectivity",
                new_callable=AsyncMock,
                return_value=DependencyInfo(name="hindsight", status=ServiceStatus.UNAVAILABLE, message="down"),
            ),
            patch(
                "app.api.health.LLMService.check_connectivity",
                new_callable=AsyncMock,
                return_value=DependencyInfo(name="llm", status=ServiceStatus.UNAVAILABLE, message="down"),
            ),
            patch(
                "app.api.health.ForecastingService.check_availability",
                return_value=DependencyInfo(name="forecasting", status=ServiceStatus.UNAVAILABLE, message="down"),
            ),
        ):
            assert client.get("/api/v1/status").status_code == 200


# ── Task 3 — Error handling ────────────────────────────────────────────────────


class TestErrorHandling:
    def test_unknown_route_returns_404(self, client):
        r = client.get("/does/not/exist")
        assert r.status_code == 404

    def test_predict_unknown_competitor_returns_404(self, client):
        import uuid
        from datetime import datetime, timezone
        from app.schemas.cluster import StrategicCluster

        r = client.post("/api/v1/predict/", json={
            "competitor_id": str(uuid.uuid4()),
            "cluster": StrategicCluster.PRICING_PROMOTIONS.value,
            "cutoff_date": datetime.now(timezone.utc).isoformat(),
            "horizon_days": 30,
            "evidence_ids": [],
            "metadata": {},
        })
        assert r.status_code == 404

    def test_register_competitor_invalid_body_returns_422(self, client):
        r = client.post("/api/v1/competitors/", json={"bad_field": 123})
        assert r.status_code == 422


# ── Task 3/4 — LLM error categorisation ──────────────────────────────────────


class TestLLMErrorHandling:
    @pytest.fixture
    def llm_service(self):
        from app.services.llm_service import LLMService

        settings = Settings(
            LLM_PROVIDER="openai-compatible",
            LLM_BASE_URL="https://api.groq.com/openai/v1",
            LLM_MODEL="openai/gpt-oss-120b",
            LLM_API_KEY="fake-key",
            LLM_TIMEOUT=1,
        )
        return LLMService(settings=settings)

    @pytest.mark.asyncio
    async def test_disabled_returns_message(self):
        from app.services.llm_service import LLMService

        settings = Settings(LLM_PROVIDER="disabled")
        svc = LLMService(settings=settings)
        result = await svc.generate_explanation("test")
        assert "disabled" in result.lower()

    @pytest.mark.asyncio
    async def test_auth_error_returns_safe_message(self, llm_service):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "401", request=MagicMock(), response=mock_resp
            )
            result = await llm_service.generate_explanation("test")
        assert "authentication" in result.lower()
        assert "key" not in result.lower() or "check" in result.lower()

    @pytest.mark.asyncio
    async def test_rate_limit_returns_safe_message(self, llm_service):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=mock_resp
            )
            result = await llm_service.generate_explanation("test")
        assert "rate limit" in result.lower()

    @pytest.mark.asyncio
    async def test_timeout_returns_safe_message(self, llm_service):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("timeout")
            result = await llm_service.generate_explanation("test")
        assert "timed out" in result.lower()

    @pytest.mark.asyncio
    async def test_error_message_does_not_contain_api_key(self, llm_service):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=mock_resp
            )
            result = await llm_service.generate_explanation("test")
        assert "fake-key" not in result


# ── Task 3 — Forecasting error handling ──────────────────────────────────────


class TestForecastingErrorHandling:
    def test_missing_artifacts_returns_unavailable(self):
        from app.services.forecasting_service import ForecastingService

        settings = Settings(FORECASTING_MODEL="sklearn")
        svc = ForecastingService.__new__(ForecastingService)
        svc._settings = settings
        svc._model = None
        svc._metadata = None

        result = svc.predict_competitor_action({"evidence_count": 3, "horizon_days": 30, "cluster": "price_cut"})
        assert result["status"] == "unavailable"

    def test_baseline_always_returns_probability(self):
        from app.services.forecasting_service import ForecastingService

        settings = Settings(FORECASTING_MODEL="baseline")
        svc = ForecastingService(settings=settings)
        result = svc.predict_competitor_action({"cluster": "price_cut", "horizon_days": 30})
        assert result["status"] == "ok"
        assert result["model_version"] == "baseline"
        assert 0.0 <= result["probability"] <= 1.0

    def test_baseline_does_not_label_as_trained_model(self):
        from app.services.forecasting_service import ForecastingService

        settings = Settings(FORECASTING_MODEL="baseline")
        svc = ForecastingService(settings=settings)
        result = svc.predict_competitor_action({"cluster": "product_launch", "horizon_days": 14})
        assert result["model_version"] == "baseline"

    def test_sklearn_degraded_when_artifacts_missing(self):
        from app.services.forecasting_service import ForecastingService

        settings = Settings(FORECASTING_MODEL="sklearn")
        svc = ForecastingService.__new__(ForecastingService)
        svc._settings = settings
        svc._model = None
        svc._metadata = None

        result = svc.check_availability()
        assert result.status == ServiceStatus.DEGRADED

    def test_evaluate_prediction_raises_not_implemented(self):
        from app.services.forecasting_service import ForecastingService

        settings = Settings(FORECASTING_MODEL="baseline")
        svc = ForecastingService(settings=settings)
        with pytest.raises(NotImplementedError):
            svc.evaluate_prediction({}, {})


# ── Task 4 — Logging (no secrets) ─────────────────────────────────────────────


class TestLoggingSecretRedaction:
    def test_safe_summary_masks_key(self, caplog):
        with caplog.at_level(logging.INFO, logger="app.main"):
            s = Settings(LLM_API_KEY="gsk_supersecret", LLM_PROVIDER="disabled")
            summary = s.safe_summary()
        assert "gsk_supersecret" not in summary

    def test_llm_error_logs_do_not_contain_api_key(self, caplog):
        """Ensure that the API key is never written to the log."""
        from app.services.llm_service import LLMService

        settings = Settings(
            LLM_PROVIDER="openai-compatible",
            LLM_API_KEY="my-secret-key",
            LLM_TIMEOUT=1,
        )
        svc = LLMService(settings=settings)

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with caplog.at_level(logging.ERROR, logger="app.services.llm_service"):
            with patch("httpx.AsyncClient.post") as mock_post:
                mock_post.side_effect = httpx.HTTPStatusError(
                    "500", request=MagicMock(), response=mock_resp
                )
                import asyncio
                asyncio.get_event_loop().run_until_complete(
                    svc.generate_explanation("test")
                )

        for record in caplog.records:
            assert "my-secret-key" not in record.getMessage()


# ── Task 6 — Hindsight unavailability ────────────────────────────────────────


class TestHindsightUnavailability:
    @pytest.mark.asyncio
    async def test_connect_error_returns_unavailable(self):
        from app.services.hindsight_service import HindsightService

        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("refused")):
            svc = HindsightService()
            result = await svc.check_connectivity()
        assert result.status == ServiceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_timeout_returns_unavailable(self):
        from app.services.hindsight_service import HindsightService

        with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("timed out")):
            svc = HindsightService()
            result = await svc.check_connectivity()
        assert result.status == ServiceStatus.UNAVAILABLE
