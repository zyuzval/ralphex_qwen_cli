"""FastAPI web server for dashboard."""

from pathlib import Path
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .broadcast import BroadcastService

# Setup templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


# Background task reference
_demo_task = None


async def send_demo_progress():
    """Send demo progress updates for testing."""
    from .broadcast import BroadcastService
    broadcast = BroadcastService.get_instance()
    
    tasks = [
        "Запуск статического анализа...",
        "mypy: проверка типов...",
        "ruff: проверка стиля...",
        "bandit: проверка безопасности...",
        "Генерация отчёта...",
    ]
    
    for i, task in enumerate(tasks):
        progress = (i + 1) * 20
        await broadcast.send_progress(progress, task)
        await broadcast.send_log(task, "info")
        await asyncio.sleep(2)
    
    await broadcast.send_log("Code review завершён!", "success")


app = FastAPI(title="Qwenex Dashboard")


@app.get("/")
async def index(request: Request):
    """Serve dashboard HTML."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/demo/start")
async def start_demo():
    """Start demo progress for testing."""
    global _demo_task
    _demo_task = asyncio.create_task(send_demo_progress())
    return {"status": "started", "message": "Demo progress started"}


@app.get("/demo/status")
async def demo_status():
    """Get current demo status."""
    from .broadcast import BroadcastService
    broadcast = BroadcastService.get_instance()
    if broadcast.current_update:
        return {"status": "running", "update": broadcast.current_update}
    return {"status": "idle"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await websocket.accept()
    await websocket.send_json({"type": "connected"})
    
    # Keep connection alive
    try:
        while True:
            # Wait for messages (keep connection open)
            await websocket.receive_text()
    except Exception:
        # Connection closed
        pass
