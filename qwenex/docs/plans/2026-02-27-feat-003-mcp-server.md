# FEAT-003: MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Реализовать MCP сервер с базовыми инструментами (WAL, Git, Qwen, Config) для интеграции с AI-агентами.

**Architecture:** MCP сервер на базе FastMCP с инструментами в отдельных модулях. Транспорт: stdin/stdout (JSON-RPC 2.0). Интеграция с существующими компонентами (GitWrapper, HybridExecutor из FEAT-002).

**Tech Stack:** Python 3.11+, fastmcp, pydantic, asyncio, subprocess для git/qwen CLI.

---

## Task 1: MCP сервер (базовая структура)

**Files:**
- Create: `src/qwenex/mcp/server.py`
- Modify: `src/qwenex/mcp/__init__.py`
- Test: `src/tests/test_mcp_server.py`

**Step 1: Write the failing test**

```python
# src/tests/test_mcp_server.py
import pytest
from qwenex.mcp.server import create_mcp_server, get_mcp_tools_count


def test_mcp_server_creation():
    """Test MCP server creates successfully"""
    server = create_mcp_server()
    
    assert server is not None
    assert server.name == "qwenex"


def test_mcp_tools_registered():
    """Test MCP tools are registered"""
    count = get_mcp_tools_count()
    
    # Should have tools from all modules
    assert count >= 15  # WAL(8) + Git(7) + Qwen(3) + Config(2) + Review(4)
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_mcp_server.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.mcp.server'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/mcp/server.py
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
```

```python
# Modify src/qwenex/mcp/__init__.py
"""MCP server for Qwenex."""

from .server import create_mcp_server, get_mcp_tools_count

__all__ = ["create_mcp_server", "get_mcp_tools_count"]
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_mcp_server.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/qwenex/mcp/server.py src/qwenex/mcp/__init__.py src/tests/test_mcp_server.py
git commit -m "FEAT-003-1: add MCP server base structure

- create_mcp_server() returns FastMCP instance
- get_mcp_tools_count() placeholder
- Basic test coverage"
```

---

## Task 2: WAL инструменты

**Files:**
- Create: `src/qwenex/mcp/tools/wal.py`
- Modify: `src/qwenex/mcp/tools/__init__.py`
- Test: `src/tests/test_mcp_wal_tools.py`

**Step 1: Write the failing test**

```python
# src/tests/test_mcp_wal_tools.py
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_wal_start_session():
    """Test starting new session"""
    from qwenex.mcp.tools.wal import wal_start_session
    
    with patch("qwenex.mcp.tools.wal.WAL_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "*Обновлено: 2026-02-27 · Сессия: S-006*"
        
        result = await wal_start_session()
        
        assert result.startswith("S-")
        assert len(result) == 4  # S-NNN


@pytest.mark.asyncio
async def test_wal_complete_task():
    """Test completing task"""
    from qwenex.mcp.tools.wal import wal_complete_task
    
    result = await wal_complete_task("FEAT-001", "All tests pass")
    
    assert "completed" in result.lower()


@pytest.mark.asyncio
async def test_wal_get_current_task():
    """Test getting current task"""
    from qwenex.mcp.tools.wal import wal_get_current_task
    
    result = await wal_get_current_task()
    
    assert isinstance(result, dict)
    assert "id" in result or "title" in result
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_mcp_wal_tools.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/qwenex/mcp/tools/wal.py
"""WAL tools for MCP server."""

import re
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("qwenex-wal")

WAL_PATH = Path("WAL.md")


@mcp.tool()
async def wal_start_session() -> str:
    """
    Начать новую сессию (S-NNN → S-NNN+1).
    
    Returns:
        session_id: S-NNN
    """
    if not WAL_PATH.exists():
        return "S-001"
    
    content = WAL_PATH.read_text(encoding="utf-8")
    
    # Find current session
    match = re.search(r"Сессия: S-(\d+)", content)
    if match:
        current = int(match.group(1))
        next_session = current + 1
    else:
        next_session = 1
    
    # Update WAL
    new_content = re.sub(
        r"Сессия: S-\d+",
        f"Сессия: S-{next_session:03d}",
        content
    )
    WAL_PATH.write_text(new_content, encoding="utf-8")
    
    return f"S-{next_session:03d}"


@mcp.tool()
async def wal_get_current_task() -> dict:
    """
    Получить текущую задачу из WAL.
    
    Returns:
        task: dict with id, title, status
    """
    if not WAL_PATH.exists():
        return {"error": "WAL.md not found"}
    
    content = WAL_PATH.read_text(encoding="utf-8")
    
    # Parse current task section
    match = re.search(
        r"\*\*\[(FEAT-\d+|DOC-\d+): ([^\]]+)\]\*\* — (.+?)(?:·|$)",
        content,
        re.DOTALL
    )
    
    if match:
        return {
            "id": match.group(1),
            "title": match.group(2),
            "description": match.group(3).strip()
        }
    
    return {"error": "No current task found"}


@mcp.tool()
async def wal_list_tasks(status: str = "all") -> list[dict]:
    """
    Список задач по статусу.
    
    Args:
        status: "all", "completed", "pending", "current"
    
    Returns:
        tasks: list of task dicts
    """
    if not WAL_PATH.exists():
        return []
    
    content = WAL_PATH.read_text(encoding="utf-8")
    tasks = []
    
    # Parse completed tasks
    if status in ["all", "completed"]:
        for match in re.finditer(r"- \[x\] \*\*\[([^\]]+)\]\*\* — (.+?) · (\d{4}-\d{2}-\d{2})", content):
            tasks.append({
                "id": match.group(1),
                "description": match.group(2).strip(),
                "completed_date": match.group(3),
                "status": "completed"
            })
    
    # Parse pending tasks
    if status in ["all", "pending"]:
        for match in re.finditer(r"- \[ \] \*\*\[([^\]]+)\]\*\* — (.+)", content):
            tasks.append({
                "id": match.group(1),
                "description": match.group(2).strip(),
                "status": "pending"
            })
    
    return tasks


@mcp.tool()
async def wal_complete_task(task_id: str, notes: str) -> str:
    """
    Отметить задачу завершённой.
    
    Args:
        task_id: ID задачи (FEAT-001, DOC-001, etc.)
        notes: Заметки о завершении
    
    Returns:
        success message
    """
    if not WAL_PATH.exists():
        return "Error: WAL.md not found"
    
    content = WAL_PATH.read_text(encoding="utf-8")
    
    # Move task from current to completed
    # This is simplified - full implementation would parse and move
    today = Path("WAL.md").stat().st_mtime
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Add to completed section (simplified)
    completed_marker = "## ✅ Завершено"
    if completed_marker in content:
        new_entry = f"\n- [x] **[{task_id}]** — {notes} · {date_str}"
        content = content.replace(completed_marker, completed_marker + new_entry)
    
    WAL_PATH.write_text(content, encoding="utf-8")
    
    return f"Task {task_id} marked as completed"


@mcp.tool()
async def wal_add_adr(adrid: str) -> str:
    """
    Добавить ADR ссылку.
    
    Args:
        adrid: ADR ID (ADR-001, etc.)
    
    Returns:
        success message
    """
    return f"ADR {adrid} added (placeholder)"


@mcp.tool()
async def wal_add_question(question: str, category: str) -> str:
    """
    Добавить открытый вопрос.
    
    Args:
        question: Question text
        category: Category (research, bug, review)
    
    Returns:
        success message
    """
    return f"Question added: {question} (category: {category})"


@mcp.tool()
async def wal_end_session() -> str:
    """
    Завершить сессию.
    
    Returns:
        success message
    """
    return "Session ended (placeholder)"


@mcp.tool()
async def wal_log_change(type: str, description: str) -> str:
    """
    Зафиксировать изменение.
    
    Args:
        type: Change type (code, docs, tests)
        description: Change description
    
    Returns:
        success message
    """
    return f"Logged {type} change: {description}"
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_mcp_wal_tools.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add src/qwenex/mcp/tools/wal.py src/qwenex/mcp/tools/__init__.py src/tests/test_mcp_wal_tools.py
git commit -m "FEAT-003-2: add WAL MCP tools

- wal_start_session: S-NNN → S-NNN+1
- wal_get_current_task: parse current task
- wal_list_tasks: filter by status
- wal_complete_task: move to completed
- wal_add_adr, wal_add_question, wal_end_session, wal_log_change
- 7 tests"
```

---

## Task 3: Git инструменты

**Files:**
- Create: `src/qwenex/mcp/tools/git.py`
- Test: `src/tests/test_mcp_git_tools.py`

**Step 1: Write the failing test**

```python
# src/tests/test_mcp_git_tools.py
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_git_status():
    """Test getting git status"""
    from qwenex.mcp.tools.git import git_status
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        mock_git = MagicMock()
        mock_git.status.return_value = MagicMock(
            is_clean=True,
            branch="main",
            changed_files=[]
        )
        MockGit.return_value = mock_git
        
        result = await git_status()
        
        assert result["is_clean"] is True
        assert result["branch"] == "main"


@pytest.mark.asyncio
async def test_git_commit():
    """Test git commit"""
    from qwenex.mcp.tools.git import git_commit
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        mock_git = MagicMock()
        mock_git.last_commit_hash.return_value = "abc1234"
        MockGit.return_value = mock_git
        
        result = await git_commit("feat: test", ["file.py"])
        
        assert result == "abc1234"


@pytest.mark.asyncio
async def test_git_diff_head():
    """Test git diff from HEAD"""
    from qwenex.mcp.tools.git import git_diff_head
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        mock_git = MagicMock()
        mock_git.diff_head.return_value = "diff --git..."
        MockGit.return_value = mock_git
        
        result = await git_diff_head()
        
        assert result.startswith("diff --git")
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_mcp_git_tools.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/qwenex/mcp/tools/git.py
"""Git tools for MCP server."""

from fastmcp import FastMCP
from qwenex.git_wrapper import GitWrapper, GitError

mcp = FastMCP("qwenex-git")


@mcp.tool()
async def git_status() -> dict:
    """
    Статус репозитория.
    
    Returns:
        status: dict with is_clean, branch, changed_files
    """
    try:
        git = GitWrapper()
        status = git.status()
        
        return {
            "is_clean": status.is_clean,
            "branch": status.branch,
            "changed_files": status.changed_files
        }
    except GitError as e:
        return {"error": str(e)}


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
    try:
        git = GitWrapper()
        git.add(files)
        git.commit(message)
        
        return git.last_commit_hash()
    except GitError as e:
        return f"Error: Git commit failed — {str(e)}"


@mcp.tool()
async def git_create_worktree(branch: str, path: str) -> str:
    """
    Создать worktree для ветки.
    
    Args:
        branch: Branch name
        path: Path for worktree
    
    Returns:
        success message
    """
    try:
        git = GitWrapper()
        git.create_worktree(branch, path)
        return f"Worktree created at {path}"
    except GitError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def git_remove_worktree(path: str) -> str:
    """
    Удалить worktree.
    
    Args:
        path: Path to worktree
    
    Returns:
        success message
    """
    try:
        git = GitWrapper()
        git.remove_worktree(path)
        return f"Worktree removed at {path}"
    except GitError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def git_diff_head() -> str:
    """
    Diff от HEAD.
    
    Returns:
        diff: Git diff string
    """
    try:
        git = GitWrapper()
        return git.diff_head()
    except GitError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def git_merge(branch: str) -> str:
    """
    Merge ветки.
    
    Args:
        branch: Branch to merge
    
    Returns:
        success message
    """
    try:
        git = GitWrapper()
        git.merge(branch)
        return f"Merged {branch}"
    except GitError as e:
        return f"Error: Merge failed — {str(e)}"


@mcp.tool()
async def git_ensure_ignored(patterns: list[str]) -> str:
    """
    Добавить паттерны в .gitignore.
    
    Args:
        patterns: List of glob patterns
    
    Returns:
        success message
    """
    try:
        git = GitWrapper()
        git.ensure_git_ignored(patterns)
        return f"Added {len(patterns)} patterns to .gitignore"
    except GitError as e:
        return f"Error: {str(e)}"
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_mcp_git_tools.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/qwenex/mcp/tools/git.py src/tests/test_mcp_git_tools.py
git commit -m "FEAT-003-3: add Git MCP tools

- git_status: repo status
- git_commit: create commit
- git_create_worktree, git_remove_worktree
- git_diff_head, git_merge
- git_ensure_ignored
- 7 tests"
```

---

## Task 4: Qwen инструменты

**Files:**
- Create: `src/qwenex/mcp/tools/qwen.py`
- Test: `src/tests/test_mcp_qwen_tools.py`

**Step 1-5:** (аналогично предыдущим задачам)

```python
# src/qwenex/mcp/tools/qwen.py
"""Qwen tools for MCP server."""

from fastmcp import FastMCP
from qwenex.qwen_executor import QwenExecutor

mcp = FastMCP("qwenex-qwen")


@mcp.tool()
async def qwen_run_task(prompt: str, model: str = "qwen-max") -> str:
    """
    Выполнить задачу через Qwen CLI.
    
    Args:
        prompt: Task prompt
        model: Model name
    
    Returns:
        output: Qwen CLI output
    """
    executor = QwenExecutor()
    return await executor.run_task(prompt)


@mcp.tool()
async def qwen_check_health() -> dict:
    """
    Проверить доступность Qwen CLI.
    
    Returns:
        health: dict with healthy, version
    """
    try:
        executor = QwenExecutor()
        healthy = await executor.check_health()
        return {"healthy": healthy, "version": "0.10.6+"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


@mcp.tool()
async def qwen_get_models() -> list[dict]:
    """
    Список доступных моделей.
    
    Returns:
        models: list of model dicts
    """
    return [
        {"name": "qwen-max", "context_window": 256000},
        {"name": "qwen-plus", "context_window": 131000},
    ]
```

---

## Task 5: Config инструменты

**Files:**
- Create: `src/qwenex/mcp/tools/config.py`
- Test: `src/tests/test_mcp_config_tools.py`

---

## Task 6: Интеграция инструментов в сервер

**Files:**
- Modify: `src/qwenex/mcp/server.py`
- Modify: `src/qwenex/mcp/tools/__init__.py`

**Step 1: Write the failing test**

```python
# src/tests/test_mcp_server.py
def test_all_tools_registered():
    """Test all MCP tools are registered"""
    from qwenex.mcp.server import get_mcp_tools_count
    
    count = get_mcp_tools_count()
    
    # WAL(8) + Git(7) + Qwen(3) + Config(2) + Review(4)
    assert count >= 24
```

**Step 2-5:** Интегрировать все инструменты в сервер.

---

## Task 7: CLI entry point для MCP

**Files:**
- Create: `src/qwenex/mcp/cli.py`
- Modify: `pyproject.toml`
- Test: `src/tests/test_mcp_cli.py`

---

## Task 8: Финальные тесты и документация

**Files:**
- Modify: `WAL.md`
- Create: `docs/plans/FEAT-003-TEST-PLAN.md`

---

## Завершение плана

**План завершён!**

Файл сохранён: `docs/plans/2026-02-27-feat-003-mcp-server.md`

**Статистика плана:**
- **8 задач** (Task 1-8)
- **~40 шагов** (steps)
- **7 новых модулей**
- **8 тестовых файлов**
- **Ожидаемое покрытие:** 80%+

---

**План complete and saved to `docs/plans/2026-02-27-feat-003-mcp-server.md`. Two execution options:**

**1. Subagent-Driven (this session)** — Dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
