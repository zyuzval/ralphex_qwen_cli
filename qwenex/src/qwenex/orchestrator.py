"""Orchestrate plan execution."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .plan_models import Plan, Task
from .models.base import LLMProvider, ProviderConfig
from .qwen_executor import QwenExecutor, TaskTimeoutError
from .validator import Validator
from .git_wrapper import GitWrapper
from .progress import ProgressTracker
from .review.hybrid_executor import HybridExecutor
from .review.aggregator import ReviewAggregator
from .review.models import ReviewMarker


class MaxIterationsExceededError(Exception):
    """Raised when task exceeds max iterations."""
    pass


@dataclass
class OrchestratorResult:
    """Result of orchestration."""
    tasks_completed: int
    tasks_failed: int
    validation_passed: bool
    review_markers: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"Orchestration complete: {self.tasks_completed} completed, "
            f"{self.tasks_failed} failed"
        )


class Orchestrator:
    """Orchestrate plan execution with validation and retry."""

    def __init__(
        self,
        plan: Plan,
        provider: Optional[LLMProvider] = None,
        provider_config: Optional[ProviderConfig] = None,
        max_iterations: int = 3,
        timeout_min: int = 10,
        auto_mode: bool = False,
        enable_web: bool = False,
    ):
        """Initialize orchestrator.

        Args:
            plan: Plan to execute
            provider: LLM provider instance (optional)
            provider_config: Provider configuration (optional)
            max_iterations: Max retry iterations per task
            timeout_min: Timeout per task in minutes
            auto_mode: Auto-approve review markers
            enable_web: Enable web dashboard integration
        """
        self.plan = plan
        self.max_iterations = max_iterations
        self.timeout_min = timeout_min
        self.auto_mode = auto_mode
        self.enable_web = enable_web

        self.executor = QwenExecutor(
            provider=provider,
            provider_config=provider_config,
            timeout_min=timeout_min
        )
        self.validator = Validator()
        self.git = GitWrapper()
        
        # Setup web broadcast if enabled
        if enable_web:
            from .web.broadcast import BroadcastService
            self.broadcast = BroadcastService.get_instance()
        else:
            self.broadcast = None
        
        self.progress = ProgressTracker(plan_file=plan.file_path)
        self.reviewer = HybridExecutor()
        self.aggregator = ReviewAggregator()

    def _extract_review_markers(self, output: str) -> List[str]:
        """Extract REVIEW markers from output.

        Args:
            output: Qwen CLI output

        Returns:
            List of review marker comments
        """
        pattern = r'<!--\s*REVIEW:\s*(.+?)\s*-->'
        return re.findall(pattern, output, re.DOTALL)

    def _apply_review_markers(self, markers: List[ReviewMarker]) -> int:
        """Apply REVIEW markers from review report.

        Args:
            markers: List of review markers

        Returns:
            Number of markers applied
        """
        applied = 0
        for marker in markers:
            if self.auto_mode and not marker.critical:
                # Auto-approve non-critical markers
                self.git.apply_fix(marker.suggestion)
                applied += 1
                self.progress.log(f"Auto-applied marker: {marker.suggestion}")
        return applied

    def _build_task_prompt(self, task: Task) -> str:
        """Build prompt for task execution.

        Args:
            task: Task to execute

        Returns:
            Prompt string for Qwen CLI
        """
        checkboxes = "\n".join(
            f"- {'[x]' if cb.completed else '[ ]'} {cb.text}"
            for cb in task.checkboxes
        )
        return (
            f"Task {task.number}: {task.title}\n\n"
            f"Checklist:\n{checkboxes}\n\n"
            f"Complete this task following the project conventions."
        )

    async def execute_task_with_retry(
        self,
        task: Task,
    ) -> OrchestratorResult:
        """Execute task with validation and retry.

        Args:
            task: Task to execute

        Returns:
            OrchestratorResult with success status

        Raises:
            MaxIterationsExceededError: If task fails after max iterations
        """
        self.progress.task_started(task.number, task.title)

        iteration = 0
        all_output = []
        all_markers = []

        while iteration < self.max_iterations:
            iteration += 1

            # Execute task via Qwen CLI
            self.progress.log(f"Executing task {task.number} (attempt {iteration})")
            
            output_lines = []
            async for event in self.executor.run_task(self._build_task_prompt(task)):
                output_lines.append(str(event))
                if event.get('type') == 'result':
                    result_text = event.get('result', '')
                    all_output.append(result_text)
                    # Extract review markers
                    markers = self._extract_review_markers(result_text)
                    all_markers.extend(markers)

            output_str = "\n".join(all_output)

            # Run validation
            self.progress.validation_started(self.plan.validation_commands)
            validation_result = await self.validator.run(self.plan.validation_commands)

            if validation_result.success:
                self.progress.validation_passed()
                self.progress.task_completed(task.number, task.title)

                # Run review system
                self.progress.log("Running review system...")
                git_diff = self.git.diff_head()
                review_report = await self.reviewer.run_review(
                    session_id=f"task-{task.number}",
                    git_diff=git_diff,
                )
                
                # Log review results
                self.progress.log(f"Review: {review_report.summary}")
                for result in review_report.results:
                    status = "✅" if result.success else "❌"
                    self.progress.log(f"  {status} {result.agent}: {len(result.findings)} findings")
                
                # Apply review markers (auto mode)
                if self.auto_mode:
                    applied = self._apply_review_markers(review_report.aggregated_markers)
                    if applied > 0:
                        self.progress.log(f"Auto-applied {applied} review markers")

                # Git commit
                commit_msg = f"feat: complete task {task.number}: {task.title}"
                self.git.add(["."])
                try:
                    self.git.commit(commit_msg)
                    self.progress.git_committed(commit_msg)
                except Exception:
                    self.progress.log("Warning: git commit failed")

                return OrchestratorResult(
                    tasks_completed=1,
                    tasks_failed=0,
                    validation_passed=True,
                    review_markers=all_markers
                )
            else:
                self.progress.validation_failed(validation_result.output)
                self.progress.log(f"Validation failed, retry {iteration}/{self.max_iterations}")

        # Max iterations exceeded
        raise MaxIterationsExceededError(
            f"Task {task.number} failed after {self.max_iterations} iterations"
        )

    async def run(self) -> OrchestratorResult:
        """Run all tasks in the plan.

        Returns:
            OrchestratorResult with overall status
        """
        # Setup web callback if enabled
        if self.enable_web and self.broadcast:
            async def web_callback(event_type: str, data: dict):
                if event_type == "task_started":
                    await self.broadcast.send_progress(0, data.get("task", ""))
                elif event_type == "log":
                    await self.broadcast.send_log(data.get("message", ""), data.get("level", "info"))
            
            self.progress.callback = web_callback
        
        self.progress.log(f"Starting plan: {self.plan.title}")
        self.progress.save()

        total_completed = 0
        total_failed = 0
        all_markers = []

        while not self.plan.is_complete:
            task = self.plan.current_task
            if task is None:
                break

            try:
                result = await self.execute_task_with_retry(task)
                total_completed += result.tasks_completed
                all_markers.extend(result.review_markers)
                
                # Move to next task
                self.plan.next_task()
                
            except (MaxIterationsExceededError, TaskTimeoutError) as e:
                self.progress.log(f"Task failed: {e}")
                total_failed += 1
                
                # Continue to next task or stop based on mode
                if not self.auto_mode:
                    self.progress.save()
                    raise
                
                self.plan.next_task()

        self.progress.log(f"Plan complete: {total_completed} tasks, {total_failed} failed")
        self.progress.save()

        return OrchestratorResult(
            tasks_completed=total_completed,
            tasks_failed=total_failed,
            validation_passed=total_failed == 0,
            review_markers=all_markers
        )
