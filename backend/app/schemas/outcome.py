from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum

class EvaluationStatus(str, Enum):
    PENDING = "pending"
    EVALUATED = "evaluated"

class EventOccurrence(str, Enum):
    OCCURRED = "occurred"
    NOT_OCCURRED = "not_occurred"
    UNKNOWN = "unknown"

class PredictionOutcomeBase(BaseModel):
    prediction_id: UUID
    occurrence: EventOccurrence = Field(default=EventOccurrence.UNKNOWN, description="Whether the target event occurred")
    window_start: datetime
    window_end: datetime
    evidence_ids: list[UUID] = Field(default_factory=list, description="Evidence supporting the outcome")
    metrics: dict = Field(default_factory=dict, description="Optional evaluation metrics")
    lesson_ids: list[UUID] = Field(default_factory=list, description="Optional lesson references")

class PredictionOutcomeCreate(PredictionOutcomeBase):
    pass

class PredictionOutcomeResponse(PredictionOutcomeBase):
    outcome_id: UUID
    status: EvaluationStatus = Field(default=EvaluationStatus.PENDING)
    evaluation_time: Optional[datetime] = None
