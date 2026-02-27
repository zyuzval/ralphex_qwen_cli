"""MCP Server for Qwenex."""

from fastmcp import FastMCP


def create_mcp_server() -> FastMCP:
    """Create MCP server instance.
    
    Returns:
        FastMCP server instance
    """
    return FastMCP("qwenex")


def get_mcp_tools_count() -> int:
    """Get count of registered tools.
    
    Returns:
        Number of registered tools
    """
    # Placeholder - will be updated as tools are added
    return 0
