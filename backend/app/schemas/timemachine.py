from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from app.schemas.behaviour import CompetitorBehaviourProfile
from app.schemas.prediction import PredictionResponse
from app.schemas.outcome import PredictionOutcomeResponse


class TimeMachineReplayRequest(BaseModel):
    """Request payload for launching a historical Time Machine replay simulation."""
    competitor_id: UUID
    start_cutoff: datetime = Field(..., description="Earliest cutoff timestamp for timeline simulation")
    end_cutoff: datetime = Field(..., description="Latest cutoff timestamp for timeline simulation")
    step_days: int = Field(30, gt=0, description="Step size in days between simulation snapshots")
    horizon_days: int = Field(30, gt=0, description="Forecast horizon window in days for each snapshot")


class TimeMachineSnapshot(BaseModel):
    """A single historical slice snapshot within a timeline replay."""
    snapshot_id: UUID = Field(default_factory=uuid4)
    cutoff_date: datetime = Field(..., description="Historical cutoff timestamp for this snapshot")
    available_evidence_count: int = Field(..., ge=0, description="Number of valid evidence items observed up to cutoff_date")
    behaviour_profile: CompetitorBehaviourProfile = Field(..., description="Historical behaviour profile computed at cutoff_date")
    prediction: PredictionResponse = Field(..., description="Historical prediction response computed at cutoff_date")
    outcome: Optional[PredictionOutcomeResponse] = Field(None, description="Actual outcome observed in [cutoff_date, cutoff_date + horizon_days]")
    brier_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Brier score error metric if outcome is known")
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Binary accuracy (1.0 = match, 0.0 = mismatch) if outcome is known")


class TimeMachineReplayResponse(BaseModel):
    """Complete historical timeline replay response."""
    replay_id: UUID = Field(default_factory=uuid4)
    competitor_id: UUID
    start_cutoff: datetime
    end_cutoff: datetime
    step_days: int
    horizon_days: int
    snapshots: List[TimeMachineSnapshot] = Field(default_factory=list)
    mean_brier_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Mean Brier score across evaluated snapshots")
    mean_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Mean prediction accuracy across evaluated snapshots")
    total_snapshots: int = Field(..., ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
