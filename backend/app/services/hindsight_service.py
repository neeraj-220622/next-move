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
import asyncio
from datetime import datetime
import uuid

import httpx
from hindsight_client import Hindsight

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
        self.client = Hindsight(base_url=self._base_url, timeout=self._timeout)
        self.bank_id = "nextmove"

    async def _ensure_bank_exists(self) -> None:
        try:
            from hindsight_client_api.models.create_bank_request import CreateBankRequest
            req = CreateBankRequest(name="NextMove Memory", retain_extraction_mode="none")
            await self.client.banks.create_or_update_bank(
                bank_id=self.bank_id,
                create_bank_request=req,
            )
        except Exception as e:
            logger.error("Failed to ensure bank exists: %s", e)
            raise RuntimeError(f"Hindsight server error: {e}")

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

    async def store_evidence(self, evidence: dict[str, Any]) -> None:
        """
        [Phase 5A] Persist a competitor signal as a Hindsight memory.
        """
        try:
            await self._ensure_bank_exists()
            
            obs_time = evidence.get("observation_time")
            ts = None
            if isinstance(obs_time, str):
                try:
                    ts = datetime.fromisoformat(obs_time.replace("Z", "+00:00"))
                except ValueError:
                    pass
            elif isinstance(obs_time, datetime):
                ts = obs_time
                
            resp = await self.client.aretain(
                bank_id=self.bank_id,
                content=evidence.get("description", ""),
                metadata={
                    "evidence_id": str(evidence.get("evidence_id")),
                    "competitor_id": str(evidence.get("competitor_id")),
                    "cluster": str(evidence.get("cluster")),
                    "provenance": str(evidence.get("provenance", "unknown")),
                    "observation_time": str(obs_time) if obs_time else "",
                    "ingestion_time": str(evidence.get("ingestion_time", "")),
                    "type": "evidence"
                },
                timestamp=ts
            )
            if not resp.success:
                raise RuntimeError(f"Hindsight SDK returned success=False. items_count={resp.items_count}")
        except Exception as e:
            logger.error(f"Hindsight store_evidence failed: {e}")
            raise RuntimeError(f"Hindsight retention failed: {e}")

    async def recall_relevant(
        self, context: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        [Phase 5A] Retrieve memories relevant to the given context string.
        """
        try:
            await self._ensure_bank_exists()
            
            response = await self.client.arecall(
                bank_id=self.bank_id,
                query=context,
                max_source_facts_tokens=4096
            )
            
            results = []
            for r in response.results:
                if len(results) >= top_k:
                    break
                    
                md = r.metadata or {}
                obs_time = r.occurred_start or md.get("observation_time")
                
                if not obs_time:
                    logger.warning(f"Excluding memory {r.id} due to insufficient timestamp metadata")
                    continue
                    
                if isinstance(obs_time, datetime):
                    obs_time_str = obs_time.isoformat()
                else:
                    obs_time_str = str(obs_time)
                    
                results.append({
                    "evidence_id": md.get("evidence_id") or str(uuid.uuid4()),
                    "competitor_id": md.get("competitor_id") or str(uuid.uuid4()),
                    "cluster": md.get("cluster") or "unknown",
                    "description": r.text,
                    "observation_time": obs_time_str,
                    "provenance": md.get("provenance") or "synthetic",
                    "ingestion_time": md.get("ingestion_time") or datetime.now().isoformat(),
                    "validation_status": "validated"
                })
            return results
        except Exception as e:
            logger.error(f"Hindsight recall_relevant failed: {e}")
            raise RuntimeError(f"Hindsight recall failed: {e}")

    async def retain_outcome(self, outcome: dict[str, Any]) -> None:
        """
        [Phase 5A] Store a prediction outcome for future learning.
        """
        try:
            await self._ensure_bank_exists()
            
            content = f"Prediction: {outcome.get('probability', 'unknown')} | Status: {outcome.get('status')}"
            if outcome.get("explanation"):
                content += f" | Explanation: {outcome['explanation']}"
                
            resp = await self.client.aretain(
                bank_id=self.bank_id,
                content=content,
                metadata={
                    "prediction_id": str(outcome.get("prediction_id")),
                    "competitor_id": str(outcome.get("competitor_id")),
                    "cluster": str(outcome.get("cluster")),
                    "type": "prediction_outcome"
                }
            )
            if not resp.success:
                raise RuntimeError("Hindsight SDK returned success=False for retain_outcome")
        except Exception as e:
            logger.error(f"Hindsight retain_outcome failed: {e}")
            raise RuntimeError(f"Hindsight retention failed: {e}")
