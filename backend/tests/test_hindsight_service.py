import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import uuid


from app.services.hindsight_service import HindsightService
from app.core.config import Settings
from app.agents.adapters import HindsightMemoryAdapter
from app.schemas.evidence import EvidenceResponse

@pytest.fixture
def mock_settings():
    return Settings(
        hindsight_base_url="http://fake-hindsight:8888",
        hindsight_timeout=5,
        llm_provider="disabled"
    )

@pytest.fixture
def mock_client():
    with patch("app.services.hindsight_service.Hindsight") as mock_cls:
        client_instance = MagicMock()
        client_instance.banks.create_or_update_bank = AsyncMock()
        
        # Async methods
        client_instance.arecall = AsyncMock()
        client_instance.aretain = AsyncMock()
        
        mock_cls.return_value = client_instance
        yield client_instance

@pytest.mark.asyncio
async def test_store_evidence_success(mock_settings, mock_client):
    service = HindsightService(mock_settings)
    
    mock_retain_response = MagicMock()
    mock_retain_response.success = True
    mock_client.aretain.return_value = mock_retain_response
    
    obs_time = datetime.now(timezone.utc)
    
    evidence = {
        "evidence_id": str(uuid.uuid4()),
        "competitor_id": str(uuid.uuid4()),
        "cluster": "pricing",
        "description": "Lowered prices",
        "observation_time": obs_time,
        "provenance": "verified"
    }
    
    await service.store_evidence(evidence)
    
    mock_client.banks.create_or_update_bank.assert_called_once()
    call_kwargs = mock_client.banks.create_or_update_bank.call_args.kwargs
    assert call_kwargs["bank_id"] == "nextmove"
    from hindsight_client_api.models.create_bank_request import CreateBankRequest
    assert isinstance(call_kwargs["create_bank_request"], CreateBankRequest)
    assert call_kwargs["create_bank_request"].name == "NextMove Memory"
    assert call_kwargs["create_bank_request"].retain_extraction_mode == "none"
    
    mock_client.aretain.assert_called_once()
    args, kwargs = mock_client.aretain.call_args
    assert kwargs["content"] == "Lowered prices"
    assert kwargs["metadata"]["cluster"] == "pricing"
    assert kwargs["metadata"]["type"] == "evidence"

@pytest.mark.asyncio
async def test_store_evidence_fails_when_success_false(mock_settings, mock_client):
    service = HindsightService(mock_settings)
    
    mock_retain_response = MagicMock()
    mock_retain_response.success = False
    mock_retain_response.items_count = 0
    mock_client.aretain.return_value = mock_retain_response
    
    with pytest.raises(RuntimeError, match="success=False"):
        await service.store_evidence({})

@pytest.mark.asyncio
async def test_recall_relevant_success(mock_settings, mock_client):
    service = HindsightService(mock_settings)
    
    mock_recall_response = MagicMock()
    result1 = MagicMock()
    result1.id = "mem-1"
    result1.text = "Competitor raised prices"
    result1.occurred_start = datetime.now(timezone.utc)
    result1.metadata = {
        "evidence_id": str(uuid.uuid4()),
        "competitor_id": str(uuid.uuid4()),
        "cluster": "pricing",
        "provenance": "verified"
    }
    
    # Missing timestamp
    result2 = MagicMock()
    result2.id = "mem-2"
    result2.text = "No time"
    result2.occurred_start = None
    result2.metadata = {}
    
    mock_recall_response.results = [result1, result2]
    mock_client.arecall.return_value = mock_recall_response
    
    results = await service.recall_relevant("context", top_k=5)
    
    assert len(results) == 1  # result2 is excluded
    assert results[0]["description"] == "Competitor raised prices"
    assert results[0]["cluster"] == "pricing"

@pytest.mark.asyncio
async def test_recall_unavailable_raises(mock_settings, mock_client):
    service = HindsightService(mock_settings)
    
    mock_client.arecall.side_effect = Exception("Connection error")
    
    with pytest.raises(RuntimeError, match="Hindsight recall failed"):
        await service.recall_relevant("context")

@pytest.mark.asyncio
async def test_uninitialized_bank_handled_by_ensure(mock_settings, mock_client):
    service = HindsightService(mock_settings)
    
    # Simulate API error on bank creation
    mock_client.banks.create_or_update_bank.side_effect = Exception("Unauthorized")
    
    with pytest.raises(RuntimeError, match="Hindsight server error: Unauthorized"):
        await service.store_evidence({})

@pytest.mark.asyncio
async def test_retain_outcome_success(mock_settings, mock_client):
    service = HindsightService(mock_settings)
    
    mock_retain_response = MagicMock()
    mock_retain_response.success = True
    mock_client.aretain.return_value = mock_retain_response
    
    await service.retain_outcome({
        "prediction_id": str(uuid.uuid4()),
        "competitor_id": str(uuid.uuid4()),
        "cluster": "pricing",
        "status": "completed",
        "probability": 0.9,
        "explanation": "Because"
    })
    
    mock_client.aretain.assert_called_once()
    args, kwargs = mock_client.aretain.call_args
    assert "Prediction: 0.9" in kwargs["content"]
    assert "Because" in kwargs["content"]
    assert kwargs["metadata"]["type"] == "prediction_outcome"

@pytest.mark.asyncio
async def test_adapter_maps_exceptions_to_not_implemented(mock_settings, mock_client):
    service = HindsightService(mock_settings)
    adapter = HindsightMemoryAdapter(service)
    
    mock_client.arecall.side_effect = Exception("SDK Error")
    
    with pytest.raises(NotImplementedError, match="Recall failed or unavailable"):
        await adapter.recall_evidence(uuid.uuid4(), "pricing")
        
    mock_client.aretain.side_effect = Exception("SDK Error")
    
    with pytest.raises(NotImplementedError, match="Retention failed or unavailable"):
        await adapter.retain_prediction(uuid.uuid4(), {})
