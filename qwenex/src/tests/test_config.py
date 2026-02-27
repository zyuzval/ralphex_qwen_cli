"""Tests for configuration management."""

import pytest
import os
import json
from pathlib import Path
from qwenex.config import QwenexConfig, ProviderSettings, load_config, save_config


def test_provider_settings():
    """Test ProviderSettings dataclass."""
    settings = ProviderSettings(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key",
        base_url="https://api.example.com",
        timeout_sec=300
    )
    assert settings.name == "qwen_cloud"
    assert settings.api_key == "test-key"


def test_qwenex_config():
    """Test QwenexConfig dataclass."""
    config = QwenexConfig(
        default_provider="qwen_cloud",
        providers={
            "qwen_cloud": ProviderSettings(
                name="qwen_cloud",
                model="qwen-max",
                api_key="test-key"
            )
        }
    )
    assert config.default_provider == "qwen_cloud"
    assert "qwen_cloud" in config.providers


def test_load_config_from_file(tmp_path):
    """Test loading config from file."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "default_provider": "ollama",
        "providers": {
            "ollama": {
                "name": "ollama",
                "model": "llama3.1:8b",
                "base_url": "http://localhost:11434"
            }
        }
    }))
    
    config = load_config(config_file)
    assert config.default_provider == "ollama"
    assert "ollama" in config.providers


def test_save_config(tmp_path):
    """Test saving config to file."""
    config_file = tmp_path / "config.json"
    
    config = QwenexConfig(
        default_provider="openai",
        providers={
            "openai": ProviderSettings(
                name="openai",
                model="gpt-4o",
                api_key="sk-test"
            )
        }
    )
    
    save_config(config, config_file)
    assert config_file.exists()
    
    loaded = load_config(config_file)
    assert loaded.default_provider == "openai"


def test_load_config_from_env(monkeypatch):
    """Test loading config from environment."""
    monkeypatch.setenv("QWENEX_DEFAULT_PROVIDER", "ollama")
    monkeypatch.setenv("QWENEX_MODEL", "llama3.1:8b")
    
    config = load_config()
    assert config.default_provider == "ollama"
