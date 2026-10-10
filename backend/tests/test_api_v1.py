import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.db.repository import competitor_repo, prediction_repo, evidence_repo
from app.schemas.cluster import StrategicCluster

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_repos():
    competitor_repo.clear()
    prediction_repo.clear()
    evidence_repo.clear()
    yield

def test_register_competitor():
    response = client.post("/api/v1/competitors/", json={
        "name": "Amazon",
        "website": "https://amazon.com",
        "description": "Retail giant",
        "tracked_clusters": [StrategicCluster.LOGISTICS_FULFILLMENT.value]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Amazon"
    assert "competitor_id" in data

def test_get_competitor():
    comp = client.post("/api/v1/competitors/", json={
        "name": "Walmart",
        "tracked_clusters": []
    }).json()
    comp_id = comp["competitor_id"]

    response = client.get(f"/api/v1/competitors/{comp_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Walmart"

def test_get_unknown_competitor():
    response = client.get(f"/api/v1/competitors/{uuid4()}")
    assert response.status_code == 404

def test_duplicate_competitor():
    client.post("/api/v1/competitors/", json={"name": "eBay", "tracked_clusters": []})
    response = client.post("/api/v1/competitors/", json={"name": "ebay", "tracked_clusters": []})
    assert response.status_code == 409

def test_request_prediction():
    comp = client.post("/api/v1/competitors/", json={"name": "Target", "tracked_clusters": []}).json()
    comp_id = comp["competitor_id"]
    
    response = client.post("/api/v1/predict/", json={
        "competitor_id": comp_id,
        "cluster": StrategicCluster.PRICING_PROMOTIONS.value,
        "cutoff_date": datetime.now(timezone.utc).isoformat(),
        "horizon_days": 30,
        "evidence_ids": [],
        "metadata": {}
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["probability"] is not None

def test_get_prediction():
    comp = client.post("/api/v1/competitors/", json={"name": "Macy", "tracked_clusters": []}).json()
    pred = client.post("/api/v1/predict/", json={
        "competitor_id": comp["competitor_id"],
        "cluster": StrategicCluster.PRICING_PROMOTIONS.value,
        "cutoff_date": datetime.now(timezone.utc).isoformat(),
        "horizon_days": 30,
        "evidence_ids": [],
        "metadata": {}
    }).json()
    
    res = client.get(f"/api/v1/predict/{pred['prediction_id']}")
    assert res.status_code == 200
    assert res.json()["prediction_id"] == pred["prediction_id"]

def test_get_unknown_prediction():
    res = client.get(f"/api/v1/predict/{uuid4()}")
    assert res.status_code == 404

def test_register_evidence():
    comp = client.post("/api/v1/competitors/", json={"name": "Best Buy", "tracked_clusters": []}).json()
    
    response = client.post("/api/v1/evidence/", json={
        "competitor_id": comp["competitor_id"],
        "cluster": StrategicCluster.MARKETPLACE_SELLER.value,
        "description": "New seller fees",
        "observation_time": datetime.now(timezone.utc).isoformat(),
        "provenance": "unverified"
    })
    
    assert response.status_code == 201
    assert response.json()["validation_status"] == "pending"
