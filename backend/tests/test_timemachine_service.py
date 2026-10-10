import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.schemas.evidence import EvidenceResponse, Provenance, ValidationStatus
from app.schemas.outcome import PredictionOutcomeResponse, EventOccurrence, EvaluationStatus
from app.schemas.cluster import StrategicCluster
from app.schemas.timemachine import TimeMachineReplayRequest
from app.services.timemachine_service import TimeMachineService


@pytest.fixture
def service():
    return TimeMachineService()


@pytest.fixture
def competitor_id():
    return uuid4()


def create_evidence(competitor_id, cluster: StrategicCluster, obs_time: datetime) -> EvidenceResponse:
    return EvidenceResponse(
        evidence_id=uuid4(),
        competitor_id=competitor_id,
        cluster=cluster,
        description=f"Evidence in {cluster.value}",
        observation_time=obs_time,
        provenance=Provenance.VERIFIED,
        validation_status=ValidationStatus.VALIDATED,
    )


def test_invalid_cutoff_range(service, competitor_id):
    t1 = datetime(2025, 6, 1, tzinfo=timezone.utc)
    t2 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    req = TimeMachineReplayRequest(
        competitor_id=competitor_id,
        start_cutoff=t1,
        end_cutoff=t2,
        step_days=30,
        horizon_days=30,
    )
    with pytest.raises(ValueError, match="start_cutoff cannot be later than end_cutoff"):
        service.run_replay(req, [])


def test_timeline_evidence_growth_and_snapshots(service, competitor_id):
    t_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t_mid = datetime(2025, 1, 15, tzinfo=timezone.utc)
    t_end = datetime(2025, 2, 1, tzinfo=timezone.utc)

    e1 = create_evidence(competitor_id, StrategicCluster.PRICING_PROMOTIONS, t_start)
    e2 = create_evidence(competitor_id, StrategicCluster.LOGISTICS_FULFILLMENT, t_mid)

    req = TimeMachineReplayRequest(
        competitor_id=competitor_id,
        start_cutoff=t_start,
        end_cutoff=t_end,
        step_days=15,
        horizon_days=30,
    )

    res = service.run_replay(req, [e1, e2], competitor_name="Acme Corp")

    assert res.competitor_id == competitor_id
    assert res.total_snapshots >= 2
    # Snapshot 0 (t_start): e1 available (1 item)
    assert res.snapshots[0].available_evidence_count == 1
    # Snapshot 1 (t_mid or later): e1 and e2 available (2 items)
    assert res.snapshots[-1].available_evidence_count == 2


def test_outcome_matching_and_evaluation(service, competitor_id):
    t_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t_end = datetime(2025, 1, 1, tzinfo=timezone.utc)

    e1 = create_evidence(competitor_id, StrategicCluster.PRICING_PROMOTIONS, t_start)

    req = TimeMachineReplayRequest(
        competitor_id=competitor_id,
        start_cutoff=t_start,
        end_cutoff=t_end,
        step_days=30,
        horizon_days=30,
    )

    pred_id = uuid4()
    outcome = PredictionOutcomeResponse(
        outcome_id=uuid4(),
        prediction_id=pred_id,
        occurrence=EventOccurrence.OCCURRED,
        window_start=t_start - timedelta(days=1),
        window_end=t_start + timedelta(days=35),
        status=EvaluationStatus.EVALUATED,
    )

    res = service.run_replay(req, [e1], outcomes_list=[outcome])

    assert res.total_snapshots == 1
    snap = res.snapshots[0]
    assert snap.outcome is not None
    assert snap.brier_score is not None
    assert snap.accuracy is not None
    assert res.mean_brier_score is not None
    assert res.mean_accuracy is not None
