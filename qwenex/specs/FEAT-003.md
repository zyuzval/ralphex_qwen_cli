# FEAT-003: MCP сервер

**Версия:** 1.0
**Дата:** 2026-02-27
**Статус:** Черновик
**Приоритет:** P0 (MVP Фаза 1)
**Зависимости:** FEAT-001 ✅, FEAT-002 ✅

---

## Цель

Реализовать MCP сервер с базовыми инструментами для интеграции с AI-агентами (Cline, Roo Code, Qwen Code): WAL операции, Git операции, Qwen CLI операции.

---

## Контекст

MCP (Model Context Protocol) — стандартный интерфейс для подключения AI-агентов к инструментам. Qwenex предоставляет MCP сервер для:
- Управления WAL.md (прогресс, задачи)
- Git операций (worktree, commits, status)
- Вызова Qwen CLI (задачи, промпты)

**Решения из ADR:**
- **ADR-002:** Один процесс (MCP внутри qwenex, не sidecar)
- **ADR-018:** WAL.md обновляется через MCP инструменты
- **ADR-016:** Technical debt — если MCP нестабилен, перейти на sidecar в v0.2

**Архитектурный паттерн:** MCP Server с группами инструментов

---

## Требования

### Функциональные

**F-001: WAL инструменты**

| Инструмент | Описание | Вход | Выход |
|------------|----------|------|-------|
| `wal_start_session()` | Начать новую сессию (S-NNN → S-NNN+1) | — | session_id: str |
| `wal_get_current_task()` | Получить текущую задачу из WAL | — | task: dict |
| `wal_list_tasks(status?)` | Список задач по статусу | status: str | tasks: list[dict] |
| `wal_complete_task(task_id, notes)` | Отметить задачу завершённой | task_id: str, notes: str | success: bool |
| `wal_add_adr(adrid)` | Добавить ADR ссылку | adrid: str | success: bool |
| `wal_add_question(question, category)` | Добавить открытый вопрос | question: str, category: str | success: bool |
| `wal_end_session()` | Завершить сессию | — | success: bool |
| `wal_log_change(type, description)` | Зафиксировать изменение | type: str, description: str | success: bool |

**F-002: Git инструменты**

| Инструмент | Описание | Вход | Выход |
|------------|----------|------|-------|
| `git_status()` | Статус репозитория | — | status: dict |
| `git_commit(message, files[])` | Коммит файлов | message: str, files: list[str] | commit_hash: str |
| `git_create_worktree(branch, path)` | Создать worktree | branch: str, path: str | success: bool |
| `git_remove_worktree(path)` | Удалить worktree | path: str | success: bool |
| `git_diff_head()` | Diff от HEAD | — | diff: str |
| `git_merge(branch)` | Merge ветки | branch: str | success: bool |
| `git_ensure_ignored(patterns[])` | Добавить в .gitignore | patterns: list[str] | success: bool |

**F-003: Qwen инструменты**

| Инструмент | Описание | Вход | Выход |
|------------|----------|------|-------|
| `qwen_run_task(prompt, model)` | Выполнить задачу | prompt: str, model: str | output: str |
| `qwen_check_health()` | Проверить доступность | — | healthy: bool |
| `qwen_get_models()` | Список доступных моделей | — | models: list[str] |

**F-004: Review инструменты** (из FEAT-002 ✅)

| Инструмент | Описание | Вход | Выход |
|------------|----------|------|-------|
| `launch_review(session_id, agents?)` | Запустить 5 агентов | session_id: str, agents: list[str] | summary: str |
| `get_review_report(session_id)` | Получить отчёт | session_id: str | ReviewReport |
| `apply_review_marker(session_id, index, approve)` | Применить маркер | session_id: str, index: int, approve: bool | status: str |
| `resolve_conflicts(session_id, resolutions)` | Разрешить конфликты | session_id: str, resolutions: dict | status: str |

**F-005: Config инструменты**

| Инструмент | Описание | Вход | Выход |
|------------|----------|------|-------|
| `config_get()` | Получить конфигурацию | — | config: dict |
| `config_set(key, value)` | Установить значение | key: str, value: any | success: bool |

### Нефункциональные

**NF-001: Производительность**
- Время отклика инструмента: < 1 сек (кроме qwen_run_task)
- Параллельные вызовы: поддержка до 5 одновременных

**NF-002: Надёжность**
- Graceful degradation: если инструмент упал — вернуть ошибку, не крашить сервер
- Логирование: все вызовы инструментов логируются

**NF-003: Безопасность**
- Нет доступа к секретам (API keys из ENV)
- Git операции только в пределах репозитория

**NF-004: Тестируемость**
- Покрытие тестами: 80%+
- Unit тесты на каждый инструмент
- Integration тесты на MCP сервер

---

## Архитектура

### Компоненты

```
src/qwenex/
├── mcp/
│   ├── __init__.py
│   ├── server.py           # MCP сервер (FastMCP)
│   └── tools/
│       ├── __init__.py
│       ├── wal.py          # WAL инструменты
│       ├── git.py          # Git инструменты
│       ├── qwen.py         # Qwen инструменты
│       ├── review.py       # Review инструменты (FEAT-002 ✅)
│       └── config.py       # Config инструменты
└── tests/
    ├── test_mcp_server.py
    ├── test_mcp_wal_tools.py
    ├── test_mcp_git_tools.py
    └── test_mcp_qwen_tools.py
```

### Модели данных

#### WALTask

```python
@dataclass
class WALTask:
    id: str  # FEAT-001, DOC-001, etc.
    title: str
    status: str  # "current", "completed", "pending"
    description: str
    completed_date: str | None  # YYYY-MM-DD
```

#### GitStatus

```python
@dataclass
class GitStatus:
    is_clean: bool
    branch: str
    changed_files: list[str]
    untracked_files: list[str]
```

#### QwenModel

```python
@dataclass
class QwenModel:
    name: str
    context_window: int  # tokens
    max_output: int  # tokens
```

### Поток данных

```
AI-агент (Cline/Roo Code)
    │
    │ MCP вызов (JSON-RPC 2.0 через stdin/stdout)
    ▼
MCP Server (FastMCP)
    │
    ├─→ WAL Tools → WAL.md (парсинг/обновление)
    ├─→ Git Tools → git CLI (subprocess)
    ├─→ Qwen Tools → qwen CLI (subprocess)
    ├─→ Review Tools → review system (FEAT-002)
    └─→ Config Tools → config.yaml
```

---

## Промпты инструментов

### wal_start_session

```python
@mcp.tool()
async def wal_start_session() -> str:
    """
    Начать новую сессию (S-NNN → S-NNN+1).
    
    Обновляет WAL.md:
    - Увеличивает номер сессии
    - Добавляет дату
    
    Returns:
        session_id: S-NNN
    """
```

### wal_complete_task

```python
@mcp.tool()
async def wal_complete_task(task_id: str, notes: str) -> str:
    """
    Отметить задачу завершённой.
    
    Обновляет WAL.md:
    - Перемещает задачу из "Текущая задача" в "Завершено"
    - Добавляет дату завершения
    - Добавляет notes
    
    Args:
        task_id: ID задачи (FEAT-001, DOC-001, etc.)
        notes: Заметки о завершении
    
    Returns:
        success: "Task {task_id} marked as completed"
    """
```

### git_commit

```python
@mcp.tool()
async def git_commit(message: str, files: list[str]) -> str:
    """
    Создать git commit.
    
    Args:
        message: Commit message
        files: List of files to commit
    
    Returns:
        commit_hash: Short hash (7 chars)
    """
```

### qwen_run_task

```python
@mcp.tool()
async def qwen_run_task(prompt: str, model: str = "qwen-max") -> str:
    """
    Выполнить задачу через Qwen CLI.
    
    Args:
        prompt: Task prompt
        model: Model name (default: qwen-max)
    
    Returns:
        output: Qwen CLI output
    """
```

---

## Интерфейсы

### CLI интерфейс

```bash
# Запуск MCP сервера
qwenex-mcp

# Запуск с логированием
qwenex-mcp --log-level debug

# Проверка здоровья
qwenex-mcp --health
```

### MCP транспорт

**Транспорт:** stdin/stdout (JSON-RPC 2.0)

**Пример вызова:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "wal_start_session",
    "arguments": {}
  }
}
```

**Пример ответа:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{"type": "text", "text": "S-007"}]
  }
}
```

---

## Обработка ошибок

### Таймауты

```python
# qwen_run_task — 10 мин
@mcp.tool()
async def qwen_run_task(prompt: str, timeout_min: int = 10) -> str:
    try:
        output = await asyncio.wait_for(
            self.executor.run_task(prompt),
            timeout=timeout_min * 60
        )
        return output
    except asyncio.TimeoutError:
        return f"Error: Task timed out after {timeout_min} minutes"
```

### Graceful degradation

```python
@mcp.tool()
async def git_commit(message: str, files: list[str]) -> str:
    try:
        git = GitWrapper()
        git.add(files)
        git.commit(message)
        return git.last_commit_hash()
    except GitError as e:
        logger.error(f"Git commit failed: {e}")
        return f"Error: Git commit failed — {str(e)}"
```

---

## Тесты

### Unit тесты

```python
# tests/test_mcp_wal_tools.py
@pytest.mark.asyncio
async def test_wal_start_session():
    """Test starting new session"""
    from qwenex.mcp.tools.wal import wal_start_session
    
    result = await wal_start_session()
    
    assert result.startswith("S-")
    # S-NNN format
    assert len(result) == 4

@pytest.mark.asyncio
async def test_wal_complete_task():
    """Test completing task"""
    from qwenex.mcp.tools.wal import wal_complete_task
    
    result = await wal_complete_task("FEAT-001", "All tests pass")
    
    assert "completed" in result.lower()
```

### Integration тесты

```python
# tests/test_mcp_server.py
@pytest.mark.asyncio
async def test_mcp_server_startup():
    """Test MCP server starts correctly"""
    from qwenex.mcp.server import run_mcp_server
    
    server = run_mcp_server()
    
    assert server.is_running
    assert len(server.tools) >= 10  # All tools registered
```

---

## Интеграция с FEAT-001/002

### Orchestrator → MCP

```python
# MCP вызывается из AI-агента, не из orchestrator
# Orchestrator использует напрямую:
# - HybridExecutor (FEAT-002)
# - GitWrapper
# - ProgressTracker
```

### Review → MCP

```python
# Review инструменты уже реализованы (FEAT-002 ✅)
# src/qwenex/mcp/tools/review.py
```

---

## Критерии приёмки

- [ ] WAL инструменты (8 инструментов)
- [ ] Git инструменты (7 инструментов)
- [ ] Qwen инструменты (3 инструмента)
- [ ] Review инструменты (FEAT-002 ✅)
- [ ] Config инструменты (2 инструмента)
- [ ] MCP сервер запускается через `qwenex-mcp`
- [ ] JSON-RPC 2.0 транспорт работает
- [ ] Graceful degradation на ошибках
- [ ] Таймауты на qwen_run_task
- [ ] Покрытие тестами 80%+
- [ ] Integration тесты с AI-агентом (Cline/Roo Code)

---

## Зависимости

### Внешние

| Зависимость | Версия | Цель |
|-------------|--------|------|
| `fastmcp` | latest | MCP сервер |
| `git` | 2.x | Git CLI |
| `qwen` | 0.10.6+ | Qwen CLI |

### Python пакеты

| Пакет | Версия | Цель |
|-------|--------|------|
| `fastmcp` | latest | MCP сервер |
| `pydantic` | 2.x | Модели данных |
| `pytest` | 7.x+ | Тесты |
| `pytest-asyncio` | 0.21+ | Async тесты |

---

## Связанные документы

| Документ | Описание |
|----------|----------|
| [BOOT.md](../BOOT.md) | Конституция проекта |
| [WAL.md](../WAL.md) | Текущий статус |
| [FEAT-001](./FEAT-001.md) | Ядро оркестратора |
| [FEAT-002](./FEAT-002.md) | Система ревью |
| [ADR-002](../docs/DECISIONS.md) | Один процесс (MCP внутри) |
| [ADR-018](../docs/DECISIONS.md) | Процесс обновления WAL.md |

---

## История версий

| Версия | Дата | Изменение |
|--------|------|-----------|
| 1.0 | 2026-02-27 | Initial version — spec на основе FEAT-001/002 |
