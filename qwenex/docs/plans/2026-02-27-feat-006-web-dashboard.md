# FEAT-006: Web dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Real-time web dashboard для мониторинга выполнения планов и задач qwenex.

**Architecture:** FastAPI сервер + WebSocket для real-time обновлений. Простой HTML/JS frontend без фреймворков. Dashboard показывает статус текущей сессии, прогресс задач, логи выполнения.

**Tech Stack:** Python 3.11+ · FastAPI · WebSockets · Jinja2 · HTML/CSS/JS (vanilla)

---

### Task 1: FastAPI сервер

**Files:**
- Create: `src/qwenex/web/__init__.py`
- Create: `src/qwenex/web/server.py`
- Test: `src/tests/test_web_server.py`

**Step 1: Write the failing test**

```python
# src/tests/test_web_server.py
"""Tests for web server."""

import pytest
from fastapi.testclient import TestClient
from qwenex.web.server import create_app


def test_create_app():
    """Test app creation."""
    app = create_app()
    assert app is not None


def test_index_route():
    """Test index page."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    assert b"Qwenex Dashboard" in response.content


def test_health_route():
    """Test health endpoint."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_web_server.py -v --no-cov`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.web'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/web/__init__.py
"""Web dashboard package."""

from .server import create_app

__all__ = ["create_app"]
```

```python
# src/qwenex/web/server.py
"""FastAPI web server for dashboard."""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path


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
```

**Step 4: Add fastapi dependency**

```toml
# pyproject.toml - add to [project.dependencies]
"fastapi>=0.100.0",
"uvicorn>=0.23.0",
"websockets>=12.0",
```

**Step 5: Run test to verify it passes**

Run: `cd qwenex && pip install -e . && pytest src/tests/test_web_server.py -v --no-cov`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
cd qwenex
git add src/qwenex/web/ pyproject.toml src/tests/test_web_server.py
git commit -m "feat(FEAT-006-1): add FastAPI web server

- Basic FastAPI application
- Index route for dashboard
- /health endpoint
- WebSocket endpoint for real-time updates
- Tests: 3 passing"
```

---

### Task 2: Dashboard HTML template

**Files:**
- Create: `src/qwenex/web/templates/dashboard.html`
- Modify: `src/qwenex/web/server.py`

**Step 1: Create HTML template**

```html
<!-- src/qwenex/web/templates/dashboard.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qwenex Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #00d9ff; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .status.running { background: #0f3460; }
        .status.completed { background: #1a5c38; }
        .task { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .task-title { color: #00d9ff; font-weight: bold; }
        .progress-bar { width: 100%; height: 20px; background: #0f3460; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: #00d9ff; transition: width 0.3s; }
        #logs { background: #0f0f23; padding: 10px; height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; }
        .log-entry { margin: 5px 0; }
        .log-info { color: #888; }
        .log-success { color: #4ade80; }
        .log-error { color: #f87171; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Qwenex Dashboard</h1>
        
        <div id="status" class="status running">
            <strong>Status:</strong> <span id="status-text">Connecting...</span>
        </div>
        
        <div class="progress-bar">
            <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
        </div>
        <p>Progress: <span id="progress-text">0%</span></p>
        
        <h2>Current Task</h2>
        <div id="current-task" class="task">
            <div class="task-title">No active task</div>
        </div>
        
        <h2>Logs</h2>
        <div id="logs"></div>
    </div>
    
    <script>
        const ws = new WebSocket(`ws://${location.host}/ws`);
        const logs = document.getElementById('logs');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const statusText = document.getElementById('status-text');
        const currentTask = document.getElementById('current-task');
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'connected':
                    statusText.textContent = 'Connected';
                    break;
                case 'progress':
                    progressFill.style.width = data.percent + '%';
                    progressText.textContent = data.percent + '%';
                    break;
                case 'task_started':
                    currentTask.innerHTML = `<div class="task-title">${data.task}</div>`;
                    break;
                case 'log':
                    const entry = document.createElement('div');
                    entry.className = 'log-entry log-' + data.level;
                    entry.textContent = `[${data.timestamp}] ${data.message}`;
                    logs.appendChild(entry);
                    logs.scrollTop = logs.scrollHeight;
                    break;
            }
        };
        
        ws.onclose = () => {
            statusText.textContent = 'Disconnected';
        };
    </script>
</body>
</html>
```

**Step 2: Update server.py to serve template**

```python
# src/qwenex/web/server.py - update
from fastapi.templating import Jinja2Templates

# In create_app():
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@app.get("/")
async def index():
    """Serve dashboard HTML."""
    return templates.TemplateResponse("dashboard.html", {"request": {}})
```

**Step 3: Run manual test**

Run: `cd qwenex && uvicorn qwenex.web.server:create_app --reload`
Expected: Server starts, http://localhost:8000 shows dashboard

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/web/templates/ src/qwenex/web/server.py
git commit -m "feat(FEAT-006-2): add dashboard HTML template

- Modern dark theme UI
- Real-time progress bar
- Current task display
- Live logs console
- WebSocket client for updates"
```

---

### Task 3: Progress broadcast service

**Files:**
- Create: `src/qwenex/web/broadcast.py`
- Test: `src/tests/test_web_broadcast.py`

**Step 1: Write the failing test**

```python
# src/tests/test_web_broadcast.py
"""Tests for broadcast service."""

import pytest
from qwenex.web.broadcast import BroadcastService, ProgressUpdate


def test_broadcast_service_singleton():
    """Test singleton pattern."""
    service1 = BroadcastService.get_instance()
    service2 = BroadcastService.get_instance()
    assert service1 is service2


def test_progress_update():
    """Test ProgressUpdate dataclass."""
    update = ProgressUpdate(
        percent=50,
        current_task="Task 1",
        message="In progress"
    )
    assert update.percent == 50
    assert update.current_task == "Task 1"
    assert update.to_dict() == {
        "percent": 50,
        "current_task": "Task 1",
        "message": "In progress"
    }
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_web_broadcast.py -v --no-cov`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/qwenex/web/broadcast.py
"""Broadcast service for WebSocket updates."""

from dataclasses import dataclass, asdict
from typing import List, Optional
from fastapi import WebSocket


@dataclass
class ProgressUpdate:
    """Progress update data."""
    percent: float
    current_task: Optional[str] = None
    message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class BroadcastService:
    """Service for broadcasting updates to WebSocket clients."""
    
    _instance: Optional['BroadcastService'] = None
    
    def __init__(self):
        """Initialize broadcast service."""
        self.clients: List[WebSocket] = []
        self.current_update: Optional[ProgressUpdate] = None
    
    @classmethod
    def get_instance(cls) -> 'BroadcastService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def connect(self, websocket: WebSocket) -> None:
        """Add client to broadcast list."""
        self.clients.append(websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove client from broadcast list."""
        if websocket in self.clients:
            self.clients.remove(websocket)
    
    async def broadcast(self, update: ProgressUpdate) -> None:
        """Broadcast update to all connected clients."""
        self.current_update = update
        
        disconnected = []
        for client in self.clients:
            try:
                await client.send_json(update.to_dict())
            except Exception:
                disconnected.append(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            self.disconnect(client)
    
    async def send_progress(self, percent: float, task: Optional[str] = None) -> None:
        """Send progress update."""
        update = ProgressUpdate(percent=percent, current_task=task)
        await self.broadcast(update)
    
    async def send_log(self, message: str, level: str = "info") -> None:
        """Send log entry."""
        from datetime import datetime
        update = {
            "type": "log",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "level": level
        }
        
        disconnected = []
        for client in self.clients:
            try:
                await client.send_json(update)
            except Exception:
                disconnected.append(client)
        
        for client in disconnected:
            self.disconnect(client)
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_web_broadcast.py -v --no-cov`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/web/broadcast.py src/tests/test_web_broadcast.py
git commit -m "feat(FEAT-006-3): add broadcast service

- BroadcastService singleton for WebSocket management
- ProgressUpdate dataclass
- broadcast() to all connected clients
- send_progress() and send_log() helpers
- Tests: 2 passing"
```

---

### Task 4: Интеграция с orchestrator

**Files:**
- Modify: `src/qwenex/orchestrator.py`
- Modify: `src/qwenex/progress.py`

**Step 1: Add web progress callback**

```python
# src/qwenex/progress.py - add callback support
from typing import Optional, Callable, Awaitable


class ProgressTracker:
    """Track plan execution progress."""
    
    def __init__(
        self,
        plan_file: str,
        callback: Optional[Callable[[str, dict], Awaitable[None]]] = None
    ):
        """Initialize progress tracker.
        
        Args:
            plan_file: Path to plan file
            callback: Optional async callback for progress updates
        """
        self.plan_file = plan_file
        self.callback = callback
    
    async def _notify(self, event_type: str, data: dict) -> None:
        """Send notification via callback."""
        if self.callback:
            await self.callback(event_type, data)
    
    async def task_started(self, task_num: str, task_title: str) -> None:
        """Log task start."""
        await self._notify("task_started", {
            "task": f"{task_num}: {task_title}"
        })
    
    async def log(self, message: str) -> None:
        """Log message."""
        await self._notify("log", {"message": message, "level": "info"})
```

**Step 2: Update orchestrator to use web callback**

```python
# src/qwenex/orchestrator.py - add web parameter
from .web.broadcast import BroadcastService


class Orchestrator:
    def __init__(
        self,
        plan: Plan,
        provider: Optional[LLMProvider] = None,
        provider_config: Optional[ProviderConfig] = None,
        max_iterations: int = 3,
        timeout_min: int = 10,
        auto_mode: bool = False,
        enable_web: bool = False,
    ):
        # ... existing code ...
        
        self.enable_web = enable_web
        if enable_web:
            self.broadcast = BroadcastService.get_instance()
        else:
            self.broadcast = None
    
    async def run(self) -> OrchestratorResult:
        """Run plan execution."""
        # Create progress tracker with callback
        async def web_callback(event_type: str, data: dict):
            if self.broadcast:
                if event_type == "task_started":
                    await self.broadcast.send_progress(
                        0, 
                        data.get("task", "")
                    )
                elif event_type == "log":
                    await self.broadcast.send_log(
                        data.get("message", ""),
                        data.get("level", "info")
                    )
        
        self.progress = ProgressTracker(
            plan_file=self.plan.file_path,
            callback=web_callback
        )
        
        # ... rest of run method ...
```

**Step 3: Run tests**

Run: `cd qwenex && pytest src/tests/test_orchestrator.py -v --no-cov`
Expected: PASS (update existing tests if needed)

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/orchestrator.py src/qwenex/progress.py
git commit -m "feat(FEAT-006-4): integrate web dashboard with orchestrator

- ProgressTracker callback support
- Orchestrator enable_web flag
- BroadcastService integration
- Real-time task and log updates"
```

---

### Task 5: CLI команда для dashboard

**Files:**
- Create: `src/qwenex/web/cli.py`
- Modify: `pyproject.toml`

**Step 1: Create web CLI**

```python
# src/qwenex/web/cli.py
"""CLI for web dashboard."""

import argparse
import uvicorn
from pathlib import Path


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
```

**Step 2: Register entry point**

```toml
# pyproject.toml - add to [project.scripts]
qwenex-web = "qwenex.web.cli:web_entry_point"
```

**Step 3: Test CLI**

Run: `cd qwenex && pip install -e . && qwenex-web --help`
Expected: Help message displayed

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/web/cli.py pyproject.toml
git commit -m "feat(FEAT-006-5): add qwenex-web CLI command

- qwenex-web entry point
- --host and --port options
- --reload for development
- uvicorn server integration"
```

---

### Task 6: Документация

**Files:**
- Create: `docs/DASHBOARD.md`
- Modify: `README.md`

**Step 1: Create DASHBOARD.md**

```markdown
# Web Dashboard

Qwenex включает web dashboard для real-time мониторинга выполнения планов.

## Быстрый старт

```bash
# Запустить dashboard сервер
qwenex-web

# На другом порту
qwenex-web --port 9000

# С авто-перезагрузкой (dev режим)
qwenex-web --reload
```

## Интеграция с qwenex

```bash
# Запустить выполнение с web dashboard
qwenex plan.md --web
```

## WebSocket API

Dashboard использует WebSocket для real-time обновлений.

**Подключение:**
```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
```

**События:**
```javascript
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case "progress":
            console.log(`Progress: ${data.percent}%`);
            break;
        case "task_started":
            console.log(`Task: ${data.task}`);
            break;
        case "log":
            console.log(`[${data.level}] ${data.message}`);
            break;
    }
};
```

## REST API

**GET /health**
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

**GET /**
- Dashboard HTML страница

## Архитектура

```
┌─────────────┐     WebSocket      ┌──────────────┐
│   Browser   │ ◄────────────────► │  Broadcast   │
│             │                    │   Service    │
└─────────────┘                    └──────┬───────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │ Orchestrator │
                                   │  Progress    │
                                   └──────────────┘
```
```

**Step 2: Update README.md**

```markdown
# Add to features section
- **Web dashboard** — Real-time мониторинг через WebSocket
```

```markdown
# Add to documentation table
| [docs/DASHBOARD.md](./docs/DASHBOARD.md) | Web dashboard руководство |
```

**Step 3: Commit**

```bash
cd qwenex
git add docs/DASHBOARD.md README.md
git commit -m "docs(FEAT-006-6): add web dashboard documentation

- DASHBOARD.md with usage guide
- WebSocket API documentation
- Update README with new feature"
```

---

## Завершение плана

**Проверка покрытия тестов:**

```bash
cd qwenex && pytest --cov=src/qwenex --cov-report=term-missing
```

Expected: 80%+ покрытие

**Запуск всех тестов:**

```bash
cd qwenex && pytest -v
```

Expected: Все тесты проходят

---

## Итоговый список коммитов

1. `feat(FEAT-006-1): add FastAPI web server`
2. `feat(FEAT-006-2): add dashboard HTML template`
3. `feat(FEAT-006-3): add broadcast service`
4. `feat(FEAT-006-4): integrate web dashboard with orchestrator`
5. `feat(FEAT-006-5): add qwenex-web CLI command`
6. `docs(FEAT-006-6): add web dashboard documentation`

**Всего:** 6 коммитов, ~7 тестов

---

План готов и сохранён в `docs/plans/2026-02-27-feat-006-web-dashboard.md`.

**Два варианта выполнения:**

**1. Subagent-Driven (эта сессия)** — Запускаю свежего субагента на каждую задачу, code review между задачами, быстрая итерация

**2. Параллельная сессия (отдельная)** — Открыть новую сессию с `superpowers:executing-plans`, пакетное выполнение с чекпоинтами

**Какой подход выбираешь?**
