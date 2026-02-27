"""FastAPI web server for dashboard."""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse


def create_app() -> FastAPI:
    """Create FastAPI application.
    
    Returns:
        FastAPI application instance
    """
    app = FastAPI(title="Qwenex Dashboard")
    
    @app.get("/")
    async def index():
        """Serve dashboard HTML."""
        return HTMLResponse("<html><body><h1>Qwenex Dashboard</h1></body></html>")
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok"}
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket for real-time updates."""
        await websocket.accept()
        await websocket.send_json({"type": "connected"})
    
    return app
