"""Tests for provider factory."""

import pytest
import os
from qwenex.models.factory import ProviderFactory, ProviderType
from qwenex.models.qwen_cloud import QwenCloudProvider
from qwenex.models.ollama import OllamaProvider
from qwenex.models.openai import OpenAIProvider
from qwenex.models.base import ProviderConfig


def test_provider_type_enum():
    """Test ProviderType enum values."""
    assert ProviderType.QWEN_CLOUD.value == "qwen_cloud"
    assert ProviderType.OLLAMA.value == "ollama"
    assert ProviderType.OPENAI.value == "openai"


def test_factory_create_qwen():
    """Test factory creates QwenCloudProvider."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = ProviderFactory.create(ProviderType.QWEN_CLOUD, config)
    assert isinstance(provider, QwenCloudProvider)


def test_factory_create_ollama():
    """Test factory creates OllamaProvider."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = ProviderFactory.create(ProviderType.OLLAMA, config)
    assert isinstance(provider, OllamaProvider)


def test_factory_create_openai():
    """Test factory creates OpenAIProvider."""
    config = ProviderConfig(
        name="openai",
        model="gpt-4o",
        api_key="sk-test123"
    )
    provider = ProviderFactory.create(ProviderType.OPENAI, config)
    assert isinstance(provider, OpenAIProvider)


def test_factory_create_invalid():
    """Test factory raises on invalid provider type."""
    config = ProviderConfig(name="invalid", model="test")
    with pytest.raises(ValueError):
        ProviderFactory.create("invalid", config)


def test_factory_create_from_string():
    """Test factory creates provider from string."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b"
    )
    provider = ProviderFactory.create("ollama", config)
    assert isinstance(provider, OllamaProvider)
