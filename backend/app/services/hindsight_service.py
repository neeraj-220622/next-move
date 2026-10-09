"""
Hindsight service — Phase 1 interface definition.

This module encapsulates all communication with the local Hindsight memory
server.  Only the client wrapper and connection-check logic are implemented
here; the full RECALL → ANALYZE → RETAIN workflow is deferred to Phase 5.

Design constraints
------------------
* All Hindsight SDK / HTTP calls live in this module.  No other module
  imports ``httpx`` or constructs Hindsight URLs directly.
* The service gracefully degrades: callers receive a clear status object
  rather than an unhandled exception when Hindsight is unavailable.
* The base URL and timeout are read from ``Settings``; they are never
  hard-coded here.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.schemas.common import DependencyInfo, ServiceStatus

logger = logging.getLogger(__name__)


class HindsightService:
    """
    Thin wrapper around the Hindsight memory server HTTP API.

    Phase 1 — implemented
    ─────────────────────
    * ``check_connectivity`` — probe the Hindsight health endpoint and
      return a ``DependencyInfo`` describing the server's availability.

    Phase 5 — planned (not yet implemented)
    ────────────────────────────────────────
    * ``store_evidence``    — persist a competitor signal as a memory.
    * ``recall_relevant``  — retrieve memories relevant to a given context.
    * ``retain_outcome``   — store a prediction outcome for future learning.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = self._settings.hindsight_base_url
        self._timeout = self._settings.hindsight_timeout

    # ── Connectivity check ────────────────────────────────────────────────────

    async def check_connectivity(self) -> DependencyInfo:
        """
        Probe the Hindsight server and return its availability status.

        Returns a ``DependencyInfo`` with ``status=ok`` on success or
        ``status=unavailable`` on any connection/timeout error.  This method
        never raises; callers should inspect the returned object.
        """
        url = f"{self._base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                if response.status_code < 400:
                    return DependencyInfo(
                        name="hindsight",
                        status=ServiceStatus.OK,
                        message=f"Reachable at {self._base_url}",
                        latency_ms=response.elapsed.total_seconds() * 1000,
                    )
                return DependencyInfo(
                    name="hindsight",
                    status=ServiceStatus.UNAVAILABLE,
                    message=(
                        f"Unexpected HTTP {response.status_code} from "
                        f"{self._base_url}"
                    ),
                )
        except httpx.ConnectError:
            logger.debug("Hindsight server not reachable at %s", self._base_url)
            return DependencyInfo(
                name="hindsight",
                status=ServiceStatus.UNAVAILABLE,
                message=f"Connection refused — is Hindsight running at {self._base_url}?",
            )
        except httpx.TimeoutException:
            logger.debug("Hindsight server timed out at %s", self._base_url)
            return DependencyInfo(
                name="hindsight",
                status=ServiceStatus.UNAVAILABLE,
                message=f"Timed out after {self._timeout}s — {self._base_url}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unexpected Hindsight error: %s", exc)
            return DependencyInfo(
                name="hindsight",
                status=ServiceStatus.UNKNOWN,
                message=f"Unexpected error: {exc}",
            )

    # ── Phase 5 stubs ────────────────────────────────────────────────────────
    # These signatures define the interface for the ML/memory developer.
    # Implementations will be added in Phase 5.

    async def store_evidence(self, evidence: dict[str, Any]) -> None:
        """
        [Phase 5] Persist a competitor signal as a Hindsight memory.

        Parameters
        ----------
        evidence:
            Structured competitor signal data to store.
        """
        raise NotImplementedError("store_evidence is planned for Phase 5.")

    async def recall_relevant(
        self, context: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        [Phase 5] Retrieve memories relevant to the given context string.

        Parameters
        ----------
        context:
            Natural-language description of the current analysis context.
        top_k:
            Maximum number of memories to return.
        """
        raise NotImplementedError("recall_relevant is planned for Phase 5.")

    async def retain_outcome(self, outcome: dict[str, Any]) -> None:
        """
        [Phase 5] Store a prediction outcome for future learning.

        Parameters
        ----------
        outcome:
            Structured prediction outcome data, including the original
            prediction and the observed real-world result.
        """
        raise NotImplementedError("retain_outcome is planned for Phase 5.")
