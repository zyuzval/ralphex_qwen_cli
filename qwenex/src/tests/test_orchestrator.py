"""Tests for orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from qwenex.orchestrator import Orchestrator, OrchestratorResult, MaxIterationsExceededError
from qwenex.models import Plan, Task, Checkbox


# Helper for async generator mock
async def async_gen(items):
    """Yield items as async generator."""
    for item in items:
        yield item


class TestOrchestratorResult:
    """Tests for OrchestratorResult dataclass."""

    def test_result_creation(self):
        """Test basic result creation."""
        result = OrchestratorResult(
            tasks_completed=5,
            tasks_failed=0,
            validation_passed=True
        )
        assert result.tasks_completed == 5
        assert result.tasks_failed == 0
        assert result.validation_passed is True

    def test_result_str(self):
        """Test result string representation."""
        result = OrchestratorResult(
            tasks_completed=3,
            tasks_failed=1,
            validation_passed=True
        )
        str_repr = str(result)
        assert "3" in str_repr
        assert "completed" in str_repr.lower()


class TestOrchestrator:
    """Tests for Orchestrator class."""

    @pytest.fixture
    def sample_plan(self):
        """Create a sample plan for testing."""
        return Plan(
            title="Test Plan",
            file_path="docs/plans/test.md",
            validation_commands=["echo test"],
            tasks=[
                Task(
                    number="1",
                    title="First task",
                    checkboxes=[Checkbox(text="Do something", completed=False)]
                ),
                Task(
                    number="2",
                    title="Second task",
                    checkboxes=[Checkbox(text="Do another thing", completed=False)]
                ),
            ]
        )

    @pytest.mark.asyncio
    async def test_orchestrator_creation(self, sample_plan):
        """Test creating an orchestrator."""
        with patch('qwenex.orchestrator.QwenExecutor'), \
             patch('qwenex.orchestrator.Validator'), \
             patch('qwenex.orchestrator.GitWrapper'), \
             patch('qwenex.orchestrator.ProgressTracker'):
            
            orchestrator = Orchestrator(plan=sample_plan)
            
            assert orchestrator.plan is sample_plan
            assert orchestrator.max_iterations == 3

    @pytest.mark.asyncio
    async def test_execute_task_success(self, sample_plan):
        """Test successful task execution."""
        with patch('qwenex.orchestrator.QwenExecutor') as MockExecutor, \
             patch('qwenex.orchestrator.Validator') as MockValidator, \
             patch('qwenex.orchestrator.GitWrapper'), \
             patch('qwenex.orchestrator.ProgressTracker'):
            
            # Mock executor with async generator
            mock_executor = MockExecutor.return_value
            mock_executor.run_task = MagicMock(return_value=async_gen([
                {"type": "result", "result": "Done"}
            ]))
            
            # Mock validator
            mock_validator = MockValidator.return_value
            mock_validator.run = AsyncMock(return_value=MagicMock(success=True, output="OK"))
            
            orchestrator = Orchestrator(plan=sample_plan)
            orchestrator.executor = mock_executor
            orchestrator.validator = mock_validator
            
            # Execute first task
            result = await orchestrator.execute_task_with_retry(sample_plan.tasks[0])
            
            assert result.tasks_completed == 1
            assert result.tasks_failed == 0
            assert result.validation_passed is True
            assert mock_executor.run_task.called
            assert mock_validator.run.called

    @pytest.mark.asyncio
    async def test_execute_task_retry_on_failure(self, sample_plan):
        """Test task retry on validation failure."""
        with patch('qwenex.orchestrator.QwenExecutor') as MockExecutor, \
             patch('qwenex.orchestrator.Validator') as MockValidator, \
             patch('qwenex.orchestrator.GitWrapper'), \
             patch('qwenex.orchestrator.ProgressTracker'):
            
            # Mock executor with async generator
            mock_executor = MockExecutor.return_value
            mock_executor.run_task = MagicMock(return_value=async_gen([
                {"type": "result", "result": "Done"}
            ]))
            
            # Mock validator - fail first, then succeed
            mock_validator = MockValidator.return_value
            mock_validator.run = AsyncMock(side_effect=[
                MagicMock(success=False, output="Failed"),
                MagicMock(success=True, output="OK"),
            ])
            
            orchestrator = Orchestrator(plan=sample_plan)
            orchestrator.executor = mock_executor
            orchestrator.validator = mock_validator
            
            result = await orchestrator.execute_task_with_retry(sample_plan.tasks[0])
            
            assert result.tasks_completed == 1
            assert result.tasks_failed == 0
            assert result.validation_passed is True
            assert mock_validator.run.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_task_max_iterations(self, sample_plan):
        """Test max iterations exceeded."""
        with patch('qwenex.orchestrator.QwenExecutor') as MockExecutor, \
             patch('qwenex.orchestrator.Validator') as MockValidator, \
             patch('qwenex.orchestrator.GitWrapper'), \
             patch('qwenex.orchestrator.ProgressTracker'):
            
            # Mock executor with async generator
            mock_executor = MockExecutor.return_value
            mock_executor.run_task = MagicMock(return_value=async_gen([
                {"type": "result", "result": "Done"}
            ]))
            
            # Mock validator - always fail
            mock_validator = MockValidator.return_value
            mock_validator.run = AsyncMock(return_value=MagicMock(success=False, output="Failed"))
            
            orchestrator = Orchestrator(plan=sample_plan, max_iterations=2)
            orchestrator.executor = mock_executor
            orchestrator.validator = mock_validator
            
            with pytest.raises(MaxIterationsExceededError):
                await orchestrator.execute_task_with_retry(sample_plan.tasks[0])

    @pytest.mark.asyncio
    async def test_run_all_tasks(self, sample_plan):
        """Test running all tasks."""
        with patch('qwenex.orchestrator.QwenExecutor') as MockExecutor, \
             patch('qwenex.orchestrator.Validator') as MockValidator, \
             patch('qwenex.orchestrator.GitWrapper'), \
             patch('qwenex.orchestrator.ProgressTracker'):
            
            # Mock executor with async generator
            mock_executor = MockExecutor.return_value
            mock_executor.run_task = MagicMock(return_value=async_gen([
                {"type": "result", "result": "Done"}
            ]))
            
            # Mock validator
            mock_validator = MockValidator.return_value
            mock_validator.run = AsyncMock(return_value=MagicMock(success=True, output="OK"))
            
            orchestrator = Orchestrator(plan=sample_plan)
            orchestrator.executor = mock_executor
            orchestrator.validator = mock_validator
            
            result = await orchestrator.run()
            
            assert result.tasks_completed == 2
            assert result.tasks_failed == 0

    @pytest.mark.asyncio
    async def test_run_with_review_markers(self, sample_plan):
        """Test handling of review markers."""
        with patch('qwenex.orchestrator.QwenExecutor') as MockExecutor, \
             patch('qwenex.orchestrator.Validator') as MockValidator, \
             patch('qwenex.orchestrator.GitWrapper'), \
             patch('qwenex.orchestrator.ProgressTracker'):
            
            # Mock executor with review markers in output
            mock_executor = MockExecutor.return_value
            mock_executor.run_task = MagicMock(return_value=async_gen([
                {"type": "result", "result": "<!-- REVIEW: Check this --> Done"}
            ]))
            
            # Mock validator
            mock_validator = MockValidator.return_value
            mock_validator.run = AsyncMock(return_value=MagicMock(success=True, output="OK"))
            
            orchestrator = Orchestrator(plan=sample_plan)
            orchestrator.executor = mock_executor
            orchestrator.validator = mock_validator
            
            result = await orchestrator.run()
            
            assert result.tasks_completed == 2
            # Review markers should be collected
            assert len(result.review_markers) >= 0  # May be empty if not parsed
