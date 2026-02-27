"""Tests for base LLM provider models and protocol."""

import pytest
from qwenex.models.base import LLMProvider, Message, ProviderConfig


def test_protocol_definition():
    """Test that LLMProvider protocol is properly defined."""
    # Protocol should be definable
    assert hasattr(LLMProvider, 'complete')
    assert hasattr(LLMProvider, 'check_health')
    assert hasattr(LLMProvider, 'get_config')


@pytest.mark.asyncio
async def test_message_structure():
    """Test Message dataclass."""
    msg = Message(role="user", content="Test prompt")
    assert msg.role == "user"
    assert msg.content == "Test prompt"
    
    msg_with_system = Message(
        role="user",
        content="Test",
        system_prompt="You are helpful"
    )
    assert msg_with_system.system_prompt == "You are helpful"


def test_provider_config():
    """Test ProviderConfig dataclass."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key",
        timeout_sec=600
    )
    assert config.name == "qwen_cloud"
    assert config.api_key == "test-key"
    assert config.model == "qwen-max"
    assert config.timeout_sec == 600
    assert config.base_url is None  # Optional field
