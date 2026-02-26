# MCP-сервер для tg-stats: Полный гайд

**Дата:** 2026-02-25  
**Стек:** Python + FastAPI + MCP SDK  
**Инструменты:** VS Code (Cline, Roo Code, Continue), Qwen Code CLI

---

## Оглавление

1. [Концепция и архитектура](#1-концепция-и-архитектура)
2. [Что вынести в MCP, что оставить в Skills](#2-что-вынести-в-mcp-что-оставить-в-skills)
3. [Структура файлов](#3-структура-файлов)
4. [Установка и настройка](#4-установка-и-настройка)
5. [Реализация сервера](#5-реализация-сервера)
6. [Подключение к инструментам](#6-подключение-к-инструментам)
7. [Отладка и тестирование](#7-отладка-и-тестирование)
8. [Шаблон нового инструмента](#8-шаблон-нового-инструмента)
9. [Типичные ошибки](#9-типичные-ошибки)
10. [Чеклист при добавлении инструмента](#10-чеклист-при-добавлении-инструмента)

---

## 1. Концепция и архитектура

### Как работает MCP

```
┌─────────────────────────────────────────────────────┐
│   VS Code (Cline / Roo Code / Continue)             │
│   ─ читает Skills (AGENTS.md, BOOT.md) как контекст │
│   ─ вызывает MCP как инструменты                    │
└────────────────────┬────────────────────────────────┘
                     │  JSON-RPC 2.0
                     │  (stdin/stdout)
          ┌──────────▼──────────┐
          │   mcp_server.py     │
          │   ─ list_tools()    │
          │   ─ call_tool()     │
          └──────────┬──────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   WAL.md      sessions/     git / pytest
  (состояние)  (сессии)      (команды)
```

MCP-сервер запускается агентом как дочерний процесс. Общение — через stdin/stdout (режим stdio). Каждый инструмент — это функция с чётким input/output.

### Skills vs MCP в этом проекте

| Файл | Тип | Почему |
|------|-----|--------|
| AGENTS.md | **Skill** | Правила поведения агента, не данные |
| BOOT.md | **Skill** | Архитектура, запреты, контекст |
| TEMPLATE.md | **Skill** | Шаблон сессии — знание, не функция |
| README-DEV.md | **Skill** | Best practices, troubleshooting |
| WAL.md (состояние) | **MCP** | Меняется, нужен структурированный доступ |
| scripts/*.py | **MCP** | Детерминированные операции |
| git операции | **MCP** | Вызов с параметрами → результат |
| pytest | **MCP** | Запуск → структурированный вывод |

---

## 2. Что вынести в MCP, что оставить в Skills

### Правило выбора

**MCP** — если выполняется хотя бы одно:
- Меняет состояние (файл, БД, git)
- Возвращает актуальные данные (не то, что было на момент написания Skill)
- Требует параметров от агента
- Может упасть с ошибкой, которую нужно обработать

**Skill** — если:
- Это правило или политика ("всегда делай X перед Y")
- Это архитектурное знание ("используй SQLite, не PostgreSQL")
- Не меняется между запросами
- Агент должен это *понимать*, а не *вызывать*

### Конкретные инструменты для tg-stats

```
WAL-инструменты:
  get_current_task()              → текущая задача + статус
  list_tasks(status?)             → список задач с фильтром
  update_task_status(id, status)  → обновить статус задачи
  add_completed_task(task, info)  → добавить в историю

Сессии:
  list_sessions()                 → все сессии + их статус
  get_session(session_id)         → детали конкретной сессии
  create_session(name, priority)  → создать новую сессию
  update_session_status(id, s)    → обновить статус сессии

Разработка:
  run_tests(module?)              → pytest → {passed, failed, errors[]}
  run_build()                     → npm build → {success, errors[]}
  git_status()                    → изменённые файлы
  git_commit(message, files[])    → коммит → hash

Проект:
  get_project_info()              → стек, структура, текущий статус
```

---

## 3. Структура файлов

```
tg-stats/
├── mcp/
│   ├── server.py           ← точка входа
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── wal.py          ← WAL-инструменты
│   │   ├── sessions.py     ← управление сессиями
│   │   ├── dev.py          ← тесты, сборка, git
│   │   └── project.py      ← информация о проекте
│   ├── models.py           ← pydantic-модели для WAL/сессий
│   └── config.py           ← пути и настройки
├── docs/
│   ├── sessions/
│   └── reviews/
├── AGENTS.md               ← Skill (остаётся как есть)
├── BOOT.md                 ← Skill (остаётся как есть)
├── WAL.md                  ← читается через MCP (не напрямую)
└── ...
```

---

## 4. Установка и настройка

### Зависимости

```bash
# В виртуальное окружение проекта
pip install mcp pydantic

# Проверить что установилось
python -c "import mcp; print(mcp.__version__)"
```

### config.py

```python
# mcp/config.py
from pathlib import Path

# Корень проекта — относительно этого файла
PROJECT_ROOT = Path(__file__).parent.parent

WAL_PATH = PROJECT_ROOT / "WAL.md"
SESSIONS_DIR = PROJECT_ROOT / "docs" / "sessions"
REVIEWS_DIR = PROJECT_ROOT / "docs" / "reviews"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
WEB_DIR = PROJECT_ROOT / "web"
TESTS_DIR = PROJECT_ROOT / "tests"
SRC_DIR = PROJECT_ROOT / "src"
```

---

## 5. Реализация сервера

### server.py — точка входа

```python
# mcp/server.py
import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from .tools.wal import WALTools
from .tools.sessions import SessionTools
from .tools.dev import DevTools
from .tools.project import ProjectTools

app = Server("tg-stats")

# Инициализируем группы инструментов
wal = WALTools()
sessions = SessionTools()
dev = DevTools()
project = ProjectTools()

# Все инструменты в одном списке
ALL_TOOLS = [
    *wal.get_tool_definitions(),
    *sessions.get_tool_definitions(),
    *dev.get_tool_definitions(),
    *project.get_tool_definitions(),
]

# Маршрутизатор вызовов
HANDLERS = {
    **wal.get_handlers(),
    **sessions.get_handlers(),
    **dev.get_handlers(),
    **project.get_handlers(),
}


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return ALL_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name not in HANDLERS:
        raise ValueError(f"Unknown tool: {name}")
    
    try:
        result = await HANDLERS[name](arguments)
        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        # Ошибки возвращаем как текст, не роняем сервер
        error_msg = f"ERROR in {name}: {type(e).__name__}: {e}"
        print(error_msg, file=sys.stderr)  # лог в stderr
        return [types.TextContent(type="text", text=error_msg)]


async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

### tools/wal.py — WAL инструменты

```python
# mcp/tools/wal.py
import json
import re
from datetime import datetime
from pathlib import Path
from mcp import types
from ..config import WAL_PATH


class WALTools:
    """Инструменты для работы с WAL.md"""

    def get_tool_definitions(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="get_current_task",
                description=(
                    "Получить текущую задачу из WAL. "
                    "Вызывай в начале каждой сессии вместо чтения WAL.md напрямую."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            types.Tool(
                name="list_tasks",
                description="Список задач из WAL с опциональным фильтром по статусу.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "done", "all"],
                            "description": "Фильтр по статусу. По умолчанию: all"
                        }
                    }
                }
            ),
            types.Tool(
                name="update_task_status",
                description="Обновить статус задачи в WAL. Используй после завершения работы.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID или короткое название задачи"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["done", "in_progress", "blocked", "pending"]
                        },
                        "notes": {
                            "type": "string",
                            "description": "Опциональные заметки о выполнении"
                        }
                    },
                    "required": ["task_id", "status"]
                }
            ),
        ]

    def get_handlers(self) -> dict:
        return {
            "get_current_task": self._get_current_task,
            "list_tasks": self._list_tasks,
            "update_task_status": self._update_task_status,
        }

    async def _get_current_task(self, args: dict) -> str:
        content = WAL_PATH.read_text(encoding="utf-8")
        
        # Ищем секцию "Текущая задача"
        match = re.search(
            r"## Текущая задача\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL
        )
        if not match:
            return json.dumps({"error": "Current task section not found"}, ensure_ascii=False)
        
        section = match.group(1).strip()
        
        # Парсим заголовок и статус
        task_match = re.search(r"### (.+)", section)
        status_match = re.search(r"\*\*Статус:\*\* (.+)", section)
        
        return json.dumps({
            "task": task_match.group(1) if task_match else "Unknown",
            "status": status_match.group(1) if status_match else "Unknown",
            "raw": section[:500]  # первые 500 символов для контекста
        }, ensure_ascii=False, indent=2)

    async def _list_tasks(self, args: dict) -> str:
        status_filter = args.get("status", "all")
        content = WAL_PATH.read_text(encoding="utf-8")
        
        tasks = []
        # Ищем чекбоксы: - [x] или - [ ]
        for line in content.split("\n"):
            if line.strip().startswith("- ["):
                done = line.strip().startswith("- [x]")
                task_text = re.sub(r"^- \[.\] ", "", line.strip())
                
                if status_filter == "done" and not done:
                    continue
                if status_filter == "pending" and done:
                    continue
                
                tasks.append({
                    "status": "done" if done else "pending",
                    "task": task_text
                })
        
        return json.dumps({
            "total": len(tasks),
            "filter": status_filter,
            "tasks": tasks
        }, ensure_ascii=False, indent=2)

    async def _update_task_status(self, args: dict) -> str:
        task_id = args["task_id"]
        status = args["status"]
        notes = args.get("notes", "")
        
        content = WAL_PATH.read_text(encoding="utf-8")
        
        # Ищем задачу по подстроке
        if task_id not in content:
            return json.dumps({"error": f"Task '{task_id}' not found in WAL"}, ensure_ascii=False)
        
        # Простое обновление: меняем [ ] на [x] или наоборот
        if status == "done":
            updated = content.replace(f"- [ ] {task_id}", f"- [x] {task_id}", 1)
        elif status in ("pending", "in_progress", "blocked"):
            updated = content.replace(f"- [x] {task_id}", f"- [ ] {task_id}", 1)
        else:
            updated = content
        
        if updated == content:
            return json.dumps({"warning": "No changes made, task might already be in that status"})
        
        WAL_PATH.write_text(updated, encoding="utf-8")
        
        return json.dumps({
            "success": True,
            "task": task_id,
            "status": status,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False)
```

### tools/sessions.py — управление сессиями

```python
# mcp/tools/sessions.py
import json
import subprocess
from datetime import datetime
from mcp import types
from ..config import SESSIONS_DIR, SCRIPTS_DIR, PROJECT_ROOT


class SessionTools:
    """Инструменты для управления сессиями исправлений"""

    def get_tool_definitions(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="list_sessions",
                description="Список всех сессий исправлений с их статусами.",
                inputSchema={"type": "object", "properties": {}}
            ),
            types.Tool(
                name="get_session",
                description="Детальная информация о конкретной сессии.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "ID сессии, например SESSION-001"
                        }
                    },
                    "required": ["session_id"]
                }
            ),
            types.Tool(
                name="create_session",
                description="Создать новую сессию исправлений.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Имя сессии (без SESSION-XXX префикса)"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["Critical", "High", "Medium", "Low"]
                        }
                    },
                    "required": ["name", "priority"]
                }
            ),
        ]

    def get_handlers(self) -> dict:
        return {
            "list_sessions": self._list_sessions,
            "get_session": self._get_session,
            "create_session": self._create_session,
        }

    async def _list_sessions(self, args: dict) -> str:
        if not SESSIONS_DIR.exists():
            return json.dumps({"sessions": [], "error": "Sessions directory not found"})
        
        sessions = []
        for session_dir in sorted(SESSIONS_DIR.iterdir()):
            if not session_dir.is_dir():
                continue
            
            # Ищем последний status.json
            status_files = list(session_dir.rglob("status.json"))
            status = "unknown"
            ready = False
            
            if status_files:
                latest = sorted(status_files)[-1]
                try:
                    data = json.loads(latest.read_text())
                    status = data.get("status", "unknown")
                    ready = data.get("ready_to_commit", False)
                except Exception:
                    pass
            
            sessions.append({
                "id": session_dir.name,
                "status": status,
                "ready_to_commit": ready,
                "iterations": len(list(session_dir.glob("iteration-*")))
            })
        
        return json.dumps({"sessions": sessions, "total": len(sessions)}, ensure_ascii=False, indent=2)

    async def _get_session(self, args: dict) -> str:
        session_id = args["session_id"]
        
        # Ищем директорию сессии (имя может содержать суффикс)
        matches = list(SESSIONS_DIR.glob(f"{session_id}*"))
        if not matches:
            return json.dumps({"error": f"Session {session_id} not found"})
        
        session_dir = matches[0]
        
        # Читаем session.md
        session_md = session_dir / "session.md"
        session_content = session_md.read_text(encoding="utf-8") if session_md.exists() else ""
        
        # Читаем последний status.json
        status_files = sorted(session_dir.rglob("status.json"))
        last_status = {}
        if status_files:
            try:
                last_status = json.loads(status_files[-1].read_text())
            except Exception:
                pass
        
        return json.dumps({
            "id": session_dir.name,
            "session_md": session_content[:1000],  # первые 1000 символов
            "last_status": last_status,
            "iterations": len(list(session_dir.glob("iteration-*")))
        }, ensure_ascii=False, indent=2)

    async def _create_session(self, args: dict) -> str:
        name = args["name"]
        priority = args["priority"]
        
        script = SCRIPTS_DIR / "create-session.py"
        if not script.exists():
            return json.dumps({"error": "create-session.py not found"})
        
        result = subprocess.run(
            ["python", str(script), "--name", name, "--priority", priority],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        
        return json.dumps({
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }, ensure_ascii=False)
```

### tools/dev.py — тесты, сборка, git

```python
# mcp/tools/dev.py
import json
import subprocess
import re
from mcp import types
from ..config import PROJECT_ROOT, WEB_DIR, TESTS_DIR


class DevTools:
    """Инструменты для разработки: тесты, сборка, git"""

    def get_tool_definitions(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="run_tests",
                description=(
                    "Запустить тесты pytest. Возвращает количество прошедших/упавших "
                    "и список ошибок. Вызывай перед коммитом."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "module": {
                            "type": "string",
                            "description": "Опциональный путь к модулю, например 'tests/analysis/'"
                        },
                        "verbose": {
                            "type": "boolean",
                            "description": "Включить подробный вывод. По умолчанию: false"
                        }
                    }
                }
            ),
            types.Tool(
                name="run_build",
                description="Запустить сборку React (npm run build). Возвращает статус и ошибки.",
                inputSchema={"type": "object", "properties": {}}
            ),
            types.Tool(
                name="git_status",
                description="Получить список изменённых файлов в git.",
                inputSchema={"type": "object", "properties": {}}
            ),
            types.Tool(
                name="git_commit",
                description="Закоммитить изменения. Все файлы должны быть явно указаны.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Сообщение коммита в формате: type: description"
                        },
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Список файлов для git add. Используй [] для 'git add -A'"
                        }
                    },
                    "required": ["message"]
                }
            ),
        ]

    def get_handlers(self) -> dict:
        return {
            "run_tests": self._run_tests,
            "run_build": self._run_build,
            "git_status": self._git_status,
            "git_commit": self._git_commit,
        }

    async def _run_tests(self, args: dict) -> str:
        cmd = ["python", "-m", "pytest"]
        
        module = args.get("module")
        if module:
            cmd.append(module)
        else:
            cmd.append("tests/")
        
        if args.get("verbose"):
            cmd.append("-v")
        
        cmd.extend(["--tb=short", "-q"])
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        
        # Парсим итоговую строку pytest
        output = result.stdout + result.stderr
        summary_match = re.search(r"(\d+) passed(?:, (\d+) failed)?", output)
        
        passed = int(summary_match.group(1)) if summary_match else 0
        failed = int(summary_match.group(2)) if summary_match and summary_match.group(2) else 0
        
        # Извлекаем ошибки
        errors = []
        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                errors.append(line.strip())
        
        return json.dumps({
            "success": result.returncode == 0,
            "passed": passed,
            "failed": failed,
            "errors": errors[:20],  # максимум 20 ошибок
            "returncode": result.returncode,
            "output_tail": output[-500:] if len(output) > 500 else output
        }, ensure_ascii=False, indent=2)

    async def _run_build(self, args: dict) -> str:
        result = subprocess.run(
            ["npm", "run", "build"],
            capture_output=True, text=True, cwd=WEB_DIR
        )
        
        output = result.stdout + result.stderr
        
        # TS-ошибки
        ts_errors = [l.strip() for l in output.split("\n") if "error TS" in l]
        
        return json.dumps({
            "success": result.returncode == 0,
            "typescript_errors": ts_errors,
            "returncode": result.returncode,
            "output_tail": output[-500:] if len(output) > 500 else output
        }, ensure_ascii=False, indent=2)

    async def _git_status(self, args: dict) -> str:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        
        files = []
        for line in result.stdout.strip().split("\n"):
            if line:
                status_code = line[:2].strip()
                filepath = line[3:]
                files.append({"status": status_code, "file": filepath})
        
        return json.dumps({
            "files": files,
            "total_changed": len(files)
        }, ensure_ascii=False, indent=2)

    async def _git_commit(self, args: dict) -> str:
        message = args["message"]
        files = args.get("files", [])
        
        # git add
        if files:
            for f in files:
                subprocess.run(["git", "add", f], cwd=PROJECT_ROOT)
        else:
            subprocess.run(["git", "add", "-A"], cwd=PROJECT_ROOT)
        
        # git commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        
        # Получаем hash коммита
        hash_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        
        return json.dumps({
            "success": result.returncode == 0,
            "commit_hash": hash_result.stdout.strip(),
            "message": message,
            "stdout": result.stdout,
            "stderr": result.stderr
        }, ensure_ascii=False)
```

---

## 6. Подключение к инструментам

### Точка запуска

Создай скрипт-обёртку в корне проекта:

```bash
#!/bin/bash
# run_mcp.sh
cd /ПОЛНЫЙ/ПУТЬ/К/tg-stats
source .venv/bin/activate
python -m mcp.server
```

Или Python-скрипт:

```python
# run_mcp.py (в корне проекта)
import sys
import asyncio
sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

from mcp.server import main
asyncio.run(main())
```

### Cline (VS Code)

Открыть `settings.json` (Ctrl+Shift+P → "Open User Settings JSON"):

```json
{
  "cline.mcpServers": {
    "tg-stats": {
      "command": "python",
      "args": ["/ПОЛНЫЙ/ПУТЬ/tg-stats/run_mcp.py"],
      "env": {},
      "disabled": false,
      "autoApprove": ["get_current_task", "list_sessions", "git_status", "run_tests"]
    }
  }
}
```

`autoApprove` — инструменты, которые Cline вызывает без запроса у тебя. Read-only операции можно добавлять смело. Write-операции (git_commit, create_session) лучше оставить с подтверждением.

### Roo Code (VS Code)

```json
{
  "roo-cline.mcpServers": {
    "tg-stats": {
      "command": "python",
      "args": ["/ПОЛНЫЙ/ПУТЬ/tg-stats/run_mcp.py"]
    }
  }
}
```

### Continue (VS Code)

Файл `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "tg-stats",
      "command": "python",
      "args": ["/ПОЛНЫЙ/ПУТЬ/tg-stats/run_mcp.py"],
      "env": {}
    }
  ]
}
```

### Qwen Code CLI

Если Qwen Code поддерживает MCP (проверить в документации), конфиг обычно в `~/.qwen/mcp.json` или передаётся флагом:

```json
{
  "mcpServers": {
    "tg-stats": {
      "command": "python",
      "args": ["/ПОЛНЫЙ/ПУТЬ/tg-stats/run_mcp.py"]
    }
  }
}
```

Если нативной поддержки нет — запускай сервер в HTTP-режиме (см. ниже) и подключайся как к обычному API.

### HTTP-режим (если нужно несколько клиентов)

```python
# mcp/server_http.py
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn

# Тот же app из server.py
from .server import app

sse = SseServerTransport("/messages/")

async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

starlette_app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),
    Mount("/messages/", app=sse.handle_post_message),
])

if __name__ == "__main__":
    uvicorn.run(starlette_app, host="127.0.0.1", port=8765)
```

Запуск: `python -m mcp.server_http`  
URL для клиентов: `http://127.0.0.1:8765/sse`

---

## 7. Отладка и тестирование

### MCP Inspector — главный инструмент отладки

```bash
# Установить один раз
npm install -g @modelcontextprotocol/inspector

# Запустить с твоим сервером
npx @modelcontextprotocol/inspector python /ПУТЬ/tg-stats/run_mcp.py
```

Открой браузер — увидишь:
- Список всех инструментов
- Форму для вызова каждого
- Полный JSON-RPC лог

### Ручное тестирование через stdin

```bash
# Запустить сервер
python run_mcp.py

# В другом терминале — отправить JSON-RPC вручную
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python run_mcp.py
```

### Тесты для инструментов

```python
# tests/mcp/test_wal_tools.py
import pytest
import json
from mcp.tools.wal import WALTools


@pytest.fixture
def wal_tools(tmp_path):
    """Создаёт WALTools с тестовым WAL.md"""
    wal_content = """# WAL

## Текущая задача

### 🔍 Test Task
**Статус:** 🔄 В ПРОЦЕССЕ

## Очередь задач

- [x] Завершённая задача
- [ ] Незавершённая задача
"""
    wal_file = tmp_path / "WAL.md"
    wal_file.write_text(wal_content, encoding="utf-8")
    
    # Патчим путь
    import mcp.config as cfg
    original = cfg.WAL_PATH
    cfg.WAL_PATH = wal_file
    
    yield WALTools()
    
    cfg.WAL_PATH = original


@pytest.mark.asyncio
async def test_get_current_task(wal_tools):
    result = await wal_tools._get_current_task({})
    data = json.loads(result)
    assert "task" in data
    assert "Test Task" in data["task"]


@pytest.mark.asyncio
async def test_list_tasks_pending(wal_tools):
    result = await wal_tools._list_tasks({"status": "pending"})
    data = json.loads(result)
    assert data["total"] == 1
    assert "Незавершённая" in data["tasks"][0]["task"]
```

### Логирование

```python
# В начале server.py добавь:
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr  # ОБЯЗАТЕЛЬНО stderr, не stdout
)

logger = logging.getLogger("tg-stats-mcp")
```

---

## 8. Шаблон нового инструмента

Когда нужно добавить новый инструмент — копируй этот шаблон.

### Чеклист перед написанием

Ответь на 4 вопроса:

1. **Меняет ли состояние?** → Если да, нужна защита от дублей
2. **Может ли упасть?** → Если да, оберни в try/except в call_tool
3. **Нужны параметры?** → Опиши в inputSchema с `description`
4. **Это точно MCP, а не Skill?** → Если это правило/политика — лучше в AGENTS.md

### Шаблон файла

```python
# mcp/tools/my_feature.py
import json
from mcp import types
from ..config import PROJECT_ROOT  # импортируй нужные пути


class MyFeatureTools:
    """
    Одна строка: что делает эта группа инструментов.
    """

    def get_tool_definitions(self) -> list[types.Tool]:
        """Объявление инструментов. Здесь агент узнаёт что доступно."""
        return [
            types.Tool(
                name="my_tool_name",            # snake_case, глагол_существительное
                description=(
                    "Что делает инструмент. "   # Первое предложение — суть
                    "Когда его вызывать. "       # Второе — контекст использования
                    "Что возвращает."            # Третье — формат ответа
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "required_param": {
                            "type": "string",
                            "description": "Чёткое описание что передавать"
                        },
                        "optional_param": {
                            "type": "integer",
                            "description": "Описание. По умолчанию: 10",
                            "default": 10
                        }
                    },
                    "required": ["required_param"]  # только реально обязательные
                }
            ),
        ]

    def get_handlers(self) -> dict:
        """Словарь name → handler. Имена должны совпадать с Tool.name."""
        return {
            "my_tool_name": self._my_tool_name,
        }

    async def _my_tool_name(self, args: dict) -> str:
        """
        Реализация инструмента.
        ВСЕГДА возвращает строку (обычно JSON).
        НИКОГДА не поднимает исключение — возвращает {"error": "..."}.
        """
        # 1. Извлекаем параметры с дефолтами
        required_param = args["required_param"]
        optional_param = args.get("optional_param", 10)
        
        # 2. Логика
        try:
            result = self._do_something(required_param, optional_param)
            
            # 3. Возвращаем JSON-строку
            return json.dumps({
                "success": True,
                "result": result,
                # Включай только полезное. Не надо дублировать входные параметры.
            }, ensure_ascii=False, indent=2)
            
        except FileNotFoundError as e:
            return json.dumps({"error": f"File not found: {e}"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False)

    def _do_something(self, param: str, limit: int) -> dict:
        """Вспомогательный метод. Здесь чистая логика без MCP-специфики."""
        # ...
        return {}
```

### Подключение нового инструмента к серверу

В `mcp/server.py` добавить три строки:

```python
from .tools.my_feature import MyFeatureTools  # 1. импорт

my_feature = MyFeatureTools()                  # 2. инициализация

ALL_TOOLS = [
    *wal.get_tool_definitions(),
    *sessions.get_tool_definitions(),
    *dev.get_tool_definitions(),
    *project.get_tool_definitions(),
    *my_feature.get_tool_definitions(),        # 3. добавить в список
]

HANDLERS = {
    **wal.get_handlers(),
    **sessions.get_handlers(),
    **dev.get_handlers(),
    **project.get_handlers(),
    **my_feature.get_handlers(),               # 4. добавить хэндлеры
}
```

---

## 9. Типичные ошибки

### print() вместо sys.stderr

```python
# ❌ Ломает протокол — stdout занят JSON-RPC
print("Debug message")

# ✅ Правильно
import sys
print("Debug message", file=sys.stderr)
# или
logger.debug("Debug message")
```

### Поднятие исключений из хэндлера

```python
# ❌ Уронит сервер
async def _my_tool(self, args):
    raise ValueError("something wrong")

# ✅ Возвращай ошибку как результат
async def _my_tool(self, args):
    try:
        ...
    except ValueError as e:
        return json.dumps({"error": str(e)})
```

### Нет описания в inputSchema

```python
# ❌ Агент будет гадать что передавать
"properties": {
    "mode": {"type": "string"}
}

# ✅ Всегда description и enum если значения фиксированные
"properties": {
    "mode": {
        "type": "string",
        "enum": ["semantic", "keyword", "hybrid"],
        "description": "Тип поиска. hybrid рекомендуется для большинства запросов"
    }
}
```

### Возврат не-строки из хэндлера

```python
# ❌ TextContent ожидает str
return {"success": True}

# ✅
return json.dumps({"success": True})
```

### Слишком большой ответ

```python
# ❌ Агент захлебнётся в данных
return json.dumps({"all_messages": all_1_million_messages})

# ✅ Ограничивай
return json.dumps({
    "total": len(messages),
    "sample": messages[:10],
    "hint": "Use filter_messages tool for specific queries"
})
```

---

## 10. Чеклист при добавлении инструмента

Перед тем как считать инструмент готовым:

```
□ Имя в snake_case, начинается с глагола (get_, list_, create_, run_, update_)
□ description объясняет: ЧТО делает / КОГДА вызывать / ЧТО возвращает
□ Все параметры имеют description в inputSchema
□ required[] содержит только действительно обязательные параметры
□ Хэндлер возвращает строку (обычно json.dumps)
□ Хэндлер не поднимает исключения — только {"error": "..."}
□ Ответ ограничен по размеру (не возвращает мегабайты данных)
□ Имя в get_handlers() совпадает с Tool.name
□ Инструмент добавлен в ALL_TOOLS и HANDLERS в server.py
□ Написан хотя бы один тест (test_my_tool.py)
□ Протестировано через MCP Inspector
□ Логи идут в sys.stderr, не в stdout
```

---

## Быстрый старт (TL;DR)

```bash
# 1. Установить зависимости
pip install mcp pydantic pytest pytest-asyncio

# 2. Создать структуру
mkdir -p mcp/tools
touch mcp/__init__.py mcp/tools/__init__.py

# 3. Создать файлы из гайда выше
# mcp/config.py, mcp/server.py, mcp/tools/*.py

# 4. Проверить что запускается
python run_mcp.py
# Должен молчать и ждать JSON-RPC на stdin

# 5. Открыть в Inspector
npx @modelcontextprotocol/inspector python run_mcp.py

# 6. Добавить в Cline/Roo/Continue (settings.json)

# 7. Проверить в агенте:
# "Вызови get_current_task и скажи что там"
```
