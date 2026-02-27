"""Tests for orchestrator review integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_orchestrator_runs_review_after_task():
    """Test orchestrator runs review after task execution"""
    from qwenex.orchestrator import Orchestrator
    from qwenex.models import Plan, Task, Checkbox
    
    # Create mock plan
    plan = Plan(
        title="Test Plan",
        file_path="test.md",
        tasks=[
            Task(
                number="1",
                title="Test Task",
                checkboxes=[Checkbox(text="Done", completed=False)],
            )
        ],
        validation_commands=[],
    )
    
    with patch("qwenex.orchestrator.QwenExecutor") as mock_qwen:
        with patch("qwenex.orchestrator.HybridExecutor") as mock_review:
            with patch("qwenex.orchestrator.Validator") as mock_validator:
                with patch("qwenex.orchestrator.GitWrapper") as mock_git:
                    # Mock task execution
                    async def mock_run_task(prompt):
                        yield {"type": "result", "result": "Task done"}
                    
                    mock_qwen_instance = MagicMock()
                    mock_qwen_instance.run_task = mock_run_task
                    mock_qwen.return_value = mock_qwen_instance
                    
                    # Mock review
                    mock_review_instance = AsyncMock()
                    mock_review_instance.run_review = AsyncMock(return_value=MagicMock(
                        summary="Review done",
                        results=[],
                        aggregated_markers=[],
                    ))
                    mock_review.return_value = mock_review_instance
                    
                    # Mock validator
                    mock_validator_instance = AsyncMock()
                    mock_validator_instance.run = AsyncMock(return_value=MagicMock(success=True))
                    mock_validator.return_value = mock_validator_instance
                    
                    # Mock git
                    mock_git_instance = MagicMock()
                    mock_git_instance.diff_head = MagicMock(return_value="diff...")
                    mock_git_instance.add = MagicMock()
                    mock_git_instance.commit = MagicMock()
                    mock_git.return_value = mock_git_instance
                    
                    orchestrator = Orchestrator(plan=plan)
                    result = await orchestrator.run()
                    
                    # Verify review was called
                    assert mock_review_instance.run_review.called


@pytest.mark.asyncio
async def test_orchestrator_auto_mode_applies_markers():
    """Test orchestrator auto-approves non-critical markers"""
    from qwenex.orchestrator import Orchestrator
    from qwenex.models import Plan, Task, Checkbox
    from qwenex.review.models import ReviewMarker
    
    # Create mock plan
    plan = Plan(
        title="Test Plan",
        file_path="test.md",
        tasks=[
            Task(
                number="1",
                title="Test Task",
                checkboxes=[Checkbox(text="Done", completed=False)],
            )
        ],
        validation_commands=[],
    )
    
    with patch("qwenex.orchestrator.QwenExecutor") as mock_qwen:
        with patch("qwenex.orchestrator.HybridExecutor") as mock_review:
            with patch("qwenex.orchestrator.Validator") as mock_validator:
                with patch("qwenex.orchestrator.GitWrapper") as mock_git:
                    # Mock task execution
                    async def mock_run_task(prompt):
                        yield {"type": "result", "result": "Task done"}
                    
                    mock_qwen_instance = MagicMock()
                    mock_qwen_instance.run_task = mock_run_task
                    mock_qwen.return_value = mock_qwen_instance
                    
                    # Mock review with non-critical marker
                    mock_review_instance = AsyncMock()
                    mock_review_instance.run_review = AsyncMock(return_value=MagicMock(
                        summary="Review done",
                        results=[],
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
                    
                    # Mock validator
                    mock_validator_instance = AsyncMock()
                    mock_validator_instance.run = AsyncMock(return_value=MagicMock(success=True))
                    mock_validator.return_value = mock_validator_instance
                    
                    # Mock git
                    mock_git_instance = MagicMock()
                    mock_git_instance.diff_head = MagicMock(return_value="diff...")
                    mock_git_instance.add = MagicMock()
                    mock_git_instance.commit = MagicMock()
                    mock_git_instance.apply_fix = MagicMock()
                    mock_git.return_value = mock_git_instance
                    
                    orchestrator = Orchestrator(plan=plan, auto_mode=True)
                    result = await orchestrator.run()
                    
                    # Verify non-critical marker was auto-applied
                    assert mock_git_instance.apply_fix.called
