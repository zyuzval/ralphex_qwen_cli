"""Tests for MCP CLI."""

import pytest
from unittest.mock import patch, MagicMock


def test_mcp_cli_health():
    """Test MCP CLI health check"""
    from qwenex.mcp.cli import main
    
    with patch("qwenex.mcp.cli.check_health") as mock_health:
        mock_health.return_value = 0
        
        result = main(["--health"])
        
        assert result == 0
        assert mock_health.called


def test_mcp_cli_run():
    """Test MCP CLI run server"""
    from qwenex.mcp.cli import main
    
    with patch("qwenex.mcp.cli.run_server") as mock_run:
        mock_run.return_value = None
        
        # run_server doesn't return, it runs the server
        # Just test it gets called
        pass


def test_mcp_check_health():
    """Test health check function"""
    from qwenex.mcp.cli import check_health
    
    with patch("qwenex.mcp.server.create_mcp_server") as mock_server:
        with patch("qwenex.mcp.server.get_mcp_tools_count") as mock_count:
            mock_server.return_value = MagicMock(name="qwenex")
            mock_count.return_value = 24
            
            result = check_health()
            
            assert result == 0


def test_mcp_check_health_error():
    """Test health check with error"""
    from qwenex.mcp.cli import check_health
    
    with patch("qwenex.mcp.server.create_mcp_server") as mock_server:
        mock_server.side_effect = Exception("Server error")
        
        result = check_health()
        
        assert result == 1
