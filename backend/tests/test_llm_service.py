import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_service import LLMService
from app.core.config import Settings
import httpx

@pytest.fixture
def mock_settings():
    return Settings(
        llm_provider="openai-compatible",
        llm_base_url="https://api.groq.com/openai/v1",
        llm_model="openai/gpt-oss-120b",
        llm_api_key="fake-key",
        llm_timeout=1
    )

@pytest.fixture
def llm_service(mock_settings):
    return LLMService(settings=mock_settings)

@pytest.mark.asyncio
async def test_generate_explanation_success(llm_service):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is an explanation."}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = await llm_service.generate_explanation("Test prompt")
        assert result == "This is an explanation."
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["messages"][0]["content"] == "Test prompt"
        assert kwargs["json"]["model"] == "openai/gpt-oss-120b"

@pytest.mark.asyncio
async def test_summarise_evidence_success(llm_service):
    with patch("app.services.llm_service.LLMService.generate_explanation") as mock_gen:
        mock_gen.return_value = "Summarised evidence."
        
        result = await llm_service.summarise_evidence(["evidence 1", "evidence 2"])
        
        assert result == "Summarised evidence."
        mock_gen.assert_called_once()
        args, kwargs = mock_gen.call_args
        assert "evidence 1" in args[0]
        assert "evidence 2" in args[0]

@pytest.mark.asyncio
async def test_generate_explanation_disabled(mock_settings):
    mock_settings.llm_provider = "disabled"
    service = LLMService(settings=mock_settings)
    result = await service.generate_explanation("Test")
    assert result == "LLM explanations are currently disabled."

@pytest.mark.asyncio
async def test_generate_explanation_http_error(llm_service):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=mock_response)
        
        result = await llm_service.generate_explanation("Test")
        assert result == "Error: LLM returned HTTP 500."
