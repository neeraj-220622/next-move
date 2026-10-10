from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from .cluster import StrategicCluster

class CompetitorBase(BaseModel):
    name: str = Field(..., description="Competitor display name")
    website: Optional[str] = Field(None, description="Optional website URL")
    description: Optional[str] = Field(None, description="Optional description")
    tracked_clusters: list[StrategicCluster] = Field(default_factory=list, description="Strategic clusters being monitored")

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorResponse(CompetitorBase):
    competitor_id: UUID = Field(..., description="Stable identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
