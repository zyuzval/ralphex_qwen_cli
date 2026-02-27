"""CLI for web dashboard."""

import argparse
import uvicorn


def web_entry_point():
    """Run web dashboard server."""
    parser = argparse.ArgumentParser(
        prog="qwenex-web",
        description="Qwenex web dashboard server"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Qwenex Dashboard at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "qwenex.web.server:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True
    )


if __name__ == "__main__":
    web_entry_point()
