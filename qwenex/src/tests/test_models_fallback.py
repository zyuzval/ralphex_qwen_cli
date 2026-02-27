"""Tests for fallback provider."""

import pytest
from unittest.mock import AsyncMock, patch
from qwenex.models.fallback import FallbackProvider
from qwenex.models.base import ProviderConfig


@pytest.mark.asyncio
async def test_fallback_primary_available():
    """Test fallback uses primary when available."""
    primary_config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    fallback_config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    
    fallback = FallbackProvider(primary_config, fallback_config)
    
    # Mock primary health check to succeed
    with patch.object(fallback.primary, 'check_health', new=AsyncMock(return_value=True)):
        with patch.object(fallback.primary, 'complete', new=AsyncMock(return_value="Primary")):
            result = await fallback.complete("Test")
            assert result == "Primary"


@pytest.mark.asyncio
async def test_fallback_primary_unavailable():
    """Test fallback uses secondary when primary fails."""
    primary_config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    fallback_config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    
    fallback = FallbackProvider(primary_config, fallback_config)
    
    # Mock primary health check to fail
    with patch.object(fallback.primary, 'check_health', new=AsyncMock(return_value=False)):
        with patch.object(fallback.fallback, 'complete', new=AsyncMock(return_value="Fallback")):
            result = await fallback.complete("Test")
            assert result == "Fallback"


@pytest.mark.asyncio
async def test_fallback_health_check():
    """Test fallback health check."""
    primary_config = ProviderConfig(name="ollama", model="llama3.1:8b")
    fallback_config = ProviderConfig(name="qwen_cloud", model="qwen-max", api_key="key")
    
    fallback = FallbackProvider(primary_config, fallback_config)
    
    with patch.object(fallback.primary, 'check_health', new=AsyncMock(return_value=False)):
        with patch.object(fallback.fallback, 'check_health', new=AsyncMock(return_value=True)):
            result = await fallback.check_health()
            assert result is True
