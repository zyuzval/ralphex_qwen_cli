"""Tests for Config MCP tools."""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_config_get():
    """Test getting config"""
    from qwenex.mcp.tools.config import config_get
    
    with patch("qwenex.mcp.tools.config.get_config") as mock_get:
        mock_get.return_value = {"auto_mode": False, "timeout": 10}
        
        result = await config_get()
        
        assert isinstance(result, dict)
        assert "auto_mode" in result or "timeout" in result


@pytest.mark.asyncio
async def test_config_get_error():
    """Test getting config with error"""
    from qwenex.mcp.tools.config import config_get
    
    with patch("qwenex.mcp.tools.config.get_config") as mock_get:
        mock_get.side_effect = Exception("Config not found")
        
        result = await config_get()
        
        assert "error" in result


@pytest.mark.asyncio
async def test_config_set():
    """Test setting config value"""
    from qwenex.mcp.tools.config import config_set
    
    with patch("qwenex.mcp.tools.config.set_config_value") as mock_set:
        mock_set.return_value = True
        
        result = await config_set("auto_mode", True)
        
        assert "Updated" in result or "success" in result.lower()


@pytest.mark.asyncio
async def test_config_set_error():
    """Test setting config with error"""
    from qwenex.mcp.tools.config import config_set
    
    with patch("qwenex.mcp.tools.config.set_config_value") as mock_set:
        mock_set.side_effect = Exception("Invalid key")
        
        result = await config_set("invalid_key", "value")
        
        assert "Error" in result
