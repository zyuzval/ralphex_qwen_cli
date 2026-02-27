"""Tests for OpenAI provider."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from qwenex.models.openai import OpenAIProvider
from qwenex.models.base import ProviderConfig


def test_openai_config_creation():
    """Test OpenAIProvider configuration."""
    config = ProviderConfig(
        name="openai",
        model="gpt-4o",
        api_key="sk-test123",
        base_url="https://api.openai.com/v1",
        timeout_sec=300
    )
    provider = OpenAIProvider(config)
    assert provider.get_config().name == "openai"
    assert provider.get_config().model == "gpt-4o"


@pytest.mark.asyncio
async def test_openai_complete():
    """Test completion request."""
    config = ProviderConfig(
        name="openai",
        model="gpt-4o",
        api_key="sk-test123"
    )
    provider = OpenAIProvider(config)
    
    mock_response = {
        "choices": [{
            "message": {"content": "Generated response"}
        }]
    }
    
    mock_response_obj = MagicMock()
    mock_response_obj.status = 200
    mock_response_obj.json = AsyncMock(return_value=mock_response)
    mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
    mock_response_obj.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response_obj)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await provider.complete("Test prompt", system_prompt="You are helpful")
        assert result == "Generated response"
