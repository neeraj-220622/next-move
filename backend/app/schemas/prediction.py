from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from .cluster import StrategicCluster

class PredictionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"

class PredictionRequest(BaseModel):
    competitor_id: UUID
    cluster: StrategicCluster
    cutoff_date: datetime = Field(..., description="Forecast reference timestamp")
    horizon_days: int = Field(30, gt=0, description="Forecast horizon in days")
    evidence_ids: list[UUID] = Field(default_factory=list, description="Evidence references")
    metadata: dict = Field(default_factory=dict, description="Optional metadata")

class PredictionResponse(BaseModel):
    prediction_id: UUID
    competitor_id: UUID
    cluster: StrategicCluster
    cutoff_date: datetime
    horizon_days: int
    probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Forecast probability. Null if pending/unavailable")
    model_version: Optional[str] = None
    explanation: Optional[str] = Field(None, description="LLM-generated natural-language explanation for the prediction")
    evidence_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: PredictionStatus
