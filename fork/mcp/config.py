"""Конфигурация MCP-сервера: пути и настройки."""

from pathlib import Path

# Корень проекта — относительно этого файла
PROJECT_ROOT = Path(__file__).parent.parent

# Основные пути
WAL_PATH = PROJECT_ROOT / "WAL.md"
SESSIONS_DIR = PROJECT_ROOT / "docs" / "sessions"
REVIEWS_DIR = PROJECT_ROOT / "docs" / "reviews"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
WEB_DIR = PROJECT_ROOT / "web"
TESTS_DIR = PROJECT_ROOT / "tests"
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"

# Настройки
DEFAULT_TEST_TIMEOUT = 120  # секунд
DEFAULT_BUILD_TIMEOUT = 180  # секунд
MAX_ERRORS_RETURNED = 20  # максимум ошибок в ответе
