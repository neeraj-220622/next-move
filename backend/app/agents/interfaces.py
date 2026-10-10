from typing import Protocol, Any, Optional
from datetime import datetime
from uuid import UUID

from app.schemas.evidence import EvidenceResponse
from app.schemas.memory import MemoryReference

class MemoryStore(Protocol):
    async def recall_evidence(self, competitor_id: UUID, cluster: str) -> list[EvidenceResponse]:
        ...
        
    async def retain_prediction(self, prediction_id: UUID, payload: dict[str, Any]) -> bool:
        ...

class ForecastingEngine(Protocol):
    async def predict_action(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Return a dict with keys like 'probability', 'model_version', 'status'
        """
        ...

class ExplanationEngine(Protocol):
    async def generate_explanation(self, context: dict[str, Any]) -> Optional[str]:
        ...
