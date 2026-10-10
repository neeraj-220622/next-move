from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum

from .cluster import StrategicCluster

class Provenance(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    SYNTHETIC = "synthetic"

class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"

class EvidenceBase(BaseModel):
    competitor_id: UUID
    cluster: StrategicCluster
    description: str = Field(..., description="Event description")
    source_url: Optional[str] = None
    observation_time: datetime = Field(..., description="Publication or observation timestamp")
    provenance: Provenance = Field(default=Provenance.UNVERIFIED)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional quality/confidence score")

class EvidenceCreate(EvidenceBase):
    pass

class EvidenceResponse(EvidenceBase):
    evidence_id: UUID = Field(..., description="Stable event/evidence identifier")
    ingestion_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
