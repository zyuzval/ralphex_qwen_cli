"""Tests for broadcast service."""

import pytest
from qwenex.web.broadcast import BroadcastService, ProgressUpdate


def test_broadcast_service_singleton():
    """Test singleton pattern."""
    service1 = BroadcastService.get_instance()
    service2 = BroadcastService.get_instance()
    assert service1 is service2


def test_progress_update():
    """Test ProgressUpdate dataclass."""
    update = ProgressUpdate(
        percent=50,
        current_task="Task 1",
        message="In progress"
    )
    assert update.percent == 50
    assert update.current_task == "Task 1"
    assert update.to_dict() == {
        "percent": 50,
        "current_task": "Task 1",
        "message": "In progress"
    }
