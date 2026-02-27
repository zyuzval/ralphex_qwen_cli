# MAJOR-ISSUES-FIX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Исправить 8 Major issues из code review для повышения качества кода.

**Architecture:** Последовательное исправление: error handling → type hints → review marker parsing → constants → docstrings → async consistency → placeholder implementations → input validation.

**Tech Stack:** Python 3.11+ · typing · pytest · logging

---

### Task 1: Error handling в MCP tools

**Files:**
- Modify: `src/qwenex/mcp/tools/wal.py:15-50`
- Modify: `src/qwenex/mcp/tools/config.py:20-60`
- Test: `src/tests/test_mcp_wal_tools.py` (update)

**Step 1: Add error handling to wal_start_session**

```python
# src/qwenex/mcp/tools/wal.py
@mcp.tool()
async def wal_start_session() -> str:
    """Start a new WAL session.
    
    Returns:
        Session ID (e.g., "S-001")
    """
    try:
        if not WAL_PATH.exists():
            WAL_PATH.parent.mkdir(parents=True, exist_ok=True)
            WAL_PATH.write_text("# WAL\n\nСессия: S-001", encoding="utf-8")
            return "S-001"
        
        content = WAL_PATH.read_text(encoding="utf-8")
        # ... rest of implementation
    except (IOError, OSError) as e:
        return f"Error: Failed to access WAL.md — {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error — {str(e)}"
```

**Step 2: Add error handling to config tools**

```python
# src/qwenex/mcp/tools/config.py
VALID_KEYS = {"auto_mode", "timeout", "max_iterations", "model", "provider"}

@mcp.tool()
async def config_set(key: str, value) -> str:
    """Set configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
        
    Returns:
        Success or error message
    """
    if key not in VALID_KEYS:
        return f"Error: Invalid key '{key}'. Valid keys: {VALID_KEYS}"
    
    try:
        config = load_config()
        # ... set value
        save_config(config)
        return f"Config set: {key}={value}"
    except Exception as e:
        return f"Error: Failed to set config — {str(e)}"
```

**Step 3: Run tests**

Run: `cd qwenex && pytest src/tests/test_mcp_wal_tools.py src/tests/test_mcp_config_tools.py -v --no-cov`
Expected: PASS

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/mcp/tools/wal.py src/qwenex/mcp/tools/config.py
git commit -m "fix: add error handling to MCP tools

- wal_start_session: IOError/OSError handling
- config_set: input validation and error handling
- Return descriptive error messages
- Tests: updated"
```

---

### Task 2: Complete type hints

**Files:**
- Modify: `src/qwenex/orchestrator.py`
- Modify: `src/qwenex/progress.py`
- Modify: `src/qwenex/mcp/tools/*.py`

**Step 1: Add return types to orchestrator**

```python
# src/qwenex/orchestrator.py
def _extract_review_markers(self, output: str) -> List[str]:  # Already has it ✓
    ...

def _build_task_prompt(self, task: Task) -> str:  # Already has it ✓
    ...

async def _execute_task_with_retry(
    self,
    task: Task,
) -> OrchestratorResult:  # Already has it ✓
    ...
```

**Step 2: Add callback type to progress.py**

```python
# src/qwenex/progress.py
from typing import Callable, Awaitable, Any, Dict

@dataclass
class ProgressTracker:
    plan_file: str
    progress_dir: str = ".qwenex/progress"
    events: List[ProgressEvent] = field(default_factory=list)
    callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None
```

**Step 3: Add return types to MCP tools**

```python
# src/qwenex/mcp/tools/wal.py
@mcp.tool()
async def wal_start_session() -> str:
    ...

@mcp.tool()
async def wal_get_current_task() -> str:
    ...

@mcp.tool()
async def wal_list_tasks(status: Optional[str] = None) -> str:
    ...
```

**Step 4: Run mypy**

Run: `cd qwenex && mypy src/qwenex --ignore-missing-imports`
Expected: No errors (or minimal)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/orchestrator.py src/qwenex/progress.py src/qwenex/mcp/tools/
git commit -m "fix: add complete type hints

- Add return types to all public functions
- Add callback type annotation in ProgressTracker
- MCP tools have explicit return types
- mypy: passing"
```

---

### Task 3: Review marker bilingual parsing

**Files:**
- Modify: `src/qwenex/review/models.py:42-52`
- Test: `src/tests/test_review_models.py`

**Step 1: Update regex pattern**

```python
# src/qwenex/review/models.py
@dataclass
class ReviewMarker:
    """Review marker from AI output."""
    comment: str
    reason: str
    awaits: str
    critical: bool = False
    
    @classmethod
    def parse_from_output(cls, output: str) -> List['ReviewMarker']:
        """Parse review markers from output.
        
        Supports both Russian and English formats:
        - Russian: <!-- REVIEW: comment — причина: reason — ждёт: awaits -->
        - English: <!-- REVIEW: comment - reason: reason - awaits: awaits -->
        """
        pattern = r'<!--\s*REVIEW:\s*(.+?)\s*[-—]\s*(?:причина|reason):\s*(.+?)\s*[-—]\s*(?:ждёт|awaits):\s*(.+?)\s*-->'
        
        markers = []
        for match in re.finditer(pattern, output, re.IGNORECASE):
            markers.append(cls(
                comment=match.group(1).strip(),
                reason=match.group(2).strip(),
                awaits=match.group(3).strip(),
                critical=False
            ))
        
        return markers
```

**Step 2: Add tests for bilingual parsing**

```python
# src/tests/test_review_models.py
def test_review_marker_parse_russian():
    """Test Russian format parsing."""
    output = "<!-- REVIEW: Fix bug — причина: Security issue — ждёт: Confirmation -->"
    markers = ReviewMarker.parse_from_output(output)
    assert len(markers) == 1
    assert markers[0].comment == "Fix bug"
    assert markers[0].reason == "Security issue"


def test_review_marker_parse_english():
    """Test English format parsing."""
    output = "<!-- REVIEW: Fix bug - reason: Security issue - awaits: Confirmation -->"
    markers = ReviewMarker.parse_from_output(output)
    assert len(markers) == 1
    assert markers[0].comment == "Fix bug"
    assert markers[0].reason == "Security issue"


def test_review_marker_parse_mixed():
    """Test mixed language parsing."""
    output = """
    <!-- REVIEW: Fix A — причина: Reason A — ждёт: Awaits A -->
    <!-- REVIEW: Fix B - reason: Reason B - awaits: Awaits B -->
    """
    markers = ReviewMarker.parse_from_output(output)
    assert len(markers) == 2
```

**Step 3: Run tests**

Run: `cd qwenex && pytest src/tests/test_review_models.py::test_review_marker_parse_russian -v --no-cov`
Run: `cd qwenex && pytest src/tests/test_review_models.py::test_review_marker_parse_english -v --no-cov`
Run: `cd qwenex && pytest src/tests/test_review_models.py::test_review_marker_parse_mixed -v --no-cov`
Expected: All PASS

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/review/models.py src/tests/test_review_models.py
git commit -m "fix: support bilingual review markers

- Parse both Russian and English formats
- Regex: (причина|reason), (ждёт|awaits)
- Case-insensitive matching
- Tests: 3 new tests passing"
```

---

### Task 4: Constants for magic numbers

**Files:**
- Create: `src/qwenex/constants.py`
- Modify: `src/qwenex/orchestrator.py`
- Modify: `src/qwenex/review/hybrid_executor.py`
- Modify: `src/qwenex/qwen_executor.py`

**Step 1: Create constants module**

```python
# src/qwenex/constants.py
"""Default values and constants for Qwenex."""

# Timeouts (in minutes)
TASK_TIMEOUT_MIN: int = 10
REVIEW_TIMEOUT_MIN: int = 5
HEALTH_CHECK_TIMEOUT_SEC: int = 10

# Retry settings
MAX_ITERATIONS: int = 3
MAX_RETRIES: int = 2

# Review settings
REVIEW_ITERATIONS: int = 3

# Paths
DEFAULT_SPECS_DIR: str = "specs"
DEFAULT_PROGRESS_DIR: str = ".qwenex/progress"
DEFAULT_CONFIG_DIR: str = ".qwenex"
```

**Step 2: Update orchestrator.py**

```python
# src/qwenex/orchestrator.py
from .constants import MAX_ITERATIONS, TASK_TIMEOUT_MIN

class Orchestrator:
    def __init__(
        self,
        plan: Plan,
        provider: Optional[LLMProvider] = None,
        provider_config: Optional[ProviderConfig] = None,
        max_iterations: int = MAX_ITERATIONS,  # Use constant
        timeout_min: int = TASK_TIMEOUT_MIN,  # Use constant
        auto_mode: bool = False,
        enable_web: bool = False,
    ):
        ...
```

**Step 3: Update hybrid_executor.py**

```python
# src/qwenex/review/hybrid_executor.py
from ..constants import REVIEW_TIMEOUT_MIN, REVIEW_ITERATIONS

class HybridExecutor:
    def __init__(
        self,
        timeout_min: int = REVIEW_TIMEOUT_MIN,  # Use constant
        max_iterations: int = REVIEW_ITERATIONS,  # Use constant
    ):
        self.timeout_min = timeout_min
        self.max_iterations = max_iterations
```

**Step 4: Update qwen_executor.py**

```python
# src/qwenex/qwen_executor.py
from .constants import TASK_TIMEOUT_MIN

class QwenExecutor:
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        provider_config: Optional[ProviderConfig] = None,
        timeout_min: int = TASK_TIMEOUT_MIN,  # Use constant
    ):
        self.timeout_min = timeout_min
```

**Step 5: Run tests**

Run: `cd qwenex && pytest src/tests/test_orchestrator.py src/tests/test_hybrid_executor.py -v --no-cov`
Expected: PASS

**Step 6: Commit**

```bash
cd qwenex
git add src/qwenex/constants.py src/qwenex/orchestrator.py src/qwenex/review/hybrid_executor.py src/qwenex/qwen_executor.py
git commit -m "fix: extract magic numbers to constants

- Create constants.py with default values
- TASK_TIMEOUT_MIN, REVIEW_TIMEOUT_MIN
- MAX_ITERATIONS, MAX_RETRIES
- Update orchestrator, hybrid_executor, qwen_executor
- Tests: passing"
```

---

### Task 5: Missing docstrings

**Files:**
- Modify: `src/qwenex/mcp/tools/*.py`
- Modify: `src/qwenex/web/broadcast.py`
- Modify: `src/qwenex/spec_registry.py`

**Step 1: Add module docstrings**

```python
# src/qwenex/spec_registry.py
"""Specification registry for auto-numbering.

This module provides functionality to track existing FEAT/PROP
specifications and generate the next available number.
"""
```

**Step 2: Add class docstrings**

```python
# src/qwenex/web/broadcast.py
class BroadcastService:
    """Service for broadcasting progress updates to WebSocket clients.
    
    This is a singleton class that manages WebSocket connections
    and broadcasts progress updates in real-time during plan execution.
    
    Attributes:
        clients: List of connected WebSocket clients
        current_update: Current progress update being broadcast
    """
```

**Step 3: Add method docstrings to MCP tools**

```python
# src/qwenex/mcp/tools/wal.py
@mcp.tool()
async def wal_start_session() -> str:
    """Start a new WAL session.
    
    Creates a new session in WAL.md or returns existing session ID.
    
    Returns:
        Session ID (e.g., "S-001") or error message
        
    Raises:
        IOError: If WAL.md cannot be accessed
    """
```

**Step 4: Run docstring checker (optional)**

Run: `cd qwenex && python -m pydocstyle src/qwenex`
Expected: Minimal warnings

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/spec_registry.py src/qwenex/web/broadcast.py src/qwenex/mcp/tools/
git commit -m "docs: add missing docstrings

- Module docstrings for spec_registry
- Class docstrings for BroadcastService
- Method docstrings for MCP tools
- Google style format"
```

---

### Task 6: Async consistency in progress.py

**Files:**
- Modify: `src/qwenex/progress.py`
- Test: `src/tests/test_progress.py`

**Step 1: Make all methods async**

```python
# src/qwenex/progress.py
async def validation_started(self, commands: List[str]) -> None:
    """Log validation start.
    
    Args:
        commands: Validation commands
    """
    cmds = ", ".join(commands) if commands else "none"
    self.log(f"Running validation: {cmds}")
    await self._notify("validation_started", {"commands": commands})

async def validation_passed(self) -> None:
    """Log validation success."""
    self.log("Validation passed")
    await self._notify("validation_passed", {})

async def validation_failed(self, reason: str) -> None:
    """Log validation failure.
    
    Args:
        reason: Failure reason
    """
    self.log(f"Validation failed: {reason}")
    await self._notify("validation_failed", {"reason": reason})

async def git_committed(self, message: str) -> None:
    """Log git commit.
    
    Args:
        message: Commit message
    """
    self.log(f"Committed: {message}")
    await self._notify("git_committed", {"message": message})

async def save(self) -> None:
    """Save progress to file."""
    self._get_progress_path().parent.mkdir(parents=True, exist_ok=True)
    with open(self._get_progress_path(), 'w', encoding='utf-8') as f:
        for event in self.events:
            f.write(f"{event}\n")
```

**Step 2: Update orchestrator to await async methods**

```python
# src/qwenex/orchestrator.py
# Update calls to progress methods
await self.progress.validation_started(self.plan.validation_commands)
await self.progress.validation_passed()
await self.progress.git_committed(commit_msg)
```

**Step 3: Run tests**

Run: `cd qwenex && pytest src/tests/test_progress.py -v --no-cov`
Expected: PASS

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/progress.py src/qwenex/orchestrator.py
git commit -m "fix: make all ProgressTracker methods async

- validation_started, validation_passed, validation_failed
- git_committed, save
- Consistent async API
- Update orchestrator calls
- Tests: passing"
```

---

### Task 7: Placeholder implementations

**Files:**
- Modify: `src/qwenex/mcp/tools/review.py`
- Modify: `src/qwenex/git_wrapper.py`

**Step 1: Implement save_review_report**

```python
# src/qwenex/mcp/tools/review.py
@mcp.tool()
async def save_review_report(session_id: str, report: str) -> str:
    """Save review report to file.
    
    Args:
        session_id: Review session ID
        report: Review report markdown
        
    Returns:
        Success or error message
    """
    try:
        reviews_dir = Path(".qwenex/reviews")
        reviews_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = reviews_dir / f"{session_id}.md"
        report_path.write_text(report, encoding="utf-8")
        
        return f"Review saved to {report_path}"
    except (IOError, OSError) as e:
        return f"Error: Failed to save review — {str(e)}"
```

**Step 2: Implement load_review_report**

```python
# src/qwenex/mcp/tools/review.py
@mcp.tool()
async def load_review_report(session_id: str) -> str:
    """Load review report from file.
    
    Args:
        session_id: Review session ID
        
    Returns:
        Review report markdown or error message
    """
    try:
        report_path = Path(f".qwenex/reviews/{session_id}.md")
        
        if not report_path.exists():
            return f"Error: Review not found for session {session_id}"
        
        return report_path.read_text(encoding="utf-8")
    except (IOError, OSError) as e:
        return f"Error: Failed to load review — {str(e)}"
```

**Step 3: Implement apply_marker_fix**

```python
# src/qwenex/mcp/tools/review.py
@mcp.tool()
async def apply_marker_fix(file_path: str, line_number: int, fix: str) -> str:
    """Apply a review marker fix to a file.
    
    Args:
        file_path: Path to file
        line_number: Line number to fix
        fix: Fix suggestion
        
    Returns:
        Success or error message
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return f"Error: File not found: {file_path}"
        
        lines = path.read_text(encoding="utf-8").splitlines()
        
        if line_number < 1 or line_number > len(lines):
            return f"Error: Invalid line number: {line_number}"
        
        # Insert fix as comment before the line
        lines.insert(line_number - 1, f"# FIXME: {fix}")
        
        path.write_text("\n".join(lines), encoding="utf-8")
        
        return f"Fix applied to {file_path}:{line_number}"
    except (IOError, OSError) as e:
        return f"Error: Failed to apply fix — {str(e)}"
```

**Step 4: Run tests**

Run: `cd qwenex && pytest src/tests/test_mcp_review_tools.py -v --no-cov`
Expected: PASS (or create tests if missing)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/mcp/tools/review.py
git commit -m "feat: implement placeholder MCP review tools

- save_review_report: Save to .qwenex/reviews/
- load_review_report: Load from file
- apply_marker_fix: Insert FIXME comments
- Error handling for all methods"
```

---

### Task 8: Input validation

**Files:**
- Modify: `src/qwenex/mcp/tools/config.py`
- Modify: `src/qwenex/transformer/transformer.py`
- Modify: `src/qwenex/orchestrator.py`

**Step 1: Validate config keys**

```python
# src/qwenex/mcp/tools/config.py
VALID_KEYS = {
    "auto_mode": bool,
    "timeout": int,
    "max_iterations": int,
    "model": str,
    "provider": str,
}

@mcp.tool()
async def config_set(key: str, value) -> str:
    """Set configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
        
    Returns:
        Success or error message
    """
    if key not in VALID_KEYS:
        return f"Error: Invalid key '{key}'. Valid keys: {set(VALID_KEYS.keys())}"
    
    # Type validation
    expected_type = VALID_KEYS[key]
    if not isinstance(value, expected_type):
        return f"Error: Invalid type for '{key}'. Expected {expected_type.__name__}, got {type(value).__name__}"
    
    try:
        config = load_config()
        # ... set value
        save_config(config)
        return f"Config set: {key}={value}"
    except Exception as e:
        return f"Error: Failed to set config — {str(e)}"
```

**Step 2: Validate spec_type in transformer**

```python
# src/qwenex/transformer/transformer.py
VALID_SPEC_TYPES = {"FEAT", "PROP"}

async def transform(
    self,
    simple_plan: str,
    spec_number: str,
    spec_type: str = "FEAT",
    module: str = "module",
    **kwargs: Any
) -> str:
    """Transform simple plan to specification.
    
    Args:
        simple_plan: Simple markdown plan
        spec_number: Specification number
        spec_type: Type of specification (FEAT or PROP)
        module: Module name for URI
        **kwargs: Additional template variables
        
    Returns:
        Generated specification markdown
        
    Raises:
        TransformError: If transformation fails
    """
    if spec_type not in VALID_SPEC_TYPES:
        raise TransformError(
            f"Invalid spec_type '{spec_type}'. Must be one of: {VALID_SPEC_TYPES}"
        )
    
    # ... rest of implementation
```

**Step 3: Validate plan in orchestrator**

```python
# src/qwenex/orchestrator.py
def __init__(
    self,
    plan: Plan,
    ...
):
    if not plan.tasks:
        raise ValueError("Plan must have at least one task")
    
    if not plan.validation_commands:
        # Log warning but continue
        print("Warning: Plan has no validation commands")
    
    # ... rest of init
```

**Step 4: Run tests**

Run: `cd qwenex && pytest src/tests/test_mcp_config_tools.py -v --no-cov`
Expected: PASS

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/mcp/tools/config.py src/qwenex/transformer/transformer.py src/qwenex/orchestrator.py
git commit -m "fix: add input validation

- config_set: Validate keys and types
- transform: Validate spec_type (FEAT/PROP)
- Orchestrator: Validate plan has tasks
- Return descriptive error messages"
```

---

## Завершение плана

**Проверка качества:**

```bash
cd qwenex
# Run all tests
pytest -v

# Run mypy
mypy src/qwenex --ignore-missing-imports

# Run ruff
ruff check src/qwenex
```

Expected: All tests pass, minimal mypy warnings, no ruff errors

---

## Итоговый список коммитов

1. `fix: add error handling to MCP tools`
2. `fix: add complete type hints`
3. `fix: support bilingual review markers`
4. `fix: extract magic numbers to constants`
5. `docs: add missing docstrings`
6. `fix: make all ProgressTracker methods async`
7. `feat: implement placeholder MCP review tools`
8. `fix: add input validation`

**Всего:** 8 коммитов

---

План готов и сохранён в `docs/plans/2026-02-27-major-issues-fix.md`.

**Два варианта выполнения:**

**1. Subagent-Driven (эта сессия)** — Запускаю свежего субагента на каждую задачу, code review между задачами

**2. Параллельная сессия (отдельная)** — Открыть новую сессию с `superpowers:executing-plans`

**Какой подход выбираешь?**
