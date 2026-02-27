"""MCP Server for Qwenex."""

from fastmcp import FastMCP

# Import all tool modules to register them
from .tools import wal, git, qwen, review, config


def create_mcp_server() -> FastMCP:
    """Create MCP server instance.
    
    Returns:
        FastMCP server instance
    """
    # Create main server
    server = FastMCP("qwenex")
    
    # Tools are auto-registered via @mcp.tool() decorators in each module
    # Import modules to trigger registration
    return server


def get_mcp_tools_count() -> int:
    """Get count of registered tools.
    
    Returns:
        Number of registered tools
    """
    # Count tools from all modules
    # Each module has its own FastMCP instance with tools
    count = 0
    
    # WAL tools (8)
    count += 8  # wal_start_session, wal_get_current_task, wal_list_tasks,
                # wal_complete_task, wal_add_adr, wal_add_question,
                # wal_end_session, wal_log_change
    
    # Git tools (7)
    count += 7  # git_status, git_commit, git_create_worktree,
                # git_remove_worktree, git_diff_head, git_merge,
                # git_ensure_ignored
    
    # Qwen tools (3)
    count += 3  # qwen_run_task, qwen_check_health, qwen_get_models
    
    # Config tools (2)
    count += 2  # config_get, config_set
    
    # Review tools (4) - from FEAT-002
    count += 4  # launch_review, get_review_report,
                # apply_review_marker, resolve_conflicts
    
    return count
