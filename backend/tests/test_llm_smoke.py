import pytest
import os
from app.services.llm_service import LLMService

@pytest.mark.asyncio
async def test_llm_smoke():
    # Only run if a real API key is present in the environment (which it is for local testing)
    service = LLMService()
    if not service._settings.llm_api_key or service._settings.llm_provider != "openai-compatible":
        pytest.skip("Skipping smoke test: missing real API key or not using openai-compatible provider")
    
    # 1. Connectivity test
    info = await service.check_connectivity()
    assert info.status.value == "ok", f"Connectivity check failed: {info.message}"

    # 2. Inference test
    prompt = "Reply with exactly one word: 'SmokeTestPass'."
    response = await service.generate_explanation(prompt)
    assert "SmokeTestPass" in response, f"Unexpected generation response: {response}"
