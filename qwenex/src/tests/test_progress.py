"""Tests for progress tracker."""

import pytest
import tempfile
import os
from datetime import datetime
from qwenex.progress import ProgressTracker, ProgressEvent


class TestProgressEvent:
    """Tests for ProgressEvent dataclass."""

    def test_progress_event_creation(self):
        """Test basic event creation."""
        event = ProgressEvent(
            timestamp="10:30:05",
            message="Started task 1"
        )
        assert event.timestamp == "10:30:05"
        assert event.message == "Started task 1"

    def test_progress_event_str(self):
        """Test event string representation."""
        event = ProgressEvent(
            timestamp="10:30:05",
            message="Test message"
        )
        assert str(event) == "[10:30:05] Test message"


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    @pytest.fixture
    def temp_progress_dir(self):
        """Create temporary progress directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_create_tracker(self, temp_progress_dir):
        """Test creating a progress tracker."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        assert tracker.plan_file == "docs/plans/feature.md"
        assert tracker.events == []

    def test_log_event(self, temp_progress_dir):
        """Test logging an event."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.log("Started task 1")
        
        assert len(tracker.events) == 1
        assert "Started task 1" in tracker.events[0].message

    def test_log_multiple_events(self, temp_progress_dir):
        """Test logging multiple events."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.log("Event 1")
        tracker.log("Event 2")
        tracker.log("Event 3")
        
        assert len(tracker.events) == 3

    def test_save_progress(self, temp_progress_dir):
        """Test saving progress to file."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.log("Event 1")
        tracker.log("Event 2")
        tracker.save()
        
        # Check file exists
        progress_file = os.path.join(temp_progress_dir, "progress-feature.txt")
        assert os.path.exists(progress_file)
        
        # Check content
        with open(progress_file, 'r') as f:
            content = f.read()
        
        assert "Progress: docs/plans/feature.md" in content
        assert "Event 1" in content
        assert "Event 2" in content

    def test_save_creates_directory(self, temp_progress_dir):
        """Test that save creates progress directory if needed."""
        nested_dir = os.path.join(temp_progress_dir, "nested", "progress")
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=nested_dir
        )
        
        tracker.log("Event")
        tracker.save()
        
        assert os.path.exists(nested_dir)

    def test_load_progress(self, temp_progress_dir):
        """Test loading progress from file."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.log("Event 1")
        tracker.log("Event 2")
        tracker.save()
        
        # Create new tracker and load
        tracker2 = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        tracker2.load()
        
        assert len(tracker2.events) == 2

    def test_load_nonexistent_file(self, temp_progress_dir):
        """Test loading from nonexistent file."""
        tracker = ProgressTracker(
            plan_file="docs/plans/nonexistent.md",
            progress_dir=temp_progress_dir
        )
        
        # Should not raise, just return empty
        tracker.load()
        
        assert tracker.events == []

    def test_task_started(self, temp_progress_dir):
        """Test task_started helper method."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.task_started("1", "Implement feature")
        
        assert len(tracker.events) == 1
        assert "Started task 1: Implement feature" in tracker.events[0].message

    def test_task_completed(self, temp_progress_dir):
        """Test task_completed helper method."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.task_completed("1", "Implement feature")
        
        assert len(tracker.events) == 1
        assert "Completed task 1: Implement feature" in tracker.events[0].message

    def test_validation_started(self, temp_progress_dir):
        """Test validation_started helper method."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.validation_started(["pytest", "ruff check"])
        
        assert len(tracker.events) == 1
        assert "Running validation" in tracker.events[0].message

    def test_validation_passed(self, temp_progress_dir):
        """Test validation_passed helper method."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.validation_passed()
        
        assert len(tracker.events) == 1
        assert "Validation passed" in tracker.events[0].message

    def test_validation_failed(self, temp_progress_dir):
        """Test validation_failed helper method."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.validation_failed("pytest failed")
        
        assert len(tracker.events) == 1
        assert "Validation failed" in tracker.events[0].message
        assert "pytest failed" in tracker.events[0].message

    def test_git_committed(self, temp_progress_dir):
        """Test git_committed helper method."""
        tracker = ProgressTracker(
            plan_file="docs/plans/feature.md",
            progress_dir=temp_progress_dir
        )
        
        tracker.git_committed("feat: implement feature")
        
        assert len(tracker.events) == 1
        assert "Committed" in tracker.events[0].message
        assert "feat: implement feature" in tracker.events[0].message
