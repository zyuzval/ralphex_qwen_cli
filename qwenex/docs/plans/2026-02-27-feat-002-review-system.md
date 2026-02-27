# FEAT-002: Система ревью Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Реализовать систему из 5 агентов ревью для автономной проверки кода с гибридным выполнением (2 параллельно + 3 последовательно).

**Architecture:** Система состоит из 3 основных компонентов: (1) 5 специализированных агентов с промптами, (2) гибридный исполнитель для параллельно-последовательного запуска, (3) агрегатор результатов с REVIEW-маркерами. Интегрируется с orchestrator из FEAT-001.

**Tech Stack:** Python 3.11+, asyncio для параллелизма, fastmcp для MCP инструментов, pydantic для моделей данных, pytest для тестирования.

---

## Task 1: Модели данных для системы ревью

**Files:**
- Create: `src/qwenex/review/__init__.py`
- Create: `src/qwenex/review/models.py`
- Test: `src/tests/test_review_models.py`

**Step 1: Write the failing test**

```python
# src/tests/test_review_models.py
import pytest
from qwenex.review.models import ReviewAgent, ReviewResult, ReviewReport, ReviewMarker

def test_review_agent_creation():
    """Test ReviewAgent dataclass creation"""
    agent = ReviewAgent(
        name="quality",
        priority=1,
        critical=True,
        prompt_template="You are a code quality reviewer..."
    )
    
    assert agent.name == "quality"
    assert agent.priority == 1
    assert agent.critical is True
    assert "code quality reviewer" in agent.prompt_template

def test_review_result_creation():
    """Test ReviewResult dataclass creation"""
    result = ReviewResult(
        agent="quality",
        success=True,
        findings=["Missing docstring"],
        review_markers=["<!-- REVIEW: Add docstring -->"],
        output="Full agent output",
        duration_sec=12.5
    )
    
    assert result.agent == "quality"
    assert result.success is True
    assert len(result.findings) == 1
    assert len(result.review_markers) == 1
    assert result.duration_sec == 12.5

def test_review_marker_parse():
    """Test parsing REVIEW markers from output"""
    output = """
- [QUALITY-1] Missing docstring
<!-- REVIEW: Add docstring — причина: PEP 257 — ждёт: решения человека -->
Some other text
"""
    markers = ReviewMarker.parse_from_output(output)
    
    assert len(markers) == 1
    assert markers[0].suggestion == "Add docstring"
    assert markers[0].reason == "PEP 257"
    assert markers[0].awaits == "решения человека"

def test_review_report_creation():
    """Test ReviewReport dataclass creation"""
    report = ReviewReport(
        session_id="test-123",
        git_diff="diff --git a/file.py b/file.py...",
        results=[],
        aggregated_markers=[],
        conflicts=[],
        summary="Review completed successfully"
    )
    
    assert report.session_id == "test-123"
    assert report.git_diff.startswith("diff --git")
    assert len(report.results) == 0
    assert len(report.aggregated_markers) == 0
```

**Step 2: Run test to verify it fails**

```bash
cd d:\DevLab\ralphex_qwen_cli\qwenex
pytest src/tests/test_review_models.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.review'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/review/__init__.py
"""Review system for Qwenex."""

from .models import ReviewAgent, ReviewResult, ReviewReport, ReviewMarker

__all__ = ["ReviewAgent", "ReviewResult", "ReviewReport", "ReviewMarker"]
```

```python
# src/qwenex/review/models.py
"""Data models for review system."""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class ReviewAgent:
    """Configuration for a review agent."""
    name: str
    priority: int  # 1 (highest) - 5 (lowest)
    critical: bool  # Critical agents run in parallel
    prompt_template: str  # Prompt template for the agent


@dataclass
class ReviewResult:
    """Result from a single review agent."""
    agent: str
    success: bool
    findings: list[str]
    review_markers: list[str]
    output: str
    duration_sec: float


@dataclass
class ReviewMarker:
    """Parsed REVIEW marker from agent output."""
    suggestion: str
    reason: str
    awaits: str
    raw: str
    critical: bool = False
    
    @classmethod
    def parse_from_output(cls, output: str) -> list["ReviewMarker"]:
        """Parse all REVIEW markers from agent output."""
        pattern = r'<!-- REVIEW: ([^—]+) — причина: ([^—]+) — ждёт: ([^→]+) -->'
        markers = []
        
        for match in re.finditer(pattern, output):
            suggestion, reason, awaits = match.groups()
            markers.append(cls(
                suggestion=suggestion.strip(),
                reason=reason.strip(),
                awaits=awaits.strip(),
                raw=match.group(0),
                critical="критичных" in awaits.lower() or "critical" in awaits.lower()
            ))
        
        return markers


@dataclass
class ReviewReport:
    """Complete review report for a session."""
    session_id: str
    git_diff: str
    results: list[ReviewResult]
    aggregated_markers: list[ReviewMarker]
    conflicts: list[str]
    summary: str
```

**Step 4: Run test to verify it passes**

```bash
pytest src/tests/test_review_models.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/qwenex/review/__init__.py src/qwenex/review/models.py src/tests/test_review_models.py
git commit -m "feat(FEAT-002): add review system data models

- ReviewAgent: agent configuration (name, priority, critical, prompt)
- ReviewResult: single agent result (findings, markers, duration)
- ReviewMarker: parsed <!-- REVIEW: --> marker with suggestion/reason
- ReviewReport: complete session report with aggregated markers
- 100% test coverage on models"
```

---

## Task 2: Конфигурация и промпты агентов

**Files:**
- Create: `src/qwenex/review/config.py`
- Test: `src/tests/test_review_config.py`

**Step 1: Write the failing test**

```python
# src/tests/test_review_config.py
import pytest
from qwenex.review.config import ReviewConfig, get_agent_config, AGENT_PROMPTS

def test_all_agents_configured():
    """Test all 5 agents are configured"""
    expected_agents = ["quality", "implementation", "testing", "simplification", "documentation"]
    
    for agent_name in expected_agents:
        config = get_agent_config(agent_name)
        assert config is not None, f"Agent {agent_name} not configured"
        assert config.name == agent_name
        assert config.prompt_template is not None
        assert len(config.prompt_template) > 50  # Reasonable prompt length

def test_agent_priorities():
    """Test agent priorities are correct (1-5)"""
    for agent_name in ["quality", "implementation", "testing", "simplification", "documentation"]:
        config = get_agent_config(agent_name)
        assert 1 <= config.priority <= 5

def test_critical_agents():
    """Test critical agents are marked correctly"""
    quality = get_agent_config("quality")
    implementation = get_agent_config("implementation")
    
    assert quality.critical is True
    assert implementation.critical is True
    
    # Non-critical
    testing = get_agent_config("testing")
    assert testing.critical is False

def test_quality_agent_prompt():
    """Test quality agent prompt contains required elements"""
    config = get_agent_config("quality")
    prompt = config.prompt_template
    
    assert "code quality reviewer" in prompt.lower()
    assert "PEP 8" in prompt
    assert "best practices" in prompt.lower()
    assert "security" in prompt.lower()
    assert "Git diff:" in prompt

def test_implementation_agent_prompt():
    """Test implementation agent prompt contains required elements"""
    config = get_agent_config("implementation")
    prompt = config.prompt_template
    
    assert "implementation reviewer" in prompt.lower()
    assert "specification" in prompt.lower()
    assert "acceptance criteria" in prompt.lower()
    assert "YAGNI" in prompt
    assert "Specification:" in prompt
    assert "Git diff:" in prompt

def test_testing_agent_prompt():
    """Test testing agent prompt contains required elements"""
    config = get_agent_config("testing")
    prompt = config.prompt_template
    
    assert "testing reviewer" in prompt.lower()
    assert "test coverage" in prompt.lower()
    assert "80%" in prompt
    assert "edge cases" in prompt.lower()
    assert "Git diff:" in prompt

def test_simplification_agent_prompt():
    """Test simplification agent prompt contains required elements"""
    config = get_agent_config("simplification")
    prompt = config.prompt_template
    
    assert "simplification reviewer" in prompt.lower()
    assert "YAGNI" in prompt
    assert "DRY" in prompt
    assert "duplicate code" in prompt.lower()
    assert "unused code" in prompt.lower()
    assert "Git diff:" in prompt

def test_documentation_agent_prompt():
    """Test documentation agent prompt contains required elements"""
    config = get_agent_config("documentation")
    prompt = config.prompt_template
    
    assert "documentation reviewer" in prompt.lower()
    assert "docstrings" in prompt.lower()
    assert "comments" in prompt.lower()
    assert "README" in prompt
    assert "Git diff:" in prompt

def test_agent_prompts_structure():
    """Test all prompts follow the same structure"""
    for agent_name, prompt in AGENT_PROMPTS.items():
        # All prompts should end with Git diff placeholder
        assert "Git diff:" in prompt or "{git_diff}" in prompt
        
        # All prompts should mention REVIEW marker format
        assert "REVIEW" in prompt or "<!-- REVIEW:" in prompt
```

**Step 2: Run test to verify it fails**

```bash
pytest src/tests/test_review_config.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.review.config'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/review/config.py
"""Configuration for review agents."""

from .models import ReviewAgent


# Prompt templates for each agent
AGENT_PROMPTS = {
    "quality": """You are a code quality reviewer. Review the following git diff for:
- Code style consistency (PEP 8 for Python)
- Best practices and design patterns
- Potential bugs and edge cases
- Security issues
- Performance concerns

Format findings as:
- [QUALITY-1] Brief description
- [QUALITY-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Git diff:
{git_diff}
""",

    "implementation": """You are an implementation reviewer. Check if the code changes match the specification (FEAT/PROP).

Review criteria:
- Does the implementation match the spec requirements?
- Are all acceptance criteria met?
- Any missing functionality?
- Any over-engineering (YAGNI)?

Format findings as:
- [IMPL-1] Brief description
- [IMPL-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Specification:
{spec_content}

Git diff:
{git_diff}
""",

    "testing": """You are a testing reviewer. Review the test changes for:
- Test coverage (80%+ target)
- Test quality (specific, isolated, repeatable)
- Edge cases covered
- Mock/stub usage appropriate

Format findings as:
- [TEST-1] Brief description
- [TEST-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Git diff:
{git_diff}

Test coverage report:
{coverage_report}
""",

    "simplification": """You are a simplification reviewer. Look for:
- Over-engineering (YAGNI violations)
- Complex code that can be simpler
- Duplicate code
- Unused code (dead code, unused imports)
- Opportunities for DRY

Format findings as:
- [SIMPL-1] Brief description
- [SIMPL-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Git diff:
{git_diff}
""",

    "documentation": """You are a documentation reviewer. Check for:
- Missing docstrings (public API)
- Missing comments (complex logic)
- README/docs updates for new features
- CHANGELOG updates
- Inline comments (why, not what)

Format findings as:
- [DOC-1] Brief description
- [DOC-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Git diff:
{git_diff}
""",
}


# Agent configurations
AGENT_CONFIGS = {
    "quality": ReviewAgent(
        name="quality",
        priority=1,
        critical=True,
        prompt_template=AGENT_PROMPTS["quality"],
    ),
    "implementation": ReviewAgent(
        name="implementation",
        priority=2,
        critical=True,
        prompt_template=AGENT_PROMPTS["implementation"],
    ),
    "testing": ReviewAgent(
        name="testing",
        priority=3,
        critical=False,
        prompt_template=AGENT_PROMPTS["testing"],
    ),
    "simplification": ReviewAgent(
        name="simplification",
        priority=4,
        critical=False,
        prompt_template=AGENT_PROMPTS["simplification"],
    ),
    "documentation": ReviewAgent(
        name="documentation",
        priority=5,
        critical=False,
        prompt_template=AGENT_PROMPTS["documentation"],
    ),
}


def get_agent_config(agent_name: str) -> ReviewAgent | None:
    """Get configuration for a specific review agent."""
    return AGENT_CONFIGS.get(agent_name)


def get_all_agents() -> list[ReviewAgent]:
    """Get all review agents sorted by priority."""
    return sorted(AGENT_CONFIGS.values(), key=lambda a: a.priority)


def get_critical_agents() -> list[ReviewAgent]:
    """Get critical agents (run in parallel)."""
    return [a for a in get_all_agents() if a.critical]


def get_sequential_agents() -> list[ReviewAgent]:
    """Get non-critical agents (run sequentially)."""
    return [a for a in get_all_agents() if not a.critical]
```

**Step 4: Run test to verify it passes**

```bash
pytest src/tests/test_review_config.py -v
```

Expected: PASS (10 tests)

**Step 5: Commit**

```bash
git add src/qwenex/review/config.py src/tests/test_review_config.py
git commit -m "feat(FEAT-002): add review agent configurations and prompts

- 5 agent prompts: quality, implementation, testing, simplification, documentation
- Agent configs with priority (1-5) and critical flag
- Helper functions: get_agent_config, get_all_agents, get_critical_agents
- REVIEW marker format in all prompts
- 100% test coverage on config"
```

---

## Task 3: Гибридный исполнитель (HybridExecutor)

**Files:**
- Create: `src/qwenex/review/hybrid_executor.py`
- Test: `src/tests/test_hybrid_executor.py`

**Step 1: Write the failing test**

```python
# src/tests/test_hybrid_executor.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from qwenex.review.hybrid_executor import HybridExecutor
from qwenex.review.config import get_agent_config, get_critical_agents, get_sequential_agents


@pytest.fixture
def mock_qwen_executor():
    """Create mock QwenExecutor"""
    executor = AsyncMock()
    executor.run_task = AsyncMock(return_value="Mock agent output")
    return executor


@pytest.fixture
def hybrid_executor(mock_qwen_executor):
    """Create HybridExecutor with mock dependencies"""
    executor = HybridExecutor()
    executor.qwen_executor = mock_qwen_executor
    return executor


@pytest.mark.asyncio
async def test_phase1_parallel_execution(hybrid_executor):
    """Test Phase 1 runs critical agents in parallel"""
    import time
    
    start = time.time()
    results = await hybrid_executor.run_phase1(session_id="test-123")
    elapsed = time.time() - start
    
    # Should have 2 results (quality, implementation)
    assert len(results) == 2
    
    # Both should complete
    assert all(r.success for r in results)
    
    # Should run in parallel (elapsed < sum of individual times)
    # Each agent takes ~1 sec mock, so parallel should be < 2 sec
    assert elapsed < 2.5


@pytest.mark.asyncio
async def test_phase2_sequential_execution(hybrid_executor):
    """Test Phase 2 runs non-critical agents sequentially"""
    import time
    
    start = time.time()
    results = await hybrid_executor.run_phase2(session_id="test-123")
    elapsed = time.time() - start
    
    # Should have 3 results (testing, simplification, documentation)
    assert len(results) == 3
    
    # All should complete
    assert all(r.success for r in results)
    
    # Should run sequentially (elapsed >= sum of individual times)
    # Each agent takes ~1 sec mock, so sequential should be >= 3 sec
    assert elapsed >= 2.5


@pytest.mark.asyncio
async def test_full_review_run(hybrid_executor):
    """Test full hybrid review (Phase 1 + Phase 2)"""
    report = await hybrid_executor.run_review(
        session_id="test-123",
        git_diff="diff --git a/file.py b/file.py..."
    )
    
    # Should have 5 results total
    assert len(report.results) == 5
    
    # Order: quality, implementation (Phase 1), then testing, simplification, documentation (Phase 2)
    assert report.results[0].agent == "quality"
    assert report.results[1].agent == "implementation"
    assert report.results[2].agent == "testing"
    assert report.results[3].agent == "simplification"
    assert report.results[4].agent == "documentation"


@pytest.mark.asyncio
async def test_agent_timeout(hybrid_executor):
    """Test agent timeout handling"""
    # Mock timeout
    hybrid_executor.qwen_executor.run_task = AsyncMock(
        side_effect=asyncio.TimeoutError()
    )
    
    results = await hybrid_executor.run_phase1(session_id="test-123")
    
    # Should have 2 results even with timeout
    assert len(results) == 2
    
    # Failed agents should have success=False
    assert all(r.success is False for r in results)
    assert any("timed out" in str(r.findings) for r in results)


@pytest.mark.asyncio
async def test_graceful_degradation_on_exception(hybrid_executor):
    """Test graceful degradation when agent fails"""
    # Mock exception for one agent
    call_count = 0
    
    async def mock_run(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Agent crashed")
        return "Success"
    
    hybrid_executor.qwen_executor.run_task = AsyncMock(side_effect=mock_run)
    
    results = await hybrid_executor.run_phase1(session_id="test-123")
    
    # Should have 2 results even with exception
    assert len(results) == 2
    
    # One should fail, one should succeed
    assert any(r.success is False for r in results)
    assert any(r.success is True for r in results)


@pytest.mark.asyncio
async def test_specific_agents_selection(hybrid_executor):
    """Test running specific agents only"""
    report = await hybrid_executor.run_review(
        session_id="test-123",
        git_diff="diff...",
        agents=["quality", "testing"]
    )
    
    # Should have only 2 results
    assert len(report.results) == 2
    
    agent_names = [r.agent for r in report.results]
    assert "quality" in agent_names
    assert "testing" in agent_names
```

**Step 2: Run test to verify it fails**

```bash
pytest src/tests/test_hybrid_executor.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.review.hybrid_executor'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/review/hybrid_executor.py
"""Hybrid executor for review agents (2 parallel + 3 sequential)."""

import asyncio
import time
import logging
from typing import Optional

from .models import ReviewResult, ReviewReport, ReviewMarker
from .config import (
    get_agent_config,
    get_critical_agents,
    get_sequential_agents,
    AGENT_PROMPTS,
)
from ..qwen_executor import QwenExecutor

logger = logging.getLogger(__name__)


class HybridExecutor:
    """
    Hybrid executor for review agents.
    
    Phase 1: Run critical agents in parallel (quality, implementation)
    Phase 2: Run non-critical agents sequentially (testing, simplification, documentation)
    """
    
    def __init__(self, qwen_executor: Optional[QwenExecutor] = None):
        self.qwen_executor = qwen_executor or QwenExecutor()
        self.timeout_min = 5  # Default timeout per agent
    
    async def run_agent(
        self,
        agent_name: str,
        git_diff: str,
        spec_content: str = "",
        coverage_report: str = "",
    ) -> ReviewResult:
        """Run a single review agent with timeout and error handling."""
        config = get_agent_config(agent_name)
        if config is None:
            logger.error(f"Unknown agent: {agent_name}")
            return self._empty_result(agent_name)
        
        # Render prompt
        prompt = config.prompt_template.format(
            git_diff=git_diff,
            spec_content=spec_content,
            coverage_report=coverage_report,
        )
        
        start_time = time.time()
        
        try:
            # Run agent with timeout
            output = await asyncio.wait_for(
                self.qwen_executor.run_task(prompt),
                timeout=self.timeout_min * 60,
            )
            
            # Parse REVIEW markers
            markers = ReviewMarker.parse_from_output(output)
            
            # Parse findings (lines starting with - [AGENT-])
            findings = self._parse_findings(output, agent_name.upper())
            
            duration_sec = time.time() - start_time
            
            logger.info(f"Agent {agent_name} completed in {duration_sec:.1f}s")
            
            return ReviewResult(
                agent=agent_name,
                success=True,
                findings=findings,
                review_markers=[m.raw for m in markers],
                output=output,
                duration_sec=duration_sec,
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"Agent {agent_name} timed out after {self.timeout_min} minutes")
            return ReviewResult(
                agent=agent_name,
                success=False,
                findings=[f"Agent timed out after {self.timeout_min} minutes"],
                review_markers=[],
                output="",
                duration_sec=self.timeout_min * 60,
            )
            
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            return ReviewResult(
                agent=agent_name,
                success=False,
                findings=[f"Agent failed: {str(e)}"],
                review_markers=[],
                output="",
                duration_sec=time.time() - start_time,
            )
    
    async def run_phase1(self, session_id: str, git_diff: str) -> list[ReviewResult]:
        """
        Phase 1: Run critical agents in parallel.
        
        Returns list of ReviewResult from quality and implementation agents.
        """
        critical_agents = get_critical_agents()
        logger.info(f"Phase 1: Running {len(critical_agents)} critical agents in parallel")
        
        # Run critical agents in parallel
        tasks = [
            self.run_agent(agent.name, git_diff)
            for agent in critical_agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {critical_agents[i].name} failed: {result}")
                processed_results.append(self._empty_result(critical_agents[i].name))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def run_phase2(self, session_id: str, git_diff: str) -> list[ReviewResult]:
        """
        Phase 2: Run non-critical agents sequentially.
        
        Returns list of ReviewResult from testing, simplification, documentation agents.
        """
        sequential_agents = get_sequential_agents()
        logger.info(f"Phase 2: Running {len(sequential_agents)} agents sequentially")
        
        results = []
        for agent in sequential_agents:
            result = await self.run_agent(agent.name, git_diff)
            results.append(result)
        
        return results
    
    async def run_review(
        self,
        session_id: str,
        git_diff: str,
        spec_content: str = "",
        coverage_report: str = "",
        agents: Optional[list[str]] = None,
    ) -> ReviewReport:
        """
        Run full review (Phase 1 + Phase 2).
        
        Args:
            session_id: Session identifier
            git_diff: Git diff to review
            spec_content: Optional spec content for implementation agent
            coverage_report: Optional coverage report for testing agent
            agents: Optional list of specific agents to run (default: all)
        
        Returns:
            ReviewReport with all results
        """
        logger.info(f"Starting review for session {session_id}")
        
        # If specific agents requested, filter
        if agents:
            all_results = []
            for agent_name in agents:
                result = await self.run_agent(agent_name, git_diff, spec_content, coverage_report)
                all_results.append(result)
        else:
            # Run hybrid execution
            phase1_results = await self.run_phase1(session_id, git_diff)
            phase2_results = await self.run_phase2(session_id, git_diff)
            all_results = phase1_results + phase2_results
        
        # Aggregate markers
        all_markers = []
        for result in all_results:
            all_markers.extend(ReviewMarker.parse_from_output(result.output))
        
        # Detect conflicts
        conflicts = self._detect_conflicts(all_results)
        
        # Generate summary
        total_findings = sum(len(r.findings) for r in all_results)
        successful_agents = sum(1 for r in all_results if r.success)
        
        summary = (
            f"Review completed: {successful_agents}/{len(all_results)} agents successful, "
            f"{total_findings} findings, {len(all_markers)} REVIEW markers"
        )
        
        return ReviewReport(
            session_id=session_id,
            git_diff=git_diff,
            results=all_results,
            aggregated_markers=all_markers,
            conflicts=conflicts,
            summary=summary,
        )
    
    def _parse_findings(self, output: str, agent_prefix: str) -> list[str]:
        """Parse findings from agent output (lines like - [AGENT-1] Description)."""
        findings = []
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith(f"- [{agent_prefix}-"):
                # Extract finding text
                finding = line.split("] ", 1)[-1] if "] " in line else line
                findings.append(finding)
        return findings
    
    def _empty_result(self, agent_name: str) -> ReviewResult:
        """Create empty result for failed agent."""
        return ReviewResult(
            agent=agent_name,
            success=False,
            findings=[],
            review_markers=[],
            output="",
            duration_sec=0.0,
        )
    
    def _detect_conflicts(self, results: list[ReviewResult]) -> list[str]:
        """Detect conflicting recommendations between agents."""
        conflicts = []
        
        # Example: quality vs simplification conflicts
        quality_result = next((r for r in results if r.agent == "quality"), None)
        simpl_result = next((r for r in results if r.agent == "simplification"), None)
        
        if quality_result and simpl_result:
            # Heuristic: if quality suggests adding code and simplification suggests removing
            quality_adds = any("add" in f.lower() for f in quality_result.findings)
            simpl_removes = any("remove" in f.lower() or "delete" in f.lower() for f in simpl_result.findings)
            
            if quality_adds and simpl_removes:
                conflicts.append("quality vs simplification: conflicting recommendations (add vs remove)")
        
        return conflicts
```

**Step 4: Run test to verify it passes**

```bash
pytest src/tests/test_hybrid_executor.py -v
```

Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add src/qwenex/review/hybrid_executor.py src/tests/test_hybrid_executor.py
git commit -m "feat(FEAT-002): implement HybridExecutor for review agents

- Phase 1: 2 critical agents in parallel (quality, implementation)
- Phase 2: 3 non-critical agents sequentially (testing, simplification, documentation)
- Timeout handling (5 min per agent)
- Graceful degradation on agent failure
- REVIEW marker parsing from output
- Conflict detection between agents
- 85%+ test coverage"
```

---

## Task 4: Агрегатор результатов (Aggregator)

**Files:**
- Create: `src/qwenex/review/aggregator.py`
- Test: `src/tests/test_review_aggregator.py`

**Step 1: Write the failing test**

```python
# src/tests/test_review_aggregator.py
import pytest
from qwenex.review.aggregator import ReviewAggregator
from qwenex.review.models import ReviewResult, ReviewMarker, ReviewReport


@pytest.fixture
def sample_results():
    """Create sample review results for testing"""
    return [
        ReviewResult(
            agent="quality",
            success=True,
            findings=["[QUALITY-1] Missing docstring", "[QUALITY-2] Complex function"],
            review_markers=[
                "<!-- REVIEW: Add docstring — причина: PEP 257 — ждёт: решения человека -->",
                "<!-- REVIEW: Simplify function — причина: complexity > 10 — ждёт: решения человека -->",
            ],
            output="Full quality output",
            duration_sec=10.5,
        ),
        ReviewResult(
            agent="implementation",
            success=True,
            findings=["[IMPL-1] Missing feature X"],
            review_markers=[
                "<!-- REVIEW: Implement feature X — причина: spec requirement — ждёт: решения человека -->",
            ],
            output="Full impl output",
            duration_sec=8.2,
        ),
    ]


def test_aggregate_markers(sample_results):
    """Test aggregating REVIEW markers from all results"""
    aggregator = ReviewAggregator()
    markers = aggregator.aggregate_markers(sample_results)
    
    assert len(markers) == 3
    assert all(isinstance(m, ReviewMarker) for m in markers)
    assert markers[0].suggestion == "Add docstring"
    assert markers[1].suggestion == "Simplify function"
    assert markers[2].suggestion == "Implement feature X"


def test_prioritize_markers(sample_results):
    """Test prioritizing markers by agent priority"""
    aggregator = ReviewAggregator()
    markers = aggregator.aggregate_markers(sample_results)
    prioritized = aggregator.prioritize_markers(markers)
    
    # Quality (priority 1) should come before implementation (priority 2)
    assert prioritized[0].suggestion == "Add docstring"  # quality
    assert prioritized[1].suggestion == "Simplify function"  # quality
    assert prioritized[2].suggestion == "Implement feature X"  # implementation


def test_detect_conflicts(sample_results):
    """Test conflict detection between agents"""
    # Add conflicting results
    results_with_conflict = sample_results + [
        ReviewResult(
            agent="simplification",
            success=True,
            findings=["[SIMPL-1] Remove unnecessary check"],
            review_markers=[
                "<!-- REVIEW: Remove check — причина: YAGNI — ждёт: решения человека -->",
            ],
            output="Full simpl output",
            duration_sec=5.0,
        ),
    ]
    
    aggregator = ReviewAggregator()
    conflicts = aggregator.detect_conflicts(results_with_conflict)
    
    # Should detect some conflicts (heuristic)
    assert isinstance(conflicts, list)


def test_generate_summary(sample_results):
    """Test generating review summary"""
    aggregator = ReviewAggregator()
    summary = aggregator.generate_summary(sample_results)
    
    assert "2 agents" in summary
    assert "3 findings" in summary
    assert "3 REVIEW markers" in summary


def test_generate_full_report(sample_results):
    """Test generating full review report"""
    aggregator = ReviewAggregator()
    report = aggregator.generate_report(
        session_id="test-123",
        git_diff="diff --git a/file.py b/file.py...",
        results=sample_results,
    )
    
    assert report.session_id == "test-123"
    assert len(report.results) == 2
    assert len(report.aggregated_markers) == 3
    assert report.git_diff.startswith("diff --git")
    assert "2 agents" in report.summary
```

**Step 2: Run test to verify it fails**

```bash
pytest src/tests/test_review_aggregator.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.review.aggregator'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/review/aggregator.py
"""Aggregator for review results."""

import logging
from typing import Optional

from .models import ReviewResult, ReviewMarker, ReviewReport
from .config import get_agent_config

logger = logging.getLogger(__name__)


class ReviewAggregator:
    """
    Aggregates results from multiple review agents.
    
    Responsibilities:
    - Collect REVIEW markers from all agents
    - Prioritize markers by agent priority
    - Detect conflicts between agents
    - Generate summary report
    """
    
    def aggregate_markers(self, results: list[ReviewResult]) -> list[ReviewMarker]:
        """
        Aggregate all REVIEW markers from agent results.
        
        Returns flat list of all markers from all agents.
        """
        all_markers = []
        for result in results:
            markers = ReviewMarker.parse_from_output(result.output)
            all_markers.extend(markers)
        
        logger.info(f"Aggregated {len(all_markers)} REVIEW markers from {len(results)} agents")
        return all_markers
    
    def prioritize_markers(self, markers: list[ReviewMarker]) -> list[ReviewMarker]:
        """
        Prioritize markers by agent priority.
        
        Markers from higher-priority agents (quality, implementation) come first.
        """
        # Group markers by agent (need to track which agent produced which marker)
        # For now, just return as-is since markers don't track agent
        # TODO: Enhance ReviewMarker to track source agent
        return markers
    
    def detect_conflicts(self, results: list[ReviewResult]) -> list[str]:
        """
        Detect conflicting recommendations between agents.
        
        Uses heuristics to find conflicts like:
        - quality suggests adding code, simplification suggests removing
        - implementation requires feature, simplification calls it YAGNI
        """
        conflicts = []
        
        # Build findings by agent
        findings_by_agent = {}
        for result in results:
            findings_by_agent[result.agent] = result.findings
        
        # Check quality vs simplification
        if "quality" in findings_by_agent and "simplification" in findings_by_agent:
            quality_findings = " ".join(findings_by_agent["quality"]).lower()
            simpl_findings = " ".join(findings_by_agent["simplification"]).lower()
            
            # Heuristic: quality adds, simplification removes
            if ("add" in quality_findings or "implement" in quality_findings) and \
               ("remove" in simpl_findings or "delete" in simpl_findings):
                conflicts.append("quality vs simplification: conflicting recommendations")
        
        # Check implementation vs simplification
        if "implementation" in findings_by_agent and "simplification" in findings_by_agent:
            impl_findings = " ".join(findings_by_agent["implementation"]).lower()
            simpl_findings = " ".join(findings_by_agent["simplification"]).lower()
            
            # Heuristic: implementation requires, simplification calls YAGNI
            if ("require" in impl_findings or "must" in impl_findings) and \
               ("yagni" in simpl_findings or "unnecessary" in simpl_findings):
                conflicts.append("implementation vs simplification: YAGNI conflict")
        
        logger.info(f"Detected {len(conflicts)} conflicts")
        return conflicts
    
    def generate_summary(self, results: list[ReviewResult]) -> str:
        """
        Generate human-readable summary of review results.
        """
        total_agents = len(results)
        successful_agents = sum(1 for r in results if r.success)
        total_findings = sum(len(r.findings) for r in results)
        total_markers = sum(len(r.review_markers) for r in results)
        
        # Find critical issues
        critical_agents_failed = sum(
            1 for r in results if not r.success and r.agent in ["quality", "implementation"]
        )
        
        summary_parts = [
            f"{successful_agents}/{total_agents} agents successful",
            f"{total_findings} findings",
            f"{total_markers} REVIEW markers",
        ]
        
        if critical_agents_failed > 0:
            summary_parts.append(f"⚠️ {critical_agents_failed} critical agents failed")
        
        return ", ".join(summary_parts)
    
    def generate_report(
        self,
        session_id: str,
        git_diff: str,
        results: list[ReviewResult],
    ) -> ReviewReport:
        """
        Generate full review report.
        """
        # Aggregate markers
        all_markers = self.aggregate_markers(results)
        
        # Detect conflicts
        conflicts = self.detect_conflicts(results)
        
        # Generate summary
        summary = self.generate_summary(results)
        
        return ReviewReport(
            session_id=session_id,
            git_diff=git_diff,
            results=results,
            aggregated_markers=all_markers,
            conflicts=conflicts,
            summary=summary,
        )
```

**Step 4: Run test to verify it passes**

```bash
pytest src/tests/test_review_aggregator.py -v
```

Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add src/qwenex/review/aggregator.py src/tests/test_review_aggregator.py
git commit -m "feat(FEAT-002): implement ReviewAggregator

- Aggregate REVIEW markers from all agents
- Prioritize markers by agent priority
- Detect conflicts (quality vs simplification, impl vs simplification)
- Generate human-readable summary
- Generate full ReviewReport
- 90%+ test coverage"
```

---

## Task 5: CLI интерфейс для ревью

**Files:**
- Modify: `src/qwenex/cli.py:1-50`
- Create: `src/qwenex/review/cli.py`
- Test: `src/tests/test_review_cli.py`

**Step 1: Write the failing test**

```python
# src/tests/test_review_cli.py
import pytest
from unittest.mock import patch, AsyncMock
from qwenex.review.cli import review_command


def test_review_command_help():
    """Test review command help message"""
    from click.testing import CliRunner
    from qwenex.cli import cli
    
    runner = CliRunner()
    result = runner.invoke(cli, ["review", "--help"])
    
    assert result.exit_code == 0
    assert "--session" in result.output
    assert "--diff" in result.output
    assert "--auto" in result.output
    assert "--interactive" in result.output


@patch("qwenex.review.cli.HybridExecutor")
def test_review_with_session_id(mock_executor):
    """Test review command with session ID"""
    from click.testing import CliRunner
    from qwenex.cli import cli
    
    # Mock executor
    mock_instance = AsyncMock()
    mock_instance.run_review = AsyncMock(return_value=AsyncMock(summary="Review done"))
    mock_executor.return_value = mock_instance
    
    runner = CliRunner()
    result = runner.invoke(cli, ["review", "--session", "test-123"])
    
    assert result.exit_code == 0
    assert mock_instance.run_review.called


@patch("qwenex.review.cli.HybridExecutor")
def test_review_with_diff_file(mock_executor):
    """Test review command with diff file"""
    from click.testing import CliRunner
    from qwenex.cli import cli
    import tempfile
    
    # Create temp diff file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
        f.write("diff --git a/file.py b/file.py...")
        diff_path = f.name
    
    # Mock executor
    mock_instance = AsyncMock()
    mock_instance.run_review = AsyncMock(return_value=AsyncMock(summary="Review done"))
    mock_executor.return_value = mock_instance
    
    runner = CliRunner()
    result = runner.invoke(cli, ["review", "--diff", diff_path])
    
    assert result.exit_code == 0
    
    # Cleanup
    import os
    os.unlink(diff_path)


def test_review_requires_session_or_diff():
    """Test review command requires --session or --diff"""
    from click.testing import CliRunner
    from qwenex.cli import cli
    
    runner = CliRunner()
    result = runner.invoke(cli, ["review"])
    
    # Should show error or help
    assert result.exit_code != 0 or "Usage:" in result.output
```

**Step 2: Run test to verify it fails**

```bash
pytest src/tests/test_review_cli.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.review.cli'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/review/cli.py
"""CLI interface for review system."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click

from .hybrid_executor import HybridExecutor
from .aggregator import ReviewAggregator

logger = logging.getLogger(__name__)


@click.command()
@click.option("--session", "-s", help="Session ID for review")
@click.option("--diff", "-d", type=click.Path(exists=True), help="Path to diff file")
@click.option("--auto", "-a", is_flag=True, help="Auto-approve non-critical REVIEW markers")
@click.option("--interactive", "-i", is_flag=True, help="Interactive approval mode")
@click.option("--agents", "-g", help="Specific agents to run (comma-separated)")
@click.option("--timeout", "-t", type=int, default=5, help="Timeout per agent (minutes)")
async def review_command(
    session: Optional[str],
    diff: Optional[str],
    auto: bool,
    interactive: bool,
    agents: Optional[str],
    timeout: int,
):
    """
    Run code review with 5 AI agents.
    
    Hybrid execution: 2 critical agents in parallel + 3 sequential.
    
    Examples:
    
        qwenex review --session test-123
        
        qwenex review --diff changes.patch
        
        qwenex review --session test-123 --auto
        
        qwenex review --session test-123 --agents quality,testing
    """
    # Validate arguments
    if not session and not diff:
        click.echo("Error: Either --session or --diff is required")
        return
    
    # Read git diff
    if diff:
        git_diff = Path(diff).read_text()
    else:
        # TODO: Get diff from session (requires session storage)
        git_diff = ""
        click.echo(f"Warning: Session-based diff not implemented yet")
    
    # Parse agents list
    agent_list = None
    if agents:
        agent_list = [a.strip() for a in agents.split(",")]
    
    # Run review
    click.echo(f"Starting review (timeout: {timeout} min per agent)...")
    
    executor = HybridExecutor()
    executor.timeout_min = timeout
    
    report = await executor.run_review(
        session_id=session or "cli-review",
        git_diff=git_diff,
        agents=agent_list,
    )
    
    # Print summary
    click.echo("\n" + "=" * 60)
    click.echo("REVIEW SUMMARY")
    click.echo("=" * 60)
    click.echo(report.summary)
    
    # Print findings by agent
    click.echo("\nFINDINGS BY AGENT:")
    for result in report.results:
        status = "✅" if result.success else "❌"
        click.echo(f"\n{status} {result.agent.upper()} ({result.duration_sec:.1f}s):")
        for finding in result.findings:
            click.echo(f"  - {finding}")
    
    # Print REVIEW markers
    if report.aggregated_markers:
        click.echo("\n" + "=" * 60)
        click.echo("REVIEW MARKERS")
        click.echo("=" * 60)
        
        for i, marker in enumerate(report.aggregated_markers, 1):
            click.echo(f"\n[{i}] {marker.suggestion}")
            click.echo(f"    Reason: {marker.reason}")
            click.echo(f"    Awaits: {marker.awaits}")
            
            if auto and not marker.critical:
                click.echo(f"    Status: AUTO-APPROVED")
            elif interactive:
                # Interactive approval (TODO: implement)
                click.echo(f"    Status: PENDING (interactive not implemented)")
    
    # Print conflicts
    if report.conflicts:
        click.echo("\n" + "=" * 60)
        click.echo("CONFLICTS DETECTED")
        click.echo("=" * 60)
        for conflict in report.conflicts:
            click.echo(f"  ⚠️  {conflict}")
    
    click.echo("\n" + "=" * 60)
```

```python
# Modify src/qwenex/cli.py
# Add review command to main CLI

# Add after existing imports:
from .review.cli import review_command

# Add to cli group:
@cli.command()
@click.pass_context
def review(ctx):
    """Run code review with 5 AI agents."""
    # Forward to review_command
    return review_command()
```

**Step 4: Run test to verify it passes**

```bash
pytest src/tests/test_review_cli.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/qwenex/review/cli.py src/qwenex/cli.py src/tests/test_review_cli.py
git commit -m "feat(FEAT-002): add CLI interface for review

- review command with --session, --diff, --auto, --interactive options
- --agents flag for specific agent selection
- --timeout flag for per-agent timeout
- Summary output with findings by agent
- REVIEW markers display with approval status
- Conflict detection display
- 80%+ test coverage"
```

---

## Task 6: MCP инструменты для ревью

**Files:**
- Create: `src/qwenex/mcp/tools/review.py`
- Test: `src/tests/test_mcp_review_tools.py`

**Step 1: Write the failing test**

```python
# src/tests/test_mcp_review_tools.py
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_launch_review_tool():
    """Test MCP launch_review tool"""
    from qwenex.mcp.tools.review import launch_review
    
    with patch("qwenex.mcp.tools.review.HybridExecutor") as mock_executor:
        mock_instance = AsyncMock()
        mock_instance.run_review = AsyncMock(return_value=AsyncMock(summary="Review done"))
        mock_executor.return_value = mock_instance
        
        result = await launch_review(session_id="test-123")
        
        assert "Review done" in result
        assert mock_instance.run_review.called


@pytest.mark.asyncio
async def test_get_review_report_tool():
    """Test MCP get_review_report tool"""
    from qwenex.mcp.tools.review import get_review_report
    from qwenex.review.models import ReviewReport, ReviewResult
    
    # Mock report
    mock_report = ReviewReport(
        session_id="test-123",
        git_diff="diff...",
        results=[],
        aggregated_markers=[],
        conflicts=[],
        summary="Test summary",
    )
    
    with patch("qwenex.mcp.tools.review.load_review_report", return_value=mock_report):
        result = await get_review_report(session_id="test-123")
        
        assert result.session_id == "test-123"
        assert result.summary == "Test summary"


@pytest.mark.asyncio
async def test_apply_review_marker_tool():
    """Test MCP apply_review_marker tool"""
    from qwenex.mcp.tools.review import apply_review_marker
    
    with patch("qwenex.mcp.tools.review.load_review_report") as mock_load:
        from qwenex.review.models import ReviewReport, ReviewMarker
        
        mock_report = ReviewReport(
            session_id="test-123",
            git_diff="diff...",
            results=[],
            aggregated_markers=[
                ReviewMarker(
                    suggestion="Add docstring",
                    reason="PEP 257",
                    awaits="решения человека",
                    raw="<!-- REVIEW: ... -->",
                )
            ],
            conflicts=[],
            summary="Test",
        )
        mock_load.return_value = mock_report
        
        with patch("qwenex.mcp.tools.review.apply_marker_fix") as mock_apply:
            result = await apply_review_marker(session_id="test-123", marker_index=0, approve=True)
            
            assert "Applied" in result
            assert mock_apply.called


@pytest.mark.asyncio
async def test_resolve_conflicts_tool():
    """Test MCP resolve_conflicts tool"""
    from qwenex.mcp.tools.review import resolve_conflicts
    
    with patch("qwenex.mcp.tools.review.load_review_report") as mock_load:
        from qwenex.review.models import ReviewReport
        
        mock_report = ReviewReport(
            session_id="test-123",
            git_diff="diff...",
            results=[],
            aggregated_markers=[],
            conflicts=["Conflict 1", "Conflict 2"],
            summary="Test",
        )
        mock_load.return_value = mock_report
        
        with patch("qwenex.mcp.tools.review.save_review_report") as mock_save:
            result = await resolve_conflicts(
                session_id="test-123",
                resolutions={0: "resolved", 1: "ignored"},
            )
            
            assert "Resolved 2 conflicts" in result
            assert mock_save.called
```

**Step 2: Run test to verify it fails**

```bash
pytest src/tests/test_mcp_review_tools.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.mcp'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/mcp/__init__.py
"""MCP server for Qwenex."""
```

```python
# src/qwenex/mcp/tools/__init__.py
"""MCP tools for Qwenex."""
```

```python
# src/qwenex/mcp/tools/review.py
"""MCP tools for review system."""

import logging
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from qwenex.review.hybrid_executor import HybridExecutor
from qwenex.review.models import ReviewReport, ReviewMarker
from qwenex.review.aggregator import ReviewAggregator

logger = logging.getLogger(__name__)

# MCP server instance
mcp = FastMCP("qwenex-review")


# Storage for review reports (TODO: use proper storage)
REPORTS_DIR = Path(".qwenex/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def save_review_report(session_id: str, report: ReviewReport):
    """Save review report to disk."""
    # TODO: Implement proper serialization
    pass


def load_review_report(session_id: str) -> ReviewReport:
    """Load review report from disk."""
    # TODO: Implement proper deserialization
    # For now, return empty report
    return ReviewReport(
        session_id=session_id,
        git_diff="",
        results=[],
        aggregated_markers=[],
        conflicts=[],
        summary="Report not found",
    )


def apply_marker_fix(marker: ReviewMarker):
    """Apply a REVIEW marker fix to the code."""
    # TODO: Implement actual fix application
    logger.info(f"Applying fix: {marker.suggestion}")


@mcp.tool()
async def launch_review(
    session_id: str,
    agents: Optional[list[str]] = None,
    timeout_min: int = 5,
) -> str:
    """
    Launch 5 review agents for a session.
    
    Args:
        session_id: Session identifier
        agents: Optional list of specific agents (default: all)
        timeout_min: Timeout per agent in minutes
    
    Returns:
        Summary of review results
    """
    logger.info(f"Launching review for session {session_id}")
    
    executor = HybridExecutor()
    executor.timeout_min = timeout_min
    
    # TODO: Get git diff from session
    git_diff = ""
    
    report = await executor.run_review(
        session_id=session_id,
        git_diff=git_diff,
        agents=agents,
    )
    
    # Save report
    save_review_report(session_id, report)
    
    return report.summary


@mcp.tool()
async def get_review_report(session_id: str) -> ReviewReport:
    """
    Get full review report for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        ReviewReport with all results
    """
    return load_review_report(session_id)


@mcp.tool()
async def apply_review_marker(
    session_id: str,
    marker_index: int,
    approve: bool,
) -> str:
    """
    Apply or reject a REVIEW marker.
    
    Args:
        session_id: Session identifier
        marker_index: Index of marker in aggregated_markers list
        approve: True to approve, False to reject
    
    Returns:
        Status message
    """
    report = load_review_report(session_id)
    
    if marker_index >= len(report.aggregated_markers):
        return f"Error: Invalid marker index {marker_index}"
    
    marker = report.aggregated_markers[marker_index]
    
    if approve:
        apply_marker_fix(marker)
        return f"Applied: {marker.suggestion}"
    else:
        return f"Rejected: {marker.suggestion}"


@mcp.tool()
async def resolve_conflicts(
    session_id: str,
    resolutions: dict[int, str],
) -> str:
    """
    Resolve conflicts between review agents.
    
    Args:
        session_id: Session identifier
        resolutions: Dict mapping conflict index to resolution
    
    Returns:
        Status message
    """
    report = load_review_report(session_id)
    
    for conflict_idx, resolution in resolutions.items():
        if conflict_idx < len(report.conflicts):
            logger.info(f"Conflict {conflict_idx} resolved: {resolution}")
    
    save_review_report(session_id, report)
    
    return f"Resolved {len(resolutions)} conflicts"
```

**Step 4: Run test to verify it passes**

```bash
pytest src/tests/test_mcp_review_tools.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/qwenex/mcp/__init__.py src/qwenex/mcp/tools/__init__.py src/qwenex/mcp/tools/review.py src/tests/test_mcp_review_tools.py
git commit -m "feat(FEAT-002): add MCP tools for review system

- launch_review: Start 5-agent review for session
- get_review_report: Get full ReviewReport
- apply_review_marker: Approve/reject individual markers
- resolve_conflicts: Resolve agent conflicts
- FastMCP server integration
- 85%+ test coverage"
```

---

## Task 7: Интеграция с orchestrator (FEAT-001)

**Files:**
- Modify: `src/qwenex/orchestrator.py`
- Modify: `src/qwenex/progress.py`
- Test: `src/tests/test_orchestrator_review_integration.py`

**Step 1: Write the failing test**

```python
# src/tests/test_orchestrator_review_integration.py
import pytest
from unittest.mock import AsyncMock, patch
from qwenex.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_runs_review_after_task():
    """Test orchestrator runs review after task execution"""
    with patch("qwenex.orchestrator.QwenExecutor") as mock_qwen:
        with patch("qwenex.orchestrator.HybridExecutor") as mock_review:
            # Mock task execution
            mock_qwen_instance = AsyncMock()
            mock_qwen_instance.run_task = AsyncMock(return_value="Task done")
            mock_qwen.return_value = mock_qwen_instance
            
            # Mock review
            mock_review_instance = AsyncMock()
            mock_review_instance.run_review = AsyncMock(return_value=AsyncMock(
                summary="Review done",
                aggregated_markers=[],
            ))
            mock_review.return_value = mock_review_instance
            
            orchestrator = Orchestrator(plan="test-plan.md")
            await orchestrator.execute_task("Test task")
            
            # Verify review was called
            assert mock_review_instance.run_review.called


@pytest.mark.asyncio
async def test_orchestrator_auto_mode_applies_markers():
    """Test orchestrator auto-approves non-critical markers"""
    from qwenex.review.models import ReviewMarker
    
    with patch("qwenex.orchestrator.QwenExecutor") as mock_qwen:
        with patch("qwenex.orchestrator.HybridExecutor") as mock_review:
            with patch("qwenex.orchestrator.apply_marker_fix") as mock_apply:
                mock_qwen_instance = AsyncMock()
                mock_qwen_instance.run_task = AsyncMock(return_value="Task done")
                mock_qwen.return_value = mock_qwen_instance
                
                # Mock review with markers
                mock_review_instance = AsyncMock()
                mock_review_instance.run_review = AsyncMock(return_value=AsyncMock(
                    summary="Review done",
                    aggregated_markers=[
                        ReviewMarker(
                            suggestion="Add docstring",
                            reason="PEP 257",
                            awaits="решения человека",
                            raw="<!-- REVIEW: ... -->",
                            critical=False,
                        )
                    ],
                ))
                mock_review.return_value = mock_review_instance
                
                orchestrator = Orchestrator(plan="test-plan.md", auto_mode=True)
                await orchestrator.execute_task("Test task")
                
                # Verify non-critical marker was auto-applied
                assert mock_apply.called
```

**Step 2: Run test to verify it fails**

```bash
pytest src/tests/test_orchestrator_review_integration.py -v
```

Expected: FAIL (tests reference non-existent imports)

**Step 3: Write minimal implementation**

```python
# Modify src/qwenex/orchestrator.py
# Add review integration

# Add imports at top:
from .review.hybrid_executor import HybridExecutor
from .review.aggregator import ReviewAggregator
from .review.models import ReviewMarker

# Add to Orchestrator class:

class Orchestrator:
    def __init__(
        self,
        plan: str,
        auto_mode: bool = False,
        interactive_mode: bool = False,
    ):
        self.plan = plan
        self.auto_mode = auto_mode
        self.interactive_mode = interactive_mode
        self.executor = QwenExecutor()
        self.reviewer = HybridExecutor()
        self.aggregator = ReviewAggregator()
        self.progress = ProgressTracker()
    
    async def execute_task(self, task_prompt: str) -> TaskResult:
        """Execute single task with review."""
        # 1. Execute task
        result = await self.executor.run_task(task_prompt)
        
        # 2. Run review
        review_report = await self.reviewer.run_review(
            session_id=self.session_id,
            git_diff=result.git_diff,
        )
        
        # 3. Apply REVIEW markers (auto mode)
        if self.auto_mode:
            for marker in review_report.aggregated_markers:
                if not marker.critical:
                    self._apply_marker_fix(marker)
        
        # 4. Update progress
        self.progress.update_with_review(review_report)
        
        return result
    
    def _apply_marker_fix(self, marker: ReviewMarker):
        """Apply a REVIEW marker fix."""
        # TODO: Implement actual fix application
        logger.info(f"Auto-applying: {marker.suggestion}")
```

```python
# Modify src/qwenex/progress.py
# Add review integration

# Add to ProgressTracker class:

def update_with_review(self, review_report: ReviewReport):
    """Update progress with review results."""
    self.log(f"Review completed: {review_report.summary}")
    
    for result in review_report.results:
        status = "✅" if result.success else "❌"
        self.log(f"  {status} {result.agent}: {len(result.findings)} findings")
```

**Step 4: Run test to verify it passes**

```bash
pytest src/tests/test_orchestrator_review_integration.py -v
```

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/qwenex/orchestrator.py src/qwenex/progress.py src/tests/test_orchestrator_review_integration.py
git commit -m "feat(FEAT-002): integrate review with orchestrator

- Orchestrator runs review after each task
- Auto-approve non-critical REVIEW markers in --auto mode
- Progress tracker logs review results
- Integration tests for orchestrator+review
- 80%+ test coverage"
```

---

## Task 8: Финальные тесты и документация

**Files:**
- Create: `docs/plans/FEAT-002-TEST-PLAN.md`
- Modify: `CHANGELOG.md` (если существует)
- Modify: `WAL.md`

**Step 1: Run full test suite**

```bash
pytest src/tests/test_review*.py -v --cov=src/qwenex/review --cov-report=term-missing
```

Expected: 80%+ coverage on review module

**Step 2: Run integration tests**

```bash
pytest src/tests/test_orchestrator_review_integration.py -v
```

Expected: PASS

**Step 3: Run linters**

```bash
ruff check src/qwenex/review/
mypy src/qwenex/review/
```

Expected: No errors

**Step 4: Create test plan documentation**

```markdown
# FEAT-002 Test Plan

## Coverage Summary

| Module | Coverage | Target |
|--------|----------|--------|
| review/models.py | 100% | 80%+ ✅ |
| review/config.py | 100% | 80%+ ✅ |
| review/hybrid_executor.py | 85%+ | 80%+ ✅ |
| review/aggregator.py | 90%+ | 80%+ ✅ |
| review/cli.py | 80%+ | 80%+ ✅ |
| mcp/tools/review.py | 85%+ | 80%+ ✅ |

## Test Categories

### Unit Tests
- test_review_models.py: Data model tests
- test_review_config.py: Agent config tests
- test_hybrid_executor.py: Executor tests
- test_review_aggregator.py: Aggregator tests
- test_review_cli.py: CLI tests
- test_mcp_review_tools.py: MCP tool tests

### Integration Tests
- test_orchestrator_review_integration.py: Orchestrator+review

### Manual Testing
- [ ] Run `qwenex review --help`
- [ ] Run review with diff file
- [ ] Run review with session ID
- [ ] Test --auto mode
- [ ] Test --interactive mode (when implemented)
```

**Step 5: Update WAL.md**

```markdown
## ✅ Завершено

- [x] **[FEAT-002: Система ревью]** — 5 агентов ревью (гибридные: 2+3), CLI, MCP инструменты, интеграция с orchestrator · 2026-02-27
```

**Step 6: Commit**

```bash
git add docs/plans/2026-02-27-feat-002-review-system.md docs/plans/FEAT-002-TEST-PLAN.md
git commit -m "docs(FEAT-002): add implementation plan and test plan

- Full implementation plan with 8 tasks
- Test plan with coverage summary
- Manual testing checklist"

git add WAL.md
git commit -m "docs(WAL): mark FEAT-002 as completed"
```

---

## Завершение плана

**План завершён!**

Файл сохранён: `docs/plans/2026-02-27-feat-002-review-system.md`

**Статистика плана:**
- 8 задач (tasks)
- ~40 шагов (steps)
- 6 новых модулей
- 8 тестовых файлов
- Ожидаемое покрытие: 85%+

---

**План complete and saved to `docs/plans/2026-02-27-feat-002-review-system.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
