from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

from app.schemas.prediction import PredictionRequest
from app.schemas.evidence import EvidenceResponse
from .stages import StageResult

class OrchestrationContext(BaseModel):
    request: PredictionRequest
    
    # Accumulated state
    recalled_evidence: list[EvidenceResponse] = Field(default_factory=list)
    valid_historical_evidence: list[EvidenceResponse] = Field(default_factory=list)
    
    # Forecasting results
    probability: Optional[float] = None
    model_version: Optional[str] = None
    
    # LLM results
    explanation: Optional[str] = None
    
    # Trace tracking
    stage_results: list[StageResult] = Field(default_factory=list)
    
    def build_analysis_payload(self) -> dict[str, Any]:
        """Prepares the clean payload for the forecasting engine, excluding future data."""
        return {
            "competitor_id": str(self.request.competitor_id),
            "cluster": self.request.cluster,
            "cutoff_date": self.request.cutoff_date.isoformat(),
            "evidence_count": len(self.valid_historical_evidence),
            "evidence_ids": [str(e.evidence_id) for e in self.valid_historical_evidence],
            "horizon_days": self.request.horizon_days,
            "metadata": self.request.metadata
        }
