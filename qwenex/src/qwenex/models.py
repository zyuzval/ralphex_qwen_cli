"""Models for Qwenex plan execution."""

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
