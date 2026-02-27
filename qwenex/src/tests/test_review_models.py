"""Tests for review system data models."""

import pytest
from qwenex.review.models import ReviewAgent, ReviewResult, ReviewReport, ReviewMarker


def test_review_agent_creation():
    """Test ReviewAgent dataclass creation"""
    agent = ReviewAgent(
        name="quality",
        priority=1,
        critical=True,
        prompt_template="You are a code quality reviewer..."
    )
    
    assert agent.name == "quality"
    assert agent.priority == 1
    assert agent.critical is True
    assert "code quality reviewer" in agent.prompt_template


def test_review_result_creation():
    """Test ReviewResult dataclass creation"""
    result = ReviewResult(
        agent="quality",
        success=True,
        findings=["Missing docstring"],
        review_markers=["<!-- REVIEW: Add docstring -->"],
        output="Full agent output",
        duration_sec=12.5
    )
    
    assert result.agent == "quality"
    assert result.success is True
    assert len(result.findings) == 1
    assert len(result.review_markers) == 1
    assert result.duration_sec == 12.5


def test_review_marker_parse():
    """Test parsing REVIEW markers from output"""
    output = """
- [QUALITY-1] Missing docstring
<!-- REVIEW: Add docstring — причина: PEP 257 — ждёт: решения человека -->
Some other text
"""
    markers = ReviewMarker.parse_from_output(output)

    assert len(markers) == 1
    assert markers[0].suggestion == "Add docstring"
    assert markers[0].reason == "PEP 257"
    assert markers[0].awaits == "решения человека"


def test_review_marker_parse_russian():
    """Test Russian format parsing."""
    output = "<!-- REVIEW: Fix bug — причина: Security issue — ждёт: Confirmation -->"
    markers = ReviewMarker.parse_from_output(output)
    assert len(markers) == 1
    assert markers[0].suggestion == "Fix bug"
    assert markers[0].reason == "Security issue"


def test_review_marker_parse_english():
    """Test English format parsing."""
    output = "<!-- REVIEW: Fix bug - reason: Security issue - awaits: Confirmation -->"
    markers = ReviewMarker.parse_from_output(output)
    assert len(markers) == 1
    assert markers[0].suggestion == "Fix bug"
    assert markers[0].reason == "Security issue"


def test_review_marker_parse_mixed():
    """Test mixed language parsing."""
    output = """
    <!-- REVIEW: Fix A — причина: Reason A — ждёт: Awaits A -->
    <!-- REVIEW: Fix B - reason: Reason B - awaits: Awaits B -->
    """
    markers = ReviewMarker.parse_from_output(output)
    assert len(markers) == 2


def test_review_report_creation():
    """Test ReviewReport dataclass creation"""
    report = ReviewReport(
        session_id="test-123",
        git_diff="diff --git a/file.py b/file.py...",
        results=[],
        aggregated_markers=[],
        conflicts=[],
        summary="Review completed successfully"
    )
    
    assert report.session_id == "test-123"
    assert report.git_diff.startswith("diff --git")
    assert len(report.results) == 0
    assert len(report.aggregated_markers) == 0
