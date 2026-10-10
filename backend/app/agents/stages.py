from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class StageName(str, Enum):
    RECALL = "recall"
    ANALYZE = "analyze"
    PREDICT = "predict"
    EXPLAIN = "explain"
    RETAIN = "retain"

class StageStatus(str, Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"

class StageResult(BaseModel):
    stage: StageName
    status: StageStatus
    message: str = Field(..., description="Short explanation of the outcome")
    duration_ms: Optional[float] = None
    records_affected: list[str] = Field(default_factory=list)
