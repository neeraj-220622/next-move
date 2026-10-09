"""
LLM service — Phase 1 interface definition.

This module provides a provider-agnostic interface for generating language
model explanations.  Phase 1 establishes the interface and connectivity probe
only.  The full generation pipeline is deferred to Phase 5.

Design constraints
------------------
* The model name, endpoint, and provider type are read from ``Settings``.
* If the runtime is unavailable the service reports that clearly; it never
  raises an unhandled exception.
* Swapping providers (Qwen ↔ OpenAI-compatible ↔ disabled) requires only a
  settings change, not code changes.
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import Settings, get_settings
from app.schemas.common import DependencyInfo, ServiceStatus

logger = logging.getLogger(__name__)


class LLMService:
    """
    Provider-agnostic wrapper for local language model inference.

    Supported providers (configured via ``LLM_PROVIDER`` env var)
    ─────────────────────────────────────────────────────────────
    * ``local``              — OpenAI-compatible local endpoint (Ollama,
                               LM Studio, etc.).  Qwen models are used here.
    * ``openai-compatible``  — Any remote endpoint that speaks the OpenAI
                               Chat Completions API.
    * ``disabled``           — LLM features are explicitly turned off; all
                               calls return a clear "disabled" status.

    Phase 1 — implemented
    ─────────────────────
    * ``check_connectivity`` — probe the configured endpoint and return a
      ``DependencyInfo`` describing availability.

    Phase 5 — planned
    ──────────────────
    * ``generate_explanation`` — generate a natural-language explanation for
      a competitor action or prediction.
    * ``summarise_evidence``   — distil a list of evidence items into a
      concise analysis paragraph.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    # ── Connectivity check ────────────────────────────────────────────────────

    async def check_connectivity(self) -> DependencyInfo:
        """
        Probe the configured LLM endpoint and return its availability.

        Returns a ``DependencyInfo`` with ``status=disabled`` when the
        provider is set to ``disabled``, ``status=ok`` on a successful
        probe, and ``status=unavailable`` on connection failures.  Never
        raises.
        """
        provider = self._settings.llm_provider.lower()

        if provider == "disabled":
            return DependencyInfo(
                name="llm",
                status=ServiceStatus.DISABLED,
                message="LLM provider is set to 'disabled' in configuration.",
            )

        base_url = self._settings.llm_base_url
        timeout = self._settings.llm_timeout

        # For local / openai-compatible providers, probe the models endpoint.
        probe_url = f"{base_url.rstrip('/')}/models"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(probe_url)
                if response.status_code < 400:
                    model_label = self._settings.llm_model or "(not configured)"
                    return DependencyInfo(
                        name="llm",
                        status=ServiceStatus.OK,
                        message=(
                            f"Provider '{provider}' reachable. "
                            f"Model: {model_label}"
                        ),
                        latency_ms=response.elapsed.total_seconds() * 1000,
                    )
                return DependencyInfo(
                    name="llm",
                    status=ServiceStatus.UNAVAILABLE,
                    message=(
                        f"HTTP {response.status_code} from {probe_url}. "
                        "Is the local inference server running?"
                    ),
                )
        except httpx.ConnectError:
            logger.debug("LLM endpoint not reachable at %s", base_url)
            return DependencyInfo(
                name="llm",
                status=ServiceStatus.UNAVAILABLE,
                message=(
                    f"Connection refused — is the local LLM server running "
                    f"at {base_url}?"
                ),
            )
        except httpx.TimeoutException:
            return DependencyInfo(
                name="llm",
                status=ServiceStatus.UNAVAILABLE,
                message=f"Timed out after {timeout}s — {base_url}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unexpected LLM probe error: %s", exc)
            return DependencyInfo(
                name="llm",
                status=ServiceStatus.UNKNOWN,
                message=f"Unexpected error: {exc}",
            )

    # ── Phase 5 stubs ────────────────────────────────────────────────────────

    async def generate_explanation(self, prompt: str) -> str:
        """
        [Phase 5] Generate a natural-language explanation for an analysis.

        Parameters
        ----------
        prompt:
            Structured prompt describing the competitor context.

        Returns
        -------
        str
            LLM-generated explanation text.
        """
        raise NotImplementedError("generate_explanation is planned for Phase 5.")

    async def summarise_evidence(self, evidence_items: list[str]) -> str:
        """
        [Phase 5] Distil a list of evidence items into a concise paragraph.

        Parameters
        ----------
        evidence_items:
            Raw evidence strings collected from competitor signals.
        """
        raise NotImplementedError("summarise_evidence is planned for Phase 5.")
