"""FastAPI web server for dashboard."""

from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request


def create_app() -> FastAPI:
    """Create FastAPI application.
    
    Returns:
        FastAPI application instance
    """
    app = FastAPI(title="Qwenex Dashboard")
    
    # Setup templates
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    
    @app.get("/")
    async def index(request: Request):
        """Serve dashboard HTML."""
        return templates.TemplateResponse("dashboard.html", {"request": request})
    
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
