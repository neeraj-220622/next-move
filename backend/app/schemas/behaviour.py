from datetime import datetime, timezone
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum

from app.schemas.cluster import StrategicCluster
from app.schemas.evidence import Provenance

class ActionFrequency(BaseModel):
    """Frequency stats for a specific strategic cluster."""
    cluster: StrategicCluster
    count: int = Field(..., ge=0, description="Total count of observed actions in this cluster")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total observed actions")

class TransitionProbability(BaseModel):
    """1st-order Markov transition probability between consecutive actions."""
    from_cluster: StrategicCluster
    to_cluster: StrategicCluster
    count: int = Field(..., ge=0, description="Number of observed sequential transitions")
    probability: float = Field(..., ge=0.0, le=1.0, description="Conditional probability P(To | From)")

class TemporalStats(BaseModel):
    """Time-series observation stats."""
    total_observations: int = Field(..., ge=0)
    first_observed: Optional[datetime] = Field(None, description="Earliest observation timestamp")
    last_observed: Optional[datetime] = Field(None, description="Latest observation timestamp")
    time_span_days: float = Field(0.0, ge=0.0, description="Total span in days between first and last observation")
    avg_days_between_events: float = Field(0.0, ge=0.0, description="Average gap in days between consecutive events")
    event_velocity_per_day: float = Field(0.0, ge=0.0, description="Average events per day over the time span")

class RecurringPattern(BaseModel):
    """Detected recurring sequence pattern of actions."""
    pattern_id: str = Field(..., description="Unique pattern key e.g. PATTERN_PRICING_TO_MARKETPLACE")
    sequence: List[StrategicCluster] = Field(..., description="Ordered list of clusters forming the sequence")
    occurrences: int = Field(..., ge=1, description="Number of times this sequence pattern occurred")
    avg_interval_days: float = Field(0.0, ge=0.0, description="Average days between sequence occurrences")
    evidence_ids: List[UUID] = Field(default_factory=list, description="IDs of evidence supporting this pattern")

class ProvenanceBreakdown(BaseModel):
    """Counts by data provenance type."""
    verified: int = Field(0, ge=0)
    unverified: int = Field(0, ge=0)
    synthetic: int = Field(0, ge=0)

class ClusterConfidenceInterval(BaseModel):
    """Wilson score 95% confidence interval for a cluster's proportion."""
    cluster: StrategicCluster
    proportion: float = Field(..., ge=0.0, le=1.0)
    ci_lower: float = Field(..., ge=0.0, le=1.0)
    ci_upper: float = Field(..., ge=0.0, le=1.0)

class CompetitorBehaviourProfile(BaseModel):
    """Complete behavior profile for a competitor derived from observed evidence."""
    competitor_id: UUID
    competitor_name: Optional[str] = Field(None, description="Competitor name if known")
    sample_size: int = Field(..., ge=0, description="Total number of valid evidence observations analyzed")
    provenance_breakdown: ProvenanceBreakdown
    cluster_frequencies: List[ActionFrequency] = Field(default_factory=list)
    transition_matrix: List[TransitionProbability] = Field(default_factory=list)
    temporal_stats: TemporalStats
    recurring_patterns: List[RecurringPattern] = Field(default_factory=list)
    entropy_score: float = Field(0.0, ge=0.0, description="Shannon entropy of cluster distribution (higher = more erratic)")
    confidence_intervals: List[ClusterConfidenceInterval] = Field(default_factory=list)
    low_sample_warning: bool = Field(False, description="Flagged true if sample size < 5 (higher statistical uncertainty)")
    backing_evidence_ids: List[UUID] = Field(default_factory=list, description="List of all evidence IDs included in analysis")
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BehaviourAnalysisRequest(BaseModel):
    """Request payload for behavior analysis."""
    competitor_id: UUID
    cutoff_date: Optional[datetime] = Field(None, description="Optional timestamp cutoff for analysis")
    start_date: Optional[datetime] = Field(None, description="Optional start timestamp filter")

class BehaviourAnalysisResponse(BaseModel):
    """Response payload enclosing the behavior profile."""
    profile: CompetitorBehaviourProfile
    request_id: Optional[str] = None
