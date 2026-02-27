"""WAL tools for MCP server."""

import re
from pathlib import Path
from datetime import datetime
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
    try:
        if not WAL_PATH.exists():
            WAL_PATH.parent.mkdir(parents=True, exist_ok=True)
            WAL_PATH.write_text("# WAL\n\nСессия: S-001", encoding="utf-8")
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
    except (IOError, OSError) as e:
        return f"Error: Failed to access WAL.md — {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error — {str(e)}"


@mcp.tool()
async def wal_get_current_task() -> dict:
    """
    Получить текущую задачу из WAL.

    Returns:
        task: dict with id, title, status
    """
    try:
        if not WAL_PATH.exists():
            return {"error": "WAL.md not found"}

        content = WAL_PATH.read_text(encoding="utf-8")

        # Parse current task section
        match = re.search(
            r"\*\*\[([A-Z]+-\d+|DOC-\d+): ([^\]]+)\]\*\* — (.+?)(?:·|$)",
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
    except (IOError, OSError) as e:
        return {"error": f"Failed to read WAL.md — {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error — {str(e)}"}


@mcp.tool()
async def wal_list_tasks(status: str = "all") -> list:
    """
    Список задач по статусу.

    Args:
        status: "all", "completed", "pending", "current"

    Returns:
        tasks: list of task dicts
    """
    try:
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
    except (IOError, OSError) as e:
        return [{"error": f"Failed to read WAL.md — {str(e)}"}]
    except Exception as e:
        return [{"error": f"Unexpected error — {str(e)}"}]


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
    try:
        if not WAL_PATH.exists():
            return "Error: WAL.md not found"

        content = WAL_PATH.read_text(encoding="utf-8")

        # Add to completed section
        today = datetime.now().strftime("%Y-%m-%d")
        completed_marker = "## ✅ Завершено"

        if completed_marker in content:
            new_entry = f"\n- [x] **[{task_id}]** — {notes} · {today}"
            content = content.replace(completed_marker, completed_marker + new_entry)

        WAL_PATH.write_text(content, encoding="utf-8")

        return f"Task {task_id} marked as completed"
    except (IOError, OSError) as e:
        return f"Error: Failed to update WAL.md — {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error — {str(e)}"


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
