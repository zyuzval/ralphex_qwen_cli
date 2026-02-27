"""Progress tracking for Qwenex."""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from pathlib import Path


@dataclass
class ProgressEvent:
    """Single progress event."""
    timestamp: str
    message: str

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.message}"


@dataclass
class ProgressTracker:
    """Track and persist execution progress."""
    plan_file: str
    progress_dir: str = ".qwenex/progress"
    events: List[ProgressEvent] = field(default_factory=list)

    def _get_progress_filename(self) -> str:
        """Generate progress filename from plan file."""
        # Extract plan name from path
        plan_name = os.path.basename(self.plan_file)
        # Remove .md extension
        if plan_name.endswith('.md'):
            plan_name = plan_name[:-3]
        return f"progress-{plan_name}.txt"

    def _get_progress_path(self) -> Path:
        """Get full path to progress file."""
        return Path(self.progress_dir) / self._get_progress_filename()

    def _now(self) -> str:
        """Get current timestamp."""
        return datetime.now().strftime("%H:%M:%S")

    def log(self, message: str) -> None:
        """Log a progress event.

        Args:
            message: Event message
        """
        event = ProgressEvent(
            timestamp=self._now(),
            message=message
        )
        self.events.append(event)

    def task_started(self, task_number: str, task_title: str) -> None:
        """Log task start.

        Args:
            task_number: Task number (e.g., "1", "2.5")
            task_title: Task title
        """
        self.log(f"Started task {task_number}: {task_title}")

    def task_completed(self, task_number: str, task_title: str) -> None:
        """Log task completion.

        Args:
            task_number: Task number
            task_title: Task title
        """
        self.log(f"Completed task {task_number}: {task_title}")

    def validation_started(self, commands: List[str]) -> None:
        """Log validation start.

        Args:
            commands: Validation commands
        """
        cmds = ", ".join(commands) if commands else "none"
        self.log(f"Running validation: {cmds}")

    def validation_passed(self) -> None:
        """Log validation success."""
        self.log("Validation passed")

    def validation_failed(self, reason: str) -> None:
        """Log validation failure.

        Args:
            reason: Failure reason
        """
        self.log(f"Validation failed: {reason}")

    def git_committed(self, message: str) -> None:
        """Log git commit.

        Args:
            message: Commit message
        """
        self.log(f"Committed: {message}")

    def review_started(self) -> None:
        """Log review system start."""
        self.log("🔍 Starting review system...")

    def review_completed(self, summary: str, results: list) -> None:
        """Log review system completion.

        Args:
            summary: Review summary
            results: List of review results
        """
        self.log(f"✅ Review: {summary}")
        for result in results:
            status = "✅" if result.success else "❌"
            self.log(f"   {status} {result.agent}: {len(result.findings)} findings")

    def save(self) -> None:
        """Save progress to file."""
        progress_path = self._get_progress_path()
        
        # Create directory if needed
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write progress
        with open(progress_path, 'w', encoding='utf-8') as f:
            f.write(f"# Progress: {self.plan_file}\n")
            f.write(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")
            for event in self.events:
                f.write(f"{event}\n")

    def load(self) -> None:
        """Load progress from file."""
        progress_path = self._get_progress_path()
        
        if not progress_path.exists():
            return
        
        self.events = []
        with open(progress_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse format: [HH:MM:SS] message
                if line.startswith('[') and ']' in line:
                    end_bracket = line.index(']')
                    timestamp = line[1:end_bracket]
                    message = line[end_bracket + 2:]  # Skip "] "
                    self.events.append(ProgressEvent(
                        timestamp=timestamp,
                        message=message
                    ))
