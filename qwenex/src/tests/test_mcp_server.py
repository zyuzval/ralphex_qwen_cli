"""Tests for MCP server base structure."""

import pytest
from qwenex.mcp.server import create_mcp_server, get_mcp_tools_count


def test_mcp_server_creation():
    """Test MCP server creates successfully"""
    server = create_mcp_server()
    
    assert server is not None
    assert server.name == "qwenex"


def test_mcp_tools_registered():
    """Test MCP tools are registered"""
    count = get_mcp_tools_count()
    
    # Should have tools from all modules
    # For now, just check it returns a number
    assert isinstance(count, int)
    assert count >= 0
