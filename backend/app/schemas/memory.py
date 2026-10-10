from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum

from .cluster import StrategicCluster
from .evidence import Provenance

class MemoryCategory(str, Enum):
    HISTORICAL_EVIDENCE = "historical_evidence"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    PREDICTION = "prediction"
    OUTCOME = "outcome"
    LESSON = "lesson"

class MemoryReference(BaseModel):
    memory_id: UUID = Field(..., description="Memory identifier or reference")
    competitor_id: Optional[UUID] = None
    cluster: Optional[StrategicCluster] = None
    category: MemoryCategory
    content: str = Field(..., description="Content or summary")
    evidence_ids: list[UUID] = Field(default_factory=list)
    observation_time: Optional[datetime] = None
    provenance: Provenance = Field(default=Provenance.UNVERIFIED)
    metadata: dict = Field(default_factory=dict)
