"""Tests for MCP review tools."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_launch_review_tool():
    """Test MCP launch_review tool"""
    from qwenex.mcp.tools.review import launch_review
    
    with patch("qwenex.mcp.tools.review.HybridExecutor") as mock_executor:
        mock_instance = AsyncMock()
        mock_instance.run_review = AsyncMock(return_value=MagicMock(summary="Review done"))
        mock_executor.return_value = mock_instance
        
        result = await launch_review(session_id="test-123")
        
        assert "Review done" in result
        assert mock_instance.run_review.called


@pytest.mark.asyncio
async def test_get_review_report_tool():
    """Test MCP get_review_report tool"""
    from qwenex.mcp.tools.review import get_review_report
    from qwenex.review.models import ReviewReport, ReviewResult
    
    # Mock report
    mock_report = ReviewReport(
        session_id="test-123",
        git_diff="diff...",
        results=[],
        aggregated_markers=[],
        conflicts=[],
        summary="Test summary",
    )
    
    with patch("qwenex.mcp.tools.review.load_review_report", return_value=mock_report):
        result = await get_review_report(session_id="test-123")
        
        assert result.session_id == "test-123"
        assert result.summary == "Test summary"


@pytest.mark.asyncio
async def test_apply_review_marker_tool():
    """Test MCP apply_review_marker tool"""
    from qwenex.mcp.tools.review import apply_review_marker
    from qwenex.review.models import ReviewReport, ReviewMarker
    
    mock_report = ReviewReport(
        session_id="test-123",
        git_diff="diff...",
        results=[],
        aggregated_markers=[
            ReviewMarker(
                suggestion="Add docstring",
                reason="PEP 257",
                awaits="решения человека",
                raw="<!-- REVIEW: ... -->",
            )
        ],
        conflicts=[],
        summary="Test",
    )
    
    with patch("qwenex.mcp.tools.review.load_review_report", return_value=mock_report):
        with patch("qwenex.mcp.tools.review.apply_marker_fix") as mock_apply:
            result = await apply_review_marker(
                session_id="test-123",
                marker_index=0,
                approve=True,
            )
            
            assert "Applied" in result
            assert mock_apply.called


@pytest.mark.asyncio
async def test_resolve_conflicts_tool():
    """Test MCP resolve_conflicts tool"""
    from qwenex.mcp.tools.review import resolve_conflicts
    from qwenex.review.models import ReviewReport
    
    mock_report = ReviewReport(
        session_id="test-123",
        git_diff="diff...",
        results=[],
        aggregated_markers=[],
        conflicts=["Conflict 1", "Conflict 2"],
        summary="Test",
    )
    
    with patch("qwenex.mcp.tools.review.load_review_report", return_value=mock_report):
        with patch("qwenex.mcp.tools.review.save_review_report") as mock_save:
            result = await resolve_conflicts(
                session_id="test-123",
                resolutions={0: "resolved", 1: "ignored"},
            )
            
            assert "Resolved 2 conflicts" in result
            assert mock_save.called
