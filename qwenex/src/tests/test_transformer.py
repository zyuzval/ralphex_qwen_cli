"""Tests for plan transformer."""

import pytest
from unittest.mock import AsyncMock, patch
from qwenex.transformer import PlanTransformer
from qwenex.models.base import ProviderConfig
from qwenex.models.qwen_cloud import QwenCloudProvider


@pytest.mark.asyncio
async def test_transform_simple_plan():
    """Test transforming a simple plan."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    transformer = PlanTransformer(provider=provider)
    
    simple_plan = """# Plan: Add login

## Tasks
1. Create login form
2. Add API endpoint
3. Write tests
"""
    
    mock_response = '''{
        "title": "Login System",
        "goal": "Implement user authentication",
        "scenarios": ["User logs in with credentials"],
        "requirements": [{"name": "Login Form", "description": "Login form with username and password", "why": "Required for authentication"}],
        "out_of_scope": ["Password reset"],
        "tests": [{"name": "test_login_success", "description": "Valid credentials log in user"}]
    }'''
    
    with patch.object(provider, 'complete', new=AsyncMock(return_value=mock_response)):
        result = await transformer.transform(simple_plan, "001")
        assert "FEAT-001" in result
        assert "Login System" in result


@pytest.mark.asyncio
async def test_transform_preserves_structure():
    """Test that transformation preserves FEAT structure."""
    config = ProviderConfig(name="qwen_cloud", model="qwen-max", api_key="key")
    provider = QwenCloudProvider(config)
    transformer = PlanTransformer(provider=provider)
    
    simple_plan = "# Plan: Test\n\n## Tasks\n1. Do something"
    mock_response = '''{
        "title": "Test",
        "goal": "Test goal",
        "scenarios": [],
        "requirements": [],
        "out_of_scope": [],
        "tests": []
    }'''
    
    with patch.object(provider, 'complete', new=AsyncMock(return_value=mock_response)):
        result = await transformer.transform(simple_plan, "001")
        assert "## 1. Цель" in result
        assert "Test goal" in result
