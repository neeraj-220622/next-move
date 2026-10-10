from uuid import UUID
from typing import Any, Optional

from app.schemas.evidence import EvidenceResponse
from app.services.hindsight_service import HindsightService
from app.services.forecasting_service import ForecastingService
from app.services.llm_service import LLMService

from .interfaces import MemoryStore, ForecastingEngine, ExplanationEngine

class HindsightMemoryAdapter(MemoryStore):
    def __init__(self, service: HindsightService):
        self.svc = service

    async def recall_evidence(self, competitor_id: UUID, cluster: str) -> list[EvidenceResponse]:
        try:
            records = await self.svc.recall_relevant(context=f"competitor {competitor_id} cluster {cluster}")
            return [EvidenceResponse(**r) for r in records]
        except Exception:
            raise NotImplementedError("Recall failed or unavailable")

    async def retain_prediction(self, prediction_id: UUID, payload: dict[str, Any]) -> bool:
        try:
            await self.svc.retain_outcome(payload)
            return True
        except Exception:
            # Raise NotImplementedError so the coordinator marks it as unavailable/failed
            raise NotImplementedError("Retention failed or unavailable")

class ForecastingAdapter(ForecastingEngine):
    def __init__(self, service: ForecastingService):
        self.svc = service

    async def predict_action(self, context: dict[str, Any]) -> dict[str, Any]:
        # Raises NotImplementedError inside service
        return self.svc.predict_competitor_action(context)

class LLMAdapter(ExplanationEngine):
    def __init__(self, service: LLMService):
        self.svc = service

    async def generate_explanation(self, context: dict[str, Any]) -> Optional[str]:
        # Raises NotImplementedError inside service
        return await self.svc.generate_explanation(str(context))
