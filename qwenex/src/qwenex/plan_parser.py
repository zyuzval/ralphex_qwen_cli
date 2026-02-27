"""Parse markdown plan files."""

import re

from .plan_models import Checkbox, Plan, Task


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
    validation_commands: list[str] = []
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
    tasks: list[Task] = []
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
    with open(file_path, encoding='utf-8') as f:
        markdown = f.read()
    return parse_plan(markdown, file_path)
