"""Точка входа для запуска через python -m mcp."""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())
