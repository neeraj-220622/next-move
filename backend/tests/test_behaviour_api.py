import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from app.main import app
from app.db.repository import competitor_repo, evidence_repo
from app.schemas.competitor import CompetitorResponse
from app.schemas.evidence import EvidenceResponse, Provenance, ValidationStatus
from app.schemas.cluster import StrategicCluster

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_repos():
    competitor_repo.clear()
    evidence_repo.clear()
    yield
    competitor_repo.clear()
    evidence_repo.clear()


def test_get_competitor_behaviour_not_found():
    random_id = uuid4()
    response = client.get(f"/api/v1/behaviour/competitor/{random_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_post_analyze_behaviour_not_found():
    random_id = uuid4()
    response = client.post("/api/v1/behaviour/analyze", json={"competitor_id": str(random_id)})
    assert response.status_code == 404


def test_get_competitor_behaviour_success():
    comp_id = uuid4()
    now = datetime.now(timezone.utc)

    # Register competitor
    comp = CompetitorResponse(
        competitor_id=comp_id,
        name="Acme Corp",
        website="https://acme.com",
        description="Competitor",
        tracked_clusters=[StrategicCluster.PRICING_PROMOTIONS, StrategicCluster.LOGISTICS_FULFILLMENT],
        created_at=now,
        updated_at=now,
    )
    competitor_repo.add(comp_id, comp)

    # Add 2 evidence items
    e1_id = uuid4()
    e1 = EvidenceResponse(
        evidence_id=e1_id,
        competitor_id=comp_id,
        cluster=StrategicCluster.PRICING_PROMOTIONS,
        description="Price reduction",
        observation_time=now - timedelta(days=5),
        provenance=Provenance.VERIFIED,
        validation_status=ValidationStatus.VALIDATED,
    )
    evidence_repo.add(e1_id, e1)

    e2_id = uuid4()
    e2 = EvidenceResponse(
        evidence_id=e2_id,
        competitor_id=comp_id,
        cluster=StrategicCluster.LOGISTICS_FULFILLMENT,
        description="Warehouse expansion",
        observation_time=now,
        provenance=Provenance.VERIFIED,
        validation_status=ValidationStatus.VALIDATED,
    )
    evidence_repo.add(e2_id, e2)

    # GET endpoint call
    res = client.get(f"/api/v1/behaviour/competitor/{comp_id}")
    assert res.status_code == 200

    data = res.json()
    assert "profile" in data
    profile = data["profile"]
    assert profile["competitor_id"] == str(comp_id)
    assert profile["competitor_name"] == "Acme Corp"
    assert profile["sample_size"] == 2
    assert profile["low_sample_warning"] is True
    assert len(profile["cluster_frequencies"]) == 2
    assert profile["temporal_stats"]["total_observations"] == 2
    assert profile["temporal_stats"]["time_span_days"] == 5.0
    assert len(profile["backing_evidence_ids"]) == 2


def test_post_analyze_behaviour_success():
    comp_id = uuid4()
    now = datetime.now(timezone.utc)

    comp = CompetitorResponse(
        competitor_id=comp_id,
        name="Globex Tech",
        website="https://globex.com",
        description="Global competitor",
        tracked_clusters=[StrategicCluster.PRICING_PROMOTIONS],
        created_at=now,
        updated_at=now,
    )
    competitor_repo.add(comp_id, comp)

    res = client.post("/api/v1/behaviour/analyze", json={"competitor_id": str(comp_id)})
    assert res.status_code == 200

    data = res.json()
    assert "profile" in data
    profile = data["profile"]
    assert profile["competitor_id"] == str(comp_id)
    assert profile["competitor_name"] == "Globex Tech"
    assert profile["sample_size"] == 0
    assert profile["low_sample_warning"] is True
