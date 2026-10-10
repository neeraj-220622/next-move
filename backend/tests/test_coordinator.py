import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from app.schemas.prediction import PredictionRequest
from app.schemas.evidence import EvidenceResponse, Provenance, ValidationStatus
from app.schemas.cluster import StrategicCluster
from app.agents.coordinator import WorkflowCoordinator
from app.agents.interfaces import MemoryStore, ForecastingEngine, ExplanationEngine
from app.agents.stages import StageStatus, StageName

class FakeMemoryStore(MemoryStore):
    def __init__(self, evidence=None, unavailable=False, fail=False):
        self.evidence = evidence or []
        self.unavailable = unavailable
        self.fail = fail
        self.retained = []

    async def recall_evidence(self, competitor_id: UUID, cluster: str) -> list[EvidenceResponse]:
        if self.unavailable: raise NotImplementedError()
        if self.fail: raise Exception("Boom")
        return self.evidence

    async def retain_prediction(self, prediction_id: UUID, payload: dict[str, Any]) -> bool:
        if self.unavailable: raise NotImplementedError()
        if self.fail: return False
        self.retained.append(payload)
        return True

class FakeForecasting(ForecastingEngine):
    def __init__(self, prob=None, status="completed", fail=False):
        self.prob = prob
        self.status = status
        self.fail = fail

    async def predict_action(self, context: dict[str, Any]) -> dict[str, Any]:
        if self.fail: raise Exception("Boom")
        return {"probability": self.prob, "status": self.status, "model_version": "v1"}

class FakeLLM(ExplanationEngine):
    def __init__(self, exp="Because", unavailable=False):
        self.exp = exp
        self.unavailable = unavailable

    async def generate_explanation(self, context: dict[str, Any]) -> Optional[str]:
        if self.unavailable: raise NotImplementedError()
        return self.exp

@pytest.fixture
def req():
    return PredictionRequest(
        competitor_id=uuid4(),
        cluster=StrategicCluster.PRICING_PROMOTIONS,
        cutoff_date=datetime.now(timezone.utc),
        horizon_days=30
    )

@pytest.fixture
def old_evidence(req):
    return EvidenceResponse(
        evidence_id=uuid4(),
        competitor_id=req.competitor_id,
        cluster=req.cluster,
        description="Old",
        observation_time=req.cutoff_date - timedelta(days=1),
        provenance=Provenance.VERIFIED,
        ingestion_time=req.cutoff_date - timedelta(days=1),
        validation_status=ValidationStatus.VALIDATED
    )

@pytest.fixture
def future_evidence(req):
    return EvidenceResponse(
        evidence_id=uuid4(),
        competitor_id=req.competitor_id,
        cluster=req.cluster,
        description="Future",
        observation_time=req.cutoff_date + timedelta(days=1),
        provenance=Provenance.VERIFIED,
        ingestion_time=req.cutoff_date + timedelta(days=1),
        validation_status=ValidationStatus.VALIDATED
    )

@pytest.mark.asyncio
async def test_successful_orchestration(req, old_evidence):
    mem = FakeMemoryStore(evidence=[old_evidence])
    fc = FakeForecasting(prob=0.8)
    llm = FakeLLM()
    
    coord = WorkflowCoordinator(mem, fc, llm)
    res, ctx = await coord.execute_prediction(req)
    
    assert res.probability == 0.8
    assert res.status == "completed"
    assert len(ctx.valid_historical_evidence) == 1
    assert len(mem.retained) == 1
    
    stages = {s.stage: s.status for s in ctx.stage_results}
    assert stages[StageName.RECALL] == StageStatus.COMPLETED
    assert stages[StageName.ANALYZE] == StageStatus.COMPLETED
    assert stages[StageName.PREDICT] == StageStatus.COMPLETED
    assert stages[StageName.EXPLAIN] == StageStatus.COMPLETED
    assert stages[StageName.RETAIN] == StageStatus.COMPLETED

@pytest.mark.asyncio
async def test_recall_unavailable(req):
    mem = FakeMemoryStore(unavailable=True)
    coord = WorkflowCoordinator(mem, FakeForecasting(), FakeLLM())
    res, ctx = await coord.execute_prediction(req)
    
    stages = {s.stage: s.status for s in ctx.stage_results}
    assert stages[StageName.RECALL] == StageStatus.UNAVAILABLE

@pytest.mark.asyncio
async def test_cutoff_filtering(req, old_evidence, future_evidence):
    mem = FakeMemoryStore(evidence=[old_evidence, future_evidence])
    coord = WorkflowCoordinator(mem, FakeForecasting(prob=0.5), FakeLLM())
    res, ctx = await coord.execute_prediction(req)
    
    assert len(ctx.recalled_evidence) == 2
    assert len(ctx.valid_historical_evidence) == 1
    assert ctx.valid_historical_evidence[0].description == "Old"

@pytest.mark.asyncio
async def test_forecasting_unavailable(req):
    fc = FakeForecasting(status="unavailable")
    coord = WorkflowCoordinator(FakeMemoryStore(), fc, FakeLLM())
    res, ctx = await coord.execute_prediction(req)
    
    assert res.probability is None
    assert res.status == "unavailable"
    stages = {s.stage: s.status for s in ctx.stage_results}
    assert stages[StageName.PREDICT] == StageStatus.UNAVAILABLE
    assert stages[StageName.EXPLAIN] == StageStatus.SKIPPED

@pytest.mark.asyncio
async def test_invalid_probability(req):
    fc = FakeForecasting(prob=1.5)
    coord = WorkflowCoordinator(FakeMemoryStore(), fc, FakeLLM())
    res, ctx = await coord.execute_prediction(req)
    
    assert res.probability is None
    stages = {s.stage: s.status for s in ctx.stage_results}
    assert stages[StageName.PREDICT] == StageStatus.FAILED

@pytest.mark.asyncio
async def test_unexpected_failure(req):
    fc = FakeForecasting(fail=True)
    coord = WorkflowCoordinator(FakeMemoryStore(), fc, FakeLLM())
    res, ctx = await coord.execute_prediction(req)
    
    stages = {s.stage: s.status for s in ctx.stage_results}
    assert stages[StageName.PREDICT] == StageStatus.FAILED
    assert res.probability is None
