"""Tests for hybrid executor (2 parallel + 3 sequential)."""

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
    results = await hybrid_executor.run_phase1(session_id="test-123", git_diff="diff content")
    elapsed = time.time() - start
    
    # Should have 2 results (quality, implementation)
    assert len(results) == 2
    
    # Both should complete
    assert all(r.success for r in results)
    
    # Should run in parallel (elapsed < sum of individual times)
    # Each agent takes ~0 sec mock, so parallel should be fast
    assert elapsed < 2.5


@pytest.mark.asyncio
async def test_phase2_sequential_execution(hybrid_executor):
    """Test Phase 2 runs non-critical agents sequentially"""
    import time
    
    start = time.time()
    results = await hybrid_executor.run_phase2(session_id="test-123", git_diff="diff content")
    elapsed = time.time() - start
    
    # Should have 3 results (testing, simplification, documentation)
    assert len(results) == 3
    
    # All should complete
    assert all(r.success for r in results)


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
    
    results = await hybrid_executor.run_phase1(session_id="test-123", git_diff="diff")
    
    # Should have 2 results even with timeout
    assert len(results) == 2
    
    # Failed agents should have success=False
    assert all(r.success is False for r in results)
    assert any("timed out" in str(r.findings).lower() for r in results)


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
    
    results = await hybrid_executor.run_phase1(session_id="test-123", git_diff="diff")
    
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
