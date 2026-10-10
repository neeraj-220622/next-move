"""
LLM service — Phase 5B implementation.

This module provides a provider-agnostic interface for generating language
model explanations via an OpenAI-compatible API (Groq, local Ollama, etc.).

Design constraints
------------------
* The model name, endpoint, and provider type are read from ``Settings``.
* API keys are never logged or echoed; they appear only in HTTP headers.
* If the runtime is unavailable the service reports that clearly; it never
  raises an unhandled exception to the caller.
* Swapping providers (Groq ↔ OpenAI-compatible ↔ disabled) requires only a
  settings change, not code changes.
"""

from __future__ import annotations

import logging
import time

import httpx

from app.core.config import Settings, get_settings
from app.schemas.common import DependencyInfo, ServiceStatus

logger = logging.getLogger(__name__)


class LLMService:
    """
    Provider-agnostic wrapper for language model inference.

    Supported providers (configured via ``LLM_PROVIDER`` env var)
    ─────────────────────────────────────────────────────────────
    * ``local``              — OpenAI-compatible local endpoint (Ollama,
                               LM Studio, etc.).
    * ``openai-compatible``  — Any remote endpoint that speaks the OpenAI
                               Chat Completions API (e.g. Groq).
    * ``disabled``           — LLM features are explicitly turned off; all
                               calls return a clear "disabled" status.

    Phase 5B — implemented
    ──────────────────────
    * ``check_connectivity``   — probe the /models endpoint; distinguish
                                 connectivity from successful inference.
    * ``generate_explanation`` — call the chat completions endpoint and
                                 return the LLM-generated text.
    * ``summarise_evidence``   — condense a list of evidence strings into a
                                 concise paragraph via ``generate_explanation``.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    # ── Connectivity check ────────────────────────────────────────────────────

    async def check_connectivity(self) -> DependencyInfo:
        """
        Probe the configured LLM endpoint and return its availability.

        Returns a ``DependencyInfo`` with ``status=disabled`` when the
        provider is set to ``disabled``, ``status=ok`` on a successful
        probe (HTTP < 400 from the /models endpoint), and
        ``status=unavailable`` on connection / timeout failures.  Never
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
            headers = self._build_auth_headers()

            async with httpx.AsyncClient(
                timeout=timeout,
                headers=headers,
            ) as client:
                response = await client.get(probe_url)
                latency_ms = response.elapsed.total_seconds() * 1000
                if response.status_code < 400:
                    model_label = self._settings.llm_model or "(not configured)"
                    logger.info(
                        "LLM connectivity OK provider=%s model=%s latency_ms=%.1f",
                        provider,
                        model_label,
                        latency_ms,
                    )
                    return DependencyInfo(
                        name="llm",
                        status=ServiceStatus.OK,
                        message=(
                            f"Provider '{provider}' reachable. "
                            f"Model: {model_label}"
                        ),
                        latency_ms=latency_ms,
                    )
                logger.warning(
                    "LLM probe returned HTTP %s from %s",
                    response.status_code,
                    probe_url,
                )
                return DependencyInfo(
                    name="llm",
                    status=ServiceStatus.UNAVAILABLE,
                    message=(
                        f"HTTP {response.status_code} from {probe_url}. "
                        "Is the inference server running?"
                    ),
                )
        except httpx.ConnectError:
            logger.debug("LLM endpoint not reachable at %s", base_url)
            return DependencyInfo(
                name="llm",
                status=ServiceStatus.UNAVAILABLE,
                message=(
                    f"Connection refused — is the LLM server running "
                    f"at {base_url}?"
                ),
            )
        except httpx.TimeoutException:
            logger.warning("LLM probe timed out after %ss at %s", timeout, base_url)
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
                message=f"Unexpected error during connectivity probe.",
            )

    # ── Generation ────────────────────────────────────────────────────────────

    async def generate_explanation(self, prompt: str) -> str:
        """
        Generate a natural-language explanation via the configured LLM.

        Parameters
        ----------
        prompt:
            Structured prompt describing the competitor context.

        Returns
        -------
        str
            LLM-generated explanation text, or an error message string if
            the provider is unavailable.  Never raises.
        """
        provider = self._settings.llm_provider.lower()
        if provider == "disabled":
            return "LLM explanations are currently disabled."

        base_url = self._settings.llm_base_url.rstrip("/")
        if provider in ("local", "openai-compatible"):
            chat_url = f"{base_url}/chat/completions"
        else:
            return "Unsupported LLM provider configuration."

        headers = self._build_auth_headers()
        payload = {
            "model": self._settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.llm_timeout, headers=headers
            ) as client:
                response = await client.post(chat_url, json=payload)
                response.raise_for_status()
                data = response.json()
                latency_ms = (time.perf_counter() - t0) * 1000
                logger.info(
                    "LLM inference OK provider=%s model=%s latency_ms=%.1f",
                    provider,
                    self._settings.llm_model,
                    latency_ms,
                )
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            latency_ms = (time.perf_counter() - t0) * 1000
            status_code = exc.response.status_code
            if status_code == 401:
                category = "authentication_error"
            elif status_code == 429:
                category = "rate_limit"
            elif status_code in (503, 529):
                category = "service_unavailable"
            else:
                category = "http_error"
            logger.error(
                "LLM %s provider=%s status=%s latency_ms=%.1f",
                category,
                provider,
                status_code,
                latency_ms,
            )
            if status_code == 401:
                return "Error: LLM authentication failed. Check LLM_API_KEY."
            if status_code == 429:
                return "Error: LLM rate limit exceeded. Please retry later."
            return f"Error: LLM returned HTTP {status_code}."
        except httpx.TimeoutException:
            latency_ms = (time.perf_counter() - t0) * 1000
            logger.error(
                "LLM timeout provider=%s after %.1fms",
                provider,
                latency_ms,
            )
            return f"Error: LLM request timed out after {self._settings.llm_timeout}s."
        except Exception as exc:  # noqa: BLE001
            latency_ms = (time.perf_counter() - t0) * 1000
            logger.error(
                "LLM unexpected error provider=%s latency_ms=%.1f: %s",
                provider,
                latency_ms,
                type(exc).__name__,
            )
            return "Error: LLM generation failed unexpectedly."

    async def summarise_evidence(self, evidence_items: list[str]) -> str:
        """
        Distil a list of evidence items into a concise paragraph.

        Parameters
        ----------
        evidence_items:
            Raw evidence strings collected from competitor signals.

        Returns
        -------
        str
            LLM-generated summary paragraph, or an error message string.
        """
        if not evidence_items:
            return "No evidence available to summarise."

        prompt = (
            "Please summarise the following evidence points into a single, "
            "concise paragraph:\n\n" + "\n".join(f"- {e}" for e in evidence_items)
        )
        return await self.generate_explanation(prompt)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_auth_headers(self) -> dict[str, str]:
        """Build HTTP headers with Authorization if an API key is configured."""
        headers: dict[str, str] = {}
        api_key = self._settings.llm_api_key
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers
