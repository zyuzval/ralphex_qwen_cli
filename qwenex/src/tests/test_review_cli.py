"""Tests for review CLI interface."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import asyncio


def test_review_command_help():
    """Test review command help message"""
    from click.testing import CliRunner
    from qwenex.review.cli import review_command
    
    runner = CliRunner()
    result = runner.invoke(review_command, ["--help"])
    
    assert result.exit_code == 0
    assert "--session" in result.output
    assert "--diff" in result.output
    assert "--auto" in result.output
    assert "--interactive" in result.output


@pytest.mark.asyncio
@patch("qwenex.review.cli.HybridExecutor")
async def test_review_with_session_id(mock_executor_class):
    """Test review command with session ID"""
    from qwenex.review.cli import review_command
    
    # Mock executor
    mock_instance = AsyncMock()
    mock_instance.run_review = AsyncMock(return_value=MagicMock(
        summary="Review done",
        results=[],
        aggregated_markers=[],
        conflicts=[],
    ))
    mock_executor_class.return_value = mock_instance
    
    # Run async command
    await review_command.callback(
        session="test-123",
        diff=None,
        auto=False,
        interactive=False,
        agents=None,
        timeout=5,
    )
    
    assert mock_instance.run_review.called


@pytest.mark.asyncio
@patch("qwenex.review.cli.HybridExecutor")
async def test_review_with_diff_file(mock_executor_class):
    """Test review command with diff file"""
    from qwenex.review.cli import review_command
    
    # Create temp diff file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
        f.write("diff --git a/file.py b/file.py...")
        diff_path = f.name
    
    try:
        # Mock executor
        mock_instance = AsyncMock()
        mock_instance.run_review = AsyncMock(return_value=MagicMock(
            summary="Review done",
            results=[],
            aggregated_markers=[],
            conflicts=[],
        ))
        mock_executor_class.return_value = mock_instance
        
        # Run async command
        await review_command.callback(
            session=None,
            diff=diff_path,
            auto=False,
            interactive=False,
            agents=None,
            timeout=5,
        )
        
        assert mock_instance.run_review.called
    finally:
        # Cleanup
        import os
        os.unlink(diff_path)


@pytest.mark.asyncio
async def test_review_requires_session_or_diff():
    """Test review command requires --session or --diff"""
    from qwenex.review.cli import review_command
    from click.testing import CliRunner
    
    # Test via callback - should print error
    import io
    import sys
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        await review_command.callback(
            session=None,
            diff=None,
            auto=False,
            interactive=False,
            agents=None,
            timeout=5,
        )
    
    output = f.getvalue()
    assert "Error" in output or "required" in output
