"""Tests for Ollama provider."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from qwenex.models.ollama import OllamaProvider
from qwenex.models.base import ProviderConfig


def test_ollama_config_creation():
    """Test OllamaProvider configuration."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434",
        timeout_sec=300
    )
    provider = OllamaProvider(config)
    assert provider.get_config().name == "ollama"
    assert provider.get_config().model == "llama3.1:8b"


@pytest.mark.asyncio
async def test_ollama_health_check_success():
    """Test successful health check."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = OllamaProvider(config)
    
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
async def test_ollama_complete():
    """Test completion request."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = OllamaProvider(config)
    
    mock_response = {
        "response": "Generated response",
        "done": True
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
        result = await provider.complete("Test prompt")
        assert result == "Generated response"


@pytest.mark.asyncio
async def test_ollama_stream():
    """Test streaming completion."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = OllamaProvider(config)
    
    chunks = [
        {"response": "Hello ", "done": False},
        {"response": "world", "done": False},
        {"response": "!", "done": True}
    ]
    
    mock_response_obj = MagicMock()
    mock_response_obj.status = 200
    mock_response_obj.content.__aiter__.return_value = [
        json.dumps(chunk).encode() for chunk in chunks
    ]
    mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
    mock_response_obj.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response_obj)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = []
        async for chunk in provider.stream("Test prompt"):
            result.append(chunk)
        
        assert result == ["Hello ", "world", "!"]
