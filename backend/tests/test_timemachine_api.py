import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from app.main import app
from app.db.repository import (
    competitor_repo,
    evidence_repo,
    outcome_repo,
    timemachine_repo,
    prediction_repo,
)
from app.schemas.competitor import CompetitorResponse
from app.schemas.evidence import EvidenceResponse, Provenance, ValidationStatus
from app.schemas.cluster import StrategicCluster
from app.schemas.outcome import EventOccurrence

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_repos():
    competitor_repo.clear()
    evidence_repo.clear()
    outcome_repo.clear()
    timemachine_repo.clear()
    prediction_repo.clear()
    yield
    competitor_repo.clear()
    evidence_repo.clear()
    outcome_repo.clear()
    timemachine_repo.clear()
    prediction_repo.clear()


def test_outcome_registration_and_retrieval():
    pred_id = uuid4()
    t_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t_end = datetime(2025, 2, 1, tzinfo=timezone.utc)

    # Register outcome
    payload = {
        "prediction_id": str(pred_id),
        "occurrence": "occurred",
        "window_start": t_start.isoformat(),
        "window_end": t_end.isoformat(),
    }
    res = client.post("/api/v1/outcomes/", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["prediction_id"] == str(pred_id)
    assert data["occurrence"] == "occurred"

    # Get outcome
    get_res = client.get(f"/api/v1/outcomes/prediction/{pred_id}")
    assert get_res.status_code == 200
    assert get_res.json()["prediction_id"] == str(pred_id)


def test_outcome_not_found():
    res = client.get(f"/api/v1/outcomes/prediction/{uuid4()}")
    assert res.status_code == 404


def test_timemachine_replay_not_found():
    res = client.get(f"/api/v1/timemachine/replay/{uuid4()}")
    assert res.status_code == 404


def test_timemachine_replay_invalid_cutoff():
    comp_id = uuid4()
    t1 = datetime(2025, 6, 1, tzinfo=timezone.utc)
    t2 = datetime(2025, 1, 1, tzinfo=timezone.utc)

    comp = CompetitorResponse(
        competitor_id=comp_id,
        name="Test Corp",
        website="https://test.com",
        description="Competitor",
        tracked_clusters=[StrategicCluster.PRICING_PROMOTIONS],
        created_at=t2,
        updated_at=t2,
    )
    competitor_repo.add(comp_id, comp)

    payload = {
        "competitor_id": str(comp_id),
        "start_cutoff": t1.isoformat(),
        "end_cutoff": t2.isoformat(),
        "step_days": 30,
        "horizon_days": 30,
    }
    res = client.post("/api/v1/timemachine/replay", json=payload)
    assert res.status_code == 400
    assert "start_cutoff cannot be later than end_cutoff" in res.json()["detail"]


def test_timemachine_replay_success():
    comp_id = uuid4()
    t_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t_end = datetime(2025, 2, 1, tzinfo=timezone.utc)

    comp = CompetitorResponse(
        competitor_id=comp_id,
        name="Omni Corp",
        website="https://omni.com",
        description="Omni Competitor",
        tracked_clusters=[StrategicCluster.PRICING_PROMOTIONS],
        created_at=t_start,
        updated_at=t_start,
    )
    competitor_repo.add(comp_id, comp)

    e1_id = uuid4()
    e1 = EvidenceResponse(
        evidence_id=e1_id,
        competitor_id=comp_id,
        cluster=StrategicCluster.PRICING_PROMOTIONS,
        description="Price cut",
        observation_time=t_start,
        provenance=Provenance.VERIFIED,
        validation_status=ValidationStatus.VALIDATED,
    )
    evidence_repo.add(e1_id, e1)

    payload = {
        "competitor_id": str(comp_id),
        "start_cutoff": t_start.isoformat(),
        "end_cutoff": t_end.isoformat(),
        "step_days": 15,
        "horizon_days": 30,
    }

    res = client.post("/api/v1/timemachine/replay", json=payload)
    assert res.status_code == 201

    data = res.json()
    assert "replay_id" in data
    assert data["competitor_id"] == str(comp_id)
    assert data["total_snapshots"] >= 2
    replay_id = data["replay_id"]

    # GET endpoint call
    get_res = client.get(f"/api/v1/timemachine/replay/{replay_id}")
    assert get_res.status_code == 200
    assert get_res.json()["replay_id"] == replay_id
