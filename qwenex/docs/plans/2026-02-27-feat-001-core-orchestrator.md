# FEAT-001: Ядро оркестратора Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Реализовать базовую оркестрацию задач через Qwen CLI: чтение плана, выполнение задач, валидация, прогресс-трекинг.

**Architecture:** 7 компонентов (cli.py, orchestrator.py, plan_parser.py, qwen_executor.py, validator.py, progress.py, git_wrapper.py) с TDD подходом, покрытие 80%+.

**Tech Stack:** Python 3.11+, pytest, pytest-asyncio, subprocess (Qwen CLI, git), stream-json парсинг.

---

## Предварительные задачи

### Task 0: Настройка проекта

**Files:**
- Create: `src/qwenex/__init__.py`
- Create: `src/tests/__init__.py`
- Create: `pyproject.toml`
- Create: `pytest.ini`
- Create: `.gitignore` (дополнения)

**Step 1: Создать pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "qwenex"
version = "0.1.0"
description = "Autonomous plan execution with Qwen CLI"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Qwenex Team"}
]
dependencies = [
    "fastmcp>=0.1.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
]

[project.scripts]
qwenex = "qwenex.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["src/tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --cov=src/qwenex --cov-report=term-missing --cov-fail-under=80"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "N", "D", "UP"]
```

**Step 2: Создать pytest.ini**

```ini
[pytest]
asyncio_mode = auto
testpaths = src/tests
python_files = test_*.py
python_functions = test_*
addopts = -v --cov=src/qwenex --cov-report=term-missing --cov-fail-under=80
```

**Step 3: Создать __init__.py файлы**

```python
# src/qwenex/__init__.py
"""Qwenex - Autonomous plan execution with Qwen CLI."""

__version__ = "0.1.0"

# src/tests/__init__.py
"""Tests for Qwenex."""
```

**Step 4: Обновить .gitignore**

Добавить в конец:
```
# Qwenex
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
.qwenex/
```

**Step 5: Установить зависимости**

Run: `pip install -e ".[dev]"`
Expected: Успешная установка в editable режиме

**Step 6: Запустить пустой тест для проверки настройки**

Run: `pytest --collect-only`
Expected: Список тестов (пока пусто)

**Step 7: Commit**

```bash
git add qwenex/src/qwenex/__init__.py qwenex/src/tests/__init__.py qwenex/pyproject.toml qwenex/pytest.ini qwenex/.gitignore
git commit -m "feat(FEAT-001): настройка проекта (pyproject, pytest, mypy, ruff)"
```

---

## Компонент 1: Plan Parser

### Task 1: Модели данных плана

**Files:**
- Create: `src/qwenex/models.py`
- Test: `src/tests/test_plan_parser.py`

**Step 1: Write the failing test**

```python
# src/tests/test_plan_parser.py
import pytest
from qwenex.models import Plan, Task, Checkbox


def test_checkbox_creation():
    checkbox = Checkbox(text="Add feature", completed=False)
    assert checkbox.text == "Add feature"
    assert checkbox.completed == False
    assert checkbox.markdown == "- [ ] Add feature"


def test_checkbox_completed_markdown():
    checkbox = Checkbox(text="Done", completed=True)
    assert checkbox.markdown == "- [x] Done"


def test_task_creation():
    task = Task(
        number="1",
        title="Implement feature",
        checkboxes=[
            Checkbox(text="Add code", completed=False),
            Checkbox(text="Add tests", completed=True),
        ]
    )
    assert task.number == "1"
    assert task.title == "Implement feature"
    assert len(task.checkboxes) == 2
    assert task.incomplete_count == 1


def test_plan_creation():
    plan = Plan(
        title="My Feature",
        file_path="docs/plans/feature.md",
        validation_commands=["pytest", "ruff check"],
        tasks=[
            Task(
                number="1",
                title="Implement",
                checkboxes=[Checkbox(text="Code", completed=False)]
            )
        ]
    )
    assert plan.title == "My Feature"
    assert plan.file_path == "docs/plans/feature.md"
    assert len(plan.validation_commands) == 2
    assert plan.current_task_index == 0
    assert plan.is_complete == False
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_plan_parser.py::test_checkbox_creation -v`
Expected: FAIL с "ModuleNotFoundError: No module named 'qwenex.models'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/models.py
"""Models for Qwenex."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Checkbox:
    """Checkbox in a task."""
    text: str
    completed: bool = False

    @property
    def markdown(self) -> str:
        """Return markdown representation."""
        marker = "x" if self.completed else " "
        return f"- [{marker}] {self.text}"


@dataclass
class Task:
    """Task in a plan."""
    number: str
    title: str
    checkboxes: List[Checkbox] = field(default_factory=list)

    @property
    def incomplete_count(self) -> int:
        """Count incomplete checkboxes."""
        return sum(1 for cb in self.checkboxes if not cb.completed)

    @property
    def is_complete(self) -> bool:
        """Check if all checkboxes are complete."""
        return self.incomplete_count == 0


@dataclass
class Plan:
    """Plan file."""
    title: str
    file_path: str
    validation_commands: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    current_task_index: int = 0

    @property
    def current_task(self) -> Task | None:
        """Get current task or None if complete."""
        if self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all tasks are complete."""
        return self.current_task_index >= len(self.tasks)

    def next_task(self) -> None:
        """Move to next task."""
        self.current_task_index += 1
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_plan_parser.py::test_checkbox_creation -v`
Expected: PASS

**Step 5: Run all model tests**

Run: `pytest src/tests/test_plan_parser.py -v`
Expected: PASS (4 теста)

**Step 6: Commit**

```bash
git add src/qwenex/models.py src/tests/test_plan_parser.py
git commit -m "feat(FEAT-001.1): модели данных (Plan, Task, Checkbox)"
```

---

### Task 2: Парсинг markdown плана

**Files:**
- Modify: `src/qwenex/models.py` (добавить classmethod from_markdown)
- Create: `src/qwenex/plan_parser.py`
- Test: `src/tests/test_plan_parser.py` (добавить тесты)

**Step 1: Write the failing test**

```python
# src/tests/test_plan_parser.py (добавить)
from qwenex.plan_parser import parse_plan


def test_parse_plan_simple():
    markdown = """# Plan: My Feature

## Validation Commands
- pytest
- ruff check

### Task 1: Implement feature
- [ ] Add code
- [ ] Add tests
- [x] Done
"""
    plan = parse_plan(markdown, "docs/plans/feature.md")
    
    assert plan.title == "My Feature"
    assert plan.file_path == "docs/plans/feature.md"
    assert plan.validation_commands == ["pytest", "ruff check"]
    assert len(plan.tasks) == 1
    assert plan.tasks[0].number == "1"
    assert plan.tasks[0].title == "Implement feature"
    assert len(plan.tasks[0].checkboxes) == 3
    assert plan.tasks[0].checkboxes[0].completed == False
    assert plan.tasks[0].checkboxes[1].completed == False
    assert plan.tasks[0].checkboxes[2].completed == True


def test_parse_plan_multiple_tasks():
    markdown = """# Plan: Big Feature

## Validation Commands
- pytest

### Task 1: First part
- [ ] Code part 1

### Task 2: Second part
- [ ] Code part 2
"""
    plan = parse_plan(markdown, "docs/plans/big.md")
    
    assert plan.title == "Big Feature"
    assert len(plan.tasks) == 2
    assert plan.tasks[0].number == "1"
    assert plan.tasks[1].number == "2"


def test_parse_plan_no_validation():
    markdown = """# Plan: Simple

### Task 1: Do something
- [ ] Do it
"""
    plan = parse_plan(markdown, "docs/plans/simple.md")
    
    assert plan.validation_commands == []
    assert len(plan.tasks) == 1


def test_parse_plan_non_integer_task_numbers():
    """Support task numbers like 2.5, 2a, etc."""
    markdown = """# Plan: Complex

### Task 1: First
- [ ] Code

### Task 2.5: Middle
- [ ] Code

### Task 3: Last
- [ ] Code
"""
    plan = parse_plan(markdown, "docs/plans/complex.md")
    
    assert len(plan.tasks) == 3
    assert plan.tasks[0].number == "1"
    assert plan.tasks[1].number == "2.5"
    assert plan.tasks[2].number == "3"
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_plan_parser.py::test_parse_plan_simple -v`
Expected: FAIL с "ModuleNotFoundError: No module named 'qwenex.plan_parser'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/plan_parser.py
"""Parse markdown plan files."""

import re
from typing import List

from .models import Plan, Task, Checkbox


def parse_plan(markdown: str, file_path: str) -> Plan:
    """Parse a markdown plan file.
    
    Args:
        markdown: Markdown content
        file_path: Path to the plan file
        
    Returns:
        Parsed Plan object
    """
    lines = markdown.split('\n')
    
    # Parse title
    title = ""
    for line in lines:
        if line.startswith('# '):
            title = line[2:].replace('Plan:', '').strip()
            break
    
    # Parse validation commands
    validation_commands: List[str] = []
    in_validation = False
    for line in lines:
        if line.startswith('## Validation Commands'):
            in_validation = True
            continue
        if in_validation:
            if line.startswith('### '):
                break
            if line.startswith('- '):
                cmd = line[2:].strip()
                if cmd:
                    validation_commands.append(cmd)
    
    # Parse tasks
    tasks: List[Task] = []
    current_task: Task | None = None
    
    task_pattern = re.compile(r'^### Task\s+([^\s:]+):\s*(.+)$')
    checkbox_pattern = re.compile(r'^-\s+\[([ x])\]\s+(.+)$')
    
    for line in lines:
        # Skip validation section
        if line.startswith('## Validation Commands'):
            continue
        if in_validation and line.startswith('### '):
            in_validation = False
        
        # Check for task header
        task_match = task_pattern.match(line)
        if task_match:
            # Save previous task
            if current_task:
                tasks.append(current_task)
            
            # Start new task
            current_task = Task(
                number=task_match.group(1),
                title=task_match.group(2).strip()
            )
            continue
        
        # Check for checkbox
        if current_task:
            checkbox_match = checkbox_pattern.match(line)
            if checkbox_match:
                completed = checkbox_match.group(1) == 'x'
                text = checkbox_match.group(2)
                current_task.checkboxes.append(
                    Checkbox(text=text, completed=completed)
                )
    
    # Don't forget last task
    if current_task:
        tasks.append(current_task)
    
    return Plan(
        title=title,
        file_path=file_path,
        validation_commands=validation_commands,
        tasks=tasks
    )


def parse_plan_file(file_path: str) -> Plan:
    """Parse a plan file from disk.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Parsed Plan object
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        markdown = f.read()
    return parse_plan(markdown, file_path)
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_plan_parser.py -v`
Expected: PASS (8 тестов)

**Step 5: Commit**

```bash
git add src/qwenex/plan_parser.py src/qwenex/models.py src/tests/test_plan_parser.py
git commit -m "feat(FEAT-001.2): парсинг markdown плана"
```

---

## Компонент 2: Qwen Executor

### Task 3: Запуск Qwen CLI с stream-json

**Files:**
- Create: `src/qwenex/qwen_executor.py`
- Test: `src/tests/test_qwen_executor.py`

**Step 1: Write the failing test**

```python
# src/tests/test_qwen_executor.py
import pytest
from qwenex.qwen_executor import QwenExecutor, TaskTimeoutError


@pytest.mark.asyncio
async def test_run_task_basic():
    """Test basic task execution."""
    executor = QwenExecutor()
    
    # Simple prompt that should complete quickly
    events = []
    async for event in executor.run_task("Say 'OK' in one word"):
        events.append(event)
    
    # Should have system, assistant, and result events
    assert len(events) >= 2
    assert any(e.get('type') == 'assistant' for e in events)
    assert any(e.get('type') == 'result' for e in events)


@pytest.mark.asyncio
async def test_run_task_timeout():
    """Test timeout handling."""
    executor = QwenExecutor(timeout_min=0.1)  # 6 seconds
    
    with pytest.raises(TaskTimeoutError):
        async for event in executor.run_task("Wait 10 seconds then say done"):
            pass


def test_parse_stream_json_line():
    """Test parsing a single stream-json line."""
    import json
    from qwenex.qwen_executor import parse_event
    
    line = '{"type":"assistant","message":{"content":[{"type":"text","text":"OK"}]}}'
    event = parse_event(line)
    
    assert event['type'] == 'assistant'
    assert event['message']['content'][0]['text'] == 'OK'
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_qwen_executor.py::test_parse_stream_json_line -v`
Expected: FAIL с "ModuleNotFoundError: No module named 'qwenex.qwen_executor'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/qwen_executor.py
"""Execute tasks using Qwen CLI."""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any


class TaskTimeoutError(Exception):
    """Raised when a task exceeds the timeout."""
    pass


def parse_event(line: str) -> Dict[str, Any]:
    """Parse a stream-json event line.
    
    Args:
        line: JSON line from Qwen CLI
        
    Returns:
        Parsed event dictionary
    """
    return json.loads(line.strip())


class QwenExecutor:
    """Execute tasks using Qwen CLI subprocess."""
    
    def __init__(self, timeout_min: int = 10):
        """Initialize executor.
        
        Args:
            timeout_min: Timeout in minutes for each task
        """
        self.timeout_min = timeout_min
    
    async def run_task(
        self,
        prompt: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run a task using Qwen CLI.
        
        Args:
            prompt: Task prompt to execute
            
        Yields:
            Stream-json events from Qwen CLI
            
        Raises:
            TaskTimeoutError: If task exceeds timeout
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "qwen",
                "-y",  # YOLO mode - auto-approve all actions
                "-o", "stream-json",
                "-p", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Read stdout line by line
            async def read_stream():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    yield line
                
            async for line in read_stream():
                try:
                    event = parse_event(line.decode('utf-8'))
                    yield event
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    # Skip malformed lines
                    continue
            
            # Wait for process to complete
            await process.wait()
            
        except asyncio.TimeoutError:
            if process:
                process.kill()
            raise TaskTimeoutError(
                f"Task exceeded {self.timeout_min} minutes timeout"
            )
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_qwen_executor.py -v`
Expected: PASS (тесты с реальным Qwen CLI могут требовать сеть)

**Примечание:** Тесты с реальным Qwen CLI требуют:
- Установленный qwen CLI
- Настроенные credentials
- Сетевое подключение

Для CI/CD добавить моки:

```python
# src/tests/test_qwen_executor.py (добавить)
@pytest.mark.asyncio
async def test_run_task_mocked(monkeypatch):
    """Test with mocked subprocess."""
    import subprocess
    
    # Mock subprocess to return fake events
    async def mock_create_subprocess_exec(*args, **kwargs):
        class MockProcess:
            stdout = asyncio.Queue()
            stderr = asyncio.Queue()
            
            async def readline(self):
                return b'{"type":"result","result":"OK"}'
            
            async def wait(self):
                pass
            
            def kill(self):
                pass
        
        return MockProcess()
    
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', mock_create_subprocess_exec)
    
    executor = QwenExecutor()
    events = []
    async for event in executor.run_task("test"):
        events.append(event)
    
    assert len(events) == 1
    assert events[0]['type'] == 'result'
```

**Step 5: Commit**

```bash
git add src/qwenex/qwen_executor.py src/tests/test_qwen_executor.py
git commit -m "feat(FEAT-001.3): Qwen CLI executor (stream-json)"
```

---

## Компонент 3: Validator

### Task 4: Валидация команд

**Files:**
- Create: `src/qwenex/validator.py`
- Test: `src/tests/test_validator.py`

**Step 1: Write the failing test**

```python
# src/tests/test_validator.py
import pytest
from qwenex.validator import Validator, ValidationResult


@pytest.mark.asyncio
async def test_validate_success():
    """Test successful validation."""
    validator = Validator()
    
    # Use a command that always succeeds
    result = await validator.run(["echo test"])
    
    assert result.success == True
    assert "test" in result.output


@pytest.mark.asyncio
async def test_validate_failure():
    """Test failed validation."""
    validator = Validator()
    
    # Use a command that always fails
    result = await validator.run(["exit 1"])
    
    assert result.success == False


@pytest.mark.asyncio
async def test_validate_multiple_commands():
    """Test multiple validation commands."""
    validator = Validator()
    
    result = await validator.run([
        "echo first",
        "echo second",
    ])
    
    assert result.success == True
    assert "first" in result.output
    assert "second" in result.output


def test_validation_result_str():
    """Test ValidationResult string representation."""
    result = ValidationResult(
        success=True,
        output="Test output",
        commands=["echo test"]
    )
    
    assert "PASS" in str(result)
    assert "Test output" in str(result)
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_validator.py::test_validate_success -v`
Expected: FAIL с "ModuleNotFoundError: No module named 'qwenex.validator'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/validator.py
"""Validate task results using shell commands."""

import asyncio
from dataclasses import dataclass
from typing import List


@dataclass
class ValidationResult:
    """Result of validation."""
    success: bool
    output: str
    commands: List[str]
    
    def __str__(self) -> str:
        status = "PASS" if self.success else "FAIL"
        return f"Validation {status}:\n{self.output}"


class Validator:
    """Run validation commands."""
    
    async def run(self, commands: List[str]) -> ValidationResult:
        """Run validation commands.
        
        Args:
            commands: List of shell commands to run
            
        Returns:
            ValidationResult with success status and output
        """
        if not commands:
            return ValidationResult(
                success=True,
                output="No validation commands",
                commands=[]
            )
        
        all_output = []
        all_success = True
        
        for cmd in commands:
            try:
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                
                stdout, _ = await process.communicate()
                output = stdout.decode('utf-8', errors='replace')
                all_output.append(f"$ {cmd}\n{output}")
                
                if process.returncode != 0:
                    all_success = False
                    
            except Exception as e:
                all_output.append(f"$ {cmd}\nError: {e}")
                all_success = False
        
        return ValidationResult(
            success=all_success,
            output="\n".join(all_output),
            commands=commands
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_validator.py -v`
Expected: PASS (4 теста)

**Step 5: Commit**

```bash
git add src/qwenex/validator.py src/tests/test_validator.py
git commit -m "feat(FEAT-001.4): валидация команд"
```

---

## Компонент 4: Git Wrapper

### Task 5: Git операции

**Files:**
- Create: `src/qwenex/git_wrapper.py`
- Test: `src/tests/test_git_wrapper.py`

**Step 1: Write the failing test**

```python
# src/tests/test_git_wrapper.py
import pytest
import tempfile
import os
from qwenex.git_wrapper import GitWrapper, GitError


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.system("git init >nul 2>&1")
        os.system("git config user.email 'test@test.com'")
        os.system("git config user.name 'Test User'")
        yield tmpdir
        os.chdir(os.path.dirname(tmpdir))


def test_git_status_clean(temp_git_repo):
    """Test git status on clean repo."""
    git = GitWrapper()
    status = git.status()
    
    assert status.is_clean == True
    assert status.branch == "master"  # or "main"


def test_git_status_dirty(temp_git_repo):
    """Test git status with uncommitted changes."""
    # Create a file
    with open("test.txt", "w") as f:
        f.write("test")
    
    git = GitWrapper()
    status = git.status()
    
    assert status.is_clean == False


def test_git_commit(temp_git_repo):
    """Test git commit."""
    # Create and stage a file
    with open("test.txt", "w") as f:
        f.write("test")
    os.system("git add test.txt")
    
    git = GitWrapper()
    git.commit("Test commit")
    
    status = git.status()
    assert status.is_clean == True


def test_git_create_worktree(temp_git_repo):
    """Test git worktree creation."""
    # Create a branch first
    os.system("git checkout -b test-branch >nul 2>&1")
    os.system("git checkout master >nul 2>&1")
    
    git = GitWrapper()
    worktree_path = os.path.join(temp_git_repo, "wt-test")
    
    git.create_worktree("test-branch", worktree_path)
    
    assert os.path.exists(worktree_path)
    assert os.path.isdir(worktree_path)


def test_ensure_git_ignored(temp_git_repo):
    """Test ensure_git_ignored pattern."""
    git = GitWrapper()
    
    # Add a pattern
    git.ensure_git_ignored(["*.tmp", ".cache/"])
    
    # Check .gitignore contains patterns
    with open(".gitignore", "r") as f:
        content = f.read()
    
    assert "*.tmp" in content
    assert ".cache/" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_git_wrapper.py::test_git_status_clean -v`
Expected: FAIL с "ModuleNotFoundError: No module named 'qwenex.git_wrapper'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/git_wrapper.py
"""Git operations wrapper using subprocess."""

import subprocess
from dataclasses import dataclass
from typing import List
from pathlib import Path


class GitError(Exception):
    """Git operation error."""
    pass


@dataclass
class GitStatus:
    """Git repository status."""
    is_clean: bool
    branch: str
    changed_files: List[str]


class GitWrapper:
    """Wrapper for git CLI operations."""
    
    def __init__(self, repo_path: str | None = None):
        """Initialize git wrapper.
        
        Args:
            repo_path: Path to git repository (default: current directory)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
    
    def _run(self, args: List[str]) -> str:
        """Run git command.
        
        Args:
            args: Git arguments (without 'git')
            
        Returns:
            Command output
            
        Raises:
            GitError: If git command fails
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise GitError(f"Git failed: {e.stderr}")
    
    def status(self) -> GitStatus:
        """Get repository status.
        
        Returns:
            GitStatus object
        """
        # Get current branch
        branch = self._run(["branch", "--show-current"])
        
        # Check for changes
        try:
            self._run(["diff", "--quiet"])
            self._run(["diff", "--cached", "--quiet"])
            is_clean = True
            changed_files = []
        except GitError:
            is_clean = False
            # Get list of changed files
            try:
                changed = self._run(["diff", "--name-only"])
                changed_files = changed.split('\n') if changed else []
            except GitError:
                changed_files = []
        
        return GitStatus(
            is_clean=is_clean,
            branch=branch,
            changed_files=changed_files
        )
    
    def commit(self, message: str) -> None:
        """Create a commit.
        
        Args:
            message: Commit message
        """
        self._run(["commit", "-m", message])
    
    def add(self, files: List[str]) -> None:
        """Stage files.
        
        Args:
            files: Files to stage
        """
        self._run(["add"] + files)
    
    def create_worktree(self, branch: str, path: str) -> None:
        """Create a git worktree.
        
        Args:
            branch: Branch name
            path: Path for worktree
        """
        self._run(["worktree", "add", "-b", branch, path])
    
    def remove_worktree(self, path: str) -> None:
        """Remove a git worktree.
        
        Args:
            path: Path to worktree
        """
        self._run(["worktree", "remove", "--force", path])
    
    def ensure_git_ignored(self, patterns: List[str]) -> None:
        """Add patterns to .gitignore and commit if clean.
        
        Args:
            patterns: Patterns to add to .gitignore
        """
        gitignore_path = self.repo_path / ".gitignore"
        
        # Read existing content
        existing = ""
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing = f.read()
        
        # Add new patterns
        new_patterns = "\n".join(patterns)
        updated = existing.rstrip() + "\n\n# Added by qwenex\n" + new_patterns + "\n"
        
        # Write back
        with open(gitignore_path, 'w') as f:
            f.write(updated)
        
        # Commit if was clean
        status = self.status()
        if status.is_clean:
            self.add([".gitignore"])
            self.commit("chore: update .gitignore (qwenex)")
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_git_wrapper.py -v`
Expected: PASS (5 тестов)

**Step 5: Commit**

```bash
git add src/qwenex/git_wrapper.py src/tests/test_git_wrapper.py
git commit -m "feat(FEAT-001.5): git wrapper (subprocess)"
```

---

## Компонент 5: Progress Tracker

### Task 6: Прогресс-трекинг

**Files:**
- Create: `src/qwenex/progress.py`
- Test: `src/tests/test_progress.py`

**Step 1: Write the failing test**

```python
# src/tests/test_progress.py
import pytest
import tempfile
import os
from datetime import datetime
from qwenex.progress import ProgressTracker


@pytest.fixture
def temp_progress_dir():
    """Create temporary progress directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_progress_tracker_init(temp_progress_dir):
    """Test progress tracker initialization."""
    tracker = ProgressTracker(
        plan_file="docs/plans/test.md",
        progress_dir=temp_progress_dir
    )
    
    assert tracker.plan_file == "docs/plans/test.md"
    assert tracker.progress_file.endswith("progress-test.txt")


def test_log_message(temp_progress_dir):
    """Test logging messages."""
    tracker = ProgressTracker(
        plan_file="docs/plans/test.md",
        progress_dir=temp_progress_dir
    )
    
    tracker.log("Started task 1")
    
    # Check file exists and contains message
    assert os.path.exists(tracker.progress_file)
    with open(tracker.progress_file, 'r') as f:
        content = f.read()
    
    assert "Started task 1" in content
    assert "[1" in content  # Timestamp


def test_save_and_load(temp_progress_dir):
    """Test save and load state."""
    tracker = ProgressTracker(
        plan_file="docs/plans/test.md",
        progress_dir=temp_progress_dir
    )
    
    tracker.current_task_index = 1
    tracker.iteration_count = 2
    tracker.save()
    
    # Load in new tracker
    tracker2 = ProgressTracker(
        plan_file="docs/plans/test.md",
        progress_dir=temp_progress_dir
    )
    tracker2.load()
    
    assert tracker2.current_task_index == 1
    assert tracker2.iteration_count == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_progress.py::test_progress_tracker_init -v`
Expected: FAIL с "ModuleNotFoundError: No module named 'qwenex.progress'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/progress.py
"""Progress tracking for Qwenex."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any
import json


class ProgressTracker:
    """Track progress of plan execution."""
    
    def __init__(
        self,
        plan_file: str,
        progress_dir: str | None = None,
    ):
        """Initialize progress tracker.
        
        Args:
            plan_file: Path to plan file
            progress_dir: Directory for progress files
        """
        self.plan_file = plan_file
        self.progress_dir = Path(progress_dir) if progress_dir else Path(".qwenex/progress")
        
        # Generate progress filename from plan filename
        plan_name = Path(plan_file).stem
        self.progress_file = self.progress_dir / f"progress-{plan_name}.txt"
        
        # State
        self.current_task_index = 0
        self.iteration_count = 0
        self.started_at: str | None = None
    
    def _ensure_dir(self) -> None:
        """Ensure progress directory exists."""
        self.progress_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str) -> None:
        """Log a message to progress file.
        
        Args:
            message: Message to log
        """
        self._ensure_dir()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        with open(self.progress_file, 'a', encoding='utf-8') as f:
            f.write(log_line)
    
    def save(self) -> None:
        """Save state to JSON file."""
        self._ensure_dir()
        
        state_file = self.progress_dir / f"state-{Path(self.plan_file).stem}.json"
        
        state = {
            "plan_file": self.plan_file,
            "current_task_index": self.current_task_index,
            "iteration_count": self.iteration_count,
            "started_at": self.started_at,
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    def load(self) -> None:
        """Load state from JSON file."""
        state_file = self.progress_dir / f"state-{Path(self.plan_file).stem}.json"
        
        if not state_file.exists():
            return
        
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        self.current_task_index = state.get("current_task_index", 0)
        self.iteration_count = state.get("iteration_count", 0)
        self.started_at = state.get("started_at")
    
    def start(self) -> None:
        """Start tracking."""
        self.started_at = datetime.now().isoformat()
        self._ensure_dir()
        
        # Write header
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            f.write(f"# Progress: {self.plan_file}\n")
            f.write(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        self.log("Started plan execution")
        self.save()
    
    def complete_task(self, task_number: str, task_title: str) -> None:
        """Mark task as complete.
        
        Args:
            task_number: Task number
            task_title: Task title
        """
        self.log(f"Completed task {task_number}: {task_title}")
        self.current_task_index += 1
        self.save()
    
    def task_failed(self, task_number: str, error: str) -> None:
        """Log task failure.
        
        Args:
            task_number: Task number
            error: Error message
        """
        self.log(f"Task {task_number} failed: {error}")
        self.save()
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_progress.py -v`
Expected: PASS (3 теста)

**Step 5: Commit**

```bash
git add src/qwenex/progress.py src/tests/test_progress.py
git commit -m "feat(FEAT-001.6): progress tracker"
```

---

## Компонент 6: Orchestrator

### Task 7: Оркестрация задач (Task Loop with Validation)

**Files:**
- Create: `src/qwenex/orchestrator.py`
- Test: `src/tests/test_orchestrator.py`

**Step 1: Write the failing test**

```python
# src/tests/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from qwenex.orchestrator import Orchestrator, MaxIterationsExceededError
from qwenex.models import Plan, Task, Checkbox


@pytest.fixture
def sample_plan():
    """Create a sample plan."""
    return Plan(
        title="Test Plan",
        file_path="docs/plans/test.md",
        validation_commands=["echo test"],
        tasks=[
            Task(
                number="1",
                title="Test task",
                checkboxes=[
                    Checkbox(text="Do something", completed=False),
                    Checkbox(text="Mark completed", completed=False),
                ]
            )
        ]
    )


@pytest.mark.asyncio
async def test_orchestrator_run_task(sample_plan, monkeypatch):
    """Test running a single task."""
    # Mock executor
    mock_executor = AsyncMock()
    mock_executor.run_task = AsyncMock(return_value=[
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Done"}]}}
    ])
    
    # Mock validator
    mock_validator = AsyncMock()
    mock_validator.run = AsyncMock(return_value=MagicMock(success=True, output="test"))
    
    # Mock progress
    mock_progress = MagicMock()
    
    orchestrator = Orchestrator(
        plan=sample_plan,
        executor=mock_executor,
        validator=mock_validator,
        progress=mock_progress,
    )
    
    result = await orchestrator.run_task(sample_plan.tasks[0])
    
    assert result.success == True
    assert result.iterations == 1


@pytest.mark.asyncio
async def test_orchestrator_retry_on_validation_failure(sample_plan, monkeypatch):
    """Test retry when validation fails."""
    call_count = 0
    
    async def mock_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return MagicMock(success=False, output="fail")
        return MagicMock(success=True, output="pass")
    
    mock_validator = AsyncMock()
    mock_validator.run = mock_run
    
    mock_executor = AsyncMock()
    mock_executor.run_task = AsyncMock(return_value=[])
    
    orchestrator = Orchestrator(
        plan=sample_plan,
        executor=mock_executor,
        validator=mock_validator,
        progress=MagicMock(),
    )
    
    result = await orchestrator.run_task(sample_plan.tasks[0])
    
    assert result.success == True
    assert result.iterations == 2  # Retried once


@pytest.mark.asyncio
async def test_orchestrator_max_iterations(sample_plan, monkeypatch):
    """Test max iterations exceeded."""
    mock_validator = AsyncMock()
    mock_validator.run = AsyncMock(return_value=MagicMock(success=False, output="fail"))
    
    mock_executor = AsyncMock()
    mock_executor.run_task = AsyncMock(return_value=[])
    
    orchestrator = Orchestrator(
        plan=sample_plan,
        executor=mock_executor,
        validator=mock_validator,
        progress=MagicMock(),
        max_iterations=2,
    )
    
    with pytest.raises(MaxIterationsExceededError):
        await orchestrator.run_task(sample_plan.tasks[0])
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_orchestrator.py::test_orchestrator_run_task -v`
Expected: FAIL с "ModuleNotFoundError: No module named 'qwenex.orchestrator'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/orchestrator.py
"""Orchestrate task execution with validation."""

from dataclasses import dataclass
from typing import List, Dict, Any

from .models import Plan, Task, Checkbox
from .qwen_executor import QwenExecutor
from .validator import Validator, ValidationResult
from .progress import ProgressTracker


class MaxIterationsExceededError(Exception):
    """Raised when max iterations is exceeded."""
    pass


@dataclass
class TaskResult:
    """Result of task execution."""
    task: Task
    success: bool
    output: str
    validation_output: str | None
    iterations: int
    review_markers: List[str]


class Orchestrator:
    """Orchestrate task execution."""
    
    def __init__(
        self,
        plan: Plan,
        executor: QwenExecutor | None = None,
        validator: Validator | None = None,
        progress: ProgressTracker | None = None,
        max_iterations: int = 3,
        review_mode: str = "auto",  # "auto" or "interactive"
    ):
        """Initialize orchestrator.
        
        Args:
            plan: Plan to execute
            executor: Qwen executor (default: create new)
            validator: Validator (default: create new)
            progress: Progress tracker (default: create new)
            max_iterations: Max retry iterations per task
            review_mode: "auto" or "interactive"
        """
        self.plan = plan
        self.executor = executor or QwenExecutor()
        self.validator = validator or Validator()
        self.progress = progress or ProgressTracker(plan.file_path)
        self.max_iterations = max_iterations
        self.review_mode = review_mode
    
    async def run_task(self, task: Task) -> TaskResult:
        """Run a single task with validation.
        
        Args:
            task: Task to execute
            
        Returns:
            TaskResult
            
        Raises:
            MaxIterationsExceededError: If validation fails max_iterations times
        """
        self.progress.log(f"Started task {task.number}: {task.title}")
        
        review_markers: List[str] = []
        last_output = ""
        
        for iteration in range(1, self.max_iterations + 1):
            self.progress.log(f"Iteration {iteration}/{self.max_iterations}")
            
            # Build prompt from task checkboxes
            prompt = self._build_task_prompt(task)
            
            # Execute task
            output_parts = []
            async for event in self.executor.run_task(prompt):
                if event.get('type') == 'assistant':
                    content = event.get('message', {}).get('content', [])
                    for c in content:
                        if c.get('type') == 'text':
                            output_parts.append(c.get('text', ''))
            
            last_output = "\n".join(output_parts)
            
            # Extract REVIEW markers from output
            review_markers = self._extract_review_markers(last_output)
            
            # Handle REVIEW markers based on mode
            if review_markers and self.review_mode == "interactive":
                # Pause for human review
                self.progress.log(f"REVIEW markers found: {len(review_markers)}")
                # In interactive mode, we'd wait for human input
                # For now, just log
                for marker in review_markers:
                    self.progress.log(f"  REVIEW: {marker}")
            
            # Run validation
            validation_result = await self.validator.run(self.plan.validation_commands)
            self.progress.log(f"Validation: {'PASS' if validation_result.success else 'FAIL'}")
            
            if validation_result.success:
                self.progress.log(f"Completed task {task.number}")
                return TaskResult(
                    task=task,
                    success=True,
                    output=last_output,
                    validation_output=validation_result.output,
                    iterations=iteration,
                    review_markers=review_markers,
                )
            
            self.progress.log(f"Validation failed, retrying...")
        
        # Max iterations exceeded
        raise MaxIterationsExceededError(
            f"Task {task.number} failed after {self.max_iterations} iterations"
        )
    
    def _build_task_prompt(self, task: Task) -> str:
        """Build prompt from task checkboxes.
        
        Args:
            task: Task to execute
            
        Returns:
            Prompt string
        """
        incomplete = [cb for cb in task.checkboxes if not cb.completed]
        
        if not incomplete:
            return f"Task {task.number}: {task.title} is already complete."
        
        items = "\n".join(f"- [ ] {cb.text}" for cb in incomplete)
        return f"""Task {task.number}: {task.title}

Complete the following items:
{items}

After completing, mark each item as done by updating the checkbox to [x].
"""
    
    def _extract_review_markers(self, text: str) -> List[str]:
        """Extract REVIEW markers from output.
        
        Args:
            text: Output text
            
        Returns:
            List of REVIEW marker contents
        """
        import re
        pattern = r'<!--\s*REVIEW:\s*(.+?)\s*-->'
        matches = re.findall(pattern, text, re.DOTALL)
        return [m.strip() for m in matches]
    
    async def run(self) -> None:
        """Run all tasks in the plan."""
        self.progress.start()
        
        while not self.plan.is_complete:
            task = self.plan.current_task
            if not task:
                break
            
            try:
                result = await self.run_task(task)
                
                if result.success:
                    # Update checkboxes
                    for cb in task.checkboxes:
                        cb.completed = True
                    
                    self.plan.next_task()
                    self.progress.complete_task(task.number, task.title)
                    
            except MaxIterationsExceededError as e:
                self.progress.task_failed(task.number, str(e))
                raise
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_orchestrator.py -v`
Expected: PASS (3 теста)

**Step 5: Commit**

```bash
git add src/qwenex/orchestrator.py src/tests/test_orchestrator.py
git commit -m "feat(FEAT-001.7): orchestrator (Task Loop with Validation)"
```

---

## Компонент 7: CLI

### Task 8: CLI интерфейс

**Files:**
- Create: `src/qwenex/cli.py`
- Test: `src/tests/test_cli.py`

**Step 1: Write the failing test**

```python
# src/tests/test_cli.py
import pytest
from qwenex.cli import main, parse_args


def test_parse_args_basic():
    """Test basic argument parsing."""
    args = parse_args(["docs/plans/test.md"])
    
    assert args.plan_file == "docs/plans/test.md"
    assert args.auto == False
    assert args.interactive == False
    assert args.tasks_only == False
    assert args.max_iterations == 3
    assert args.timeout == 10


def test_parse_args_auto_mode():
    """Test --auto flag."""
    args = parse_args(["--auto", "docs/plans/test.md"])
    
    assert args.auto == True
    assert args.interactive == False


def test_parse_args_interactive_mode():
    """Test --interactive flag."""
    args = parse_args(["--interactive", "docs/plans/test.md"])
    
    assert args.interactive == True
    assert args.auto == False


def test_parse_args_tasks_only():
    """Test --tasks-only flag."""
    args = parse_args(["--tasks-only", "docs/plans/test.md"])
    
    assert args.tasks_only == True


def test_parse_args_max_iterations():
    """Test --max-iterations flag."""
    args = parse_args(["--max-iterations", "5", "docs/plans/test.md"])
    
    assert args.max_iterations == 5


def test_parse_args_timeout():
    """Test --timeout flag."""
    args = parse_args(["--timeout", "15", "docs/plans/test.md"])
    
    assert args.timeout == 15
```

**Step 2: Run test to verify it fails**

Run: `pytest src/tests/test_cli.py::test_parse_args_basic -v`
Expected: FAIL с "ModuleNotFoundError: No module named 'qwenex.cli'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/cli.py
"""CLI interface for Qwenex."""

import argparse
import asyncio
import signal
import sys
from pathlib import Path

from .plan_parser import parse_plan_file
from .orchestrator import Orchestrator
from .progress import ProgressTracker
from .qwen_executor import QwenExecutor
from .validator import Validator


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.
    
    Args:
        argv: Command line arguments (default: sys.argv[1:])
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="qwenex",
        description="Autonomous plan execution with Qwen CLI"
    )
    
    parser.add_argument(
        "plan_file",
        help="Path to plan markdown file"
    )
    
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Autonomous mode: REVIEW markers auto-approved"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode: pause on REVIEW markers"
    )
    
    parser.add_argument(
        "--tasks-only",
        action="store_true",
        help="Run only tasks, skip all reviews"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum iterations per task (default: 3)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout in minutes per task (default: 10)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color output"
    )
    
    return parser.parse_args(argv)


def setup_signal_handlers(progress: ProgressTracker | None = None) -> None:
    """Setup signal handlers for graceful shutdown.
    
    Args:
        progress: Progress tracker to save on shutdown
    """
    def handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        if progress:
            progress.save()
            print("Progress saved.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


async def run_async(args: argparse.Namespace) -> int:
    """Run qwenex asynchronously.
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code
    """
    # Parse plan
    print(f"Loading plan: {args.plan_file}")
    plan = parse_plan_file(args.plan_file)
    print(f"Plan: {plan.title}")
    print(f"Tasks: {len(plan.tasks)}")
    
    # Create components
    progress = ProgressTracker(args.plan_file)
    executor = QwenExecutor(timeout_min=args.timeout)
    validator = Validator()
    
    # Setup signal handlers
    setup_signal_handlers(progress)
    
    # Determine review mode
    review_mode = "auto" if args.auto else "interactive"
    
    # Create orchestrator
    orchestrator = Orchestrator(
        plan=plan,
        executor=executor,
        validator=validator,
        progress=progress,
        max_iterations=args.max_iterations,
        review_mode=review_mode,
    )
    
    # Run
    try:
        await orchestrator.run()
        print("\n✅ Plan completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Plan failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main entry point.
    
    Args:
        argv: Command line arguments
        
    Returns:
        Exit code
    """
    args = parse_args(argv)
    return asyncio.run(run_async(args))


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run test to verify it passes**

Run: `pytest src/tests/test_cli.py -v`
Expected: PASS (6 тестов)

**Step 5: Commit**

```bash
git add src/qwenex/cli.py src/tests/test_cli.py
git commit -m "feat(FEAT-001.8): CLI интерфейс"
```

---

## Финальные задачи

### Task 9: Интеграционные тесты

**Files:**
- Create: `src/tests/test_integration.py`

**Step 1: Write integration test**

```python
# src/tests/test_integration.py
"""Integration tests for Qwenex."""

import pytest
import tempfile
import os
from pathlib import Path

from qwenex.plan_parser import parse_plan_file
from qwenex.orchestrator import Orchestrator
from qwenex.progress import ProgressTracker
from qwenex.validator import Validator


@pytest.fixture
def temp_plan_file():
    """Create a temporary plan file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_path = Path(tmpdir) / "test-plan.md"
        plan_path.write_text("""# Plan: Integration Test

## Validation Commands
- echo validation passed

### Task 1: Test task
- [ ] Say hello
- [ ] Mark completed
""")
        yield str(plan_path)


def test_parse_plan_integration(temp_plan_file):
    """Test plan parsing end-to-end."""
    plan = parse_plan_file(temp_plan_file)
    
    assert plan.title == "Integration Test"
    assert len(plan.tasks) == 1
    assert plan.tasks[0].number == "1"
    assert len(plan.tasks[0].checkboxes) == 2


@pytest.mark.asyncio
async def test_orchestrator_with_mock_executor(temp_plan_file, monkeypatch):
    """Test orchestrator with mocked executor."""
    from unittest.mock import AsyncMock, MagicMock
    
    plan = parse_plan_file(temp_plan_file)
    
    # Mock executor
    mock_executor = AsyncMock()
    mock_executor.run_task = AsyncMock(return_value=[
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Done"}]}}
    ])
    
    # Create temp progress dir
    with tempfile.TemporaryDirectory() as progress_dir:
        progress = ProgressTracker(temp_plan_file, progress_dir)
        validator = Validator()
        
        orchestrator = Orchestrator(
            plan=plan,
            executor=mock_executor,
            validator=validator,
            progress=progress,
        )
        
        await orchestrator.run()
        
        assert plan.is_complete == True
```

**Step 2: Run integration tests**

Run: `pytest src/tests/test_integration.py -v`
Expected: PASS (2 теста)

**Step 3: Commit**

```bash
git add src/tests/test_integration.py
git commit -m "test(FEAT-001.9): интеграционные тесты"
```

---

### Task 10: Финальная проверка и документация

**Files:**
- Create: `qwenex/README.md`
- Modify: `qwenex/README.md` (основной)

**Step 1: Создать README для qwenex/**

```markdown
# Qwenex Source

Исходный код qwenex.

## Структура

```
src/
├── qwenex/           # Основной пакет
│   ├── cli.py        # CLI интерфейс
│   ├── orchestrator.py  # Оркестрация задач
│   ├── plan_parser.py   # Парсинг планов
│   ├── qwen_executor.py # Qwen CLI executor
│   ├── validator.py     # Валидация
│   ├── progress.py      # Прогресс-трекинг
│   ├── git_wrapper.py   # Git операции
│   └── models.py        # Модели данных
└── tests/            # Тесты
```

## Установка

```bash
pip install -e ".[dev]"
```

## Запуск тестов

```bash
pytest
```

## Покрытие

Требуется 80%+ покрытие:

```bash
pytest --cov=src/qwenex --cov-fail-under=80
```
```

**Step 2: Обновить основной README.md**

Добавить секцию "Разработка":

```markdown
## Разработка

### Установка зависимостей

```bash
cd qwenex
pip install -e ".[dev]"
```

### Запуск тестов

```bash
pytest
```

### Структура кода

См. [qwenex/README.md](qwenex/README.md)
```

**Step 3: Запустить финальные тесты**

Run: `pytest --cov=src/qwenex --cov-report=term-missing`
Expected: Покрытие 80%+, все тесты проходят

**Step 4: Commit**

```bash
git add qwenex/README.md README.md src/tests/test_integration.py
git commit -m "docs(FEAT-001.10): документация и финальная проверка"
```

---

## Критерии приёмки

- [ ] Все 10 задач выполнены
- [ ] Все тесты проходят: `pytest` без ошибок
- [ ] Покрытие 80%+: `pytest --cov-fail-under=80`
- [ ] Типизация проверена: `mypy src/qwenex`
- [ ] Линтер проходит: `ruff check src/qwenex`
- [ ] CLI работает: `qwenex --help` показывает справку
- [ ] Документация создана

---

## Связанные документы

| Документ | Описание |
|----------|----------|
| [FEAT-001.md](../../specs/FEAT-001.md) | Спека ядра оркестратора |
| [ADR-017](../../docs/DECISIONS.md) | Qwen CLI интерфейс |
| [ADR-021](../../docs/DECISIONS.md) | Qwen CLI stream-json подтверждён |

---

**Plan complete and saved to `docs/plans/2026-02-27-feat-001-core-orchestrator.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
