"""Tests for Qwen MCP tools."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_qwen_run_task():
    """Test running Qwen task"""
    from qwenex.mcp.tools.qwen import qwen_run_task
    
    with patch("qwenex.mcp.tools.qwen.QwenExecutor") as MockExecutor:
        mock_executor = MagicMock()
        
        # Create async generator mock
        async def mock_run_gen(prompt):
            yield {"type": "result", "result": "Task output"}
        
        mock_executor.run_task = mock_run_gen
        MockExecutor.return_value = mock_executor
        
        result = await qwen_run_task("Test prompt")
        
        assert "Task output" in result


@pytest.mark.asyncio
async def test_qwen_run_task_with_model():
    """Test running Qwen task with specific model"""
    from qwenex.mcp.tools.qwen import qwen_run_task
    
    with patch("qwenex.mcp.tools.qwen.QwenExecutor") as MockExecutor:
        mock_executor = MagicMock()
        
        # Create async generator mock
        async def mock_run_gen(prompt):
            yield {"type": "result", "result": "Task output"}
        
        mock_executor.run_task = mock_run_gen
        MockExecutor.return_value = mock_executor
        
        result = await qwen_run_task("Test prompt", model="qwen-plus")
        
        assert "Task output" in result


@pytest.mark.asyncio
async def test_qwen_check_health():
    """Test checking Qwen health"""
    from qwenex.mcp.tools.qwen import qwen_check_health
    
    with patch("qwenex.mcp.tools.qwen.QwenExecutor") as MockExecutor:
        mock_executor = MagicMock()
        
        async def mock_check():
            return True
        
        mock_executor.check_health = mock_check
        MockExecutor.return_value = mock_executor
        
        result = await qwen_check_health()
        
        assert result["healthy"] is True


@pytest.mark.asyncio
async def test_qwen_check_health_unhealthy():
    """Test checking Qwen health when unhealthy"""
    from qwenex.mcp.tools.qwen import qwen_check_health
    
    with patch("qwenex.mcp.tools.qwen.QwenExecutor") as MockExecutor:
        mock_executor = MagicMock()
        
        async def mock_check():
            raise Exception("Connection error")
        
        mock_executor.check_health = mock_check
        MockExecutor.return_value = mock_executor
        
        result = await qwen_check_health()
        
        assert result["healthy"] is False
        assert "error" in result


@pytest.mark.asyncio
async def test_qwen_get_models():
    """Test getting available models"""
    from qwenex.mcp.tools.qwen import qwen_get_models
    
    result = await qwen_get_models()
    
    assert isinstance(result, list)
    assert len(result) >= 2
    assert any(m["name"] == "qwen-max" for m in result)
