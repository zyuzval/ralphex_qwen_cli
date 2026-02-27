"""Tests for WAL MCP tools."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


@pytest.mark.asyncio
async def test_wal_start_session():
    """Test starting new session"""
    from qwenex.mcp.tools.wal import wal_start_session
    
    with patch("qwenex.mcp.tools.wal.WAL_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "*Обновлено: 2026-02-27 · Сессия: S-006*"
        mock_path.stat.return_value = MagicMock(st_mtime=1234567890)
        
        result = await wal_start_session()
        
        assert result.startswith("S-")
        assert len(result) == 5  # S-NNN format (e.g., S-007)


@pytest.mark.asyncio
async def test_wal_start_session_no_file():
    """Test starting session when WAL.md doesn't exist"""
    from qwenex.mcp.tools.wal import wal_start_session
    
    with patch("qwenex.mcp.tools.wal.WAL_PATH") as mock_path:
        mock_path.exists.return_value = False
        
        result = await wal_start_session()
        
        assert result == "S-001"


@pytest.mark.asyncio
async def test_wal_get_current_task():
    """Test getting current task"""
    from qwenex.mcp.tools.wal import wal_get_current_task
    
    with patch("qwenex.mcp.tools.wal.WAL_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = """
## ⚡ Текущая задача

**[FEAT-003: MCP сервер]** — Базовые инструменты
"""
        
        result = await wal_get_current_task()
        
        assert isinstance(result, dict)
        assert "id" in result or "FEAT-003" in str(result)


@pytest.mark.asyncio
async def test_wal_list_tasks():
    """Test listing tasks"""
    from qwenex.mcp.tools.wal import wal_list_tasks
    
    with patch("qwenex.mcp.tools.wal.WAL_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = """
## ✅ Завершено

- [x] **[FEAT-001]** — Ядро оркестратора · 2026-02-27

## 📋 Очередь

- [ ] **[FEAT-003]** — MCP сервер
"""
        
        result = await wal_list_tasks("all")
        
        assert isinstance(result, list)


@pytest.mark.asyncio
async def test_wal_complete_task():
    """Test completing task"""
    from qwenex.mcp.tools.wal import wal_complete_task
    
    with patch("qwenex.mcp.tools.wal.WAL_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "## ✅ Завершено\n"
        mock_path.stat.return_value = MagicMock(st_mtime=1234567890)
        
        result = await wal_complete_task("FEAT-001", "All tests pass")
        
        assert "completed" in result.lower()


@pytest.mark.asyncio
async def test_wal_log_change():
    """Test logging change"""
    from qwenex.mcp.tools.wal import wal_log_change
    
    result = await wal_log_change("code", "Added feature")
    
    assert "Logged" in result
    assert "code" in result
