"""Tests for plan parser and models."""

import pytest
from qwenex.models import Plan, Task, Checkbox


def test_checkbox_creation():
    """Test basic checkbox creation."""
    checkbox = Checkbox(text="Add feature", completed=False)
    assert checkbox.text == "Add feature"
    assert checkbox.completed is False
    assert checkbox.markdown == "- [ ] Add feature"


def test_checkbox_completed_markdown():
    """Test checkbox markdown with completed status."""
    checkbox = Checkbox(text="Done", completed=True)
    assert checkbox.markdown == "- [x] Done"


def test_task_creation():
    """Test basic task creation."""
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


def test_task_is_complete():
    """Test task completion check."""
    # Incomplete task
    task = Task(
        number="1",
        title="Test",
        checkboxes=[Checkbox(text="Do it", completed=False)]
    )
    assert task.is_complete is False

    # Complete task
    task_complete = Task(
        number="1",
        title="Test",
        checkboxes=[Checkbox(text="Do it", completed=True)]
    )
    assert task_complete.is_complete is True


def test_plan_creation():
    """Test basic plan creation."""
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
    assert plan.validation_commands == ["pytest", "ruff check"]
    assert plan.current_task_index == 0
    assert plan.is_complete is False


def test_plan_current_task():
    """Test getting current task from plan."""
    plan = Plan(
        title="Test Plan",
        file_path="test.md",
        tasks=[
            Task(number="1", title="First", checkboxes=[]),
            Task(number="2", title="Second", checkboxes=[]),
        ]
    )
    
    assert plan.current_task is not None
    assert plan.current_task.number == "1"
    
    # Move to next task
    plan.next_task()
    assert plan.current_task is not None
    assert plan.current_task.number == "2"
    
    # No more tasks
    plan.next_task()
    assert plan.current_task is None


def test_plan_is_complete():
    """Test plan completion check."""
    plan = Plan(
        title="Test",
        file_path="test.md",
        tasks=[Task(number="1", title="Task", checkboxes=[Checkbox(text="Do", completed=True)])]
    )
    
    # Not complete - task not marked done
    assert plan.is_complete is False
    
    # Move past last task
    plan.next_task()
    plan.next_task()
    assert plan.is_complete is True


def test_plan_no_tasks():
    """Test plan with no tasks is immediately complete."""
    plan = Plan(title="Empty", file_path="empty.md", tasks=[])
    assert plan.is_complete is True
    assert plan.current_task is None
