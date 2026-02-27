"""MCP tools for review system."""

import logging
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from qwenex.review.hybrid_executor import HybridExecutor
from qwenex.review.models import ReviewReport, ReviewMarker
from qwenex.review.aggregator import ReviewAggregator

logger = logging.getLogger(__name__)

# MCP server instance
mcp = FastMCP("qwenex-review")


# Storage for review reports (TODO: use proper storage)
REPORTS_DIR = Path(".qwenex/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def save_review_report(session_id: str, report: ReviewReport) -> None:
    """Save review report to disk."""
    # TODO: Implement proper serialization
    pass


def load_review_report(session_id: str) -> ReviewReport:
    """Load review report from disk."""
    # TODO: Implement proper deserialization
    # For now, return empty report
    return ReviewReport(
        session_id=session_id,
        git_diff="",
        results=[],
        aggregated_markers=[],
        conflicts=[],
        summary="Report not found",
    )


def apply_marker_fix(marker: ReviewMarker) -> None:
    """Apply a REVIEW marker fix to the code."""
    # TODO: Implement actual fix application
    logger.info(f"Applying fix: {marker.suggestion}")


@mcp.tool()
async def launch_review(
    session_id: str,
    agents: Optional[list[str]] = None,
    timeout_min: int = 5,
) -> str:
    """
    Launch 5 review agents for a session.
    
    Args:
        session_id: Session identifier
        agents: Optional list of specific agents (default: all)
        timeout_min: Timeout per agent in minutes
    
    Returns:
        Summary of review results
    """
    logger.info(f"Launching review for session {session_id}")
    
    executor = HybridExecutor()
    executor.timeout_min = timeout_min
    
    # TODO: Get git diff from session
    git_diff = ""
    
    report = await executor.run_review(
        session_id=session_id,
        git_diff=git_diff,
        agents=agents,
    )
    
    # Save report
    save_review_report(session_id, report)
    
    return report.summary


@mcp.tool()
async def get_review_report(session_id: str) -> ReviewReport:
    """
    Get full review report for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        ReviewReport with all results
    """
    return load_review_report(session_id)


@mcp.tool()
async def apply_review_marker(
    session_id: str,
    marker_index: int,
    approve: bool,
) -> str:
    """
    Apply or reject a REVIEW marker.
    
    Args:
        session_id: Session identifier
        marker_index: Index of marker in aggregated_markers list
        approve: True to approve, False to reject
    
    Returns:
        Status message
    """
    report = load_review_report(session_id)
    
    if marker_index >= len(report.aggregated_markers):
        return f"Error: Invalid marker index {marker_index}"
    
    marker = report.aggregated_markers[marker_index]
    
    if approve:
        apply_marker_fix(marker)
        return f"Applied: {marker.suggestion}"
    else:
        return f"Rejected: {marker.suggestion}"


@mcp.tool()
async def resolve_conflicts(
    session_id: str,
    resolutions: dict[int, str],
) -> str:
    """
    Resolve conflicts between review agents.
    
    Args:
        session_id: Session identifier
        resolutions: Dict mapping conflict index to resolution
    
    Returns:
        Status message
    """
    report = load_review_report(session_id)
    
    for conflict_idx, resolution in resolutions.items():
        if conflict_idx < len(report.conflicts):
            logger.info(f"Conflict {conflict_idx} resolved: {resolution}")
    
    save_review_report(session_id, report)
    
    return f"Resolved {len(resolutions)} conflicts"
