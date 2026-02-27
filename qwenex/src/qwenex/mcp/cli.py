"""CLI entry point for MCP server."""

import argparse
import sys
import asyncio


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="qwenex-mcp",
        description="MCP Server for Qwenex"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level"
    )
    
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check MCP server health"
    )
    
    return parser.parse_args(args)


def check_health():
    """Check MCP server health."""
    from .server import create_mcp_server, get_mcp_tools_count
    
    try:
        server = create_mcp_server()
        tools_count = get_mcp_tools_count()
        
        print(f"MCP Server: {server.name}")
        print(f"Tools registered: {tools_count}")
        print("Health: OK")
        return 0
    except Exception as e:
        print(f"Health: FAILED - {e}")
        return 1


def run_server():
    """Run MCP server."""
    import logging
    
    from qwenex.mcp.server import create_mcp_server
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and run server
    server = create_mcp_server()
    
    print(f"Starting MCP server: {server.name}")
    print("Transport: stdin/stdout (JSON-RPC 2.0)")
    print("Press Ctrl+C to stop")
    
    # Run server (FastMCP handles the event loop)
    server.run()


def main(args=None):
    """Main entry point."""
    parsed_args = parse_args(args)
    
    if parsed_args.health:
        return check_health()
    else:
        return run_server()


if __name__ == "__main__":
    sys.exit(main())
