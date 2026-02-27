"""Tests for Qwen Cloud provider."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from qwenex.models.qwen_cloud import QwenCloudProvider
from qwenex.models.base import ProviderConfig


def test_qwen_config_creation():
    """Test QwenCloudProvider configuration."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/api/v1",
        timeout_sec=300
    )
    provider = QwenCloudProvider(config)
    assert provider.get_config().name == "qwen_cloud"
    assert provider.get_config().model == "qwen-max"


@pytest.mark.asyncio
async def test_qwen_health_check_success():
    """Test successful health check."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/api/v1"
    )
    provider = QwenCloudProvider(config)
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await provider.check_health()
        assert result is True


@pytest.mark.asyncio
async def test_qwen_health_check_failure():
    """Test failed health check."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/api/v1"
    )
    provider = QwenCloudProvider(config)
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.get.side_effect = Exception("Connection error")
        
        result = await provider.check_health()
        assert result is False


@pytest.mark.asyncio
async def test_qwen_complete():
    """Test completion request."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    
    mock_response = {
        "choices": [{
            "message": {"content": "Generated response"}
        }]
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        result = await provider.complete("Test prompt", system_prompt="You are helpful")
        assert result == "Generated response"


@pytest.mark.asyncio
async def test_qwen_stream():
    """Test streaming completion."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    
    chunks = ["Hello ", "world", "!"]
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.content.__aiter__.return_value = [
            f'data: {{"choices": [{{"delta": {{"content": "{chunk}"}}}}]}}\n'.encode()
            for chunk in chunks
        ]
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        result = []
        async for chunk in provider.stream("Test prompt"):
            result.append(chunk)
        
        assert result == chunks
